# MT5 EURUSD Historie → Projektformat

## 1) In MT5 exportieren (chunked)

- Script: `tools/mt5/ExportRates_Chunked.mq5`
- In MetaEditor nach `MQL5/Scripts/` kopieren, kompilieren, dann in MT5 starten.
- Default-Output:
  - `InpUseCommonFolder=true` ⇒ Datei landet unter **Common\\Files**
  - Spalten: `time_unix,time,open,high,low,close,tick_volume,spread,real_volume`

Tipp: In MT5 **File → Open Data Folder** und dort zu `.../Common/Files` navigieren.

## 2) Ins Projekt importieren (Daily OHLCV)

Konvertiert z.B. ein M1-Export zu Daily-OHLCV im Projektformat:

```bash
python3 -m scripts.import_mt5_rates --in /path/to/Common/Files/EURUSD_M1_2020_2025.csv
```

Hinweis: Wenn du über `View → Symbols → Bars → Export Bars` exportierst, ist die Datei
je nach MT5-Version oft TAB-separiert und hat Header wie `<DATE> <OPEN> ...`.
`scripts/import_mt5_rates.py` erkennt das automatisch.

Default-Output:
- `data/raw/fx/EURUSD_mt5_D1.csv` mit Spalten: `Date,Open,High,Low,Close,Volume`

Optional:
- Wochenenden entfernen: `--drop-weekends`
- weniger RAM: `--chunksize 200000`

## 3) In der Pipeline verwenden

In den Label-Funktionen als Quelle wählen:
- `price_source="mt5"` (liest `data/raw/fx/EURUSD_mt5_D1.csv`)
