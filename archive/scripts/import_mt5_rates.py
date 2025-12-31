"""Import/convert MT5 bar exports for this project.

Expected MT5 export format (CSV):
    time_unix,time,open,high,low,close,tick_volume,spread,real_volume

This script converts M1 exports to Daily OHLCV in the project's raw format:
    Date,Open,High,Low,Close,Volume
and writes it to:
    data/raw/fx/EURUSD_mt5_D1.csv  (by default)
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import DATA_RAW


def _pick_col(cols: list[str], *candidates: str) -> str | None:
    lower_to_orig = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_to_orig:
            return lower_to_orig[cand.lower()]
    return None


def _read_mt5_csv(path: Path, *, chunksize: int) -> pd.io.parsers.TextFileReader:
    """Reads MT5 exports in a few common formats.

    Formats seen in the wild:
    - Our script export: comma-separated with headers `time_unix,time,open,...`
    - MT5 GUI "Export Bars": often TAB-separated with headers like `<DATE>\t<OPEN>...`
    - Some locales use `;` as separator.
    """
    # Try comma-separated first (default).
    reader = pd.read_csv(path, chunksize=chunksize)
    # Peek first chunk to detect tab/semicolon formats.
    first = next(reader)
    cols = list(first.columns)

    def _rechain(first_chunk: pd.DataFrame, new_reader: pd.io.parsers.TextFileReader):
        yield first_chunk
        for c in new_reader:
            yield c

    # Tab-separated: pandas reads the whole header line as one column containing '\t'.
    if len(cols) == 1 and "\t" in cols[0]:
        tab_reader = pd.read_csv(path, sep="\t", engine="python", chunksize=chunksize)
        first_tab = next(tab_reader)
        return _rechain(first_tab, tab_reader)  # type: ignore[return-value]

    # Semicolon-separated (common in some CSV locales).
    if len(cols) == 1 and ";" in cols[0]:
        semi_reader = pd.read_csv(path, sep=";", engine="python", chunksize=chunksize)
        first_semi = next(semi_reader)
        return _rechain(first_semi, semi_reader)  # type: ignore[return-value]

    # Default comma-separated: return iterator that already has first chunk.
    return _rechain(first, reader)  # type: ignore[return-value]


def _parse_dt(chunk: pd.DataFrame) -> pd.Series:
    # MT5 exports can vary:
    # - our script: time_unix,time,...
    # - MT5 GUI (Export Bars): Date,Open,High,... (sometimes "Time" instead of "Date")
    cols = list(chunk.columns)
    # MT5/MT4-style headers
    if _pick_col(cols, "<date>") is not None:
        date_col = _pick_col(cols, "<date>")
        time_col = _pick_col(cols, "<time>")
        if date_col is None:
            raise ValueError("Unexpected: <DATE> not found.")
        if time_col is not None:
            dt = (chunk[date_col].astype(str) + " " + chunk[time_col].astype(str)).str.strip()
            return pd.to_datetime(dt, errors="coerce")
        return pd.to_datetime(chunk[date_col].astype(str), errors="coerce")

    time_unix_col = _pick_col(cols, "time_unix", "time", "date", "datetime")
    if time_unix_col is None:
        raise ValueError(
            "Missing time column. Expected one of: 'time_unix', 'time', 'Date', 'date', 'datetime'."
        )

    s = chunk[time_unix_col]
    # Prefer unix seconds if it looks numeric.
    s_num = pd.to_numeric(s, errors="coerce")
    if s_num.notna().mean() > 0.95:
        return pd.to_datetime(s_num, unit="s", errors="coerce")

    # Fallback: parse formatted time strings (e.g. '2020.01.01 00:00:00').
    return pd.to_datetime(s.astype(str), errors="coerce")


def mt5_m1_to_d1(
    *,
    in_path: Path,
    out_path: Path,
    chunksize: int = 500_000,
    drop_weekends: bool = False,
) -> pd.DataFrame:
    open_col = None
    high_col = None
    low_col = None
    close_col = None
    vol_col = None

    out_rows: list[dict] = []
    carry: dict | None = None

    for chunk in _read_mt5_csv(in_path, chunksize=chunksize):
        if open_col is None:
            cols = list(chunk.columns)
            open_col = _pick_col(cols, "open", "<open>")
            high_col = _pick_col(cols, "high", "<high>")
            low_col = _pick_col(cols, "low", "<low>")
            close_col = _pick_col(cols, "close", "<close>")
            vol_col = _pick_col(
                cols,
                "tick_volume",
                "tick volume",
                "tickvolume",
                "<tickvol>",
                "<vol>",
                "volume",
            )
            missing = [n for n, c in [("open", open_col), ("high", high_col), ("low", low_col), ("close", close_col)] if c is None]
            if missing:
                raise ValueError(f"Missing required columns: {missing}.")
            if vol_col is None:
                raise ValueError("Missing volume column. Expected 'tick_volume' (preferred) or 'volume'.")

        dt = _parse_dt(chunk)
        chunk = chunk.assign(_dt=dt).dropna(subset=["_dt"]).copy()
        if chunk.empty:
            continue

        for c in [open_col, high_col, low_col, close_col, vol_col]:
            chunk[c] = pd.to_numeric(chunk[c], errors="coerce")
        chunk = chunk.dropna(subset=[open_col, high_col, low_col, close_col]).copy()
        if chunk.empty:
            continue

        chunk = chunk.sort_values("_dt")
        chunk["_date"] = chunk["_dt"].dt.strftime("%Y-%m-%d")

        agg = (
            chunk.groupby("_date", sort=True)
            .agg(
                Open=(open_col, "first"),
                High=(high_col, "max"),
                Low=(low_col, "min"),
                Close=(close_col, "last"),
                Volume=(vol_col, "sum"),
            )
            .reset_index()
            .rename(columns={"_date": "Date"})
        )
        if agg.empty:
            continue

        if carry is not None and carry["Date"] == agg.loc[0, "Date"]:
            agg.loc[0, "Open"] = carry["Open"]
            agg.loc[0, "High"] = max(float(carry["High"]), float(agg.loc[0, "High"]))
            agg.loc[0, "Low"] = min(float(carry["Low"]), float(agg.loc[0, "Low"]))
            agg.loc[0, "Close"] = agg.loc[0, "Close"]
            agg.loc[0, "Volume"] = float(carry["Volume"]) + float(agg.loc[0, "Volume"])
            carry = None

        if len(agg) > 1:
            out_rows.extend(agg.iloc[:-1].to_dict(orient="records"))
        carry = agg.iloc[-1].to_dict()

    if carry is not None:
        out_rows.append(carry)

    df = pd.DataFrame(out_rows)
    if df.empty:
        raise RuntimeError("No rows produced. Check input file/columns and time parsing.")

    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
    df = df[df["Date"].notna()].copy()
    df = df.sort_values("Date").reset_index(drop=True)

    if drop_weekends:
        df = df[df["Date"].dt.dayofweek < 5].copy()

    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Konvertiert MT5 Bar-Exports (z.B. M1) in Daily-OHLCV im Projektformat."
    )
    parser.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        required=True,
        help="Pfad zur MT5-CSV (Export aus tools/mt5/ExportRates_Chunked.mq5).",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        type=Path,
        default=None,
        help="Ausgabepfad (Default: data/raw/fx/EURUSD_mt5_D1.csv).",
    )
    parser.add_argument(
        "--drop-weekends",
        action="store_true",
        help="Entfernt Sa/So-Zeilen aus dem Daily-Output.",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=500_000,
        help="CSV-Chunksize für Streaming-Import (Default: 500000).",
    )
    args = parser.parse_args()

    out_path = args.out_path or (DATA_RAW / "fx" / "EURUSD_mt5_D1.csv")
    df = mt5_m1_to_d1(
        in_path=args.in_path,
        out_path=out_path,
        chunksize=int(args.chunksize),
        drop_weekends=bool(args.drop_weekends),
    )
    print("[ok] Daily OHLCV gespeichert unter:", out_path)
    print("[info] Tage:", len(df))


if __name__ == "__main__":
    main()
