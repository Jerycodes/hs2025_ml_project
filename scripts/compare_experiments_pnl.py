"""Vergleichsplot: price_only vs news+price (Final Two-Stage).

Erzeugt eine Grafik (PNG/PDF), die zwei Experimente übereinander legt
(z.B. price_only vs news+price) und unten Balken für die Gewinn-Differenz
über die Zeit zeigt.

Standard:
    - Strategie B (10% Kapital) als kumulierter P&L
    - Hebel 20

Beispiel:
    python3 -m scripts.compare_experiments_pnl \
        --exp-a hp_long_final_yahoo \
        --exp-b hv_long_final_yahoo \
        --strategy B \
        --leverage 20 \
        --output notebooks/results/final_two_stage/pdf/compare_hp_long_vs_hv_long_pnlB_lev20.pdf
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

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
)


Strategy = Literal["A", "B"]


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

    df["trade_return"] = [
        _compute_trade_return(dt, pred, true, fx, label_params)
        for dt, pred, true in zip(df["date"], df["combined_pred"], df["label_true"])
    ]

    is_trade = df["combined_pred"].isin(["up", "down"]).astype(int)
    df["is_trade"] = is_trade

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
    parser.add_argument("--strategy", choices=["A", "B"], default="B", help="A=fixed stake, B=10%% Kapital")
    parser.add_argument("--leverage", type=float, default=20.0, help="Hebel (z.B. 1 oder 20)")
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
        leverage=args.leverage,
        stake_fixed_chf=args.stake_fixed,
        frac_capital=args.frac_capital,
        start_capital=args.start_capital,
    ).rename(columns={"pnl_cum": "pnl_a"})

    df_b = _compute_strategy_series(
        project_root,
        exp_b,
        strategy=strategy,
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
    title = (
        f"Vergleich: {label_strat} – kumulierter P&L als Punkte (Hebel {args.leverage:g}, Test)\n"
        f"{exp_a} (ohne News) vs {exp_b} (mit News)"
    )

    ax_top.scatter(
        merged["date"],
        merged["pnl_a"],
        s=18,
        alpha=0.85,
        color="#4c72b0",
        label=f"{exp_a} (ohne News)",
    )
    ax_top.scatter(
        merged["date"],
        merged["pnl_b"],
        s=18,
        alpha=0.85,
        color="#c44e52",
        label=f"{exp_b} (mit News)",
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
    ax_bot.set_ylabel("Δ (mit − ohne)\n(CHF)")
    ax_bot.set_xlabel("Datum")
    ax_bot.grid(alpha=0.15)
    ax_bot.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    _format_x_as_months(ax_bot)

    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.24, hspace=0.08)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Oben kumulierter Gewinn/Verlust als Punkte. Unten Balken: Differenz Δ = (mit News − ohne News) je Datum.",
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

