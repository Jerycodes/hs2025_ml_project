# Bericht (für dich): Projektstand + Vorgehen + Ergebnisse  
**Projekt:** EURUSD – Zwei‑Stufen‑XGBoost (Signal + Richtung) mit Backtest/Tradesimulation  
**Fokus‑Experiment (aktueller Stand):** `hp_long_final_yahoo` (identisch zu `hp_long_h4_thr0p4pct_hit_1_2` in Profit‑Simulation)

> Ziel dieses Dokuments: Du sollst **verstehen**, was gebaut wurde, **warum** wir es so gemacht haben, **wie** es technisch umgesetzt ist, und wie du daraus eine Präsentation ableiten kannst.

---

## 0) Kurzfazit: Was du erreicht hast (in 30 Sekunden erklärbar)

Du hast eine **reproduzierbare Experiment‑Pipeline** gebaut, mit der du:
- EURUSD‑Labels **parametrierbar** erzeugst (Horizon/Thresholds/Stop‑Filter/Hit‑Logik),
- einen **Zwei‑Stufen‑XGBoost** trainierst (Signal + Richtung),
- **Trading‑Entscheidungen** aus Modell‑Wahrscheinlichkeiten ableitest (inkl. kostenbasierter Threshold‑Optimierung),
- Ergebnisse automatisch als **PDF‑Report** inklusive Profit‑Simulation visualisierst.

Und du hast dich nach vielen Iterationen auf ein **robustes, profitables Setup** festgelegt:
- **Fokus‑Resultat:** `hp_long_final_yahoo` (price_only)  
  - Strategie A (fixer Einsatz): ca. **+24.76 CHF** (ohne Hebel) / **+495.16 CHF** (Hebel 20)  
  - Strategie B (10% Kapital): ca. **+25.05 CHF** (ohne Hebel) / **+632.89 CHF** (Hebel 20)

> Wichtig für die Präsentation: Du zeigst **kurz** den Vergleich zu News‑Varianten, erklärst dann, warum du dich bewusst auf `hp_long_final_yahoo` festgelegt hast.

---

## 1) Worum geht es (Problem, Ziel, Idee)

Wir wollen aus täglichen EURUSD‑Daten ein Modell bauen, das uns **Trade‑Signale** liefert:

- **Wann lohnt sich ein Trade?** (Signal: *Bewegung* vs. *neutral*)  
- **In welche Richtung?** (Richtung: *up* vs. *down*)  

Warum “Zwei‑Stufen”?
- Das ist eine praktische Strategie bei **unbalancierten Klassen**: “neutral” ist oft sehr häufig, “up/down” seltener.  
- Stufe 1 filtert: *Gibt es überhaupt eine relevante Bewegung?*  
- Stufe 2 entscheidet nur auf diesen “Bewegungs‑Tagen”: *up oder down?*

Wichtig: Das ist **kein** echtes Trading‑System mit Live‑Broker, Slippage, Spread, etc. Wir machen eine **vereinfachte Tradesimulation** (Backtest‑ähnlich), um zu verstehen, ob die Signale *prinzipiell* profitabel sein könnten.

---

## 2) Grundbegriffe (einfach erklärt)

### 2.1 Numpy / Pandas (warum wir das brauchen)
- **NumPy** (`numpy`) ist eine Bibliothek für schnelle Rechenoperationen auf Arrays (Vektoren/Matritzen).  
  Beispiel: Wenn wir für jeden Tag `t` die nächsten 4 Tage ansehen, ist das eine typische Array‑Berechnung.
- **Pandas** (`pandas`) ist für Tabellen (DataFrames).  
  Wir nutzen Pandas, weil unsere Daten natürlich tabellarisch sind: eine Zeile = ein Tag, Spalten = Features/Labels.

### 2.2 Features vs. Labels
- **Feature** = Eingabe für das Modell, z.B. Volatilität, Returns, Kalender‑Infos.  
- **Label** = das “richtige Ergebnis”, das das Modell lernen soll, z.B. `up/down/neutral`.

### 2.3 Warum XGBoost?
- **XGBoost** ist ein sehr starkes Modell für tabellarische Daten.  
- Es basiert auf **Gradient Boosted Decision Trees**: viele kleine Entscheidungsbäume werden nacheinander trainiert und korrigieren die Fehler der vorherigen.
- Vorteile: funktioniert gut ohne extrem viel Feature‑Scaling, kann Nichtlinearitäten abbilden, ist robust und schnell.

### 2.4 Glossar (Abkürzungen, die bei uns überall vorkommen)

**Label‑Notation**
- `h4/h5/h6`: Horizont in Tagen (`horizon_days`).
- `thr0p4pct`: 0.4% Schwelle (`0p4 = 0.004`).  
- `strict`: `strict_monotonic=True` (Pfad muss streng steigen/fallen).
- `tolerant / tol0p3pct`: `max_adverse_move_pct` gesetzt (z.B. 0.3% = 0.003).
- `hit`: `hit_within_horizon=True` (Schwelle reicht, wenn sie irgendwann im Horizont erreicht wird).

**Experiment‑Serien (aus `docs/two_stage_timeline.md`)**
- `v*`: frühe Baselines (striktere Label‑Definitionen / klassische Schwellen).
- `nv*`: viele Varianten zur Label/Threshold‑Suche (größerer Parameter‑Sweep).
- `hv*`: “hit within horizon”‑Serie (Take‑Profit‑Logik im Labeling).
- `hp*`: price‑only Baselines (News weggelassen).
- `*_eod*`: Preisquelle EODHD statt Yahoo (`price_source='eodhd'`).

**Trading‑Thresholds**
- `SIGNAL_THRESHOLD`: Stufe 1 Threshold für Metriken (oft 0.5).
- `SIGNAL_THRESHOLD_TRADE`: Stufe 1 Threshold speziell fürs Trading (kostenbasiert).
- `DIRECTION_THRESHOLD`: Stufe 2 Threshold für Metriken (val‑basiert).
- `DIRECTION_THRESHOLD_DOWN/UP`: Stufe 2 Trading‑Grenzen mit “No‑Trade‑Zone”.

### 2.5 Tools, Installation, Requirements (so läuft es bei dir)

**Du brauchst:**
- Python 3.x
- ein virtuelles Environment (`.venv`)
- Jupyter/VS Code für die Notebooks
- Git (für Historie/Commits)

**Python‑Pakete** (Auszug, Quelle: `requirements.txt`):
- `numpy`, `pandas` (Daten)
- `xgboost`, `scikit-learn` (Modelle/Metriken)
- `matplotlib`, `seaborn` (Plots)
- `yfinance` (Yahoo‑Daten), `eodhd` (EODHD API)

**Setup (typisch):**
```bash
cd hs2025_ml_project/hs2025_ml_project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Wichtige Hinweise:**
- Wenn du EODHD‑News/Fx neu laden willst, brauchst du einen API‑Key (meist als Env‑Var `EODHD_TOKEN`).  
- Für reine Reproduktion der bereits gespeicherten Experimente brauchst du oft **keinen** neuen Download.

**Wo ist die offizielle Pipeline‑Beschreibung?**
- `docs/data_pipeline_eurusd_xgboost.md` (sehr ausführlich, Schritt‑für‑Schritt)
- `docs/README_data_pipeline.md` (noch ausführlicher, “Landkarte”)

---

## 3) Daten & Ordnerstruktur (was liegt wo)

### 3.1 Wichtige Ordner
- `data/raw/`  
  Rohdaten (FX‑Preise und News). Wird grundsätzlich **nicht** überschrieben.
- `data/processed/`  
  Verarbeitete Daten: Labels, Tages‑Features, fertige Trainings‑Datasets, Experiment‑Configs.
- `src/`  
  Python‑Code (Datenaufbereitung, Features, Modelle).
- `notebooks/`  
  Experimente/Workflows (Data‑Prep, Training, Evaluation).
- `notebooks/results/`  
  Ergebnisse (JSON + CSV + PDFs).  

### 3.2 Wichtige Dateien für **dieses Experiment**
(Diese Paths sind “die Wahrheit” für deinen aktuellen Stand.)

- Label‑Definition (Parameter/Setup): `data/processed/experiments/hp_long_final_yahoo_config.json`  
- Labels (pro Tag): `data/processed/fx/eurusd_labels__hp_long_final_yahoo.csv`  
- Trainingsdatensatz: `data/processed/datasets/eurusd_news_training__hp_long_final_yahoo.csv`  
- Final‑Ergebnis (JSON): `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json`  
- Final‑Metriken (CSV): `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_metrics.csv`  
- Final‑Predictions (CSV): `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_predictions.csv`  
- Report (PDF): wird mit `scripts/generate_two_stage_report.py` erzeugt (bei dir existiert z.B. `..._report.pdf`)

### 3.3 Wie du ein Experiment “richtig” wiederholst (Kurz‑Workflow)

**Option A (empfohlen): über die Final‑Notebooks**
1. `notebooks/final_two_stage/1_data_prep_final.ipynb`  
   - setzt `EXP_ID` und Label‑Parameter  
   - schreibt Labels + Dataset + Experiment‑Config
2. `notebooks/final_two_stage/2_train_final.ipynb`  
   - trainiert Signal + Richtung  
   - sucht Trading‑Thresholds (kostenbasiert, Val)  
   - schreibt JSON + Metrics CSV + Predictions CSV
3. `notebooks/final_two_stage/3_eval_final.ipynb`  
   - lädt Resultate, macht Vergleichsplots/Checks
4. PDF generieren:
   ```bash
   python3 -m scripts.generate_two_stage_report --exp-id hp_long_final_yahoo
   ```

**Option B: “alte” Notebooks (historisch)**
- `notebooks/1_data_prep_xgboost_two_stage.ipynb`, `2_train_xgboost_two_stage.ipynb`, `3_results_xgboost_two_stage.ipynb`  
  (Diese sind eher für die frühen Serien `v/nv` relevant.)

---

## 4) Label‑Definition (sehr wichtig, weil sie alles beeinflusst)

Die Labels entstehen aus EURUSD‑Preisen. Zentral ist: **Horizont** und **Schwellen**.

### 4.1 Die Parameter (aktueller Stand)
Aus `data/processed/experiments/hp_long_final_yahoo_config.json`:
- `horizon_days = 4`  
  Wir schauen von Tag `t` bis Tag `t+4`.
- `up_threshold = +0.004` (= +0.4%)  
- `down_threshold = -0.004` (= −0.4%)
- `strict_monotonic = False`  
  Wir verlangen **nicht**: “jeden Tag streng hoch/runter”.
- `max_adverse_move_pct = 0.01` (= 1%)  
  “Tolerant”: Ein Up‑Move darf unterwegs maximal 1% gegen dich laufen (Stop‑ähnlich).
- `hit_within_horizon = True`  
  Up/Down gilt schon, wenn die Schwelle **irgendwo innerhalb** der 4 Tage erreicht wird (Take‑Profit‑Logik).

### 4.2 Was bedeutet das als Regel?
Im Code `src/data/label_eurusd.py` passiert im Kern:

Für jeden Starttag `t` betrachten wir das Segment `Close[t], Close[t+1], ..., Close[t+4]`.

- “Up‑Hit”:  
  `max(segment) >= Close[t] * (1 + up_threshold)`  
  und gleichzeitig darf der Kurs nicht zu stark gegen dich laufen (Adverse‑Move Filter).
- “Down‑Hit”:  
  `min(segment) <= Close[t] * (1 + down_threshold)`  
  plus Adverse‑Move Filter.
- Sonst: `neutral`.

### 4.3 Warum haben wir die Label‑Logik verändert (historisch)?
Am Anfang war es “streng” (Monotonie und Endpunkt‑Treffer). Das führt oft zu:
- sehr wenigen up/down Labels  
- starkem Klassen‑Ungleichgewicht  
- Modell lernt “meist neutral”  

Dann kamen “tolerant” und später “hit_within_horizon”, weil:
- reale Kurse bewegen sich oft **mit Rücksetzern**  
- Take‑Profit wird oft **irgendwann** erreicht, nicht exakt am Endtag  

Diese Änderungen siehst du auch in den Commits:
- **Tolerant (Adverse‑Move Filter):** `6630eaa` (2025‑11‑18)  
- **Hit‑within‑horizon:** `7f85d93` (2025‑11‑28)  

---

## 5) Modell‑Architektur (Zwei‑Stufen)

### 5.1 Stufe 1: Signal‑Modell (neutral vs. move)
Ziel: Vorhersagen, ob ein Tag eine “relevante Bewegung” hat.
- Target: `signal = 1`, wenn Label `up` oder `down` ist; sonst `0`.
- Output: Wahrscheinlichkeit `P(move)`.

### 5.2 Stufe 2: Richtungs‑Modell (down vs. up)
Ziel: Nur auf Tagen mit Bewegung (oder wenn wir handeln wollen) Richtung entscheiden.
- Target: `direction = 1` für `up`, `0` für `down`.
- Output: Wahrscheinlichkeit `P(up)`.

### 5.3 Warum 2 Stufen statt 1 Modell mit 3 Klassen?
Weil die 3‑Klassen‑Variante oft schwerer stabil zu bekommen ist:
- “neutral” dominiert häufig,
- “up” und “down” sind relativ selten und schwer zu trennen,
- die Modell‑Wahrscheinlichkeiten sind besser interpretierbar, wenn man zuerst “Trade ja/nein” trennt.

---

## 6) Features (welche Eingaben nutzt das Modell?)

### 6.1 Feature‑Mode
Im Final‑Workflow unterscheiden wir grob:

- `news+price`: Preis‑Features + News/Sentiment‑Features  
- `price_only`: nur Preis‑/Kalender‑/Holiday‑Features (keine News)

Für das Fokus‑Experiment ist es **`price_only`**. Das war eine bewusste Entscheidung, weil wir in der Praxis gesehen haben:
- News‑Features haben die Metriken teilweise verbessert, aber **nicht stabil** den Profit (Backtest) erhöht.  
- Preis‑Features sind “direkter” und robuster für kurzfristige Bewegungen im EURUSD.

### 6.2 Aktuelle Feature‑Liste (21 Features)
Quelle: `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json` (`config.feature_cols`)

| Feature | Was es bedeutet (einfach) | Wie es berechnet wird (Formel/Idee) |
|---|---|---|
| `intraday_range_pct` | Tagesvolatilität | `(High - Low) / Close` |
| `upper_shadow` | oberer Docht | `High - max(Open, Close)` |
| `lower_shadow` | unterer Docht | `min(Open, Close) - Low` |
| `price_close_ret_1d` | 1‑Tages‑Return | `Close_t / Close_{t-1} - 1` |
| `price_close_ret_5d` | 5‑Tages‑Return | `Close_t / Close_{t-5} - 1` |
| `price_range_pct_5d_std` | Volatilität (5d) | `std(intraday_range_pct, window=5)` |
| `price_body_pct_5d_mean` | Kerzenkörper‑Ø (5d) | `mean(body_pct, window=5)` |
| `price_close_ret_30d` | 30‑Tages‑Return | `Close_t / Close_{t-30} - 1` |
| `price_range_pct_30d_std` | Volatilität (30d) | `std(intraday_range_pct, window=30)` |
| `price_body_pct_30d_mean` | Kerzenkörper‑Ø (30d) | `mean(body_pct, window=30)` |
| `month` | Monat (Saisonalität) | `date.month` |
| `quarter` | Quartal | `date.quarter` |
| `cal_dow` | Wochentag | `date.dayofweek` (Mo=0…So=6) |
| `cal_day_of_month` | Tag im Monat | `date.day` |
| `cal_is_monday` | Montag‑Flag | `1 wenn dow==0 sonst 0` |
| `cal_is_friday` | Freitag‑Flag | `1 wenn dow==4 sonst 0` |
| `cal_is_month_start` | Monatsanfang | `date.is_month_start` |
| `cal_is_month_end` | Monatsende | `date.is_month_end` |
| `hol_is_us_federal_holiday` | US‑Feiertag | Flag aus `pandas` Holiday‑Calendar |
| `hol_is_day_before_us_federal_holiday` | Tag vor US‑Feiertag | `date+1 ist Feiertag?` |
| `hol_is_day_after_us_federal_holiday` | Tag nach US‑Feiertag | `date-1 ist Feiertag?` |

Wo wird das berechnet?
- Merge + Basis‑Spalten: `src/data/build_training_set.py`
- Ableitungen / Rolling‑Features / Kalender / Holidays: `src/features/eurusd_features.py`

### 6.3 Was ist mit News‑Features?
News‑Features existieren weiterhin (z.B. `article_count`, `avg_polarity`, `news_article_count_7d_sum`, …).  
Sie werden verwendet, wenn `feature_mode='news+price'` (z.B. `final_yahoo` oder `hv_long_final_yahoo`).

---

## 7) Modell‑Parameter (aktueller Stand) – und was sie bedeuten

Quelle: `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json` (`model_params`)

### 7.1 Gemeinsame Parameter‑Idee
- `objective = binary:logistic`  
  -> binäre Klassifikation liefert Wahrscheinlichkeit 0..1.
- `max_depth = 3`  
  -> Baumtiefe (Komplexität). Tiefer = komplexer, aber riskanter (Overfitting).
- `learning_rate = 0.05`  
  -> wie stark jede neue Baum‑“Korrektur” ist.
- `subsample = 0.9`, `colsample_bytree = 0.9`  
  -> leichte Randomisierung, hilft gegen Overfitting.

### 7.2 `scale_pos_weight` (wichtig wegen Klassenverteilung)
- Signal‑Modell: `scale_pos_weight = 0.152...`
- Richtungs‑Modell: `scale_pos_weight = 1.0`

Was bedeutet das?
- `scale_pos_weight` gewichtet die positive Klasse im Training.  
- Durch unsere Label‑Definition (`hit_within_horizon=True`) gibt es relativ viele `move`‑Tage; dadurch kann `n_neg/n_pos` < 1 sein.  
- Effekt: Das Training kann das Signal‑Modell so “kalibrieren”, dass es weniger/längst nicht jede Kleinbewegung als Trade interpretiert.

Wo wird das gesetzt?
- im Final‑Training Notebook: `notebooks/final_two_stage/2_train_final.ipynb` (Berechnung `n_neg/n_pos`)

---

## 8) Entscheidungsgrenzen / Thresholds (wie wird aus Wahrscheinlichkeit ein Trade?)

Hier liegt ein Kern‑Learning:  
**Ein Threshold für “Metrik” ist nicht automatisch optimal für “Trading”.**

Quelle: `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo.json` (`config`)

### 8.1 Thresholds für Metriken (klassische Auswertung)
- `SIGNAL_THRESHOLD = 0.5`  
  -> ab `P(move) >= 0.5` wird “move” gezählt (für Precision/Recall/F1).
- `DIRECTION_THRESHOLD = 0.42`  
  -> ab `P(up) >= 0.42` wird “up” gezählt (sonst “down”) – für Metriken.

### 8.2 Thresholds für Trading (kostenbasiert optimiert)
- `SIGNAL_THRESHOLD_TRADE = 0.425`  
  -> ab `P(move) >= 0.425` **darf** gehandelt werden.
- `DIRECTION_THRESHOLD_DOWN = 0.3` und `DIRECTION_THRESHOLD_UP = 0.675`  
  -> “down”, wenn `P(up) <= 0.3`; “up”, wenn `P(up) >= 0.675`.  
  Alles dazwischen wird **neutral** (kein Trade), obwohl Signal evtl. “move” sagt.

Warum zwei Direction‑Grenzen?
- Wir bauen eine “No‑Trade Zone” zwischen 0.3 und 0.675, um nur bei hoher Sicherheit zu handeln.

Woher kommen diese Werte?
- Im Final‑Training Notebook `notebooks/final_two_stage/2_train_final.ipynb` wird eine vereinfachte **Kosten-/Gewinnfunktion** definiert (ungefähr: Take‑Profit bringt `threshold*stake`, Stop‑Loss kostet `max_adverse_move_pct*stake`).  
- Dann werden auf dem **Val‑Split** Thresholds gesucht, die den erwarteten P&L maximieren (Commit‑Meilenstein: `b033083` und `b851d53`).

---

## 9) Evaluation: Was messen wir?

Wir machen zwei Arten von “Erfolg”:

### 9.1 Klassische ML‑Metriken
Für jede Stufe:
- Confusion Matrix
- Precision / Recall / F1 (pro Klasse)

Zusätzlich kombiniert (3 Klassen `neutral/up/down`):
- Confusion Matrix 3x3
- macro‑F1 (wichtig, weil Klassen nicht gleich häufig sind)

### 9.2 Trading‑Metriken (Backtest‑ähnlich)
Im PDF‑Report simulieren wir Trades mit 2 Strategien:

- **Strategie A (fixer Einsatz)**  
  Pro Trade werden 100 CHF eingesetzt.
- **Strategie B (10% Kapital)**  
  Pro Trade wird 10% des aktuellen Kapitals eingesetzt (Zinseszins‑Effekt möglich).
- **Hebel 20 (optional)**  
  Die Trade‑Returns werden mit 20 multipliziert (nur Modell‑Simulation, kein echtes Risiko‑Modell).

Wichtig: Der Report nutzt eine Trade‑Return‑Simulation `_compute_trade_return(...)` in `scripts/generate_two_stage_report.py`, die:
- Take‑Profit bei Erreichen von `up_threshold/down_threshold`  
- Stop‑Loss bei `max_adverse_move_pct`  
- (sonst) Return am Horizontende  
berücksichtigt (auf Basis des tatsächlichen Preisverlaufs im Horizont).

---

## 10) Resultate (konkret, aktueller Stand)

Für `hp_long_final_yahoo` (und identisch `hp_long_h4_thr0p4pct_hit_1_2`) ergeben sich aus den gespeicherten Predictions:

- Testtage: `218`
- Trades: `105` (Tage, an denen `combined_pred` nicht neutral ist)

**Strategie A (fixer Einsatz)**
- ohne Hebel: ca. **+24.76 CHF**
- mit Hebel 20: ca. **+495.16 CHF**

**Strategie B (10% Kapital)**
- ohne Hebel: Endkapital ca. **1025.05 CHF** (= **+25.05 CHF**)  
- mit Hebel 20: Endkapital ca. **1632.89 CHF** (= **+632.89 CHF**)  

Interpretation:
- Ohne Hebel ist der Effekt klein (weil pro Trade nur 10% Kapital “wirkt”).  
- Mit Hebel 20 sieht man den Unterschied deutlich; das ist aber auch **sehr riskant** in der Realität.

### 10.1 Kurzvergleich (nur 1 Folie in der Präsentation)
Du willst den Vergleich nur kurz zeigen – dafür reicht eine einfache Aussage:

- `final_yahoo` (news+price) hat in unserer Simulation **weniger P&L** als `hp_long_final_yahoo` (price_only), obwohl die ML‑Metriken nicht zwingend schlechter sein müssen.

Konkreter (aus den gespeicherten Predictions, gleiche Testperiode):
- `hp_long_final_yahoo`: Trades `105`, Strategie B Hebel 20: **+632.89 CHF**
- `final_yahoo`: Trades `132`, Strategie B Hebel 20: **+426.12 CHF**

Interpretation:
- News kann helfen, aber bei Trading zählt nicht nur “Trefferquote” – es zählt **welche Fehler** passieren und wie viele “schlechte Trades” durchkommen.  
- Darum war `price_only` für dich die bessere, robustere Basis.

---

## 11) Wie es dazu gekommen ist (chronologisches Vorgehen mit Commit‑Inhalten)

Diese Timeline ist bewusst “Erzähl‑fähig”: **Beobachtung → Änderung → Warum**.

> Detail‑Timeline aller Experimente: `docs/two_stage_timeline.md` (auto‑generiert).

### 11.1 Timeline (Meilensteine aus Git)

| Datum | Commit | Was wurde gemacht (Inhalt, nicht nur Message) | Warum / Learning |
|---|---|---|---|
| 2025‑11‑15 | `c90fb09` | EXP_ID‑basierte Notebooks (Data‑Prep/Train/Results), Labeling + Training‑Set‑Build integriert. | Grundlage für reproduzierbare Experimente. |
| 2025‑11‑15 | `8842c8a` | Pipeline‑Doku + erstes v1‑Experiment, Training/Result‑Outputs als JSON/CSV. | “Landkarte” des Projekts + erste Baseline. |
| 2025‑11‑16 | `e26dde0` | PDF‑Report Generator `scripts/generate_two_stage_report.py` + v1 PDF. | Ergebnisse besser kommunizieren (Plots, Tabellen). |
| 2025‑11‑17 | `751dea1` | Neue engineered Preis‑Features + Erweiterung Training‑Set + Updates im Two‑Stage Training Code. | Features verbessern, nicht nur Roh‑News. |
| 2025‑11‑18 | `6630eaa` | Label‑Logik “tolerant”: `max_adverse_move_pct` (Stop‑ähnlicher Filter) ergänzt. | Strikte Labels waren zu unrealistisch/selten. |
| 2025‑11‑18 | `08bb245` | EDA‑Notebook: Label Coverage/Path‑Analyse. | Beweisen/sehen, warum Labels zu selten sind. |
| 2025‑11‑18 | `256f8e3` | v4/v5 tolerant Experimente + Anpassungen in Notebooks/Labels. | Systematisches Tuning der Label‑Parameter. |
| 2025‑11‑19 | `79ab367` | v6–v8 Varianten: Signal‑Modell‑Tuning (Depth, scale_pos_weight, etc.). | Fehlalarme reduzieren / Stabilität erhöhen. |
| 2025‑11‑19 | `db8fb32` | Up‑only / Down‑only Notebooks + `tune_xgboost_thresholds.py` (Threshold‑Kurven, FN/FP‑Vis). | Thresholds bewusst wählen statt “0.5 immer”. |
| 2025‑11‑21 | `dd75efb` | Start Final‑Workflow‑Notebooks `notebooks/final_two_stage/*`. | Stabiler Standard‑Ablauf (data/train/eval). |
| 2025‑11‑22 | `859a5a1` | Final‑PDF‑Reporting, viele Final‑Runs (v/nv) mit Predictions CSVs. | Reproduzierbare Reports & Vergleichbarkeit. |
| 2025‑11‑28 | `7f85d93` | Trade‑Simulation + Kostenmatrizen + hv‑Serie; Labeling: `hit_within_horizon`. | Trading‑Realismus: TP/SL‑Logik, nicht nur Endpunkt. |
| 2025‑11‑30 | `b033083` | Kostenbasierte Direction‑Trading‑Thresholds (`down/up`) + hv5 Resultate. | “No‑Trade‑Zone” für bessere Trade‑Qualität. |
| 2025‑11‑30 | `b851d53` | `SIGNAL_THRESHOLD_TRADE` kostenbasiert; hp_long Runs + Split‑Plot im Report. | Separater Threshold für Trading vs Metriken. |
| 2025‑11‑30 | `f77ea1b` | hp_long “price_only baseline” + weitere Runs (Feature‑Cleanups). | News weglassen → Profit stabiler. |
| 2025‑12‑12 | `46f1cea` | EODHD FX Pipeline + Vergleich Yahoo vs EODHD; Labeling: `price_source`. | Datenquellen vergleichen (Qualität/Abweichungen). |
| 2025‑12‑12 | `265f8af` | Aktualisierte Label‑Snapshots. | Konsistente Labels/Versionierung. |

### 11.2 Was wurde verworfen/relativiert?
- **Strikt monotone Pfade (`strict_monotonic=True`)**: zu wenige Labels, unrealistisch.  
- **Nur Metriken optimieren**: führte nicht automatisch zu Profit (Trading braucht andere Schwellen).  
- **News‑Features als Haupttreiber**: in unseren Tests nicht stabil profitabler als price_only.  
- **EODHD‑Preisquelle**: wurde getestet; Ergebnisse waren (zumindest in den ersten Runs) deutlich schlechter → wahrscheinlich Daten‑Mismatch/Qualität/Synchronisation.

---

## 12) Schwierigkeiten & Learnings (für den Vortrag extrem gut)

### 12.1 Label‑Definition ist “das eigentliche Modell”
Wenn du `hit_within_horizon`, Schwelle, Stop‑Filter änderst, änderst du:
- wie oft `up/down` vorkommt (Klassenverteilung),
- was “richtig” bedeutet,
- wie schwer die Klassifikation ist,
- wie viele Trades es gibt.

### 12.2 Metriken vs. Profit (zwei unterschiedliche Ziele)
- Ein Modell kann macro‑F1 verbessern, aber Profit verschlechtern (z.B. mehr Trades, mehr False Positives).  
- Darum: **separate Trading‑Thresholds** (Signal‑Trade + Direction‑Down/Up).

### 12.3 Warum wächst Strategie B nicht “perfekt exponentiell”?
Zinseszins ist möglich, aber:
- du setzt nur **10%** ein (nicht 100%),
- es gibt **Verlust‑Trades** und **Tage ohne Trades**,
- in ~1 Jahr sieht “exponentiell” oft noch “fast linear” aus.

---

## 13) Vorschlag für deine Präsentation (10–15 Minuten)

Deine Idee ist gut. Ein möglicher Ablauf:

1. **Einführung (1–2 min)**  
   Ziel, Problem, warum EURUSD/Labels/2‑Stufen.
2. **Vorgehen (5–6 min, Hauptteil)**  
   Story als Iterations‑Loop: *Beobachten → Hypothese → Experiment → Messen → Entscheiden*.  
   Phasen: `strict` → `tolerant` → `hit` → Threshold‑Tuning → Trading‑Simulation → price_only.
3. **Resultate (2–3 min)**  
   **1 Folie Vergleich** (News vs price_only), dann Fokus: `hp_long_final_yahoo` (P&L/Kapital/Trades pro Monat/Gewinn pro Trade).
4. **Herausforderungen (2–3 min)**  
   Labeling, Klassenverteilung, Metriken vs Profit, “Trading ≠ Klassifikation”.
5. **Ausblick (1–2 min)**  
   Realismus‑Schritte: Kosten/Slippage, Walk‑Forward, Risiko‑Metriken.

---

## 14) Ausblick / Next Steps (wenn du gefragt wirst)

Realistische Verbesserungen:
- Transaktionskosten/Spread/Slippage im Backtest einbauen.  
- Walk‑forward Validation (rollierende Zeitfenster).  
- Probability‑Calibration (z.B. Platt/Isotonic) vor Threshold‑Optimierung.  
- Risiko‑Metriken: Max Drawdown, Sharpe, Var.  
- Feature‑Ablationen: welche price_features wirklich helfen?  

---

## 15) Fragen an dich (damit ich es perfekt zuschneiden kann)

1) Willst du in der Präsentation **nur** `hp_long_final_yahoo` zeigen, oder auch kurz “News‑Experiment vs Price‑only” als Vergleich?  
2) Soll der Fokus eher auf **ML‑Teil** (Labels/Features/Modelle) oder **Trading‑Teil** (Profit/Strategien/Backtest) liegen?
