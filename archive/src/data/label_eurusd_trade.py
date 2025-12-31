"""Trading-nahes Labeling für EURUSD auf Daily-OHLC.

Dieses Modul ist bewusst getrennt von `src/data/label_eurusd.py`, damit das
bestehende System unverändert bleibt. Es wird primär für die v2-Pipeline genutzt.

Grundidee (vereinfachtes Daily Backtesting):
- Wir entscheiden 1x täglich am Tag t.
- Entry erfolgt entweder am Close(t) oder am Open(t+1) (konfigurierbar).
- Innerhalb eines Horizonts von `horizon_days` wird geprüft, ob Take-Profit
  oder Stop-Loss zuerst erreicht wird (auf Basis von High/Low pro Tag).

Wichtige Einschränkung:
- Innerhalb einer einzelnen Tageskerze kennen wir die Reihenfolge nicht, in
  der High/Low erreicht wurden. Falls TP und SL am selben Tag berührt werden,
  wird das über `intraday_tie_breaker` aufgelöst.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

from src.utils.io import DATA_RAW


@dataclass(frozen=True)
class TradeLabelParams:
    horizon_days: int = 15
    entry: str = "next_open"  # 'close' | 'next_open'
    tp_pct: float = 0.02
    sl_mode: str = "fixed_pct"  # 'fixed_pct' | 'atr' | 'none'
    sl_pct: float = 0.01
    atr_window: int = 14
    atr_mult: float = 1.0
    intraday_tie_breaker: str = "stop"  # 'stop' | 'tp'
    conflict_policy: str = "first"  # 'first' | 'neutral' | 'prefer_down'


def _load_prices(
    *,
    price_source: str = "yahoo",
    drop_weekends: bool = False,
    date_shift_days: int = 0,
) -> pd.DataFrame:
    if price_source == "yahoo":
        csv_name = "EURUSDX.csv"
        df = pd.read_csv(DATA_RAW / "fx" / csv_name)
        if "Date" not in df.columns and df.columns[0] == "Price":
            df.columns = ["Date", "Close", "High", "Low", "Open", "Volume"]
    elif price_source == "eodhd":
        csv_name = "EURUSDX_eodhd.csv"
        df = pd.read_csv(DATA_RAW / "fx" / csv_name)
    elif price_source == "mt5":
        csv_name = "EURUSD_mt5_D1.csv"
        df = pd.read_csv(DATA_RAW / "fx" / csv_name)
    else:
        raise ValueError(f"Unbekannte price_source='{price_source}'.")

    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
    df = df[df["Date"].notna()].copy()

    if date_shift_days:
        df["Date"] = df["Date"] + pd.Timedelta(days=int(date_shift_days))

    df = df.sort_values("Date").set_index("Date")

    if drop_weekends:
        df = df[df.index.dayofweek < 5]

    for col in ["Close", "High", "Low", "Open", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _atr_sma(df: pd.DataFrame, window: int) -> pd.Series:
    """Simple ATR (SMA) auf Daily OHLC."""
    high = df["High"]
    low = df["Low"]
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(window=window, min_periods=window).mean()


def label_eurusd_trade(
    *,
    price_source: str = "yahoo",
    drop_weekends: bool = False,
    date_shift_days: int = 0,
    params: TradeLabelParams | None = None,
) -> pd.DataFrame:
    """Erstellt Labels 'up'/'down'/'neutral' über TP/SL-Hits auf Daily-OHLC.

    Output-Index ist immer der Signal-Tag t (Features bis t). Der Trade-Entry
    kann (konfigurierbar) am Close(t) oder Open(t+1) stattfinden.
    """
    if params is None:
        params = TradeLabelParams()

    if params.horizon_days <= 0:
        raise ValueError("horizon_days muss > 0 sein.")
    if params.entry not in {"close", "next_open"}:
        raise ValueError("entry muss 'close' oder 'next_open' sein.")
    if params.sl_mode not in {"fixed_pct", "atr", "none"}:
        raise ValueError("sl_mode muss 'fixed_pct', 'atr' oder 'none' sein.")
    if params.intraday_tie_breaker not in {"stop", "tp"}:
        raise ValueError("intraday_tie_breaker muss 'stop' oder 'tp' sein.")
    if params.conflict_policy not in {"first", "neutral", "prefer_down"}:
        raise ValueError("conflict_policy muss 'first', 'neutral' oder 'prefer_down' sein.")

    df = _load_prices(
        price_source=price_source,
        drop_weekends=drop_weekends,
        date_shift_days=date_shift_days,
    )
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()

    # Referenz: Close-to-Close Lookahead-Return (wie im v1 Labeling), nur für Analyse.
    df["lookahead_return"] = df["Close"].shift(-params.horizon_days) / df["Close"] - 1.0

    atr = None
    if params.sl_mode == "atr":
        atr = _atr_sma(df, params.atr_window)
        df["atr"] = atr

    dates = df.index.to_numpy()
    o = df["Open"].to_numpy()
    h = df["High"].to_numpy()
    l = df["Low"].to_numpy()
    c = df["Close"].to_numpy()

    n = int(df.shape[0])
    labels = np.array(["neutral"] * n, dtype=object)
    entry_price = np.full(n, np.nan, dtype=float)
    nat = np.datetime64("NaT")
    entry_date = np.full(n, nat, dtype="datetime64[ns]")
    exit_date = np.full(n, nat, dtype="datetime64[ns]")
    exit_reason = np.array([""] * n, dtype=object)
    hit_offset = np.full(n, -1, dtype=int)

    def _resolve_same_day_hit(tp_hit: bool, sl_hit: bool) -> str | None:
        if tp_hit and sl_hit:
            return "tp" if params.intraday_tie_breaker == "tp" else "sl"
        if tp_hit:
            return "tp"
        if sl_hit:
            return "sl"
        return None

    for i in range(n):
        entry_idx = i if params.entry == "close" else i + 1
        end_idx = i + params.horizon_days
        if entry_idx >= n or end_idx >= n:
            continue

        if params.entry == "close":
            ent = c[entry_idx]
            ent_dt = dates[entry_idx]
            start_idx = i + 1  # wir nutzen t+1..t+h als Hit-Fenster
        else:
            ent = o[entry_idx]
            ent_dt = dates[entry_idx]
            start_idx = entry_idx  # t+1..t+h

        if not np.isfinite(ent) or ent <= 0:
            continue

        sl_pct = None
        if params.sl_mode == "fixed_pct":
            sl_pct = float(params.sl_pct)
        elif params.sl_mode == "atr":
            if atr is None or not np.isfinite(float(df["atr"].iloc[entry_idx])):
                continue
            sl_pct = float(params.atr_mult) * float(df["atr"].iloc[entry_idx]) / ent
        else:
            sl_pct = None

        tp_long = ent * (1.0 + float(params.tp_pct))
        sl_long = ent * (1.0 - sl_pct) if sl_pct is not None else -np.inf
        tp_short = ent * (1.0 - float(params.tp_pct))
        sl_short = ent * (1.0 + sl_pct) if sl_pct is not None else np.inf

        # Track first outcome for long/short
        long_hit: tuple[int, str] | None = None  # (idx, 'tp'|'sl')
        short_hit: tuple[int, str] | None = None

        for j in range(start_idx, end_idx + 1):
            # Long: TP if High >= tp_long, SL if Low <= sl_long
            long_out = _resolve_same_day_hit(h[j] >= tp_long, l[j] <= sl_long)
            if long_hit is None and long_out is not None:
                long_hit = (j, long_out)

            # Short: TP if Low <= tp_short, SL if High >= sl_short
            short_out = _resolve_same_day_hit(l[j] <= tp_short, h[j] >= sl_short)
            if short_hit is None and short_out is not None:
                short_hit = (j, short_out)

            if long_hit is not None and short_hit is not None:
                # wir kennen beide ersten Hits – weitere Tage sind irrelevant
                break

        cand: list[tuple[str, int, str]] = []
        if long_hit is not None and long_hit[1] == "tp":
            cand.append(("up", long_hit[0], "tp"))
        if short_hit is not None and short_hit[1] == "tp":
            cand.append(("down", short_hit[0], "tp"))

        chosen: tuple[str, int, str] | None = None
        if len(cand) == 1:
            chosen = cand[0]
        elif len(cand) == 2:
            # Konflikt: sowohl Long-TP als auch Short-TP innerhalb des Horizonts möglich.
            # Entscheide nach dem früheren Treffer, oder fallback nach Policy.
            cand.sort(key=lambda x: x[1])
            if cand[0][1] < cand[1][1]:
                chosen = cand[0]
            else:
                if params.conflict_policy == "neutral":
                    chosen = None
                elif params.conflict_policy == "prefer_down":
                    chosen = next((x for x in cand if x[0] == "down"), None)
                else:
                    # first (bei Gleichstand prefer_down wie im v1 Bias)
                    chosen = next((x for x in cand if x[0] == "down"), cand[0])

        # Wenn kein TP erreicht wurde, bleibt neutral.
        if chosen is None:
            entry_price[i] = ent
            entry_date[i] = ent_dt
            continue

        lab, hit_j, reason = chosen
        labels[i] = lab
        entry_price[i] = ent
        entry_date[i] = ent_dt
        exit_date[i] = dates[hit_j]
        exit_reason[i] = reason
        hit_offset[i] = int(hit_j - i)

    out = df.copy()
    out["label"] = labels
    out["entry_price"] = entry_price
    out["entry_date"] = entry_date
    out["exit_date"] = exit_date
    out["exit_reason"] = exit_reason
    out["hit_offset"] = hit_offset

    # drop rows without sufficient future context
    return out.dropna(subset=["lookahead_return"]).copy()
