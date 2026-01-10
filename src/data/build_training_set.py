"""Verknüpft News-Features mit EURUSD-Labels zu einem Trainingsdatensatz."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.features.eurusd_features import (
    add_eurusd_features,
    add_price_features,
    add_news_features,
    add_calendar_features,
    add_holiday_features,
)
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
    """Baut den vollständigen Trainings-DataFrame für das Zwei-Stufen-Modell.

    Schritte:
    1. News-Tagesfeatures laden.
    2. FX-Labels laden (ggf. mit Experiment-ID).
    3. Auf dem Datum mergen.
    4. Zusätzliche Zielvariablen (signal/direction) und Feature-Spalten
       (Kalender-, Preis- und Sentimentfeatures) berechnen.

    Parameter
    ---------
    exp_id:
        Optionale Experiment-ID, um eine bestimmte Label-Datei
        (``eurusd_labels__<exp_id>.csv``) zu verwenden.
    """
    news = load_news_features()
    labels = load_labels(exp_id=exp_id)

    # Wichtig: Preis-Features sollten auf der vollen Preis-Historie berechnet werden,
    # auch wenn die News erst später starten (z.B. ab 2020). Sonst verlieren Rolling-
    # Features (5d/30d) am Anfang der News-Periode den Kontext und werden unnötig NaN.
    labels = labels.sort_values("date").copy()

    # Zusätzliche Zielvariablen für das Zwei-Stufen-Modell:
    # signal: 1 = Bewegung (up/down), 0 = neutral.
    labels["signal"] = (labels["label"] != "neutral").astype(int)

    # direction: nur für Tage mit Bewegung relevant.
    # 1 = up, 0 = down, NaN = neutral (wird für das Richtungsmodell ignoriert).
    direction_map = {"down": 0, "up": 1}
    labels["direction"] = labels["label"].map(direction_map)

    # Kalender-basierte Zusatzfeatures:
    # Monat (1–12), Kalenderwoche (ISO-Standard) und Quartal (1–4).
    labels["month"] = labels["date"].dt.month
    iso = labels["date"].dt.isocalendar()
    labels["week"] = iso.week.astype(int)
    labels["quarter"] = labels["date"].dt.quarter

    # Preisbasierte Tagesfeatures aus High/Low/Open/Close:
    # 1) Intraday-Spanne in absoluten Punkten.
    labels["intraday_range"] = labels["High"] - labels["Low"]
    # 2) Intraday-Spanne relativ zum Schlusskurs (Volatilität eines Tages).
    labels["intraday_range_pct"] = labels["intraday_range"] / labels["Close"]
    # 3) Kerzenkoerper: Close minus Open (positiv = bullische Kerze).
    labels["body"] = labels["Close"] - labels["Open"]
    labels["body_pct"] = labels["body"] / labels["Close"]
    # 4) Docht/Lunte: Abstand vom Kerzenkoerper zu High/Low.
    labels["upper_shadow"] = labels["High"] - labels[["Open", "Close"]].max(axis=1)
    labels["lower_shadow"] = labels[["Open", "Close"]].min(axis=1) - labels["Low"]

    # Preis-Features (rolling etc.) auf kompletter Preis-Historie berechnen
    # (News-Features werden später auf dem gemergten Zeitraum berechnet).
    labels = add_price_features(labels)

    # Sentiment-basierte abgeleitete Features:
    # Anteil positiver / negativer Sentiment-Anteile (auf Basis avg_pos/avg_neg).
    # (pos_share/neg_share + News-Rolling erst nach News-Merge, damit keine Stub-Werte.)

    # News ab Startdatum mergen: automatisch nur Zeiträume behalten, wo News existieren.
    merged = labels.merge(news, on="date", how="inner")

    sentiment_denom = (merged["avg_pos"] + merged["avg_neg"]).replace(0, 1e-6)
    merged["pos_share"] = merged["avg_pos"] / sentiment_denom
    merged["neg_share"] = merged["avg_neg"] / sentiment_denom

    # Nur News-Historie + Kalender/Holiday ergänzen (Preis-Features sind bereits da).
    merged = add_news_features(merged)
    merged = add_calendar_features(merged)
    merged = add_holiday_features(merged)

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
        # Zusätzliche Preis-Features
        "price_close_ret_1d",
        "price_close_ret_5d",
        "price_range_pct_5d_std",
        "price_body_pct_5d_mean",
        "price_close_ret_30d",
        "price_range_pct_30d_std",
        "price_body_pct_30d_mean",
        "price_body_vs_range",
        "price_body_vs_range_5d_mean",
        "price_shadow_balance",
        "price_shadow_balance_5d_mean",
        # News-Historie / -Intensität
        "news_article_count_3d_sum",
        "news_article_count_7d_sum",
        "news_pos_share_5d_mean",
        "news_neg_share_5d_mean",
        "news_article_count_lag1",
        "news_pos_share_lag1",
        "news_neg_share_lag1",
        # Kalender-Features
        "cal_dow",
        "cal_day_of_month",
        "cal_is_monday",
        "cal_is_friday",
        "cal_is_month_start",
        "cal_is_month_end",
        # US-Feiertags-Features
        "hol_is_us_federal_holiday",
        "hol_is_day_before_us_federal_holiday",
        "hol_is_day_after_us_federal_holiday",
        "lookahead_return",
        "article_count",
        "avg_polarity",
        "avg_neg",
        "avg_neu",
        "avg_pos",
    ]
    merged = merged[cols]
    return merged


def build_price_only_training_dataframe_from_labels(exp_id: str | None = None) -> pd.DataFrame:
    """Baut einen Trainings-DataFrame nur aus FX-Labels (ohne News-Merge).

    Die Struktur orientiert sich an ``build_training_dataframe``, damit
    das Trainings-Notebook denselben Pfad benutzen kann, aber alle
    News-abhängigen Features werden später im Price-only-Modus
    aus ``feature_cols`` herausgefiltert.
    """
    labels = load_labels(exp_id=exp_id)
    merged = labels.copy()

    # Zielvariablen wie im Standard-DataFrame
    merged["signal"] = (merged["label"] != "neutral").astype(int)
    direction_map = {"down": 0, "up": 1}
    merged["direction"] = merged["label"].map(direction_map)

    # Kalender-Features
    merged["month"] = merged["date"].dt.month
    iso = merged["date"].dt.isocalendar()
    merged["week"] = iso.week.astype(int)
    merged["quarter"] = merged["date"].dt.quarter

    # Preisbasierte Tagesfeatures
    merged["intraday_range"] = merged["High"] - merged["Low"]
    merged["intraday_range_pct"] = merged["intraday_range"] / merged["Close"]
    merged["body"] = merged["Close"] - merged["Open"]
    merged["body_pct"] = merged["body"] / merged["Close"]
    merged["upper_shadow"] = merged["High"] - merged[["Open", "Close"]].max(axis=1)
    merged["lower_shadow"] = merged[["Open", "Close"]].min(axis=1) - merged["Low"]

    # Stub-News-Spalten für Price-Only-Modus:
    # Die Funktion add_eurusd_features() erwartet News-Spalten (article_count, avg_polarity etc.),
    # auch wenn im Price-Only-Modus keine echten News-Daten vorhanden sind.
    # Durch das Setzen von Null-Werten können wir dieselbe Feature-Pipeline verwenden,
    # wobei die resultierenden news_*-Features später im Trainings-Notebook
    # aus feature_cols herausgefiltert werden.
    # Das vermeidet Code-Duplizierung und hält die Pipeline konsistent.
    merged["article_count"] = 0.0
    merged["avg_polarity"] = 0.0
    merged["avg_neg"] = 0.0
    merged["avg_neu"] = 1.0  # Neutral-Sentiment als Default (100% neutral)
    merged["avg_pos"] = 0.0

    sentiment_denom = (merged["avg_pos"] + merged["avg_neg"]).replace(0, 1e-6)
    merged["pos_share"] = merged["avg_pos"] / sentiment_denom
    merged["neg_share"] = merged["avg_neg"] / sentiment_denom

    merged = add_eurusd_features(merged)

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
        "price_close_ret_1d",
        "price_close_ret_5d",
        "price_range_pct_5d_std",
        "price_body_pct_5d_mean",
        "price_close_ret_30d",
        "price_range_pct_30d_std",
        "price_body_pct_30d_mean",
        "price_body_vs_range",
        "price_body_vs_range_5d_mean",
        "price_shadow_balance",
        "price_shadow_balance_5d_mean",
        "news_article_count_3d_sum",
        "news_article_count_7d_sum",
        "news_pos_share_5d_mean",
        "news_neg_share_5d_mean",
        "news_article_count_lag1",
        "news_pos_share_lag1",
        "news_neg_share_lag1",
        "cal_dow",
        "cal_day_of_month",
        "cal_is_monday",
        "cal_is_friday",
        "cal_is_month_start",
        "cal_is_month_end",
        "hol_is_us_federal_holiday",
        "hol_is_day_before_us_federal_holiday",
        "hol_is_day_after_us_federal_holiday",
        "lookahead_return",
        "article_count",
        "avg_polarity",
        "avg_neg",
        "avg_neu",
        "avg_pos",
    ]
    merged = merged[cols]
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
