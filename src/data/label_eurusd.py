"""Label-Generator fuer EURUSD (Tagesdaten).

Die Funktion `label_eurusd` liest data/raw/fx/EURUSDX.csv ein
und vergibt fuer jeden Tag ein Label:

- up      => Kurs ist nach `horizon_days` deutlich hoeher
             UND steigt auf dem Weg dorthin an jedem Tag.
- down    => Kurs ist nach `horizon_days` deutlich tiefer
             UND faellt auf dem Weg dorthin an jedem Tag.
- neutral => alle uebrigen Faelle.

Konkrete Standard-Logik:
- horizon_days = 4 → wir betrachten die Tage t, t+1, t+2, t+3, t+4.
- up:   C_{t+4} >= C_t * (1 + up_threshold)
        UND C_{t+1} > C_t, C_{t+2} > C_{t+1}, ... (streng steigend)
- down: C_{t+4} <= C_t * (1 + down_threshold)
        UND C_{t+1} < C_t, C_{t+2} < C_{t+1}, ... (streng fallend)

Die Ausgabe wird in data/processed/fx/eurusd_labels.csv gespeichert.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd

from src.utils.io import DATA_PROCESSED, DATA_RAW


def _label_eurusd_core(
    df: pd.DataFrame,
    *,
    horizon_days: int,
    up_threshold: float,
    down_threshold: float,
    strict_monotonic: bool,
    max_adverse_move_pct: float | None,
    hit_within_horizon: bool,
    first_hit_wins: bool,
    hit_source: str = "close",  # 'close' | 'hl'
    intraday_tie_breaker: str = "down",  # 'down' | 'up' (only relevant when both touched same day)
) -> pd.DataFrame:
    """Core labeling logic on a prepared Daily-OHLC DataFrame (Index=Date)."""
    if hit_source not in {"close", "hl"}:
        raise ValueError("hit_source muss 'close' oder 'hl' sein.")
    if intraday_tie_breaker not in {"down", "up"}:
        raise ValueError("intraday_tie_breaker muss 'down' oder 'up' sein.")

    # Lookahead-Return: Kurs in N Tagen vs. heutiger Kurs
    future_close = df["Close"].shift(-horizon_days)
    returns = (future_close - df["Close"]) / df["Close"]
    close = df["Close"].to_numpy()
    high = df["High"].to_numpy() if "High" in df.columns else None
    low = df["Low"].to_numpy() if "Low" in df.columns else None

    n = len(close)
    mono_up = np.full(n, False)
    mono_down = np.full(n, False)
    hit_up = np.full(n, False)
    hit_down = np.full(n, False)
    first_up = np.full(n, False)
    first_down = np.full(n, False)

    for i in range(n):
        end = i + horizon_days
        if end >= n:
            continue

        segment = close[i : end + 1]
        start = segment[0]

        if strict_monotonic:
            diffs = np.diff(segment)
            up_ok_monotonic = np.all(diffs > 0)
            down_ok_monotonic = np.all(diffs < 0)
        else:
            up_ok_monotonic = True
            down_ok_monotonic = True

        if max_adverse_move_pct is not None:
            if hit_source == "hl" and high is not None and low is not None:
                # For intraday-aware labeling, adverse move should be based on Low/High, not Close.
                # Use t+1..t+horizon_days window (exclude the start day itself).
                low_seg = low[i + 1 : end + 1]
                high_seg = high[i + 1 : end + 1]
                up_ok_adverse = float(np.nanmin(low_seg)) >= start * (1 - max_adverse_move_pct)
                down_ok_adverse = float(np.nanmax(high_seg)) <= start * (1 + max_adverse_move_pct)
            else:
                min_seg = segment.min()
                max_seg = segment.max()
                up_ok_adverse = min_seg >= start * (1 - max_adverse_move_pct)
                down_ok_adverse = max_seg <= start * (1 + max_adverse_move_pct)
        else:
            up_ok_adverse = True
            down_ok_adverse = True

        mono_up[i] = up_ok_monotonic and up_ok_adverse
        mono_down[i] = down_ok_monotonic and down_ok_adverse

        if hit_source == "hl" and high is not None and low is not None:
            high_seg = high[i + 1 : end + 1]
            low_seg = low[i + 1 : end + 1]
            hit_up[i] = float(np.nanmax(high_seg)) >= start * (1 + up_threshold)
            hit_down[i] = float(np.nanmin(low_seg)) <= start * (1 + down_threshold)
        else:
            max_seg = segment.max()
            min_seg = segment.min()
            hit_up[i] = max_seg >= start * (1 + up_threshold)
            hit_down[i] = min_seg <= start * (1 + down_threshold)

        if hit_within_horizon and first_hit_wins:
            up_level = start * (1 + up_threshold)
            down_level = start * (1 + down_threshold)

            up_idx: int | None = None
            down_idx: int | None = None

            if hit_source == "hl" and high is not None and low is not None:
                for j in range(1, horizon_days + 1):
                    if up_idx is None and float(high[i + j]) >= up_level:
                        up_idx = j
                    if down_idx is None and float(low[i + j]) <= down_level:
                        down_idx = j
                    if up_idx is not None and down_idx is not None:
                        break
            else:
                for j, price in enumerate(segment[1:], start=1):
                    if up_idx is None and price >= up_level:
                        up_idx = j
                    if down_idx is None and price <= down_level:
                        down_idx = j
                    if up_idx is not None and down_idx is not None:
                        break

            if up_idx is None and down_idx is None:
                continue

            if down_idx is None:
                winner = "up"
                hit_idx = up_idx
            elif up_idx is None:
                winner = "down"
                hit_idx = down_idx
            else:
                if up_idx < down_idx:
                    winner = "up"
                    hit_idx = up_idx
                elif down_idx < up_idx:
                    winner = "down"
                    hit_idx = down_idx
                else:
                    # Same day: with Daily OHLC we don't know order; tie-break explicitly.
                    winner = intraday_tie_breaker

            subseg = segment[: hit_idx + 1]
            if strict_monotonic:
                diffs = np.diff(subseg)
                ok_monotonic = bool(np.all(diffs > 0)) if winner == "up" else bool(np.all(diffs < 0))
            else:
                ok_monotonic = True

            if max_adverse_move_pct is not None:
                if hit_source == "hl" and high is not None and low is not None:
                    low_sub = low[i + 1 : i + hit_idx + 1]
                    high_sub = high[i + 1 : i + hit_idx + 1]
                    if winner == "up":
                        ok_adverse = bool(float(np.nanmin(low_sub)) >= start * (1 - max_adverse_move_pct))
                    else:
                        ok_adverse = bool(float(np.nanmax(high_sub)) <= start * (1 + max_adverse_move_pct))
                else:
                    min_sub = subseg.min()
                    max_sub = subseg.max()
                    if winner == "up":
                        ok_adverse = bool(min_sub >= start * (1 - max_adverse_move_pct))
                    else:
                        ok_adverse = bool(max_sub <= start * (1 + max_adverse_move_pct))
            else:
                ok_adverse = True

            ok_path = ok_monotonic and ok_adverse
            if winner == "up":
                first_up[i] = ok_path
            else:
                first_down[i] = ok_path

    labels = pd.Series("neutral", index=df.index)
    mono_up_series = pd.Series(mono_up, index=df.index)
    mono_down_series = pd.Series(mono_down, index=df.index)

    if hit_within_horizon:
        if first_hit_wins:
            up_mask = pd.Series(first_up, index=df.index)
            down_mask = pd.Series(first_down, index=df.index)
        else:
            hit_up_series = pd.Series(hit_up, index=df.index)
            hit_down_series = pd.Series(hit_down, index=df.index)
            up_mask = hit_up_series & mono_up_series
            down_mask = hit_down_series & mono_down_series
    else:
        up_mask = (returns >= up_threshold) & mono_up_series
        down_mask = (returns <= down_threshold) & mono_down_series

    labels.loc[up_mask] = "up"
    labels.loc[down_mask] = "down"

    result = df.copy()
    result["lookahead_return"] = returns
    result["label"] = labels
    result.index.name = "Date"
    return result.dropna(subset=["lookahead_return"])


def label_eurusd_from_daily_prices(
    df: pd.DataFrame,
    *,
    horizon_days: int = 4,
    up_threshold: float = 0.01,
    down_threshold: float = -0.01,
    strict_monotonic: bool = True,
    max_adverse_move_pct: float | None = None,
    hit_within_horizon: bool = False,
    first_hit_wins: bool = False,
    hit_source: str = "close",
    intraday_tie_breaker: str = "down",
    drop_weekends: bool = False,
) -> pd.DataFrame:
    """Labeling wie `label_eurusd`, aber direkt aus Daily-OHLC (z.B. aus MT5 H1 aggregiert)."""
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("df muss einen DatetimeIndex haben (Index=Date).")

    df = df.sort_index().copy()
    if drop_weekends:
        df = df[df.index.dayofweek < 5]

    for col in ["Close", "High", "Low", "Open", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if "Volume" not in df.columns:
        df["Volume"] = 0.0

    return _label_eurusd_core(
        df,
        horizon_days=horizon_days,
        up_threshold=up_threshold,
        down_threshold=down_threshold,
        strict_monotonic=strict_monotonic,
        max_adverse_move_pct=max_adverse_move_pct,
        hit_within_horizon=hit_within_horizon,
        first_hit_wins=first_hit_wins,
        hit_source=hit_source,
        intraday_tie_breaker=intraday_tie_breaker,
    )


def label_eurusd_from_daily_and_h1(
    df_daily: pd.DataFrame,
    df_h1: pd.DataFrame,
    *,
    cut_hour: int = 0,
    horizon_days: int = 4,
    up_threshold: float = 0.01,
    down_threshold: float = -0.01,
    strict_monotonic: bool = True,
    max_adverse_move_pct: float | None = None,
    hit_within_horizon: bool = False,
    first_hit_wins: bool = False,
    hit_source: str = "h1",  # only supported value here
    intraday_tie_breaker: str = "down",
    drop_weekends: bool = False,
) -> pd.DataFrame:
    """Intraday-aware labeling using H1 bars (for order-aware 'first hit wins' logic).

    Motivation:
    - With Daily OHLC, if both thresholds are touched on the same day, the order is unknown
      and a tie-breaker is required.
    - With H1 bars, we can approximate the order by scanning hour-by-hour.

    Notes:
    - Start price is the daily Close at day t (same convention as label_eurusd_from_daily_prices).
    - We look at H1 bars in days t+1..t+horizon_days (sessionized by cut_hour).
    - If both thresholds are crossed within the same *hour*, order is still unknown -> tie-breaker.
    """
    if hit_source != "h1":
        raise ValueError("label_eurusd_from_daily_and_h1 unterstützt nur hit_source='h1'.")
    if intraday_tie_breaker not in {"down", "up"}:
        raise ValueError("intraday_tie_breaker muss 'down' oder 'up' sein.")
    if first_hit_wins and not hit_within_horizon:
        raise ValueError("first_hit_wins=True ist nur sinnvoll, wenn hit_within_horizon=True.")

    if not isinstance(df_daily.index, pd.DatetimeIndex):
        raise TypeError("df_daily muss einen DatetimeIndex haben (Index=Date).")
    if not isinstance(df_h1.index, pd.DatetimeIndex):
        raise TypeError("df_h1 muss einen DatetimeIndex haben (Index=Datetime).")

    daily = df_daily.sort_index().copy()
    if drop_weekends:
        daily = daily[daily.index.dayofweek < 5]

    for col in ["Close", "High", "Low", "Open", "Volume"]:
        if col in daily.columns:
            daily[col] = pd.to_numeric(daily[col], errors="coerce")
    daily = daily.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if "Volume" not in daily.columns:
        daily["Volume"] = 0.0

    h1 = df_h1.sort_index().copy()
    for col in ["open", "high", "low", "close"]:
        if col not in h1.columns:
            raise ValueError(f"df_h1 missing required column: {col}")
        h1[col] = pd.to_numeric(h1[col], errors="coerce")
    h1 = h1.dropna(subset=["open", "high", "low", "close"]).copy()

    from src.data.mt5_h1 import session_date_index

    h1_session = session_date_index(h1.index, cut_hour=int(cut_hour))
    h1_dates_ns = h1_session.to_numpy(dtype="datetime64[ns]").view("int64")

    h1_high = h1["high"].to_numpy(dtype="float64")
    h1_low = h1["low"].to_numpy(dtype="float64")

    # Map session date -> slice [start, end) into H1 arrays
    start_by_date: dict[int, int] = {}
    end_by_date: dict[int, int] = {}
    for idx, key in enumerate(h1_dates_ns):
        if key not in start_by_date:
            start_by_date[key] = idx
        end_by_date[key] = idx + 1

    close = daily["Close"].to_numpy(dtype="float64")
    future_close = daily["Close"].shift(-horizon_days)
    returns = ((future_close - daily["Close"]) / daily["Close"]).to_numpy(dtype="float64")

    daily_dates_ns = daily.index.to_numpy(dtype="datetime64[ns]").view("int64")
    n = len(daily_dates_ns)

    mono_up = np.full(n, False)
    mono_down = np.full(n, False)
    hit_up = np.full(n, False)
    hit_down = np.full(n, False)
    first_up = np.full(n, False)
    first_down = np.full(n, False)

    for i in range(n):
        end_day = i + horizon_days
        if end_day >= n:
            continue

        start_price = float(close[i])
        up_level = start_price * (1 + up_threshold)
        down_level = start_price * (1 + down_threshold)

        # Monotonicity on daily closes (same semantics as the daily-based labels)
        if strict_monotonic:
            diffs = np.diff(close[i : end_day + 1])
            up_ok_monotonic = bool(np.all(diffs > 0))
            down_ok_monotonic = bool(np.all(diffs < 0))
        else:
            up_ok_monotonic = True
            down_ok_monotonic = True

        if hit_within_horizon and first_hit_wins:
            min_low_so_far = float("inf")
            max_high_so_far = float("-inf")
            found = False

            for day_offset in range(1, horizon_days + 1):
                day_key = int(daily_dates_ns[i + day_offset])
                s = start_by_date.get(day_key)
                e = end_by_date.get(day_key)
                if s is None or e is None:
                    continue

                for k in range(s, e):
                    h = float(h1_high[k])
                    l = float(h1_low[k])
                    if l < min_low_so_far:
                        min_low_so_far = l
                    if h > max_high_so_far:
                        max_high_so_far = h

                    up_touched = h >= up_level
                    down_touched = l <= down_level
                    if not (up_touched or down_touched):
                        continue

                    if up_touched and down_touched:
                        winner = intraday_tie_breaker
                    elif up_touched:
                        winner = "up"
                    else:
                        winner = "down"

                    if strict_monotonic:
                        diffs = np.diff(close[i : i + day_offset + 1])
                        ok_monotonic = bool(np.all(diffs > 0)) if winner == "up" else bool(np.all(diffs < 0))
                    else:
                        ok_monotonic = True

                    if max_adverse_move_pct is not None:
                        if winner == "up":
                            ok_adverse = min_low_so_far >= start_price * (1 - max_adverse_move_pct)
                        else:
                            ok_adverse = max_high_so_far <= start_price * (1 + max_adverse_move_pct)
                    else:
                        ok_adverse = True

                    ok_path = ok_monotonic and ok_adverse
                    if winner == "up":
                        first_up[i] = ok_path
                    else:
                        first_down[i] = ok_path

                    found = True
                    break

                if found:
                    break

            # Path-valid flags for completeness (used only for reporting / debugging)
            mono_up[i] = up_ok_monotonic
            mono_down[i] = down_ok_monotonic
        else:
            # Hit detection over the full horizon window.
            min_low = float("inf")
            max_high = float("-inf")
            any_up = False
            any_down = False

            for day_offset in range(1, horizon_days + 1):
                day_key = int(daily_dates_ns[i + day_offset])
                s = start_by_date.get(day_key)
                e = end_by_date.get(day_key)
                if s is None or e is None:
                    continue

                highs = h1_high[s:e]
                lows = h1_low[s:e]
                if highs.size:
                    day_max_high = float(np.nanmax(highs))
                    max_high = max(max_high, day_max_high)
                    if not any_up and np.isfinite(day_max_high) and day_max_high >= up_level:
                        any_up = True
                if lows.size:
                    day_min_low = float(np.nanmin(lows))
                    min_low = min(min_low, day_min_low)
                    if not any_down and np.isfinite(day_min_low) and day_min_low <= down_level:
                        any_down = True

            hit_up[i] = any_up
            hit_down[i] = any_down

            if max_adverse_move_pct is not None and np.isfinite(min_low) and np.isfinite(max_high):
                up_ok_adverse = min_low >= start_price * (1 - max_adverse_move_pct)
                down_ok_adverse = max_high <= start_price * (1 + max_adverse_move_pct)
            else:
                up_ok_adverse = True
                down_ok_adverse = True

            mono_up[i] = up_ok_monotonic and up_ok_adverse
            mono_down[i] = down_ok_monotonic and down_ok_adverse

    labels = pd.Series("neutral", index=daily.index)
    if hit_within_horizon:
        if first_hit_wins:
            up_mask = pd.Series(first_up, index=daily.index)
            down_mask = pd.Series(first_down, index=daily.index)
        else:
            up_mask = pd.Series(hit_up, index=daily.index) & pd.Series(mono_up, index=daily.index)
            down_mask = pd.Series(hit_down, index=daily.index) & pd.Series(mono_down, index=daily.index)
    else:
        up_mask = (pd.Series(returns, index=daily.index) >= up_threshold) & pd.Series(mono_up, index=daily.index)
        down_mask = (pd.Series(returns, index=daily.index) <= down_threshold) & pd.Series(mono_down, index=daily.index)

    labels.loc[up_mask] = "up"
    labels.loc[down_mask] = "down"

    result = daily.copy()
    result["lookahead_return"] = returns
    result["label"] = labels
    result.index.name = "Date"
    return result.dropna(subset=["lookahead_return"])


def label_eurusd(
    horizon_days: int = 4,
    up_threshold: float = 0.01,
    down_threshold: float = -0.01,
    strict_monotonic: bool = True,
    max_adverse_move_pct: float | None = None,
    hit_within_horizon: bool = False,
    first_hit_wins: bool = False,
    hit_source: str = "close",
    intraday_tie_breaker: str = "down",
    price_source: str = "yahoo",
    drop_weekends: bool = False,
) -> pd.DataFrame:
    """Erstellt ein DataFrame mit Lookahead-Rendite + Label fuer jede Tageskerze.

    Parameter:
    - horizon_days: Anzahl Tage, in die in die Zukunft geschaut wird
      (Standard: 4 → t bis t+4).
    - up_threshold / down_threshold: minimale/negative Rendite, ab der ein up/down
      vergeben wird, wenn die Pfad-Bedingung erfuellt ist.
    - strict_monotonic: Wenn True, muss der Pfad zwischen Start und Horizont
      fuer up streng steigend bzw. fuer down streng fallend sein.
      Wenn False, wird keine Monotonie-Bedingung erzwungen.
    - max_adverse_move_pct:
        Optionaler zusaetzlicher Pfad-Filter (tolerante Variante).

        Idee:
        - up:   Kurs darf zwischen t und t+horizon_days nie mehr als
                ``max_adverse_move_pct`` unter den Startkurs fallen.
        - down: Kurs darf zwischen t und t+horizon_days nie mehr als
                ``max_adverse_move_pct`` ueber den Startkurs steigen.

        Beispiele:
        - max_adverse_move_pct = 0.003 → maximal -0.3 % gegen die eigentliche
          Richtung erlaubt.

        Wenn ``max_adverse_move_pct`` = None, wird kein zusaetzlicher
        Adverse-Move-Filter angewendet.
    - hit_within_horizon:
        Steuerung der Treffer-Logik fuer up/down.

        False (Standard, v-/nv-Serien):
            up/down wird nur vergeben, wenn der Schlusskurs am Horizont-Tag
            t+horizon_days die jeweilige Schwelle erreicht/ueberschreitet
            (also wie in der eingangs beschriebenen Standard-Logik).

        True (neue Experiment-Serien):
            up/down wird bereits vergeben, wenn **irgendwo** innerhalb des
            Fensters [t, t+horizon_days] die Schwelle einmal erreicht oder
            ueberschritten (up) bzw. unterschritten (down) wird. Damit wird
            eher die Logik eines Take-Profit-Treffers abgebildet.
    - first_hit_wins:
        Nur relevant, wenn ``hit_within_horizon=True``.

        Problem: Im selben Horizont-Fenster kann sowohl die Up- als auch die
        Down-Schwelle erreicht werden (z.B. erst +0.4%, danach -0.4%).

        - False (Standard / Backwards-Kompatibilität):
            Es wird nur geprüft *ob* innerhalb des Fensters getroffen wurde
            (max/min über das Segment). Wenn beide Treffer möglich sind,
            kann es zu Overlap kommen (aktuell gewinnt „down“, da es zuletzt gesetzt wird).
        - True (empfohlen für trading-nahe Logik):
            Es wird geprüft, welche Schwelle *zuerst* erreicht wird. Das Label
            entspricht dem ersten Treffer. Pfad-Filter (Monotonie / Adverse Move)
            werden in diesem Fall nur bis zum Treffer-Tag geprüft (danach wäre man
            im Trading-Sinn bereits aus dem Trade raus).
    - price_source:
        Datenquelle fuer die FX-Preise.

        - \"yahoo\" (Standard): liest data/raw/fx/EURUSDX.csv
        - \"eodhd\":            liest data/raw/fx/EURUSDX_eodhd.csv
        - \"mt5\":              liest data/raw/fx/EURUSD_mt5_D1.csv (Daily aus MT5-Export)

        Weitere Quellen koennen spaeter ergaenzt werden.
    - drop_weekends:
        Wenn True, werden Samstage/Sonntage aus der Preiszeitreihe entfernt.
        Das ist sinnvoll, wenn eine Datenquelle (z.B. EODHD) Wochenend-Zeilen enthält,
        da unser Modell „Handelstage“ (typisch Mo–Fr) annimmt.
    """

    # Rohdaten laden und chronologisch sortieren
    if price_source == "yahoo":
        csv_name = "EURUSDX.csv"
    elif price_source == "eodhd":
        csv_name = "EURUSDX_eodhd.csv"
    elif price_source == "mt5":
        csv_name = "EURUSD_mt5_D1.csv"
    else:
        raise ValueError(
            f"Unbekannte price_source='{price_source}'. Erwarte 'yahoo', 'eodhd' oder 'mt5'."
        )

    csv_path = DATA_RAW / "fx" / csv_name
    df = pd.read_csv(csv_path)

    # YFinance schreibt Metazeilen ("Price", "Ticker") vor die eigentlichen Daten.
    if "Date" not in df.columns and df.columns[0] == "Price":
        df.columns = ["Date", "Close", "High", "Low", "Open", "Volume"]

    parsed_dates = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
    df = df[parsed_dates.notna()]
    df["Date"] = parsed_dates
    df = df.sort_values("Date").set_index("Date")

    if drop_weekends:
        df = df[df.index.dayofweek < 5]

    # Spalten in numerische Typen umwandeln, damit Rechnungen funktionieren
    for col in ["Close", "High", "Low", "Open", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return _label_eurusd_core(
        df,
        horizon_days=horizon_days,
        up_threshold=up_threshold,
        down_threshold=down_threshold,
        strict_monotonic=strict_monotonic,
        max_adverse_move_pct=max_adverse_move_pct,
        hit_within_horizon=hit_within_horizon,
        first_hit_wins=first_hit_wins,
        hit_source=hit_source,
        intraday_tie_breaker=intraday_tie_breaker,
    )


def main() -> None:
    """Berechnet Labels und schreibt sie nach data/processed/fx/.

    Zusätzlich zur Standarddatei ``eurusd_labels.csv`` kann per ``--exp-id``
    eine Varianten-Datei angelegt werden, z. B.:

    ``eurusd_labels__v1_h4_thr0p5pct_strict.csv``

    So lassen sich verschiedene Label-Konfigurationen archivieren,
    während weiterhin eine „aktuelle“ Datei existiert.
    """

    parser = argparse.ArgumentParser(description="EURUSD-Labels generieren.")
    parser.add_argument(
        "--exp-id",
        type=str,
        default=None,
        help=(
            "Optionale Experiment-ID, die als Suffix an den Dateinamen "
            "angehängt wird, z. B. 'v1_h4_thr0p5pct_strict'."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=(
            "Optionaler Pfad zu einer JSON-Konfiguration. Erwartet entweder "
            "direkt ein dict mit Label-Parametern oder einen Block "
            "{'label_params': {...}} (wie in data/processed/experiments/<EXP_ID>_config.json)."
        ),
    )
    parser.add_argument(
        "--horizon-days",
        type=int,
        default=None,
        help="Anzahl Tage in die Zukunft (überschreibt Config/Default).",
    )
    parser.add_argument(
        "--up-threshold",
        type=float,
        default=None,
        help="Up-Schwelle als Rendite, z.B. 0.02 für +2 Prozent (überschreibt Config/Default).",
    )
    parser.add_argument(
        "--down-threshold",
        type=float,
        default=None,
        help="Down-Schwelle als Rendite, z.B. -0.02 für -2 Prozent (überschreibt Config/Default).",
    )
    parser.add_argument(
        "--strict-monotonic",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Wenn gesetzt, erzwingt/nicht erzwingt strenge Monotonie (überschreibt Config/Default).",
    )
    parser.add_argument(
        "--max-adverse-move-pct",
        type=float,
        default=None,
        help="Optionaler Adverse-Move-Filter, z.B. 0.004 für 0.4 Prozent (überschreibt Config/Default).",
    )
    parser.add_argument(
        "--no-max-adverse-move",
        action="store_true",
        help="Deaktiviert den Adverse-Move-Filter (setzt max_adverse_move_pct=None), auch wenn in Config gesetzt.",
    )
    parser.add_argument(
        "--hit-within-horizon",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Wenn True, reicht Treffer irgendwo im Horizont (überschreibt Config/Default).",
    )
    parser.add_argument(
        "--first-hit-wins",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Nur bei hit_within_horizon: erster Treffer entscheidet (überschreibt Config/Default).",
    )
    parser.add_argument(
        "--price-source",
        choices=["yahoo", "eodhd", "mt5"],
        default=None,
        help="Datenquelle für FX-Preise (überschreibt Config/Default).",
    )
    parser.add_argument(
        "--drop-weekends",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Wenn True, filtert Wochenenden aus der Zeitreihe (überschreibt Config/Default).",
    )
    args = parser.parse_args()

    def load_label_params_from_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "label_params" in data and isinstance(data["label_params"], dict):
            return data["label_params"]
        if isinstance(data, dict):
            return data
        raise ValueError(f"Unerwartetes JSON-Format in {path}. Erwartet dict oder {{'label_params': dict}}.")

    label_params: dict = {}
    loaded_from: Path | None = None

    if args.config is not None:
        loaded_from = args.config
        label_params.update(load_label_params_from_json(args.config))
    elif args.exp_id:
        safe_suffix = args.exp_id.replace(" ", "_")
        cfg_path = DATA_PROCESSED / "experiments" / f"{safe_suffix}_config.json"
        if cfg_path.is_file():
            loaded_from = cfg_path
            label_params.update(load_label_params_from_json(cfg_path))

    allowed_keys = {
        "horizon_days",
        "up_threshold",
        "down_threshold",
        "strict_monotonic",
        "max_adverse_move_pct",
        "hit_within_horizon",
        "first_hit_wins",
        "hit_source",
        "intraday_tie_breaker",
        "price_source",
        "drop_weekends",
    }
    label_params = {k: v for k, v in label_params.items() if k in allowed_keys}

    # CLI-Overrides (nur wenn explizit gesetzt)
    if args.horizon_days is not None:
        label_params["horizon_days"] = args.horizon_days
    if args.up_threshold is not None:
        label_params["up_threshold"] = args.up_threshold
    if args.down_threshold is not None:
        label_params["down_threshold"] = args.down_threshold
    if args.strict_monotonic is not None:
        label_params["strict_monotonic"] = args.strict_monotonic
    if args.no_max_adverse_move:
        label_params["max_adverse_move_pct"] = None
    elif args.max_adverse_move_pct is not None:
        label_params["max_adverse_move_pct"] = args.max_adverse_move_pct
    if args.hit_within_horizon is not None:
        label_params["hit_within_horizon"] = args.hit_within_horizon
    if args.first_hit_wins is not None:
        label_params["first_hit_wins"] = args.first_hit_wins
    if args.price_source is not None:
        label_params["price_source"] = args.price_source
    if args.drop_weekends is not None:
        label_params["drop_weekends"] = args.drop_weekends

    if "horizon_days" in label_params and int(label_params["horizon_days"]) <= 0:
        raise ValueError("horizon_days muss > 0 sein.")

    if loaded_from is not None:
        print(f"[info] Label-Parameter aus Config geladen: {loaded_from}")
    if label_params:
        print(f"[info] Verwendete Label-Parameter (Overrides berücksichtigt): {label_params}")

    labeled = label_eurusd(**label_params)

    out_dir = DATA_PROCESSED / "fx"
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Aktuelle Standarddatei (für Notebook-Default und Backwards-Kompatibilität)
    latest_path = out_dir / "eurusd_labels.csv"
    labeled.to_csv(latest_path)
    print(f"[ok] EURUSD-Labels (aktuell) gespeichert: {latest_path}")

    # 2) Optionale Varianten-Datei mit Experiment-ID als Suffix
    if args.exp_id:
        safe_suffix = args.exp_id.replace(" ", "_")
        exp_path = out_dir / f"eurusd_labels__{safe_suffix}.csv"
        labeled.to_csv(exp_path)
        print(f"[ok] EURUSD-Labels (Experiment) gespeichert: {exp_path}")


if __name__ == "__main__":
    main()
