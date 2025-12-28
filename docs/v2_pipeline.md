## v2 Pipeline (getrennt vom bisherigen System)

Ziel der v2-Pipeline:
- Bestehende Notebooks/Skripte **nicht verändern**.
- Alle Parameter **zentral** definieren, so dass:
  - `EXP_ID` **aus genau dieser Config** abgeleitet wird,
  - Labels/Training/Report **dieselbe Config** benutzen,
  - es keine “Hardcoded” Parameter im PDF gibt.
- Outputs werden ausschließlich unter `data/processed/v2/` abgelegt.

---

### Output-Struktur

Pro Experiment-ID (`EXP_ID`) entstehen (keine “latest” Files, kein Überschreiben des alten Systems):
- Config: `data/processed/v2/experiments/<EXP_ID>_config.json`
- Labels: `data/processed/v2/fx/eurusd_labels__<EXP_ID>.csv`
- Dataset (price-only): `data/processed/v2/datasets/eurusd_price_training__<EXP_ID>.csv`
- Results (JSON/CSV): `data/processed/v2/results/two_stage__<EXP_ID>.*`
- PDF Report: `data/processed/v2/reports/two_stage__<EXP_ID>.pdf`
- Manifest (Pfade an einem Ort): `data/processed/v2/results/two_stage__<EXP_ID>_manifest.json`

Der PDF-Report enthält:
- alle relevanten Parameter aus `results['config']` (inkl. `data_params`, `label_params`, Thresholds, Cost-Model),
- Pfade zu Config/Labels/Dataset/Results/Predictions/Manifest,
- Confusion-Matrizen,
- vollständigen Config-Dump (Audit-Page).

---

### Notebooks (v2)

**0) Parameter kalibrieren (TP/SL/ATR)**
- Notebook: `notebooks/v2_two_stage/0_calibrate_params_v2.ipynb`
- Zweck: datenbasiert entscheiden, ob fix-% Stop oder ATR-Stop sinnvoll ist und welche Größenordnung passt.

**1) Experimente laufen lassen**
- Notebook: `notebooks/v2_two_stage/1_run_experiments_v2.ipynb`
- In einer zentralen Zelle definierst du:
  - Datenquellen (Yahoo/EODHD),
  - Label-Varianten (`close_path` vs `tp_sl`, inkl. Parameterlisten),
  - Modell-/Threshold-Search-Parameter.
- Das Notebook erzeugt EXP_IDs, speichert die Configs und ruft den Runner pro EXP_ID auf.

**2) Ergebnisse zusammenfassen (Ranking/Tabelle)**
- Notebook: `notebooks/v2_two_stage/2_summarize_results_v2.ipynb`
- Erzeugt:
  - `data/processed/v2/summary/v2_summary.csv`
  - `data/processed/v2/summary/v2_summary.md`

---

### Runner (CLI)

Alles-in-einem (Labels → Dataset → Training → PDF):

`python3 -m scripts.run_two_stage_experiment_v2 --exp-id <EXP_ID>`

oder direkt aus einer JSON-Config:

`python3 -m scripts.run_two_stage_experiment_v2 --config path/to/<EXP_ID>_config.json`

Summary/Ranking:

`python3 -m scripts.summarize_v2_results`

---

### Label-Logiken

**A) `close_path` (v1-kompatibel):**
- nutzt `src/data/label_eurusd.py`
- optionaler Pfadfilter `max_adverse_move_pct` kann sehr sensitiv sein.

**B) `tp_sl` (trading-nah):**
- nutzt `src/data/label_eurusd_trade.py`
- prüft TP/SL über High/Low innerhalb eines Horizonts.
- optional ATR-Stop (`sl_mode='atr'`).

---

### Daily-Cut Hinweis (wichtig für Live-Trading)

FX-Daily-Kerzen hängen am “Cut” (Timezone/Session-Close). Yahoo und EODHD können
bei ähnlichem Preisniveau unterschiedliche Daily-Returns liefern.
Für Live-Trading sollte idealerweise der Cut des Brokers (ActiveTrades) reproduziert werden
(oder du trainierst direkt auf Broker-OHLC).
