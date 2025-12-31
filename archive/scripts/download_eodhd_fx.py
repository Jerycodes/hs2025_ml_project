"""Hilfsskript zum Laden von EURUSD-EOD-Daten von EODHD.

Dieses Skript nutzt die offizielle ``eodhd``-Python-Library, um
End-of-Day-Preisdaten fuer EURUSD zu laden und im Projektformat
abzulegen:

    data/raw/fx/EURUSDX_eodhd.csv

Die Ausgabe-Spalten sind an die bestehende Yahoo-Datei angepasst:

    Date, Open, High, Low, Close, Volume

Voraussetzung:
    - Environment-Variable ``EODHD_API_KEY`` mit deinem API-Key.
    - Paket ``eodhd`` ist installiert (siehe requirements.txt).
"""

from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path
import sys

import pandas as pd
from eodhd import APIClient

# Projekt-Root zum Modul-Suchpfad hinzufügen, damit `src.*` importierbar ist,
# auch wenn dieses Skript direkt über `python scripts/...` aufgerufen wird.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import DATA_RAW


def fetch_eodhd_eurusd(
    from_date: str = "2015-01-01",
    to_date: str | None = None,
    symbol: str = "EURUSD.FOREX",
) -> pd.DataFrame:
    """Lädt historische Tagesdaten für EURUSD von EODHD.

    Gibt ein DataFrame mit Spalten
    ``Date, Open, High, Low, Close, Volume`` zurück.
    """
    api_key = os.environ.get("EODHD_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Environment-Variable EODHD_API_KEY ist nicht gesetzt. "
            "Bitte deinen EODHD API Key dort hinterlegen."
        )

    if to_date is None:
        to_date = date.today().strftime("%Y-%m-%d")

    api = APIClient(api_key)
    data = api.get_eod_historical_stock_market_data(
        symbol=symbol,
        period="d",
        from_date=from_date,
        to_date=to_date,
        order="a",
    )

    df = pd.DataFrame(data)
    expected_cols = {"date", "open", "high", "low", "close", "volume"}
    if not expected_cols.issubset(df.columns):
        raise ValueError(
            f"Unerwartete Spalten von EODHD: {df.columns.tolist()}. "
            f"Erwarte mindestens: {sorted(expected_cols)}"
        )

    df = df[["date", "open", "high", "low", "close", "volume"]].copy()
    df.rename(
        columns={
            "date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        },
        inplace=True,
    )
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lädt EURUSD-EOD-Daten von EODHD und speichert sie als CSV."
    )
    parser.add_argument(
        "--from-date",
        type=str,
        default="2015-01-01",
        help="Startdatum (YYYY-MM-DD) für die Historie.",
    )
    parser.add_argument(
        "--to-date",
        type=str,
        default=None,
        help="Enddatum (YYYY-MM-DD). Standard: heutiges Datum.",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="EURUSD.FOREX",
        help="EODHD-Symbol (Standard: EURUSD.FOREX).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help=(
            "Ausgabepfad für die CSV-Datei. "
            "Standard: data/raw/fx/EURUSDX_eodhd.csv"
        ),
    )
    args = parser.parse_args()

    df = fetch_eodhd_eurusd(
        from_date=args.from_date,
        to_date=args.to_date,
        symbol=args.symbol,
    )

    out_dir = DATA_RAW / "fx"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out or (out_dir / "EURUSDX_eodhd.csv")
    df.to_csv(out_path, index=False)
    print("[ok] EODHD EURUSD-Daten gespeichert unter:", out_path)
    print("[info] Zeilen:", len(df))


if __name__ == "__main__":
    main()
