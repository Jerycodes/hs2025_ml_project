# Dokumentation: Von Rohdaten zu Modellergebnissen (EURUSD & News)

Dieses Dokument beschreibt Schritt für Schritt, wie du in diesem Projekt

- von den **Rohdaten** (FX-Kurse und News)
- zu einem **trainierten Zwei-Stufen-XGBoost-Modell**
- und zu **vergleichbaren Ergebnissen pro Experiment**

kommst.

Für jeden Schritt wird erklärt:

- **Was** gemacht wird (fachlich),
- **Womit** es gemacht wird (Skript/Notebook, wichtige Importe),
- **Wo** es ausgeführt wird (Terminal vs. Notebook),
- **Wie** es ausgeführt wird (konkreter Befehl),
- **Was dabei entsteht** (Dateien, Spalten, Abkürzungen).

Python-Code der internen Funktionen wird hier nicht gezeigt, nur die Abläufe.

---

## 0. Voraussetzungen und Umgebung

In diesem Abschnitt wird beschrieben, welche technischen Rahmenbedingungen nötig sind, damit alle weiteren Schritte zuverlässig funktionieren. Es geht darum, dass du im richtigen Ordner arbeitest, das passende Python-Environment verwendest und Notebooks später denselben Interpreter sehen wie das Terminal.

Bevor du mit der Pipeline arbeitest, brauchst du:

- Python 3 (im Projekt ist ein virtuelles Environment `.venv` eingerichtet),
- alle Abhängigkeiten aus `requirements.txt` installiert,
- Zugriff auf das Projektverzeichnis.

### 0.1 Projektordner und virtuelles Environment

Im Terminal:

```bash
cd /Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project
source .venv/bin/activate
```

Damit

- zeigt das aktuelle Verzeichnis auf das Projekt,
- verwendest du das richtige Python-Environment (mit allen Bibliotheken).

### 0.2 Notebook-Kernel

In VS Code / Jupyter:

- als Kernel das Python aus `.venv` auswählen (derselbe Interpreter, den du im Terminal verwendest),
- so stellen wir sicher, dass dieselben Pakete und Pfade verfügbar sind.

---

## 1. Überblick: Ordnerstruktur und Hauptkomponenten

Bevor wir in die einzelnen Schritte einsteigen, ist es hilfreich zu wissen, **wo** welche Daten und Skripte liegen. Dieser Abschnitt ist wie eine kleine Landkarte des Projekts: Du siehst, wo Rohdaten gespeichert sind, wo verarbeitete Daten landen und welche Python-Module für welche Aufgabe zuständig sind. So kannst du später jeden Dateinamen aus den folgenden Schritten direkt einordnen.

Wichtige Verzeichnisse:

- `data/raw/`
  - Rohdaten, unverändert:
    - `data/raw/fx/EURUSDX.csv` – EURUSD-Kurse (Tagesdaten),
    - `data/raw/news/eodhd_news*.jsonl` – News von EODHD (eine Zeile = ein Artikel, JSON).
- `data/processed/`
  - verarbeitete Daten (Ausgaben der Skripte):
    - `data/processed/news/eodhd_daily_features.csv` – News-Features pro Tag,
    - `data/processed/fx/eurusd_labels*.csv` – labels pro Tag,
    - `data/processed/datasets/eurusd_news_training*.csv` – Trainingsdatensätze.
- `src/data/`
  - Skripte zur Datenaufbereitung:
    - `fetch_eodhd_news.py` – News von der API holen,
    - `prepare_eodhd_news.py` – News pro Tag aggregieren,
    - `label_eurusd.py` – Labels aus FX-Kursen erzeugen,
    - `build_training_set.py` – Labels + News + Features zu Trainingsdaten verbinden.
- `src/models/`
  - Skripte zum Modelltraining:
    - `train_xgboost.py` – ursprüngliches Modell,
    - `train_xgboost_two_stage.py` – Zwei-Stufen-XGBoost (Signal + Richtung).
- `notebooks/`
  - gesteuerte Workflows und Experimente:
    - `1_data_prep_xgboost_two_stage.ipynb` – Data Preparation pro Experiment,
    - `2_train_xgboost_two_stage.ipynb` – Training + Metriken + JSON-Ergebnisse,
    - `3_results_xgboost_two_stage.ipynb` – Vergleich verschiedener Experimente,
    - `eda_eurusd_news.ipynb` – Explorative Analysen und Plots.

Wichtige Hilfsbibliotheken, die in den Skripten importiert werden:

- `pandas` – Tabellen / DataFrames,
- `numpy` – numerische Arrays, Berechnungen,
- `requests` – HTTP-Anfragen (für die News-API),
- `xgboost` – XGBoost-Modelle,
- `sklearn` – Metriken (Accuracy, Precision, Recall, F1, Confusion Matrix),
- `matplotlib`, `seaborn` – Plots in Notebooks.

---

## 2. Rohdaten: Was liegt wo?

Die Rohdaten sind der Ausgangspunkt für alles, was wir später machen. Sie werden nicht verändert, sondern nur gelesen. In diesem Abschnitt wird beschrieben, welche Rohdaten es gibt, wie sie aufgebaut sind und von welchen Skripten sie verwendet werden. So weißt du genau, auf welcher Basis die weiteren Berechnungen erfolgen.

### 2.1 FX-Daten (EURUSD)

- Datei: `data/raw/fx/EURUSDX.csv`
- Inhalt:
  - `Date` – Datum (YYYY-MM-DD),
  - `Open`, `High`, `Low`, `Close` – Tageskurs (Open/High/Low/Close),
  - `Volume` – Volumen (falls verfügbar).
- Verwendung:
  - `src/data/label_eurusd.py` liest diese Datei, um Labels zu erzeugen.

### 2.2 News-Daten (EODHD)

- Dateien:
  - `data/raw/news/eodhd_news.jsonl` – Hauptdatensatz,
  - optional weitere Teilfiles wie `eodhd_news_2019.jsonl`, `eodhd_news_2020_early.jsonl`.
- Inhalt:
  - pro Zeile ein JSON-Objekt mit Feldern wie:
    - Datum/Zeit,
    - Symbol,
    - Überschrift, Text,
    - Sentiment-Scores.
- Verwendung:
  - `src/data/fetch_eodhd_news.py` erzeugt diese Dateien,
  - `src/data/prepare_eodhd_news.py` aggregiert aus diesen Files Tages-Features.

---

## 3. News von der EODHD-API holen (optional)

Manchmal möchtest du weitere oder aktuellere News-Daten von der EODHD-API abrufen. Dieser Schritt ist optional, weil du bereits vorhandene `.jsonl`-Dateien weiterverwenden kannst. Wenn sich der Zeitraum oder der Umfang der News ändern soll, kannst du über dieses Skript neue Rohdaten erzeugen.

Wenn du neue News laden möchtest, verwendest du:

- Skript: `src/data/fetch_eodhd_news.py`

Dieses Skript

- importiert u. a. `requests`, `argparse`, `os` und `pathlib`,
- verwendet deinen EODHD-API-Key (meist über die Umgebungsvariable `EODHD_TOKEN`),
- ruft die News-API von EODHD auf,
- schreibt die API-Antwort in `.jsonl`-Dateien unter `data/raw/news/`.

Beispielaufruf im Terminal (Symbol und Zeitraum sind nur exemplarisch):

```bash
python3 -m src.data.fetch_eodhd_news \
    --token "$EODHD_TOKEN" \
    --symbol "EURUSD.FOREX" \
    --start "2020-01-01" \
    --end "2024-12-31"
```

Dabei entsteht z. B.:

- `data/raw/news/eodhd_news.jsonl`

Wenn du bereits passende `.jsonl`-Dateien hast, musst du dieses Skript nicht erneut laufen lassen.

---

## 4. News-Tagesfeatures erzeugen

Die Roh-News liegen zunächst als einzelne Artikel in JSONL-Dateien vor. Für das spätere Modell ist es aber sinnvoll, pro Tag nur eine Zeile mit zusammengefassten Kennzahlen zu haben. In diesem Schritt werden daher alle Artikel eines Tages zu sogenannten Tages-Features zusammengefasst, etwa Anzahl der News oder durchschnittliche Sentiment-Werte.

**Ziel:** Wir bauen aus allen Artikeln eines Tages einen einzigen Datensatz mit Tages-Features (z. B. wie viele Artikel, durchschnittliches Sentiment).

- Skript: `src/data/prepare_eodhd_news.py`
- Importe:
  - `pandas` – JSONL einlesen, gruppieren,
  - `pathlib` – Pfade,
  - eigene Hilfsfunktionen aus `src.utils.io` (z. B. `DATA_RAW`, `DATA_PROCESSED`).

### 4.1 Ausführung im Terminal

Im Projektwurzel-Ordner:

```bash
python3 -m src.data.prepare_eodhd_news
```

### 4.2 Was das Skript fachlich macht

1. **Einlesen der Roh-News**  
   - Alle relevanten `.jsonl`-Dateien aus `data/raw/news/` werden eingelesen.
2. **Konvertierung in einen DataFrame**  
   - JSON-Zeilen werden in Tabellenform gebracht.
3. **Gruppierung nach Datum**  
   - Alle Artikel mit demselben Datum werden zusammengefasst.
4. **Berechnung von Tages-Features**, u. a.:
   - `article_count`: Anzahl Artikel pro Tag,
   - `avg_polarity`: mittlerer Sentiment-Polarity-Wert,
   - `avg_neg`: mittlerer negativer Anteil,
   - `avg_neu`: mittlerer neutraler Anteil,
   - `avg_pos`: mittlerer positiver Anteil.
5. **Speichern als CSV**  
   - Die Tages-Features werden nach  
     `data/processed/news/eodhd_daily_features.csv` geschrieben.

### 4.3 Ergebnis und Abkürzungen

- Datei: `data/processed/news/eodhd_daily_features.csv`
- wichtige Spalten:
  - `date` – Datum (Tages-Schlüssel),
  - `article_count` – Anzahl News-Artikel an diesem Tag,
  - `avg_polarity` – durchschnittlicher Polarity-Wert (negativ = negativ, positiv = positiv),
  - `avg_neg` – durchschnittlicher negativer Sentiment-Anteil,
  - `avg_neu` – durchschnittlicher neutraler Sentiment-Anteil,
  - `avg_pos` – durchschnittlicher positiver Sentiment-Anteil.

---

## 5. Labels aus FX-Daten erzeugen

Damit das Modell überhaupt lernen kann, brauchen wir Zielwerte (Labels), die sagen, ob der Kurs in den nächsten Tagen eher steigt, fällt oder sich neutral verhält. In diesem Schritt werden aus den historischen Kursen solche Labels berechnet. Damit wird aus einer reinen Kurs-Zeitreihe ein Datensatz mit klaren Klassen, die das Modell vorhersagen soll.

**Ziel:** Jedem Tag wird ein Label `up`, `down` oder `neutral` zugewiesen, abhängig von der Kursentwicklung in den nächsten Tagen.

- Skript: `src/data/label_eurusd.py`
- Importe:
  - `pandas` – CSV lesen und Zeitreihen verarbeiten,
  - `numpy` – Differenzen und Monotonie prüfen,
  - `argparse` – Kommandozeilenparameter (z. B. `--exp-id`),
  - `pathlib` – Pfade,
  - `src.utils.io` – Konstanten `DATA_RAW`, `DATA_PROCESSED`.

### 5.1 Ausführung im Terminal (Standard-Setup mit Experiment-ID)

Beispiel für eine Experiment-ID:

- `v1_h4_thr1pct_strict`  
  (= Version 1, Horizont 4 Tage, ~1 %-Schwelle, strenge Monotonie).

Im Terminal:

```bash
python3 -m src.data.label_eurusd --exp-id v1_h4_thr1pct_strict
```

### 5.2 Was das Skript fachlich macht

1. **FX-Rohdaten einlesen**
   - Datei: `data/raw/fx/EURUSDX.csv`
   - Spalten: `Date`, `Open`, `High`, `Low`, `Close`, `Volume`.
2. **Daten säubern und sortieren**
   - Datumsspalte wird als Datum interpretiert,
   - Zeilen mit ungültigem Datum werden verworfen,
   - sortiert nach `Date`.
3. **Lookahead-Return berechnen**
   - Für jeden Tag wird der Schlusskurs `horizon_days` in der Zukunft verwendet (z. B. 4 Tage),
   - `lookahead_return = (Close_{t+4} - Close_t) / Close_t`.
4. **Monotonie-Bedingung prüfen** (bei `strict_monotonic = True`)
   - Für `up`:
     - Kurs muss an jedem Zwischentag steigen (alle täglichen Differenzen > 0),
   - Für `down`:
     - Kurs muss an jedem Zwischentag fallen (alle täglichen Differenzen < 0).
5. **Labels zuweisen**
   - `up`, wenn:
     - `lookahead_return` ≥ `up_threshold` (z. B. +1 %),
     - und die Monotonie-Bedingung für steigende Kurse erfüllt ist.
   - `down`, wenn:
     - `lookahead_return` ≤ `down_threshold` (z. B. −1 %),
     - und die Monotonie-Bedingung für fallende Kurse erfüllt ist.
   - ansonsten: `neutral`.

### 5.3 Ergebnis-Dateien

- `data/processed/fx/eurusd_labels.csv`
  - aktuelle Label-Datei (wird bei jedem Lauf überschrieben),
- `data/processed/fx/eurusd_labels__<EXP_ID>.csv`
  - experiment-spezifische Label-Datei (Archiv für dieses Setup),
  - `<EXP_ID>` ist die Experiment-ID aus dem Aufruf (z. B. `v1_h4_thr1pct_strict`).

Wichtige Spalten:

- `Date` – Datum,
- `Open`, `High`, `Low`, `Close`, `Volume`,
- `lookahead_return` – zukünftige Rendite über den Horizont,
- `label` – `neutral`, `up` oder `down`.

---

## 6. Trainingsdatensatz: Labels + News + Zusatz-Features

Bis hierher liegen die Informationen noch getrennt vor: Die Labels stammen aus den FX-Daten, die News-Informationen aus der API. Für das Modelltraining brauchen wir jedoch einen **gemeinsamen** Datensatz, in dem pro Tag sowohl das Label als auch alle relevanten Features stehen. In diesem Schritt werden die beiden Welten zusammengeführt und durch zusätzliche Merkmale wie Kalender- und Kerzen-Features ergänzt.

**Ziel:** Ein CSV, das direkt vom XGBoost-Modell verwendet werden kann: Labels, News-Features, zusätzliche Preis- und Kalender-Features.

- Skript: `src/data/build_training_set.py`
- Importe:
  - `pandas` – Mergen, Feature-Berechnung,
  - `argparse` – `--exp-id`,
  - `pathlib` – Pfade,
  - `src.utils.io` – `DATA_PROCESSED`.

### 6.1 Ausführung im Terminal mit Experiment-ID

Beispiel: du hast vorher `eurusd_labels__v1_h4_thr1pct_strict.csv` erzeugt.

Im Terminal:

```bash
python3 -m src.data.build_training_set --exp-id v1_h4_thr1pct_strict
```

### 6.2 Was das Skript fachlich macht

1. **News-Features laden**
   - Datei: `data/processed/news/eodhd_daily_features.csv`
   - enthält u. a.:
     - `date`,
     - `article_count`,
     - `avg_polarity`, `avg_neg`, `avg_neu`, `avg_pos`.
2. **Labels laden**
   - Datei:
     - bei gesetzter `--exp-id`: `data/processed/fx/eurusd_labels__<EXP_ID>.csv`,
     - sonst: `data/processed/fx/eurusd_labels.csv`.
   - Spalte `Date` wird in `date` umbenannt.
3. **Merge auf `date`**
   - News und Labels werden mit einem inner join auf `date` zusammengeführt,
   - Ergebnis: nur Tage mit sowohl Kurs-Label als auch News-Features.
4. **Zielvariablen erzeugen**
   - `signal`:
     - 1, wenn `label` ≠ `neutral` (also Bewegung),
     - 0, wenn `label` = `neutral`.
   - `direction`:
     - 1 = up,
     - 0 = down,
     - `NaN` für `neutral` (wird im Richtungs-Modell ignoriert).
5. **Kalender-Features berechnen**
   - `month`: Monat 1–12,
   - `week`: ISO-Kalenderwoche,
   - `quarter`: Quartal 1–4.
6. **Preis-Features aus High/Low/Open/Close**
   - `intraday_range` = `High - Low`  
     → Spanne des Tages in absoluten Punkten.
   - `intraday_range_pct` = `intraday_range / Close`  
     → Spanne relativ zum Schlusskurs (Volatilität).
   - `body` = `Close - Open`  
     → Kerzenkörper (positiv = bullischer Tag).
   - `body_pct` = `body / Close`
   - `upper_shadow` = `High - max(Open, Close)`  
     → oberer Docht der Kerze.
   - `lower_shadow` = `min(Open, Close) - Low`  
     → untere Lunte der Kerze.
7. **Sentiment-Anteile**
   - `pos_share` = `avg_pos / (avg_pos + avg_neg)`  
   - `neg_share` = `avg_neg / (avg_pos + avg_neg)`  
   → Verhältnis positiver/negativer Sentiment-Komponente.
8. **Spaltenauswahl**
   - Der finale Trainingsdatensatz enthält u. a.:
     - `date`,
     - `label`, `signal`, `direction`,
     - `month`, `week`, `quarter`,
     - `intraday_range`, `intraday_range_pct`,
     - `body`, `body_pct`,
     - `upper_shadow`, `lower_shadow`,
     - `pos_share`, `neg_share`,
     - `lookahead_return`,
     - `article_count`, `avg_polarity`, `avg_neg`, `avg_neu`, `avg_pos`.

### 6.3 Ergebnis-Dateien

- `data/processed/datasets/eurusd_news_training.csv`
  - aktuelle Trainingsdaten (wird bei jedem Lauf überschrieben),
- `data/processed/datasets/eurusd_news_training__<EXP_ID>.csv`
  - Trainingsdaten für dieses Experiment (Archiv).

---

## 7. Zwei-Stufen-XGBoost: Modelltraining

Wenn der Trainingsdatensatz steht, geht es darum, ein Modell zu trainieren, das aus den Features sinnvolle Vorhersagen ableiten kann. Das hier verwendete Verfahren ist ein Zwei-Stufen-XGBoost: Zuerst wird entschieden, ob überhaupt eine Bewegung stattfindet, und nur in diesem Fall wird in einem zweiten Schritt die Richtung (up/down) vorhergesagt. Dadurch lässt sich das unausgeglichene Verhältnis zwischen neutralen und Bewegungs-Tagen besser handhaben.

**Ziel:** Ein Modell, das

- zuerst vorhersagt, ob es eine signifikante Bewegung gibt (Signal),
- und dann – falls ja – die Richtung (up vs. down).

- Skript: `src/models/train_xgboost_two_stage.py`
- Importe:
  - `pandas`, `numpy` – Daten,
  - `xgboost` – XGBoost-Classifier,
  - `sklearn.metrics` – Accuracy, Confusion-Matrix, Classification Report,
  - `argparse`, `pathlib`.

### 7.1 Training über das Skript (Terminal)

Mit der **aktuellen** Trainingsdatei:

```bash
python3 -m src.models.train_xgboost_two_stage
```

oder mit einer **Experiment-spezifischen** Datei:

```bash
python3 -m src.models.train_xgboost_two_stage \
    --dataset data/processed/datasets/eurusd_news_training__v1_h4_thr1pct_strict.csv \
    --test-start 2025-01-01 \
    --train-frac-pretest 0.8
```

### 7.2 Was das Skript fachlich macht

1. **Datensatz laden**
   - liest die angegebene CSV (Standard: `eurusd_news_training.csv`),
   - parsed die `date`-Spalte,
   - sortiert nach Datum.
2. **Zeitliche Splits**
   - `test`: alle Zeilen mit `date >= test-start` (z. B. 2025-01-01),
   - `train` + `val`: alle Zeilen davor,
     - Aufteilung im Verhältnis `train-frac-pretest` (z. B. 80 % train, 20 % val).
3. **Stufe 1 – Signal-Modell**
   - Zielvariable: `signal` (0 = neutral, 1 = Bewegung),
   - Features: eine vordefinierte Liste `FEATURE_COLS` (News-, Preis-, Kalender-Features),
   - trainiert ein binäres XGBoost-Modell,
   - wertet für `train`, `val`, `test` aus:
     - Accuracy,
     - Confusion-Matrix,
     - Classification Report (mit Precision/Recall/F1).
4. **Stufe 2 – Richtungs-Modell**
   - Zielvariable: `direction` (0 = down, 1 = up),
   - verwendet nur Zeilen mit `signal == 1`,
   - trainiert erneut ein binäres XGBoost-Modell,
   - wertet für `train`, `val`, `test` aus.
5. **Kombinierte Auswertung (3 Klassen)**
   - Für den Test-Split:
     - Vorhersage des Signals,
     - Vorhersage der Richtung für Tage mit vorhergesagtem `signal == 1`,
     - Bildung eines kombinierten Labels (`neutral`, `up`, `down`),
   - Auswertung:
     - Confusion-Matrix für `neutral/up/down`,
     - Classification Report.

Die Ergebnisse werden im Terminal ausgegeben.  
Für eine strukturierte Speicherung als JSON wird das Trainings-Notebook verwendet.

---

## 8. Notebook-basierter Workflow (Empfohlen für Experimente)

Die bisherigen Schritte lassen sich alle über Skripte im Terminal ausführen. Für die tägliche Arbeit, zum Ausprobieren verschiedener Parameter und zum Dokumentieren von Ergebnissen ist es jedoch praktischer, mit Notebooks zu arbeiten. In diesem Abschnitt wird deshalb beschrieben, wie die drei zentralen Notebooks zusammenwirken, um Experimente sauber zu steuern, Ergebnisse zu speichern und sie später zu vergleichen.

Für Experimente mit klaren IDs und Versionierung gibt es drei zentrale Notebooks:

- `notebooks/1_data_prep_xgboost_two_stage.ipynb`
- `notebooks/2_train_xgboost_two_stage.ipynb`
- `notebooks/3_results_xgboost_two_stage.ipynb`

### 8.1 Notebook 1: Data Preparation pro Experiment

Datei: `notebooks/1_data_prep_xgboost_two_stage.ipynb`

**Importe** (sinngemäß):

- Bibliotheken wie `pandas`, `pathlib`, `os`, `sys`,
- Funktionen aus `src.data.label_eurusd` und `src.data.build_training_set`,
- Konstanten aus `src.utils.io` (`DATA_RAW`, `DATA_PROCESSED`).

**Ablauf:**

1. Projektwurzel bestimmen und `os.chdir(...)` dorthin.
2. `EXP_ID` setzen (z. B. `v2_h4_thr0p5pct_strict`) und Label-Parameter definieren.
3. Labels mit diesen Parametern erzeugen und speichern:
   - `eurusd_labels.csv` und `eurusd_labels__<EXP_ID>.csv`.
4. Trainingsdatensatz für dieses Experiment erzeugen:
   - `eurusd_news_training.csv` und `eurusd_news_training__<EXP_ID>.csv`.
5. Kontrolle:
   - CSV laden,
   - erste Zeilen und Label-Verteilungen ansehen.

**Was du tun musst:**

- Kernel `.venv` wählen,
- `EXP_ID` und ggf. Parameter anpassen,
- alle Zellen nacheinander ausführen.

### 8.2 Notebook 2: Training + JSON-Ergebnisse

Datei: `notebooks/2_train_xgboost_two_stage.ipynb`

**Importe** (sinngemäß):

- `pandas`, `numpy`, `matplotlib`, `seaborn`,
- Funktionen aus `src.models.train_xgboost_two_stage` (z. B. `load_dataset`, `split_train_val_test`, Training-Funktionen),
- `json` zum Speichern der Ergebnisse.

**Ablauf:**

1. `EXP_ID` setzen (muss zur Data-Prep passen).
2. Trainings-CSV `eurusd_news_training__<EXP_ID>.csv` laden.
3. Zeitliche Splits (train/val/test) erzeugen.
4. Zwei-Stufen-XGBoost trainieren (Signal + Richtung).
5. Metriken berechnen (Accuracy, Precision, Recall, F1).
6. Ergebnisse in eine JSON-Datei schreiben:
   - z. B. `notebooks/results/two_stage__<EXP_ID>.json`.

**Was du tun musst:**

- Kernel `.venv` wählen,
- `EXP_ID` korrekt setzen,
- alle Zellen ausführen,
- prüfen, ob die JSON im `notebooks/results/`-Ordner erzeugt wurde.

### 8.3 Notebook 3: Vergleich der Experimente

Datei: `notebooks/3_results_xgboost_two_stage.ipynb`

**Importe** (sinngemäß):

- `json`, `pandas`, `matplotlib`, `seaborn`,
- `pathlib` zum Auflisten der Ergebnisdateien.

**Ablauf:**

1. Alle `two_stage__*.json` aus `notebooks/results/` einlesen.
2. Aus jeder JSON die wichtigsten Kennzahlen extrahieren (z. B. Precision/Recall für Signal und Richtung).
3. Eine Übersichtstabelle (DataFrame) pro Experiment-ID erstellen.
4. Plots zeichnen (z. B. Balkendiagramme für Precision/Recall).

**Was du tun musst:**

- Notebook öffnen,
- alle Zellen ausführen,
- Tabellen und Plots zur Bewertung der Experimente nutzen.

---

## 9. Kurz-Zusammenfassung: Komplettes Experiment

Zum Abschluss fassen wir den gesamten Ablauf noch einmal komprimiert zusammen. Die folgenden Punkte kannst du als Checkliste verwenden, wenn du ein neues Experiment startest: von der Einrichtung der Umgebung über die Datenaufbereitung und das Training bis hin zum Vergleich der erzielten Ergebnisse.

1. **Umgebung vorbereiten**
   - Terminal:
     ```bash
     cd /Users/jeremynathan/Documents/GitHub/hs2025_ml_project/hs2025_ml_project
     source .venv/bin/activate
     ```
   - Notebook-Kernel auf dieses `.venv` setzen.

2. **News-Features aktualisieren (falls neue Roh-News)**
   - Terminal:
     ```bash
     python3 -m src.data.prepare_eodhd_news
     ```

3. **Data Preparation für eine Experiment-ID**
   - Notebook `1_data_prep_xgboost_two_stage.ipynb`:
     - `EXP_ID` und Parameter setzen,
     - alle Zellen ausführen,
     - Ergebnis: `eurusd_labels__<EXP_ID>.csv` und `eurusd_news_training__<EXP_ID>.csv`.

4. **Modelltraining und Ergebnis-JSON**
   - Notebook `2_train_xgboost_two_stage.ipynb`:
     - dieselbe `EXP_ID` setzen,
     - alle Zellen ausführen,
     - Ergebnis: `two_stage__<EXP_ID>.json` im `notebooks/results/`-Ordner.

5. **Vergleich mehrerer Experimente**
   - Notebook `3_results_xgboost_two_stage.ipynb`:
     - alle Zellen ausführen,
     - Tabelle und Plots zur Bewertung der Experimente verwenden.

Damit ist für jede Experiment-ID klar dokumentiert:

- welche Label-Logik verwendet wurde,
- welche Trainingsdaten verwendet wurden,
- welche Modell-Metriken erreicht wurden.  
