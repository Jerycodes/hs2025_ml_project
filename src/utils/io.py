from pathlib import Path  # Path sorgt für OS-neutrale Pfad-Operationen.

DATA_DIR = Path("data")  # Wurzel für alle Projektdaten.
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"

# Verzeichnisse anlegen, falls sie fehlen – verhindert Laufzeitfehler bei Downloads.
for path in (DATA_RAW, DATA_PROCESSED):
    path.mkdir(parents=True, exist_ok=True)
