"""Vergleich: Yahoo-trainiertes Modell auf EODHD-Testdaten auswerten.

Dieses Skript trainiert das Zwei-Stufen-XGBoost-Modell auf dem
Yahoo-Experiment ``hp_long_h4_thr0p4pct_hit_1_2`` und wertet
anschließend das gleiche Modell auf dem Test-Split der EODHD-
Variante ``hp_long_eod_h4_thr0p4pct_hit_2`` aus.

Es nutzt dabei den einfachen Trainingscode aus
``src/models/train_xgboost_two_stage.py`` (ohne Tradesimulation),
um die Ursache der Unterschiede besser zu verstehen.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

# Projekt-Root auf den Modulpfad setzen, damit ``src`` importierbar ist,
# wenn das Skript direkt über ``python scripts/...`` aufgerufen wird.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.train_xgboost_two_stage import (
    get_feature_cols,
    split_train_val_test,
    train_xgb_binary,
    build_signal_targets,
    build_direction_targets,
)
from src.utils.io import DATA_PROCESSED


TEST_START = pd.to_datetime("2025-01-01")


def _load_dataset(exp_id: str) -> pd.DataFrame:
    """Lädt den Trainingsdatensatz für ein Experiment."""
    ds_path = (
        DATA_PROCESSED
        / "datasets"
        / f"eurusd_news_training__{exp_id}.csv"
    )
    df = pd.read_csv(ds_path, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def train_on_yahoo() -> tuple:
    """Trainiert das Zwei-Stufen-Modell auf dem Yahoo-Experiment."""
    exp_id_yahoo = "hp_long_h4_thr0p4pct_hit_1_2"
    df = _load_dataset(exp_id_yahoo)
    feature_cols = get_feature_cols(df)

    splits = split_train_val_test(df, TEST_START, train_frac_within_pretest=0.8)

    # Stufe 1: Signal
    y_train_signal = build_signal_targets(splits["train"])
    y_val_signal = build_signal_targets(splits["val"])

    X_train_signal = splits["train"][feature_cols]
    X_val_signal = splits["val"][feature_cols]

    model_signal = train_xgb_binary(
        X_train_signal,
        y_train_signal,
        X_val_signal,
        y_val_signal,
    )

    # Stufe 2: Richtung
    X_train_dir, y_train_dir = build_direction_targets(
        splits["train"], feature_cols=feature_cols
    )
    X_val_dir, y_val_dir = build_direction_targets(
        splits["val"], feature_cols=feature_cols
    )

    model_dir = train_xgb_binary(
        X_train_dir,
        y_train_dir,
        X_val_dir,
        y_val_dir,
        scale_pos_weight=1.0,
    )

    return model_signal, model_dir, feature_cols


def eval_on_eod(model_signal, model_dir, feature_cols: list[str]) -> None:
    """Wertet die Modelle auf dem EODHD-Testsplit aus."""
    exp_id_eod = "hp_long_eod_h4_thr0p4pct_hit_2"
    df_eod = _load_dataset(exp_id_eod)

    # Nur Test-Split (>= TEST_START)
    df_test = df_eod[df_eod["date"] >= TEST_START].copy()
    df_test = df_test.reset_index(drop=True)

    # Signal-Metrik (move vs neutral, Schwelle 0.5)
    y_test_signal = build_signal_targets(df_test)
    X_test = df_test[feature_cols]
    p_sig = model_signal.predict_proba(X_test)[:, 1]
    y_pred_sig = (p_sig >= 0.5).astype(int)

    print("=== EODHD – Stufe 1 (Signal, Yahoo-trainiertes Modell) ===")
    print("Confusion Matrix (rows=true, cols=pred):")
    print(confusion_matrix(y_test_signal, y_pred_sig))
    print("\nClassification Report:")
    print(
        classification_report(
            y_test_signal,
            y_pred_sig,
            target_names=["neutral", "move"],
            digits=3,
        )
    )

    # Richtungs-Metrik (down vs up), nur auf Bewegungstagen
    from src.models.train_xgboost_two_stage import build_direction_targets as build_dir

    X_test_dir, y_test_dir = build_dir(df_test, feature_cols=feature_cols)
    p_dir = model_dir.predict_proba(X_test_dir)[:, 1]
    y_pred_dir = (p_dir >= 0.5).astype(int)

    print("\n=== EODHD – Stufe 2 (Richtung, Yahoo-trainiertes Modell) ===")
    print("Confusion Matrix (rows=true, cols=pred):")
    print(confusion_matrix(y_test_dir, y_pred_dir))
    print("\nClassification Report:")
    print(
        classification_report(
            y_test_dir,
            y_pred_dir,
            target_names=["down", "up"],
            digits=3,
        )
    )


def main() -> None:
    print("[info] Trainiere Modelle auf Yahoo-Experiment hp_long_h4_thr0p4pct_hit_1_2 ...")
    model_signal, model_dir, feature_cols = train_on_yahoo()
    print("[ok] Training abgeschlossen.")

    print("\n[info] Werte Yahoo-Modelle auf EODHD-Testsplit (hp_long_eod_h4_thr0p4pct_hit_2) aus ...")
    eval_on_eod(model_signal, model_dir, feature_cols)


if __name__ == "__main__":
    main()
