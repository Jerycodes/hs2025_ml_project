# hs2025_ml_project

Projekt für das Modul **KI & Maschinelles Lernen** (HS2025).
Ziel ist eine reproduzierbare Pipeline, die **EURUSD** klassifiziert:

- **Stufe 1 (Signal):** `neutral` vs. `move`
- **Stufe 2 (Richtung):** `down` vs. `up` (nur wenn `move`)

Zusätzlich gibt es eine **symbolische KI‑Komponente** (Fuzzy‑Regeln via FLEX), die aus Modell‑Wahrscheinlichkeiten
und Risikofaktoren eine **Positionsgröße (CHF)** ableitet.

## Schnellstart

Voraussetzungen:
- Python **3.12**

Setup (im Repo‑Root):
- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`

Wenn Matplotlib Warnungen macht (Cache‑Pfad nicht beschreibbar), setze:
- `export MPLCONFIGDIR=/tmp/mpl`

## Aktuelle Experimente (Pipelines)

Alle Experimente laufen über eine eindeutige `EXP_ID`. Dadurch sind Outputs sauber trennbar und vergleichbar.

### Pipeline 1: MT5 H1 (stündlich → täglich)

Notebooks:
- `notebooks/final_two_stage_h1/1_data_prep_h1.ipynb`
- `notebooks/final_two_stage_h1/2_train_h1.ipynb`
- `notebooks/final_two_stage_h1/3_eval_h1.ipynb`

Rohdaten:
- `data/raw/fx/EURUSD_mt5_H1_2015_2025.csv`

Wichtig:
- `CUT_HOUR` steuert den „Tages‑Cut“ (FX‑Session‑Grenze) bei H1→Daily Aggregation.

### Pipeline 2: Yahoo Finance (Daily)

Notebooks:
- `notebooks/final_two_stage/1_data_prep_final.ipynb`
- `notebooks/final_two_stage/2_train_final.ipynb`
- `notebooks/final_two_stage/3_eval_final.ipynb`

Rohdaten:
- `data/raw/fx/EURUSDX.csv`

### Pipeline 3: EODHD (Daily + News)

Notebooks:
- `notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb`
- `notebooks/eodhd_two_stage/2_train_eodhd.ipynb`
- `notebooks/eodhd_two_stage/3_eval_eodhd.ipynb`

Rohdaten:
- `data/raw/fx/EURUSDX_eodhd.csv`
- `data/raw/news/eodhd_news.jsonl`

Hinweis:
- Die EODHD‑News‑Rohdaten sind bereits im Repo enthalten (kein API‑Token nötig).
- Ein optionaler Downloader liegt im Archiv: `archive/src/data/fetch_eodhd_news.py` (API‑Token nötig).

## Experiment durchführen (Protokoll)

Die 3 Pipelines haben immer denselben Ablauf:

1. **Data‑Prep** (Labels + Dataset bauen)
2. **Training** (Modelle trainieren + Resultate/Predictions schreiben)
3. **Evaluation** (PDF‑Report erzeugen)

### 0) `EXP_ID` wählen (wichtig)

- `EXP_ID` ist ein frei wählbarer String und ist nur ein „Label“ für dein Experiment.
- Wichtig ist nur: **Du musst dieselbe `EXP_ID` in allen 3 Notebooks der Pipeline setzen.**
- Empfehlung (nur Konvention): nutze sprechende Präfixe wie `hp_...` oder `hv_...` (z.B. `hp_long_yahoo_1`), damit du später an den Dateinamen erkennst, zu welchem Setup ein Experiment gehört.
  - Der Code wertet diese Präfixe **nicht** aus. Es ist reine Namenskonvention.

### 1) Data‑Prep Notebook ausführen (pro Pipeline)

Du setzt die Parameter immer im **„EXPERIMENT SETTINGS“**‑Block ganz oben im Notebook.

**Gemeinsame Parameter (alle Data‑Prep Notebooks):**
- `EXP_ID`: eindeutige ID (siehe oben).
- `USE_NEWS` + `FEATURE_MODE`: `USE_NEWS=True` → `FEATURE_MODE='news+price'`, sonst `price_only`.
  - Warum: steuert, ob News‑Features in den Trainingsdatensatz gemerged werden.
- `WRITE_LATEST`: wenn `True`, werden zusätzlich „latest“-Dateien ohne EXP‑Suffix überschrieben (z.B. `eurusd_labels.csv`).
  - Warum: praktisch fürs schnelle Arbeiten, aber **schlecht für Reproduzierbarkeit**. Für die Abgabe: **False** lassen.
- `LABEL_PARAMS`: definiert, wie die Labels aus der Preisreihe erzeugt werden (Trading‑Logik).
  - `horizon_days`: Vorhersagehorizont in Tagen.
  - `up_threshold` / `down_threshold`: Rendite‑Schwellen (z.B. `0.02` = +2%).
  - `hit_within_horizon`: `True` → Treffer **irgendwo** im Fenster `[t, t+horizon_days]` reicht (Take‑Profit‑ähnlich).
  - `first_hit_wins`: nur relevant bei `hit_within_horizon=True`; erster Treffer (up/down) entscheidet.
  - `drop_weekends`: filtert Sa/So aus der Zeitreihe (sinnvoll, wenn eine Quelle Wochenend‑Zeilen enthält).

**Pipeline 1 (MT5 H1 → Daily):** `notebooks/final_two_stage_h1/1_data_prep_h1.ipynb`
- Zusätzlich setzen:
  - `H1_CSV_PATH`: Pfad zur MT5‑H1 CSV (`data/raw/fx/EURUSD_mt5_H1_2015_2025.csv`).
  - `CUT_HOUR`: definiert den „Tages‑Cut“ bei der Aggregation von H1 → Daily (FX‑Session‑Grenze).
  - `DROP_WEEKENDS`: ob Wochenenden aus der aggregierten Daily‑Serie entfernt werden.
  - In `LABEL_PARAMS`:
    - `hit_source='h1'`: nutzt die stündlichen Bars für eine pfad‑nähere Trefferlogik.
    - `intraday_tie_breaker`: falls up und down im selben Fenster getroffen werden, entscheidet diese Regel.

**Pipeline 2 (Yahoo Daily):** `notebooks/final_two_stage/1_data_prep_final.ipynb`
- In `LABEL_PARAMS` ist `price_source='yahoo'` und liest `data/raw/fx/EURUSDX.csv` (siehe `src/data/label_eurusd.py`).

**Pipeline 3 (EODHD Daily + News):** `notebooks/eodhd_two_stage/1_data_prep_eodhd.ipynb`
- In `LABEL_PARAMS` ist `price_source='eodhd'` und liest `data/raw/fx/EURUSDX_eodhd.csv`.
- News‑Rohdaten sind bereits vorhanden: `data/raw/news/eodhd_news.jsonl`.

Nach dem Run schreibt Data‑Prep (immer mit `__<EXP_ID>` im Dateinamen):
- Labels nach `data/processed/fx/`
- Config nach `data/processed/experiments/`
- Dataset nach `data/processed/datasets/`

### 2) Training Notebook ausführen

Du setzt wieder `EXP_ID` (muss zur Data‑Prep passen) und – falls vorhanden – `USE_NEWS`.

- MT5 H1: `notebooks/final_two_stage_h1/2_train_h1.ipynb`
  - Zusätzlich relevant: `USE_VALIDATION`, `TRAIN_FRAC_PRETEST`, Threshold‑Tuning/Fixed‑Thresholds.
- Yahoo: `notebooks/final_two_stage/2_train_final.ipynb`
- EODHD: `notebooks/eodhd_two_stage/2_train_eodhd.ipynb`

Training schreibt:
- Final‑Result (JSON): `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>.json`
- Metrics (CSV): `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_metrics.csv`
- Predictions (CSV): `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_predictions.csv`

### 3) Evaluation / PDF‑Report erzeugen

Eval‑Notebook öffnen, `EXP_ID` setzen und ausführen:
- MT5 H1: `notebooks/final_two_stage_h1/3_eval_h1.ipynb`
- Yahoo: `notebooks/final_two_stage/3_eval_final.ipynb`
- EODHD: `notebooks/eodhd_two_stage/3_eval_eodhd.ipynb`

Das Notebook erzeugt den PDF‑Report unter:
- `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_report.pdf`

Alternative: PDF direkt per Script:
- `python3 -m scripts.generate_two_stage_report --exp-id <EXP_ID>`

### 4) Hinweis zu „hp/hv“ im Namen

Einige Notebooks enthalten Beispiel‑IDs wie `hp_...` oder `hv_...`.
Das ist nur eine **Namenskonvention**, damit man Labels/Settings später schneller zuordnen kann.
Für die Pipeline ist nur wichtig, dass `EXP_ID` eindeutig ist und in Data‑Prep/Train/Eval übereinstimmt.

## Output pro `EXP_ID`

Data‑Prep:
- Labels: `data/processed/fx/eurusd_labels__<EXP_ID>.csv`
- Config: `data/processed/experiments/<EXP_ID>_config.json`
- Dataset:
  - News+Price: `data/processed/datasets/eurusd_news_training__<EXP_ID>.csv`
  - Price‑only: `data/processed/datasets/eurusd_price_training__<EXP_ID>.csv`

Training / Evaluation:
- Results (final): `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>.json`
- Metrics: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_metrics.csv`
- Predictions: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_predictions.csv`
- PDF‑Report: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_report.pdf`

PDF‑Report manuell erzeugen:
- `python3 -m scripts.generate_two_stage_report --exp-id <EXP_ID>`

## Symbolische KI (FLEX / Fuzzy Risk)

- Regeln: `rules/risk.flex` (und optional `rules/risk.ksl`)
- Wrapper: `src/risk/flex_engine.py`
- Positionsgröße (CHF): `src/risk/position_sizer.py`
- Demo: `python3 -m src.risk.demo_position_sizer`

## Was ist „alt“?

Alte/abgelöste Artefakte liegen in `archive/` und werden für die Abgabe nicht benötigt.
Sie sind bewusst ausgelagert, damit die aktuellen Notebooks schnell verständlich sind.
