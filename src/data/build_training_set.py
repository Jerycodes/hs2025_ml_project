"""Verknüpft News-Features mit EURUSD-Labels zu einem Trainingsdatensatz."""

from __future__ import annotations

from pathlib import Path
import argparse

import pandas as pd

from src.utils.io import DATA_PROCESSED


def load_news_features(path: Path | None = None) -> pd.DataFrame:
    """Lädt die zuvor erzeugten Tagesfeatures aus data/processed/news."""
    if path is None:
        path = DATA_PROCESSED / "news" / "eodhd_daily_features.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    return df


def load_labels(path: Path | None = None, exp_id: str | None = None) -> pd.DataFrame:
    """Lädt die EURUSD-Labels und benennt die Datums-Spalte für den Merge um.

    Wenn ``exp_id`` gesetzt ist, wird versucht, die Datei
    ``eurusd_labels__<exp_id>.csv`` zu lesen. Andernfalls wird die
    Standarddatei ``eurusd_labels.csv`` verwendet.
    """
    if path is None:
        base_dir = DATA_PROCESSED / "fx"
        if exp_id:
            safe_suffix = exp_id.replace(" ", "_")
            path = base_dir / f"eurusd_labels__{safe_suffix}.csv"
        else:
            path = base_dir / "eurusd_labels.csv"
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.rename(columns={"Date": "date"})
    return df


def build_training_dataframe(exp_id: str | None = None) -> pd.DataFrame:
    """Merged die News-Features mit den FX-Labels.

    Parameter:
    - exp_id: Optionale Experiment-ID, um eine bestimmte Label-Datei
      (eurusd_labels__<exp_id>.csv) zu verwenden.
    """
    news = load_news_features()
    labels = load_labels(exp_id=exp_id)
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
    """Erzeugt den Trainingsdatensatz und legt Varianten-Dateien an.

    Standardfall:
        - schreibt nach data/processed/datasets/eurusd_news_training.csv

    Mit ``--exp-id``:
        - verwendet die Label-Datei eurusd_labels__<exp_id>.csv
        - legt zusätzlich eurusd_news_training__<exp_id>.csv an
    """

    parser = argparse.ArgumentParser(description="Trainingsdatensatz aus Labels + News bauen.")
    parser.add_argument(
        "--exp-id",
        type=str,
        default=None,
        help=(
            "Experiment-ID, z. B. 'v1_h4_thr0p5pct_strict'. "
            "Wenn gesetzt, wird die passende Label-Datei verwendet "
            "und der Trainingsdatensatz zusätzlich mit dieser ID archiviert."
        ),
    )
    args = parser.parse_args()

    merged = build_training_dataframe(exp_id=args.exp_id)

    # Zusätzliche Zielvariablen für das Zwei-Stufen-Modell:
    # signal: 1 = Bewegung (up/down), 0 = neutral.
    merged["signal"] = (merged["label"] != "neutral").astype(int)

    # direction: nur für Tage mit Bewegung relevant.
    # 1 = up, 0 = down, NaN = neutral (wird für das Richtungsmodell ignoriert).
    direction_map = {"down": 0, "up": 1}
    merged["direction"] = merged["label"].map(direction_map)

    # Kalender-basierte Zusatzfeatures:
    # Monat (1–12), Kalenderwoche (ISO-Standard) und Quartal (1–4).
    merged["month"] = merged["date"].dt.month
    iso = merged["date"].dt.isocalendar()
    merged["week"] = iso.week.astype(int)
    merged["quarter"] = merged["date"].dt.quarter

    # Preisbasierte Tagesfeatures aus High/Low/Open/Close:
    # 1) Intraday-Spanne in absoluten Punkten.
    merged["intraday_range"] = merged["High"] - merged["Low"]
    # 2) Intraday-Spanne relativ zum Schlusskurs (Volatilität eines Tages).
    merged["intraday_range_pct"] = merged["intraday_range"] / merged["Close"]
    # 3) Kerzenkoerper: Close minus Open (positiv = bullische Kerze).
    merged["body"] = merged["Close"] - merged["Open"]
    merged["body_pct"] = merged["body"] / merged["Close"]
    # 4) Docht/Lunte: Abstand vom Kerzenkoerper zu High/Low.
    merged["upper_shadow"] = merged["High"] - merged[["Open", "Close"]].max(axis=1)
    merged["lower_shadow"] = merged[["Open", "Close"]].min(axis=1) - merged["Low"]

    # Sentiment-basierte abgeleitete Features:
    # Anteil positiver / negativer Sentiment-Anteile (auf Basis avg_pos/avg_neg).
    sentiment_denom = (merged["avg_pos"] + merged["avg_neg"]).replace(0, 1e-6)
    merged["pos_share"] = merged["avg_pos"] / sentiment_denom
    merged["neg_share"] = merged["avg_neg"] / sentiment_denom

    # Für das spätere Modell reichen News-Features + Label + Lookahead + neue Targets.
    cols = [
        "date",
        "label",
        "signal",
        "direction",
        "month",
        "week",
        "quarter",
        "intraday_range",
        "intraday_range_pct",
        "body",
        "body_pct",
        "upper_shadow",
        "lower_shadow",
        "pos_share",
        "neg_share",
        "lookahead_return",
        "article_count",
        "avg_polarity",
        "avg_neg",
        "avg_neu",
        "avg_pos",
    ]
    merged = merged[cols]

    # 1) Standarddatei (aktuelle Version)
    out_path = save_training_dataframe(merged)
    print(f"[ok] Trainingsdatensatz (aktuell) gespeichert unter {out_path} ({merged.shape[0]} Zeilen)")

    # 2) Optionale Varianten-Datei mit Experiment-ID als Suffix
    if args.exp_id:
        safe_suffix = args.exp_id.replace(" ", "_")
        alt_path = DATA_PROCESSED / "datasets" / f"eurusd_news_training__{safe_suffix}.csv"
        save_training_dataframe(merged, alt_path)
        print(
            f"[ok] Trainingsdatensatz (Experiment) gespeichert unter "
            f"{alt_path} ({merged.shape[0]} Zeilen)"
        )


if __name__ == "__main__":
    main()
