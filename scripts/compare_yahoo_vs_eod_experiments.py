"""Vergleicht Yahoo- vs. EODHD-Experimente (FX-Daten, Labels, Training-Outputs).

Fokus: hp_long_* Experimente, aber funktioniert generell, solange:

- `data/processed/experiments/<EXP_ID>_config.json` existiert (label_params)
- `data/processed/fx/eurusd_labels__<EXP_ID>.csv` existiert (Label-CSV)
- Optional: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>.json`
            `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_predictions.csv`

Beispiel:
    python3 -m scripts.compare_yahoo_vs_eod_experiments --exp-a hp_long_yahoo_2 --exp-b hp_long_eod_1
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

try:
    from sklearn.metrics import roc_auc_score
except Exception:  # pragma: no cover
    roc_auc_score = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"


@dataclass(frozen=True)
class Experiment:
    exp_id: str
    label_params: Dict[str, Any]


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_experiment(exp_id: str) -> Experiment:
    safe = exp_id.replace(" ", "_")
    cfg_path = DATA_PROCESSED / "experiments" / f"{safe}_config.json"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Experiment-Config nicht gefunden: {cfg_path}")
    cfg = _read_json(cfg_path)
    label_params = cfg.get("label_params", {})
    if not isinstance(label_params, dict):
        raise ValueError(f"Unerwartetes Format in {cfg_path}: label_params ist kein dict.")
    return Experiment(exp_id=exp_id, label_params=label_params)


def load_prices(price_source: str, *, drop_weekends: bool) -> pd.DataFrame:
    if price_source == "yahoo":
        path = DATA_RAW / "fx" / "EURUSDX.csv"
        df = pd.read_csv(path)
        # YFinance schreibt Metazeilen vor die eigentlichen Daten.
        if "Date" not in df.columns and df.columns[0] == "Price":
            df.columns = ["Date", "Close", "High", "Low", "Open", "Volume"]
    elif price_source == "eodhd":
        path = DATA_RAW / "fx" / "EURUSDX_eodhd.csv"
        df = pd.read_csv(path)
    else:
        raise ValueError("price_source muss 'yahoo' oder 'eodhd' sein.")

    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
    df = df[df["Date"].notna()].sort_values("Date").set_index("Date")

    for col in ["Close", "High", "Low", "Open", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if drop_weekends:
        df = df[df.index.dayofweek < 5]

    return df


def _corr(a: pd.Series, b: pd.Series) -> float:
    joined = pd.concat([a, b], axis=1, join="inner").dropna()
    if len(joined) < 2:
        return float("nan")
    return float(joined.corr().iloc[0, 1])


def compare_fx(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    *,
    horizon_days: int,
    threshold: float,
) -> None:
    idx = df_a.index.intersection(df_b.index)
    if len(idx) == 0:
        print("[fx] keine überlappenden Tage.")
        return

    a_close = df_a.loc[idx, "Close"]
    b_close = df_b.loc[idx, "Close"]

    print("[fx] overlap days:", len(idx))
    print("[fx] close corr:", f"{_corr(a_close, b_close):.3f}")

    # Daily returns: erst pro Quelle berechnen, dann auf gemeinsamen Dates joinen.
    a_ret = df_a["Close"].pct_change().rename("a_ret")
    b_ret = df_b["Close"].pct_change().rename("b_ret")
    joined_ret = pd.concat([a_ret, b_ret], axis=1, join="inner").dropna()
    if len(joined_ret):
        sign_mismatch = (
            (np.sign(joined_ret["a_ret"]) != np.sign(joined_ret["b_ret"]))
            & (joined_ret["a_ret"] != 0)
            & (joined_ret["b_ret"] != 0)
        ).mean()
        print("[fx] daily return corr:", f"{joined_ret.corr().iloc[0,1]:.3f}")
        print("[fx] daily sign mismatch rate:", f"{float(sign_mismatch):.3f}")

    # Forward return für Label-Horizont (N Schritte in den Daten).
    a_fwd = (df_a["Close"].shift(-horizon_days) / df_a["Close"] - 1).rename("a_fwd")
    b_fwd = (df_b["Close"].shift(-horizon_days) / df_b["Close"] - 1).rename("b_fwd")
    joined_fwd = pd.concat([a_fwd, b_fwd], axis=1, join="inner").dropna()
    if len(joined_fwd):
        up_mm = ((joined_fwd["a_fwd"] >= threshold) != (joined_fwd["b_fwd"] >= threshold)).mean()
        dn_mm = ((joined_fwd["a_fwd"] <= -threshold) != (joined_fwd["b_fwd"] <= -threshold)).mean()
        print("[fx] fwd return corr:", f"{joined_fwd.corr().iloc[0,1]:.3f}", f"(h={horizon_days})")
        print("[fx] thr mismatch up/dn:", f"{float(up_mm):.3f}", f"{float(dn_mm):.3f}", f"(thr={threshold:.3f})")


def load_labels_csv(exp_id: str) -> pd.DataFrame:
    path = DATA_PROCESSED / "fx" / f"eurusd_labels__{exp_id}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Label-CSV nicht gefunden: {path}")
    return pd.read_csv(path, parse_dates=["Date"]).set_index("Date")


def compare_labels(
    lab_a: pd.DataFrame,
    lab_b: pd.DataFrame,
    *,
    test_start: str,
) -> None:
    joined = lab_a[["label", "lookahead_return"]].rename(
        columns={"label": "label_a", "lookahead_return": "ret_a"}
    ).join(
        lab_b[["label", "lookahead_return"]].rename(
            columns={"label": "label_b", "lookahead_return": "ret_b"}
        ),
        how="inner",
    )
    print("[labels] overlap rows:", len(joined))
    if len(joined) == 0:
        return
    print("[labels] counts A:", joined["label_a"].value_counts().to_dict())
    print("[labels] counts B:", joined["label_b"].value_counts().to_dict())
    print("[labels] confusion (rows=A, cols=B):")
    print(pd.crosstab(joined["label_a"], joined["label_b"]))

    test = joined[joined.index >= pd.Timestamp(test_start)]
    print("[labels] TEST rows:", len(test), f"(>= {test_start})")
    if len(test):
        print("[labels] TEST counts A:", test["label_a"].value_counts().to_dict())
        print("[labels] TEST counts B:", test["label_b"].value_counts().to_dict())
        print("[labels] TEST confusion:")
        print(pd.crosstab(test["label_a"], test["label_b"]))
        mism = test[test["label_a"] != test["label_b"]]
        print("[labels] TEST mismatches:", len(mism))


def load_final_results(exp_id: str) -> Dict[str, Any] | None:
    safe = exp_id.replace(" ", "_")
    path = (
        PROJECT_ROOT
        / "notebooks"
        / "results"
        / "final_two_stage"
        / f"two_stage_final__{safe}.json"
    )
    if not path.is_file():
        return None
    return _read_json(path)


def summarize_training_from_results(final: Dict[str, Any]) -> None:
    cfg = final.get("config", {})
    if not cfg:
        return
    print("[train] dataset_path:", cfg.get("dataset_path"))
    print("[train] feature_mode:", cfg.get("feature_mode"))
    print("[train] test_start:", cfg.get("test_start"))
    print("[train] train_frac_within_pretest:", cfg.get("train_frac_within_pretest"))
    print("[train] signal_threshold_trade:", cfg.get("signal_threshold_trade"))
    print(
        "[train] direction_threshold_down/up:",
        cfg.get("direction_threshold_down"),
        cfg.get("direction_threshold_up"),
    )


def summarize_predictions(exp_id: str) -> None:
    pred_path = (
        PROJECT_ROOT
        / "notebooks"
        / "results"
        / "final_two_stage"
        / f"two_stage_final__{exp_id}_predictions.csv"
    )
    if not pred_path.is_file():
        print("[pred] keine Predictions-CSV:", pred_path)
        return

    df = pd.read_csv(pred_path, parse_dates=["date"])
    print("[pred] rows:", len(df))
    print("[pred] combined_pred:", df["combined_pred"].value_counts().to_dict())
    print("[pred] signal_pred:", df["signal_pred"].value_counts().to_dict())

    trade = df[df["signal_pred"] == 1]
    if len(trade):
        print("[pred] signal_pred==1 rows:", len(trade))
        for lab in ["up", "down", "neutral"]:
            sub = trade[trade["label_true"] == lab]
            if len(sub) == 0:
                continue
            s = sub["direction_prob_up"]
            print(
                f"[pred] dir_prob_up stats ({lab}, trade): "
                f"n={len(sub)} min={float(s.min()):.3f} med={float(s.median()):.3f} "
                f"max={float(s.max()):.3f} std={float(s.std()):.3f}"
            )

    if roc_auc_score is not None:
        move = df[df["label_true"].isin(["up", "down"])]
        if len(move):
            y = (move["label_true"] == "up").astype(int)
            auc = roc_auc_score(y, move["direction_prob_up"])
            print("[pred] direction AUC on test(move):", f"{float(auc):.3f}", "n=", len(move))


def main() -> None:
    parser = argparse.ArgumentParser(description="Vergleicht Yahoo- vs EODHD-Experimente.")
    parser.add_argument("--exp-a", type=str, required=True, help="z.B. hp_long_yahoo_2")
    parser.add_argument("--exp-b", type=str, required=True, help="z.B. hp_long_eod_1")
    parser.add_argument(
        "--test-start",
        type=str,
        default="2025-01-01",
        help="Teststart für Label-Auswertungen (YYYY-MM-DD).",
    )
    args = parser.parse_args()

    exp_a = load_experiment(args.exp_a)
    exp_b = load_experiment(args.exp_b)

    def get_source_params(label_params: Dict[str, Any]) -> Tuple[str, bool]:
        src = str(label_params.get("price_source", "yahoo"))
        drop = bool(label_params.get("drop_weekends", False))
        return src, drop

    src_a, drop_a = get_source_params(exp_a.label_params)
    src_b, drop_b = get_source_params(exp_b.label_params)

    h_a = int(exp_a.label_params.get("horizon_days", 4))
    h_b = int(exp_b.label_params.get("horizon_days", 4))
    if h_a != h_b:
        print(
            f"[warn] horizon_days unterschiedlich: A={h_a}, B={h_b} -> "
            "nutze min() für FX-Forward-Checks"
        )
    horizon = min(h_a, h_b)
    thr = float(exp_a.label_params.get("up_threshold", 0.0))

    print("=== EXP A ===", exp_a.exp_id)
    print("label_params:", exp_a.label_params)
    print("=== EXP B ===", exp_b.exp_id)
    print("label_params:", exp_b.label_params)

    print("\n=== 1) FX-Vergleich ===")
    df_a = load_prices(src_a, drop_weekends=drop_a)
    df_b = load_prices(src_b, drop_weekends=drop_b)
    compare_fx(df_a, df_b, horizon_days=horizon, threshold=thr)

    print("\n=== 2) Label-Vergleich (aus gespeicherten CSVs) ===")
    lab_a = load_labels_csv(exp_a.exp_id)
    lab_b = load_labels_csv(exp_b.exp_id)
    compare_labels(lab_a, lab_b, test_start=args.test_start)

    print("\n=== 3) Training/Thresholds (Final-JSON, falls vorhanden) ===")
    final_a = load_final_results(exp_a.exp_id)
    final_b = load_final_results(exp_b.exp_id)
    if final_a is None:
        print(f"[train] kein Final-JSON für {exp_a.exp_id}")
    else:
        print(f"[train] {exp_a.exp_id}")
        summarize_training_from_results(final_a)
    if final_b is None:
        print(f"[train] kein Final-JSON für {exp_b.exp_id}")
    else:
        print(f"[train] {exp_b.exp_id}")
        summarize_training_from_results(final_b)

    print("\n=== 4) Test-Predictions (Final, falls vorhanden) ===")
    print(f"[pred] {exp_a.exp_id}")
    summarize_predictions(exp_a.exp_id)
    print(f"[pred] {exp_b.exp_id}")
    summarize_predictions(exp_b.exp_id)


if __name__ == "__main__":
    main()

