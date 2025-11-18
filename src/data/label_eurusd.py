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
import numpy as np
import pandas as pd

from src.utils.io import DATA_PROCESSED, DATA_RAW


def label_eurusd(
    horizon_days: int = 4,
    up_threshold: float = 0.01,
    down_threshold: float = -0.01,
    strict_monotonic: bool = True,
    max_adverse_move_pct: float | None = None,
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
    """

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
    close = df["Close"].to_numpy()

    # Pfad-Bedingungen:
    # Fuer jeden Starttag betrachten wir den Pfad von t bis t+horizon_days.
    # - Monotonie (optional):
    #       up:   diffs > 0 an jedem Tag
    #       down: diffs < 0 an jedem Tag
    # - Adverse Move (optional, tolerante Variante):
    #       up:   min(segment) >= start * (1 - max_adverse_move_pct)
    #       down: max(segment) <= start * (1 + max_adverse_move_pct)
    n = len(close)
    mono_up = np.full(n, False)
    mono_down = np.full(n, False)

    # Wenn weder Monotonie noch Adverse-Move-Filter gesetzt sind,
    # sind alle Pfade formal "erlaubt".
    if not strict_monotonic and max_adverse_move_pct is None:
        mono_up[:] = True
        mono_down[:] = True
    else:
        for i in range(n):
            end = i + horizon_days
            if end >= n:
                # Am Ende der Zeitreihe gibt es nicht mehr genug Zukunftsdaten.
                continue

            segment = close[i : end + 1]  # Werte von t bis t+horizon_days
            start = segment[0]

            # 1) Monotonie-Bedingung (falls aktiviert)
            if strict_monotonic:
                diffs = np.diff(segment)
                up_ok_monotonic = np.all(diffs > 0)
                down_ok_monotonic = np.all(diffs < 0)
            else:
                up_ok_monotonic = True
                down_ok_monotonic = True

            # 2) Adverse-Move-Bedingung (falls aktiviert)
            if max_adverse_move_pct is not None:
                min_seg = segment.min()
                max_seg = segment.max()
                up_ok_adverse = min_seg >= start * (1 - max_adverse_move_pct)
                down_ok_adverse = max_seg <= start * (1 + max_adverse_move_pct)
            else:
                up_ok_adverse = True
                down_ok_adverse = True

            mono_up[i] = up_ok_monotonic and up_ok_adverse
            mono_down[i] = down_ok_monotonic and down_ok_adverse

    # Schwellenwerte anwenden, um Labels zu vergeben:
    # Startwert fuer alle Tage ist neutral.
    labels = pd.Series("neutral", index=df.index)

    # Bedingungen fuer up:
    # 1) Endrendite ist stark genug positiv.
    # 2) Der Pfad ist streng steigend (oder Monotonie ist deaktiviert).
    up_mask = (returns >= up_threshold) & pd.Series(mono_up, index=df.index)
    labels.loc[up_mask] = "up"

    # Bedingungen fuer down:
    # 1) Endrendite ist stark genug negativ.
    # 2) Der Pfad ist streng fallend (oder Monotonie ist deaktiviert).
    down_mask = (returns <= down_threshold) & pd.Series(mono_down, index=df.index)
    labels.loc[down_mask] = "down"

    # Ergebnis zusammenbauen und Zeilen ohne Zukunftswerte entfernen
    result = df.copy()
    result["lookahead_return"] = returns
    result["label"] = labels
    return result.dropna(subset=["lookahead_return"])


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
    args = parser.parse_args()

    labeled = label_eurusd()

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
