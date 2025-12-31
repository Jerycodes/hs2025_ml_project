"""Kalibriert TP/SL (max adverse move) datenbasiert aus OHLC.

Ziel: Du willst 1x täglich (am Close) entscheiden und vermeiden, dass
`max_adverse_move_pct` zu streng ist (-> alles neutral) oder zu lax (-> noisy labels).

Dieses Script misst für Long/Short separat:
- Trefferquote (TP innerhalb horizon_days, ohne SL vorher)
- Verteilung der maximalen Gegenbewegung bis zum TP-Hit (Adverse Move)
- ATR-Verteilung (optional, um ATR-basierte Stops zu wählen)

Beispiele:
    python3 -m scripts.calibrate_trade_params_v2 --price-source yahoo --entry close --tp-pct 0.02 --horizon-days 15
    python3 -m scripts.calibrate_trade_params_v2 --price-source eodhd --drop-weekends --entry close --tp-pct 0.02 --horizon-days 15
    python3 -m scripts.calibrate_trade_params_v2 --price-source mt5 --entry close --tp-pct 0.02 --horizon-days 15
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Literal, Tuple

import numpy as np
import pandas as pd

from src.data.label_eurusd_trade import _atr_sma, _load_prices


EntryMode = Literal["close", "next_open"]
TieBreaker = Literal["stop", "tp"]


@dataclass(frozen=True)
class SimParams:
    horizon_days: int
    entry: EntryMode
    tp_pct: float
    sl_pct: float | None
    atr_window: int
    atr_mult: float | None
    intraday_tie_breaker: TieBreaker


def _resolve_same_day_hit(tp_hit: bool, sl_hit: bool, tie_breaker: TieBreaker) -> str | None:
    if tp_hit and sl_hit:
        return "tp" if tie_breaker == "tp" else "sl"
    if tp_hit:
        return "tp"
    if sl_hit:
        return "sl"
    return None


def _simulate_one_side(
    *,
    df: pd.DataFrame,
    side: Literal["long", "short"],
    params: SimParams,
) -> Tuple[pd.Series, pd.Series]:
    """Returns (tp_hit_mask, adverse_move_pct_until_tp_or_end)."""
    o = df["Open"].to_numpy()
    h = df["High"].to_numpy()
    l = df["Low"].to_numpy()
    c = df["Close"].to_numpy()
    dates = df.index.to_numpy()

    n = len(df)
    tp_hit = np.zeros(n, dtype=bool)
    adverse = np.full(n, np.nan, dtype=float)

    atr = None
    if params.atr_mult is not None:
        atr = _atr_sma(df, params.atr_window).to_numpy()

    for i in range(n):
        entry_idx = i if params.entry == "close" else i + 1
        end_idx = i + params.horizon_days
        if entry_idx >= n or end_idx >= n:
            continue

        ent = c[entry_idx] if params.entry == "close" else o[entry_idx]
        if not np.isfinite(ent) or ent <= 0:
            continue

        # Determine SL in pct
        sl_pct = params.sl_pct
        if params.atr_mult is not None:
            atr_i = atr[entry_idx]
            if not np.isfinite(atr_i) or atr_i <= 0:
                continue
            sl_pct = float(params.atr_mult) * float(atr_i) / float(ent)

        # Price levels
        if side == "long":
            tp_level = ent * (1 + params.tp_pct)
            sl_level = ent * (1 - sl_pct) if sl_pct is not None else -np.inf
        else:
            tp_level = ent * (1 - params.tp_pct)
            sl_level = ent * (1 + sl_pct) if sl_pct is not None else np.inf

        start_idx = i + 1 if params.entry == "close" else entry_idx

        min_low = ent
        max_high = ent
        hit_j = None
        hit_type = None

        for j in range(start_idx, end_idx + 1):
            if side == "long":
                tp = h[j] >= tp_level
                sl = l[j] <= sl_level
                out = _resolve_same_day_hit(tp, sl, params.intraday_tie_breaker)
                min_low = float(min(min_low, l[j]))
            else:
                tp = l[j] <= tp_level
                sl = h[j] >= sl_level
                out = _resolve_same_day_hit(tp, sl, params.intraday_tie_breaker)
                max_high = float(max(max_high, h[j]))

            if out is not None:
                hit_j = j
                hit_type = out
                break

        # adverse move until hit (or until end if no hit)
        if side == "long":
            adverse[i] = max(0.0, (ent - min_low) / ent)
        else:
            adverse[i] = max(0.0, (max_high - ent) / ent)

        if hit_type == "tp":
            tp_hit[i] = True

    return pd.Series(tp_hit, index=df.index), pd.Series(adverse, index=df.index)


def _print_quantiles(name: str, s: pd.Series) -> None:
    s = s.dropna()
    if len(s) == 0:
        print(f"{name}: (keine Daten)")
        return
    qs = [0.5, 0.7, 0.8, 0.9, 0.95, 0.99]
    out = {f"p{int(q*100)}": float(s.quantile(q)) for q in qs}
    out["mean"] = float(s.mean())
    print(name + ":", {k: round(v, 6) for k, v in out.items()})


def main() -> None:
    ap = argparse.ArgumentParser(description="Kalibriert max adverse move / ATR aus OHLC.")
    ap.add_argument("--price-source", choices=["yahoo", "eodhd", "mt5"], default="yahoo")
    ap.add_argument(
        "--drop-weekends",
        action="store_true",
        help="Filtert Sa/So (meist nur relevant für eodhd; bei mt5/yahoo oft ohne Effekt).",
    )
    ap.add_argument("--date-shift-days", type=int, default=0, help="Shift der Date-Spalte (Cut-Approximation).")
    ap.add_argument("--entry", choices=["close", "next_open"], default="close")
    ap.add_argument("--horizon-days", type=int, default=15)
    ap.add_argument("--tp-pct", type=float, default=0.02)
    ap.add_argument("--sl-pct", type=float, default=0.01, help="Fixer SL in Prozent (z.B. 0.01=1%%).")
    ap.add_argument("--no-sl", action="store_true", help="SL deaktivieren (nur TP-Hit, adverse move bis TP/Ende).")
    ap.add_argument("--intraday-tie-breaker", choices=["stop", "tp"], default="stop")
    ap.add_argument("--atr-window", type=int, default=14)
    ap.add_argument("--atr-mult", type=float, default=None, help="Wenn gesetzt: SL=atr_mult*ATR(window).")
    args = ap.parse_args()

    if args.horizon_days <= 0:
        raise SystemExit("horizon_days muss > 0 sein.")
    if args.tp_pct <= 0:
        raise SystemExit("tp_pct muss > 0 sein.")

    df = _load_prices(
        price_source=args.price_source,
        drop_weekends=bool(args.drop_weekends),
        date_shift_days=int(args.date_shift_days),
    ).dropna(subset=["Open", "High", "Low", "Close"])

    sl_pct = None if args.no_sl else float(args.sl_pct)
    atr_mult = float(args.atr_mult) if args.atr_mult is not None else None

    params = SimParams(
        horizon_days=int(args.horizon_days),
        entry=args.entry,  # type: ignore[arg-type]
        tp_pct=float(args.tp_pct),
        sl_pct=sl_pct,
        atr_window=int(args.atr_window),
        atr_mult=atr_mult,
        intraday_tie_breaker=args.intraday_tie_breaker,  # type: ignore[arg-type]
    )

    print("=== Settings ===")
    print(
        {
            "price_source": args.price_source,
            "drop_weekends": bool(args.drop_weekends),
            "date_shift_days": int(args.date_shift_days),
            "entry": args.entry,
            "horizon_days": int(args.horizon_days),
            "tp_pct": float(args.tp_pct),
            "sl_pct": sl_pct,
            "atr_mult": atr_mult,
            "atr_window": int(args.atr_window),
            "intraday_tie_breaker": args.intraday_tie_breaker,
        }
    )
    print("rows:", len(df), "range:", df.index.min().date(), df.index.max().date())

    # ATR stats (for intuition)
    atr = _atr_sma(df, int(args.atr_window))
    atr_pct = (atr / df["Close"]).dropna()
    _print_quantiles("ATR% (SMA)", atr_pct)

    # Simulate both sides
    for side in ["long", "short"]:
        tp_hit, adverse = _simulate_one_side(df=df, side=side, params=params)  # type: ignore[arg-type]
        hit_rate = float(tp_hit.mean())
        print(f"\n=== {side.upper()} ===")
        print("TP-hit rate:", round(hit_rate, 4))
        _print_quantiles("adverse_move_pct (all)", adverse)
        _print_quantiles("adverse_move_pct (TP hits)", adverse[tp_hit])

        # Quick suggestion: pick p80 of adverse on TP hits
        s = adverse[tp_hit].dropna()
        if len(s):
            rec = float(s.quantile(0.8))
            print("suggest max_adverse_move_pct ~ p80(TP hits):", round(rec, 6))


if __name__ == "__main__":
    main()
