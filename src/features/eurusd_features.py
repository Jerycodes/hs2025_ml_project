"""Zusätzliche abgeleitete Features für den EURUSD-Trainingsdatensatz.

Alle Features sind so konstruiert, dass sie nur Informationen aus
heutigen und vergangenen Daten nutzen (keine Lookahead-Information).

Namenskonvention:
- Prefix:
    - ``price_...``  → Features aus OHLC-Preisdaten.
    - ``news_...``   → Features aus News-/Sentimentdaten.
    - ``cal_...``    → Kalender-/Saison-Features.
    - ``hol_...``    → Feiertags-Features.
- Mittelteil: inhaltliche Beschreibung (z. B. ``close_ret``, ``range_pct``).
- Suffix:
    - ``_1d``, ``_5d``       → Horizont in Tagen (Rolling-Fenster inkl. heute).
    - ``_lag1``              → Wert vom Vortag.
    - ``_3d_sum``, ``_5d_std`` etc. → Aggregation + Fenstergröße.
"""

from __future__ import annotations

from typing import Final

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar


US_HOLIDAY_CAL: Final = USFederalHolidayCalendar()


def _add_us_holiday_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Fügt US-Feiertags-Flags hinzu, basierend nur auf dem Datum.

    Verwendet den eingebauten ``USFederalHolidayCalendar`` von pandas.

    Erzeugte Features:
    - ``hol_is_us_federal_holiday``:
        1, wenn der Tag ein US-Feiertag ist, sonst 0.
    - ``hol_is_day_before_us_federal_holiday``:
        1, wenn der Folgetag ein US-Feiertag ist.
    - ``hol_is_day_after_us_federal_holiday``:
        1, wenn der Vortag ein US-Feiertag ist.
    """
    if df.empty:
        df["hol_is_us_federal_holiday"] = pd.Series(dtype="int8")
        df["hol_is_day_before_us_federal_holiday"] = pd.Series(dtype="int8")
        df["hol_is_day_after_us_federal_holiday"] = pd.Series(dtype="int8")
        return df

    date_series = df["date"].dt.normalize()
    holidays = US_HOLIDAY_CAL.holidays(start=date_series.min(), end=date_series.max())
    # Wir arbeiten mit normalisierten Timestamps (Mitternacht), um Vergleiche zu vereinfachen.
    holidays = holidays.normalize()

    df["hol_is_us_federal_holiday"] = date_series.isin(holidays).astype("int8")
    df["hol_is_day_before_us_federal_holiday"] = (
        date_series.add(pd.Timedelta(days=1)).isin(holidays)
    ).astype("int8")
    df["hol_is_day_after_us_federal_holiday"] = (
        date_series.add(pd.Timedelta(days=-1)).isin(holidays)
    ).astype("int8")

    return df


def add_eurusd_features(df: pd.DataFrame) -> pd.DataFrame:
    """Erweitert den EURUSD-Trainings-DataFrame um zusätzliche Features.

    Erwartet ein DataFrame nach dem Merge von FX-Labels und News-Features,
    das u. a. folgende Spalten enthält:
        - date (datetime64[ns])
        - Close, High, Low, Open
        - intraday_range_pct, body_pct
        - article_count, pos_share, neg_share

    Alle Berechnungen nutzen ausschließlich Informationen bis einschließlich
    des aktuellen Tages (kein Blick in die Zukunft).
    """
    if df.empty:
        return df

    df = df.sort_values("date").copy()

    # ---------- Preis-Features (price_...) ----------
    close = df["Close"]
    df["price_close_ret_1d"] = close.pct_change(periods=1)
    df["price_close_ret_5d"] = close.pct_change(periods=5)

    df["price_range_pct_5d_std"] = (
        df["intraday_range_pct"].rolling(window=5, min_periods=5).std()
    )
    df["price_body_pct_5d_mean"] = (
        df["body_pct"].rolling(window=5, min_periods=5).mean()
    )

    # ---------- News-Historie / -Intensität (news_...) ----------
    df["news_article_count_3d_sum"] = (
        df["article_count"].rolling(window=3, min_periods=3).sum()
    )
    df["news_article_count_7d_sum"] = (
        df["article_count"].rolling(window=7, min_periods=7).sum()
    )

    df["news_pos_share_5d_mean"] = (
        df["pos_share"].rolling(window=5, min_periods=5).mean()
    )
    df["news_neg_share_5d_mean"] = (
        df["neg_share"].rolling(window=5, min_periods=5).mean()
    )

    df["news_article_count_lag1"] = df["article_count"].shift(1)
    df["news_pos_share_lag1"] = df["pos_share"].shift(1)
    df["news_neg_share_lag1"] = df["neg_share"].shift(1)

    # ---------- Kalender-Features (cal_...) ----------
    date = df["date"]
    dow = date.dt.dayofweek  # Montag=0, Sonntag=6

    df["cal_dow"] = dow
    df["cal_day_of_month"] = date.dt.day
    df["cal_is_monday"] = (dow == 0).astype("int8")
    df["cal_is_friday"] = (dow == 4).astype("int8")
    df["cal_is_month_start"] = date.dt.is_month_start.astype("int8")
    df["cal_is_month_end"] = date.dt.is_month_end.astype("int8")

    # ---------- Feiertags-Features (hol_...) ----------
    df = _add_us_holiday_flags(df)

    return df

