# Chat Journal (Zentral)

Diese Datei ist das zentrale Protokoll für alle Codex-/Chat-Verläufe in diesem Repo.  
Ziel: nachvollziehbar festhalten, **was gemacht wurde**, **warum**, **welche Ergebnisse/Fehler auftraten**, **was explizit nicht gemacht wurde**, sowie **welche Änderungen wieder rückgängig gemacht/gelöscht wurden**.

## Regeln (damit es verlässlich bleibt)

- Immer **nur Fakten** protokollieren (keine Annahmen). Wenn etwas unklar ist: als *unklar* markieren.
- Jede Session bekommt **einen Eintrag** mit Datum/Uhrzeit, Thema, Kontext und Ergebnis.
- Wenn Code/Dateien geändert wurden: **Dateipfade + Kurzbeschreibung** aufführen.
- Wenn nichts geändert wurde: explizit „**Keine Dateiänderungen**“ notieren.
- Wenn etwas gelöscht/rollback gemacht wurde: **was** und **wie** (z. B. `git checkout -- …`, `rm …`) notieren.
- Wichtige Terminal-Kommandos und Fehlermeldungen kurz aufnehmen (Copy/Paste ok, aber kompakt).

## Template für neue Einträge (kopieren & ausfüllen)

```md
### YYYY-MM-DD HH:MM — <kurzer Titel>

**Ziel**
- …

**Kontext**
- Working dir: `…`
- Branch/Status: `…` (z. B. Ausgabe von `git status -sb`)
- Relevante Dateien: `…`

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
- Relevante Commits dieser Session (Hashes + Message): `…`
- Commit-Inhalt (kurz): Ausgabe von `git show --stat <hash>`
- Commit-Inhalt (voll, nur wenn klein/überschaubar): Ausgabe von `git show <hash>`

**Vorgehen (was gemacht wurde)**
- …

**Kommandos/Outputs (wichtigste)**
- `…`
- Fehler/Traceback: `…`

**Änderungen**
- Geändert: `…`
- Neu: `…`
- Gelöscht: `…`
- Rückgängig gemacht: `…`
- **Keine Dateiänderungen**: ja/nein

**Ergebnis**
- …

**Offen / Nicht gemacht (bewusst)**
- …
```

## Prompt zum Einfügen in anderen Chat-Verläufen (damit sie dieses Journal ergänzen)

Kopiere diesen Prompt in den anderen Chat:

```text
Du arbeitest in demselben Repo. Bitte ergänze die Datei `CHAT_JOURNAL.md` um einen neuen Eintrag (am Ende der Datei).

Anforderungen:
1) Protokolliere nur Fakten aus diesem Chat: Ziel, Kontext, Vorgehen, wichtige Kommandos/Outputs, Fehler, Ergebnisse.
2) Liste ALLE Dateiänderungen (geändert/neu/gelöscht) mit Pfaden; wenn es keine gab, schreibe explizit „Keine Dateiänderungen“.
3) Falls etwas rückgängig gemacht/gelöscht wurde: beschreibe genau, was und wie.
4) Halte auch fest, was NICHT gemacht wurde (z. B. „keine Packages installiert“, „keine Tests ausgeführt“, „keine Netzwerkcalls“).
5) Keine Halluzinationen: wenn du etwas nicht sicher weißt, markiere es als „unklar“.
6) Nutze das Template aus `CHAT_JOURNAL.md`.
7) Wenn in diesem Chat Commits erstellt wurden: nenne Hash + Message und dokumentiere den Inhalt:
   - immer mindestens `git show --stat <hash>`
   - wenn klein/überschaubar: zusätzlich `git show <hash>` (Patch) in das Journal übernehmen
   - wenn groß: nur `--stat` und Hinweis „Details: git show <hash>“

Führe (wenn möglich) `git status -sb` aus und nutze die Ausgabe im Kontext-Abschnitt.
Führe zusätzlich `git log --oneline --decorate -n 10` aus und nutze es im Abschnitt „Git“.
```

## Einträge

### 2025-12-17 — Debugging: `scripts/fetch_finance.sh` läuft nicht

**Ziel**
- Herausfinden, warum `scripts/fetch_finance.sh` nicht funktioniert.

**Kontext**
- Datum/Uhrzeit: (laut System-`date`) 2025-12-17 (CET); falls abweichend, bitte manuell korrigieren.
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Relevante Dateien: `scripts/fetch_finance.sh`, `src/data/load_finance.py`

**Vorgehen (was gemacht wurde)**
- Script ausgeführt und den Fehler reproduziert.
- Repo-Struktur geprüft (`src/`, `src/utils/`, `src/data/`) und nach `DATA_RAW` gesucht.
- Ursache identifiziert: Import erwartet `src/utils/io.py`, aber dieses Modul war im Workspace nicht vorhanden (leeres `src/utils/`).
- Lösungsvorschlag formuliert (Modul `src/utils/io.py` mit `DATA_RAW` anlegen; ggf. `__init__.py`), ohne selbst Änderungen zu machen.
- Nachfrage des Users beantwortet: ob etwas rückgängig zu machen ist (nein; keine Änderungen vorgenommen), inkl. Hinweis bzgl. `.venv` (nichts installiert/geändert).

**Kommandos/Outputs (wichtigste)**
- `bash scripts/fetch_finance.sh` → bricht ab mit:
  - `ModuleNotFoundError: No module named 'src.utils.io'` aus `src/data/load_finance.py`
- `ls src/utils` → Verzeichnis war leer.

**Änderungen**
- **Keine Dateiänderungen**: ja (nur Ausführen/Lesen von Befehlen).

**Ergebnis**
- Root Cause: fehlendes Modul `src.utils.io` (erwartete Definition von `DATA_RAW`).

**Offen / Nicht gemacht (bewusst)**
- Keine Files erstellt/geändert.
- Keine Packages installiert, nichts am `.venv/` verändert.
- (unklar) Ob `yfinance`/Netzwerk später funktioniert, da der Fehler vorher auftritt.

### 2025-12-17 20:35 CET — EURUSD Datenpipeline stabilisiert + Labels erzeugt

**Ziel**
- EURUSD historische Kursdaten zuverlässig laden/speichern und eine erste Label-Logik (up/down/neutral) erstellen.
- Nebenbei: Git/Commit-Konventionen (Conventional Commits) klären und `.gitignore` so anpassen, dass ein Label-Snapshot versioniert werden kann.

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: Ausgabe von `git status -sb` (Zeitpunkt dieses Eintrags):
  ```text
  ## main...origin/main [ahead 4]
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   ...
  ```
  - Viele Änderungen/Untracked im Workspace (lange Ausgabe; im Terminal sichtbar). *Unklar*, ob diese Änderungen alle in dieser Chat-Session entstanden sind.
- Relevante Dateien: `scripts/fetch_finance.sh`, `src/data/load_finance.py`, `src/utils/io.py`, `config/symbols.yaml`, `src/data/label_eurusd.py`, `.gitignore`, `data/raw/fx/EURUSDX.csv`, `data/processed/fx/eurusd_labels.csv`, `notebooks/eda_labels.ipynb` (vom User angelegt; Inhalt anfangs unklar/leer).

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): (aus Chat/Repo-Historie)
  - `2a702d8 feat: support chunked download and add EURUSD config`
  - `7889019 feat: add data directory helpers`
  - `4a6b708 feat: add EURUSD labeling script`
  - `7475f51 feat: add EURUSD labeling script`
- Commit-Inhalt (kurz): `git show --stat <hash>`
  - `git show --stat 2a702d8`
    ```text
    .gitignore               |   8 +++
    config/symbols.yaml      |   7 +++
    scripts/fetch_finance.sh |  36 +++++++++++++
    src/data/load_finance.py | 133 +++++++++++++++++++++++++++++++++++++++++++++++
    4 files changed, 184 insertions(+)
    ```
    - Details: `git show 2a702d8`
  - `git show --stat 7889019`
    ```text
    src/utils/io.py | 9 +++++++++
    1 file changed, 9 insertions(+)
    ```
  - `git show --stat 4a6b708`
    ```text
    src/data/label_eurusd.py | 73 ++++++++++++++++++++++++++++++++++++++++++++++++
    1 file changed, 73 insertions(+)
    ```
  - `git show --stat 7475f51`
    ```text
    .gitignore                          |    5 +-
    data/processed/fx/eurusd_labels.csv | 2826 +++++++++++++++++++++++++++++++++++
    2 files changed, 2830 insertions(+), 1 deletion(-)
    ```
    - Details: `git show 7475f51` (zu groß fürs Journal)
- Commit-Inhalt (voll, nur wenn klein/überschaubar): Ausgabe von `git show <hash>`
  - `git show 7889019`
    ```diff
    diff --git a/src/utils/io.py b/src/utils/io.py
    new file mode 100644
    index 0000000..72171cb
    --- /dev/null
    +++ b/src/utils/io.py
    @@ -0,0 +1,9 @@
    +from pathlib import Path  # Path sorgt für OS-neutrale Pfad-Operationen.
    +
    +DATA_DIR = Path("data")  # Wurzel für alle Projektdaten.
    +DATA_RAW = DATA_DIR / "raw"
    +DATA_PROCESSED = DATA_DIR / "processed"
    +
    +# Verzeichnisse anlegen, falls sie fehlen – verhindert Laufzeitfehler bei Downloads.
    +for path in (DATA_RAW, DATA_PROCESSED):
    +    path.mkdir(parents=True, exist_ok=True)
    ```
  - `git show 4a6b708`
    ```diff
    diff --git a/src/data/label_eurusd.py b/src/data/label_eurusd.py
    new file mode 100644
    index 0000000..902bc61
    --- /dev/null
    +++ b/src/data/label_eurusd.py
    @@ -0,0 +1,73 @@
    +"""Label-Generator fuer EURUSD (Tagesdaten).
    +
    +Die Funktion `label_eurusd` liest data/raw/fx/EURUSDX.csv ein,
    +vergleicht jeden Tag mit dem Kurs N Tage spaeter und vergibt Labels:
    +- up    => Lookahead-Return >= up_threshold
    +- down  => Lookahead-Return <= down_threshold
    +- neutral => dazwischen.
    +Die Ausgabe wird in data/processed/fx/eurusd_labels.csv gespeichert.
    +"""
    +
    +from __future__ import annotations
    +
    +from pathlib import Path
    +
    +import pandas as pd
    +
    +from src.utils.io import DATA_PROCESSED, DATA_RAW
    +
    +
    +def label_eurusd(
    +    horizon_days: int = 3,
    +    up_threshold: float = 0.005,
    +    down_threshold: float = -0.005,
    +) -> pd.DataFrame:
    +    """Erstellt ein DataFrame mit Lookahead-Rendite + Label fuer jede Tageskerze."""
    +
    +    # Rohdaten laden und chronologisch sortieren
    +    csv_path = DATA_RAW / "fx" / "EURUSDX.csv"
    +    df = pd.read_csv(csv_path)
    +
    +    # YFinance schreibt Metazeilen ("Price", "Ticker") vor die eigentlichen Daten.
    +    if "Date" not in df.columns and df.columns[0] == "Price":
    +        df.columns = ["Date", "Close", "High", "Low", "Open", "Volume"]
    +
    +    parsed_dates = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
    +    df = df[parsed_dates.notna()]
    +    df["Date"] = parsed_dates
    +    df = df.sort_values("Date").set_index("Date")
    +
    +    # Spalten in numerische Typen umwandeln, damit Rechnungen funktionieren
    +    for col in ["Close", "High", "Low", "Open", "Volume"]:
    +        df[col] = pd.to_numeric(df[col], errors="coerce")
    +
    +    # Lookahead-Return: Kurs in N Tagen vs. heutiger Kurs
    +    future_close = df["Close"].shift(-horizon_days)
    +    returns = (future_close - df["Close"]) / df["Close"]
    +
    +    # Schwellenwerte anwenden, um Labels zu vergeben
    +    labels = pd.Series("neutral", index=df.index)
    +    labels.loc[returns >= up_threshold] = "up"
    +    labels.loc[returns <= down_threshold] = "down"
    +
    +    # Ergebnis zusammenbauen und Zeilen ohne Zukunftswerte entfernen
    +    result = df.copy()
    +    result["lookahead_return"] = returns
    +    result["label"] = labels
    +    return result.dropna(subset=["lookahead_return"])
    +
    +
    +def main() -> None:
    +    """Berechnet Labels und schreibt sie nach data/processed/fx/."""
    +
    +    labeled = label_eurusd()
    +
    +    out_path = DATA_PROCESSED / "fx" / "eurusd_labels.csv"
    +    out_path.parent.mkdir(parents=True, exist_ok=True)
    +    labeled.to_csv(out_path)
    +
    +    print(f"[ok] EURUSD-Labels gespeichert: {out_path}")
    +
    +
    +if __name__ == "__main__":
    +    main()
    ```

**Vorgehen (was gemacht wurde)**
- Ursache für Script-Fehler identifiziert und behoben:
  - `src/utils/io.py` war (zeitweise) leer → `from src.utils.io import DATA_RAW` schlug fehl.
  - `config/symbols.yaml` war leer/fehlte → `yaml.safe_load` lieferte `None` → `TypeError: 'NoneType' object is not subscriptable`.
- `config/symbols.yaml` für EURUSD befüllt (`start/end/interval`, `fx: ["EURUSD=X"]`, `equities: []`).
- `yfinance` Limit erkannt: `interval=1h` ist historisch nur ~730 Tage verfügbar → Fehlermeldung im Output.
- `src/data/load_finance.py` erweitert, um Zeiträume zu chunk-en und DataFrames zu mergen; danach für vollständige Historie 2015–2025 auf `interval=1d` umgestellt, damit der Download funktioniert.
- Label-Pipeline implementiert (`src/data/label_eurusd.py`) und an das spezielle CSV-Format von `yfinance` angepasst (Metazeilen `Price`/`Ticker`, Datum parsing, numerische Spalten).
- `.gitignore` angepasst, um einen einzelnen Output-Snapshot (`data/processed/fx/eurusd_labels.csv`) versionieren zu können; dabei wurde ein erster Versuch mit `!data/processed/fx/eurusd_labels.csv` durch ein Pattern mit `data/processed/*` + gezielter Ausnahme ersetzt, weil Ordner-Ignore sonst weiterhin greift.
- Notebook-Workflow vorbereitet (User hat `notebooks/eda_labels.ipynb` angelegt; Text/Zellen zum Einfügen geliefert); in VS Code traten Jupyter/Kernel-Probleme auf (Extensions/Update/readonly volume).

**Kommandos/Outputs (wichtigste)**
- `./scripts/fetch_finance.sh`
  - Fehler (früh): `FileNotFoundError: ... 'config/symbols.yaml'`
  - Fehler (1h, lange Range): `YFPricesMissingError ... The requested range must be within the last 730 days.`
  - Erfolg (1d): `[ok] Gespeichert: data/raw/fx/EURUSDX.csv`
- `python -m src.data.label_eurusd`
  - Fehler: `ValueError: Missing column provided to 'parse_dates': 'Date'` (wegen `Price/Ticker` Metazeilen im CSV)
  - Fehler: `TypeError: unsupported operand type(s) for -: 'str' and 'str'` (Spalten waren Strings)
  - Erfolg: `[ok] EURUSD-Labels gespeichert: data/processed/fx/eurusd_labels.csv`
- Notebook/VS Code (Jupyter):
  - Error: `this.vscNotebook.onDidChangeNotebookCellExecutionState is not a function`
  - Error beim Update: `Cannot update while running on a read-only volume`
- Tooling/Session:
  - Fehler beim Erstellen per Here-Doc: `bash: cannot create temp file for here document: Operation not permitted` (Workaround: Datei per Patch erstellt).
  - Patch-Versuch für `notebooks/eda_labels.ipynb` wurde abgelehnt (vom User/Umgebung); Notebook wurde danach manuell angelegt.
- Git:
  - `git add ...`, `git commit -m "feat: ..."` und `git push origin main` (Hashes siehe Git-Abschnitt).
- Hinweis: Im Tooling gab es wiederholt Shell-Warnungen wie `/opt/homebrew/.../ps: Operation not permitted` (kommt aus der Umgebung; fachlich nicht Teil der Pipeline).

**Änderungen**
- Geändert:
  - `CHAT_JOURNAL.md` (dieser Eintrag ergänzt)
  - `src/data/load_finance.py` (Chunking/Download-Logik ergänzt; später mit `interval=1d` erfolgreich genutzt)
  - `config/symbols.yaml` (EURUSD-Config ergänzt)
  - `.gitignore` (Ignorieren von `.venv/`, `data/raw/`; Ausnahme für `data/processed/fx/eurusd_labels.csv`)
- Neu:
  - `scripts/fetch_finance.sh` (laut Commit `2a702d8`)
  - `src/utils/io.py` (laut Commit `7889019`)
  - `src/data/label_eurusd.py` (laut Commit `4a6b708`)
  - `data/processed/fx/eurusd_labels.csv` (laut Commit `7475f51`, Snapshot versioniert)
  - `notebooks/eda_labels.ipynb` (vom User angelegt; Inhalt zu Beginn unklar/leer)
- Gelöscht: keine explizit in dieser Session (unklar bzgl. der vielen `D ...` Einträge im aktuellen `git status -sb`).
- Rückgängig gemacht: nichts explizit per `git restore`/`git checkout`/`rm` dokumentiert.
- **Keine Dateiänderungen**: nein

**Ergebnis**
- EURUSD Tagesdaten 2015–2025 konnten über `./scripts/fetch_finance.sh` geladen und als CSV gespeichert werden (`data/raw/fx/EURUSDX.csv`).
- Labels (Lookahead-Return + `up/down/neutral`) konnten erzeugt und als `data/processed/fx/eurusd_labels.csv` gespeichert werden.
- `.gitignore` ermöglicht, diesen Label-Snapshot zu versionieren, ohne den gesamten `data/processed/`-Ordner zu tracken.

**Offen / Nicht gemacht (bewusst)**
- Keine Tests/Linting/Formatter ausgeführt (keine entsprechenden Kommandos im Chat).
- Keine zusätzlichen Python-Packages per `pip install` installiert (nur bestehende `.venv` genutzt).
- Keine SQLite/DB-Integration umgesetzt (nur diskutiert).
- Kein News-Download/News-Processing implementiert (nur als nächster Schritt geplant).
- Netzwerk:
  - `yfinance`-Downloads wurden vom User ausgeführt (Netzwerkzugriff implizit).
  - Keine separaten Netzwerk-Calls über Tooling/CLI-Aktionen dokumentiert.

### 2025-12-17 20:43 CET — VS Code Jupyter Kernel: Troubleshooting + Label-EDA (EURUSD)

**Ziel**
- Notebook `notebooks/eda_labels.ipynb` ausführen (Label-Verteilung ansehen).
- VS Code/Jupyter Kernel-Problem verstehen und beheben.

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: Ausgabe von `git status -sb` (Ausgabe gekürzt; vollständige Liste im Terminal)
  ```text
  ## main...origin/main [ahead 4]
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   ...
  ```
- Relevante Dateien: `notebooks/eda_labels.ipynb`, `data/raw/fx/EURUSDX.csv`, `data/processed/fx/eurusd_labels.csv`, `src/data/load_finance.py`, `src/data/label_eurusd.py`, `src/utils/io.py`, `config/symbols.yaml`, `requirements.txt`, `.gitignore`

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): keine (keine Commits im Chat erstellt).

**Vorgehen (was gemacht wurde)**
- Erklärt, dass VS Code in einer read-only Umgebung nicht updaten/Extensions installieren kann (Hinweis aus Screenshot: „Cannot update while running on a read-only volume …“).
- Repo-Dateien gelesen und die EURUSD-Daten-/Label-Pipeline grob geprüft (`src/data/load_finance.py`, `src/data/label_eurusd.py`, `config/symbols.yaml`, Roh-/Processed-CSV).
- Rohdatenformat geprüft: `data/raw/fx/EURUSDX.csv` enthält yfinance-Metazeilen („Price“, „Ticker“, leere „Date“-Zeile); `src/data/label_eurusd.py` hat Logik, die das beim Einlesen bereinigt.
- Label-EDA als Workaround ohne Notebook-Kernel per CLI durchgeführt (Counts/Anteile aus `data/processed/fx/eurusd_labels.csv`).
- User (macOS) Schritt-für-Schritt durch lokale Kernel-Einrichtung geführt: `.venv` aktivieren, `ipykernel` installieren, Kernel registrieren, Interpreter in VS Code auswählen.
- Kernel-Auswahl in VS Code blieb leer; es traten Jupyter-/VS-Code-Fehler aus Screenshots/Extension-UI auf, inkl. „command 'jupyter.selectJupyterInterpreter' not found“ und `this.vscNotebook.onDidChangeNotebookCellExecutionState is not a function`.

**Kommandos/Outputs (wichtigste)**
- `head -n 5 data/raw/fx/EURUSDX.csv` → zeigt Metazeilen:
  - `Price,Close,High,Low,Open,Volume`
  - `Ticker,EURUSD=X,EURUSD=X,EURUSD=X,EURUSD=X,EURUSD=X`
- `python3 -c "import pandas as pd; df=pd.read_csv('data/processed/fx/eurusd_labels.csv'); ..."` → Verteilung:
  - `neutral` = 1387 (0.490973)
  - `down` = 724 (0.256283)
  - `up` = 714 (0.252743)
- User-Terminal:
  - `pip install -r requirements.txt ipykernel` → `Successfully installed ... ipykernel-7.1.0 ...`
  - `pip install --upgrade pip` → `Successfully installed pip-25.3`
  - `python -m ipykernel install --user --name hs2025 --display-name "Python (.venv hs2025)"` → `Installed kernelspec hs2025 in /Users/jeremynathan/Library/Jupyter/kernels/hs2025`
- Tooling-Hinweis: In mehreren Tool-Ausgaben erschien `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted`.

**Änderungen**
- Geändert: `CHAT_JOURNAL.md` (dieser Eintrag ergänzt)
- Neu: keine
- Gelöscht: keine
- Rückgängig gemacht: nichts dokumentiert
- **Keine Dateiänderungen**: nein

**Ergebnis**
- Label-Verteilung für die vorhandenen EURUSD-Labels ist bekannt (ca. 49% neutral, 26% down, 25% up).
- Jupyter-Kernel `hs2025` wurde lokal im User-Home registriert; VS Code zeigte im Kernel-Dialog weiterhin keine Auswahl (Ursache unklar; Stand Ende Chat).

**Offen / Nicht gemacht (bewusst)**
- Keine Änderungen an `src/`-Code oder Notebooks durchgeführt (außer diesem Journal-Eintrag).
- Keine Tests/Linting/Formatter ausgeführt.
- Keine `yfinance`-Downloads oder News-Processing im Tooling ausgeführt.
- Netzwerk:
  - Tooling/CLI in dieser Session: keine Netzwerkcalls dokumentiert.
  - User führte `pip install ...` aus; ob Pakete aus Cache oder via Netzwerk geladen wurden, ist *unklar*.

### 2025-12-17 20:47 CET — VS Code Update: Troubleshooting-Checkliste + Vorgehens-Zusammenfassung

**Ziel**
- Gründe/typische Ursachen klären, warum Visual Studio Code nicht updatet, und ein Vorgehen zur Fehlersuche festhalten.

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: Ausgabe von `git status -sb`
  ```text
  ## main...origin/main [ahead 4]
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   ...
  ```
- Status dieses Files: Ausgabe von `git status -sb -- CHAT_JOURNAL.md`
  ```text
  ## main...origin/main [ahead 4]
  ?? CHAT_JOURNAL.md
  ```
- Relevante Dateien: `CHAT_JOURNAL.md` (dieser Eintrag); weitere vom User erwähnte/geöffnete Dateien: `scripts/fetch_finance.sh`, `src/utils/io.py`, `README.md`, `src/data/load_finance.py`, `data/processed/fx/eurusd_labels.csv` (Kontext; in dieser Session nicht bearbeitet).
- VS-Code-Umgebung/Fehlermeldung: *unklar* (User nannte keine konkrete Fehlermeldung/OS-Details im Chat).

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): keine (keine Commits im Chat erstellt).

**Vorgehen (was gemacht wurde)**
- User-Frage beantwortet: typische Ursachen für fehlende VS-Code-Updates gesammelt (Rechte/Installationsort, parallel laufende Prozesse, Antivirus/Firewall, Proxy/Netzwerk, Unternehmens-Policies) und eine Reihenfolge zur Prüfung vorgeschlagen.
- Workaround genannt: aktuelle Version manuell herunterladen und überinstallieren bzw. „User Setup“ nutzen; bei Policy-Themen IT/Admin einbeziehen.
- Auf User-Wunsch das Vorgehen als kurze Zusammenfassung wiedergegeben.

**Kommandos/Outputs (wichtigste)**
- `git status -sb`
- `git status -sb -- CHAT_JOURNAL.md`
- `git log --oneline --decorate -n 10`
- Tooling-Hinweis: Bei Tool-Ausgaben erschien `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted`.

**Änderungen**
- Geändert: `CHAT_JOURNAL.md` (neuer Eintrag am Ende; `git status -sb -- CHAT_JOURNAL.md` zeigt `??`)
- Neu: keine
- Gelöscht: keine
- Rückgängig gemacht: nichts
- **Keine Dateiänderungen**: nein

**Ergebnis**
- Checkliste/Vorgehensplan zur Fehlersuche für VS-Code-Update-Probleme dokumentiert; keine technische Diagnose am VS-Code-Setup selbst durchgeführt.

**Offen / Nicht gemacht (bewusst)**
- Keine VS-Code-Update-Aktion ausgeführt (nur Beratung/Checkliste).
- Keine Packages installiert.
- Keine Tests/Linting/Formatter ausgeführt.
- Keine Netzwerkcalls über Tooling/CLI ausgeführt.

### 2025-12-17 20:52 CET — VS Code Jupyter: Kernel-Auswahl leer

**Ziel**
- Jupyter Notebook in VS Code verwenden; Kernel auswählen können.

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: Ausgabe von `git status -sb` (gekürzt)
  ```text
  ## main...origin/main [ahead 4]
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   ...
  ```
- Status dieses Files: Ausgabe von `git status -sb -- CHAT_JOURNAL.md`
  ```text
  ## main...origin/main [ahead 4]
  ?? CHAT_JOURNAL.md
  ```
- Relevante Dateien: `notebooks/eda_labels.ipynb`, `requirements.txt`, `.venv/`, `src/data/load_finance.py`, `src/data/label_eurusd.py`, `config/symbols.yaml`, `data/raw/fx/EURUSDX.csv`, `data/processed/fx/eurusd_labels.csv`

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): keine (keine Commits im Chat erstellt).

**Vorgehen (was gemacht wurde)**
- User-Problem aufgenommen: In VS Code erscheint bei `Select Kernel` keine Auswahl (leere Liste).
- Repo geprüft: `.venv/` existiert; `ipykernel` ist in `.venv` installiert.
- Kernel-Registrierung geprüft: es gab keinen sichtbaren Jupyter-Kernel-Spec-Ordner; `jupyter kernelspec list` scheiterte in der Tool-Umgebung mit PermissionError beim Erstellen von `~/.jupyter`.
- Nächste Schritte vorgeschlagen (für lokale Ausführung außerhalb der Tool-Sandbox): `~/.jupyter` + `~/.local/share/jupyter/kernels` anlegen, Kernel aus `.venv` registrieren (`python -m ipykernel install --user ...`), dann in VS Code den Kernel auswählen.
- Zusätzlicher Befund aus User-Screenshot: Jupyter-Extension zeigt Runtime-Fehler `this.vscNotebook.onDidChangeNotebookCellExecutionState is not a function`; empfohlen wurden VS-Code-Update oder (falls Update nicht möglich) Downgrade der Jupyter-Extension.
- User bat um Update-Hilfe: Schrittfolge zum Updaten (Check for Updates / manuelles Installieren) beschrieben; User-Screenshot zeigt danach VS Code Version `1.104.3 (Universal)` (Details nur per Screenshot belegt).
- Bei weiterem Nicht-Funktionieren: vorgeschlagen, Jupyter/Python-Extensions zu de-/reinstallieren (Stable), `Developer: Reload Window`, `Jupyter: Clear Cache and Reload` und Errors in `Help → Toggle Developer Tools → Console` zu prüfen.

**Kommandos/Outputs (wichtigste)**
- `ls` / `ls -a` → zeigt u. a. `.venv/`, `requirements.txt`, `notebooks/`, `src/`
- `.venv/bin/python -m pip list` → u. a. `ipykernel 7.1.0`, `jupyter_client 8.6.3`, `jupyter_core 5.9.1`
- `ls ~/.local/share/jupyter/kernels` → `No such file or directory`
- `.venv/bin/jupyter kernelspec list` → Traceback endet mit:
  - `PermissionError: [Errno 1] Operation not permitted: '/Users/jeremynathan/.jupyter'`
- Tooling-Hinweis: In Tool-Ausgaben erschien wiederholt
  - `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted`
  - einmalig auch: `/opt/homebrew/Library/Homebrew/brew.sh: line 60: cannot create temp file for here document: Operation not permitted`

**Änderungen**
- Geändert: `CHAT_JOURNAL.md` (dieser Eintrag ergänzt)
- Neu: keine
- Gelöscht: keine
- Rückgängig gemacht: nichts dokumentiert
- **Keine Dateiänderungen**: nein

**Ergebnis**
- Root Cause in der Tool-Umgebung: Jupyter konnte keinen Kernelspec lesen/erzeugen, weil Schreiben nach `~/.jupyter` nicht erlaubt war; zusätzlich deutet der User-Screenshot auf ein VS-Code/Jupyter-Extension-Kompatibilitätsproblem hin.

**Offen / Nicht gemacht (bewusst)**
- Keine VS-Code-/Extension-Änderungen lokal ausgeführt (nur Anleitung; Update-Erfolg basiert auf User-Screenshot).
- Keine Kernel-Registrierung lokal ausgeführt (nur vorgeschlagen).
- Keine Packages installiert, keine Tests/Linting/Formatter ausgeführt.
- Keine Netzwerkcalls über Tooling/CLI ausgeführt.

### 2025-12-17 20:56 CET — VS Code Jupyter: Extension activation failed

**Ziel**
- Den VS-Code-Fehler „Extension activation failed“ (Quelle: Jupyter) eingrenzen und eine praktikable Lösung ableiten.

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: `git status -sb` (Ausgabe gekürzt; sehr lang)
  ```text
  ## main...origin/main [ahead 4]
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   M notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb
   M notebooks/eodhd_two_stage/2_train_eodhd.ipynb
   ...
  ```
- Status dieses Files: `git status -sb -- CHAT_JOURNAL.md`
  ```text
  ## main...origin/main [ahead 4]
  ?? CHAT_JOURNAL.md
  ```
- Relevante Dateien: keine Repo-Dateien waren Ursache; es ging um VS Code / Jupyter-Extension.

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): keine (keine Commits im Chat erstellt).

**Vorgehen (was gemacht wurde)**
- User gemeldet: „der error bleibt“ bei Jupyter in VS Code (Extension-Aktivierung schlägt fehl).
- Anleitung gegeben, wo die Logs in VS Code zu finden sind: `Developer: Toggle Developer Tools` → Console, sowie Output Channels „Jupyter“/„Jupyter Server“.
- User lieferte Console-Fehler (Screenshot). Daraus abgeleitet: Kompatibilitätsproblem zwischen VS Code und Jupyter-Extension (fehlende Notebook-API).
- Lösungsvorschläge gegeben:
  - VS Code wirklich aktualisieren (inkl. Hinweis auf manuelle Neuinstallation, wenn „Check for Updates“ nicht greift).
  - Alternativ: Jupyter-Extension auf eine ältere Version downgraden (`Install Another Version…`) und Auto-Update deaktivieren.
- User fragte nach Zusammenfassung; kurze Zusammenfassung des Vorgehens geliefert.

**Kommandos/Outputs (wichtigste)**
- VS Code DevTools Console (aus User-Screenshot):
  - `TypeError: this.vscNotebook.onDidChangeNotebookCellExecutionState is not a function`
  - Zusätzlich sichtbar: `ERR TreeError [DebugRepl] Tree input not set` und `ERR An unknown error occurred. Please consult the log for more details.`
- VS Code Version (aus User-Screenshot):
  - `Version: 1.104.3 (Universal)`; `OS: Darwin arm64 25.1.0`
  - Weitere Details (Electron/Node/Chromium) nur per Screenshot belegt.
- Tooling (bei CLI-Kommandos in dieser Session):
  - `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted`

**Änderungen**
- Geändert: `CHAT_JOURNAL.md` (dieser Eintrag ergänzt)
- Neu: keine
- Gelöscht: keine
- Rückgängig gemacht: nichts
- **Keine Dateiänderungen**: nein

**Ergebnis**
- Diagnose: Jupyter-Extension scheitert an einer VS-Code-Notebook-API (`onDidChangeNotebookCellExecutionState`), was auf ein VS Code ↔ Extension Versionsmismatch hindeutet.
- Konkrete Fix-Optionen: VS Code manuell aktualisieren oder Jupyter-Extension downgraden (Umsetzung durch User; Erfolg unklar).

**Offen / Nicht gemacht (bewusst)**
- Keine VS-Code-/Extension-Änderungen lokal ausgeführt (nur Anleitung).
- Keine Repo-Codeänderungen (außer Journal-Eintrag).
- Keine Packages installiert, keine Tests/Linting/Formatter ausgeführt.
- Keine Netzwerkcalls über Tooling/CLI ausgeführt.

### 2025-12-17 — EURUSD Label-EDA (Notebook) + GDELT-Downloader Versuch + Rollback

**Ziel**
- Label-CSV (`up/down/neutral`) aus EURUSD-Kursen prüfen (EDA im Notebook).
- Nächste Schritte Richtung News-Features vorbereiten (kostenlose Quelle diskutieren; GDELT als Kandidat).

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: `git status -sb` (Ausgabe stark gekürzt; außerdem erscheint bei Tooling wiederholt)
  - `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted`
  ```text
  ## main...origin/main [ahead 4]
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   ...
  ```
  - Hinweis: Die sehr vielen `M/D/??` Einträge im Workspace sind sichtbar, aber es ist *unklar*, welche davon in dieser Chat-Session entstanden sind.
- Relevante Dateien: `data/processed/fx/eurusd_labels.csv`, `data/raw/fx/EURUSDX.csv`, `src/data/label_eurusd.py`, `notebooks/eda_labels.ipynb` (lokal beim User), `requirements.txt` (kurzzeitig angepasst, später zurückgesetzt)

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): keine (keine Commits im Chat erstellt).

**Vorgehen (was gemacht wurde)**
- Label-CSV lokal ausgelesen und die Klassenverteilung geprüft.
- Notebook-Problem analysiert: `FileNotFoundError` trotz vorhandener Datei → Ursache war das Arbeitsverzeichnis (`notebooks/`); Lösung: einmalig `os.chdir("..")` oder Pfad `../data/...`.
- Notebook-Plot scheiterte wegen fehlendem `matplotlib` → Installation empfohlen; zusätzlich wurde `matplotlib==3.9.2` kurzzeitig in `requirements.txt` ergänzt, um Setup für Dritte zu vereinheitlichen (später zurückgesetzt).
- Label-Logik diskutiert: scheinbar „balancierte“ Klassenverteilung ist konsistent mit Schwellenwahl (±0.5% über 3 Tage) und der empirischen Return-Verteilung.
- News-Quellen evaluiert: Google News verworfen (keine stabile/offizielle API, Historie problematisch); GDELT als kostenlose historische Quelle ab 2015 gewählt.
- Versuch, einen GDELT-Downloader (`src/data/fetch_gdelt.py`) schrittweise aufzubauen und zu testen; dabei traten mehrfach URL-/404- und SSL-Zertifikatsprobleme auf.
- Auf User-Wunsch: Repository auf den letzten Commit zurückgesetzt (inkl. Entfernen untracked Dateien) mittels `git reset --hard` und `git clean -fd`. Danach war `git status` leer (zu diesem Zeitpunkt).

**Kommandos/Outputs (wichtigste)**
- Labels (aus `data/processed/fx/eurusd_labels.csv`) per Python ausgewertet:
  - Counts: `down 724`, `neutral 1387`, `up 714`
  - Anteile: `down 25.63%`, `neutral 49.10%`, `up 25.27%`
  - `lookahead_return.describe()` (Auszug): `mean -0.000008`, `std 0.008588`, `min -0.045315`, `max 0.041826`
- Notebook-Fehler:
  - `FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/fx/eurusd_labels.csv'` (trotz existierender Datei; Ursache: Arbeitsverzeichnis)
  - `ModuleNotFoundError: No module named 'matplotlib'`
- Tooling/Sandbox-Einschränkung:
  - `bash: cannot create temp file for here document: Operation not permitted` (bei Here-Doc)
  - `bash: python: command not found` (nur `python3` verfügbar)
- GDELT-Downloader Versuche (Auszüge):
  - `curl: (6) Could not resolve host: data.gdeltproject.org` (Netzwerkrestriktion/Resolution)
  - `HTTP Error 404: Not Found` (URL-Struktur/Archiv unklar)
  - `[SSL: CERTIFICATE_VERIFY_FAILED] ... unable to get local issuer certificate` (HTTPS im lokalen Python)
  - `zsh: number expected` (ungültiger `--end` Zeitstempel wie `2024-01-01T01`)
  - `name 'build_gkg_url' is not defined` (Zwischenzustand im Skript, danach behoben)
- Rollback:
  - `git reset --hard HEAD` → `HEAD is now at 7475f51 feat: add EURUSD labeling script` (zu diesem Zeitpunkt)
  - `git clean -fd` → entfernte u. a. `docs/`, `notebooks/`, `tests/`, `src/data/fetch_gdelt.py` (untracked; Herkunft teils unklar)

**Änderungen**
- Geändert:
  - `requirements.txt` (kurzzeitig `matplotlib==3.9.2` ergänzt; danach via Reset rückgängig)
  - `src/data/fetch_gdelt.py` (neu erstellt und mehrfach angepasst; danach via Clean gelöscht)
  - `CHAT_JOURNAL.md` (dieser Eintrag ergänzt)
- Neu:
  - `src/data/fetch_gdelt.py` (zeitweise; später gelöscht)
- Gelöscht:
  - `src/data/fetch_gdelt.py` (via `git clean -fd`)
  - `docs/` (via `git clean -fd`, unklar ob in dieser Session erstellt)
  - `notebooks/` (via `git clean -fd`, unklar ob in dieser Session erstellt)
  - `tests/` (via `git clean -fd`, unklar ob in dieser Session erstellt)
- Rückgängig gemacht:
  - `requirements.txt` Änderungen via `git reset --hard HEAD`
  - Allgemein: Rückkehr zu „letzter Commit“-Version via `git reset --hard HEAD` + `git clean -fd`
- **Keine Dateiänderungen**: nein

**Ergebnis**
- Label-CSV ist konsistent und plausibel für Lookahead 3 Tage / ±0.5% (Neutral dominiert ~49%, Up/Down ~25% je).
- Notebook kann die Datei laden, wenn Arbeitsverzeichnis korrigiert wird; Plot benötigt `matplotlib`.
- GDELT-Download konnte in dieser Session nicht stabil abgeschlossen werden (Netzwerk/DNS/SSL und 404/URL-Struktur).
- Repo wurde auf User-Wunsch auf den letzten Commit zurückgesetzt; experimentelle Änderungen wurden entfernt.

**Offen / Nicht gemacht (bewusst)**
- Kein ML-Modell trainiert, kein News-Processing produktiv implementiert.
- Keine Tests/Linting/Formatter ausgeführt.
- Keine erfolgreichen GDELT-Downloads über den implementierten Downloader (Fehler oben).
- (unklar) Ob der User lokal `pip install matplotlib` tatsächlich ausgeführt hat; Empfehlung wurde gegeben.

### 2025-12-17 21:09 CET — EURUSD News → Zwei-Stufen-XGBoost Experimente + PDF-Report

**Ziel**
- Reproduzierbarer Workflow von Rohdaten (FX + News) zu Modell-Ergebnissen (JSON + PDF), ohne dass sich Dateien gegenseitig überschreiben (Experiment-IDs).
- Zwei-Stufen-Ansatz: (1) Signal „move vs neutral“, (2) Richtung „up vs down“.

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: `git status -sb` (gekürzt; die vollständige Liste steht unten im Abschnitt „Änderungen“)
  ```text
  ## main...origin/main [ahead 4]
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   M notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb
   M notebooks/eodhd_two_stage/2_train_eodhd.ipynb
   M notebooks/eodhd_two_stage/3_eval_eodhd.ipynb
   M notebooks/final_two_stage/1_data_prep_final.ipynb
   M notebooks/final_two_stage/2_train_final.ipynb
   M notebooks/final_two_stage/3_eval_final.ipynb
   …
  ```
- Relevante Dateien (Auszug, siehe auch „Änderungen“): `src/data/label_eurusd.py`, `src/models/train_xgboost_two_stage.py`, `scripts/generate_two_stage_report.py`, Notebooks unter `notebooks/…`, Ergebnisdateien unter `notebooks/results/…`.

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): *unklar* (es wurden im Chat mehrere Commits erwähnt/ausgeführt; sicher belegt ist dieser Commit aus dem Chat-Verlauf:)
  - `571168d feat(data): update EURUSD labels and two-stage model notebooks`
- Commit-Inhalt (kurz): `git show --stat 571168d`
  ```text
  commit 571168d09452a199c83f739bf7278d5c0427133e
  Author: Jerycodes <129053489+Jerycodes@users.noreply.github.com>
  Date:   Sat Nov 15 17:46:44 2025 +0100

      feat(data): update EURUSD labels and two-stage model notebooks

   data/processed/fx/eurusd_labels.csv                | 5643 ++++++++++----------
   notebooks/eda_eurusd_news.ipynb                    |  318 ++
   notebooks/notebooks/model_xgboost_two_stage.ipynb  | 1702 ++++++
   .../results/two_stage_v0_h4_thr1pct_strict.json    |  326 ++
   requirements.txt                                   |    3 +
   src/data/build_training_set.py                     |   50 +-
   src/data/label_eurusd.py                           |   83 +-
   src/models/train_xgboost_two_stage.py              |  245 +
   8 files changed, 5534 insertions(+), 2836 deletions(-)
  ```
  - Details: `git show 571168d`

**Vorgehen (was gemacht wurde)**
- API/News:
  - EODHD News-API im Projekt verwendet (Token via `EODHD_TOKEN` oder `--token` im Downloader).
  - News wurden lokal als JSONL gespeichert; danach wurden Tages-Features (z. B. Anzahl Artikel/Tag und Sentiment-Aggregate) erzeugt und mit FX-Daten gemerged.
- Labeling:
  - EURUSD-Labels wurden iterativ angepasst (Horizon/Schwellen/Monotonie-Bedingung), um „up/down“ nur bei „sauberem“ Bewegungsverlauf zu zählen (anstatt starker Zwischen-Schwankungen).
  - Aus `label` wurden zusätzlich `signal` (neutral vs move) und `direction` (down vs up, nur wenn move) abgeleitet.
- Features:
  - Zusätzliche Feature-Ideen diskutiert und umgesetzt (u. a. Kalender-Features wie Monat/Quartal; Candle-/Preis-Features wie Range/Body/Shadows; Sentiment-Shares).
  - Es gab dabei Verwirrung, ob alle Features im CSV auftauchen; Ursache war zeitweise (unklar) ein „alter“ Import-/Kernel-Stand im Notebook oder ein falscher Pfad/Arbeitsverzeichnis.
- Training (Two-Stage XGBoost):
  - Zwei Modelle trainiert: Stufe 1 (Signal), Stufe 2 (Direction).
  - Evaluationsfokus: Precision/Recall der „move“-Klasse (Stufe 1) und Precision/Recall für up/down (Stufe 2); zusätzlich kombinierte 3-Klassen-Auswertung.
  - Typische Notebook-Probleme wurden gelöst: `ModuleNotFoundError: No module named 'src'` (Python-Pfad/Working-Dir), `FileNotFoundError` (relativer Pfad im Notebook), fehlende Python-Pakete (z. B. `sklearn`, `xgboost`).
- Ergebnis-Speicherung (Reproduzierbarkeit):
  - Ergebnisse pro Experiment als JSON gespeichert (Name enthält `EXP_ID`), inkl. Label-Parameter, Datensatzpfad, Feature-Liste und (falls vorhanden) Modell-Parameter/Feature-Importances.
  - Zusätzlich wurden PDFs für Reports generiert, die Konfiguration + Plots + Tabellen zusammenfassen sollen.
- Report (PDF):
  - Ein Report-Skript erstellt/erweitert, das aus JSON + CSV ein PDF baut (Metriken tabellarisch, Confusion Matrices, Feature Importance, Verteilungen, und eine Preis-Zeitreihe mit markierten up/down/neutral-Tagen).
  - Layout-Probleme (Text zu weit rechts, abgeschnitten, kein Umbruch auf Folgeseite) wurden identifiziert; Anpassungen an Margin/Zeilenabstand/Zeilenumbruch waren nötig.

**Kommandos/Outputs (wichtigste)**
- Package/Umgebung (User-Terminal):
  - `pip install -r requirements.txt` → `zsh: command not found: pip` (Workaround: `python3 -m pip …`)
  - `python3 -m src.models.train_xgboost_two_stage` → `ModuleNotFoundError: No module named 'sklearn'`
- Notebook/Imports:
  - `ModuleNotFoundError: No module named 'src'` (Notebook-Kernel startete nicht im Projekt-Root / `sys.path` fehlte)
  - `FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/fx/eurusd_labels.csv'` (Pfad/Working-Dir im Notebook)
- XGBoost-Hinweis:
  - Warnung im Output: `early_stopping_rounds` in `fit()` ist deprecated (XGBoost sklearn wrapper).
- PDF Report:
  - `python3 -m scripts.generate_two_stage_report --exp-id v1_h4_thr0p5pct_strict` → `KeyError: 'Close'` (Spaltenname/Quelle für Close-Preis im Report-Skript war inkonsistent).
- Tooling-Hinweis (in mehreren Command-Ausgaben):
  - `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted`

**Änderungen**
- Geändert (laut `git status --porcelain=v1 -uall`; vollständige Liste inkl. gelöschter/neu angelegter Dateien unten):
  - `README.md`
  - `config/symbols.yaml`
  - `data/processed/fx/eurusd_labels.csv`
  - `notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb`
  - `notebooks/eodhd_two_stage/2_train_eodhd.ipynb`
  - `notebooks/eodhd_two_stage/3_eval_eodhd.ipynb`
  - `notebooks/final_two_stage/1_data_prep_final.ipynb`
  - `notebooks/final_two_stage/2_train_final.ipynb`
  - `notebooks/final_two_stage/3_eval_final.ipynb`
  - `scripts/compare_experiments_pnl.py`
  - `scripts/generate_two_stage_report.py`
  - `src/data/label_eurusd.py`
  - `src/models/train_xgboost_two_stage.py`
- Rückgängig gemacht: nichts explizit per `git restore`/`git checkout`/`git reset`/`git clean` in diesem Teil des Chats dokumentiert (*unklar*).
- **Keine Dateiänderungen**: nein
- Vollständige Liste (Status + Pfade):
  ```text
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   M notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb
   M notebooks/eodhd_two_stage/2_train_eodhd.ipynb
   M notebooks/eodhd_two_stage/3_eval_eodhd.ipynb
   M notebooks/final_two_stage/1_data_prep_final.ipynb
   M notebooks/final_two_stage/2_train_final.ipynb
   M notebooks/final_two_stage/3_eval_final.ipynb
   D notebooks/results/final_two_stage/two_stage_final__hp1_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hpL1_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long1_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p3pct_hit_7_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_2_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_8_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p5pct_hit_3_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p6pct_hit_6_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h5_thr0p4pct_hit_5_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h5_thr0p5pct_hit_4_report.pdf
   M notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_2_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_3_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_4_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv1_h4_thr0p3pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv2_h4_thr0p4pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv3_h4_thr0p5pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv4_h4_thr0p4pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_2_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_3_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_4_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_5_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_6_2_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_6_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv10_h4_thr0p_55pct_tolerant0p1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv11_h4_thr0p_4pct_tolerant0p1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv12_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv13_h4_thr0p_3pct_tolerant0p1pct_4p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv14_h4_thr0p_3pct_tolerant0p1pct_51p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv15_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv16_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv17_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv18_h4_thr0p_3pct_tolerant0p1pct_7p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv19_h4_thr0p_3pct_tolerant0p1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv1_h4_thr0p7pct_tolerant0p3pct_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv20_h4_thr0p_6pct_tolerant0p1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv21_h4_thr0p_6pct_tolerant0p6pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv22_h4_thr0p_3pct_tolerant_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv23_h3_thr0p_3pct_tolerant_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv24_h6_thr0p_6pct_tolerant_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv25_h6_thr1p_0pct_tolerant_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv26_h6_thr1p_0pct_strict_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv27_h6_thr1p_0pct_tolerant_p_pct_5p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv28_h6_thr1p_5pct_tolerant_p_pct_5p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv2_h4_thr0p_8pct_tolerant0p4pct_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv3_h4_thr0p_65pct_tolerant0p35pct_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv4_h4_thr0p_65pct_tolerant0p15pct_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv5_h4_thr0p_65pct_tolerant0p15pct_7p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv6_h4_thr0p_6pct_tolerant0p15pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv7_h4_thr0p_6pct_tolerant0p2pct_7p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv8_h4_thr0p_6pct_tolerant0p2pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv9_h4_thr0p_55pct_tolerant0p2pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__v0_h4_thr1pct_strict_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__v1_h4_thr0p5pct_strict_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__v3_h4_thr0p3pct_relaxed_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
   D notebooks/results/two_stage__v1_h4_thr0p5pct_strict_report.pdf
   D notebooks/results/two_stage__v2_h4_thr0p5pct_strict_newfeat_report.pdf
   D notebooks/results/two_stage__v3_h4_thr0p3pct_relaxed_report.pdf
   D notebooks/results/two_stage__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
   D notebooks/results/two_stage__v5_h4_thr0p5pct_tolerant0p3pct_spw1p0_report.pdf
   D notebooks/results/two_stage__v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2_report.pdf
   D notebooks/results/two_stage__v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600_report.pdf
   D notebooks/results/two_stage__v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain_report.pdf
   D notebooks/results/two_stage__v9_h4_thr0p5pct_tol0p3_30dfeat_report.pdf
   D notebooks/results/updown__s1_h4_thr0p5pct_tol0p3_report.pdf
   D notebooks/results/updown__s2_h4_thr0p5pct_tol0p3_report.pdf
   M scripts/compare_experiments_pnl.py
   M scripts/generate_two_stage_report.py
   M src/data/label_eurusd.py
   M src/models/train_xgboost_two_stage.py
  ?? CHAT_JOURNAL.md
  ?? docs/v2_pipeline.md
  ?? notebooks/results/final_two_stage/_debug_hp_long_result_report.pdf
  ?? notebooks/results/final_two_stage/_debug_hp_long_result_report_v2.pdf
  ?? notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3.pdf
  ?? notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3_full.pdf
  ?? notebooks/results/final_two_stage/pdf/compare__hp_long_result__vs__hp_result__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare__hp_long_result__vs__hv_result__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare__hp_result__vs__hp_long_result__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare__hp_result__vs__hv_result__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_3__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_3__B_pnl_lev20.png
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_4__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_4__B_pnl_lev20.png
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_3_vs_hp_long_final_yahoo_4__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_3_vs_hp_long_final_yahoo_4__B_pnl_lev20.png
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_eod_result__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_long_eod_1__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_long_eod_result__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_long_final_yahoo_2__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hv_eod_result__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_long_vs_hv_long__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__sl_tp.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only_exit.pdf
  ?? notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only_exit_v3.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v2.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v3.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v4.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v5.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v6.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v7.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v8.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp1_h4_thr0p4pct_hit_1_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hpL1_h4_thr0p4pct_hit_1_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long1_h4_thr0p4pct_hit_1_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p3pct_hit_7_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_1_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_2_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_8_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p5pct_hit_3_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p6pct_hit_6_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h5_thr0p4pct_hit_5_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h5_thr0p5pct_hit_4_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_final_yahoo_9_report_v2.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_2_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_3_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_4_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv1_h4_thr0p3pct_hit_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv2_h4_thr0p4pct_hit_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv3_h4_thr0p5pct_hit_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv4_h4_thr0p4pct_hit_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_2_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_3_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_4_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_5_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_6_2_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_6_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv10_h4_thr0p_55pct_tolerant0p1pct_6p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv11_h4_thr0p_4pct_tolerant0p1pct_6p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv12_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv13_h4_thr0p_3pct_tolerant0p1pct_4p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv14_h4_thr0p_3pct_tolerant0p1pct_51p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv15_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv16_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv17_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv18_h4_thr0p_3pct_tolerant0p1pct_7p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv19_h4_thr0p_3pct_tolerant0p1pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv1_h4_thr0p7pct_tolerant0p3pct_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv20_h4_thr0p_6pct_tolerant0p1pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv21_h4_thr0p_6pct_tolerant0p6pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv22_h4_thr0p_3pct_tolerant_p_pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv23_h3_thr0p_3pct_tolerant_p_pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv24_h6_thr0p_6pct_tolerant_p_pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv25_h6_thr1p_0pct_tolerant_p_pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv26_h6_thr1p_0pct_strict_p_pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv27_h6_thr1p_0pct_tolerant_p_pct_5p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv28_h6_thr1p_5pct_tolerant_p_pct_5p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv2_h4_thr0p_8pct_tolerant0p4pct_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv3_h4_thr0p_65pct_tolerant0p35pct_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv4_h4_thr0p_65pct_tolerant0p15pct_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv5_h4_thr0p_65pct_tolerant0p15pct_7p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv6_h4_thr0p_6pct_tolerant0p15pct_6p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv7_h4_thr0p_6pct_tolerant0p2pct_7p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv8_h4_thr0p_6pct_tolerant0p2pct_6p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__nv9_h4_thr0p_55pct_tolerant0p2pct_6p_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__v0_h4_thr1pct_strict_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__v1_h4_thr0p5pct_strict_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__v3_h4_thr0p3pct_relaxed_report.pdf
  ?? notebooks/results/final_two_stage/pdf/two_stage_final__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__final_yahoo.json
  ?? notebooks/results/final_two_stage/two_stage_final__final_yahoo_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__final_yahoo_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__final_yahoo_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_eod_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_eod_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_eod_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_eod_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_report.pdf
  ?? notebooks/results/pdf/two_stage__v1_h4_thr0p5pct_strict_report.pdf
  ?? notebooks/results/pdf/two_stage__v2_h4_thr0p5pct_strict_newfeat_report.pdf
  ?? notebooks/results/pdf/two_stage__v3_h4_thr0p3pct_relaxed_report.pdf
  ?? notebooks/results/pdf/two_stage__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
  ?? notebooks/results/pdf/two_stage__v5_h4_thr0p5pct_tolerant0p3pct_spw1p0_report.pdf
  ?? notebooks/results/pdf/two_stage__v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2_report.pdf
  ?? notebooks/results/pdf/two_stage__v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600_report.pdf
  ?? notebooks/results/pdf/two_stage__v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain_report.pdf
  ?? notebooks/results/pdf/two_stage__v9_h4_thr0p5pct_tol0p3_30dfeat_report.pdf
  ?? notebooks/results/pdf/updown__s1_h4_thr0p5pct_tol0p3_report.pdf
  ?? notebooks/results/pdf/updown__s2_h4_thr0p5pct_tol0p3_report.pdf
  ?? notebooks/results/two_stage__final_yahoo.json
  ?? notebooks/results/two_stage__hp_eod_result.json
  ?? notebooks/results/two_stage__hp_long_eod_1.json
  ?? notebooks/results/two_stage__hp_long_eod_final_yahoo_12.json
  ?? notebooks/results/two_stage__hp_long_eod_final_yahoo_13.json
  ?? notebooks/results/two_stage__hp_long_eod_result.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_10.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_11.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_12.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_2.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_3.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_4.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_5.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_6.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_7.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_8.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_9.json
  ?? notebooks/results/two_stage__hp_long_result.json
  ?? notebooks/results/two_stage__hp_long_yahoo_1.json
  ?? notebooks/results/two_stage__hp_long_yahoo_2.json
  ?? notebooks/results/two_stage__hp_long_yahoo_3.json
  ?? notebooks/results/two_stage__hp_long_yahoo_4.json
  ?? notebooks/results/two_stage__hp_long_yahoo_5.json
  ?? notebooks/results/two_stage__hp_long_yahoo_6.json
  ?? notebooks/results/two_stage__hp_long_yahoo_7.json
  ?? notebooks/results/two_stage__hp_result.json
  ?? notebooks/results/two_stage__hp_yahoo_1.json
  ?? notebooks/results/two_stage__hv_eod_result.json
  ?? notebooks/results/two_stage__hv_long_final_yahoo.json
  ?? notebooks/results/two_stage__hv_long_final_yahoo_2.json
  ?? notebooks/results/two_stage__hv_result.json
  ?? notebooks/results/two_stage__hv_yahoo_2.json
  ?? notebooks/v2_two_stage/0_calibrate_params_v2.ipynb
  ?? notebooks/v2_two_stage/1_run_experiments_v2.ipynb
  ?? notebooks/v2_two_stage/2_summarize_results_v2.ipynb
  ?? powerpoint/presentation.pptx
  ?? powerpoint/presentation_image_1.2
  ?? powerpoint/presentation_image_1.2.png
  ?? powerpoint/presentation_image_1.3.png
  ?? powerpoint/presentation_image_1.png
  ?? powerpoint/~$presentation.pptx
  ?? scripts/calibrate_trade_params_v2.py
  ?? scripts/compare_v2_experiments.py
  ?? scripts/compare_yahoo_vs_eod_experiments.py
  ?? scripts/run_two_stage_experiment_v2.py
  ?? scripts/summarize_v2_results.py
  ?? src/data/build_training_set_v2.py
  ?? src/data/label_eurusd_trade.py
  ?? src/experiments/__init__.py
  ?? src/experiments/v2_config.py
  ?? src/models/train_two_stage_v2.py
  ```

**Ergebnis**
- Zwei-Stufen-Training + Evaluation wurde im Notebook erfolgreich durchlaufen (inkl. Metriken/Plots) und Ergebnisse pro Experiment als JSON gespeichert.
- Ein PDF-Report konnte generiert werden, aber Layout-/Umbruch-Probleme und eine Spalten-Inkonsistenz (`Close`) wurden sichtbar und müssen bereinigt werden.

**Offen / Nicht gemacht (bewusst)**
- Kein `git push` in diesem Chat dokumentiert.
- Keine Tests/Linting/Formatter ausgeführt (keine entsprechenden Commands im Chat).
- Keine neuen Netzwerk-Calls über Tooling dokumentiert (Netzwerk ist im Sandbox-Kontext eingeschränkt); der User hat aber lokal Daten/APIs/Pip genutzt (*unklar*, welche Requests genau).

### 2025-12-17 21:36 CET — EODHD-FX Integration, Vergleich Yahoo vs. EODHD, Debugging Modellabweichungen

**Ziel**
- EODHD (End-of-Day Historical Data) als alternative Preis-Datenquelle für EURUSD in die bestehende 2‑Stufen‑Pipeline integrieren.
- Ergebnisse von Yahoo-Finance‑basierten Experimenten mit EODHD reproduzieren bzw. Abweichungen erklären.
- Rohdaten von Yahoo vs. EODHD (tagweise) vergleichen, um Verschiebungen/Unterschiede zu verstehen (Zeitzone/Wochenenden als Verdacht).

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Datum/Uhrzeit (System): `2025-12-17 21:36 CET`
- Branch/Status: Ausgabe von `git status -sb` (vollständige Dateiliste siehe „Änderungen“):
  ```text
  ## main...origin/main [ahead 4]
  ```
  - Hinweis: Bei mehreren Shell-Aufrufen erschien zusätzlich die Meldung:
    - `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted` (unklar, ob das Einfluss auf die Git-Ausgaben hat; Git-Kommandos liefen trotzdem durch).
- Relevante Dateien/Ordner (Auswahl):
  - EODHD-Notebooks: `notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb`, `notebooks/eodhd_two_stage/2_train_eodhd.ipynb`, `notebooks/eodhd_two_stage/3_eval_eodhd.ipynb`
  - Download/Tools: `scripts/download_eodhd_fx.py`, `scripts/eval_yahoo_model_on_eod.py`
  - Labeling/Preise: `src/data/label_eurusd.py`, Rohdaten `data/raw/fx/` (konkret verwendete Dateien teils unklar aus dem Chat)

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): *unklar*, welche Commits exakt „in diesem Chat“ erstellt wurden (im Chat wurde mehrfach über Committen gesprochen); Stand jetzt sind u. a. diese Commits lokal vor `origin/main`:
  - `a83dea3 feat(labeling): first-hit + weekday filter; report variants`
  - `46c107f feat(report): expand docs and add P&L comparison script`
  - `265f8af Update latest eurusd_labels snapshot`
  - `46f1cea Add EODHD FX pipeline and comparison tools`
  - (`f77ea1b hp_long price-only baseline + cleanup` ist älter datiert; Zugehörigkeit zu diesem Chat unklar)
- Commit-Inhalt (kurz): Ausgabe von `git show --stat <hash>`
  - `git show --stat a83dea3`
    ```text
    commit a83dea3654351dd72cbf60e02dd614fb06a686ba
    Author: Jerycodes <129053489+Jerycodes@users.noreply.github.com>
    Date:   Tue Dec 16 17:35:30 2025 +0100

        feat(labeling): first-hit + weekday filter; report variants

     notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb |  31 ++--
     notebooks/eodhd_two_stage/2_train_eodhd.ipynb     |  54 +++---
     notebooks/eodhd_two_stage/3_eval_eodhd.ipynb      |  62 ++++---
     notebooks/final_two_stage/1_data_prep_final.ipynb |  28 +--
     notebooks/final_two_stage/2_train_final.ipynb     |  39 ++--
     notebooks/final_two_stage/3_eval_final.ipynb      |  66 +++----
     scripts/compare_experiments_pnl.py                |  27 ++-
     scripts/generate_two_stage_report.py              | 207 +++++++++++++++++++++-
     src/data/label_eurusd.py                          | 102 ++++++++++-
     9 files changed, 477 insertions(+), 139 deletions(-)
    ```
    - Details: `git show a83dea3`
  - `git show --stat 46c107f`
    ```text
    commit 46c107fef17652cb72eeff6364e94a692fda17eb
    Author: Jerycodes <129053489+Jerycodes@users.noreply.github.com>
    Date:   Mon Dec 15 07:26:32 2025 +0100

        feat(report): expand docs and add P&L comparison script

     docs/experiment_timeline.csv                    |  111 ++
     docs/experiment_timeline.md                     | 1840 +++++++++++++++++++++++
     docs/full_report_hp_long_final_yahoo.md         |  479 ++++++
     docs/presentation_report_hp_long_final_yahoo.md |  487 ++++++
     docs/two_stage_timeline.csv                     |   75 +
     docs/two_stage_timeline.md                      | 1126 ++++++++++++++
     scripts/compare_experiments_pnl.py              |  246 +++
     scripts/generate_two_stage_report.py            |  991 +++++++++++-
     8 files changed, 5277 insertions(+), 78 deletions(-)
    ```
    - Details: `git show 46c107f`
  - `git show --stat 265f8af`
    ```text
    commit 265f8af41fa3d716aa36e318e6b0b170e1fe5bf9
    Author: Jerycodes <129053489+Jerycodes@users.noreply.github.com>
    Date:   Fri Dec 12 09:47:09 2025 +0100

        Update latest eurusd_labels snapshot

     data/processed/fx/eurusd_labels.csv | 5900 ++++++++++++++++++-----------------
     1 file changed, 3075 insertions(+), 2825 deletions(-)
    ```
    - Details: `git show 265f8af`
  - `git show --stat 46f1cea`
    ```text
    commit 46f1cea45a98366d6a608eb8b288523ee9a194f2
    Author: Jerycodes <129053489+Jerycodes@users.noreply.github.com>
    Date:   Fri Dec 12 09:46:04 2025 +0100

        Add EODHD FX pipeline and comparison tools

     notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb  | 180 +++++++
     notebooks/eodhd_two_stage/2_train_eodhd.ipynb      | 581 +++++++++++++++++++++
     notebooks/eodhd_two_stage/3_eval_eodhd.ipynb       | 249 +++++++++
     ...tage_final__hp_long_eod_h4_thr0p3pct_hit_7.json | 458 ++++++++++++++++
     ...nal__hp_long_eod_h4_thr0p3pct_hit_7_metrics.csv |   7 +
     ..._hp_long_eod_h4_thr0p3pct_hit_7_predictions.csv | 323 ++++++++++++
     ...inal__hp_long_eod_h4_thr0p3pct_hit_7_report.pdf | Bin 0 -> 203619 bytes
     ...tage_final__hp_long_eod_h4_thr0p4pct_hit_1.json | 458 ++++++++++++++++
     ...nal__hp_long_eod_h4_thr0p4pct_hit_1_metrics.csv |   7 +
     ..._hp_long_eod_h4_thr0p4pct_hit_1_predictions.csv | 323 ++++++++++++
     ...inal__hp_long_eod_h4_thr0p4pct_hit_1_report.pdf | Bin 0 -> 203466 bytes
     ...tage_final__hp_long_eod_h4_thr0p4pct_hit_2.json | 458 ++++++++++++++++
     ...nal__hp_long_eod_h4_thr0p4pct_hit_2_metrics.csv |   7 +
     ..._hp_long_eod_h4_thr0p4pct_hit_2_predictions.csv | 323 ++++++++++++
     ...inal__hp_long_eod_h4_thr0p4pct_hit_2_report.pdf | Bin 0 -> 203466 bytes
     ...tage_final__hp_long_eod_h4_thr0p4pct_hit_8.json | 458 ++++++++++++++++
     ...nal__hp_long_eod_h4_thr0p4pct_hit_8_metrics.csv |   7 +
     ..._hp_long_eod_h4_thr0p4pct_hit_8_predictions.csv | 323 ++++++++++++
     ...inal__hp_long_eod_h4_thr0p4pct_hit_8_report.pdf | Bin 0 -> 203466 bytes
     ...tage_final__hp_long_eod_h4_thr0p5pct_hit_3.json | 458 ++++++++++++++++
     ...nal__hp_long_eod_h4_thr0p5pct_hit_3_metrics.csv |   7 +
     ..._hp_long_eod_h4_thr0p5pct_hit_3_predictions.csv | 323 ++++++++++++
     ...inal__hp_long_eod_h4_thr0p5pct_hit_3_report.pdf | Bin 0 -> 203544 bytes
     ...tage_final__hp_long_eod_h4_thr0p6pct_hit_6.json | 458 ++++++++++++++++
     ...nal__hp_long_eod_h4_thr0p6pct_hit_6_metrics.csv |   7 +
     ..._hp_long_eod_h4_thr0p6pct_hit_6_predictions.csv | 323 ++++++++++++
     ...inal__hp_long_eod_h4_thr0p6pct_hit_6_report.pdf | Bin 0 -> 207717 bytes
     ...tage_final__hp_long_eod_h5_thr0p4pct_hit_5.json | 458 ++++++++++++++++
     ...nal__hp_long_eod_h5_thr0p4pct_hit_5_metrics.csv |   7 +
     ..._hp_long_eod_h5_thr0p4pct_hit_5_predictions.csv | 322 ++++++++++++
     ...inal__hp_long_eod_h5_thr0p4pct_hit_5_report.pdf | Bin 0 -> 204265 bytes
     ...tage_final__hp_long_eod_h5_thr0p5pct_hit_4.json | 458 ++++++++++++++++
     ...nal__hp_long_eod_h5_thr0p5pct_hit_4_metrics.csv |   7 +
     ..._hp_long_eod_h5_thr0p5pct_hit_4_predictions.csv | 322 ++++++++++++
     ...inal__hp_long_eod_h5_thr0p5pct_hit_4_report.pdf | Bin 0 -> 207655 bytes
     .../two_stage__hp_long_eod_h4_thr0p3pct_hit_7.json | 458 ++++++++++++++++
     .../two_stage__hp_long_eod_h4_thr0p4pct_hit_1.json | 458 ++++++++++++++++
     .../two_stage__hp_long_eod_h4_thr0p4pct_hit_2.json | 458 ++++++++++++++++
     .../two_stage__hp_long_eod_h4_thr0p4pct_hit_8.json | 458 ++++++++++++++++
     .../two_stage__hp_long_eod_h4_thr0p5pct_hit_3.json | 458 ++++++++++++++++
     .../two_stage__hp_long_eod_h4_thr0p6pct_hit_6.json | 458 ++++++++++++++++
     .../two_stage__hp_long_eod_h5_thr0p4pct_hit_5.json | 458 ++++++++++++++++
     .../two_stage__hp_long_eod_h5_thr0p5pct_hit_4.json | 458 ++++++++++++++++
     requirements.txt                                   |   1 +
     scripts/download_eodhd_fx.py                       | 140 +++++
     scripts/eval_yahoo_model_on_eod.py                 | 152 ++++++
     src/data/label_eurusd.py                           |  19 +-
     47 files changed, 11287 insertions(+), 1 deletion(-)
    ```
    - Details: `git show 46f1cea`
  - `git show --stat f77ea1b` (Zugehörigkeit zu diesem Chat unklar)
    ```text
    commit f77ea1bcafccea0ab78b6d420e45da7ba6ce214d
    Author: Jerycodes <129053489+Jerycodes@users.noreply.github.com>
    Date:   Sun Nov 30 19:40:12 2025 +0100

        hp_long price-only baseline + cleanup

     notebooks/final_two_stage/1_data_prep_final.ipynb  |  16 +-
     notebooks/final_two_stage/2_train_final.ipynb      |  51 +--
     notebooks/final_two_stage/3_eval_final.ipynb       |  66 +--
     ..._stage_final__hp_long_h4_thr0p4pct_hit_1_3.json | 443 +++++++++++++++++++
     ..._stage_final__hp_long_h4_thr0p4pct_hit_1_4.json | 470 +++++++++++++++++++++
     .../two_stage__hp_long_h4_thr0p4pct_hit_1_3.json   | 443 +++++++++++++++++++
     .../two_stage__hp_long_h4_thr0p4pct_hit_1_4.json   | 470 +++++++++++++++++++++
     src/data/build_training_set.py                     |   8 +
     src/features/eurusd_features.py                    |  18 +
     9 files changed, 1916 insertions(+), 69 deletions(-)
    ```
    - Details: `git show f77ea1b`

**Vorgehen (was gemacht wurde)**
- EODHD als Datenquelle diskutiert (CSV vs. JSON; EODHD‑Python‑Library `eodhd` wurde vom User installiert).
- Neue EODHD‑Notebooks wurden verwendet/angelegt, um Data‑Prep → Training → Eval (PDF‑Report) separat vom bisherigen `final_two_stage` Ablauf nachzubilden.
- `scripts/download_eodhd_fx.py` wurde verwendet, um EURUSD‑Preise über EODHD zu laden (API‑Key über Umgebungsvariable (ENV)).
- Debugging: beim direkten Ausführen von Scripts (`python scripts/...`) traten Import-Probleme (`No module named 'src'`) auf; danach wurde die Ausführung erneut versucht.
- Modell-/Ergebnisabweichungen wurden untersucht (Stufe 2 „Richtung“ kollabiert in manchen Runs; kombinierte Vorhersage teilweise nur `neutral`).
- Vergleichsidee umgesetzt: Yahoo‑trainiertes Modell auf EODHD‑Testdaten auswerten (separates Script).

**Kommandos/Outputs (wichtigste)**
- Script‑Ausführung (User‑Terminal, Fehler und Fix‑Hinweis):
  - `python scripts/download_eodhd_fx.py --from-date 2015-01-01`
    - zuerst: `ModuleNotFoundError: No module named 'src'`
    - später: `ValueError: API key is invalid` (bis API‑Key korrekt gesetzt war; danach „hat es geklappt“).
- Training/Eval‑Output (aus Notebook‑Print, Beispiel; EXP_ID (Experiment Identifier) im Chat: `hp_long_eod_h4_thr0p4pct_hit_2`):
  ```text
  Signal scale_pos_weight: 0.18333333333333332
  Richtungs-Schwelle (val-basiert): 0.4 F1_up(val): 0.6112956810631229
  Richtungs-Schwellen (fix gesetzt): 0.3 0.7
  Signal-Schwelle (fix gesetzt): 0.7
  [ok] Ergebnisse gespeichert unter:
     JSON base : notebooks/results/two_stage__hp_long_eod_h4_thr0p4pct_hit_2.json
     JSON final: notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_2.json
  ```
  - Hinweis: Im Chat wurde explizit diskutiert, dass Schwellen „kostenbasiert wie zuvor“ sein sollen; im Code/Output tauchten sowohl kostenbasierte Berechnung als auch „fix gesetzt“ auf (welche Schwellen am Ende tatsächlich verwendet wurden, war für den User nicht nachvollziehbar).
- Yahoo‑Modell auf EODHD‑Testdaten (User‑Run von `python scripts/eval_yahoo_model_on_eod.py`, Screenshot):
  - Stufe 1 (Signal) Konfusionsmatrix (Confusion Matrix):
    - `[[ 4 60], [17 241]]`
  - Stufe 2 (Richtung) Konfusionsmatrix (Confusion Matrix):
    - `[[70 53], [79 56]]`

**Änderungen**
- Geändert: siehe vollständige Liste unten (`M …`).
- Neu: siehe vollständige Liste unten (`?? …`).
- Gelöscht: siehe vollständige Liste unten (`D …`).
- Rückgängig gemacht: Im Chat wurde das „Rückgängig machen“ eines Filter-Versuchs (Wochenenden/verschobene Tage) gewünscht; konkrete Umsetzung/Kommandos dazu sind *unklar*. In der Git‑Historie ist mindestens ein „weekday filter“ in `a83dea3` sichtbar.
- **Keine Dateiänderungen**: nein
- Stand Arbeitsverzeichnis (vollständig): `git status --porcelain=v1` (274 Zeilen)
  ```text
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   M notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb
   M notebooks/eodhd_two_stage/2_train_eodhd.ipynb
   M notebooks/eodhd_two_stage/3_eval_eodhd.ipynb
   M notebooks/final_two_stage/1_data_prep_final.ipynb
   M notebooks/final_two_stage/2_train_final.ipynb
   M notebooks/final_two_stage/3_eval_final.ipynb
   D notebooks/results/final_two_stage/two_stage_final__hp1_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hpL1_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long1_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p3pct_hit_7_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_2_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_8_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p5pct_hit_3_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p6pct_hit_6_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h5_thr0p4pct_hit_5_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h5_thr0p5pct_hit_4_report.pdf
   M notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_2_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_3_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_4_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv1_h4_thr0p3pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv2_h4_thr0p4pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv3_h4_thr0p5pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv4_h4_thr0p4pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_2_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_3_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_4_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_5_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_6_2_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_6_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv10_h4_thr0p_55pct_tolerant0p1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv11_h4_thr0p_4pct_tolerant0p1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv12_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv13_h4_thr0p_3pct_tolerant0p1pct_4p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv14_h4_thr0p_3pct_tolerant0p1pct_51p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv15_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv16_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv17_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv18_h4_thr0p_3pct_tolerant0p1pct_7p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv19_h4_thr0p_3pct_tolerant0p1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv1_h4_thr0p7pct_tolerant0p3pct_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv20_h4_thr0p_6pct_tolerant0p1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv21_h4_thr0p_6pct_tolerant0p6pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv22_h4_thr0p_3pct_tolerant_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv23_h3_thr0p_3pct_tolerant_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv24_h6_thr0p_6pct_tolerant_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv25_h6_thr1p_0pct_tolerant_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv26_h6_thr1p_0pct_strict_p_pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv27_h6_thr1p_0pct_tolerant_p_pct_5p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv28_h6_thr1p_5pct_tolerant_p_pct_5p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv2_h4_thr0p_8pct_tolerant0p4pct_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv3_h4_thr0p_65pct_tolerant0p35pct_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv4_h4_thr0p_65pct_tolerant0p15pct_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv5_h4_thr0p_65pct_tolerant0p15pct_7p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv6_h4_thr0p_6pct_tolerant0p15pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv7_h4_thr0p_6pct_tolerant0p2pct_7p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv8_h4_thr0p_6pct_tolerant0p2pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__nv9_h4_thr0p_55pct_tolerant0p2pct_6p_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__v0_h4_thr1pct_strict_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__v1_h4_thr0p5pct_strict_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__v3_h4_thr0p3pct_relaxed_report.pdf
   D notebooks/results/final_two_stage/two_stage_final__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
   D notebooks/results/two_stage__v1_h4_thr0p5pct_strict_report.pdf
   D notebooks/results/two_stage__v2_h4_thr0p5pct_strict_newfeat_report.pdf
   D notebooks/results/two_stage__v3_h4_thr0p3pct_relaxed_report.pdf
   D notebooks/results/two_stage__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
   D notebooks/results/two_stage__v5_h4_thr0p5pct_tolerant0p3pct_spw1p0_report.pdf
   D notebooks/results/two_stage__v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2_report.pdf
   D notebooks/results/two_stage__v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600_report.pdf
   D notebooks/results/two_stage__v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain_report.pdf
   D notebooks/results/two_stage__v9_h4_thr0p5pct_tol0p3_30dfeat_report.pdf
   D notebooks/results/updown__s1_h4_thr0p5pct_tol0p3_report.pdf
   D notebooks/results/updown__s2_h4_thr0p5pct_tol0p3_report.pdf
   M scripts/compare_experiments_pnl.py
   M scripts/generate_two_stage_report.py
   M src/data/label_eurusd.py
   M src/models/train_xgboost_two_stage.py
  ?? CHAT_JOURNAL.md
  ?? docs/v2_pipeline.md
  ?? notebooks/results/final_two_stage/_debug_hp_long_result_report.pdf
  ?? notebooks/results/final_two_stage/_debug_hp_long_result_report_v2.pdf
  ?? notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3.pdf
  ?? notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3_full.pdf
  ?? notebooks/results/final_two_stage/pdf/
  ?? notebooks/results/final_two_stage/two_stage_final__final_yahoo.json
  ?? notebooks/results/final_two_stage/two_stage_final__final_yahoo_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__final_yahoo_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__final_yahoo_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1.json
  ?? notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_eod_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_eod_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_eod_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_eod_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_result.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_result_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_result_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_result_report.pdf
  ?? notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2.json
  ?? notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_metrics.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_predictions.csv
  ?? notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_report.pdf
  ?? notebooks/results/pdf/
  ?? notebooks/results/two_stage__final_yahoo.json
  ?? notebooks/results/two_stage__hp_eod_result.json
  ?? notebooks/results/two_stage__hp_long_eod_1.json
  ?? notebooks/results/two_stage__hp_long_eod_final_yahoo_12.json
  ?? notebooks/results/two_stage__hp_long_eod_final_yahoo_13.json
  ?? notebooks/results/two_stage__hp_long_eod_result.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_10.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_11.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_12.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_2.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_3.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_4.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_5.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_6.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_7.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_8.json
  ?? notebooks/results/two_stage__hp_long_final_yahoo_9.json
  ?? notebooks/results/two_stage__hp_long_result.json
  ?? notebooks/results/two_stage__hp_long_yahoo_1.json
  ?? notebooks/results/two_stage__hp_long_yahoo_2.json
  ?? notebooks/results/two_stage__hp_long_yahoo_3.json
  ?? notebooks/results/two_stage__hp_long_yahoo_4.json
  ?? notebooks/results/two_stage__hp_long_yahoo_5.json
  ?? notebooks/results/two_stage__hp_long_yahoo_6.json
  ?? notebooks/results/two_stage__hp_long_yahoo_7.json
  ?? notebooks/results/two_stage__hp_result.json
  ?? notebooks/results/two_stage__hp_yahoo_1.json
  ?? notebooks/results/two_stage__hv_eod_result.json
  ?? notebooks/results/two_stage__hv_long_final_yahoo.json
  ?? notebooks/results/two_stage__hv_long_final_yahoo_2.json
  ?? notebooks/results/two_stage__hv_result.json
  ?? notebooks/results/two_stage__hv_yahoo_2.json
  ?? notebooks/v2_two_stage/
  ?? powerpoint/
  ?? scripts/calibrate_trade_params_v2.py
  ?? scripts/compare_v2_experiments.py
  ?? scripts/compare_yahoo_vs_eod_experiments.py
  ?? scripts/run_two_stage_experiment_v2.py
  ?? scripts/summarize_v2_results.py
  ?? src/data/build_training_set_v2.py
  ?? src/data/label_eurusd_trade.py
  ?? src/experiments/
  ?? src/models/train_two_stage_v2.py
  ```

**Ergebnis**
- EODHD‑Pipeline ist im Repo vorhanden (Notebooks + Scripts laut Git‑Historie).
- Beim Vergleich zeigten sich deutliche Abweichungen in Modellverhalten/Performance zwischen Yahoo‑ und EODHD‑Trainings (insb. Stage‑2 Richtung).
- Die Ursache der Abweichungen wurde im Chat als mögliches Zusammenspiel aus Datenquelle (EODHD vs Yahoo), Wochenend-/Kalender-Handling und Schwellenlogik diskutiert; endgültige Klärung blieb offen.

**Offen / Nicht gemacht (bewusst)**
- Keine Tests/Linting/Formatter-Kommandos dokumentiert.
- Kein `git push` dokumentiert.
- Keine Package-Installation durch mich dokumentiert (User hat `pip install eodhd` gemacht).
- Keine Netzwerk-Calls durch Tooling dokumentiert (Netzwerk im Sandbox-Kontext eingeschränkt); EODHD‑API‑Calls wurden vom User lokal ausgeführt (Details unklar).

### 2025-12-17 21:59 CET — Debug/Hardening: Training- & Report-Notebooks (Yahoo vs EODHD)

**Ziel**
- Notebook-Workflow so robust machen, dass Experimente (Yahoo FX vs. EODHD FX) reproduzierbar laufen und Reports/Vergleiche nicht mehr an leeren Splits oder fehlenden Klassen craschen.
- Ursachenanalyse für auffällige Confusion-Matrices / degenerate Modelle (z.B. Direction-Modell sagt nur „up“).

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: `git status -sb`
  ```text
  ## main...origin/main [ahead 4]
   M README.md
   M config/symbols.yaml
   M data/processed/fx/eurusd_labels.csv
   M notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb
   M notebooks/eodhd_two_stage/2_train_eodhd.ipynb
   M notebooks/eodhd_two_stage/3_eval_eodhd.ipynb
   M notebooks/final_two_stage/1_data_prep_final.ipynb
   M notebooks/final_two_stage/2_train_final.ipynb
   M notebooks/final_two_stage/3_eval_final.ipynb
   … (viele weitere Deleted/Untracked Resultate/PDFs; Details in Terminalausgabe)
  ```
- Relevante Dateien:
  - `src/models/train_xgboost_two_stage.py`
  - `scripts/generate_two_stage_report.py`
  - `notebooks/final_two_stage/2_train_final.ipynb`
  - `notebooks/eodhd_two_stage/2_train_eodhd.ipynb`
  - `notebooks/eodhd_two_stage/3_eval_eodhd.ipynb`

**Git**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session: *unklar*, ob `a83dea3` in dieser Session erstellt wurde; er ist jedoch der aktuelle HEAD.
- Commit-Inhalt (kurz): `git show --stat a83dea3`
  ```text
  notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb |  31 ++--
  notebooks/eodhd_two_stage/2_train_eodhd.ipynb     |  54 +++---
  notebooks/eodhd_two_stage/3_eval_eodhd.ipynb      |  62 ++++---
  notebooks/final_two_stage/1_data_prep_final.ipynb |  28 +--
  notebooks/final_two_stage/2_train_final.ipynb     |  39 ++--
  notebooks/final_two_stage/3_eval_final.ipynb      |  66 +++----
  scripts/compare_experiments_pnl.py                |  27 ++-
  scripts/generate_two_stage_report.py              | 207 +++++++++++++++++++++-
  src/data/label_eurusd.py                          | 102 ++++++++++-
  9 files changed, 477 insertions(+), 139 deletions(-)
  ```
  - Details: `git show a83dea3`

**Vorgehen (was gemacht wurde)**
- Notebook-Crashursache analysiert (Direction `predict_proba(...)[:, 1]` schlägt fehl) und festgestellt, dass Experimente mit sehr strengen Label-Parametern (z.B. `hp_yahoo_2`: `horizon_days=20`, `±0.05`) in Val/Test kaum/keine Bewegungstage erzeugen → degenerierte Splits/fehlende Klassen.
- Guardrails eingebaut:
  - Training: klarer Fehler bei leeren Trainingsdaten/0 Features/1 Klasse.
  - Training: wenn Val-Split leer ist → ohne Early-Stopping trainieren.
  - Notebooks: existenz-check für Dataset-Datei, sichere `predict_proba`-Extraktion, und val-basierte Threshold-Optimierung nur wenn Val ausreichend Daten hat.
- Report-Generator robuster gemacht:
  - Fehlende Klassenmetriken (`KeyError: 'up'`) führen nicht mehr zum Crash (NaN-Fallback).
  - Leere/ungültige Confusion-Matrices werden als Null-Matrizen gerendert (Markierung „(keine Daten)“).
  - Matplotlib Cache standardmäßig nach `/tmp/mpl` gelegt (verhindert „~/.matplotlib not writable“ Warnungen).
- EODHD Eval-Notebook um einen optionalen Vergleichs-Cell ergänzt (EODHD vs Yahoo via `scripts/compare_experiments_pnl.py`).

**Kommandos/Outputs (wichtigste)**
- Datensatz-/Label-Verteilungen geprüft (Beispiel):
  - `data/processed/datasets/eurusd_news_training__hp_long_final_yahoo_12.csv`: `test rows 218`, `label counts test {'up': 100, 'down': 78, 'neutral': 40}`.
  - `data/processed/datasets/eurusd_news_training__hp_yahoo_2.csv`: Val-Split `signal==1` = 0, Test-Split nur `up` (keine `down`), entsprechend degenerierte Direction-Metriken.
- Report-Generator lokal verifiziert:
  - `python3 -m py_compile scripts/generate_two_stage_report.py`
  - `MPLCONFIGDIR=/tmp/mpl PYTHONPATH=. python3 - <<...>>` (Report-Render auf `/tmp/test_report.pdf` / `/tmp/test_eod_report.pdf`)
- Fehler, die dabei auftraten und behoben wurden:
  - `KeyError: 'up'` in `scripts/generate_two_stage_report.py` (fehlende Klasse im Report)
  - `IndexError: Inconsistent shape between the condition and the input` bei Heatmap mit leeren Confusion-Matrices
  - `ModuleNotFoundError: No module named 'src'` beim direkten Script-Run ohne `PYTHONPATH=.` (Workaround: `PYTHONPATH=.`)

**Änderungen**
- Geändert:
  - `CHAT_JOURNAL.md` (diesen Eintrag ergänzt)
  - `src/models/train_xgboost_two_stage.py` (Guardrails + Training ohne Early-Stopping bei leerem Val)
  - `notebooks/final_two_stage/2_train_final.ipynb` (Dataset-Existenzcheck, sichere Probas, val-threshold Guardrails, Debug-Zelle robust gemacht)
  - `scripts/generate_two_stage_report.py` (NaN-Fallback für fehlende Klassen, robuste Confusion-Matrices, `MPLCONFIGDIR=/tmp/mpl`)
  - `notebooks/eodhd_two_stage/2_train_eodhd.ipynb` (analog zu final: Dataset-Check, sichere Probas, val-threshold Guardrails)
  - `notebooks/eodhd_two_stage/3_eval_eodhd.ipynb` (zusätzlicher optionaler Vergleichs-Cell)
- Neu: keine (in diesem Abschnitt keine neue Datei per Patch angelegt)
- Gelöscht: keine absichtlichen Löschaktionen in diesem Abschnitt dokumentiert (viele `D ...pdf` im `git status` sind vorhanden; Ursache/Entstehung unklar)
- Rückgängig gemacht: keine
- **Keine Dateiänderungen**: nein

**Ergebnis**
- Training/Report-Workflow crasht nicht mehr bei Experimenten mit leeren/degenerierten Splits; stattdessen Warnungen/NaN und klare Fehlermeldungen.
- EODHD-Train/Eval-Notebooks sind auf denselben robusten Ablauf wie Yahoo ausgerichtet; zusätzlicher Vergleichs-Cell vorhanden.

**Offen / Nicht gemacht (bewusst)**
- Keine zusätzlichen Python-Packages installiert.
- Keine Test-Suite/Linter/Formatter im Repo ausgeführt (nur `py_compile` für ein Script).
- Keine Netzwerkcalls ausgeführt (Netzwerkzugriff im Sandbox-Kontext eingeschränkt).
- Keine neuen Experimente end-to-end neu gerechnet; Fokus war Debugging/Härtung des Workflows.

### 2025-12-17 22:10 CET — Review Label-Logik + v2 Pipeline (Yahoo vs EODHD)

**Ziel**
- Label-Logik prüfen (Diskrepanz Horizon 4 vs 15) und mögliche Fehl-Labels (neutral vs up) einordnen.
- Yahoo vs EODHD vergleichen und eine getrennte v2-Pipeline nutzen (Config/EXP_ID zentral, PDF auditierbar).
- Klären, wo v2 PDFs liegen und warum sie ggf. fehlen.

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: (Auszug) `git status -sb`
  ```text
  ## main...origin/main [ahead 4]
 M README.md
 M config/symbols.yaml
 M data/processed/fx/eurusd_labels.csv
 M notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb
 M notebooks/eodhd_two_stage/2_train_eodhd.ipynb
 M notebooks/eodhd_two_stage/3_eval_eodhd.ipynb
 M notebooks/final_two_stage/1_data_prep_final.ipynb
 M notebooks/final_two_stage/2_train_final.ipynb
 M notebooks/final_two_stage/3_eval_final.ipynb
 D notebooks/results/final_two_stage/two_stage_final__hp1_h4_thr0p4pct_hit_1_report.pdf
 D notebooks/results/final_two_stage/two_stage_final__hpL1_h4_thr0p4pct_hit_1_report.pdf
 D notebooks/results/final_two_stage/two_stage_final__hp_long1_h4_thr0p4pct_hit_1_report.pdf
 D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p3pct_hit_7_report.pdf
 D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_1_report.pdf
 D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_2_report.pdf
 D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_8_report.pdf
 D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p5pct_hit_3_report.pdf
 D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p6pct_hit_6_report.pdf
 D notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h5_thr0p4pct_hit_5_report.pdf
... (gekürzt; vollständige Pfade in 'Änderungen')
  ```
- Hinweis: In Shell-Outputs tauchte wiederholt auf: `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted`.

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
46c107f feat(report): expand docs and add P&L comparison script
265f8af Update latest eurusd_labels snapshot
46f1cea Add EODHD FX pipeline and comparison tools
88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
f77ea1b hp_long price-only baseline + cleanup
b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
7f2c260 Add hp1 price-only baseline and compare with hv5
ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): keine erstellt (unklar, ob vorhandene Commits außerhalb dieser Session entstanden).

**Vorgehen (was gemacht wurde)**
- v2 Output-Struktur geprüft (existierende Ergebnisse/Reports unter `data/processed/v2/...`).
- Einen v2 Run per EXP_ID erneut ausgeführt, um PDF-Erzeugung zu verifizieren.
- v2 Summary neu generiert, um `report_path` pro EXP_ID sichtbar zu machen.
- Hinweis gegeben: `0_calibrate_params_v2.ipynb` ist nur zur Parameter-Kalibrierung; PDFs entstehen beim Runner.

**Kommandos/Outputs (wichtigste)**
- `git status -sb`
- `git log --oneline --decorate -n 10`
- v2 Runner:
  - `python3 -m scripts.run_two_stage_experiment_v2 --exp-id at_v2__yahoo__h15__thr0pct__tp_sl__slfixed_pct__sl1pct__tp2pct`
  - Output (gekürzt):
    - XGBoost Warnung: `early_stopping_rounds ... deprecated` (Warnung, kein Abbruch)
    - `[ok] v2 pipeline fertig` inkl. `report : data/processed/v2/reports/two_stage__at_v2__yahoo__h15__thr0pct__tp_sl__slfixed_pct__sl1pct__tp2pct.pdf`
- v2 Summary:
  - `python3 -m scripts.summarize_v2_results`
  - Output: schreibt `data/processed/v2/summary/v2_summary.csv` und `.md` (rows: 6)
- Fehler/Umgebung:
  - `python` ist nicht verfügbar (`zsh: command not found: python`); `python3` funktioniert.

**Änderungen**
- Geändert (tracked; Quelle: `git diff --name-status`):
  - `README.md`
  - `config/symbols.yaml`
  - `data/processed/fx/eurusd_labels.csv`
  - `notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb`
  - `notebooks/eodhd_two_stage/2_train_eodhd.ipynb`
  - `notebooks/eodhd_two_stage/3_eval_eodhd.ipynb`
  - `notebooks/final_two_stage/1_data_prep_final.ipynb`
  - `notebooks/final_two_stage/2_train_final.ipynb`
  - `notebooks/final_two_stage/3_eval_final.ipynb`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_2_report.pdf`
  - `scripts/compare_experiments_pnl.py`
  - `scripts/generate_two_stage_report.py`
  - `src/data/label_eurusd.py`
  - `src/models/train_xgboost_two_stage.py`
- Gelöscht (tracked; Quelle: `git diff --name-status`):
  - `notebooks/results/final_two_stage/two_stage_final__hp1_h4_thr0p4pct_hit_1_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hpL1_h4_thr0p4pct_hit_1_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long1_h4_thr0p4pct_hit_1_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p3pct_hit_7_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_1_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_2_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_8_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p5pct_hit_3_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p6pct_hit_6_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h5_thr0p4pct_hit_5_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h5_thr0p5pct_hit_4_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_3_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_4_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv1_h4_thr0p3pct_hit_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv2_h4_thr0p4pct_hit_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv3_h4_thr0p5pct_hit_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv4_h4_thr0p4pct_hit_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_2_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_3_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_4_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_5_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_6_2_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_6_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv10_h4_thr0p_55pct_tolerant0p1pct_6p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv11_h4_thr0p_4pct_tolerant0p1pct_6p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv12_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv13_h4_thr0p_3pct_tolerant0p1pct_4p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv14_h4_thr0p_3pct_tolerant0p1pct_51p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv15_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv16_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv17_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv18_h4_thr0p_3pct_tolerant0p1pct_7p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv19_h4_thr0p_3pct_tolerant0p1pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv1_h4_thr0p7pct_tolerant0p3pct_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv20_h4_thr0p_6pct_tolerant0p1pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv21_h4_thr0p_6pct_tolerant0p6pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv22_h4_thr0p_3pct_tolerant_p_pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv23_h3_thr0p_3pct_tolerant_p_pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv24_h6_thr0p_6pct_tolerant_p_pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv25_h6_thr1p_0pct_tolerant_p_pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv26_h6_thr1p_0pct_strict_p_pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv27_h6_thr1p_0pct_tolerant_p_pct_5p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv28_h6_thr1p_5pct_tolerant_p_pct_5p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv2_h4_thr0p_8pct_tolerant0p4pct_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv3_h4_thr0p_65pct_tolerant0p35pct_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv4_h4_thr0p_65pct_tolerant0p15pct_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv5_h4_thr0p_65pct_tolerant0p15pct_7p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv6_h4_thr0p_6pct_tolerant0p15pct_6p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv7_h4_thr0p_6pct_tolerant0p2pct_7p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv8_h4_thr0p_6pct_tolerant0p2pct_6p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__nv9_h4_thr0p_55pct_tolerant0p2pct_6p_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__v0_h4_thr1pct_strict_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__v1_h4_thr0p5pct_strict_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__v3_h4_thr0p3pct_relaxed_report.pdf`
  - `notebooks/results/final_two_stage/two_stage_final__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf`
  - `notebooks/results/two_stage__v1_h4_thr0p5pct_strict_report.pdf`
  - `notebooks/results/two_stage__v2_h4_thr0p5pct_strict_newfeat_report.pdf`
  - `notebooks/results/two_stage__v3_h4_thr0p3pct_relaxed_report.pdf`
  - `notebooks/results/two_stage__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf`
  - `notebooks/results/two_stage__v5_h4_thr0p5pct_tolerant0p3pct_spw1p0_report.pdf`
  - `notebooks/results/two_stage__v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2_report.pdf`
  - `notebooks/results/two_stage__v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600_report.pdf`
  - `notebooks/results/two_stage__v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain_report.pdf`
  - `notebooks/results/two_stage__v9_h4_thr0p5pct_tol0p3_30dfeat_report.pdf`
  - `notebooks/results/updown__s1_h4_thr0p5pct_tol0p3_report.pdf`
  - `notebooks/results/updown__s2_h4_thr0p5pct_tol0p3_report.pdf`
- Andere Status (tracked; Quelle: `git diff --name-status`):
  - (keine)
- Neu (untracked; Quelle: `git ls-files --others --exclude-standard`):
  ```text
  CHAT_JOURNAL.md
docs/v2_pipeline.md
notebooks/results/final_two_stage/_debug_hp_long_result_report.pdf
notebooks/results/final_two_stage/_debug_hp_long_result_report_v2.pdf
notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3.pdf
notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3_full.pdf
notebooks/results/final_two_stage/pdf/compare__hp_long_result__vs__hp_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare__hp_long_result__vs__hv_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare__hp_result__vs__hp_long_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare__hp_result__vs__hv_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_3__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_3__B_pnl_lev20.png
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_4__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_4__B_pnl_lev20.png
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_3_vs_hp_long_final_yahoo_4__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_3_vs_hp_long_final_yahoo_4__B_pnl_lev20.png
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_eod_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_long_eod_1__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_long_eod_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_long_final_yahoo_2__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hv_eod_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_vs_hv_long__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__sl_tp.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only_exit.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only_exit_v3.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v2.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v3.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v4.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v5.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v6.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v7.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v8.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp1_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hpL1_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long1_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p3pct_hit_7_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_2_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_8_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p5pct_hit_3_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p6pct_hit_6_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h5_thr0p4pct_hit_5_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h5_thr0p5pct_hit_4_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_final_yahoo_9_report_v2.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_2_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_3_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_4_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv1_h4_thr0p3pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv2_h4_thr0p4pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv3_h4_thr0p5pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv4_h4_thr0p4pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_2_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_3_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_4_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_5_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_6_2_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_6_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv10_h4_thr0p_55pct_tolerant0p1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv11_h4_thr0p_4pct_tolerant0p1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv12_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv13_h4_thr0p_3pct_tolerant0p1pct_4p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv14_h4_thr0p_3pct_tolerant0p1pct_51p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv15_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv16_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv17_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv18_h4_thr0p_3pct_tolerant0p1pct_7p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv19_h4_thr0p_3pct_tolerant0p1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv1_h4_thr0p7pct_tolerant0p3pct_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv20_h4_thr0p_6pct_tolerant0p1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv21_h4_thr0p_6pct_tolerant0p6pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv22_h4_thr0p_3pct_tolerant_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv23_h3_thr0p_3pct_tolerant_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv24_h6_thr0p_6pct_tolerant_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv25_h6_thr1p_0pct_tolerant_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv26_h6_thr1p_0pct_strict_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv27_h6_thr1p_0pct_tolerant_p_pct_5p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv28_h6_thr1p_5pct_tolerant_p_pct_5p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv2_h4_thr0p_8pct_tolerant0p4pct_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv3_h4_thr0p_65pct_tolerant0p35pct_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv4_h4_thr0p_65pct_tolerant0p15pct_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv5_h4_thr0p_65pct_tolerant0p15pct_7p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv6_h4_thr0p_6pct_tolerant0p15pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv7_h4_thr0p_6pct_tolerant0p2pct_7p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv8_h4_thr0p_6pct_tolerant0p2pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv9_h4_thr0p_55pct_tolerant0p2pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__v0_h4_thr1pct_strict_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__v1_h4_thr0p5pct_strict_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__v3_h4_thr0p3pct_relaxed_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
notebooks/results/final_two_stage/two_stage_final__final_yahoo.json
notebooks/results/final_two_stage/two_stage_final__final_yahoo_metrics.csv
notebooks/results/final_two_stage/two_stage_final__final_yahoo_predictions.csv
notebooks/results/final_two_stage/two_stage_final__final_yahoo_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_eod_result.json
notebooks/results/final_two_stage/two_stage_final__hp_eod_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_eod_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_eod_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1.json
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12.json
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13.json
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result.json
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_result.json
notebooks/results/final_two_stage/two_stage_final__hp_long_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_result.json
notebooks/results/final_two_stage/two_stage_final__hp_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1.json
notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_eod_result.json
notebooks/results/final_two_stage/two_stage_final__hv_eod_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_eod_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_eod_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo.json
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2.json
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_result.json
notebooks/results/final_two_stage/two_stage_final__hv_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2.json
notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_report.pdf
notebooks/results/pdf/two_stage__v1_h4_thr0p5pct_strict_report.pdf
notebooks/results/pdf/two_stage__v2_h4_thr0p5pct_strict_newfeat_report.pdf
notebooks/results/pdf/two_stage__v3_h4_thr0p3pct_relaxed_report.pdf
notebooks/results/pdf/two_stage__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
notebooks/results/pdf/two_stage__v5_h4_thr0p5pct_tolerant0p3pct_spw1p0_report.pdf
notebooks/results/pdf/two_stage__v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2_report.pdf
notebooks/results/pdf/two_stage__v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600_report.pdf
notebooks/results/pdf/two_stage__v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain_report.pdf
notebooks/results/pdf/two_stage__v9_h4_thr0p5pct_tol0p3_30dfeat_report.pdf
notebooks/results/pdf/updown__s1_h4_thr0p5pct_tol0p3_report.pdf
notebooks/results/pdf/updown__s2_h4_thr0p5pct_tol0p3_report.pdf
notebooks/results/two_stage__final_yahoo.json
notebooks/results/two_stage__hp_eod_result.json
notebooks/results/two_stage__hp_long_eod_1.json
notebooks/results/two_stage__hp_long_eod_final_yahoo_12.json
notebooks/results/two_stage__hp_long_eod_final_yahoo_13.json
notebooks/results/two_stage__hp_long_eod_result.json
notebooks/results/two_stage__hp_long_final_yahoo.json
notebooks/results/two_stage__hp_long_final_yahoo_10.json
notebooks/results/two_stage__hp_long_final_yahoo_11.json
notebooks/results/two_stage__hp_long_final_yahoo_12.json
notebooks/results/two_stage__hp_long_final_yahoo_2.json
notebooks/results/two_stage__hp_long_final_yahoo_3.json
notebooks/results/two_stage__hp_long_final_yahoo_4.json
notebooks/results/two_stage__hp_long_final_yahoo_5.json
notebooks/results/two_stage__hp_long_final_yahoo_6.json
notebooks/results/two_stage__hp_long_final_yahoo_7.json
notebooks/results/two_stage__hp_long_final_yahoo_8.json
notebooks/results/two_stage__hp_long_final_yahoo_9.json
notebooks/results/two_stage__hp_long_result.json
notebooks/results/two_stage__hp_long_yahoo_1.json
notebooks/results/two_stage__hp_long_yahoo_2.json
notebooks/results/two_stage__hp_long_yahoo_3.json
notebooks/results/two_stage__hp_long_yahoo_4.json
notebooks/results/two_stage__hp_long_yahoo_5.json
notebooks/results/two_stage__hp_long_yahoo_6.json
notebooks/results/two_stage__hp_long_yahoo_7.json
notebooks/results/two_stage__hp_result.json
notebooks/results/two_stage__hp_yahoo_1.json
notebooks/results/two_stage__hv_eod_result.json
notebooks/results/two_stage__hv_long_final_yahoo.json
notebooks/results/two_stage__hv_long_final_yahoo_2.json
notebooks/results/two_stage__hv_result.json
notebooks/results/two_stage__hv_yahoo_2.json
notebooks/v2_two_stage/0_calibrate_params_v2.ipynb
notebooks/v2_two_stage/1_run_experiments_v2.ipynb
notebooks/v2_two_stage/2_summarize_results_v2.ipynb
powerpoint/presentation.pptx
powerpoint/presentation_image_1.2
powerpoint/presentation_image_1.2.png
powerpoint/presentation_image_1.3.png
powerpoint/presentation_image_1.png
powerpoint/~$presentation.pptx
scripts/calibrate_trade_params_v2.py
scripts/compare_v2_experiments.py
scripts/compare_yahoo_vs_eod_experiments.py
scripts/run_two_stage_experiment_v2.py
scripts/summarize_v2_results.py
src/data/build_training_set_v2.py
src/data/label_eurusd_trade.py
src/experiments/__init__.py
src/experiments/v2_config.py
src/models/train_two_stage_v2.py
  ```
- Rückgängig gemacht: unklar (keine entsprechenden Kommandos in diesem Chat ausgeführt).
- **Keine Dateiänderungen**: nein (Workspace enthält Änderungen/Untracked; Ursprung/Entstehungszeitpunkt teilweise unklar).

**Ergebnis**
- v2 PDFs liegen unter `data/processed/v2/reports/` und sind pro EXP_ID auch über `data/processed/v2/results/two_stage__<EXP_ID>_manifest.json` bzw. `data/processed/v2/summary/v2_summary.md` auffindbar.
- v2 Run für `at_v2__yahoo__h15__thr0pct__tp_sl__slfixed_pct__sl1pct__tp2pct` erzeugte das PDF erfolgreich.

**Offen / Nicht gemacht (bewusst)**
- Keine Packages installiert.
- Keine Tests/Linter/Formatter ausgeführt.
- Keine Netzwerkcalls ausgeführt (Network sandbox: restricted).
- Keine Git-Commits erstellt.

### 2025-12-17 (Zeit unklar) — Trading-Simulation erklärt + Varianten 2/3 in Tools ergänzt

**Ziel**
- Erklärung, wie die Strategie-A/B-Trading-Simulation und die zugehörigen Plots berechnet werden (inkl. “Variante 2” ohne Stop-Loss).
- Code-Stellen im Repo zeigen (Report-Generator + Vergleichsscript).
- Vergleichs-Plot für zwei EXP_IDs auf Variante 2 umstellen und anschließend eine “Variante 3” hinzufügen, bei der P&L erst am Exit-Datum gebucht wird.
- Report-Titelseite so anpassen, dass Text weniger wahrscheinlich am Rand abgeschnitten wird.

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: `git status -sb` (Auszug, stark gekürzt)
  ```text
  ## main...origin/main [ahead 4]
   M scripts/compare_experiments_pnl.py
   M scripts/generate_two_stage_report.py
   ?? notebooks/results/final_two_stage/_debug_hp_long_result_report.pdf
   ?? notebooks/results/final_two_stage/_debug_hp_long_result_report_v2.pdf
   ?? notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3.pdf
   ?? notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3_full.pdf
   ?? notebooks/results/final_two_stage/pdf/
   … (weitere Änderungen/Untracked im Workspace; Ursprung/Entstehungszeitpunkt unklar)
  ```
- Relevante Dateien: `notebooks/final_two_stage/3_eval_final.ipynb`, `scripts/generate_two_stage_report.py`, `scripts/compare_experiments_pnl.py`, `docs/full_report_hp_long_final_yahoo.md`

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  a83dea3 (HEAD -> main) feat(labeling): first-hit + weekday filter; report variants
  46c107f feat(report): expand docs and add P&L comparison script
  265f8af Update latest eurusd_labels snapshot
  46f1cea Add EODHD FX pipeline and comparison tools
  88e5fd0 (origin/main, origin/HEAD) Add hp_long result metrics and reports
  f77ea1b hp_long price-only baseline + cleanup
  b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
  7f2c260 Add hp1 price-only baseline and compare with hv5
  ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  b033083 Add cost-based direction thresholds and hv5_h4_thr0p4pct_hit_6 results
  ```
- Relevante Commits dieser Session (Hashes + Message): keine (keine Commits erstellt)

**Vorgehen (was gemacht wurde)**
- Codepfad identifiziert: Notebook `notebooks/final_two_stage/3_eval_final.ipynb` ruft `scripts/generate_two_stage_report.py` auf, dort werden Strategie A/B sowie die Plots erzeugt.
- Trading-Regeln erklärt und mit Code gegengeprüft:
  - Variante 1: SL+TP in `_compute_trade_return(...)`
  - Variante 2: TP-only / sonst Horizontende in `_compute_trade_return_tp_or_horizon_no_sl(...)`
- Vergleichsgrafik-Script gefunden: `scripts/compare_experiments_pnl.py` (initial nur Variante 1).
- `scripts/compare_experiments_pnl.py` erweitert um `--variant`:
  - `tp_only`/`sl_tp` (Variante 2/1; “sofort verbucht” wie bisher)
  - `tp_only_exit`/`sl_tp_exit` (Variante 3; P&L erst am Exit-Datum verbucht)
- In `scripts/generate_two_stage_report.py` eine Hilfsfunktion `_compute_trade_outcome(...)->(return, exit_date)` ergänzt, um Exit-Datum verfügbar zu machen.
- Report-Variante 3 so umgesetzt, dass sie **die gleichen Tabellen und Plots** wie Variante 1/2 erzeugt (über `settle_at_exit=True` in `_add_trade_simulation_pages_variant(...)`), nicht nur eine einzelne Grafik.
- Titelseite: Zeilenabstand in `add_title_page(...)` reduziert, um weniger Risiko für abgeschnittenen Text zu haben.

**Kommandos/Outputs (wichtigste)**
- Suchen/Verifizieren:
  - `rg "Strategie A vs B|pnl_fixed_lev20|capital_after_lev20" scripts/generate_two_stage_report.py`
  - `python3 -m py_compile scripts/generate_two_stage_report.py scripts/compare_experiments_pnl.py`
- Report generieren (Debug):
  - `python3 -m scripts.generate_two_stage_report --exp-id hp_long_result --output notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3_full.pdf`
  - Output: `[ok] Report gespeichert unter: notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3_full.pdf`
- Vergleichsplot (Variante 3):
  - `python3 -m scripts.compare_experiments_pnl --exp-a hp_result --exp-b hv_result --strategy B --leverage 20 --variant tp_only_exit --output notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only_exit.pdf`
  - Output: `[ok] Vergleichsgrafik gespeichert: notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only_exit.pdf`
- Fehler/Outputs:
  - `python` war nicht verfügbar → `python3` verwendet (`zsh: command not found: python`).
  - User-Command mit `<hp_result>` führte zu Shell-Redirection-Fehler: `zsh: no such file or directory: hp_result`.
  - Matplotlib meldete zeitweise: `~/.matplotlib is not a writable directory` + Font-Cache Build.

**Änderungen**
- Geändert:
  - `scripts/generate_two_stage_report.py` (Titelseite Zeilenabstand; `_compute_trade_outcome`; Settlement-am-Exit-Logik in `_add_trade_simulation_pages_variant`; Variante-Labeling)
  - `scripts/compare_experiments_pnl.py` (`--variant` inkl. `*_exit` Variants; Nutzung `_compute_trade_outcome` für Settlement am Exit)
- Neu (generiert, untracked):
  - `notebooks/results/final_two_stage/_debug_hp_long_result_report.pdf`
  - `notebooks/results/final_two_stage/_debug_hp_long_result_report_v2.pdf`
  - `notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3.pdf`
  - `notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3_full.pdf`
  - `notebooks/results/final_two_stage/pdf/` (enthält u.a. `compare_hp_result_vs_hv_result__B_pnl_lev20*.pdf`)
- Gelöscht: keine Dateien gelöscht (in Git).  
- Rückgängig gemacht:
  - Eine zunächst eingeführte eigene Funktion für Variante 3 wurde wieder entfernt (Codeblock gelöscht) und Variante 3 stattdessen über die bestehende `_add_trade_simulation_pages_variant(..., settle_at_exit=True)` umgesetzt.
- **Keine Dateiänderungen**: nein

**Ergebnis**
- Report enthält jetzt Variante 1/2/3, wobei Variante 3 die gleichen Tabellen/Plots wie Variante 1/2 hat, aber P&L erst am Exit-Datum bucht.
- Vergleichsscript kann Variante 2 und Variante 3 (Exit-Settlement) per `--variant` ausführen.

**Offen / Nicht gemacht (bewusst)**
- Keine Packages installiert.
- Keine Netzwerkcalls ausgeführt.
- Keine Git-Commits erstellt.
- Keine “Kapitalbindung/Positions-Lock”-Logik umgesetzt (Trades können weiterhin überlappen; nur Settlement-Zeitpunkt wurde verändert).

### 2025-12-21 10:53  — Journal-Eintrag erstellt, kurz rückgängig, dann wiederhergestellt

**Ziel**
- `CHAT_JOURNAL.md` gemäß Template um einen Eintrag ergänzen (Fakten aus dem Chat).
- Nach User-Wunsch: Änderung kurz rückgängig machen und anschließend doch wieder hinzufügen.

**Kontext**
- Working dir: `/Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project`
- Branch/Status: Auszug von `git status -sb`
  ```text
  ## main...origin/main
 M notebooks/final_two_stage/1_data_prep_final.ipynb
 M notebooks/final_two_stage/2_train_final.ipynb
 M notebooks/final_two_stage/3_eval_final.ipynb
 M scripts/compare_experiments_pnl.py
?? .tmp/
?? docs/bericht_projektanalyse_hs2025_ml_project.txt
?? docs/v2_pipeline.md
?? notebooks/results/final_two_stage/_debug_hp_long_result_report.pdf
?? notebooks/results/final_two_stage/_debug_hp_long_result_report_v2.pdf
?? notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3.pdf
?? notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3_full.pdf
?? notebooks/results/final_two_stage/pdf/
?? notebooks/results/final_two_stage/two_stage_final__final_yahoo.json
?? notebooks/results/final_two_stage/two_stage_final__final_yahoo_metrics.csv
?? notebooks/results/final_two_stage/two_stage_final__final_yahoo_predictions.csv
?? notebooks/results/final_two_stage/two_stage_final__final_yahoo_report.pdf
?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result.json
?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result_metrics.csv
?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result_predictions.csv
?? notebooks/results/final_two_stage/two_stage_final__hp_eod_result_report.pdf
?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1.json
?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_metrics.csv
?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_predictions.csv
?? notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_report.pdf
... (gekürzt)
  ```
- Hinweis: In Shell-Outputs tauchte auf: `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted`.

**Git (optional, aber wenn vorhanden ausfüllen)**
- Letzte Commits: `git log --oneline --decorate -n 10`
  ```text
  e78fb5e (HEAD -> main, origin/main, origin/HEAD) chore: update notebooks/results and report tools
a83dea3 feat(labeling): first-hit + weekday filter; report variants
46c107f feat(report): expand docs and add P&L comparison script
265f8af Update latest eurusd_labels snapshot
46f1cea Add EODHD FX pipeline and comparison tools
88e5fd0 Add hp_long result metrics and reports
f77ea1b hp_long price-only baseline + cleanup
b851d53 Add hp_long runs and cost-based signal threshold; keep news pipeline intact
7f2c260 Add hp1 price-only baseline and compare with hv5
ee1ebdf Run hv5_h4_thr0p4pct_hit_6 notebooks
  ```
- Relevante Commits dieser Session (Hashes + Message): keine erstellt.

**Vorgehen (was gemacht wurde)**
- Git-Infos und Status gesammelt (`git status -sb`, `git log ...`).
- `CHAT_JOURNAL.md` zunächst um einen Eintrag ergänzt.
- Auf Wunsch „rückgängig“: Eintrag wieder entfernt.
- Wieder auf Wunsch: Journal wiederhergestellt (Workaround, da `git restore` nicht funktionierte).

**Kommandos/Outputs (wichtigste)**
- `git status -sb`
- `git log --oneline --decorate -n 10`
- Entfernen des Eintrags: per Python-Script (Trunkierung ab Marker; Details im Chat).
- Versuchtes Restore (fehlgeschlagen):
  - `git restore --worktree CHAT_JOURNAL.md`
  - Fehler: `fatal: Unable to create '<repo>/.git/index.lock': Operation not permitted`
- Restore-Workaround (erfolgreich):
  - `git show HEAD:CHAT_JOURNAL.md > CHAT_JOURNAL.md`

**Änderungen**
- Geändert (tracked; aktueller Stand aus `git diff --name-status`):
  - `notebooks/final_two_stage/1_data_prep_final.ipynb`
  - `notebooks/final_two_stage/2_train_final.ipynb`
  - `notebooks/final_two_stage/3_eval_final.ipynb`
  - `scripts/compare_experiments_pnl.py`
- Gelöscht (tracked; aktueller Stand aus `git diff --name-status`):
  - (keine)
- Andere Status (tracked; aktueller Stand aus `git diff --name-status`):
  - (keine)
- Neu (untracked; aktueller Stand aus `git ls-files --others --exclude-standard`):
  ```text
  .tmp/mpl/fontlist-v390.json
docs/bericht_projektanalyse_hs2025_ml_project.txt
docs/v2_pipeline.md
notebooks/results/final_two_stage/_debug_hp_long_result_report.pdf
notebooks/results/final_two_stage/_debug_hp_long_result_report_v2.pdf
notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3.pdf
notebooks/results/final_two_stage/_debug_hp_long_result_report_with_v3_full.pdf
notebooks/results/final_two_stage/pdf/compare__hp_long_result__vs__hp_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare__hp_long_result__vs__hv_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare__hp_result__vs__hp_long_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare__hp_result__vs__hv_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_3__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_3__B_pnl_lev20.png
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_4__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_2_vs_hp_long_final_yahoo_4__B_pnl_lev20.png
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_3_vs_hp_long_final_yahoo_4__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_3_vs_hp_long_final_yahoo_4__B_pnl_lev20.png
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_eod_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_long_eod_1__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_long_eod_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hp_long_final_yahoo_2__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_final_yahoo_vs_hv_eod_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_result_vs_hp_long_eod_result__B_pnl_lev20_tp_only_exit.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_result_vs_hp_long_eod_result__B_pnl_lev20_tp_only_exit_FIXEDthr_sig0p45_dir0p3_0p5.pdf
notebooks/results/final_two_stage/pdf/compare_hp_long_vs_hv_long__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__sl_tp.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only_exit.pdf
notebooks/results/final_two_stage/pdf/compare_hp_result_vs_hv_result__B_pnl_lev20__tp_only_exit_v3.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v2.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v3.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v4.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v5.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v6.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v7.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__final_yahoo_report_v8.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp1_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hpL1_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long1_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p3pct_hit_7_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_2_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_8_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p5pct_hit_3_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h4_thr0p6pct_hit_6_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h5_thr0p4pct_hit_5_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_eod_h5_thr0p5pct_hit_4_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_final_yahoo_9_report_v2.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_2_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_3_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_4_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hp_long_h4_thr0p4pct_hit_1_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv1_h4_thr0p3pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv2_h4_thr0p4pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv3_h4_thr0p5pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv4_h4_thr0p4pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_2_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_3_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_4_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_5_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_6_2_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_6_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__hv5_h4_thr0p4pct_hit_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv10_h4_thr0p_55pct_tolerant0p1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv11_h4_thr0p_4pct_tolerant0p1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv12_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv13_h4_thr0p_3pct_tolerant0p1pct_4p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv14_h4_thr0p_3pct_tolerant0p1pct_51p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv15_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv16_h4_thr0p_3pct_tolerant0p1pct_5p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv17_h4_thr0p_3pct_tolerant0p1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv18_h4_thr0p_3pct_tolerant0p1pct_7p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv19_h4_thr0p_3pct_tolerant0p1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv1_h4_thr0p7pct_tolerant0p3pct_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv20_h4_thr0p_6pct_tolerant0p1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv21_h4_thr0p_6pct_tolerant0p6pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv22_h4_thr0p_3pct_tolerant_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv23_h3_thr0p_3pct_tolerant_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv24_h6_thr0p_6pct_tolerant_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv25_h6_thr1p_0pct_tolerant_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv26_h6_thr1p_0pct_strict_p_pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv27_h6_thr1p_0pct_tolerant_p_pct_5p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv28_h6_thr1p_5pct_tolerant_p_pct_5p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv2_h4_thr0p_8pct_tolerant0p4pct_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv3_h4_thr0p_65pct_tolerant0p35pct_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv4_h4_thr0p_65pct_tolerant0p15pct_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv5_h4_thr0p_65pct_tolerant0p15pct_7p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv6_h4_thr0p_6pct_tolerant0p15pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv7_h4_thr0p_6pct_tolerant0p2pct_7p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv8_h4_thr0p_6pct_tolerant0p2pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__nv9_h4_thr0p_55pct_tolerant0p2pct_6p_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__v0_h4_thr1pct_strict_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__v1_h4_thr0p5pct_strict_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__v3_h4_thr0p3pct_relaxed_report.pdf
notebooks/results/final_two_stage/pdf/two_stage_final__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
notebooks/results/final_two_stage/two_stage_final__final_yahoo.json
notebooks/results/final_two_stage/two_stage_final__final_yahoo_metrics.csv
notebooks/results/final_two_stage/two_stage_final__final_yahoo_predictions.csv
notebooks/results/final_two_stage/two_stage_final__final_yahoo_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_eod_result.json
notebooks/results/final_two_stage/two_stage_final__hp_eod_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_eod_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_eod_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1.json
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_1_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12.json
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_12_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13.json
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_final_yahoo_13_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result.json
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_eod_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_10_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_11_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_12_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_2_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_3_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_4_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_6_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_7_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_8_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9.json
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_9_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_result.json
notebooks/results/final_two_stage/two_stage_final__hp_long_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_1_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_2_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_3_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_4_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_5_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_6_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7.json
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_long_yahoo_7_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_result.json
notebooks/results/final_two_stage/two_stage_final__hp_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1.json
notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hp_yahoo_1_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_eod_result.json
notebooks/results/final_two_stage/two_stage_final__hv_eod_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_eod_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_eod_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo.json
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2.json
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_2_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_long_final_yahoo_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_result.json
notebooks/results/final_two_stage/two_stage_final__hv_result_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_result_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_result_report.pdf
notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2.json
notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_metrics.csv
notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_predictions.csv
notebooks/results/final_two_stage/two_stage_final__hv_yahoo_2_report.pdf
notebooks/results/pdf/two_stage__v1_h4_thr0p5pct_strict_report.pdf
notebooks/results/pdf/two_stage__v2_h4_thr0p5pct_strict_newfeat_report.pdf
notebooks/results/pdf/two_stage__v3_h4_thr0p3pct_relaxed_report.pdf
notebooks/results/pdf/two_stage__v4_h4_thr0p5pct_tolerant0p3pct_report.pdf
notebooks/results/pdf/two_stage__v5_h4_thr0p5pct_tolerant0p3pct_spw1p0_report.pdf
notebooks/results/pdf/two_stage__v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2_report.pdf
notebooks/results/pdf/two_stage__v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600_report.pdf
notebooks/results/pdf/two_stage__v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain_report.pdf
notebooks/results/pdf/two_stage__v9_h4_thr0p5pct_tol0p3_30dfeat_report.pdf
notebooks/results/pdf/updown__s1_h4_thr0p5pct_tol0p3_report.pdf
notebooks/results/pdf/updown__s2_h4_thr0p5pct_tol0p3_report.pdf
notebooks/results/two_stage__final_yahoo.json
notebooks/results/two_stage__hp_eod_result.json
notebooks/results/two_stage__hp_long_eod_1.json
notebooks/results/two_stage__hp_long_eod_final_yahoo_12.json
notebooks/results/two_stage__hp_long_eod_final_yahoo_13.json
notebooks/results/two_stage__hp_long_eod_result.json
notebooks/results/two_stage__hp_long_final_yahoo.json
notebooks/results/two_stage__hp_long_final_yahoo_10.json
notebooks/results/two_stage__hp_long_final_yahoo_11.json
notebooks/results/two_stage__hp_long_final_yahoo_12.json
notebooks/results/two_stage__hp_long_final_yahoo_2.json
notebooks/results/two_stage__hp_long_final_yahoo_3.json
notebooks/results/two_stage__hp_long_final_yahoo_4.json
notebooks/results/two_stage__hp_long_final_yahoo_5.json
notebooks/results/two_stage__hp_long_final_yahoo_6.json
notebooks/results/two_stage__hp_long_final_yahoo_7.json
notebooks/results/two_stage__hp_long_final_yahoo_8.json
notebooks/results/two_stage__hp_long_final_yahoo_9.json
notebooks/results/two_stage__hp_long_result.json
notebooks/results/two_stage__hp_long_yahoo_1.json
notebooks/results/two_stage__hp_long_yahoo_2.json
notebooks/results/two_stage__hp_long_yahoo_3.json
notebooks/results/two_stage__hp_long_yahoo_4.json
notebooks/results/two_stage__hp_long_yahoo_5.json
notebooks/results/two_stage__hp_long_yahoo_6.json
notebooks/results/two_stage__hp_long_yahoo_7.json
notebooks/results/two_stage__hp_result.json
notebooks/results/two_stage__hp_yahoo_1.json
notebooks/results/two_stage__hv_eod_result.json
notebooks/results/two_stage__hv_long_final_yahoo.json
notebooks/results/two_stage__hv_long_final_yahoo_2.json
notebooks/results/two_stage__hv_result.json
notebooks/results/two_stage__hv_yahoo_2.json
notebooks/v2_two_stage/0_calibrate_params_v2.ipynb
notebooks/v2_two_stage/1_run_experiments_v2.ipynb
notebooks/v2_two_stage/2_summarize_results_v2.ipynb
powerpoint/presentation.pptx
powerpoint/presentation_image_1.2
powerpoint/presentation_image_1.2.png
powerpoint/presentation_image_1.3.png
powerpoint/presentation_image_1.png
powerpoint/~$presentation.pptx
scripts/calibrate_trade_params_v2.py
scripts/compare_v2_experiments.py
scripts/compare_yahoo_vs_eod_experiments.py
scripts/run_two_stage_experiment_v2.py
scripts/summarize_v2_results.py
src/data/build_training_set_v2.py
src/data/label_eurusd_trade.py
src/experiments/__init__.py
src/experiments/v2_config.py
src/models/train_two_stage_v2.py
  ```
- Rückgängig gemacht:
  - Journal-Eintrag entfernt (Python-Trunkierung) und anschließend `CHAT_JOURNAL.md` aus `HEAD` wiederhergestellt via `git show HEAD:CHAT_JOURNAL.md > CHAT_JOURNAL.md`.

**Ergebnis**
- `CHAT_JOURNAL.md` enthält wieder einen neuen Eintrag am Ende (dieser Eintrag).

**Offen / Nicht gemacht (bewusst)**
- Keine Packages installiert.
- Keine Tests/Linter/Formatter ausgeführt.
- Keine Netzwerkcalls ausgeführt.
- Keine Git-Commits erstellt.
