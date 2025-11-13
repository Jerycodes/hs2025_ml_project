"""Label-Generator fuer EURUSD (Tagesdaten).

Die Funktion `label_eurusd` liest data/raw/fx/EURUSDX.csv ein,
vergleicht jeden Tag mit dem Kurs N Tage spaeter und vergibt Labels:
- up    => Lookahead-Return >= up_threshold
- down  => Lookahead-Return <= down_threshold
- neutral => dazwischen.
Die Ausgabe wird in data/processed/fx/eurusd_labels.csv gespeichert.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.io import DATA_PROCESSED, DATA_RAW


def label_eurusd(
    horizon_days: int = 3,
    up_threshold: float = 0.005,
    down_threshold: float = -0.005,
) -> pd.DataFrame:
    """Erstellt ein DataFrame mit Lookahead-Rendite + Label fuer jede Tageskerze."""

    # Rohdaten laden und chronologisch sortieren
    csv_path = DATA_RAW / "fx" / "EURUSDX.csv"
    df = pd.read_csv(csv_path)

    # YFinance schreibt Metazeilen ("Price", "Ticker") vor die eigentlichen Daten.
    if "Date" not in df.columns and df.columns[0] == "Price":
        df.columns = ["Date", "Close", "High", "Low", "Open", "Volume"]

    parsed_dates = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
    df = df[parsed_dates.notna()]
    df["Date"] = parsed_dates
    df = df.sort_values("Date").set_index("Date")

    # Spalten in numerische Typen umwandeln, damit Rechnungen funktionieren
    for col in ["Close", "High", "Low", "Open", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Lookahead-Return: Kurs in N Tagen vs. heutiger Kurs
    future_close = df["Close"].shift(-horizon_days)
    returns = (future_close - df["Close"]) / df["Close"]

    # Schwellenwerte anwenden, um Labels zu vergeben
    labels = pd.Series("neutral", index=df.index)
    labels.loc[returns >= up_threshold] = "up"
    labels.loc[returns <= down_threshold] = "down"

    # Ergebnis zusammenbauen und Zeilen ohne Zukunftswerte entfernen
    result = df.copy()
    result["lookahead_return"] = returns
    result["label"] = labels
    return result.dropna(subset=["lookahead_return"])


def main() -> None:
    """Berechnet Labels und schreibt sie nach data/processed/fx/."""

    labeled = label_eurusd()

    out_path = DATA_PROCESSED / "fx" / "eurusd_labels.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    labeled.to_csv(out_path)

    print(f"[ok] EURUSD-Labels gespeichert: {out_path}")


if __name__ == "__main__":
    main()
