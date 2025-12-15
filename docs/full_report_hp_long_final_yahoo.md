# Ausführlicher Report (für dich): Zwei‑Stufen‑XGBoost + Trading‑Simulation

**Projekt:** `hs2025_ml_project` (EURUSD, Labels, Feature‑Engineering, XGBoost)  
**Fokus‑Experiment:** `hp_long_final_yahoo` (price_only)  
**Kurz:** Zwei Stufen (Signal + Richtung), Trading‑Entscheidungen über Thresholds, Profit‑Simulation mit TP/SL‑Logik.

Dieses Dokument ist **nicht** für Folien gedacht, sondern als **Lern‑ und Nachschlage‑Text**: Was wurde gebaut, wie rechnet es, warum haben wir es so entschieden, was wurde verworfen und wie reproduzierst du alles.

---

## 0) Was du aktuell “hast” (Ist‑Zustand)

### 0.1 Pipeline‑Bausteine

1) **Labels aus FX‑Preisen** (up/down/neutral)  
- Code: `src/data/label_eurusd.py`  
- Output: `data/processed/fx/eurusd_labels*.csv`

2) **Trainingsdatensatz bauen** (Labels + Features)  
- Code: `src/data/build_training_set.py`, `src/features/eurusd_features.py`  
- Output: `data/processed/datasets/eurusd_news_training__<EXP_ID>.csv`

3) **Zwei‑Stufen‑Training** (XGBoost)  
- Stufe 1: Signal (neutral vs move)  
- Stufe 2: Richtung (down vs up, nur für move‑Tage)  
- Code: Kern‑Utilities in `src/models/train_xgboost_two_stage.py`  
- “Final‑Workflow” passiert primär im Notebook: `notebooks/final_two_stage/2_train_final.ipynb`

4) **Evaluation + PDF‑Reporting**  
- Code: `scripts/generate_two_stage_report.py`  
- Outputs: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>.json`, `..._metrics.csv`, `..._predictions.csv`, `..._report.pdf`

### 0.2 “Wahrheit” für dein Fokus‑Experiment (Dateien)

**Experiment‑Config (Label‑Params):**  
- `data/processed/experiments/hp_long_final_yahoo_config.json`

**Labels (pro Tag, inkl. Close):**  
- `data/processed/fx/eurusd_labels__hp_long_final_yahoo.csv`

**Trainingsdatensatz:**  
- `data/processed/datasets/eurusd_news_training__hp_long_final_yahoo.csv`

**Final‑Ergebnis (alles drin: config, model_params, confusion/report):**  
- `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json`

**Final‑Metriken (kurze Tabelle):**  
- `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_metrics.csv`

**Predictions im Test (für Fehlklassifikationen/Trading‑Analyse):**  
- `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_predictions.csv`

---

## 1) Anforderungen/Tools/Installation (damit alles läuft)

### 1.1 Python‑Umgebung

Du brauchst:
- Python 3.x
- `.venv` im Projekt (oder ein anderes Environment)
- Jupyter/VS Code für Notebooks

Setup (typisch):
```bash
cd hs2025_ml_project/hs2025_ml_project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1.2 Wichtige Libraries (was sie tun)

Aus `requirements.txt` (Auszug):
- `numpy`: schnelle Array‑Rechnungen (z.B. für Lookahead‑Segmente, Threshold‑Grid, Vektorisierung)
- `pandas`: Tabellen/CSV‑Handling, Join/Merge, Rolling‑Windows, GroupBy (Monats‑P&L)
- `xgboost`: ML‑Modelle auf tabellarischen Daten (Boosted Trees)
- `scikit-learn`: Metriken (Confusion Matrix, Classification Report)
- `matplotlib`, `seaborn`: Plots, PDF‑Pages
- `yfinance`: Yahoo‑FX‑Daten (EURUSDX)
- `eodhd`: EODHD API (News/FX‑Alternative)

---

## 2) Grundidee: Warum “Zwei‑Stufen” statt 3‑Klassen?

Wir wollen am Ende 3 Labels (`neutral`, `up`, `down`). Man könnte direkt ein 3‑Klassen‑Modell trainieren.  
Wir haben stattdessen:

1) **Signal‑Modell:** `neutral` vs `move`  
2) **Richtungs‑Modell:** `down` vs `up` (nur, wenn `move`)

Warum das oft besser ist:
- `neutral` ist typischerweise sehr häufig → 3‑Klassen‑Modelle lernen schnell “immer neutral”.
- Stufe 1 lernt “trade oder nicht trade”.
- Stufe 2 lernt “richtung” nur auf relevanten Fällen.
- In Trading ist “No Trade” eine valide Option → das passt gut zu Stufe 1 + “No‑Trade‑Zone” in Stufe 2.

---

## 3) Label‑Definition (entscheidet, was “richtig” überhaupt bedeutet)

### 3.1 Parameter im Fokus‑Experiment

Aus `data/processed/experiments/hp_long_final_yahoo_config.json`:
- `horizon_days = 4`
- `up_threshold = 0.004` (+0.4%)
- `down_threshold = -0.004` (−0.4%)
- `strict_monotonic = False`
- `max_adverse_move_pct = 0.01` (1%)
- `hit_within_horizon = True`
- (optional im Code unterstützt): `price_source = yahoo/eodhd`

### 3.2 Wie wird ein Label berechnet (konzeptionell)

Wir betrachten für jeden Tag `t` den Preis‑Pfad im Fenster:
`segment = [Close_t, Close_{t+1}, ..., Close_{t+h}]` mit `h = horizon_days`.

**Treffer‑Logik (hit_within_horizon=True):**
- Up‑Hit: `max(segment) >= Close_t * (1 + up_threshold)`
- Down‑Hit: `min(segment) <= Close_t * (1 + down_threshold)`

**Adverse‑Move Filter (tolerant):**
- Wenn wir **up** labeln wollen: der Kurs darf im Fenster nicht “zu stark nach unten” laufen:  
  `min(segment) >= Close_t * (1 - max_adverse_move_pct)`
- Wenn wir **down** labeln wollen: der Kurs darf nicht “zu stark nach oben” laufen:  
  `max(segment) <= Close_t * (1 + max_adverse_move_pct)`

**strict_monotonic=False** bedeutet:
- wir verlangen nicht, dass der Pfad jeden Tag streng steigt/fällt; nur TP/SL/Adverse‑Filter muss passen.

### 3.3 Warum diese Label‑Evolution?

Historisch (aus Commits):
- Start: “strikt” (Monotonie + Endpunkt‑Schwelle) → zu wenige up/down, sehr unbalanciert
- Dann: “tolerant” (`max_adverse_move_pct`) → realistischer, weniger “perfekte” Pfade nötig
- Dann: “hit within horizon” → Trading‑nah (Take Profit kann früher getroffen werden)

Im Code siehst du das konkret in:
- `6630eaa`: `max_adverse_move_pct` eingeführt (Label‑Pfad darf nicht zu stark gegen dich laufen)
- `7f85d93`: `hit_within_horizon` eingeführt (Schwelle reicht irgendwo im Horizont)

---

## 4) Features: Welche Eingaben nutzt das Modell?

### 4.1 price_only vs news+price

Im Final‑Workflow wird `feature_mode` meist so gesetzt:
- `price_only` für `hp*`‑Experimente
- `news+price` sonst

Dein Fokus‑Experiment ist `price_only`.

Warum price_only am Ende Sinn gemacht hat:
- News‑Features waren nicht stabil profitabler.
- Preisfeatures sind direkter, weniger “noisy” und konsistenter verfügbar.

### 4.2 Aktuelle Feature‑Liste (hp_long_final_yahoo)

Quelle: `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json` (`config.feature_cols`)

| Feature | Bedeutung | Rechenidee |
|---|---|---|
| `intraday_range_pct` | Tagesvola | `(High-Low)/Close` |
| `upper_shadow` | oberer Docht | `High - max(Open, Close)` |
| `lower_shadow` | unterer Docht | `min(Open, Close) - Low` |
| `price_close_ret_1d` | 1‑Tages Return | `pct_change(1)` |
| `price_close_ret_5d` | 5‑Tages Return | `pct_change(5)` |
| `price_range_pct_5d_std` | 5d Vola | `rolling std(5)` |
| `price_body_pct_5d_mean` | 5d Kerzen‑Body | `rolling mean(5)` |
| `price_close_ret_30d` | 30d Trend | `pct_change(30)` |
| `price_range_pct_30d_std` | 30d Vola | `rolling std(30)` |
| `price_body_pct_30d_mean` | 30d Body | `rolling mean(30)` |
| `month`, `quarter` | Saison | aus Datum |
| `cal_*` | Kalender‑Flags | aus Datum |
| `hol_*` | US‑Holiday‑Flags | aus `USFederalHolidayCalendar` |

Wo wird das berechnet?
- `src/data/build_training_set.py`: Merge, Targets, Basis‑Preisfeatures (Range, Shadows)
- `src/features/eurusd_features.py`: Rolling‑Returns/Std/Means + Kalender/Holidays

---

## 5) Datensatz‑Erstellung (wie kommen wir von Rohdaten zu `...training__EXP_ID.csv`?)

### 5.1 News‑Features (nur für news+price)
Wenn News aktiv sind:
- Roh‑News: `data/raw/news/eodhd_news*.jsonl`
- Tagesaggregation: `src/data/prepare_eodhd_news.py`
- Output: `data/processed/news/eodhd_daily_features.csv`

### 5.2 Label‑Datei (exp‑spezifisch)
Labels werden so archiviert, dass Experimente reproduzierbar bleiben:
- Standard: `data/processed/fx/eurusd_labels.csv`
- Experiment‑Variante: `data/processed/fx/eurusd_labels__<EXP_ID>.csv`

### 5.3 Trainingsdatensatz bauen
`src/data/build_training_set.py` hat zwei wichtige Pfade:
- `build_training_dataframe(exp_id=...)` (news+price)
- `build_price_only_training_dataframe_from_labels(exp_id=...)` (price_only)

Im price_only‑Fall werden News‑Spalten “stubbed”, damit die Feature‑Funktion trotzdem läuft (aber später werden News‑Features nicht in `feature_cols` aufgenommen).

---

## 6) Splits (Train/Val/Test) – warum so?

Wir splitten **zeitlich**, nicht zufällig:
- `test_start = 2025-01-01`
  - Test = alle Daten **ab** 2025‑01‑01 (Zukunft)
  - Pretest = alles **davor** (Vergangenheit)
- Pretest wird chronologisch in Train/Val geteilt, z.B. `80/20`

Warum?
- Random Split würde Zukunft/Verangenheit mischen → unrealistisch.
- Wir wollen “wie im echten Leben”: trainiere auf Vergangenheit, teste auf Zukunft.

Code/Logik:
- `split_train_val_test(...)` in `src/models/train_xgboost_two_stage.py`

---

## 7) Modelltraining (XGBoost) – wie funktioniert das genau?

### 7.1 XGBoost kurz (verständlich)
XGBoost trainiert viele kleine Entscheidungsbäume nacheinander.
Jeder neue Baum versucht, die Fehler der bisherigen Bäume zu reduzieren.

Für binäre Klassifikation:
- Output ist `P(y=1)` (Wahrscheinlichkeit)
- Du brauchst einen **Threshold**, um daraus `0/1` zu machen.

### 7.2 Stufe 1: Signal‑Modell
Target: `signal` (0 neutral, 1 move).

Im Final‑Notebook wird `scale_pos_weight` explizit berechnet:
`scale_pos_weight = n_neg / n_pos`

Warum das wichtig ist:
- Bei unbalancierten Klassen kann das Modell sonst “die Mehrheit” bevorzugen.

### 7.3 Stufe 2: Richtungs‑Modell
Target: `direction` (0 down, 1 up), nur für `signal==1`.

Hier wird `scale_pos_weight=1.0` gesetzt (down/up ist meist weniger extrem unbalanciert als neutral/move).

### 7.4 Modell‑Hyperparameter (aktueller Stand)
Quelle: `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json` (`model_params`)
- `objective=binary:logistic`
- `max_depth=3`
- `learning_rate=0.05`
- `subsample=0.9`
- `colsample_bytree=0.9`
- `early_stopping_rounds` wird in `train_xgb_binary` verwendet (je nach Version/Notebook)

---

## 8) Von Wahrscheinlichkeiten zu Trades: Threshold‑Logik (das ist der Kern!)

### 8.1 Warum 0.5 nicht genügt
0.5 ist ein Standard für Klassifikation, aber Trading ist anders:
- False Positives können teuer sein
- “Nicht handeln” ist oft besser als “unsicher handeln”

Darum:
- wir unterscheiden **Threshold für Metriken** vs **Threshold für Trading**.

### 8.2 Aktuelle Thresholds im Fokus‑Experiment
Quelle: `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json` (`config`)

**Metrik‑Thresholds:**
- `signal_threshold = 0.5`
- `direction_threshold = 0.42` (val‑basiert für F1_up)

**Trading‑Thresholds:**
- `signal_threshold_trade = 0.425`
- `direction_threshold_down = 0.3`
- `direction_threshold_up = 0.675`

Interpretation:
- Handeln nur, wenn `P(move) >= 0.425`
- Dann:
  - **up** nur wenn `P(up) >= 0.675`
  - **down** nur wenn `P(up) <= 0.3`
  - dazwischen: **neutral** (No‑Trade Zone)

### 8.3 Wie wurden Trading‑Thresholds “kostenbasiert” gewählt?
Im Final‑Notebook `notebooks/final_two_stage/2_train_final.ipynb` wird eine **vereinfachte Kostenfunktion** benutzt:
- korrekter Trade ≈ Gewinn `threshold * stake`
- falscher Trade oder Trade auf neutral ≈ Verlust `max_adverse_move_pct * stake` (Stop‑Loss Annahme)

Dann wird auf dem **Validation‑Split** über Threshold‑Gitter gesucht:
- welcher Threshold maximiert erwarteten P&L?

Das war ein bewusster Schritt, nachdem wir gesehen haben:
**beste F1 ≠ bester Profit**.

---

## 9) Trading‑Simulation im Report (wie “Gewinn” berechnet wird)

Wichtig: Die PDF‑Zahlen kommen nicht nur aus der vereinfachten Kostenfunktion.
Im Report wird eine **pfadbasierte** Simulation genutzt:
- Funktion: `_compute_trade_return(...)` in `scripts/generate_two_stage_report.py`

### 9.1 Trade Return (in %)
Für einen Tag `t` mit Prediction `up/down`:
- Einstieg: `Close_t`
- Betrachtung des Preis‑Segments `t..t+horizon`
- Logik:
  - Wenn Stop‑Level zuerst getroffen wird → Return = `-max_adverse_move_pct`
  - Wenn TP‑Level zuerst getroffen wird → Return = `+up_threshold` (für up) oder `-down_threshold` (für down)
  - sonst: Return am Horizontende (Fallback)

Bei `pred_label = neutral` wird Return = 0.
Bei `true_label = neutral`, aber wir handeln: konservativ Stop‑Loss.

### 9.2 Strategie A vs B

**Strategie A (fixer Einsatz):**
- Stake = 100 CHF pro Trade (up oder down)
- P&L pro Trade = `stake * trade_return`
- Hebel 20: P&L wird *20 skaliert

**Strategie B (10% Kapital):**
- Startkapital 1000 CHF
- Pro Trade wird 10% des aktuellen Kapitals “riskiert”:  
  `capital = capital * (1 + 0.10 * trade_return)`
- Hebel 20: `trade_return` wird *20 skaliert

---

## 10) Ergebnisse (Fokus‑Experiment)

Für `hp_long_final_yahoo` (Profit‑Simulation identisch zu `hp_long_h4_thr0p4pct_hit_1_2`):
- Testtage: 218
- Trades: 105

Strategie A:
- ohne Hebel: +24.76 CHF
- mit Hebel 20: +495.16 CHF

Strategie B:
- ohne Hebel: Endkapital 1025.05 CHF (≈ +25.05 CHF)
- mit Hebel 20: Endkapital 1632.89 CHF (≈ +632.89 CHF)

Kurzer Vergleich (nur um die Entscheidung “price_only” zu begründen):
- `final_yahoo` (news+price) liefert in der Simulation weniger P&L (z.B. Strategie B Hebel 20 ≈ +426.12 CHF) und mehr Trades (132) → mehr “schlechte” Trades.

---

## 11) Wie ist man vorgegangen? (Iterationen + Entscheidungslogik)

Du kannst dir den Prozess als Loop merken:
1) **Beobachten** (EDA/Label‑Verteilung/Fehlerbilder/Trades)  
2) **Hypothese** (z.B. “Labels sind zu streng”, “Threshold 0.5 ist nicht trading‑optimal”)  
3) **Experiment** (EXP_ID, Parameter ändern)  
4) **Messen** (Metriken + Profit‑Simulation)  
5) **Entscheiden** (beibehalten/verwerfen)

### 11.1 Meilensteine aus Git (mit Inhalt)
Diese Tabelle entspricht dem, was wir wirklich im Code/Notebooks geändert haben (aus `git show`):

| Datum | Commit | Inhalt (konkret) | Wirkung/Learning |
|---|---|---|---|
| 2025‑11‑15 | `c90fb09` | EXP_ID‑Notebooks + Label/Dataset‑Build mit Archiv‑Files | Experimente reproduzierbar |
| 2025‑11‑16 | `e26dde0` | PDF‑Report Generator eingeführt | Ergebnisse besser erklärbar |
| 2025‑11‑17 | `751dea1` | neue engineered Price‑Features | Modell bekommt “Signal” aus Preisen |
| 2025‑11‑18 | `6630eaa` | tolerant adverse move (`max_adverse_move_pct`) | Labels realistischer, mehr positives Signal |
| 2025‑11‑28 | `7f85d93` | `hit_within_horizon` + Trade‑Simulation + Kostenmatrizen | Trading‑Logik näher an Realität |
| 2025‑11‑30 | `b033083` | cost‑based Direction‑Trading‑Thresholds | No‑Trade Zone reduziert schlechte Trades |
| 2025‑11‑30 | `b851d53` | cost‑based `SIGNAL_THRESHOLD_TRADE` | Metrik‑Threshold getrennt vom Trading‑Threshold |
| 2025‑11‑30 | `f77ea1b` | hp_long price_only Baseline | News raus → Profit stabiler |
| 2025‑12‑12 | `46f1cea` | EODHD FX alternative + Vergleichstools | Datenquellen‑Risiko sichtbar |

Für die “Micro‑Timeline” einzelner Experimente siehe:
- `docs/two_stage_timeline.md`

---

## 12) Was wurde verworfen und warum?

### 12.1 Strikte Monotonie / Endpunkt‑Treffer als Hauptlabel
Problem:
- zu wenige up/down
- Modell lernt “fast alles neutral”
Entscheid:
- `strict_monotonic=False` + tolerant + hit‑within‑horizon

### 12.2 “Nur Metriken optimieren”
Problem:
- macro‑F1 kann steigen, Profit sinkt (weil falsche Trades teuer sind)
Entscheid:
- separate Trading‑Thresholds (signal_trade + direction_down/up)

### 12.3 News‑dominierter Ansatz
Problem:
- News sind noisy / schwer zeitlich exakt zuzuordnen
- nicht stabil profitabler in unseren Tests
Entscheid:
- price_only als “robuste Baseline” akzeptieren

### 12.4 EODHD Preisquelle (in ersten Tests)
Problem:
- Ergebnisse deutlich schlechter
Mögliche Gründe:
- Daten‑Mismatch (Zeitstempel, Missing Days)
- andere Kursqualität/Quelle
Entscheid:
- als Vergleich behalten, aber Fokus weiter Yahoo‑Labels

---

## 13) Typische Verständnisfragen (FAQ)

### 13.1 “Warum sehe ich manchmal flache Phasen im Gewinn?”
Weil an Tagen ohne Trade (`combined_pred='neutral'`) der P&L nicht steigt.
In Scatter‑Plots werden trotzdem Punkte pro Datum gezeichnet (kein Trade ≙ gleicher P&L wie Vortag).

### 13.2 “Warum ist der ‘Zinseszins’ nicht perfekt exponentiell?”
Weil:
- nur 10% Kapital pro Trade wirken
- Trades nicht jeden Tag passieren
- Verluste die Kurve wieder abflachen
- Zeitraum ist relativ kurz

---

## 14) Reproduzierbarkeit (konkrete Schritte)

### 14.1 Final‑Workflow (empfohlen)
1) Data Prep: `notebooks/final_two_stage/1_data_prep_final.ipynb`
2) Training: `notebooks/final_two_stage/2_train_final.ipynb`
3) Eval: `notebooks/final_two_stage/3_eval_final.ipynb`
4) PDF:
```bash
python3 -m scripts.generate_two_stage_report --exp-id hp_long_final_yahoo
```

### 14.2 Welche Outputs entstehen pro Experiment?
- `data/processed/experiments/<EXP_ID>_config.json`
- `data/processed/fx/eurusd_labels__<EXP_ID>.csv`
- `data/processed/datasets/eurusd_news_training__<EXP_ID>.csv`
- `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>.json`
- `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_metrics.csv`
- `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_predictions.csv`
- optional: `..._report.pdf`

---

## 15) Grenzen / Risiken (wichtig, wenn du Fragen bekommst)

Das ist eine **Lern‑ und Projektpipeline**, kein fertiges Echtgeld‑System.
Fehlende Realismus‑Punkte:
- Spread/Slippage/Transaktionskosten
- Order‑Ausführung (Fill‑Risk)
- Regime‑Change (Marktverhalten kann kippen)
- Overfitting‑Gefahr bei sehr vielen Experimenten

---

## 16) Nächste sinnvolle Schritte (wenn du weiter machen willst)

- Walk‑Forward Validation (Rolling Window)
- Probability Calibration vor Threshold‑Optimierung
- Risiko‑Metriken (Drawdown, Sharpe)
- Baseline‑Vergleich: “always neutral”, “simple momentum” etc.
- Ablation‑Study: welche 3–5 Features reichen?

---

## 17) Verwandte Dokumente im Repo

- Pipeline‑Doku: `docs/data_pipeline_eurusd_xgboost.md`
- Sehr ausführliche “Landkarte”: `docs/README_data_pipeline.md`
- Experiment‑Timeline: `docs/two_stage_timeline.md`
- Präsentations‑Kurzreport: `docs/presentation_report_hp_long_final_yahoo.md`

