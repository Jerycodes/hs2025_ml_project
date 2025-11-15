"""Aggregiert EODHD-News zu Tagesfeatures für EURUSD.

Schrittfolge:
1. JSONL-Datei (eine News pro Zeile) einlesen.
2. Zeitstempel in echte Datumsobjekte umwandeln.
3. Sentiment-Werte (Dictionary) aufspalten.
4. Pro Tag aggregieren (Anzahl Artikel + Durchschnittssentiment).
5. Ergebnis als CSV ablegen, damit Phase 3 damit arbeiten kann.
"""

from __future__ import annotations

from pathlib import Path
import json  # json.loads konvertiert jede Zeile (string) in ein Python-Dict.

import pandas as pd

from src.utils.io import DATA_PROCESSED, DATA_RAW


def _load_jsonl(path: Path) -> pd.DataFrame:
    """Liest die JSONL-Datei von EODHD ein und baut daraus ein DataFrame."""
    rows = []
    with path.open() as fh:
        for line in fh:
            rows.append(json.loads(line))  # jede Zeile = ein JSON-Objekt (dict)
    if not rows:  # frühe Fehlermeldung, damit Folgefunktionen nicht ins Leere laufen
        raise ValueError(f"Keine News gefunden in {path}")
    return pd.DataFrame(rows)  # DataFrame ist für Aggregationen praktischer


def build_daily_features(jsonl_path: Path | None = None) -> pd.DataFrame:
    """Berechnet Tagesaggregationen aus den News."""
    if jsonl_path is None:
        jsonl_path = DATA_RAW / "news" / "eodhd_news.jsonl"

    df = _load_jsonl(jsonl_path)  # Raw-News als DataFrame

    # EODHD liefert ISO-Strings (z.B. "2025-11-12T22:24:39+00:00").
    # pd.to_datetime wandelt sie in pandas.Timestamp-Objekte um; utc=True sorgt für saubere Zeitzone.
    df["date"] = pd.to_datetime(df["date"], utc=True)

    # Für Tagesfeatures brauchen wir nur das Datum (ohne Uhrzeit). Wir bleiben in UTC, um keine Zeitzonenfehler zu riskieren.
    df["day"] = df["date"].dt.tz_convert("UTC").dt.date  # ergibt datetime.date-Objekte

    # Die Spalte "sentiment" enthält ein Dictionary mit den Keys polarity/neg/neu/pos.
    # apply(pd.Series) macht daraus vier normale Spalten, die sich leicht aggregieren lassen.
    sent = df["sentiment"].apply(pd.Series)
    sent.columns = ["polarity", "neg", "neu", "pos"]
    df = pd.concat([df.drop(columns=["sentiment"]), sent], axis=1)  # ursprüngliche Dict-Spalte fällt weg

    # Pro Tag aggregieren wir, wie viele Artikel erschienen sind und wie ihr Sentiment im Mittel ausfällt.
    agg = (
        df.groupby("day")
        .agg(
            article_count=("title", "count"),  # Anzahl der Meldungen pro Tag
            avg_polarity=("polarity", "mean"),  # Durchschnitt aller Polarity-Werte des Tages
            avg_neg=("neg", "mean"),  # Mittelwert negativer Anteile
            avg_neu=("neu", "mean"),  # Mittelwert neutraler Anteile
            avg_pos=("pos", "mean"),  # Mittelwert positiver Anteile
        )
        .reset_index()
        .rename(columns={"day": "date"})
    )

    return agg.sort_values("date")


def save_daily_features(df: pd.DataFrame, out_path: Path | None = None) -> Path:
    """Speichert das Feature-DataFrame als CSV."""
    if out_path is None:
        out_path = DATA_PROCESSED / "news" / "eodhd_daily_features.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)  # Zielordner anlegen, falls er fehlt
    df.to_csv(out_path, index=False)  # CSV ist leicht weiterzuverarbeiten
    return out_path


def main() -> None:
    """CLI-Einstieg: Features berechnen und direkt abspeichern."""
    features = build_daily_features()  # Schritt 1–4 (s.o.)
    out_path = save_daily_features(features)  # Schritt 5
    print(f"[ok] Tagesfeatures gespeichert unter {out_path}")


if __name__ == "__main__":
    main()
