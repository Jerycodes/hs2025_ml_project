#!/usr/bin/env bash
# Shebang:
# Gibt an, welches Programm zum Ausführen dieses Scripts verwendet werden soll.
# In diesem Fall wird über 'env' das Programm 'bash' gesucht und verwendet.
# Vorteil: erhöhte Portabilität auf verschiedenen Systemen.

set -e
# Konfiguriert die Shell so, dass das Script sofort beendet wird,
# sobald ein ausgeführter Befehl einen Fehler (Exit Code ≠ 0) auslöst.
# Dadurch werden fehlerhafte Datenpipelines verhindert.

echo "[script] Starte fetch_finance.sh..."
# Log-Ausgabe zur Orientierung: zeigt an, dass das Script gestartet wurde.

echo "[script] Aktiviere virtuelle Umgebung..."
# Log-Ausgabe zur Information über den nächsten Schritt.

source .venv/bin/activate
# Aktiviert die Python Virtual Environment (venv).
# Dadurch werden alle Python-Befehle (python, pip) innerhalb dieser Umgebung ausgeführt.
# Vorteil: reproduzierbare Paketversionen und klare Trennung von System-Python.

echo "[script] Starte Python Loader für Finanzdaten..."
# Log-Ausgabe zur Orientierung: die Datenlade-Prozedur beginnt.

python -m src.data.load_finance
# Führt das Python-Modul 'src.data.load_finance' aus.
# '-m' bewirkt, dass Python das Modul wie ein Script startet.
# Das Modul:
#   - lädt die Konfigurationsdatei (symbols.yaml)
#   - liest Symbollisten (equities und fx)
#   - lädt Finanzdaten über yfinance
#   - speichert CSV-Dateien unter data/raw/<Kategorie>

echo "[script] Fertig. Daten wurden unter data/raw/ gespeichert."
# Abschließende Log-Ausgabe, die signalisiert, dass das Script erfolgreich durchgelaufen ist.