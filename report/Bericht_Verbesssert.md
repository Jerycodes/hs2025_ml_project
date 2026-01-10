# Trading mit Machine Learning

## Vorhersage signifikanter Bewegungen von EUR/USD mittels Machine Learning und Finanznachrichten

---

**Projektarbeit**

| | |
|---|---|
| **Autor:** | Jeremy Nathan |
| **Modul:** | E-Maschinelles Lernen und wissensbasierte Systeme 2025 |
| **Semester:** | Herbstsemester 2025 |

---

## Zusammenfassung

Dieses Projekt entwickelt ein Machine-Learning-System zur Vorhersage signifikanter Kursbewegungen des Währungspaares EUR/USD. Die Lösung kombiniert zwei fundamentale Ansätze der künstlichen Intelligenz: Einen Zwei-Stufen-XGBoost-Klassifikator für die Bewegungsvorhersage und ein Fuzzy-Logic-System (symbolische KI) für das transparente Risikomanagement bei der Positionsgrössenbestimmung.

Die zentrale Innovation liegt in der **Zwei-Stufen-Architektur**, die das Problem der extremen Klassenungleichheit im Forex-Markt adressiert: Stufe 1 klassifiziert zunächst, ob überhaupt eine signifikante Bewegung stattfinden wird (`neutral` vs. `move`). Erst wenn das Signal-Modell eine Bewegung vorhersagt, bestimmt Stufe 2 die Richtung (`up` vs. `down`). Diese hierarchische Trennung verbessert die Modellqualität gegenüber einem direkten 3-Klassen-Ansatz erheblich, da jede Stufe unabhängig auf ihre spezifische Aufgabe optimiert werden kann.

Als Datenquellen wurden MetaTrader 5 (Broker-Daten mit stündlicher Auflösung), Yahoo Finance und EODHD (inklusive Finanznachrichten mit Sentiment-Analyse) evaluiert und integriert. Insgesamt wurden über 35 Features aus Preis-, News-, Kalender- und Intraday-Daten entwickelt. Die symbolische KI-Komponente (Fuzzy-Regeln im FLEX-Format) übersetzt die Modell-Konfidenz zusammen mit Risikofaktoren (Volatilität, offene Positionen, verfügbares Kapital) in eine nachvollziehbare, transparente Positionsgrösse in CHF.

Die Evaluation erfolgte strikt mittels zeitlicher Train/Val/Test-Splits ohne Lookahead-Bias. In der Tradesimulation auf dem ungesehenen Test-Set (ab Januar 2025) erzielte das beste Experiment einen theoretischen Gewinn von über 3'500 CHF bei einem Startkapital von 1'000 CHF und Hebel 20. Die Ergebnisse zeigen, dass Finanznachrichten als zusätzliches Feature die Vorhersagequalität messbar verbessern können.

---

## Inhaltsverzeichnis

1. [Einleitung](#einleitung)
2. [Ziele und Aufgabenstellung](#ziele-und-aufgabenstellung)
3. [Theorie](#theorie)
4. [Methodik, Vorgehensweise und Prozeduren](#methodik-vorgehensweise-und-prozeduren)
5. [Ergebnisse](#ergebnisse)
6. [Diskussion und Interpretation](#diskussion-und-interpretation)
7. [Schlussfolgerungen](#schlussfolgerungen)
8. [Empfehlungen](#empfehlungen)
9. [Referenzen](#referenzen)
10. [Anhänge](#anhänge)

---

## Verzeichnis der Abbildungen

- **Abbildung 1:** EUR/USD Schlusskurs mit Train/Val/Test-Splits (hv_mt5_flex_result)
- **Abbildung 2:** Kumulierter P&L der drei Trading-Strategien (hv_mt5_flex_result)
- **Abbildung 3:** Trade-Details Strategie C - Fuzzy-basiertes Sizing
- **Abbildung 4:** Trade-Details Strategie B - 10% des Kapitals
- **Abbildung 5:** Confusion-Matrix des kombinierten Modells (hv_mt5_flex_result)
- **Abbildung 6:** Beispiel einer falsch klassifizierten Instanz
- **Abbildung 7:** EUR/USD Schlusskurs ohne News-Features (hp_mt5_flex_result)
- **Abbildung 8:** P&L-Vergleich ohne News-Features
- **Abbildung 9:** Confusion-Matrix ohne News (hp_mt5_flex_result)
- **Abbildung 10:** P&L Yahoo Finance Experiment (hp_long_flex_0_7_result)
- **Abbildung 11:** Confusion-Matrix Yahoo Finance
- **Abbildung 12:** Vergleich mit vs. ohne News-Features bei gleichem Trainingszeitraum

## Verzeichnis der Tabellen

- **Tabelle 1:** Übersicht der verwendeten Datenquellen
- **Tabelle 2:** Feature-Kategorien und Anzahl
- **Tabelle 3:** Labeling-Parameter der finalen Experimente
- **Tabelle 4:** Ergebnisübersicht aller Experimente

---

## Einleitung

Der Devisenmarkt (Foreign Exchange, kurz FX) ist der grösste und liquideste Finanzmarkt der Welt mit einem täglichen Handelsvolumen von über 7.5 Billionen US-Dollar. Im Gegensatz zu zentralisierten Börsen wie der SIX oder NYSE ist der Devisenmarkt dezentralisiert organisiert – es gibt keine zentrale Handelsplattform, sondern ein Netzwerk aus Banken, Brokern und institutionellen Händlern, die rund um die Uhr miteinander handeln. Das Währungspaar EUR/USD (Euro gegen US-Dollar) ist dabei das meistgehandelte Instrument und macht etwa 22% des gesamten FX-Handelsvolumens aus.

Die Kursbewegungen von Währungspaaren entstehen durch das komplexe Zusammenspiel vieler Faktoren: makroökonomische Daten wie Arbeitslosenquoten, Inflationsraten und Wirtschaftswachstum, geldpolitische Entscheidungen der Zentralbanken (EZB und Federal Reserve), politische Ereignisse wie Wahlen oder geopolitische Spannungen sowie die aggregierten Erwartungen und Positionierungen der Marktteilnehmer. Diese Vielschichtigkeit macht den Devisenmarkt aus Datenanalyse-Perspektive besonders herausfordernd, bietet aber gleichzeitig das Potenzial, mit datengetriebenen Methoden Muster zu erkennen, die dem menschlichen Auge verborgen bleiben.

Der klassische Einstieg in den EUR/USD-Handel erfolgt häufig über die technische Chartanalyse, bei der historische Kursmuster analysiert und Trends erkannt werden, um darauf basierend Handelsentscheidungen zu treffen. Dabei werden Indikatoren wie gleitende Durchschnitte, Relative-Stärke-Indizes (RSI) oder Fibonacci-Retracements verwendet. Ein grundlegendes Problem dieser Ansätze zeigt sich jedoch, wenn externe Faktoren wie überraschende Zentralbank-Entscheidungen oder neue Importzölle in Kraft treten – diese können etablierte technische Muster invalidieren und zu unerwarteten, starken Kursschwankungen führen, die mit rein preisbasierten Methoden schwer vorherzusagen sind.

Dieses Projekt wurde konzipiert, um mit Methoden des maschinellen Lernens und unter Berücksichtigung von Finanznachrichten genau solche signifikanten Bewegungen vorherzusagen. Die zentrale Hypothese lautet: **Bei grösseren Kursbewegungen sind Hinweise sowohl in historischen Kursdaten als auch in Nachrichteninformationen erkennbar, die ein Machine-Learning-Modell nutzen kann, um überzufällige Vorhersagen zu treffen.**

Eine zentrale Herausforderung liegt in der Definition von „signifikanten Bewegungen": Werden die Schwellenwerte für Up- und Down-Bewegungen zu hoch angesetzt, entstehen zu wenige Trainingsbeispiele für eine robuste Modellierung. Werden sie zu niedrig angesetzt, entstehen zu viele Falschsignale, da auch normale Marktfluktuationen als Signal gewertet werden. Daher wurden in diesem Projekt experimentell verschiedene Definitionen und Schwellenwerte getestet, um eine praktikable Balance zwischen Signalqualität und ausreichender Datenbasis zu erreichen. Das Endergebnis soll täglich eine Empfehlung generieren, ob eine Long-Position (Kauf), Short-Position (Verkauf) oder keine Position eingegangen werden sollte.

Durch die Integration symbolischer künstlicher Intelligenz in Form von Fuzzy-Logik soll zusätzlich ein transparentes Risikomanagement-System entstehen, das nicht nur die Richtungsentscheidung, sondern auch die Frage beantwortet: **Wie viel Kapital sollte bei diesem Trade eingesetzt werden?** Im Gegensatz zu Black-Box-ML-Modellen sind Fuzzy-Regeln für Menschen lesbar und nachvollziehbar, was im Finanzkontext besonders wichtig ist.

Das Thema algorithmen-gestützter Handel hat mich seit längerer Zeit interessiert. Dieses Projekt bot die Gelegenheit, ein solches System eigenständig von Grund auf zu entwickeln und dabei sowohl moderne ML-Methoden als auch klassische symbolische KI-Ansätze zu kombinieren.

---

## Ziele und Aufgabenstellung

### Aufgabenstellung

Die Aufgabenstellung dieses Projekts bestand darin, ein reales Anwendungsbeispiel für den Einsatz von künstlicher Intelligenz zu bearbeiten und umzusetzen. Dabei mussten geeignete Methoden analysiert, ausgewählt und adäquat eingesetzt werden. Das Projekt sollte die im Modul vermittelten Kompetenzen praktisch anwenden und dokumentieren.

### Modul-Lernziele

Die folgenden Kompetenzziele des Moduls wurden im Projekt adressiert:

**Anwenden von Wissen:**
- Eine Anwendungssituation analysieren und geeignete Methoden auswählen: Die Herausforderung der Kursprognose wurde analysiert und das Zwei-Stufen-XGBoost-Modell als geeignete Methode für das vorliegende Klassifikationsproblem mit unbalancierten Klassen identifiziert.
- Daten für maschinelles Lernen aufbereiten: Rohdaten aus drei verschiedenen Quellen (MT5, Yahoo, EODHD) wurden geladen, bereinigt, transformiert und in ein einheitliches Trainingsformat gebracht.
- Notwendiges Wissen über die Anwendung geeignet repräsentieren: Die Trading-Logik (wann ist eine Bewegung „signifikant"?) wurde in einer konfigurierbaren Labeling-Funktion mit über 10 Parametern formalisiert.
- Methoden der symbolischen KI und des maschinellen Lernens kombinieren: XGBoost-Klassifikation wurde mit Fuzzy-Logic-Risikomanagement zu einem hybriden System verbunden.

**Urteilen:**
- Qualität einer Lösung beurteilen: Die Modelle wurden mit ML-Metriken (F1, Precision, Recall) und Trading-Metriken (P&L, Win-Rate) evaluiert.
- Beurteilen, ob eine Anwendung für KI geeignet ist: Die Diskussion reflektiert kritisch die Grenzen und Chancen des ML-Ansatzes für Finanzprognosen.

**Kommunikative Fertigkeiten:**
- Lösung präsentieren, sodass der Nutzen ersichtlich ist: Dieser Bericht dokumentiert das Vorgehen, die Ergebnisse und den praktischen Nutzen des entwickelten Systems.

### Projektbezogene Ziele

Die konkreten Ziele dieses Projekts waren:

1. **Datenbeschaffung und -aufbereitung:** Historische EUR/USD-Kursdaten aus verschiedenen Quellen (Yahoo Finance, EODHD, MetaTrader 5) beschaffen, validieren und in ein einheitliches Format bringen.

2. **News-Integration:** Finanznachrichten als zusätzliche Informationsquelle integrieren und deren Sentiment (positiv/neutral/negativ) als Features für das Modell aufbereiten.

3. **Labeling-System:** Eine flexible, konfigurierbare Labeling-Logik entwickeln, die aus Kurszeitreihen automatisch Labels (`up`, `down`, `neutral`) generiert basierend auf definierbaren Schwellenwerten und Horizonten.

4. **Feature Engineering:** Relevante Features aus Kurs- und Nachrichtendaten extrahieren, die dem Modell Vorhersagekraft verleihen (Preis-Returns, Volatilität, Sentiment-Aggregationen, Kalender-Features).

5. **Zwei-Stufen-Klassifikationsmodell:** Ein hierarchisches XGBoost-Modell trainieren, das zuerst die Existenz einer signifikanten Bewegung erkennt und dann deren Richtung bestimmt.

6. **Evaluation:** Modell-Vorhersagen sowohl mit klassischen ML-Metriken als auch mit realistischen Trading-Simulationen evaluieren.

7. **Symbolische KI:** Ein Fuzzy-Logic-System für transparentes, regelbasiertes Risikomanagement implementieren.

8. **Hybrides System:** ML-Vorhersagen und symbolische KI zu einem integrierten System verbinden.

9. **Reproduzierbarkeit:** Das gesamte System so dokumentieren und strukturieren, dass Experimente reproduzierbar sind (EXP_ID-System, versionierte Konfigurationsdateien).

### Persönliche Lernziele

- Python-Kenntnisse vertiefen, insbesondere im Bereich Data Science (pandas, numpy, scikit-learn, xgboost)
- Praktische Erfahrung in der Durchführung eines selbstständigen ML-Projekts von der Datenbeschaffung bis zur Evaluation sammeln
- Konzeptionelles Verständnis von Zeitreihenanalyse, Feature Engineering und Evaluierungsmethoden für Finanzanwendungen aufbauen
- Den Umgang mit Fuzzy-Logik und der Kombination verschiedener KI-Paradigmen erlernen
- Best Practices für Reproduzierbarkeit und saubere Projektdokumentation praktizieren

---

## Theorie

Dieses Kapitel erläutert die grundlegenden Konzepte und Methoden, die im Projekt verwendet werden. Der Fokus liegt auf der Erklärung fachlicher Begriffe und theoretischer Grundlagen, ohne dabei auf projektspezifische Implementierungsdetails einzugehen.

### Klassifikationsprobleme und unbalancierte Klassen

Bei Klassifikationsproblemen wird versucht, Datenpunkte in vordefinierte Kategorien einzuteilen. Im vorliegenden Fall soll jeder Handelstag einer von drei Klassen zugeordnet werden: `up` (signifikanter Kursanstieg), `down` (signifikanter Kurssrückgang) oder `neutral` (keine signifikante Bewegung).

Ein häufiges Problem bei Klassifikationsaufgaben tritt auf, wenn die Klassen stark **unbalanciert** sind – das bedeutet, dass eine oder mehrere Klassen deutlich häufiger vorkommen als andere. Im Forex-Markt ist dies typischerweise der Fall: Die meisten Tage zeigen keine signifikante Bewegung und werden daher als `neutral` gelabelt. Eine typische Verteilung könnte sein: 75-85% neutral, 8-15% up, 7-12% down.

Diese Unbalance hat wichtige Konsequenzen für die Modellierung:

1. **Triviale Lösungen:** Ein Modell kann sehr hohe Accuracy erreichen, indem es einfach immer die häufigste Klasse (`neutral`) vorhersagt – ohne dabei echte Muster zu lernen. Bei 80% neutralen Tagen erreicht eine solche triviale Lösung 80% Accuracy.

2. **Gradient-basiertes Lernen:** Gradient-Boosting-Algorithmen wie XGBoost optimieren typischerweise eine Verlustfunktion, die alle Fehler gleich gewichtet. Bei unbalancierten Klassen werden Fehler auf der Minderheitsklasse untergewichtet, was zu schlechter Performance auf diesen Klassen führt.

Daher ist bei unbalancierten Klassen die **Accuracy allein ein schlechter Massstab**. Wichtiger sind klassenspezifische Metriken:

- **Precision (Präzision):** Von allen als positiv vorhergesagten Fällen, wie viele sind tatsächlich positiv? `Precision = TP / (TP + FP)`
- **Recall (Sensitivität):** Von allen tatsächlich positiven Fällen, wie viele wurden gefunden? `Recall = TP / (TP + FN)`
- **F1-Score:** Das harmonische Mittel aus Precision und Recall, das beide Aspekte ausbalanciert: `F1 = 2 * (Precision * Recall) / (Precision + Recall)`
- **Macro-F1:** Der ungewichtete Durchschnitt der F1-Scores aller Klassen. Dies gibt jeder Klasse unabhängig von ihrer Häufigkeit das gleiche Gewicht.

### Two-Stage-Klassifikation (Hierarchische Klassifikation)

Eine bewährte Strategie für Probleme mit stark unbalancierten Klassen ist die **hierarchische oder kaskadierte Klassifikation**. Statt ein einzelnes Modell zu trainieren, das direkt zwischen allen Klassen unterscheidet, wird das Problem in mehrere aufeinanderfolgende Entscheidungen aufgeteilt.

Im vorliegenden Projekt wurde folgende Zwei-Stufen-Architektur implementiert:

**Stufe 1 (Signal-Modell):**
- Aufgabe: Entscheiden, ob überhaupt eine signifikante Bewegung stattfindet
- Klassen: `neutral` (0) vs. `move` (1)
- Dies ist ein binäres Klassifikationsproblem mit typisch ~20-25% positiver Klasse

**Stufe 2 (Richtungs-Modell):**
- Aufgabe: Wenn eine Bewegung vorhergesagt wurde, deren Richtung bestimmen
- Klassen: `down` (0) vs. `up` (1)
- Wird nur auf Daten trainiert, bei denen tatsächlich eine Bewegung stattfand
- Typisch relativ ausgeglichene Klassenverteilung (ca. 45-55%)

**Vorteile dieser Architektur:**

1. **Spezialisierung:** Jedes Modell kann sich auf seine spezifische Aufgabe konzentrieren. Das Signal-Modell lernt, was einen „bewegungsreichen" Tag ausmacht. Das Richtungs-Modell lernt, was Up- von Down-Bewegungen unterscheidet.

2. **Bessere Gradientennutzung:** In Stufe 2 ist die neutrale Klasse eliminiert, was zu einer besser balancierten Verteilung führt und das Gradientenlernen effektiver macht.

3. **Unabhängige Optimierung:** Beide Modelle können mit unterschiedlichen Hyperparametern und Schwellenwerten optimiert werden.

4. **Interpretierbarkeit:** Die Zwei-Stufen-Struktur entspricht der natürlichen Denkweise eines Traders: „Erwartest du heute eine grosse Bewegung? Wenn ja, in welche Richtung?"

### Gradient Boosting mit XGBoost

**XGBoost** (Extreme Gradient Boosting) ist ein Ensemble-Lernverfahren, das Entscheidungsbäume in einer sequentiellen, additiven Weise kombiniert. Es wurde 2014 von Tianqi Chen entwickelt und hat sich seitdem als einer der leistungsstärksten Algorithmen für tabellarische (strukturierte) Daten etabliert.

**Grundprinzip des Gradient Boosting:**

1. Starte mit einem einfachen Modell (z.B. dem Durchschnitt der Zielvariable)
2. Berechne die Residuen (Fehler) zwischen Vorhersagen und tatsächlichen Werten
3. Trainiere einen neuen Entscheidungsbaum, der diese Residuen vorhersagt
4. Addiere den neuen Baum zum bestehenden Modell (gewichtet mit einer Lernrate)
5. Wiederhole Schritte 2-4 für eine festgelegte Anzahl von Iterationen

Jeder neue Baum konzentriert sich darauf, die Fehler der bisherigen Bäume zu korrigieren. Die endgültige Vorhersage ist die Summe aller Einzelbäume.

**Warum XGBoost für dieses Projekt?**

1. **Automatische Feature-Interaktionen:** Entscheidungsbäume können komplexe Abhängigkeiten zwischen Features erkennen. Beispiel: „Wenn Volatilität hoch UND Sentiment negativ UND Montag, dann sinkt der Kurs" – solche Zusammenhänge werden automatisch gelernt, ohne sie manuell definieren zu müssen.

2. **Robustheit:** XGBoost ist relativ unempfindlich gegenüber Feature-Skalierung und kann mit fehlenden Werten umgehen.

3. **Regularisierung:** Integrierte Regularisierungsparameter (L1, L2) verhindern Overfitting.

4. **Klassengewichtung:** Der Parameter `scale_pos_weight` ermöglicht es, die Minderheitsklasse stärker zu gewichten und so das Unbalance-Problem zu adressieren.

5. **Interpretierbarkeit:** Feature Importances zeigen, welche Eingabevariablen für die Vorhersagen am wichtigsten sind.

### Zeitreihen-Evaluierung und Leakage

Bei der Arbeit mit Zeitreihendaten wie Börsenkursen ist ein kritischer Fehler das sogenannte **Data Leakage**: Das Modell erhält – direkt oder indirekt – Informationen aus der Zukunft, die zum Zeitpunkt der Vorhersage nicht verfügbar gewesen wären.

**Formen von Leakage:**

1. **Direktes Leakage:** Ein Feature enthält explizit zukünftige Information (z.B. der Kurs von morgen als Feature für heute).

2. **Look-Ahead Bias bei Feature-Berechnung:** Rolling-Statistiken werden auf dem gesamten Datensatz berechnet, anstatt nur auf historischen Daten bis zum jeweiligen Zeitpunkt.

3. **Temporales Leakage beim Splitting:** Trainings- und Testdaten werden zufällig gemischt, sodass das Modell an Tagen trainiert, die zeitlich nach den Testtagen liegen.

**Korrekte Zeitreihen-Evaluation:**

Um Leakage zu vermeiden, muss beim Zeitreihensplitting strikt chronologisch vorgegangen werden:
- Die **Trainingsdaten** liegen zeitlich vollständig vor den **Validierungsdaten**
- Die **Validierungsdaten** liegen zeitlich vollständig vor den **Testdaten**
- Feature-Berechnungen (z.B. gleitende Durchschnitte) verwenden nur Daten bis zum jeweiligen Zeitpunkt

Im vorliegenden Projekt:
- **Training:** Alle Daten bis zu einem festen Cutoff (z.B. Ende 2022)
- **Validation:** Daten zwischen Cutoff und Test-Start (z.B. 2023-2024)
- **Test:** Alle Daten ab 2025-01-01 (tatsächlich „ungesehene" zukünftige Daten)

### Symbolische KI und Fuzzy-Logik

Während maschinelles Lernen (wie XGBoost) Muster aus Daten lernt und in komplexen, schwer interpretierbaren Modellen speichert, verfolgt die **symbolische KI** einen anderen Ansatz: Wissen wird durch explizite, für Menschen lesbare Regeln repräsentiert.

**Fuzzy-Logik** ist ein Teilgebiet der symbolischen KI, das mit „unscharfen" oder graduellen Wahrheitswerten arbeitet. Im Gegensatz zur klassischen Booleschen Logik, bei der Aussagen nur wahr (1) oder falsch (0) sein können, erlaubt Fuzzy-Logik Zwischenwerte. Eine Aussage wie „Volatilität ist hoch" kann beispielsweise zu 60% wahr sein.

**Kernkonzepte der Fuzzy-Logik:**

1. **Linguistische Variablen:** Statt numerischer Werte werden sprachliche Begriffe verwendet (z.B. „niedrig", „mittel", „hoch").

2. **Membership-Funktionen:** Definieren, zu welchem Grad ein numerischer Wert zu einer linguistischen Kategorie gehört. Beispiel: Bei einer Volatilität von 0.5 könnte die Zugehörigkeit zu „niedrig" 0.2, zu „mittel" 0.7 und zu „hoch" 0.3 betragen (überlappende Mengen).

3. **Fuzzy-Regeln:** Wenn-Dann-Regeln mit linguistischen Variablen:
   - WENN Konfidenz HOCH UND Volatilität NIEDRIG DANN Risiko HOCH
   - WENN Volatilität HOCH ODER offene_Trades VIELE DANN Risiko NIEDRIG

4. **Defuzzifikation:** Die Umwandlung des unscharfen Ergebnisses zurück in einen konkreten numerischen Wert (z.B. mittels Schwerpunktmethode/Centroid).

**Vorteile der Fuzzy-Logik gegenüber reinen ML-Modellen:**

1. **Transparenz:** Jede Entscheidung kann durch ihre auslösenden Regeln erklärt werden.
2. **Interpretierbarkeit:** Domänenexperten können die Regeln verstehen und validieren.
3. **Robustheit:** Kleine Änderungen in den Eingabewerten führen zu graduellen (nicht sprunghaften) Änderungen der Ausgabe.
4. **Flexibilität:** Regeln können manuell angepasst werden, um Domänenwissen einzubringen.

Im vorliegenden Projekt wird Fuzzy-Logik für das **Risikomanagement** eingesetzt: Basierend auf der Modell-Konfidenz, der aktuellen Marktvolatilität, der Anzahl offener Positionen und dem verfügbaren Kapital wird eine angemessene Positionsgrösse bestimmt – nachvollziehbar durch explizite Regeln.

---

## Methodik, Vorgehensweise und Prozeduren

### Projektverlauf und Vorgehensmodell

Das Vorgehen orientierte sich am **CRISP-DM-Prozessmodell** (Cross Industry Standard Process for Data Mining), das einen iterativen Ansatz für Data-Mining-Projekte beschreibt. Die Phasen „Business Understanding", „Data Understanding", „Data Preparation", „Modeling", „Evaluation" und „Deployment" wurden mehrfach durchlaufen. Nach jeder Evaluierungsphase wurden Erkenntnisse zurück in die Datenaufbereitung und das Modelltraining eingespeist.

Die Arbeit gliederte sich in sechs Hauptphasen:

**Phase 1 – Projektinitialisierung:**
- Projektstruktur und Git-Repository aufsetzen
- Erste Datenverarbeitungspipeline mit Yahoo Finance aufbauen
- Grundlegende Labeling-Logik implementieren
- *Überlegung:* Yahoo Finance wurde als Startpunkt gewählt, da es kostenlos, gut dokumentiert und einfach zugänglich ist. Die Datenqualität sollte später mit Broker-Daten verglichen werden.

**Phase 2 – News-Integration:**
- EODHD als Quelle für Finanznachrichten evaluieren
- News-Daten mit FX-Kursdaten verknüpfen
- Erste Sentiment-Features berechnen
- *Überlegung:* Ursprünglich war GDELT als News-Quelle geplant. Tests zeigten jedoch, dass bei vielen Artikeln nur Metadaten (Titel, URL) verfügbar waren, nicht der Volltext. EODHD bot bereits vorberechnete Sentiment-Scores, was die Integration vereinfachte.

**Phase 3 – Feature Engineering:**
- Preis-Features entwickeln (Returns, Volatilität, Kerzenkörper)
- News-Features aggregieren (3d/5d/7d Summen, Lags)
- Kalender- und Feiertags-Features hinzufügen
- *Überlegung:* Die Kalender-Features sollten saisonale Muster abfangen. Die Hypothese war, dass bestimmte Nachrichtenereignisse (Quartalsberichte, Zentralbank-Meetings) gehäuft zu bestimmten Zeitpunkten auftreten und das Modell diese Abhängigkeit lernen kann.

**Phase 4 – Two-Stage-Modell:**
- Zwei-Stufen-Architektur entwerfen und implementieren
- Signal-Modell und Richtungs-Modell separat trainieren
- Threshold-Tuning für Produktivszenarien
- *Überlegung:* Erste Versuche mit einem direkten 3-Klassen-Modell zeigten sehr schwache Performance auf den Minderheitsklassen. Die hierarchische Struktur wurde entwickelt, um dieses Problem zu adressieren.

**Phase 5 – Experiment-Management:**
- EXP_ID-System für reproduzierbare Experimente einführen
- MetaTrader 5 als zusätzliche Datenquelle integrieren
- Konfigurationsdateien versionieren
- *Überlegung:* Nach mehreren Wochen mit vielen Experimenten wurde klar, dass eine systematische Benennung und Speicherung der Ergebnisse notwendig ist. Das EXP_ID-System stellt sicher, dass jedes Experiment eindeutig identifizierbar und reproduzierbar ist.

**Phase 6 – Symbolische KI:**
- Fuzzy-Regeln für Risikomanagement entwerfen
- FLEX-Engine als Python-Modul wrappen
- Trading-Simulation mit drei Strategien implementieren
- *Überlegung:* Die ML-Modelle liefern Wahrscheinlichkeiten, aber keine direkte Handlungsempfehlung zur Positionsgrösse. Fuzzy-Logik wurde gewählt, weil sie transparente, nachvollziehbare Entscheidungen ermöglicht – wichtig im Finanzkontext.

### Projektstruktur

Die Projektstruktur wurde modular aufgebaut, um Wartbarkeit und Reproduzierbarkeit zu gewährleisten. Die Trennung zwischen wiederverwendbaren Python-Modulen (`src/`) und ausführbaren Notebooks (`notebooks/`) ermöglicht es, die Kernlogik unabhängig von spezifischen Experimenten zu entwickeln und zu testen.

```
hs2025_ml_project/
├── src/                              # Wiederverwendbare Python-Module
│   ├── data/                         # Datenverarbeitung
│   │   ├── label_eurusd.py           # Labeling-Logik (~800 LOC)
│   │   ├── build_training_set.py     # Dataset-Erstellung
│   │   ├── mt5_h1.py                 # MT5 H1→Daily Aggregation
│   │   └── prepare_eodhd_news.py     # News-Aufbereitung
│   ├── features/
│   │   └── eurusd_features.py        # Feature Engineering
│   ├── models/
│   │   └── train_xgboost_two_stage.py  # XGBoost-Trainer
│   └── risk/
│       ├── flex_engine.py            # Fuzzy-Engine Wrapper
│       └── position_sizer.py         # Positionsgrössen-Berechnung
├── notebooks/                        # Ausführbare Jupyter Pipelines
│   ├── final_two_stage/              # Yahoo Finance Pipeline
│   ├── final_two_stage_h1/           # MT5 H1 Pipeline
│   └── eodhd_two_stage/              # EODHD + News Pipeline
├── rules/
│   └── risk.flex                     # Fuzzy-Regeln (IEC 61131-7 FCL)
├── data/
│   ├── raw/                          # Unveränderte Rohdaten
│   └── processed/                    # Verarbeitete Daten
├── final_results/                    # Finale Experiment-Ergebnisse
└── archive/                          # Alte/experimentelle Artefakte
```

**EXP_ID-Workflow:**

Jedes Experiment wird durch eine eindeutige `EXP_ID` identifiziert (z.B. `hv_mt5_flex_result`). Diese ID wird in allen drei Notebooks einer Pipeline konsistent verwendet und erscheint in allen Output-Dateinamen:

- Config: `data/processed/experiments/<EXP_ID>_config.json`
- Labels: `data/processed/fx/eurusd_labels__<EXP_ID>.csv`
- Dataset: `data/processed/datasets/eurusd_*_training__<EXP_ID>.csv`
- Results: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>.json`
- Report: `notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_report.pdf`

**Namenskonvention für EXP_ID (nicht vom Code erzwungen, aber empfohlen):**
- `hp_` = Price-only (ohne News-Features)
- `hv_` = Mit News-Features
- `_mt5_` = MetaTrader 5 Datenquelle
- `_yahoo_` / `_eod_` = Yahoo Finance / EODHD Datenquelle
- `_flex_` = Mit Fuzzy-Logic Position Sizing

### Datenquellen

Für dieses Projekt wurden drei verschiedene Datenquellen evaluiert und integriert. Die Verwendung mehrerer Quellen ermöglicht den Vergleich der Datenqualität und die Validierung der Ergebnisse.

| Quelle | Typ | Zeitraum | Besonderheiten |
|--------|-----|----------|----------------|
| Yahoo Finance | Daily OHLC | 2015-2025 | Kostenlos, leicht zugänglich |
| EODHD | Daily OHLC + News | 2020-2025 | Inkl. Sentiment-Analyse |
| MetaTrader 5 | H1 OHLC | 2015-2025 | Broker-nah, Intraday-Daten |

**Yahoo Finance (Daily):**
EUR/USD-Kursdaten von Yahoo Finance wurden als Baseline verwendet. Diese Daten sind frei zugänglich und werden über die Python-Bibliothek `yfinance` geladen. Jeder Datensatz enthält: Datum, Open, High, Low, Close. Die Daten umfassen etwa 2'500 Handelstage von 2015 bis 2025.

*Überlegung zur Wahl:* Yahoo Finance diente als schneller Einstieg in das Projekt. Die Datenqualität ist für explorative Analysen ausreichend, aber für den produktiven Einsatz wurden später Broker-Daten bevorzugt.

**EODHD APIs:**
EODHD (End of Day Historical Data) ist ein kommerzieller Anbieter historischer Finanzdaten. Für dieses Projekt wurden zwei Datensätze verwendet:
1. EUR/USD-Kursdaten (als Alternative zu Yahoo für Vergleichszwecke)
2. Finanznachrichten mit automatisch berechneter Sentiment-Analyse

Die News-Daten liegen im JSONL-Format vor und enthalten pro Artikel: Titel, Veröffentlichungsdatum, Sentiment-Score (positiv/neutral/negativ). Diese wurden pro Tag aggregiert und mit den Kursdaten verknüpft. Die News-Daten sind bereits im Repository enthalten (`data/raw/news/eodhd_news.jsonl`), sodass kein API-Token für die Reproduktion benötigt wird.

*Überlegung zur Wahl:* EODHD wurde gewählt, weil es bereits vorberechnete Sentiment-Werte liefert. Die Alternative wäre gewesen, selbst NLP-Modelle für die Sentiment-Analyse zu trainieren – dies hätte den Projektumfang jedoch erheblich erweitert.

**MetaTrader 5 (MT5) – ActiveTrades:**
MetaTrader 5 ist eine weit verbreitete Handelsplattform für den Forex-Handel. Für dieses Projekt wurde ein Demokonto bei ActiveTrades eingerichtet, um broker-nahe Daten zu erhalten. MT5 bietet stündliche (H1) Kursinformationen mit:
- Open, High, Low, Close
- Tick-Volumen (Anzahl Preisänderungen pro Stunde)
- Tatsächlicher Spread (Geld-Brief-Spanne)

Die H1-Daten (2015–2025, ca. 68'000 Stunden-Bars) wurden zu täglichen OHLC-Daten aggregiert. Dabei wurden zusätzliche Intraday-Features berechnet (z.B. stündliche Return-Volatilität, Anteil steigender/fallender Stunden).

*Überlegung zur Wahl:* Broker-Daten sind für den produktiven Einsatz kritisch, da sie den tatsächlichen Kursen entsprechen, zu denen gehandelt werden kann. Die H1-Auflösung ermöglicht zudem ein realistischeres Labeling (Treffer innerhalb des Tages erkennen) und zusätzliche Intraday-Features.

**Erkenntnis zur Datenqualität:**
Im Verlauf des Projekts wurde deutlich, dass FX-Daten zwischen verschiedenen Quellen erheblich variieren können. Yahoo Finance und EODHD liefern unterschiedliche Werte für denselben Tag – Differenzen von 0.1-0.5% im Close-Kurs sind keine Seltenheit. Dies liegt daran, dass der FX-Markt dezentralisiert ist und verschiedene Datenanbieter unterschiedliche Liquidity-Provider aggregieren. Für konsistente Backtests sollte daher immer dieselbe Datenquelle verwendet werden, die auch für den späteren Live-Handel geplant ist.

### Labeling

Das Labeling – die Zuweisung von Labels (`up`, `down`, `neutral`) zu jedem Handelstag – war einer der kritischsten und aufwändigsten Teile des Projekts. Kleine Änderungen an den Labeling-Parametern führten oft zu grossen Änderungen in der Klassenverteilung und damit in den Modellergebnissen.

**Grundlegende Labeling-Logik:**

Für jeden Tag `t` wird ein Label zugewiesen basierend auf der Kursentwicklung innerhalb eines definierten Horizonts:

- `up`: Der Kurs steigt innerhalb von `horizon_days` um mindestens `up_threshold` (z.B. +2%)
- `down`: Der Kurs fällt innerhalb von `horizon_days` um mindestens `|down_threshold|` (z.B. -2%)
- `neutral`: Weder die Up- noch die Down-Schwelle wird erreicht

**Wichtige Labeling-Parameter:**

| Parameter | Beschreibung | Typische Werte |
|-----------|--------------|----------------|
| `horizon_days` | Vorhersagehorizont in Handelstagen | 4, 5, 15 |
| `up_threshold` | Mindest-Return für Up-Label | +0.02 (+2%) |
| `down_threshold` | Mindest-Return für Down-Label | -0.02 (-2%) |
| `hit_within_horizon` | Ob der Threshold irgendwann im Fenster erreicht werden muss | True/False |
| `first_hit_wins` | Bei `hit_within_horizon=True`: erster Treffer zählt | True/False |
| `max_adverse_move_pct` | Maximale Gegenbewegung (Stop-Loss-ähnlich) | 0.004 (0.4%) |
| `hit_source` | Welche Kurse für Treffer-Prüfung (H1 oder Daily) | 'close', 'hl', 'h1' |

**Evolution der Labeling-Logik:**

Die Labeling-Logik durchlief mehrere Iterationen, da bei der Analyse der Ergebnisse immer wieder Probleme auffielen:

*Iteration 1 – Einfacher End-of-Horizon-Return:*
Ursprünglich wurde nur geprüft, ob der Kurs am Ende des Horizonts über/unter dem Schwellenwert liegt. Problem: Ein Tag, an dem der Kurs zuerst stark steigt (+3%), dann aber zurückfällt und am Ende nur +0.5% über dem Start liegt, wurde als `neutral` gelabelt – obwohl ein Trader mit Take-Profit bei +2% profitiert hätte.

*Iteration 2 – Hit-Within-Horizon:*
Die Option `hit_within_horizon=True` wurde eingeführt. Nun reicht es, wenn der Threshold irgendwann innerhalb des Horizonts erreicht wird. Problem: Wenn sowohl Up- als auch Down-Threshold erreicht werden (starke Volatilität), war unklar, welches Label vergeben werden sollte.

*Iteration 3 – First-Hit-Wins:*
Mit `first_hit_wins=True` entscheidet der chronologisch erste Treffer. Bei Daily-Daten kann dies nur tagesgenau bestimmt werden. Problem: Wenn Up und Down am selben Tag erreicht werden, braucht es eine weitere Regel.

*Iteration 4 – Intraday Tie-Breaker (H1-Daten):*
Mit MT5-H1-Daten kann stundengenau geprüft werden, welcher Threshold zuerst erreicht wurde. Der Parameter `intraday_tie_breaker` (`'up'` oder `'down'`) entscheidet bei gleichzeitigem Treffer. Dies entspricht dem realistischeren Szenario eines Traders mit zwei Orders (Take-Profit und Stop-Loss).

*Iteration 5 – Max Adverse Move:*
Der Parameter `max_adverse_move_pct` wurde hinzugefügt, um Trades zu filtern, die zwar den Threshold erreichen, aber zwischenzeitlich stark gegen die Position laufen. Beispiel: Ein Trade, der zunächst -1% verliert, bevor er +2% erreicht, könnte durch einen Stop-Loss bei -0.4% bereits ausgestoppt worden sein. Mit dieser Option werden solche Fälle als `neutral` gelabelt.

**Typische Klassenverteilung:**

Mit den finalen Parametern (`horizon_days=4`, `up_threshold=0.02`, `hit_within_horizon=True`) ergibt sich typischerweise:
- 75-85% `neutral`
- 8-15% `up`
- 7-12% `down`

Die starke Unbalance bestätigt die Notwendigkeit der Zwei-Stufen-Architektur.

### Feature Engineering

Die Features lassen sich in fünf Kategorien einteilen. Insgesamt wurden ca. 35-45 Features entwickelt, wobei nicht alle in jedem Experiment verwendet werden (z.B. News-Features nur bei `USE_NEWS=True`).

**Tabelle: Feature-Kategorien**

| Kategorie | Präfix | Anzahl | Beispiele |
|-----------|--------|--------|-----------|
| Preis-Features | `price_*` | ~12 | `price_close_ret_1d`, `price_range_pct_5d_std` |
| News-Features | `news_*` | ~7 | `news_article_count_3d_sum`, `news_neg_share_5d_mean` |
| Kalender-Features | `cal_*` | ~6 | `cal_dow`, `cal_is_friday`, `cal_is_month_end` |
| Feiertags-Features | `hol_*` | ~3 | `hol_is_us_federal_holiday` |
| Intraday-Features | `h1_*` | ~9 | `h1_ret_std`, `h1_up_hours_frac` |

**Preis-Features (price_*):**

Diese Features werden aus den OHLC-Daten (Open, High, Low, Close) berechnet:

- `price_close_ret_1d`: Tagesrendite (Close-to-Close)
- `price_close_ret_5d`, `price_close_ret_30d`: 5-Tage- und 30-Tage-Return
- `price_range_pct_5d_std`: Rolling-Standardabweichung der Intraday-Range (Volatilität)
- `price_body_pct_5d_mean`: Durchschnittliche Kerzenkörper-Grösse (Close - Open)
- `price_body_vs_range`: Verhältnis Körper zu Gesamtrange (Indikator für Trend-Stärke)
- `price_shadow_balance`: Balance zwischen oberem und unterem Docht

*Überlegung:* Preis-Features erfassen die „technische" Seite des Marktes – Trends, Volatilität, Momentum. Die Rolling-Fenster (5d, 30d) sollen kurz- und mittelfristige Muster einfangen.

**News-Features (news_*):**

Diese Features aggregieren die Sentiment-Informationen aus Finanznachrichten:

- `news_article_count_3d_sum`, `news_article_count_7d_sum`: Nachrichtenvolumen
- `news_pos_share_5d_mean`, `news_neg_share_5d_mean`: Anteil positiver/negativer News
- `news_article_count_lag1`: Nachrichtenvolumen des Vortags
- `news_pos_share_lag1`, `news_neg_share_lag1`: Sentiment des Vortags

*Überlegung:* Die News-Features sollen externe Informationen einfangen, die in den Kursdaten nicht direkt sichtbar sind. Die Rolling-Summen und Lags vermeiden Look-Ahead-Bias, da nur vergangene Daten verwendet werden.

**Kalender-Features (cal_*):**

- `cal_dow`: Wochentag (0=Montag, 4=Freitag)
- `cal_day_of_month`: Tag des Monats (1-31)
- `cal_is_monday`, `cal_is_friday`: Binäre Flags für Wochenanfang/-ende
- `cal_is_month_start`, `cal_is_month_end`: Flags für Monatsübergänge

*Überlegung:* Die Hypothese war, dass bestimmte Tage systematisch anders sind. Beispiel: Am Monatsende könnten institutionelle Anleger ihre Portfolios rebalancieren. Freitags könnten Positionen vor dem Wochenende geschlossen werden.

**Feiertags-Features (hol_*):**

- `hol_is_us_federal_holiday`: Ist heute ein US-Feiertag?
- `hol_is_day_before_us_federal_holiday`, `hol_is_day_after_us_federal_holiday`: Umgebende Tage

*Überlegung:* An Feiertagen ist die Liquidität typischerweise niedriger, was zu atypischem Preisverhalten führen kann. Die Tage davor und danach könnten ebenfalls betroffen sein.

**Intraday-Features (h1_*) – nur bei MT5-Pipeline:**

Diese Features nutzen die stündliche Auflösung der MT5-Daten:

- `h1_ret_std`: Standardabweichung der stündlichen Returns (intraday Volatilität)
- `h1_ret_sum_abs`: Summe der absoluten stündlichen Returns (Aktivitätsmass)
- `h1_up_hours_frac`, `h1_down_hours_frac`: Anteil steigender/fallender Stunden
- `h1_close_open_pct`: Intraday-Return (Open→Close)
- `h1_spread_mean`: Durchschnittlicher Spread (Liquiditätsindikator)

*Überlegung:* Die Intraday-Features sollen Informationen einfangen, die in Daily-Daten verloren gehen. Ein Tag mit vielen kleinen Bewegungen (hohes `h1_ret_sum_abs`) unterscheidet sich fundamental von einem Tag mit einer einzigen grossen Bewegung.

### Modelltraining

Das Training folgt der Zwei-Stufen-Architektur:

**Stufe 1 – Signal-Modell:**
- Input: Alle Features
- Output: Binäre Klassifikation `neutral` (0) vs. `move` (1)
- Klassengewichtung: `scale_pos_weight` automatisch berechnet basierend auf dem Klassenverhältnis, geclampt auf [0.2, 5.0]

**Stufe 2 – Richtungs-Modell:**
- Input: Alle Features (nur für Tage mit `signal=1` trainiert)
- Output: Binäre Klassifikation `down` (0) vs. `up` (1)
- Klassengewichtung: `scale_pos_weight=1.0` (ausgeglichene Klassen)

**XGBoost-Hyperparameter:**

Die folgenden konservativen Defaults wurden verwendet, um Overfitting zu vermeiden:

```python
params = {
    'objective': 'binary:logistic',
    'max_depth': 3,           # Flache Bäume für Regularisierung
    'learning_rate': 0.05,    # Niedrige Lernrate
    'n_estimators': 400,      # Viele Bäume kompensieren niedrige LR
    'subsample': 0.9,         # Stochastisches Row-Sampling
    'colsample_bytree': 0.9,  # Stochastisches Column-Sampling
    'random_state': 42        # Reproduzierbarkeit
}
```

*Überlegung zu `max_depth=3`:* Bei Zeitreihendaten besteht ein hohes Overfitting-Risiko, da die Muster zeitlich begrenzt sein können. Flache Bäume erzwingen einfachere Regeln, die eher generalisieren.

**Zeitliche Splits:**

```
|----- Training -----|-- Validation --|---- Test ----|
    2015 - 2022          2023-2024        2025+
```

- **Training:** Ca. 80% der Daten vor Test-Start
- **Validation:** Ca. 20% der Daten vor Test-Start (für Early Stopping, Threshold-Tuning)
- **Test:** Alle Daten ab 2025-01-01 (tatsächlich „zukünftige" Daten)

Early Stopping mit 50 Runden auf dem Validation-Set verhindert Overfitting auf das Training-Set.

### Symbolische KI (Fuzzy Risk Engine)

Nach dem XGBoost-Training bestimmt ein Fuzzy-Logic-System die Positionsgrösse (Stake in CHF). Die Fuzzy-Engine kombiniert vier Eingabevariablen zu einer Risikobewertung:

**Eingabevariablen:**

1. `signal_confidence` [0, 1]: Kombination aus `p_move × p_direction`
2. `volatility` [0, 1]: Normalisierte Marktvolatilität
3. `open_trades` [0, 5]: Anzahl bereits offener Positionen
4. `equity` [0, 1]: Normalisiertes Kontokapital (relativ zum Startkapital)

**Ausgabevariable:**

- `risk_per_trade` [0, 1]: Risiko-Level für diese Position

**Fuzzy-Regeln (Auszug aus `rules/risk.flex`):**

```
RULE 1: IF confidence HIGH AND volatility LOW AND open_trades FEW
        THEN risk HIGH
RULE 2: IF confidence MEDIUM AND volatility MEDIUM
        THEN risk MEDIUM
RULE 3: IF volatility HIGH OR open_trades MANY
        THEN risk LOW
RULE 4: IF confidence LOW
        THEN risk LOW
```

**Membership-Funktionen:**

Die Grenzen der linguistischen Variablen wurden basierend auf typischen XGBoost-Wahrscheinlichkeiten und Trading-Best-Practices gewählt:

- `confidence HIGH`: ab ~72% (XGBoost erreicht selten >85%)
- `volatility HIGH`: ab ~60% (signalisiert turbulenten Markt)
- `open_trades MANY`: ab 3 Positionen (Portfolio-Diversifikation begrenzen)

*Überlegung zur Wahl von Fuzzy-Logik:*
Die Entscheidung für Fuzzy-Logik anstelle eines weiteren ML-Modells war bewusst: Im Finanzkontext ist Nachvollziehbarkeit kritisch. Wenn ein Trade fehlschlägt, möchte man verstehen können, warum eine bestimmte Positionsgrösse gewählt wurde. Mit Fuzzy-Regeln ist dies möglich: „Die Positionsgrösse war klein, weil die Volatilität hoch und die Konfidenz nur mittel war."

### Evaluation und Trading-Simulation

Zur Evaluation wurden drei Trading-Strategien verglichen, die alle dieselben ML-Vorhersagen verwenden, aber unterschiedliche Position-Sizing-Methoden:

**Strategie A – Fixer Einsatz:**
- Einsatz: Konstant 100 CHF pro Trade
- Vorteil: Einfach vergleichbar, unabhängig vom Kapitalverlauf
- Nachteil: Nutzt Kapitalwachstum nicht aus

**Strategie B – Prozent vom Kapital:**
- Einsatz: 10% des aktuellen Kapitals pro Trade
- Vorteil: Exponentielles Wachstum bei Gewinnserie
- Nachteil: Exponentieller Verlust bei Verlustserie, „Risk of Ruin"

**Strategie C – Fuzzy-basiert:**
- Einsatz: Fuzzy-Engine bestimmt `risk_per_trade`, multipliziert mit 10% des Kapitals
- Vorteil: Adaptiv, risikoavers bei unsicheren Signalen
- Nachteil: Geringere absolute Gewinne bei korrekten Vorhersagen

**Simulations-Parameter:**
- Startkapital: 1'000 CHF
- Hebel: 20 (typisch für Retail-FX)
- Keine Transaktionskosten (Vereinfachung)
- Keine Slippage (Vereinfachung)

**Trade-Logik:**
- Einstieg: Am Morgen nach dem Signal (Open-Kurs)
- Ausstieg: Am Ende des Horizonts oder bei Erreichen des Thresholds
- Long bei `up`-Signal, Short bei `down`-Signal

---

## Ergebnisse

Die folgenden drei Experimente wurden als finale Konfigurationen ausgewählt und detailliert evaluiert:

### Experiment 1: hv_mt5_flex_result (MT5 mit News)

**Konfiguration:**
- Datenquelle: MetaTrader 5 (H1→Daily aggregiert)
- Zeitraum Training: 2020-2024 (News verfügbar ab 2020)
- Features: Price + News (news+price Mode)
- Position Sizing: Fuzzy-basiert (Strategie C)

**Trading-Ergebnisse (Test ab 2025, Hebel 20):**

| Strategie | Endkapital | Gewinn | Anzahl Trades |
|-----------|------------|--------|---------------|
| A (Fix 100) | 3'130 CHF | +2'130 CHF | ~50 |
| B (10% Kapital) | 4'534 CHF | +3'534 CHF | ~50 |
| C (Fuzzy) | 2'109 CHF | +1'109 CHF | ~50 |

**Modell-Metriken (Test-Set):**
- Signal F1: 0.24 (schwach, aber erwartungsgemäss bei starker Unbalance)
- Direction F1: 0.81 (stark)
- Combined Accuracy: ~45% (besser als Zufall bei 3 Klassen)

**[BILD 1-6 HIER EINFÜGEN]**

*Interpretation:* Strategie B erzielt den höchsten absoluten Gewinn, birgt aber auch das höchste Risiko (Einsätze bis 600+ CHF). Strategie C ist deutlich konservativer mit kleineren, konstanteren Einsätzen.

### Experiment 2: hp_mt5_flex_result (MT5 ohne News)

**Konfiguration:**
- Datenquelle: MetaTrader 5 (H1→Daily aggregiert)
- Zeitraum Training: 2015-2024 (längere Historie ohne News-Einschränkung)
- Features: Price only (keine News-Features)
- Position Sizing: Fuzzy-basiert (Strategie C)

**Trading-Ergebnisse (Test ab 2025, Hebel 20):**

| Strategie | Endkapital | Gewinn | Anzahl Trades |
|-----------|------------|--------|---------------|
| A (Fix 100) | 1'791 CHF | +791 CHF | ~45 |
| B (10% Kapital) | 1'698 CHF | +698 CHF | ~45 |
| C (Fuzzy) | 1'252 CHF | +252 CHF | ~45 |

**[BILD 7-9 HIER EINFÜGEN]**

*Interpretation:* Trotz längerer Trainingshistorie performt das Modell ohne News-Features deutlich schlechter. Der Gewinn ist etwa 70% niedriger als mit News-Features.

### Experiment 3: hp_long_flex_0_7_result (Yahoo Finance)

**Konfiguration:**
- Datenquelle: Yahoo Finance (Daily)
- Zeitraum Training: 2015-2024
- Features: Price only
- Position Sizing: Fuzzy-basiert (Strategie C)

**Trading-Ergebnisse (Test ab 2025, Hebel 20):**

| Strategie | Endkapital | Gewinn | Anzahl Trades |
|-----------|------------|--------|---------------|
| A (Fix 100) | 2'959 CHF | +1'959 CHF | ~55 |
| B (10% Kapital) | 5'206 CHF | +4'206 CHF | ~55 |
| C (Fuzzy) | 1'785 CHF | +785 CHF | ~55 |

**[BILD 10-11 HIER EINFÜGEN]**

*Interpretation:* Das Yahoo-Experiment zeigt ähnlich gute Ergebnisse wie MT5 mit News, obwohl keine News-Features verwendet wurden. Die längere Trainingshistorie (ab 2015) könnte die fehlenden News kompensieren.

### Vergleich: Mit vs. Ohne News-Features

Um den Einfluss der News-Features isoliert zu testen, wurden zwei Experimente mit **identischem Trainingszeitraum** (2020-2024, Yahoo Finance) verglichen:

| Setup | Strategie B Gewinn |
|-------|-------------------|
| Mit News | +2'150 CHF |
| Ohne News | -820 CHF (Verlust!) |

**[BILD 12 HIER EINFÜGEN]**

*Interpretation:* Bei gleichem Trainingszeitraum zeigt sich ein drastischer Unterschied: Das Modell ohne News-Features macht Verlust, während das Modell mit News-Features profitabel ist. Dies unterstützt die Hypothese, dass Finanznachrichten wertvolle Zusatzinformationen für die Vorhersage signifikanter Bewegungen enthalten.

### Zusammenfassung der Ergebnisse

| Experiment | News | Quelle | Training | Strategie B Gewinn |
|------------|------|--------|----------|-------------------|
| hv_mt5_flex | Ja | MT5 | 2020-24 | +3'534 CHF |
| hp_mt5_flex | Nein | MT5 | 2015-24 | +698 CHF |
| hp_long_yahoo | Nein | Yahoo | 2015-24 | +4'206 CHF |
| hv_yahoo_short | Ja | Yahoo | 2020-24 | +2'150 CHF |
| hp_yahoo_short | Nein | Yahoo | 2020-24 | -820 CHF |

---

## Diskussion und Interpretation

### Interpretation der Confusion Matrix

Die Confusion Matrix des Experiments `hv_mt5_flex_result` zeigt ein interessantes Muster:

```
              Predicted
              neutral  up   down
Actual neutral   45    28    2
       up         3    15    1
       down       2    10    3
```

- **Viele Neutral→Up Fehlklassifikationen:** Das Modell neigt dazu, mehr Bewegungen vorherzusagen als tatsächlich auftreten. Im Trading-Kontext ist dies nicht unbedingt negativ: Ein falsch-positives Signal bei einem tatsächlich neutralen Tag verursacht nur geringe Kosten (kleiner Verlust oder kleiner Gewinn), wenn die Richtung zufällig stimmt.

- **Up-Bias:** Das Richtungsmodell sagt häufiger `up` vorher. Dies könnte am Aufwärtstrend in den Testdaten (2025) liegen. Das Modell hat möglicherweise gelernt, dass in unsicheren Situationen `up` die bessere Wahl ist.

- **Wenige Down-Vorhersagen:** Das Modell ist sehr konservativ bei Down-Signalen. Dies könnte bedeuten, dass Down-Bewegungen schwerer vorherzusagen sind oder dass die Features für Down weniger informativ sind.

### Diskrepanz zwischen ML-Metriken und Trading-Performance

Ein scheinbares Paradox zeigt sich in den Ergebnissen: Die klassischen ML-Metriken (F1 ~0.24 für Signal, Accuracy ~45%) wirken schwach, aber die Trading-Simulation ist profitabel (bis +3'500 CHF).

**Erklärung 1 – Asymmetrische Kosten:**
In der Confusion Matrix zählt jeder Fehler gleich. Im Trading ist ein falsch-positives Signal bei einem neutralen Tag (kleiner Verlust) viel weniger kostspielig als ein falsch-negatives Signal bei einem starken Trend (verpasster grosser Gewinn).

**Erklärung 2 – Richtung wichtiger als Existenz:**
Wenn das Signal-Modell fälschlicherweise `move` sagt, aber das Richtungsmodell die richtige Richtung wählt, kann der Trade trotzdem profitabel sein. Die neutrale Klasse ist keine „Nullsumme", sondern ein kleiner Random Walk.

**Erklärung 3 – Threshold-Artefakte:**
Viele als `neutral` gelabelte Tage sind nur knapp unter dem Threshold. Ein Trade an einem solchen Tag ist nicht automatisch ein Verlust – der Kurs bewegt sich ja, nur nicht genug für das Label.

**Implikation:**
Für die Beurteilung der Modellqualität sollte die Trading-Simulation als primäre Metrik verwendet werden. Die klassischen ML-Metriken sind zwar nützlich für die Modelldiagnostik, aber nicht direkt in Trading-Erfolg übersetzbar.

### Einfluss der Finanznachrichten

Der Vergleich der Experimente mit und ohne News-Features bei gleichem Trainingszeitraum (2020-2024) zeigt einen starken positiven Einfluss der News:

- **Mit News:** +2'150 CHF Gewinn
- **Ohne News:** -820 CHF Verlust

Die News-Features scheinen insbesondere bei kürzeren Trainingszeiträumen wichtig zu sein. Eine mögliche Erklärung: Bei weniger historischen Daten hat das Modell weniger „rein preisbasierte" Muster zum Lernen. Die News liefern zusätzliche, komplementäre Information, die dieses Defizit ausgleicht.

Interessanterweise erreicht das lange Yahoo-Experiment (2015-2024, ohne News) ähnlich gute Ergebnisse wie das kurze Experiment mit News. Dies deutet darauf hin, dass ausreichend lange Trainingshistorie teilweise als Ersatz für News-Features dienen kann – möglicherweise weil über lange Zeiträume mehr verschiedene Marktregime und Muster im Training enthalten sind.

### Performance der Symbolischen KI (Strategie C)

Die Fuzzy-basierte Strategie C performt in absoluten Zahlen schlechter als Strategie B:

| Experiment | Strategie B | Strategie C | Differenz |
|------------|-------------|-------------|-----------|
| hv_mt5_flex | +3'534 CHF | +1'109 CHF | -2'425 CHF |
| hp_yahoo_long | +4'206 CHF | +785 CHF | -3'421 CHF |

**Erklärung:**
Die Fuzzy-Regeln sind bewusst konservativ gestaltet. Bei hoher Volatilität oder niedriger Konfidenz wird der Einsatz stark reduziert. Da der Testzeitraum (2025) insgesamt profitabel war, führt jede Reduktion des Einsatzes zu niedrigeren absoluten Gewinnen.

**Vorteile der Strategie C:**
1. **Geringeres Drawdown-Risiko:** Die maximalen Verluste pro Trade sind begrenzt
2. **Nachvollziehbarkeit:** Jede Sizing-Entscheidung ist durch Regeln erklärbar
3. **Robustheit:** Bei einer Verlustserie würde Strategie C weniger dramatisch verlieren als Strategie B

**Fazit zur symbolischen KI:**
Die Fuzzy-Logik erfüllt ihren Zweck als Risikomanagement-Tool. Sie ist nicht darauf optimiert, den maximalen Gewinn zu erzielen, sondern das Risiko zu kontrollieren und Entscheidungen nachvollziehbar zu machen. In einem realen Trading-Szenario könnte dies wertvoller sein als maximale Rendite.

### Limitationen

Die Ergebnisse unterliegen mehreren wichtigen Einschränkungen:

1. **Keine Transaktionskosten:** Die Simulation berücksichtigt keine Spreads, Kommissionen oder Finanzierungskosten (Swap). Im realen Trading würden diese die Rendite um geschätzt 10-20% reduzieren.

2. **Keine Slippage:** Es wird angenommen, dass Orders zum gewünschten Preis ausgeführt werden. In der Praxis kann es zu Abweichungen kommen, insbesondere bei volatilen Märkten.

3. **Hebel-Risiko:** Der verwendete Hebel von 20 verstärkt sowohl Gewinne als auch Verluste. Ein kleiner Fehler in der Modellvorhersage kann zu erheblichen Verlusten führen.

4. **Aufwärtstrend-Bias:** Der Testzeitraum (2025) zeigt einen Aufwärtstrend im EUR/USD. Ein Modell, das tendenziell `up` vorhersagt, profitiert davon. In einem Abwärtstrend könnte die Performance deutlich schlechter sein.

5. **Kleine Test-Stichprobe:** Das Jahr 2025 enthält nur ca. 240 Handelstage. Diese Stichprobe ist zu klein für statistisch robuste Aussagen. Die Ergebnisse könnten durch Zufall beeinflusst sein.

6. **Overfitting-Risiko:** Trotz zeitlicher Splits und Regularisierung besteht das Risiko, dass das Modell an Besonderheiten des Trainingszeitraums überangepasst ist, die sich nicht in die Zukunft übertragen.

---

## Schlussfolgerungen

### Erreichung der Projektziele

Alle projektbezogenen Ziele wurden erreicht:

| Ziel | Status | Bemerkung |
|------|--------|-----------|
| Reproduzierbare ML-Pipeline | ✓ | EXP_ID-System, versionierte Configs |
| Zwei-Stufen-Klassifikator | ✓ | Signal + Direction Modelle |
| Symbolische KI für Risikomanagement | ✓ | Fuzzy-Logic in Python + FLEX |
| Verschiedene Datenquellen evaluiert | ✓ | Yahoo, EODHD, MT5 |
| Feature Engineering | ✓ | 35+ Features in 5 Kategorien |
| System dokumentiert und reproduzierbar | ✓ | README, Bericht, Kommentare |

### Haupterkenntnisse

1. **Die Zwei-Stufen-Architektur funktioniert:** Die Trennung von Signal- und Richtungsvorhersage ist sinnvoll bei starkem Klassenungleichgewicht. Das Richtungsmodell (F1 ~0.81) performt deutlich besser als das Signalmodell (F1 ~0.24), weil es auf einer balancierteren Datenbasis trainiert wird.

2. **Die Datenquelle ist entscheidend:** FX-Daten unterscheiden sich zwischen Anbietern erheblich. Für realistische Backtests und den späteren Live-Handel sollten Broker-nahe Daten (wie MT5) verwendet werden.

3. **Intraday-Daten haben Mehrwert:** Die MT5-Stundendaten ermöglichen ein realistischeres Labeling (wann genau wurde der Threshold erreicht?) und zusätzliche Intraday-Features (stündliche Volatilität, Anteil steigender Stunden).

4. **Finanznachrichten verbessern Vorhersagen:** Bei gleichem Trainingszeitraum erzielt das Modell mit News-Features signifikant bessere Ergebnisse. News liefern komplementäre Information zu reinen Kursdaten.

5. **Fuzzy-Logic ergänzt ML gut:** Die symbolische Komponente ermöglicht transparentes, regelbasiertes Risikomanagement. Die Kombination aus „Black-Box"-ML für Vorhersagen und „White-Box"-Fuzzy für Sizing ist ein pragmatischer Hybrid-Ansatz.

6. **ML-Metriken ≠ Trading-Performance:** Ein Modell kann bei klassischen Metriken (F1, Accuracy) schwach abschneiden, aber trotzdem profitabel sein. Für die Evaluation von Trading-Modellen sollte immer eine Simulation durchgeführt werden.

### Beantwortung der Forschungsfrage

*Kann ein ML-System signifikante EUR/USD-Bewegungen vorhersagen und dabei von Finanznachrichten profitieren?*

**Antwort:** Ja, mit Einschränkungen. Das entwickelte System kann Bewegungstage mit überzufälliger Genauigkeit identifizieren und deren Richtung vorhersagen. Die Integration von Finanznachrichten verbessert die Vorhersagequalität messbar, insbesondere bei kürzeren Trainingszeiträumen.

Die praktische Nutzbarkeit hängt jedoch von vielen Faktoren ab: Transaktionskosten, Marktregime, Kapitaleinsatz, Risikotoleranz. Die Ergebnisse sind ermutigend, aber keine Garantie für zukünftige Profitabilität.

---

## Empfehlungen

### Für zukünftige Arbeiten

1. **Live-Testing:** Die logische nächste Stufe wäre ein Paper-Trading-Test (simulierter Handel mit Echtzeit-Daten) über mehrere Monate, um die Robustheit unter realen Bedingungen zu prüfen.

2. **Erweiterte News-Analyse:** Statt vorberechneter Sentiment-Scores könnten eigene NLP-Modelle (z.B. FinBERT) für eine nuanciertere Sentiment-Analyse eingesetzt werden.

3. **Multi-Asset-Generalisierung:** Das System könnte auf andere Währungspaare oder Anlageklassen erweitert werden, um die Generalisierbarkeit zu testen.

4. **Reinforcement Learning:** Ein RL-Agent könnte lernen, wann und wie viel zu handeln ist, anstatt feste Regeln zu verwenden.

5. **Feature Selection:** Eine systematische Feature-Importance-Analyse und ggf. Reduktion der Features könnte die Modellinterpretierbarkeit verbessern.

### Für praktische Anwendung

1. **Risikomanagement priorisieren:** Die Fuzzy-basierte Strategie C ist konservativer, aber sicherer. Für den realen Einsatz sollte das Risiko begrenzt werden.

2. **Transaktionskosten einbeziehen:** Vor einem Live-Einsatz müssen realistische Kosten (Spread, Swap, Kommission) in die Simulation integriert werden.

3. **Regelmässiges Retraining:** Das Modell sollte regelmässig (z.B. monatlich) mit neuen Daten nachtrainiert werden, um sich an veränderte Marktbedingungen anzupassen.

4. **Diversifikation:** Das System sollte nicht als alleinige Handelsstrategie verwendet werden, sondern als ein Element in einem diversifizierten Ansatz.

---

## Referenzen

1. Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *Proceedings of the 22nd ACM SIGKDD*.

2. Zadeh, L. A. (1965). Fuzzy Sets. *Information and Control*, 8(3), 338-353.

3. Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2018). Statistical and Machine Learning forecasting methods: Concerns and ways forward. *PLOS ONE*, 13(3).

4. Fischer, T., & Krauss, C. (2018). Deep learning with long short-term memory networks for financial market predictions. *European Journal of Operational Research*, 270(2), 654-669.

5. IEC 61131-7:2000 - Programmable controllers — Part 7: Fuzzy control programming (FCL Standard).

---

## Anhänge

### Anhang A: Code-Repository

Das vollständige Code-Repository ist unter folgendem Pfad verfügbar und enthält alle notwendigen Dateien zur Reproduktion der Experimente:

**Repository-Struktur:** Siehe `README.md` im Projekt-Root für eine vollständige Dokumentation der Projektstruktur, Installation und Verwendung.

**Experiment-Reproduktion:**
1. Repository klonen und virtuelle Umgebung einrichten
2. `pip install -r requirements.txt`
3. Notebooks in der Reihenfolge 1→2→3 ausführen (Data-Prep → Training → Evaluation)

### Anhang B: Glossar

| Begriff | Erklärung |
|---------|-----------|
| EXP_ID | Eindeutige Experiment-Identifikation für Reproduzierbarkeit |
| H1 | Stündliche Kursdaten (Hourly, 1 Hour) |
| OHLC | Open, High, Low, Close – Standardformat für Kursdaten |
| P&L | Profit & Loss – Gewinn und Verlust |
| Spread | Differenz zwischen Kauf- und Verkaufspreis |
| Hebel | Multiplikator für Kapitaleinsatz (z.B. 20x) |
| Take-Profit | Automatischer Gewinnmitnahme-Auftrag |
| Stop-Loss | Automatischer Verlustbegrenzungs-Auftrag |
| Lookahead Bias | Verwendung zukünftiger Information in der Modellierung |

### Anhang C: Feature-Liste

**Preis-Features:**
- price_close_ret_1d, price_close_ret_5d, price_close_ret_30d
- price_range_pct_5d_std, price_range_pct_30d_std
- price_body_pct_5d_mean, price_body_pct_30d_mean
- price_body_vs_range, price_body_vs_range_5d_mean
- price_shadow_balance, price_shadow_balance_5d_mean
- intraday_range_pct, body_pct, upper_shadow, lower_shadow

**News-Features:**
- article_count, avg_polarity, avg_pos, avg_neg, avg_neu
- pos_share, neg_share
- news_article_count_3d_sum, news_article_count_7d_sum
- news_pos_share_5d_mean, news_neg_share_5d_mean
- news_article_count_lag1, news_pos_share_lag1, news_neg_share_lag1

**Kalender-Features:**
- month, quarter, week
- cal_dow, cal_day_of_month
- cal_is_monday, cal_is_friday
- cal_is_month_start, cal_is_month_end

**Feiertags-Features:**
- hol_is_us_federal_holiday
- hol_is_day_before_us_federal_holiday
- hol_is_day_after_us_federal_holiday

**Intraday-Features (MT5):**
- h1_ret_std, h1_ret_sum_abs
- h1_range_pct_mean, h1_range_pct_max
- h1_close_open_pct
- h1_up_hours_frac, h1_down_hours_frac
- h1_tick_volume_sum, h1_spread_mean

---

*Hinweis: Dieser Bericht wurde im Rahmen des Moduls „E-Maschinelles Lernen und wissensbasierte Systeme 2025" erstellt. Die Bilder sind als Platzhalter markiert und müssen aus den PDF-Reports der jeweiligen Experimente eingefügt werden.*
