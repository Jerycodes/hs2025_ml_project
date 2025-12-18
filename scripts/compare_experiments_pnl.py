"""Vergleichsplot: price_only vs news+price (Final Two-Stage).

Erzeugt eine Grafik (PNG/PDF), die zwei Experimente übereinander legt
(z.B. price_only vs news+price) und unten Balken für die Gewinn-Differenz
über die Zeit zeigt.

Standard:
    - Strategie B (10% Kapital) als kumulierter P&L
    - Hebel 20
    - Variante 2 (TP-only, kein Stop-Loss)

Beispiel:
    python3 -m scripts.compare_experiments_pnl \
        --exp-a hp_long_final_yahoo \
        --exp-b hv_long_final_yahoo \
        --strategy B \
        --leverage 20 \
        --variant tp_only \
        --output notebooks/results/final_two_stage/pdf/compare_hp_long_vs_hv_long_pnlB_lev20.pdf
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Literal

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scripts.generate_two_stage_report import (
    load_predictions,
    load_fx_labels_for_exp,
    _compute_trade_return,
    _compute_trade_return_tp_or_horizon_no_sl,
    _compute_trade_outcome,
)


Strategy = Literal["A", "B"]
Variant = Literal["sl_tp", "tp_only", "sl_tp_exit", "tp_only_exit"]


def find_project_root(start: Path | None = None) -> Path:
    if start is None:
        start = Path.cwd()
    root = start
    while not (root / "src").is_dir():
        if root.parent == root:
            raise RuntimeError("Projektwurzel mit Unterordner 'src' nicht gefunden.")
        root = root.parent
    return root


def _load_exp_config(project_root: Path, exp_id: str) -> dict:
    safe_id = exp_id.replace(" ", "_")
    path = project_root / "data" / "processed" / "experiments" / f"{safe_id}_config.json"
    if not path.is_file():
        raise FileNotFoundError(f"Experiment-Config nicht gefunden: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _compute_strategy_series(
    project_root: Path,
    exp_id: str,
    *,
    strategy: Strategy,
    variant: Variant,
    leverage: float,
    stake_fixed_chf: float,
    frac_capital: float,
    start_capital: float,
) -> pd.DataFrame:
    preds = load_predictions(project_root, exp_id)
    if preds is None:
        raise FileNotFoundError(f"Predictions-CSV fehlt für EXP_ID='{exp_id}'.")

    fx = load_fx_labels_for_exp(project_root, exp_id)
    if fx is None:
        raise FileNotFoundError(f"FX-Labels fehlen für EXP_ID='{exp_id}'.")

    exp_config = _load_exp_config(project_root, exp_id)
    label_params = exp_config.get("label_params", {})

    df = preds.copy().sort_values("date")
    df["date"] = pd.to_datetime(df["date"])
    df["label_true"] = df["label_true"].astype(str)
    df["combined_pred"] = df["combined_pred"].astype(str)

    settle_at_exit = str(variant).endswith("_exit")
    base_variant = str(variant).replace("_exit", "")
    if base_variant not in {"sl_tp", "tp_only"}:
        raise ValueError(f"Unbekannte variant: {variant}")

    is_trade = df["combined_pred"].isin(["up", "down"]).astype(int)
    df["is_trade"] = is_trade

    if settle_at_exit:
        dates = pd.DatetimeIndex(df["date"].tolist())

        def book_date(exit_dt: pd.Timestamp) -> pd.Timestamp | None:
            i = dates.searchsorted(pd.Timestamp(exit_dt))
            if i >= len(dates):
                return None
            return dates[i]

        if strategy == "A":
            pending: dict[pd.Timestamp, float] = {}
            pnl_cum: list[float] = []
            cum = 0.0
            for dt, pred, true_lab in zip(df["date"], df["combined_pred"], df["label_true"]):
                cum += float(pending.pop(dt, 0.0))
                if pred in {"up", "down"}:
                    r, exit_dt = _compute_trade_outcome(dt, pred, true_lab, fx, label_params, variant=base_variant)
                    booked = book_date(exit_dt)
                    if booked is not None:
                        pending[booked] = pending.get(booked, 0.0) + float(stake_fixed_chf) * float(r) * float(leverage)
                pnl_cum.append(cum)
            return pd.DataFrame({"date": df["date"], "pnl_cum": pnl_cum})

        # strategy B: Settlement am Exit (P&L wirkt erst beim Schließen auf Kapital)
        pending: dict[pd.Timestamp, float] = {}
        capital = float(start_capital)
        pnl_cum: list[float] = []
        for dt, pred, true_lab in zip(df["date"], df["combined_pred"], df["label_true"]):
            capital += float(pending.pop(dt, 0.0))
            if pred in {"up", "down"}:
                r, exit_dt = _compute_trade_outcome(dt, pred, true_lab, fx, label_params, variant=base_variant)
                booked = book_date(exit_dt)
                if booked is not None:
                    stake_b = float(frac_capital) * float(capital)
                    pending[booked] = pending.get(booked, 0.0) + stake_b * float(r) * float(leverage)
            pnl_cum.append(capital - float(start_capital))
        return pd.DataFrame({"date": df["date"], "pnl_cum": pnl_cum})

    # Settlement sofort (Variante 1/2 wie bisher)
    trade_return_fn = _compute_trade_return if base_variant == "sl_tp" else _compute_trade_return_tp_or_horizon_no_sl
    df["trade_return"] = [
        trade_return_fn(dt, pred, true, fx, label_params)
        for dt, pred, true in zip(df["date"], df["combined_pred"], df["label_true"])
    ]

    if strategy == "A":
        stake = df["is_trade"] * float(stake_fixed_chf)
        pnl_daily = stake * (df["trade_return"] * float(leverage))
        pnl_cum = pnl_daily.cumsum()
        out = pd.DataFrame({"date": df["date"], "pnl_cum": pnl_cum})
        return out

    # strategy B (10% Kapital pro Trade)
    capital = float(start_capital)
    capital_after: list[float] = []
    for r, trade_flag in zip(df["trade_return"], df["is_trade"]):
        if int(trade_flag) == 1:
            capital = capital * (1.0 + float(frac_capital) * float(r) * float(leverage))
        capital_after.append(capital)

    out = pd.DataFrame({"date": df["date"], "pnl_cum": np.array(capital_after) - float(start_capital)})
    return out


def _format_x_as_months(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")


def main() -> None:
    parser = argparse.ArgumentParser(description="Vergleicht Profit-Verläufe zweier Final-Two-Stage Experimente.")
    parser.add_argument("--exp-a", type=str, required=True, help="z.B. hp_long_final_yahoo (price_only)")
    parser.add_argument("--exp-b", type=str, required=True, help="z.B. hv_long_final_yahoo (news+price)")
    parser.add_argument(
        "--label-a",
        type=str,
        default=None,
        help="Optionales Label für Experiment A (z.B. 'ohne News' / 'baseline').",
    )
    parser.add_argument(
        "--label-b",
        type=str,
        default=None,
        help="Optionales Label für Experiment B (z.B. 'mit News' / 'first-hit').",
    )
    parser.add_argument("--strategy", choices=["A", "B"], default="B", help="A=fixed stake, B=10%% Kapital")
    parser.add_argument("--leverage", type=float, default=20.0, help="Hebel (z.B. 1 oder 20)")
    parser.add_argument(
        "--variant",
        choices=["sl_tp", "tp_only", "sl_tp_exit", "tp_only_exit"],
        default="tp_only",
        help=(
            "Tradesimulation: "
            "sl_tp=SL+TP (Variante 1, sofort verbucht), "
            "tp_only=TP/Horizontende (Variante 2, sofort verbucht), "
            "sl_tp_exit=Variante 1 aber P&L erst am Exit verbucht, "
            "tp_only_exit=Variante 2 aber P&L erst am Exit verbucht (Variante 3)."
        ),
    )
    parser.add_argument("--stake-fixed", type=float, default=100.0, help="Einsatz pro Trade (Strategie A)")
    parser.add_argument("--frac-capital", type=float, default=0.10, help="Kapitalanteil pro Trade (Strategie B)")
    parser.add_argument("--start-capital", type=float, default=1000.0, help="Startkapital (Strategie B)")
    parser.add_argument("--output", type=Path, default=None, help="Output-Pfad (.png oder .pdf)")
    args = parser.parse_args()

    project_root = find_project_root()
    exp_a = args.exp_a
    exp_b = args.exp_b
    strategy: Strategy = args.strategy

    df_a = _compute_strategy_series(
        project_root,
        exp_a,
        strategy=strategy,
        variant=args.variant,
        leverage=args.leverage,
        stake_fixed_chf=args.stake_fixed,
        frac_capital=args.frac_capital,
        start_capital=args.start_capital,
    ).rename(columns={"pnl_cum": "pnl_a"})

    df_b = _compute_strategy_series(
        project_root,
        exp_b,
        strategy=strategy,
        variant=args.variant,
        leverage=args.leverage,
        stake_fixed_chf=args.stake_fixed,
        frac_capital=args.frac_capital,
        start_capital=args.start_capital,
    ).rename(columns={"pnl_cum": "pnl_b"})

    # Fairer Vergleich: nur gemeinsame Test-Daten
    merged = df_a.merge(df_b, on="date", how="inner").sort_values("date")
    if merged.empty:
        raise RuntimeError("Keine überlappenden Test-Daten zwischen den Experimenten gefunden.")

    merged["delta"] = merged["pnl_b"] - merged["pnl_a"]

    # Plot
    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(11.69, 6.2),
        gridspec_kw={"height_ratios": [3.0, 1.2]},
        sharex=True,
    )

    label_strat = "Strategie A (fixer Einsatz)" if strategy == "A" else "Strategie B (10% Kapital)"
    default_label_a = "ohne News" if str(exp_a).startswith("hp") and str(exp_b).startswith("hv") else None
    default_label_b = "mit News" if str(exp_a).startswith("hp") and str(exp_b).startswith("hv") else None
    label_a = args.label_a or default_label_a
    label_b = args.label_b or default_label_b
    suffix_a = f" ({label_a})" if label_a else ""
    suffix_b = f" ({label_b})" if label_b else ""
    if args.variant == "tp_only":
        variant_hint = "Variante 2 (TP-only, sofort)"
    elif args.variant == "sl_tp":
        variant_hint = "Variante 1 (SL+TP, sofort)"
    elif args.variant == "tp_only_exit":
        variant_hint = "Variante 3 (TP-only, Settlement am Exit)"
    else:
        variant_hint = "Variante 3 (SL+TP, Settlement am Exit)"
    title = (
        f"Vergleich: {label_strat} – kumulierter P&L als Punkte (Hebel {args.leverage:g}, Test, {variant_hint})\n"
        f"{exp_a}{suffix_a} vs {exp_b}{suffix_b}"
    )

    ax_top.scatter(
        merged["date"],
        merged["pnl_a"],
        s=18,
        alpha=0.85,
        color="#4c72b0",
        label=f"{exp_a}{suffix_a}",
    )
    ax_top.scatter(
        merged["date"],
        merged["pnl_b"],
        s=18,
        alpha=0.85,
        color="#c44e52",
        label=f"{exp_b}{suffix_b}",
    )
    ax_top.set_title(title, fontsize=12, weight="bold", pad=10)
    ax_top.set_ylabel("P&L (CHF)")
    ax_top.grid(alpha=0.25)
    ax_top.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax_top.legend(loc="upper left", fontsize=10, framealpha=0.9)

    ax_bot.bar(
        merged["date"],
        merged["delta"],
        width=2.0,
        color="#2ca02c",
        alpha=0.30,
    )
    ax_bot.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    delta_label_left = label_a or exp_a
    delta_label_right = label_b or exp_b
    ax_bot.set_ylabel(f"Δ ({delta_label_right} − {delta_label_left})\n(CHF)")
    ax_bot.set_xlabel("Datum")
    ax_bot.grid(alpha=0.15)
    ax_bot.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    _format_x_as_months(ax_bot)

    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.24, hspace=0.08)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Oben kumulierter Gewinn/Verlust als Punkte. Unten Balken: Differenz Δ = (B − A) je Datum.",
        fontsize=9,
    )

    if args.output is None:
        out_dir = project_root / "notebooks" / "results" / "final_two_stage" / "pdf"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_a = exp_a.replace(" ", "_")
        safe_b = exp_b.replace(" ", "_")
        out = out_dir / f"compare__{safe_a}__vs__{safe_b}__{strategy}_pnl_lev{args.leverage:g}.pdf"
    else:
        out = args.output
        out.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"[ok] Vergleichsgrafik gespeichert: {out}")


if __name__ == "__main__":
    main()
