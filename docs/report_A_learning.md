# Bericht A (Lernbericht) – hs2025_ml_project

Ziel dieses Dokuments ist, dass du nach dem Lesen **wirklich verstehst**, wie das Projekt aufgebaut ist und wie du es reproduzieren kannst.

Wichtig: Das Repo ist sehr groß (viele Notebooks + viele Ergebnis-Artefakte). Ich habe deshalb **die Kernmodule und Kern-Notebooks vollständig gelesen** und die restlichen Dateien **strukturell** analysiert (Pfad, Zweck, Muster, Dateitypen). Für “jede einzelne Datei” wörtlich Zeile für Zeile fehlt praktisch der Nutzen, weil sehr viele Dateien automatisch erzeugte Resultate sind.

---

## 1) Projekt in einfachen Worten

Du willst aus historischen EURUSD-Daten ein Handelssignal erzeugen.

Das Problem ist, dass “neutral” (keine klare Bewegung) sehr oft ist. Ein direktes 3‑Klassen‑Modell (neutral/up/down) kippt dann leicht in “immer neutral”.

Darum nutzt das Projekt ein **Zwei‑Stufen‑Modell**:

- **Stufe 1 (Signal):** “neutral” vs. “move” (es lohnt sich überhaupt zu handeln?)
- **Stufe 2 (Richtung):** nur wenn “move”: “down” vs. “up”

Dann wird daraus eine kombinierte Entscheidung gebaut: `{neutral, up, down}`.

Zusätzlich gibt es eine **Tradesimulation**, damit du nicht nur ML‑Metriken siehst, sondern auch “Wie hätte es im Trading ausgesehen?”.

Zusätzlich gibt es **symbolische KI** (regelbasierte Fuzzy-Logik): Sie nimmt Modell‑Wahrscheinlichkeiten + Risiko‑Inputs (Volatilität, offene Trades, Equity) und gibt einen Risk‑Faktor aus. Damit wird ein Einsatz berechnet (Strategie C).

---

## 2) Repo‑Landkarte (Ordnerstruktur)

### 2.1 Top‑Level

- `src/`  
  Python‑Code (Daten, Features, Modelle, Risk).
- `scripts/`  
  CLI‑Skripte (Report erzeugen, Experimente laufen lassen, Daten importieren).
- `notebooks/`  
  Jupyter‑Workflows (Data‑Prep, Training, Evaluation, Experimente).
- `rules/`  
  Fuzzy‑Regeln (symbolisch), z.B. `risk.flex` und optional `risk.ksl`.
- `docs/`  
  Dokumentation + Timelines + vorhandene Berichte.
- `data/`  
  Rohdaten und verarbeitete Daten.

### 2.2 Wichtiger Git‑Hinweis (sehr wichtig für Reproduzierbarkeit)

In `.gitignore` steht:

- `data/raw/` ist **nicht versioniert**.
- `data/processed/*` ist fast komplett **nicht versioniert** (Ausnahme: `data/processed/fx/eurusd_labels.csv`).

Das heißt: Wenn du jemandem das Repo gibst, fehlen die Rohdaten. Reproduzierbarkeit ist nur dann gegeben, wenn du erklärst:

- wie man Rohdaten beschafft (Yahoo / EODHD / MT5),
- welche Dateien am Ende vorhanden sein müssen,
- welche Notebooks/Skripte man in welcher Reihenfolge ausführt.

---

## 3) Datenquellen (und was sie im Projekt bedeuten)

### 3.1 Yahoo Finance (yfinance)

- Download passiert über `src/data/load_finance.py`.
- Konfig ist in `config/symbols.yaml` (z.B. `EURUSD=X`, Zeitraum, Interval `1d`).
- Output ist (typisch) `data/raw/fx/EURUSDX.csv`.

Wichtig: Yahoo hat Limits für lange Zeiträume. Darum lädt `load_finance.py` in **Chunks** (`_chunk_range`), damit es funktioniert.

### 3.2 EODHD

Es gibt zwei Dinge:

- **Preise** (Alternative zu Yahoo): z.B. `data/raw/fx/EURUSDX_eodhd.csv`
- **News** (Sentiment): Rohdaten als JSONL in `data/raw/news/eodhd_news.jsonl`

News werden dann pro Tag aggregiert:

- `src/data/prepare_eodhd_news.py` erzeugt `data/processed/news/eodhd_daily_features.csv`

Für EODHD brauchst du meistens einen API‑Key (`EODHD_TOKEN`).

### 3.3 MetaTrader 5 (MT5)

Du exportierst Daten aus MT5 (M1/D1/H1).

Im Projekt gibt es zwei Wege:

1) **M1/D1 Export → Daily CSV im Projektformat**
   - Import: `scripts/import_mt5_rates.py`
   - Output z.B.: `data/raw/fx/EURUSD_mt5_D1.csv`

2) **H1 Export (2015–2025) → H1‑Features + Daily‑Aggregation**
   - H1 Parsing + Aggregation: `src/data/mt5_h1.py`
   - Wichtige Idee: Aus stündlichen Bars baust du pro Tag zusätzliche Features:
     - intraday Return‑Std, Range‑Max, tick_volume‑Sum, spread‑Mean, …

---

## 4) Labeling (Zielvariablen) – ganz genau

### 4.1 Die Hauptdatei

Das Kern‑Labeling ist in `src/data/label_eurusd.py`.

Die Funktion `_label_eurusd_core(...)` ist der wichtigste Teil.

### 4.2 Was ist ein “Label” hier?

Pro Tag `t` gibt es ein Label:

- `up`: innerhalb eines Horizonts steigt der Kurs genügend stark
- `down`: innerhalb eines Horizonts fällt der Kurs genügend stark
- `neutral`: sonst

### 4.3 Wichtige Parameter (einfach erklärt)

Diese Parameter tauchen immer wieder in Notebooks/Configs auf:

- `horizon_days`  
  Wie viele Tage in die Zukunft du schaust (Fensterlänge).

- `up_threshold` / `down_threshold`  
  Prozent-Schwellen.  
  Beispiel: `up_threshold = 0.005` bedeutet “+0.5%”.

- `strict_monotonic`  
  Wenn `True`, dann muss der Kurs im Fenster “sauber” steigen/fallen (keine Gegenbewegung).  
  Das macht Labels seltener, aber “klarer”.  

- `max_adverse_move_pct`  
  Toleranz für Gegenbewegung (“Stop‑Loss‑ähnlich”).  
  Beispiel: bei `up` darf der Kurs im Fenster nicht mehr als z.B. 1% gegen dich laufen.

- `hit_within_horizon`  
  Wenn `True`: Es reicht, wenn die Schwelle irgendwo im Fenster erreicht wird.  
  Wenn `False`: Es wird nur auf dem Endtag verglichen (t+horizon).

- `first_hit_wins`  
  Wenn innerhalb des Fensters sowohl UP‑Schwelle als auch DOWN‑Schwelle getroffen werden, musst du entscheiden.  
  `first_hit_wins=True` sagt: “Wer zuerst getroffen wurde, gewinnt.”

- `hit_source`  
  `'close'` oder `'hl'`.  
  `close`: nutzt nur Schlusskurse (Daily Close)  
  `hl`: nutzt High/Low im Fenster (intraday‑näher)

- `intraday_tie_breaker`  
  Wenn UP und DOWN am selben Tag erreicht werden (bei Daily OHLC weiß man die Reihenfolge nicht).  
  Dann entscheidet diese Regel: `'down'` oder `'up'`.

### 4.4 Warum sind die Label‑Parameter so wichtig?

Weil sie direkt bestimmen:

- wie viele Trades es überhaupt gibt (Klassenverteilung),
- ob das Modell etwas lernen kann,
- ob die Evaluation fair ist (kein Leakage).

Wenn du z.B. `strict_monotonic=True` und kleine Schwellen nimmst, kannst du trotzdem wenige Trades bekommen.  
Wenn du zu große Schwellen nimmst, bekommst du auch wenige Trades.  

Darum gibt es im Projekt sehr viele Experimente mit unterschiedlichen Parametern.

---

## 5) Features (Input fürs ML)

Feature‑Engineering ist in `src/features/eurusd_features.py`.

Die wichtigsten Gruppen:

### 5.1 Preis‑Features (`price_*`)

Beispiele:

- `price_close_ret_1d`: Tagesreturn
- `price_close_ret_5d`: 5‑Tage‑Return
- `price_range_pct_30d_std`: 30‑Tage Volatilitätsmaß

Wichtig: Rolling‑Features brauchen Kontext.  
Darum werden Preis‑Features idealerweise auf der vollen Preis‑Historie gerechnet (nicht erst nach News‑Merge).

### 5.2 News‑Features (`news_*`)

Wenn du News verwendest, werden pro Tag Aggregationen gebaut:

- Anzahl Artikel
- Sentiment‑Durchschnitt
- Rolling Summen / Lags

Die Merge‑Logik steht in `src/data/build_training_set.py`:

- `labels.merge(news, on="date", how="inner")`

Das heißt: Sobald `USE_NEWS=True`, bleibt automatisch nur der Zeitraum, wo auch News existieren (bei dir typischerweise ab ca. 2020).

### 5.3 Kalender‑Features (`cal_*`) und Holidays (`hol_*`)

Beispiele:

- Wochentag (Mon/Fri)
- Monatsanfang/‑ende
- US‑Feiertage (via pandas `USFederalHolidayCalendar`)

---

## 6) Modell (Zwei‑Stufen‑XGBoost)

### 6.1 Hauptlogik

Der Kern ist in `src/models/train_xgboost_two_stage.py`.

Stufe 1:

- Input: Feature‑Matrix `X`
- Target: `signal` (0=neutral, 1=move)

Stufe 2:

- Filter: nur Zeilen mit `signal==1`
- Target: `direction` (0=down, 1=up)

### 6.2 Zeitliches Splitting

Wichtig: Bei Zeitreihen darf man nicht random mischen.

Split passiert über ein `test_start` Datum (Standard: `2025-01-01`).

- `test`: ab `test_start`
- `train/val`: davor, chronologisch

### 6.3 `scale_pos_weight`

Die Klassen sind oft unbalanciert.

XGBoost kann das über `scale_pos_weight` ausgleichen:

- ungefähr `N_negative / N_positive`

Im Code wird das automatisch berechnet und zusätzlich “sanft” begrenzt, damit es nicht extrem wird.

### 6.4 Thresholds (warum 0.5 nicht reicht)

XGBoost gibt Wahrscheinlichkeiten aus.

Du brauchst einen Threshold, um daraus Klassen zu machen.

Im Projekt gibt es mehrere Thresholds:

- `signal_threshold`: “move” vs “neutral” (Reporting‑Threshold)
- `signal_threshold_trade`: “ab welcher Sicherheit mache ich überhaupt einen Trade”
- `direction_threshold_down` / `direction_threshold_up`: down/up Entscheidung

Wenn `direction_threshold_down < p_up < direction_threshold_up`, dann kann “neutral” rauskommen (Neutral‑Zone).

---

## 7) Evaluation (Metriken + Report)

### 7.1 Standard‑ML‑Metriken

Im Report siehst du:

- Confusion Matrices
- Precision / Recall / F1

Besonders wichtig bei Klassen‑Ungleichgewicht:

- `F1` für move in Stufe 1
- `F1` für up/down in Stufe 2
- `macro F1` im kombinierten 3‑Klassen‑Output

### 7.2 PDF‑Report Generator

Die PDF‑Generierung passiert über:

- `scripts/generate_two_stage_report.py`

Der Report ist so gebaut, dass er als “Audit Trail” dient:

- zeigt Config‑Parameter
- zeigt Metriken
- erzeugt Trading‑Plots

---

## 7.3 Ergebnis‑Überblick (was in diesem Repo “gut” aussieht)

Ich habe die gespeicherten Ergebnis‑JSONs in `notebooks/results/final_two_stage/` ausgewertet.

Wichtig: “gut” hängt davon ab, **welche Metrik** du optimierst.  
Macro‑F1 ist besser als Accuracy, wenn “neutral” dominiert.

Beobachtungen (aus den vorhandenen JSONs):

- Daily, price_only (Yahoo) hat in diesem Repo die besten macro‑F1‑Werte (ca. 0.54 in `hp_long_final_yahoo_8/9`).
- Daily, news+price ist in diesem Repo meist schwächer (bestes ca. 0.48 in `hv_long_final_yahoo_2`).
- MT5 H1 → Daily (price_source=`mt5_h1`) liegt in den vorhandenen Runs eher bei macro‑F1 ca. 0.37–0.42 (z.B. `20251226_21`).

Interpretation:

- News können helfen, aber nur wenn Labels/Features/Splits gut passen.
- Der Wechsel der Datenquelle (Yahoo vs. Broker‑Cut) kann Labels/Returns verändern.
- Viele “sehr gute” Runs sind oft empfindlich gegen kleine Änderungen am Labeling.

---

## 8) Tradesimulation (Variante 3 + Strategien A/B/C)

### 8.1 Was ist “Variante 3”?

In `scripts/generate_two_stage_report.py` gibt es eine Simulation, bei der P&L am Exit “gebucht” wird (`settle_at_exit=True`).

Das ist trading‑näher als “sofort täglich buchen”, weil ein Trade über mehrere Tage offen sein kann.

### 8.2 Strategien

- **Strategie A:** fixer Einsatz (z.B. 100 CHF pro Trade)
- **Strategie B:** fixer Anteil am Kapital (z.B. 10% Equity)
- **Strategie C:** Einsatz kommt aus Fuzzy‑Logik (FLEX): `risk_per_trade ∈ [0,1]`

Hebel 20 ist als “Skalierung” eingebaut (P&L * 20).  
Das ist kein vollständiges Broker‑Margin‑Modell, sondern eine einfache Sensitivitätsanalyse.

---

## 9) Symbolische KI: Fuzzy Risk Engine (FLEX)

### 9.1 Warum ist das symbolisch?

Weil es Regeln sind.

Beispiel‑Intuition:

- Wenn Signal‑Confidence hoch ist und Volatilität niedrig ist, dann darf Risiko höher sein.
- Wenn Volatilität hoch ist, dann Risiko runter.
- Wenn viele Trades offen sind, dann Risiko runter.

Das ist keine “Black Box”. Du kannst jede Regel lesen.

### 9.2 Wo ist das im Repo?

- Regeln (FCL‑ähnlich): `rules/risk.flex`
- Optional KSL (Generation5 Flex): `rules/risk.ksl`
- Engine/Wrapper: `src/risk/flex_engine.py`
- Einsatz‑Berechnung: `src/risk/position_sizer.py`

Wichtig: Auf macOS heißt `flex` normalerweise der Lexer‑Generator (nicht die Fuzzy‑Engine).  
Darum hat `src/risk/flex_engine.py` eine **Python‑Fallback‑Implementierung**. Diese ist trotzdem symbolisch (Regeln + Defuzzifizierung).

### 9.3 Wie wird “signal_confidence” berechnet?

In `src/risk/position_sizer.py` steht:

- `p_move` aus Stufe 1
- `p_up` aus Stufe 2
- Richtung “up” oder “down”

Dann:

- `direction_conf = p_up` (wenn up) oder `1 - p_up` (wenn down)
- `signal_confidence = p_move * direction_conf`

Das ist sinnvoll: ein Trade ist nur “sicher”, wenn beide Stufen zusammen sicher sind.

---

## 10) Reproduzierbarkeit (so dass dein Dozent es nachbauen kann)

### 10.1 Environment

Empfohlen:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Hinweise:

- In `requirements.txt` ist `eodhd` unpinned. Falls es Probleme gibt, pinne es (Version ergänzen).
- yfinance/EODHD brauchen Internet.

### 10.2 Daten beschaffen

Du hast drei mögliche Quellen:

1) Yahoo (Daily):
   - `python3 -m src.data.load_finance`
   - erwartet `config/symbols.yaml`
   - schreibt nach `data/raw/fx/`

2) EODHD (News + ggf. Preise):
   - Token setzen (`EODHD_TOKEN`)
   - News: `python3 -m src.data.fetch_eodhd_news ...`
   - Aggregation: `python3 -m src.data.prepare_eodhd_news`

3) MT5:
   - Export in MT5 (GUI oder Script)
   - Import Daily: `python3 -m scripts.import_mt5_rates --in <CSV>`
   - H1 bleibt als H1‑CSV im Projekt (wird in H1‑Notebooks verarbeitet)

### 10.3 Pipeline laufen lassen (Notebook‑Pfad “final_two_stage_h1”)

Wenn du MT5 H1 verwendest:

- `notebooks/final_two_stage_h1/1_data_prep_h1.ipynb`
  - erzeugt Config + Labels + Dataset für eine `EXP_ID`
- `notebooks/final_two_stage_h1/2_train_h1.ipynb`
  - trainiert Modell + speichert Results
- `notebooks/final_two_stage_h1/3_eval_h1.ipynb`
  - erzeugt PDF Report (via `scripts/generate_two_stage_report.py`)

Wichtig: `EXP_ID` muss in allen 3 Notebooks gleich sein.

### 10.4 Pipeline laufen lassen (v2‑CLI)

Wenn du eine “sauber” konfigurierte Pipeline willst (ohne Notebook‑State):

- config speichern: `src/experiments/v2_config.py`
- runner: `python3 -m scripts.run_two_stage_experiment_v2 --exp-id <EXP_ID>`

Outputs landen dann unter `data/processed/v2/`.

---

## 11) Git‑Historie (wie sich das Projekt entwickelt hat)

Es gibt bereits zwei auto‑generierte Hilfsdateien:

- `docs/git_commit_timeline.md` (Liste aller Commits)
- `docs/git_commit_filemap.md` (pro Commit: welche Dateien betroffen waren)

Für deinen Bericht kannst du die Entwicklung in Phasen erzählen:

1) Setup + Daten‑Download (Yahoo)
2) Labeling + erste Two‑Stage Modelle
3) News‑Merge + Features
4) Experimente (EXP_ID, Timelines, Reporting)
5) “final_two_stage” + stabiler PDF‑Report
6) MT5 Integration (D1, H1)
7) Symbolische KI (FLEX) + Strategie C

Wichtig: Git speichert “push” nicht als Ereignis. Git speichert nur Commits.  
Wenn du “Pushes” auf GitHub zeigen willst, ist das meist einfach die Commit‑Historie im Remote.

---

## 12) Glossar (Abkürzungen, sehr kurz)

- `EXP_ID`: Name eines Experiments; verbindet Config/Labels/Dataset/Results.
- `OHLC`: Open/High/Low/Close (Kerzendaten).
- `H1`, `D1`: 1‑Stunde, 1‑Tag Timeframe (MT5).
- `val`: Validation‑Split (zum Tuning).
- `test`: Test‑Split (Zukunfts‑ähnliche Daten; nicht für Tuning verwenden).
- `XGB` / `XGBoost`: Gradient‑Boosted Decision Trees Library.
- `F1`: Harmonic Mean von Precision und Recall.
- `macro F1`: Durchschnitt F1 über Klassen (jede Klasse gleich wichtig).
- `COG`: Center of Gravity = Schwerpunkt (Defuzzifizierung).
- `FLEX`: hier: fuzzy rules engine (nicht der macOS Lexer‑Generator).
- `risk_per_trade`: Output aus Fuzzy‑Regeln (0..1).

---

## 13) Was du mir noch sagen solltest (damit Bericht B perfekt wird)

Für den Abgabe‑Report (Bericht B) brauche ich von dir (kurz):

1) Welche Pipeline ist “dein finaler Stand”?
   - Yahoo daily? EODHD daily? MT5 H1?
2) Welche 1–3 EXP_IDs sind deine “finalen Experimente” für die Abgabe?
3) Willst du die symbolische Komponente (FLEX) als Hauptteil zeigen oder als Extension/Anhang?
