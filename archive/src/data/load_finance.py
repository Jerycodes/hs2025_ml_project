from datetime import datetime, timedelta

import pandas as pd
# yaml wird verwendet, um Konfigurationsdateien wie symbols.yaml zu lesen
import yaml

# yfinance ist eine Bibliothek, die Finanzmarktdaten von Yahoo Finance herunterladen kann
import yfinance as yf

# DATA_RAW ist ein Pfad, den wir in src/utils/io.py definiert haben
# dort stehen Rohdaten grundsätzlich drin
from src.utils.io import DATA_RAW


def _ensure_datetime(value):
    """Konvertiert YAML-Strings zuverlässig in datetime-Objekte."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Unsupported date value: {value!r}")


def _chunk_range(start_dt, end_dt, max_days=700):
    """Yield-Chunks, damit wir unter YF's 730-Tage-Limit bleiben."""
    step = timedelta(days=max_days)
    current = start_dt
    while current < end_dt:
        chunk_end = min(current + step, end_dt)
        yield current, chunk_end
        current = chunk_end


def load_config(path: str = "config/symbols.yaml") -> dict:
    """
    Lädt die YAML-Konfigurationsdatei und gibt sie als Python Dictionary zurück.
    YAML = menschenlesbare Konfigurationssprache.
    """
    with open(path, "r") as f:        # Datei im Lesemodus öffnen
        return yaml.safe_load(f)      # YAML in Python-Objekt umwandeln


def fetch_and_save(symbols, start, end, interval, subdir):
    """
    Lädt Finanzdaten (für eine Liste von Symbolen) und speichert jede Zeitreihe als CSV.
    
    Parameter:
    - symbols    = Liste von Symbolen (z. B. ["AAPL", "MSFT"])
    - start/end  = Zeitintervall
    - interval   = Auflösung ("1d" = täglich)
    - subdir     = Unterordnername ("equities", "fx")
    """

    # Zielordner, wo die CSVs gespeichert werden sollen
    out_dir = DATA_RAW / subdir
    out_dir.mkdir(parents=True, exist_ok=True)  # Ordner sicherstellen

    for sym in symbols:
        print(f"[info] Lade Daten für {sym}")

        start_dt = _ensure_datetime(start)
        end_dt = _ensure_datetime(end)
        chunk_frames = []

        for chunk_start, chunk_end in _chunk_range(start_dt, end_dt):
            df_chunk = yf.download(
                sym,
                start=chunk_start,
                end=chunk_end,
                interval=interval,
                auto_adjust=True,
                progress=False,
            )
            if df_chunk is None or df_chunk.empty:
                continue
            chunk_frames.append(df_chunk)

        if not chunk_frames:
            print(f"[warn] Keine Daten für {sym} gefunden.")
            continue

        df = pd.concat(chunk_frames)
        df = df[~df.index.duplicated(keep="first")]
        df = df.sort_index()

        # "=" und "^" sind in Dateinamen problematisch → entfernen
        safe_name = sym.replace("=", "").replace("^", "")

        # Ausgabepfad definieren
        out_path = out_dir / f"{safe_name}.csv"

        # CSV schreiben
        df.to_csv(out_path)
        print(f"[ok] Gespeichert: {out_path}")


def main():
    """
    Hauptfunktion:
    - lädt YAML-Konfiguration
    - extrahiert Start/End-Datum & Symbole
    - ruft fetch_and_save separat für Aktien & FX auf
    """

    config = load_config()  # YAML laden

    start = config["start"]
    end = config["end"]
    interval = config["interval"]

    # Aktien-Daten laden
    fetch_and_save(
        symbols=config["equities"],
        start=start,
        end=end,
        interval=interval,
        subdir="equities"
    )

    # FX-Daten laden
    fetch_and_save(
        symbols=config["fx"],
        start=start,
        end=end,
        interval=interval,
        subdir="fx"
    )


# Diese Zeile sorgt dafür, dass main() nur ausgeführt wird,
# wenn du die Datei direkt mit Python startest.
if __name__ == "__main__":
    main()
