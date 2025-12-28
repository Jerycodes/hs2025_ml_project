from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Mt5H1DailyFeatureConfig:
    cut_hour: int = 0
    drop_weekends: bool = True


def load_mt5_export_bars(path: Path) -> pd.DataFrame:
    """Loads MT5 'Export Bars' files (commonly TAB-separated with <DATE>/<TIME>/... headers).

    Returns an H1-indexed DataFrame with columns:
        open, high, low, close, tick_volume, volume, spread
    Index is timezone-naive pandas datetime.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    # Many MT5 exports are TAB-separated; pandas otherwise reads the whole header as one column.
    df = pd.read_csv(path, sep="\t", engine="python")
    if df.shape[1] == 1 and "\t" in str(df.columns[0]):
        df = pd.read_csv(path, sep="\t", engine="python")

    # Normalize headers (case-insensitive)
    cols = {c.lower(): c for c in df.columns}
    date_col = cols.get("<date>") or cols.get("date")
    time_col = cols.get("<time>") or cols.get("time")
    open_col = cols.get("<open>") or cols.get("open")
    high_col = cols.get("<high>") or cols.get("high")
    low_col = cols.get("<low>") or cols.get("low")
    close_col = cols.get("<close>") or cols.get("close")
    tickvol_col = cols.get("<tickvol>") or cols.get("tick_volume") or cols.get("tick volume")
    vol_col = cols.get("<vol>") or cols.get("volume") or cols.get("vol")
    spread_col = cols.get("<spread>") or cols.get("spread")

    if date_col is None:
        raise ValueError("MT5 export missing date column (expected '<DATE>' or 'Date').")
    if open_col is None or high_col is None or low_col is None or close_col is None:
        raise ValueError("MT5 export missing one of: open/high/low/close columns.")

    if time_col is not None:
        dt = (df[date_col].astype(str) + " " + df[time_col].astype(str)).str.strip()
    else:
        dt = df[date_col].astype(str)
    dt = pd.to_datetime(dt, errors="coerce")

    out = pd.DataFrame(
        {
            "open": pd.to_numeric(df[open_col], errors="coerce"),
            "high": pd.to_numeric(df[high_col], errors="coerce"),
            "low": pd.to_numeric(df[low_col], errors="coerce"),
            "close": pd.to_numeric(df[close_col], errors="coerce"),
        }
    )
    if tickvol_col is not None:
        out["tick_volume"] = pd.to_numeric(df[tickvol_col], errors="coerce")
    else:
        out["tick_volume"] = np.nan
    if vol_col is not None:
        out["volume"] = pd.to_numeric(df[vol_col], errors="coerce")
    else:
        out["volume"] = np.nan
    if spread_col is not None:
        out["spread"] = pd.to_numeric(df[spread_col], errors="coerce")
    else:
        out["spread"] = np.nan

    out.index = dt
    out = out[out.index.notna()].sort_index()
    out = out.dropna(subset=["open", "high", "low", "close"])
    return out


def _session_date_index(dt_index: pd.DatetimeIndex, *, cut_hour: int) -> pd.DatetimeIndex:
    """Maps timestamps to a 'session date' based on a cut hour.

    Example: cut_hour=0 => calendar date
             cut_hour=22 => trading day ends at 22:00 (server time) and rolls over after that
    """
    return session_date_index(dt_index, cut_hour=cut_hour)


def session_date_index(dt_index: pd.DatetimeIndex, *, cut_hour: int) -> pd.DatetimeIndex:
    """Maps timestamps to a 'session date' based on a cut hour.

    This is used to align H1 bars to daily sessions consistently across data-prep and labeling.
    """
    cut_hour = int(cut_hour)
    if cut_hour < 0 or cut_hour > 23:
        raise ValueError("cut_hour must be between 0 and 23.")
    shifted = dt_index - pd.Timedelta(hours=cut_hour)
    return shifted.normalize()


def h1_to_daily_ohlc(
    df_h1: pd.DataFrame,
    *,
    cut_hour: int = 0,
    drop_weekends: bool = True,
) -> pd.DataFrame:
    """Aggregates H1 bars to daily OHLCV (project-style columns).

    Output columns: Open, High, Low, Close, Volume
    Index: Date (datetime64[ns])
    """
    if df_h1.empty:
        raise ValueError("df_h1 is empty.")
    session_date = _session_date_index(df_h1.index, cut_hour=cut_hour)

    g = df_h1.groupby(session_date, sort=True)
    daily = g.agg(
        Open=("open", "first"),
        High=("high", "max"),
        Low=("low", "min"),
        Close=("close", "last"),
        Volume=("tick_volume", "sum"),
    )
    daily.index.name = "Date"
    daily = daily.reset_index()
    daily["Date"] = pd.to_datetime(daily["Date"], errors="coerce")
    daily = daily[daily["Date"].notna()].copy()
    daily = daily.sort_values("Date").set_index("Date")

    if drop_weekends:
        daily = daily[daily.index.dayofweek < 5]

    return daily


def h1_daily_intraday_features(
    df_h1: pd.DataFrame,
    *,
    cfg: Mt5H1DailyFeatureConfig | None = None,
) -> pd.DataFrame:
    """Computes per-day intraday features from H1 bars (no lookahead).

    Output index is daily Date.
    """
    if cfg is None:
        cfg = Mt5H1DailyFeatureConfig()

    if df_h1.empty:
        raise ValueError("df_h1 is empty.")

    session_date = _session_date_index(df_h1.index, cut_hour=cfg.cut_hour)
    df = df_h1.copy()
    df["_date"] = session_date

    # Hourly close-to-close returns within each day (pct).
    df["_ret"] = df.groupby("_date")["close"].pct_change()
    df["_range_pct"] = (df["high"] - df["low"]) / df["close"]
    df["_dir"] = np.sign(df["close"] - df["open"])

    g = df.groupby("_date", sort=True)
    feat = g.agg(
        h1_ret_std=("_ret", "std"),
        h1_ret_sum_abs=("_ret", lambda s: float(np.nansum(np.abs(s.to_numpy())))),
        h1_range_pct_mean=("_range_pct", "mean"),
        h1_range_pct_max=("_range_pct", "max"),
        h1_tick_volume_sum=("tick_volume", "sum"),
        h1_spread_mean=("spread", "mean"),
        h1_bars=("close", "count"),
        h1_up_hours=("_dir", lambda s: int((s > 0).sum())),
        h1_down_hours=("_dir", lambda s: int((s < 0).sum())),
    ).astype(
        {
            "h1_tick_volume_sum": "float64",
            "h1_spread_mean": "float64",
            "h1_bars": "int64",
            "h1_up_hours": "int64",
            "h1_down_hours": "int64",
        }
    )

    # Fractions
    denom = feat["h1_bars"].replace(0, np.nan)
    feat["h1_up_hours_frac"] = feat["h1_up_hours"] / denom
    feat["h1_down_hours_frac"] = feat["h1_down_hours"] / denom

    # Day open->close return (using first open and last close of the session)
    first_open = g["open"].first()
    last_close = g["close"].last()
    feat["h1_close_open_pct"] = (last_close / first_open) - 1.0

    feat.index.name = "Date"
    feat = feat.reset_index()
    feat["Date"] = pd.to_datetime(feat["Date"], errors="coerce")
    feat = feat[feat["Date"].notna()].copy().sort_values("Date").set_index("Date")

    if cfg.drop_weekends:
        feat = feat[feat.index.dayofweek < 5]

    return feat
