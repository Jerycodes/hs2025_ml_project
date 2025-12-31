"""Threshold-Tuning für die Up-/Down-Only-XGBoost-Modelle.

Dieses Skript spiegelt im Kern die Logik der Notebooks
`2a_train_xgboost_up_only.ipynb` und
`2b_train_xgboost_down_only.ipynb` wider:

- lädt einen vorbereiteten Trainingsdatensatz für eine bestimmte ``EXP_ID``
- erzeugt zeitliche Train/Val/Test-Splits
- trainiert je ein Binärmodell für
  - up vs. not-up
  - down vs. not-down
- berechnet für ein Gitter von Schwellenwerten (thresholds) die
  Kennzahlen der positiven Klasse (precision/recall/f1) auf
  Validation- und Test-Split

Ausgabe ist eine kleine Tabelle pro Richtung, so dass man
z.B. eine Schwelle mit maximalem F1 auf dem Val-Split wählen kann.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

from src.models.train_xgboost_two_stage import load_dataset, split_train_val_test, train_xgb_binary, get_feature_cols


def build_up_target(df: pd.DataFrame) -> np.ndarray:
    """Zielvariable: 1 = up, 0 = nicht-up (neutral oder down)."""
    return (df["label"] == "up").astype(int).to_numpy()


def build_down_target(df: pd.DataFrame) -> np.ndarray:
    """Zielvariable: 1 = down, 0 = nicht-down (neutral oder up)."""
    return (df["label"] == "down").astype(int).to_numpy()


def compute_threshold_grid(
    y_true_val: np.ndarray,
    p_val: np.ndarray,
    y_true_test: np.ndarray,
    p_test: np.ndarray,
    thresholds: np.ndarray,
) -> pd.DataFrame:
    """Berechnet precision/recall/f1 der positiven Klasse für ein Threshold-Gitter.

    Die Ausgabe hat eine Zeile pro Threshold und Spalten für Val/Test.
    """
    rows: List[Dict[str, float]] = []
    for thr in thresholds:
        row: Dict[str, float] = {"threshold": float(thr)}
        for split_name, y_true, p in [
            ("val", y_true_val, p_val),
            ("test", y_true_test, p_test),
        ]:
            y_pred = (p >= thr).astype(int)
            rep = classification_report(
                y_true, y_pred, output_dict=True, digits=3
            )["1"]  # positive Klasse = 1
            row[f"precision_{split_name}"] = float(rep["precision"])
            row[f"recall_{split_name}"] = float(rep["recall"])
            row[f"f1_{split_name}"] = float(rep["f1-score"])
        rows.append(row)

    return pd.DataFrame(rows)


def tune_direction(
    df_splits: Dict[str, pd.DataFrame],
    direction: str,
    thresholds: np.ndarray,
) -> Tuple[pd.DataFrame, float]:
    """Trainiert ein Up- oder Down-Only-Modell und berechnet Threshold-Kurve.

    Gibt die Metriktabelle und den besten Threshold (max f1_val) zurück.
    """
    if direction not in {"up", "down"}:
        raise ValueError("direction muss 'up' oder 'down' sein.")

    if direction == "up":
        build_target = build_up_target
        label_name = "up"
    else:
        build_target = build_down_target
        label_name = "down"

    y_train = build_target(df_splits["train"])
    y_val = build_target(df_splits["val"])
    y_test = build_target(df_splits["test"])

    feature_cols = get_feature_cols(df_splits["train"])
    X_train = df_splits["train"][feature_cols]
    X_val = df_splits["val"][feature_cols]
    X_test = df_splits["test"][feature_cols]

    model = train_xgb_binary(X_train, y_train, X_val, y_val)

    p_val = model.predict_proba(X_val)[:, 1]
    p_test = model.predict_proba(X_test)[:, 1]

    grid = compute_threshold_grid(y_val, p_val, y_test, p_test, thresholds)

    # Beste Schwelle nach F1 auf dem Val-Split
    best_idx = int(grid["f1_val"].idxmax())
    best_thr = float(grid.loc[best_idx, "threshold"])

    print(f"\n=== {label_name.upper()} vs NOT-{label_name.upper()} ===")
    print("Threshold-Kurve (Top-10 nach f1_val):")
    display_cols = [
        "threshold",
        "precision_val",
        "recall_val",
        "f1_val",
        "precision_test",
        "recall_test",
        "f1_test",
    ]
    top = grid.sort_values("f1_val", ascending=False)[display_cols].head(10)
    print(top.to_string(index=False))
    print(
        f"\n[Empfehlung] Beste Schwelle (nach F1_val) "
        f"für Klasse '{label_name}': {best_thr:.2f}"
    )

    return grid, best_thr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Threshold-Tuning für Up-/Down-Only-XGBoost-Modelle."
    )
    parser.add_argument(
        "--exp-id",
        type=str,
        default="v4_h4_thr0p5pct_tolerant0p3pct",
        help=(
            "Experiment-/Label-ID, z.B. v4_h4_thr0p5pct_tolerant0p3pct. "
            "Es wird die Datei "
            "data/processed/datasets/eurusd_news_training__<EXP_ID>.csv geladen."
        ),
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help=(
            "Optionaler expliziter Pfad zur Datensatz-CSV. "
            "Wenn gesetzt, überschreibt dies --exp-id."
        ),
    )
    parser.add_argument(
        "--test-start",
        type=str,
        default="2025-01-01",
        help="Datum, ab dem Daten als Test-Split gelten (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--train-frac-pretest",
        type=float,
        default=0.8,
        help="Anteil Training innerhalb des Zeitraums vor test-start.",
    )
    parser.add_argument(
        "--thr-min",
        type=float,
        default=0.1,
        help="Untere Grenze des Threshold-Gitters (inklusive).",
    )
    parser.add_argument(
        "--thr-max",
        type=float,
        default=0.9,
        help="Obere Grenze des Threshold-Gitters (inklusive).",
    )
    parser.add_argument(
        "--thr-step",
        type=float,
        default=0.05,
        help="Schrittweite für das Threshold-Gitter.",
    )
    parser.add_argument(
        "--directions",
        type=str,
        choices=["up", "down", "both"],
        default="both",
        help="Welche Richtung(en) analysiert werden sollen.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.dataset is not None:
        dataset_path = args.dataset
    else:
        dataset_path = (
            Path("data")
            / "processed"
            / "datasets"
            / f"eurusd_news_training__{args.exp_id}.csv"
        )

    print("Datensatz:", dataset_path)
    df = load_dataset(dataset_path)

    splits = split_train_val_test(
        df,
        pd.to_datetime(args.test_start),
        train_frac_within_pretest=args.train_frac_pretest,
    )

    thresholds = np.arange(args.thr_min, args.thr_max + 1e-8, args.thr_step)
    print(
        f"Threshold-Gitter: {args.thr_min:.2f}..{args.thr_max:.2f} "
        f"in Schritten von {args.thr_step:.2f} "
        f"({len(thresholds)} Werte)"
    )

    if args.directions in ("up", "both"):
        tune_direction(splits, direction="up", thresholds=thresholds)

    if args.directions in ("down", "both"):
        tune_direction(splits, direction="down", thresholds=thresholds)


if __name__ == "__main__":
    main()
