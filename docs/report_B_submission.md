# Bericht B (Abgabe‑Report) – hs2025_ml_project

Dieses Dokument ist als **Abgabe‑Report** gedacht.  
Es folgt der Struktur aus dem Foto.

Hinweis: Ich schreibe bewusst **verständlich**.  
Ich verwende **kurze Sätze**.  
Der Text ist aber **trotzdem ausführlich**.  
Wo dein Dozent “deine Gedanken” sehen will, habe ich kleine **[TODO]‑Stellen** markiert. Dort solltest du 2–5 Sätze in deiner eigenen Sprache ergänzen.

---

## Abstract / Zusammenfassung

In diesem Projekt wurde eine Pipeline entwickelt. Sie erzeugt Handelssignale aus historischen EURUSD‑Daten.  
Das Kernproblem ist die Klasse “neutral”. Sie ist sehr häufig. Ein direktes 3‑Klassen‑Modell (neutral/up/down) wird dann oft instabil.  

Darum wurde ein **Zwei‑Stufen‑Ansatz** gewählt.  
Stufe 1 erkennt, ob eine relevante Bewegung vorliegt (neutral vs. move).  
Stufe 2 sagt nur bei “move”, ob die Richtung eher up oder down ist.  

Zusätzlich wurde eine trading‑nahe Evaluation ergänzt. Sie nutzt Tradesimulation und P&L.  
Als symbolische Komponente wurde eine regelbasierte Fuzzy‑Logik integriert. Sie nutzt Modell‑Wahrscheinlichkeiten und Risiko‑Inputs (Volatilität, Equity, offene Trades). Sie gibt daraus eine Positionsgröße aus.  

Die Lösung ist reproduzierbar. Jede Experiment‑Konfiguration wird über eine Experiment‑ID (EXP_ID) versioniert. Alle Parameter landen automatisch in JSON/CSV/PDF‑Reports.

---

## Inhaltsverzeichnis

[TODO: In Word/LaTeX automatisch generieren lassen.]

---

## Verzeichnis der Abbildungen und Tabellen

### Abbildungen (Vorschläge mit Repo‑Pfad)

1. Pipeline‑Übersicht: `docs/image.png` (und `docs/image-1.png`, `docs/image-2.png`, `docs/image-3.png`)
2. Experiment‑Timeline (Tabelle/Ranking): `docs/two_stage_timeline.md` oder `docs/two_stage_timeline.csv`
3. Beispiel‑Report (PDF, Confusion‑Matrizen, Parameter):  
   - Daily/Yahoo: `notebooks/results/final_two_stage/two_stage_final__hp_long_final_yahoo_5_report.pdf` (oder ein anderes EXP_ID‑PDF)  
   - MT5/H1: `notebooks/results/final_two_stage/two_stage_final__20251226_21_report.pdf`
4. Tradesimulation (Strategie A/B/C) und Kapitalverlauf: kommt aus den PDFs oben (Seiten “Variante 3 …”)
5. Symbolische KI (Fuzzy Sets / Rules): `rules/risk.flex` (Screenshots oder selbst geplottet)

### Tabellen (Vorschläge)

1. Ordnerstruktur + Artefakt‑Mapping (siehe “Methodik/Prozeduren”)
2. Label‑Parameter und Klassenverteilung (aus `data/processed/fx/eurusd_labels__<EXP_ID>.csv`)
3. Feature‑Liste (aus `scripts/generate_two_stage_report.py`, Feature‑Seite im PDF)
4. Metriken je Split (aus `notebooks/results/final_two_stage/*_metrics.csv`)

---

## Einleitung

EURUSD ist eine stark gehandelte FX‑Zeitreihe. Kurse werden von vielen Faktoren beeinflusst, zum Beispiel Marktvolatilität, Session‑Cut, Feiertage und (optional) News. Das Projekt untersucht, ob ein datengetriebener Ansatz auf Basis historischer Daten für ein grobes Handelssignal sinnvoll ist. Dabei ist wichtig, dass die Auswertung zeitlich korrekt ist, damit kein “Blick in die Zukunft” entsteht (kein Leakage).

[TODO: 2–4 Sätze: Warum hast du dieses Thema gewählt? Was war die Motivation?]

---

## Ziele & Aufgabenstellung

### Ziele

- Eine reale Anwendungssituation analysieren (Trading‑Signal für EURUSD).
- Daten für ML aufbereiten (FX‑Preise, optional News; zusätzlich MT5‑Export).
- Wissen über das Problem sinnvoll repräsentieren (Label‑Regeln, Parameter, Experimente).
- Methoden kombinieren: ML‑Modell + symbolische KI (Fuzzy‑Regeln für Risk‑Sizing).
- Qualität beurteilen (ML‑Metriken + Trading‑nahe Simulation).
- Ergebnis so präsentieren, dass Nutzen und Grenzen klar sind (PDF‑Reports).

### Aufgabenstellung (konkret im Projekt)

1. Definiere Labels (neutral/up/down) über einen Horizont und Schwellen.
2. Erzeuge Features (Preis, Kalender, Holidays, optional News; optional H1‑intraday Features).
3. Trainiere ein Zwei‑Stufen‑Modell (Signal + Richtung) mit zeitlichem Split.
4. Tuning der Entscheidungsschwellen (Thresholds) ohne Leakage.
5. Erzeuge Reports (JSON/CSV/PDF) und Tradesimulation (Strategien A/B/C).

---

## Theorie

### Zwei‑Stufen‑Klassifikation

Ein 3‑Klassen‑Modell (neutral/up/down) kann bei starker Neutral‑Dominanz instabil werden. Der Zwei‑Stufen‑Ansatz trennt die Frage:

1) “Handle ich überhaupt?” (move vs neutral)  
2) “Wenn ja, welche Richtung?” (up vs down)

So wird Stufe 2 nur auf den “Trade‑Tagen” trainiert und ist dadurch fokussierter.

### XGBoost (kurz)

XGBoost ist ein Gradient‑Boosting‑Verfahren mit Entscheidungsbäumen. Es eignet sich gut für tabellarische Daten mit gemischten Features. Es kann Klassenungleichgewicht über `scale_pos_weight` berücksichtigen.

### Zeitreihen‑Evaluation

Bei Zeitreihen ist der Split kritisch. Wenn Daten zufällig gemischt werden, entsteht Leakage. Darum wird im Projekt zeitlich gesplittet:

- Train/Val: Vergangenheit  
- Test: Zukunft (z.B. ab `2025-01-01`)

### Symbolische KI (Fuzzy‑Logik)

Fuzzy‑Logik besteht aus:

- Fuzzy Sets (Membership Functions) für Inputs/Outputs
- Regeln (“IF … THEN …”)
- Defuzzifizierung (z.B. Schwerpunkt / “Center of Gravity”)

Im Projekt wird das genutzt, um aus Modell‑Sicherheit + Risiko‑Inputs einen Risiko‑Score zu berechnen, der dann in eine Positionsgröße umgerechnet wird.

---

## Methodik, Vorgehensweise und Prozeduren

### Projektverlauf (kurz, aus Git‑Historie)

Die Entwicklung ist im Repo nachvollziehbar, weil alle Schritte commit‑basiert dokumentiert sind.

- Phase 1 (Setup, Datenbeschaffung): erste Pipeline für Yahoo‑Daten (`src/data/load_finance.py`, `config/symbols.yaml`)
- Phase 2 (Labeling + erstes Two‑Stage Modell): `src/data/label_eurusd.py`, `src/models/train_xgboost_two_stage.py`
- Phase 3 (News‑Integration + Features): `src/data/fetch_eodhd_news.py`, `src/data/prepare_eodhd_news.py`, `src/features/eurusd_features.py`
- Phase 4 (Experiment‑Management + Reporting): EXP_ID‑Workflows + `scripts/generate_two_stage_report.py`
- Phase 5 (MT5 + H1): `src/data/mt5_h1.py`, `notebooks/final_two_stage_h1/*`
- Phase 6 (Symbolische KI für Risk‑Sizing): `rules/risk.flex`, `src/risk/*`, Strategie C in Tradesimulation

Details (Liste aller Commits + betroffene Dateien):

- `docs/git_commit_timeline.md`
- `docs/git_commit_filemap.md`

### 1) Datenbeschaffung

Es gibt drei Wege:

- Yahoo Finance (Daily): `src/data/load_finance.py` mit `yfinance`
- EODHD (optional News + Preise): `src/data/fetch_eodhd_news.py`, `src/data/prepare_eodhd_news.py`
- MT5 (Broker‑Daten): Export in MT5 + Import im Projekt (`scripts/import_mt5_rates.py`) oder H1‑Processing (`src/data/mt5_h1.py`)

Wichtig: Rohdaten liegen unter `data/raw/` und werden aus Lizenz-/Größen‑Gründen nicht versioniert (`.gitignore`).

### 2) Data‑Prep (Labels + Dataset)

Hauptlogik:

- Labeling: `src/data/label_eurusd.py`
- Dataset‑Merge (News): `src/data/build_training_set.py`
- Feature Engineering: `src/features/eurusd_features.py`

Für MT5‑H1:

- H1 → Daily OHLC + H1‑Features: `src/data/mt5_h1.py`
- H1‑Labeling‑Erweiterung: `src/data/label_eurusd.py` (hit_source `'h1'` via Daily+H1)

Outputs pro Experiment:

- Config: `data/processed/experiments/<EXP_ID>_config.json`
- Labels: `data/processed/fx/eurusd_labels__<EXP_ID>.csv`
- Dataset: `data/processed/datasets/eurusd_{price|news}_training__<EXP_ID>.csv`

### 3) Training (Zwei‑Stufen‑XGBoost)

Kerncode:

- `src/models/train_xgboost_two_stage.py`

Wichtige Punkte:

- Zeitlicher Split über `test_start`
- `scale_pos_weight` gegen Klassenungleichgewicht
- Early‑Stopping auf Val (wenn Val vorhanden)

### 4) Threshold‑Tuning (Entscheidungsschwellen)

Im Projekt gibt es verschiedene Varianten:

- Klassisch: feste 0.5 Thresholds (Baseline)
- Val‑basiert: Suche nach Thresholds im Val‑Split (ohne Test‑Leakage)
- Kostenbasiert (v2‑Pipeline): einfaches P&L‑Modell als Optimierungsziel (`src/models/train_two_stage_v2.py`)

### 5) Reporting + Tradesimulation

PDF‑Report:

- `scripts/generate_two_stage_report.py`

Er enthält:

- Parameter‑Seiten (alles ist dokumentiert)
- Confusion‑Matrizen (Signal, Direction, Combined)
- Tradesimulation mit Strategien:
  - Strategie A: fixer Einsatz
  - Strategie B: fixer Anteil am Kapital
  - Strategie C: Einsatz via Fuzzy‑Logik (symbolisch)

### 6) Symbolische KI (Risk‑Sizing)

Regeln:

- `rules/risk.flex` (FCL‑ähnlich)
- optional `rules/risk.ksl` (Generation5‑Syntax)

Engine/Wrapper:

- `src/risk/flex_engine.py`
- `src/risk/position_sizer.py`

Hinweis: Auf macOS ist `flex` meist der Lexer‑Generator, nicht die Fuzzy‑Engine. Darum gibt es eine Python‑Fallback‑Implementierung, die trotzdem regelbasiert ist.

---

## Ergebnisse

### Welche Artefakte zeigen die Ergebnisse?

Für jedes Experiment gibt es:

- JSON: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>.json`
- CSV Metriken: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_metrics.csv`
- CSV Predictions: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_predictions.csv`
- PDF: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_report.pdf`

### Kurzer Ergebnisüberblick (aus den JSON‑Reports im Repo)

Diese Zahlen stammen direkt aus den gespeicherten Ergebnis‑JSONs unter `notebooks/results/final_two_stage/`.

- Beste `price_only`‑Runs (Daily, Yahoo) erreichen in diesem Repo ca. `macro_f1 ≈ 0.54` (z.B. `hp_long_final_yahoo_8`/`hp_long_final_yahoo_9`).
- Beste `news+price`‑Runs liegen in diesem Repo tiefer (ca. `macro_f1 ≈ 0.48`, z.B. `hv_long_final_yahoo_2`).
- MT5‑H1 (Broker‑Daten, H1→Daily) liegt in den vorhandenen Runs eher bei `macro_f1 ≈ 0.37–0.42` (z.B. `20251226_21`).

Interpretation (kurz): News helfen nicht automatisch. Labels und Datenquelle bestimmen sehr stark, wie gut das Modell generalisiert.

### Welche Experimente sind “final”?

[TODO: Hier die 1–3 EXP_IDs eintragen, die du in der Abgabe verwendest.]

Beispiel‑Kandidaten (aus dem Repo sichtbar):

- Daily/Yahoo (viele Experimente): z.B. `hp_long_final_yahoo_5`, `hv3_h4_thr0p5pct_hit`
- MT5/H1 (Broker‑Daten): z.B. `20251226_21`

### Was zeigen die Metriken?

Du solltest im Report mindestens diskutieren:

- Stufe 1: F1(move) auf Test
- Stufe 2: F1(up/down) auf Test (nur Trade‑Tage)
- Combined: macro‑F1 über {neutral, up, down}
- Tradesimulation: Kapitalverlauf und Drawdowns

[TODO: 5–10 Sätze: Was war “gut”? Was war “schlecht”? Was war überraschend?]

---

## Diskussion oder Interpretation

### Warum kann Val → Test schlechter werden?

Das ist normal. Gründe:

- Der Markt ändert sich (Regime‑Shift).
- Tuning passt sich an Val an, aber Val ist nicht identisch zu Test.
- Klassenverteilungen ändern sich.

### Grenzen des Projekts

- Die Labels sind heuristisch. Andere Label‑Definitionen können andere Ergebnisse liefern.
- Trading‑Simulation ist vereinfacht (Spreads, Slippage, Margin, echte TP/SL‑Ausführung sind nicht vollständig modelliert).
- Rohdaten sind nicht versioniert. Reproduzierbarkeit braucht klare Daten‑Schritte.

### Lernpunkte (bitte in deinen Worten)

[TODO: 5–10 Sätze: Was hast du gelernt? Z.B. über Zeitreihen‑Splits, Leakage, Label‑Design, Threshold‑Tuning, Evaluation.]

---

## Schlussfolgerungen

Das Projekt zeigt eine vollständige End‑to‑End Pipeline von Rohdaten bis zu Reports. Der Zwei‑Stufen‑Ansatz ist eine sinnvolle Struktur für Probleme mit stark dominierender Neutral‑Klasse. Die Kombination von ML und symbolischer KI ist möglich: ML liefert Wahrscheinlichkeiten, und Fuzzy‑Regeln übersetzen sie in ein Risikomanagement‑Signal (Positionsgröße). Die Qualität hängt aber stark von Label‑Definition, Datenquelle und Tuning ab.

---

## Empfehlungen

- Für eine robustere Aussage wären Walk‑Forward Tests sinnvoll (mehrere Test‑Fenster, nicht nur ab 2025).
- Für Trading‑Nähre sollte man Slippage/Spread/Margin genauer modellieren.
- Labels sollten eng an eine echte Strategie gekoppelt werden (TP/SL, ATR‑Stops; siehe v2‑Labeling).
- News‑Merge sollte sauber dokumentiert sein (ab wann News verfügbar sind, wie Missing Days behandelt werden).

---

## Referenzen / Bibliographie (Startliste)

- XGBoost: Chen, Tianqi; Guestrin, Carlos. “XGBoost: A Scalable Tree Boosting System.” (2016)
- scikit‑learn Dokumentation (Metriken, Splits)
- yfinance Dokumentation (Yahoo Finance Wrapper)
- EODHD API Dokumentation (News/Prices)
- Fuzzy‑Logik Grundlagen (Mamdani‑Inference, Defuzzifizierung “centroid/COG”)

[TODO: Falls du externe Webseiten/Artikel verwendet hast, hier ergänzen.]

---

## Anhänge

### A1) Reproduzierbarkeit (Checkliste)

1) Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Rohdaten beschaffen

- Yahoo: `python3 -m src.data.load_finance` (schreibt nach `data/raw/fx/`)
- EODHD News (optional): Token setzen und `python3 -m src.data.prepare_eodhd_news`
- MT5: Export manuell, dann Import ins Projekt (`scripts/import_mt5_rates.py`) oder H1‑CSV speichern

3) Pipeline laufen lassen

Option Notebook (H1):

- `notebooks/final_two_stage_h1/1_data_prep_h1.ipynb`
- `notebooks/final_two_stage_h1/2_train_h1.ipynb`
- `notebooks/final_two_stage_h1/3_eval_h1.ipynb`

Option CLI (v2):

- `python3 -m scripts.run_two_stage_experiment_v2 --exp-id <EXP_ID>`

4) Output prüfen

- PDF: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_report.pdf`
- JSON/CSV: gleiches Verzeichnis

### A2) Git‑Historie

Siehe:

- `docs/git_commit_timeline.md`
- `docs/git_commit_filemap.md`
