# Daten-Pipeline: Von Rohdaten zum Zwei-Stufen-XGBoost-Modell für EURUSD-News

Diese Dokumentation beschreibt, wie du **von den Rohdaten** (FX-Kurse und News) zu den **Modellergebnissen** (Metriken und Plots) kommst:

- welche Dateien, Skripte und Notebooks beteiligt sind,
- was diese fachlich machen,
- was du im Terminal bzw. im Notebook ausführen musst.

---

## 0. Umgebung vorbereiten

**Ziel:** Sicherstellen, dass alle Pfade stimmen und das richtige Python-Environment verwendet wird.

1. Im Terminal in den Projektordner wechseln:

   ```bash
   cd /Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project
   ```

2. Virtuelle Umgebung aktivieren:

   ```bash
   source .venv/bin/activate
   ```

3. In Jupyter/VS Code als Kernel dasselbe `.venv` auswählen.

Ab jetzt gelten alle Pfade relativ zu diesem Ordner.

---

## 1. Rohdaten

### 1.1 FX-Kurse

- Datei: `data/raw/fx/EURUSDX.csv`  
- Inhalt: Tägliche EURUSD-Kurse mit Spalten wie `Date`, `Open`, `High`, `Low`, `Close`, `Volume`.  
- Nutzung:
  - Wird von `src/data/label_eurusd.py` eingelesen, um Labels (up/down/neutral) zu berechnen.

### 1.2 News-Daten

- Dateien: `data/raw/news/eodhd_news*.jsonl`, z. B.:
  - `data/raw/news/eodhd_news.jsonl`
  - `data/raw/news/eodhd_news_2019.jsonl`
  - `data/raw/news/eodhd_news_2020_early.jsonl`
- Inhalt: Eine Zeile pro News-Artikel im JSON-Format (Datum, Text, Sentiment etc.).
- Nutzung:
  - Werden von `src/data/prepare_eodhd_news.py` eingelesen, um Tages-Features zu erzeugen.

---

## 2. News-Tagesfeatures erzeugen

**Ziel:** Aus vielen einzelnen Artikeln pro Tag einen kompakten Datensatz mit **Tages-News-Features** bauen.

- Skript: `src/data/prepare_eodhd_news.py`

### 2.1 Ausführung im Terminal

Im Projektwurzel-Ordner:

```bash
python3 -m src.data.prepare_eodhd_news
```

### 2.2 Was das Skript fachlich macht

- Liest alle `eodhd_news*.jsonl` aus `data/raw/news/`.
- Gruppiert alle Artikel nach Datum.
- Berechnet pro Tag u. a.:
  - `article_count` – Anzahl Artikel pro Tag,
  - `avg_polarity` – durchschnittliche Sentiment-Polarity,
  - `avg_neg`, `avg_neu`, `avg_pos` – durchschnittliche neg./neutral/positiv-Scores.
- Schreibt das Ergebnis in:
  - `data/processed/news/eodhd_daily_features.csv`

### 2.3 Wann dieser Schritt nötig ist

- Wenn du **neue News** von der EODHD-API geladen hast.
- Wenn du die **Aggregationslogik** im Skript geändert hast.
- Nicht zwingend vor jedem einzelnen Experiment, solange sich die Rohdaten nicht ändern.

---

## 3. Labels aus FX-Daten berechnen

**Ziel:** Jedem Handelstag ein Label `up`, `down` oder `neutral` zuordnen, basierend auf der Kursbewegung in den nächsten Tagen.

- Skript/Modul: `src/data/label_eurusd.py`
- Kernfunktion: `label_eurusd`

### 3.1 Standard-Ausführung im Terminal (mit Experiment-ID)

Beispiel: Experiment-ID `v1_h4_thr1pct_strict` (Version 1, Horizont 4 Tage, ~1 %-Schwelle, strenge Pfadbedingung):

```bash
python3 -m src.data.label_eurusd --exp-id v1_h4_thr1pct_strict
```

### 3.2 Was das Skript fachlich macht

- Liest `data/raw/fx/EURUSDX.csv`.
- Sortiert die Daten nach Datum, stellt numerische Spalten korrekt ein.
- Für jeden Tag `t`:
  - betrachtet `horizon_days` (Standard: 4) Tage in die Zukunft (`t+1` bis `t+4`),
  - berechnet `lookahead_return = (Close_{t+4} - Close_t) / Close_t`.
- Entscheidung:
  - **up**:
    - `lookahead_return` ist ≥ `up_threshold` (z. B. +1 %),
    - und der Kurs steigt an jedem Zwischentag (strenge Monotonie).
  - **down**:
    - `lookahead_return` ist ≤ `down_threshold` (z. B. −1 %),
    - und der Kurs fällt an jedem Zwischentag.
  - **neutral**:
    - alle anderen Fälle.
- Ergebnis: Eine Tabelle mit
  - Original-OHLCV-Spalten,
  - `lookahead_return`,
  - `label` (`neutral`, `up`, `down`).

### 3.3 Welche Dateien entstehen

- Immer:
  - `data/processed/fx/eurusd_labels.csv`  
    → **aktuelle** Label-Datei (wird beim nächsten Lauf überschrieben).
- Zusätzlich (wegen `--exp-id`):
  - `data/processed/fx/eurusd_labels__v1_h4_thr1pct_strict.csv`  
    → experiment-spezifische Label-Datei für dieses Setup (bleibt bestehen).

### 3.4 Steuerung der Parameter

- Die genauen Parameter (`horizon_days`, `up_threshold`, `down_threshold`, `strict_monotonic`) sind im Python-Code der Funktion `label_eurusd` definiert.
- In der Praxis steuerst du diese Parameter in der Regel über das Notebook `notebooks/1_data_prep_xgboost_two_stage.ipynb`, indem du dort eine Experiment-Konfiguration setzt (siehe Abschnitt 4).

---

## 4. Experiment-spezifische Data Preparation (Notebook `1_data_prep_xgboost_two_stage.ipynb`)

Dieses Notebook ist die **Steuerzentrale pro Experiment**. Es sorgt dafür, dass:

- die Label-Dateien zur Experiment-ID passen, und
- ein dazugehöriger Trainingsdatensatz erzeugt wird.

### 4.1 Notebook öffnen

- Datei: `notebooks/1_data_prep_xgboost_two_stage.ipynb`
- Kernel: das `.venv` aus dem Projekt wählen.

### 4.2 Projektwurzel und Importe

Die ersten Zellen im Notebook:

- suchen die Projektwurzel (den Ordner, der `src/` enthält),
- setzen das Arbeitsverzeichnis (`os.chdir(...)`) auf diese Projektwurzel,
- fügen `src/` zum Python-Suchpfad hinzu (`sys.path`).

**Was du tun musst:**

- Diese Zellen einfach nacheinander ausführen.  
  Danach funktionieren alle Pfade wie `data/raw/...` und `data/processed/...` korrekt.

### 4.3 Experiment-ID und Label-Parameter

Im Notebook gibt es eine Zelle, in der du:

- eine **Experiment-ID** festlegst, z. B.:
  - `v1_h4_thr1pct_strict` oder
  - `v2_h4_thr0p5pct_strict`,
- erklärst (oder direkt im Code setzt), welche Label-Parameter gelten sollen:
  - `horizon_days` (z. B. 4),
  - `up_threshold` / `down_threshold` (z. B. ±1 % oder ±0.5 %),
  - `strict_monotonic` (z. B. `True` für einen streng steigenden/fallenden Pfad).

**Was du tun musst:**

- `EXP_ID` auf einen sprechenden Namen für das neue Experiment setzen.
- Die in der Zelle beschriebenen Parameter so einstellen, wie du das Experiment fahren möchtest.
- Die Zelle ausführen.

### 4.4 Labels erzeugen (über das Notebook)

Eine nächste Zelle im Notebook ruft intern die Label-Funktion auf, mit den von dir gesetzten Parametern.

**Fachlich passiert:**

- die Datei `data/raw/fx/EURUSDX.csv` wird gelesen,
- für jeden Tag wird `lookahead_return` und `label` bestimmt (auf Basis deiner Schwellen/Horizont),
- das Ergebnis wird als DataFrame zurückgegeben.

**Speicherung:**

- `data/processed/fx/eurusd_labels.csv`  
  → aktuelle Label-Datei (wird überschrieben),
- `data/processed/fx/eurusd_labels__<EXP_ID>.csv`  
  → Label-Datei für dieses Experiment (Archiv).

**Was du tun musst:**

- Die Labels-Zelle ausführen.
- Optional: die erzeugten CSV-Dateien in VS Code öffnen, um z. B. `label`-Verteilungen zu prüfen.

### 4.5 Trainingsdatensatz bauen (über das Notebook)

Anschließend gibt es eine Zelle, die den **Trainingsdatensatz** erstellt.

**Fachlich passiert:**

1. News-Features werden aus `data/processed/news/eodhd_daily_features.csv` geladen.
2. Die zum Experiment gehörende Label-Datei wird geladen:
   - `data/processed/fx/eurusd_labels__<EXP_ID>.csv`.
3. Beide Tabellen werden über die Spalte `date` gemerged (inner join).
4. Es werden zusätzliche Zielvariablen erzeugt:
   - `signal`: 1, wenn `label` ≠ `neutral`, sonst 0.
   - `direction`: 1 = up, 0 = down, `NaN` für `neutral`.
5. Es werden Zusatz-Features berechnet:
   - Kalender-Features:
     - `month`, `week`, `quarter`.
   - Preis-Features aus High/Low/Open/Close:
     - `intraday_range`, `intraday_range_pct`,
     - `body`, `body_pct`,
     - `upper_shadow`, `lower_shadow`.
   - Sentiment-Anteile:
     - `pos_share`, `neg_share`.
6. Es wird auf die relevanten Spalten reduziert (Features + Targets).

**Speicherung:**

- `data/processed/datasets/eurusd_news_training.csv`  
  → aktuelle Trainingsdaten (wird überschrieben),
- `data/processed/datasets/eurusd_news_training__<EXP_ID>.csv`  
  → Trainingsdaten für dieses Experiment.

**Was du tun musst:**

- Die Zelle ausführen.
- In der Notebook-Ausgabe siehst du typischerweise:
  - wie viele Zeilen der Datensatz hat,
  - wohin er gespeichert wurde.

### 4.6 Kontrolle im Notebook

Eine weitere Zelle lädt das Trainings-CSV für dein Experiment (`eurusd_news_training__<EXP_ID>.csv`) wieder ein und zeigt z. B.:

- die ersten Zeilen (`head()`),
- Verteilungen von `label`, `signal`, `direction`.

**Was du tun musst:**

- Die Kontrollzelle ausführen.
- Prüfen, ob:
  - die Spalten vollständig sind,
  - die Zahl der Zeilen plausibel ist,
  - die Label-Verteilung sinnvoll aussieht.

Damit ist die **Data Preparation für dieses Experiment abgeschlossen**.  
Der zugehörige Trainingsdatensatz liegt nun in:

- `data/processed/datasets/eurusd_news_training__<EXP_ID>.csv`

---

## 5. Modelltraining mit XGBoost (Skript-Variante)

Falls du das Training direkt als Skript ausführen möchtest (ohne Notebook):

- Skript: `src/models/train_xgboost_two_stage.py`

### 5.1 Training mit der aktuellen Trainingsdatei

```bash
python3 -m src.models.train_xgboost_two_stage
```

- Dieses Skript liest standardmäßig:
  - `data/processed/datasets/eurusd_news_training.csv`

### 5.2 Training mit einem spezifischen Experiment-CSV

Wenn du z. B. das Experiment `v1_h4_thr1pct_strict` trainieren willst:

```bash
python3 -m src.models.train_xgboost_two_stage \
    --dataset data/processed/datasets/eurusd_news_training__v1_h4_thr1pct_strict.csv \
    --test-start 2025-01-01 \
    --train-frac-pretest 0.8
```

### 5.3 Was das Skript fachlich macht

1. **Datensatz laden und sortieren**
   - Liest die angegebene CSV.
   - Parsed die `date`-Spalte und sortiert nach Datum.

2. **Zeitliche Splits erzeugen**
   - `test`:
     - alle Zeilen mit `date >= test-start` (z. B. ab 2025-01-01),
   - `train` + `val`:
     - alle Zeilen mit `date < test-start`,
     - Aufteilung innerhalb dieses Bereichs z. B. 80 % Train / 20 % Validation (gesteuert über `--train-frac-pretest`).

3. **Stufe 1: Signal-Modell**
   - Zielvariable: `signal` (0 = neutral, 1 = Bewegung up/down).
   - Input-Features: die in `FEATURE_COLS` definierten Spalten (Kombination aus News-, Preis- und Kalender-Features).
   - Trainiert ein binäres XGBoost-Modell (neutrale vs. Bewegung).
   - Gibt für `train`, `val`, `test` aus:
     - Accuracy,
     - Confusion-Matrix,
     - Classification Report (mit Precision/Recall/F1).

4. **Stufe 2: Richtungs-Modell**
   - Zielvariable: `direction` (0 = down, 1 = up), nur für Zeilen mit `signal == 1`.
   - Verwendet wieder `FEATURE_COLS` als Input.
   - Trainiert ein binäres XGBoost-Modell (up vs. down).
   - Gibt ebenfalls Metriken für `train`, `val`, `test` aus.

5. **Kombinierte Auswertung (3-Klassen-Label)**
   - Für den Test-Split:
     - Sagt zuerst `signal` vorher (Bewegung ja/nein),
     - sagt für Tage mit `signal==1` zusätzlich `direction` (up/down) vorher,
     - bildet daraus ein kombiniertes Label:
       - `neutral`, `up`, `down`.
   - Gibt dazu:
     - Confusion-Matrix für `neutral/up/down`,
     - Classification Report (Precision/Recall/F1 je Klasse).

- Die Metriken erscheinen im Terminal bzw. im Output-Fenster des Notebooks, wenn du das Skript von dort startest.

---

## 6. Modelltraining und Ergebnis-Speicherung (Notebook `2_train_xgboost_two_stage.ipynb`)

Für eine strukturierte Dokumentation und das Speichern von Ergebnissen als JSON nutzt du:

- Notebook: `notebooks/2_train_xgboost_two_stage.ipynb`

### 6.1 Notebook öffnen und konfigurieren

1. Notebook öffnen und `.venv`-Kernel wählen.
2. In der Konfigurationszelle:
   - `EXP_ID` so setzen, dass sie **genau** zur Data-Prep passt (z. B. `v2_h4_thr0p5pct_strict`).
   - ggf. weitere Einstellungen (Oversampling-Faktor etc.) setzen.
3. Zelle ausführen.

### 6.2 Daten laden und Splits erstellen

- Eine Zelle lädt:
  - `data/processed/datasets/eurusd_news_training__<EXP_ID>.csv`
- Verwendet Hilfsfunktionen aus `src.models.train_xgboost_two_stage`:
  - z. B. `load_dataset`, `split_train_val_test`.
- Die Splits (`train`, `val`, `test`) werden erzeugt, wie in Abschnitt 5 beschrieben.

### 6.3 Training, Evaluation und JSON-Ausgabe

- Weitere Zellen:
  - trainieren das Signal- und Richtungsmodell,
  - berechnen Metriken,
  - erzeugen bei Bedarf Plots (z. B. Feature-Importance).
- Eine spezielle Zelle:
  - sammelt alle relevanten Kennzahlen (z. B. Precision/Recall für Signal und Direction; kombinierte Test-Metriken),
  - schreibt sie in eine JSON-Datei, z. B.:
    - `notebooks/results/two_stage__<EXP_ID>.json`
    - und/oder `results/two_stage__<EXP_ID>.json`.

**Was du tun musst:**

- Alle Zellen der Reihe nach ausführen.
- Sicherstellen, dass `EXP_ID` konsistent mit dem Data-Prep-Notebook ist.
- Überprüfen, dass im Ordner `notebooks/results/` eine neue `two_stage__<EXP_ID>.json` entstanden ist.

---

## 7. Vergleich mehrerer Experimente (Notebook `3_results_xgboost_two_stage.ipynb`)

**Ziel:** Verschiedene Experimente (unterschiedliche EXP_IDs) komfortabel vergleichen.

- Notebook: `notebooks/3_results_xgboost_two_stage.ipynb`

### 7.1 Einlesen der Ergebnis-JSONs

- Das Notebook durchsucht z. B.:
  - `notebooks/results/` nach Dateien `two_stage__*.json`.
- Jede JSON enthält die Metriken eines Experiments.

### 7.2 Zusammenfassungstabelle

- Alle JSON-Dateien werden zu einem DataFrame kombiniert:
  - Eine Zeile pro `EXP_ID`,
  - Spalten für wichtige Metriken:
    - Accuracy/Precision/Recall/F1:
      - für das Signal-Modell (Bewegung vs. neutral),
      - für das Richtungs-Modell (up vs. down),
      - für die kombinierte 3-Klassen-Vorhersage.

### 7.3 Plots

- Mit z. B. `matplotlib`/`seaborn` werden Balkendiagramme erstellt, z. B.:
  - Vergleich der Precision/Recall für verschiedene EXP_IDs,
  - Gegenüberstellung von Signal- und Richtungs-Modell.

**Was du tun musst:**

- Notebook öffnen und alle Zellen ausführen.
- Die Tabellen und Plots interpretieren, um zu sehen:
  - welches Experiment (welche EXP_ID) bessere Precision/Recall liefert,
  - wie sich Änderungen an Label-Regeln oder Features auswirken.

---

## 8. Kurz-Checkliste: Neues Experiment von Rohdaten bis Ergebnis

1. **Umgebung und Projektordner**
   - Terminal:
     ```bash
     cd /Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project
     source .venv/bin/activate
     ```

2. **News-Tagesfeatures aktualisieren (falls neue News vorhanden sind)**
   - Terminal:
     ```bash
     python3 -m src.data.prepare_eodhd_news
     ```

3. **Data Preparation für das Experiment**
   - Notebook `notebooks/1_data_prep_xgboost_two_stage.ipynb`:
     - Kernel `.venv` wählen.
     - `EXP_ID` und Label-Parameter setzen.
     - Alle Zellen ausführen.
     - Ergebnis:
       - `data/processed/fx/eurusd_labels__<EXP_ID>.csv`
       - `data/processed/datasets/eurusd_news_training__<EXP_ID>.csv`

4. **Modelltraining + Ergebnis-JSON**
   - Notebook `notebooks/2_train_xgboost_two_stage.ipynb`:
     - `EXP_ID` passend setzen.
     - Alle Zellen ausführen.
     - Ergebnis:
       - `notebooks/results/two_stage__<EXP_ID>.json`
       - Modell-Metriken im Notebook.

5. **Experimente vergleichen**
   - Notebook `notebooks/3_results_xgboost_two_stage.ipynb`:
     - Alle Zellen ausführen.
     - Tabellen und Plots zum Vergleich der Experimente anschauen.

Damit ist der Weg von den Rohdaten (FX + News) bis zu den dokumentierten Modell-Ergebnissen klar strukturiert und pro Experiment reproduzierbar nachvollziehbar.  
