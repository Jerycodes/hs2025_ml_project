"""Zwei-Stufen-Training mit XGBoost für EURUSD-News.

Stufe 1 (Signal-Modell):
    - Ziel: Vorhersagen, ob eine signifikante Bewegung stattfindet oder nicht.
    - Zielvariable: `signal` (0 = neutral, 1 = Bewegung up/down).

Stufe 2 (Richtungs-Modell):
    - Ziel: Wenn es eine Bewegung gibt, Richtung vorhersagen (up vs. down).
    - Zielvariable: `direction` (0 = down, 1 = up), nur für Tage mit signal == 1.

Zeitliche Splits:
    - Test: alle Daten ab 2025-01-01 (Zukunft, die das Modell nicht sieht).
    - Train/Val: alle Daten davor (2020–2024), chronologisch z.B. 80/20 geteilt.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

DATASET_PATH = Path("data/processed/datasets/eurusd_news_training.csv")

# Feature-Satz für beide Stufen (kann später erweitert/angepasst werden).
FEATURE_COLS = [
    "article_count",
    "avg_polarity",
    "avg_neg",
    "avg_neu",
    "avg_pos",
    "pos_share",
    "neg_share",
    "intraday_range_pct",
    "upper_shadow",
    "lower_shadow",
    "month",
    "quarter",
]


def load_dataset(path: Path) -> pd.DataFrame:
    """Lädt den vorbereiteten Datensatz und sortiert nach Datum."""
    df = pd.read_csv(path, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def split_train_val_test(
    df: pd.DataFrame,
    test_start: pd.Timestamp,
    train_frac_within_pretest: float = 0.8,
) -> Dict[str, pd.DataFrame]:
    """Teilt den Datensatz in Train/Val/Test, ohne die Zeit zu mischen.

    - Test-Split: alle Zeilen mit date >= test_start.
    - Train/Val: alle Zeilen mit date < test_start, darin nochmal 80/20.
    """
    df_pretest = df[df["date"] < test_start].copy()
    df_test = df[df["date"] >= test_start].copy()

    n_pre = len(df_pretest)
    train_end = int(n_pre * train_frac_within_pretest)

    train = df_pretest.iloc[:train_end].copy()
    val = df_pretest.iloc[train_end:].copy()

    return {"train": train, "val": val, "test": df_test}


def train_xgb_binary(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
    scale_pos_weight: float | None = None,
) -> xgb.XGBClassifier:
    """Trainiert ein binäres XGBoost-Modell mit einfachen Defaults.

    scale_pos_weight hilft bei stark unausgeglichenen Klassen:
        typischer Wert ≈ N_negative / N_positive.
    """
    if scale_pos_weight is None:
        # automatischer Vorschlag bei Binary Labels 0/1
        n_pos = (y_train == 1).sum()
        n_neg = (y_train == 0).sum()
        scale_pos_weight = n_neg / max(n_pos, 1)

    model = xgb.XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        max_depth=3,
        learning_rate=0.05,
        n_estimators=400,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=50,
        verbose=False,
    )
    return model


def evaluate_binary(
    name: str, model: xgb.XGBClassifier, X: pd.DataFrame, y_true: np.ndarray
) -> None:
    """Gibt Accuracy, Confusion-Matrix und Classification Report aus."""
    if len(X) == 0:
        print(f"[warn] Split {name} ist leer – keine Auswertung.")
        return

    y_pred = (model.predict_proba(X)[:, 1] >= 0.5).astype(int)
    acc = accuracy_score(y_true, y_pred)
    print(f"\n=== {name.upper()} ===")
    print(f"Accuracy: {acc:.3f}")
    print("Confusion Matrix (rows=true, cols=pred):")
    print(confusion_matrix(y_true, y_pred))
    print("Classification Report:")
    print(classification_report(y_true, y_pred, digits=3))


def build_signal_targets(df: pd.DataFrame) -> pd.Series:
    """Erstellt die Zielvariable für das Signal-Modell (0=neutral, 1=Bewegung)."""
    if "signal" not in df.columns:
        raise KeyError("Spalte 'signal' fehlt im Datensatz.")
    return df["signal"].astype(int)


def build_direction_targets(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    """Filtert auf Tage mit Bewegung und gibt X, y für das Richtungsmodell zurück."""
    if "direction" not in df.columns or "signal" not in df.columns:
        raise KeyError("Spalten 'signal' oder 'direction' fehlen im Datensatz.")

    df_move = df[df["signal"] == 1].copy()
    df_move = df_move[df_move["direction"].notna()].copy()
    y = df_move["direction"].astype(int).to_numpy()
    X = df_move[FEATURE_COLS]
    return X, y


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zwei-Stufen-XGBoost für EURUSD-News.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATASET_PATH,
        help="Pfad zur CSV mit Trainingsdaten.",
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_dataset(args.dataset)

    # Splits vorbereiten
    splits = split_train_val_test(
        df, pd.to_datetime(args.test_start), args.train_frac_pretest
    )

    # ---------- Stufe 1: Signal (neutral vs move) ----------
    print("\n===== STUFE 1: SIGNAL (neutral vs move) =====")

    y_train_signal = build_signal_targets(splits["train"])
    y_val_signal = build_signal_targets(splits["val"])
    y_test_signal = build_signal_targets(splits["test"])

    X_train_signal = splits["train"][FEATURE_COLS]
    X_val_signal = splits["val"][FEATURE_COLS]
    X_test_signal = splits["test"][FEATURE_COLS]

    model_signal = train_xgb_binary(
        X_train_signal, y_train_signal, X_val_signal, y_val_signal
    )

    for split_name, X, y in [
        ("train", X_train_signal, y_train_signal),
        ("val", X_val_signal, y_val_signal),
        ("test", X_test_signal, y_test_signal),
    ]:
        evaluate_binary(split_name, model_signal, X, y)

    # ---------- Stufe 2: Richtung (up vs down, nur wenn Bewegung) ----------
    print("\n===== STUFE 2: RICHTUNG (up vs down, nur signal==1) =====")

    X_train_dir, y_train_dir = build_direction_targets(splits["train"])
    X_val_dir, y_val_dir = build_direction_targets(splits["val"])
    X_test_dir, y_test_dir = build_direction_targets(splits["test"])

    model_dir = train_xgb_binary(
        X_train_dir, y_train_dir, X_val_dir, y_val_dir, scale_pos_weight=1.0
    )

    for split_name, X, y in [
        ("train", X_train_dir, y_train_dir),
        ("val", X_val_dir, y_val_dir),
        ("test", X_test_dir, y_test_dir),
    ]:
        evaluate_binary(split_name, model_dir, X, y)

    # ---------- kombinierte Auswertung: 3-Klassen-Label auf Test ----------
    print("\n===== KOMBINIERTE TEST-AUSWERTUNG (neutral/up/down) =====")
    X_test_all = splits["test"][FEATURE_COLS]
    # Vorhersage: zuerst Signal, dann Richtung für signal==1
    signal_pred = (model_signal.predict_proba(X_test_all)[:, 1] >= 0.5).astype(int)
    dir_pred = (model_dir.predict_proba(X_test_all)[:, 1] >= 0.5).astype(int)

    # Kombiniertes Label
    combined_pred = np.where(
        signal_pred == 0,
        "neutral",
        np.where(dir_pred == 1, "up", "down"),
    )
    combined_true = splits["test"]["label"].to_numpy()

    print("Confusion Matrix (rows=true, cols=pred):")
    print(confusion_matrix(combined_true, combined_pred, labels=["neutral", "up", "down"]))
    print("Classification Report:")
    print(classification_report(combined_true, combined_pred, digits=3))


if __name__ == "__main__":
    main()
