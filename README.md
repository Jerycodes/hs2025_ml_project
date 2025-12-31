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
