# Projektstruktur (Ist-Zustand)

Dieses Repo ist so aufgebaut, dass **jedes Experiment** über eine eindeutige `EXP_ID` läuft.
Damit sind Daten, Modelle, Reports und Resultate eindeutig zuordenbar und reproduzierbar.

## Aktuelle Pipelines (für die Abgabe)

Es gibt 3 aktive Pipelines (jeweils 3 Notebooks: Data‑Prep → Training → Evaluation):

1) **MT5 H1 (EURUSD, stündlich → täglich aggregiert)**
   - Notebooks: `notebooks/final_two_stage_h1/`
   - Rohdaten: `data/raw/fx/EURUSD_mt5_H1_2015_2025.csv`
   - Besonderheit: H1‑Bars werden mit `cut_hour` zu Tages‑Sessions aggregiert (FX‑Cut).

2) **Yahoo Finance (Daily)**
   - Notebooks: `notebooks/final_two_stage/`
   - Rohdaten (CSV): `data/raw/fx/EURUSDX.csv`

3) **EODHD (Daily)**
   - Notebooks: `notebooks/eodhd_two_stage/`
   - Rohdaten (CSV): `data/raw/fx/EURUSDX_eodhd.csv`
   - News‑Rohdaten (JSONL): `data/raw/news/eodhd_news.jsonl`

## Output‑Konvention pro Experiment (`EXP_ID`)

**Data‑Prep** schreibt:
- Labels: `data/processed/fx/eurusd_labels__<EXP_ID>.csv`
- Experiment‑Config: `data/processed/experiments/<EXP_ID>_config.json`
- Trainingsdatensatz:
  - mit News: `data/processed/datasets/eurusd_news_training__<EXP_ID>.csv`
  - ohne News: `data/processed/datasets/eurusd_price_training__<EXP_ID>.csv`

Optional kann ein Notebook zusätzlich „latest“-Dateien überschreiben (z.B. `eurusd_labels.csv`).
Das ist über `WRITE_LATEST = True/False` steuerbar und ist standardmäßig **False**.

**Training** schreibt:
- Basis‑Resultat: `notebooks/results/two_stage__<EXP_ID>.json`
- Final‑Resultat: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>.json`
- Metriken: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_metrics.csv`
- Predictions: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_predictions.csv`

**Evaluation / Report** schreibt:
- PDF‑Report: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_report.pdf`

## Zentrale Code‑Bausteine

- Labeling (Daily): `src/data/label_eurusd.py`
- MT5 H1 → Daily + Intraday‑Features: `src/data/mt5_h1.py`
- Trainingsdatensatz bauen (News+Price / Price‑only): `src/data/build_training_set.py`
- Features: `src/features/eurusd_features.py`
- Zwei‑Stufen‑Modell: `src/models/train_xgboost_two_stage.py`
- PDF‑Report‑Generator: `scripts/generate_two_stage_report.py`
- Symbolische KI (Fuzzy / FLEX) für Risiko/Einsatz:
  - Regeln: `rules/risk.flex` (und optional `rules/risk.ksl`)
  - Wrapper: `src/risk/flex_engine.py`
  - Position sizing: `src/risk/position_sizer.py`

## Archive / Alt

Der Ordner `archive/` enthält ältere Notebooks/Skripte/Module (z.B. eine frühere „v2“-Pipeline),
die **nicht** mehr für die aktuellen Experimente benötigt werden.
