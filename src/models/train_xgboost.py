"""Trainiert ein XGBoost-Modell auf den News-Features.

Ablauf in diesem Skript:

1. Den vorbereiteten Datensatz `eurusd_news_training.csv` laden.
2. Die Ziel-Labels (`up`, `down`, `neutral`) in Zahlen (0/1/2) kodieren.
3. Den Datensatz zeitlich sortiert in Train/Validation/Test aufteilen.
4. Einen XGBoost-Klassifikator nur auf den News-Features trainieren.
5. Das Modell auf allen drei Splits auswerten (Accuracy + Berichte).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

DATASET_PATH = Path("data/processed/datasets/eurusd_news_training.csv")
# Diese Spalten verwenden wir als Eingabefeatures für das Modell.
FEATURE_COLS = ["article_count", "avg_polarity", "avg_neg", "avg_neu", "avg_pos"]


def load_dataset(path: Path) -> pd.DataFrame:
    """Lädt den vorbereiteten Datensatz und sortiert nach Datum.

    Erwartet eine CSV mit mindestens:
    - `date` (Datum),
    - `label` (up/down/neutral),
    - News-Feature-Spalten (z. B. `article_count`, `avg_polarity`).
    """
    # CSV einlesen; `parse_dates` sorgt dafür, dass wir später nicht selbst konvertieren müssen.
    df = pd.read_csv(path, parse_dates=["date"])
    # Chronologisches Sortieren verhindert, dass spätere Splits (train/val/test) die Zeit durcheinanderbringen.
    return df.sort_values("date").reset_index(drop=True)


def chronological_split(
    df: pd.DataFrame, train_frac: float, val_frac: float
) -> Dict[str, pd.DataFrame]:
    """Teilt den DataFrame nach festen Anteilen auf, um Data Leakage zu vermeiden.

    Wichtig: Wir mischen die Zeilen NICHT, sondern schneiden vorn/hinten ab,
    damit das Modell nicht auf zukünftigen Daten trainiert und in der Vergangenheit
    getestet wird (typischer Fehler bei Zeitreihen).
    """
    if not 0 < train_frac < 1:
        raise ValueError("train_frac muss zwischen 0 und 1 liegen.")
    if not 0 <= val_frac < 1:
        raise ValueError("val_frac muss zwischen 0 und 1 liegen.")
    if train_frac + val_frac >= 1:
        raise ValueError("train_frac + val_frac muss kleiner als 1 sein.")

    # Gesamtanzahl der Zeilen
    n = len(df)
    # Grenze für das Trainingsfenster (z. B. 70 % der Daten)
    train_end = int(n * train_frac)  # letzter Index für das Training
    # Grenze für das Validierungsfenster (z. B. nächste 15 % der Daten)
    val_end = int(n * (train_frac + val_frac))  # letztes Element der Validation

    # Wir kopieren die Slices, damit spätere Änderungen nicht auf das Original wirken.
    return {
        "train": df.iloc[:train_end].copy(),
        "val": df.iloc[train_end:val_end].copy(),
        "test": df.iloc[val_end:].copy(),
    }


def train_model(X_train: pd.DataFrame, y_train: np.ndarray) -> xgb.XGBClassifier:
    """Initialisiert und trainiert einen einfachen XGBoost-Klassifikator.

    X_train: Matrix aus News-Features.
    y_train: Ganzzahlige Klassenlabels (0, 1, 2).
    """
    model = xgb.XGBClassifier(
        objective="multi:softprob",  # mehrklassige Klassifikation, Ausgabe sind Wahrscheinlichkeiten
        num_class=len(np.unique(y_train)),  # Anzahl der Zielklassen (up/down/neutral)
        eval_metric="mlogloss",  # Standard-Loss für Multi-Class
        max_depth=3,  # flach halten, um Overfitting bei kleinem Datensatz zu vermeiden
        learning_rate=0.05,
        n_estimators=400,
        subsample=0.9,  # leichtes Bagging für Robustheit
        colsample_bytree=0.9,
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model


def evaluate_split(
    name: str,
    model: xgb.XGBClassifier,
    X: pd.DataFrame,
    y_true: np.ndarray,
    encoder: LabelEncoder,
) -> None:
    """Berechnet Accuracy, Confusion-Matrix und Classification Report.

    - `name` steuert nur die Überschrift (Train/Val/Test).
    - `encoder` wird verwendet, um aus 0/1/2 wieder lesbare Labels zu machen.
    """
    if len(X) == 0:
        print(f"[warn] Split {name} ist leer – keine Auswertung.")
        return
    y_pred = model.predict(X)
    acc = accuracy_score(y_true, y_pred)
    print(f"\n=== {name.upper()} ===")
    print(f"Accuracy: {acc:.3f}")
    y_true_labels = encoder.inverse_transform(y_true)
    y_pred_labels = encoder.inverse_transform(y_pred)
    print("Confusion Matrix:")
    print(confusion_matrix(y_true_labels, y_pred_labels, labels=encoder.classes_))
    print("Classification Report:")
    print(classification_report(y_true_labels, y_pred_labels))


def parse_args() -> argparse.Namespace:
    """CLI-Argumente, damit wir flexibel mit Pfad/Split umgehen können."""
    parser = argparse.ArgumentParser(description="Trainiert einen XGBoost-Klassifikator.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATASET_PATH,
        help="Pfad zur CSV mit Trainingsdaten.",
    )
    parser.add_argument("--train-frac", type=float, default=0.7, help="Anteil Training.")
    parser.add_argument("--val-frac", type=float, default=0.15, help="Anteil Validierung.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 1) Daten + Labels laden
    df = load_dataset(args.dataset)

    # 2) Labels (up/down/neutral) in 0/1/2 kodieren
    encoder = LabelEncoder()
    df["label_encoded"] = encoder.fit_transform(df["label"])

    # 3) Chronologischen Split vorbereiten
    splits = chronological_split(df, args.train_frac, args.val_frac)
    X_train = splits["train"][FEATURE_COLS]
    y_train = splits["train"]["label_encoded"].to_numpy()

    # 4) Modell auf Trainingssplit fitten
    model = train_model(X_train, y_train)

    # 5) Auf allen Splits evaluieren
    for split_name in ("train", "val", "test"):
        X = splits[split_name][FEATURE_COLS]
        y = splits[split_name]["label_encoded"].to_numpy()
        evaluate_split(split_name, model, X, y, encoder)


if __name__ == "__main__":
    main()
