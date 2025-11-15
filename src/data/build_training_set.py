"""Verknüpft News-Features mit EURUSD-Labels zu einem Trainingsdatensatz."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.io import DATA_PROCESSED


def load_news_features(path: Path | None = None) -> pd.DataFrame:
    """Lädt die zuvor erzeugten Tagesfeatures aus data/processed/news."""
    if path is None:
        path = DATA_PROCESSED / "news" / "eodhd_daily_features.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    return df


def load_labels(path: Path | None = None) -> pd.DataFrame:
    """Lädt die EURUSD-Labels und benennt die Datums-Spalte für den Merge um."""
    if path is None:
        path = DATA_PROCESSED / "fx" / "eurusd_labels.csv"
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.rename(columns={"Date": "date"})
    return df


def build_training_dataframe() -> pd.DataFrame:
    """Merged die News-Features mit den FX-Labels."""
    news = load_news_features()
    labels = load_labels()
    merged = labels.merge(news, on="date", how="inner")
    return merged


def save_training_dataframe(df: pd.DataFrame, path: Path | None = None) -> Path:
    """Speichert das Training-CSV unter data/processed/datasets/."""
    if path is None:
        path = DATA_PROCESSED / "datasets" / "eurusd_news_training.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def main() -> None:
    merged = build_training_dataframe()
    # Für das spätere Modell reichen News-Features + Label + Lookahead.
    cols = [
        "date",
        "label",
        "lookahead_return",
        "article_count",
        "avg_polarity",
        "avg_neg",
        "avg_neu",
        "avg_pos",
    ]
    merged = merged[cols]
    out_path = save_training_dataframe(merged)
    print(f"[ok] Trainingsdatensatz gespeichert unter {out_path} ({merged.shape[0]} Zeilen)")


if __name__ == "__main__":
    main()
