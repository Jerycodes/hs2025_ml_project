"""v2: Trainingsdatensatz aus v2-Labels bauen (ohne bestehende Outputs zu überschreiben)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.features.eurusd_features import add_eurusd_features


def load_labels_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.rename(columns={"Date": "date"})
    return df.sort_values("date").reset_index(drop=True)


def build_price_only_training_dataframe_from_labels(df_labels: pd.DataFrame) -> pd.DataFrame:
    """Erzeugt einen Trainings-DataFrame nur aus FX-Labels (ohne News-Merge).

    Erwartet Spalten:
    - date
    - Open/High/Low/Close
    - label
    """
    required = {"date", "Open", "High", "Low", "Close", "label"}
    missing = required - set(df_labels.columns)
    if missing:
        raise KeyError(f"Labels-DataFrame fehlt Spalten: {sorted(missing)}")

    merged = df_labels.copy()

    # Zielvariablen
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

    # Stub-News-Spalten, damit add_eurusd_features funktionieren kann.
    merged["article_count"] = 0.0
    merged["avg_polarity"] = 0.0
    merged["avg_neg"] = 0.0
    merged["avg_neu"] = 1.0
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
        "article_count",
        "avg_polarity",
        "avg_neg",
        "avg_neu",
        "avg_pos",
    ]
    cols = [c for c in cols if c in merged.columns]
    return merged[cols].copy()


def save_dataset_csv(df: pd.DataFrame, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path

