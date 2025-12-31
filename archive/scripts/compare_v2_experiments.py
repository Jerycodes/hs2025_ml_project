"""Vergleicht zwei v2-Experimente (Labels/Predictions/Thresholds).

Beispiel:
    python3 -m scripts.compare_v2_experiments --exp-a <EXP_A> --exp-b <EXP_B>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.experiments.v2_config import DATA_PROCESSED_V2


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_labels(exp_id: str) -> pd.DataFrame:
    p = DATA_PROCESSED_V2 / "fx" / f"eurusd_labels__{exp_id}.csv"
    df = pd.read_csv(p, parse_dates=["Date"]).set_index("Date")
    return df


def load_results(exp_id: str) -> dict:
    p = DATA_PROCESSED_V2 / "results" / f"two_stage__{exp_id}.json"
    return _read_json(p)


def main() -> None:
    ap = argparse.ArgumentParser(description="v2 Experimente vergleichen.")
    ap.add_argument("--exp-a", required=True)
    ap.add_argument("--exp-b", required=True)
    ap.add_argument("--test-start", default="2025-01-01")
    args = ap.parse_args()

    la = load_labels(args.exp_a)
    lb = load_labels(args.exp_b)
    joined = la[["label"]].rename(columns={"label": "a"}).join(
        lb[["label"]].rename(columns={"label": "b"}), how="inner"
    )
    print("=== Labels (overlap) ===")
    print("rows:", len(joined))
    print("counts A:", joined["a"].value_counts().to_dict())
    print("counts B:", joined["b"].value_counts().to_dict())
    print("confusion (rows=A, cols=B):")
    print(pd.crosstab(joined["a"], joined["b"]))

    test = joined[joined.index >= pd.Timestamp(args.test_start)]
    print("\n=== Labels TEST (>= test_start) ===")
    print("rows:", len(test))
    print("confusion:")
    print(pd.crosstab(test["a"], test["b"]))

    ra = load_results(args.exp_a)
    rb = load_results(args.exp_b)
    print("\n=== Thresholds (combined trading) ===")
    for exp_id, res in [(args.exp_a, ra), (args.exp_b, rb)]:
        cfg = res.get("config", {})
        print("\n", exp_id)
        for k in ["signal_threshold_trade", "direction_threshold_down", "direction_threshold_up"]:
            print(f"  {k}: {cfg.get(k)}")
        cm = (res.get("combined_test", {}) or {}).get("confusion_matrix", [])
        if cm:
            print("  combined_test confusion_matrix:", cm)


if __name__ == "__main__":
    main()

