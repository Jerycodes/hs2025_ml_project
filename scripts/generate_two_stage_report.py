"""Erzeugt einen PDF-Report für ein Zwei-Stufen-XGBoost-Experiment.

Der Report fasst die wichtigsten Metadaten und Metriken zusammen und
speichert sie als mehrseitiges PDF im Ordner ``notebooks/results``.

Verwendung (aus Projektwurzel):

    python3 -m scripts.generate_two_stage_report --exp-id v1_h4_thr0p5pct_strict

Voraussetzungen:
- Data-Prep-Notebook wurde für diese EXP_ID ausgeführt
  -> es existiert data/processed/experiments/<EXP_ID>_config.json
- Trainings-Notebook wurde für diese EXP_ID ausgeführt
  -> es existiert notebooks/results/two_stage__<EXP_ID>.json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import textwrap
from typing import Dict, Any

# Matplotlib schreibt Cache/Font-Cache. In manchen Umgebungen ist ~/.matplotlib nicht beschreibbar.
# /tmp ist typischerweise beschreibbar und verhindert Warnungen/Probleme beim PDF-Rendern.
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

# Headless / server-friendly backend (verhindert GUI-Backends, die in manchen Umgebungen crashen).
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import seaborn as sns

from src.models.train_xgboost_two_stage import (
    split_train_val_test,
    build_signal_targets,
    train_xgb_binary,
    get_feature_cols,
)


# Beschreibungen der wichtigsten Features für die Feature-Seite
FEATURE_DESCRIPTIONS = {
    "article_count": "Anzahl News-Artikel an Tag t.",
    "avg_polarity": "Durchschnittliche Sentiment-Polarity der Artikel an Tag t (VADER).",
    "avg_neg": "Durchschnittlicher negativer Sentiment-Anteil an Tag t.",
    "avg_neu": "Durchschnittlicher neutraler Sentiment-Anteil an Tag t.",
    "avg_pos": "Durchschnittlicher positiver Sentiment-Anteil an Tag t.",
    "pos_share": "Anteil positiver Sentiment-Komponente: avg_pos / (avg_pos + avg_neg).",
    "neg_share": "Anteil negativer Sentiment-Komponente: avg_neg / (avg_pos + avg_neg).",
    "intraday_range_pct": "(High - Low) / Close – relative Tagesvolatilität.",
    "upper_shadow": "Oberer Kerzendocht: High - max(Open, Close).",
    "lower_shadow": "Unterer Kerzendocht: min(Open, Close) - Low.",
    "price_close_ret_1d": "Relativer Schlusskurs-Return gegenüber Vortag: Close_t / Close_{t-1} - 1.",
    "price_close_ret_5d": "Schlusskurs-Return über 5 Tage: Close_t / Close_{t-5} - 1.",
    "price_range_pct_5d_std": "Standardabweichung der intraday_range_pct über 5 Tage (Volatilität).",
    "price_body_pct_5d_mean": "Durchschnittlicher Kerzenkörper-Prozentsatz über 5 Tage.",
    "price_close_ret_30d": "Schlusskurs-Return über 30 Tage: Close_t / Close_{t-30} - 1.",
    "price_range_pct_30d_std": "Standardabweichung der intraday_range_pct über 30 Tage.",
    "price_body_pct_30d_mean": "Durchschnittlicher Kerzenkörper-Prozentsatz über 30 Tage.",
    "news_article_count_3d_sum": "Summe article_count über die letzten 3 Tage.",
    "news_article_count_7d_sum": "Summe article_count über die letzten 7 Tage.",
    "news_pos_share_5d_mean": "Durchschnittlicher pos_share über die letzten 5 Tage.",
    "news_neg_share_5d_mean": "Durchschnittlicher neg_share über die letzten 5 Tage.",
    "news_article_count_lag1": "article_count am Vortag.",
    "news_pos_share_lag1": "pos_share am Vortag.",
    "news_neg_share_lag1": "neg_share am Vortag.",
    "month": "Kalendermonat (1–12).",
    "quarter": "Kalenderquartal (1–4).",
    "cal_dow": "Wochentag (0 = Montag, 6 = Sonntag).",
    "cal_day_of_month": "Kalendertag im Monat.",
    "cal_is_monday": "Flag: 1 wenn Montag, sonst 0.",
    "cal_is_friday": "Flag: 1 wenn Freitag, sonst 0.",
    "cal_is_month_start": "Flag: 1 wenn Monatsanfang, sonst 0.",
    "cal_is_month_end": "Flag: 1 wenn Monatsende, sonst 0.",
    "hol_is_us_federal_holiday": "Flag: 1 wenn US-Feiertag, sonst 0.",
    "hol_is_day_before_us_federal_holiday": "Flag: 1 wenn Tag vor US-Feiertag.",
    "hol_is_day_after_us_federal_holiday": "Flag: 1 wenn Tag nach US-Feiertag.",
    "lookahead_return": "Return über den Label-Horizont (z.B. t..t+4).",
    # Intraday (MT5 H1 -> Daily) derived features
    "h1_ret_std": "Standardabweichung der stündlichen Returns innerhalb eines Tages (aus H1).",
    "h1_ret_sum_abs": "Summe der absoluten stündlichen Returns innerhalb eines Tages (aus H1).",
    "h1_range_pct_mean": "Mittlere stündliche Kerzenspanne (High-Low)/Close innerhalb des Tages (aus H1).",
    "h1_range_pct_max": "Maximale stündliche Kerzenspanne (High-Low)/Close innerhalb des Tages (aus H1).",
    "h1_close_open_pct": "Tages-Return auf H1-Basis: Close(last)/Open(first) - 1 (pro Session/Cut).",
    "h1_up_hours_frac": "Anteil Stunden im Tag mit Close > Open (aus H1).",
    "h1_down_hours_frac": "Anteil Stunden im Tag mit Close < Open (aus H1).",
    "h1_tick_volume_sum": "Summe Tick-Volume über alle Stunden im Tag (aus H1).",
    "h1_spread_mean": "Durchschnittlicher Spread über die Stunden im Tag (aus H1).",
}


def find_project_root(start: Path | None = None) -> Path:
    """Sucht von ``start`` aus nach oben, bis ein Ordner ``src`` existiert.

    Idee:
    - Wir starten im aktuellen Arbeitsverzeichnis (oder einem expliziten Startpfad).
    - Dann laufen wir nach oben, bis ein Unterordner `src` gefunden wird.
    - Dieser Ordner gilt als Projektwurzel.
    """
    if start is None:
        start = Path.cwd()
    root = start
    while not (root / "src").is_dir():
        if root.parent == root:
            raise RuntimeError("Projektwurzel mit Unterordner 'src' nicht gefunden.")
        root = root.parent
    return root


def load_experiment_files(project_root: Path, exp_id: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Lädt Config- und Ergebnis-JSON für ein Experiment.

    Erwartet:
    - data/processed/experiments/<EXP_ID>_config.json
    - notebooks/results/two_stage__<EXP_ID>.json
    """
    safe_id = exp_id.replace(" ", "_")

    cfg_path = project_root / "data" / "processed" / "experiments" / f"{safe_id}_config.json"
    res_path = project_root / "notebooks" / "results" / f"two_stage__{safe_id}.json"

    if not cfg_path.is_file():
        raise FileNotFoundError(f"Config-Datei nicht gefunden: {cfg_path}")
    if not res_path.is_file():
        raise FileNotFoundError(f"Ergebnis-Datei nicht gefunden: {res_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        exp_config = json.load(f)
    with res_path.open("r", encoding="utf-8") as f:
        results = json.load(f)

    return exp_config, results


def load_training_dataset(project_root: Path, results: Dict[str, Any]) -> pd.DataFrame:
    """Lädt den Trainingsdatensatz, dessen Pfad in results['config']['dataset_path'] steht.

    Der Pfad kann absolut oder relativ zur Projektwurzel sein.
    """
    cfg = results.get("config", {})
    ds_path_str = cfg.get("dataset_path")
    if not ds_path_str:
        raise KeyError("dataset_path fehlt im results['config']-Block.")
    ds_path = Path(ds_path_str)
    if not ds_path.is_file():
        # Falls der Pfad relativ gespeichert wurde, relativ zur Projektwurzel interpretieren
        ds_path = (project_root / ds_path).resolve()
    if not ds_path.is_file():
        raise FileNotFoundError(f"Trainingsdatensatz nicht gefunden: {ds_path}")

    df = pd.read_csv(ds_path, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def load_predictions(project_root: Path, exp_id: str) -> pd.DataFrame | None:
    """Lädt die Test-Predictions für ein Experiment, falls vorhanden.

    Bevorzugt die Dateien aus dem Final-Workflow:
    notebooks/results/final_two_stage/two_stage_final__<EXP_ID>_predictions.csv

    Fällt zurück auf eine ggf. vorhandene ältere Datei
    notebooks/results/two_stage_predictions__<EXP_ID>.csv.
    """
    results_dir = project_root / "notebooks" / "results"
    final_dir = results_dir / "final_two_stage"
    safe_id = exp_id.replace(" ", "_")

    candidates = [
        final_dir / f"two_stage_final__{safe_id}_predictions.csv",
        results_dir / f"two_stage_predictions__{safe_id}.csv",
    ]

    for path in candidates:
        if path.is_file():
            df = pd.read_csv(path, parse_dates=["date"])
            return df

    print(f"[warn] Keine Predictions-CSV für EXP_ID='{exp_id}' gefunden – "
          "Fehlklassifikations-Seiten werden übersprungen.")
    return None


def load_fx_labels_for_exp(project_root: Path, exp_id: str) -> pd.DataFrame | None:
    """Lädt die FX-Labels (inkl. Close) für ein Experiment.

    Bevorzugt die Varianten-Datei ``eurusd_labels__<EXP_ID>.csv``,
    fällt ansonsten auf die aktuelle Standarddatei zurück.
    """
    base_dir = project_root / "data" / "processed" / "fx"
    safe_id = exp_id.replace(" ", "_")
    candidates = [
        base_dir / f"eurusd_labels__{safe_id}.csv",
        base_dir / "eurusd_labels.csv",
    ]
    for path in candidates:
        if path.is_file():
            df = pd.read_csv(path, parse_dates=["Date"])
            df = df.sort_values("Date").set_index("Date")
            return df

    print(f"[warn] Keine FX-Label-Datei für EXP_ID='{exp_id}' gefunden – "
          "Tradesimulation wird übersprungen.")
    return None


def add_title_page(pdf: PdfPages, exp_id: str, exp_config: Dict[str, Any], results: Dict[str, Any]) -> None:
    """Fügt eine Titelseite mit den wichtigsten Metadaten und einer Kurzbeschreibung hinzu."""
    cfg = results.get("config", {})
    label_params = exp_config.get("label_params", {})
    data_params = exp_config.get("data_params", {})

    fig = plt.figure(figsize=(8.27, 11.69))  # A4-Hochformat in Zoll
    fig.clf()

    # y steuert die vertikale Position (von oben nach unten)
    y = 0.9
    # kleinerer Zeilenabstand, damit auch bei langen Experiment-IDs/Parametern
    # nichts am unteren Rand abgeschnitten wird.
    line_height = 0.026

    def write(text: str, *, size: int = 8, bold: bool = False, max_width: int = 100) -> None:
        """Hilfsfunktion, um Textzeilen zu schreiben.

        - `text` wird bei Bedarf mit textwrap auf mehrere Zeilen umgebrochen,
          damit nichts am rechten Rand abgeschnitten wird.
        - `max_width` gibt ungefähr die Anzahl Zeichen pro Zeile an.
        """
        nonlocal y
        # Text in mehrere Zeilen umbrechen, falls er zu lang ist
        for line in textwrap.wrap(str(text), width=max_width):
            if bold:
                # etwas weiter nach links rücken (x=0.04)
                fig.text(0.04, y, line, fontsize=size, weight="bold")
            else:
                fig.text(0.04, y, line, fontsize=size)
            y -= line_height

    write("Zwei-Stufen-XGBoost – Experiment-Report", size=16, bold=True)
    write(f"Experiment-ID: {exp_id}", size=12)
    y -= line_height

    write(
        "Dieses Dokument fasst die wichtigsten Parameter, Datenquellen und "
        "Metriken eines Zwei-Stufen-XGBoost-Experiments zusammen.",
        size=10,
    )
    write(
        "Stufe 1 (Signal): neutral vs. Bewegung ('move'). "
        "Stufe 2 (Richtung): down vs. up – nur an Bewegungstagen.",
        size=10,
    )
    y -= line_height

    write("Label-Parameter:", bold=True)
    write(f"- horizon_days: {label_params.get('horizon_days')}")
    write(f"- up_threshold: {label_params.get('up_threshold')}")
    write(f"- down_threshold: {label_params.get('down_threshold')}")
    write(f"- strict_monotonic: {label_params.get('strict_monotonic')}")
    if "max_adverse_move_pct" in label_params:
        write(f"- max_adverse_move_pct: {label_params.get('max_adverse_move_pct')}")
    if "price_source" in label_params:
        write(f"- price_source: {label_params.get('price_source')}")
    if "drop_weekends" in label_params:
        write(f"- drop_weekends: {label_params.get('drop_weekends')}")
    if "hit_within_horizon" in label_params:
        write(
            "- hit_within_horizon: "
            f"{label_params.get('hit_within_horizon')} "
            "(True = Schwelle reicht, wenn sie irgendwo im Horizont erreicht wird)"
        )
    if "first_hit_wins" in label_params:
        write(
            "- first_hit_wins: "
            f"{label_params.get('first_hit_wins')} "
            "(nur relevant bei hit_within_horizon=True: entscheidet nach erstem Treffer)"
        )
    if "hit_source" in label_params:
        write(
            "- hit_source: "
            f"{label_params.get('hit_source')} "
            "(close = nur Schlusskurse, hl = Daily High/Low, h1 = stündliche Bars; h1 approximiert Order innerhalb des Tages)"
        )
    if "intraday_tie_breaker" in label_params:
        write(
            "- intraday_tie_breaker: "
            f"{label_params.get('intraday_tie_breaker')} "
            "(wird genutzt, wenn Up+Down in derselben Kerze getroffen werden und die Reihenfolge nicht bestimmbar ist)"
        )
    y -= line_height

    if data_params:
        write("Daten-Parameter:", bold=True)
        # keep it short; full dump is on the config pages
        for k, v in data_params.items():
            write(f"- {k}: {v}", max_width=90)
        write("(vollständige Config: siehe 'Config Dump' Seiten)", max_width=90)
        y -= line_height

    feature_mode = cfg.get("feature_mode")

    write("Datensatz & Splits:", bold=True)
    # dataset_path kann sehr lang sein → enger umbrechen
    write(f"- dataset_path: {cfg.get('dataset_path')}", max_width=80)
    write(f"- test_start: {cfg.get('test_start')}")
    write(f"- train_frac_within_pretest: {cfg.get('train_frac_within_pretest')}")
    y -= line_height

    if feature_mode:
        write(f"- feature_mode: {feature_mode}", max_width=80)
        y -= line_height

    # Schwellwerte / Entscheidungsgrenzen dokumentieren
    signal_thr = cfg.get("signal_threshold")
    signal_thr_trade = cfg.get("signal_threshold_trade")
    dir_thr = cfg.get("direction_threshold")
    dir_thr_down = cfg.get("direction_threshold_down")
    dir_thr_up = cfg.get("direction_threshold_up")
    if (
        (signal_thr is not None)
        or (signal_thr_trade is not None)
        or (dir_thr is not None)
        or (dir_thr_down is not None)
        or (dir_thr_up is not None)
    ):
        write("Entscheidungsgrenzen (Modelle):", bold=True)
        if signal_thr is not None:
            write(
                f"- SIGNAL_THRESHOLD (Stufe 1 – move vs. neutral): {signal_thr} "
                "(höher → höhere Precision, niedrigerer Recall)."
            )
        if signal_thr_trade is not None:
            write(
                f"- SIGNAL_THRESHOLD_TRADE (Stufe 1 – Trading): {signal_thr_trade} "
                "(höher → weniger Trades, tendenziell höhere Qualität)."
            )
        if dir_thr is not None:
            write(
                f"- DIRECTION_THRESHOLD (Stufe 2 – down vs. up, für Metriken): {dir_thr} "
                "(niedriger → mehr up, höher → weniger up)."
            )
        if (dir_thr_down is not None) or (dir_thr_up is not None):
            write(
                f"- DIRECTION_THRESHOLDS (Stufe 2 – Trading-Entscheidungen): "
                f"down, wenn P(up) ≤ {dir_thr_down}, up, wenn P(up) ≥ {dir_thr_up}."
            )
        y -= line_height

    # Hinweis auf die verwendeten Features; die vollständige Liste ist
    # auf einer separaten Feature-Seite untergebracht, damit auf der
    # Titelseite nichts abgeschnitten wird.
    feature_cols = cfg.get("feature_cols", [])
    if feature_cols:
        write(
            "Features (FEATURE_COLS): vollständige Liste auf der Feature-Seite weiter unten.",
            bold=True,
            max_width=80,
        )

    pdf.savefig(fig)
    plt.close(fig)


def add_features_page(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Fügt Seite(n) mit einer vollständigen Feature-Liste hinzu (mit Pagination).

    So wird sichergestellt, dass alle genutzten Feature-Namen vollständig im Report
    sichtbar sind, auch wenn die Liste länger ist.
    """
    cfg = results.get("config", {})
    feature_cols = cfg.get("feature_cols", [])
    if not feature_cols:
        return

    # Tabelle mit drei Spalten: Index, Feature-Name, kurze Beschreibung
    rows = []
    for i, col in enumerate(feature_cols):
        desc_raw = FEATURE_DESCRIPTIONS.get(col, "")
        # Beschreibung umbrechen, damit nichts am rechten Rand abgeschnitten wird
        if desc_raw:
            desc = "\n".join(textwrap.wrap(desc_raw, width=70))
        else:
            desc = ""
        rows.append([i, col, desc])

    # Pagination: keep the table readable on A4
    rows_per_page = 34
    total_pages = int(np.ceil(len(rows) / rows_per_page))
    for page_idx in range(total_pages):
        chunk = rows[page_idx * rows_per_page : (page_idx + 1) * rows_per_page]
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis("off")
        title = "Verwendete Features (FEATURE_COLS)"
        if total_pages > 1:
            title += f" – Seite {page_idx + 1}/{total_pages}"
        ax.set_title(title, fontsize=12, weight="bold", pad=10)

        table = ax.table(
            cellText=chunk,
            colLabels=["#", "feature_name", "description"],
            loc="center",
            cellLoc="left",
            colWidths=[0.06, 0.34, 0.60],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        table.scale(1.05, 1.15)

        pdf.savefig(fig)
        plt.close(fig)


def add_config_dump_pages(pdf: PdfPages, exp_id: str, exp_config: Dict[str, Any], results: Dict[str, Any]) -> None:
    """Adds paginated config dump pages (prevents clipped text and missing params)."""

    def _dump_pages(title: str, obj: Dict[str, Any]) -> None:
        text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)
        lines: list[str] = []
        for raw in text.splitlines():
            # Wrap long lines (paths) to keep inside page width.
            wrapped = textwrap.wrap(
                raw,
                width=120,
                break_long_words=False,
                break_on_hyphens=False,
                replace_whitespace=False,
                drop_whitespace=False,
            )
            lines.extend(wrapped if wrapped else [""])

        page = 1
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.clf()
        y = 0.965
        fig.text(0.05, y, title, fontsize=12, weight="bold")
        fig.text(0.05, y - 0.025, f"EXP_ID: {exp_id}", fontsize=9)
        y -= 0.055

        line_h = 0.012
        for line in lines:
            if y <= 0.04:
                pdf.savefig(fig)
                plt.close(fig)
                page += 1
                fig = plt.figure(figsize=(8.27, 11.69))
                fig.clf()
                y = 0.965
                fig.text(0.05, y, f"{title} (cont. {page})", fontsize=12, weight="bold")
                fig.text(0.05, y - 0.025, f"EXP_ID: {exp_id}", fontsize=9)
                y -= 0.055

            fig.text(0.05, y, line, fontsize=6.5, family="monospace")
            y -= line_h

        pdf.savefig(fig)
        plt.close(fig)

    _dump_pages("Config Dump – data/processed/experiments/<EXP_ID>_config.json", exp_config)
    cfg = results.get("config", {})
    if isinstance(cfg, dict) and cfg:
        _dump_pages("Config Dump – results['config'] (aus Training-JSON)", cfg)


def add_legend_page(pdf: PdfPages) -> None:
    """Fügt eine Seite mit Erklärungen zu wichtigsten Begriffen und Abkürzungen hinzu."""
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.clf()

    y = 0.9
    # engerer Zeilenabstand für die Legende
    line_height = 0.025

    def write(text: str, *, size: int = 8, bold: bool = False, max_width: int = 100) -> None:
        nonlocal y
        for line in textwrap.wrap(str(text), width=max_width):
            if bold:
                fig.text(0.04, y, line, fontsize=size, weight="bold")
            else:
                fig.text(0.04, y, line, fontsize=size)
            y -= line_height

    write("Legende & Begriffe (Kurzüberblick)", size=14, bold=True)
    y -= line_height

    write("Zielvariablen:", bold=True)
    write("- label: 3-Klassen-Ziel auf Basis des 4-Tage-Lookaheads (neutral / up / down).")
    write("- signal: 0 = neutral, 1 = Bewegung (up oder down).")
    write("- direction: 0 = down, 1 = up; nur definiert, wenn signal == 1.")
    y -= line_height

    write("Wichtige Metriken:", bold=True)
    write("- precision: Anteil der vorhergesagten positiven Fälle, die wirklich positiv sind.")
    write("- recall: Anteil der tatsächlichen positiven Fälle, die erkannt wurden.")
    write("- f1: harmonischer Mittelwert aus precision und recall (Balance beider Größen).")
    write("- support: Anzahl der Beobachtungen in der jeweiligen Klasse.")
    y -= line_height

    write("Feature-Abkürzungen (Auswahl, nicht vollständig – vollständige Liste siehe Seite 'Verwendete Features'):", bold=True)
    write("- article_count: Anzahl News-Artikel pro Tag.")
    write("- avg_polarity / avg_neg / avg_neu / avg_pos: durchschnittliche Sentiment-Werte.")
    write("- pos_share / neg_share: Anteil positiver bzw. negativer Sentiment-Komponente.")
    write("- intraday_range_pct: (High - Low) / Close – relative Tages-Spanne (Volatilität).")
    write("- upper_shadow / lower_shadow: obere/untere Dochte der Kerzen (High/Low vs. Körper).")
    write("- month / quarter: Kalendermonat und Quartal.")
    write("- h1_*: Intraday-Features aus stündlichen MT5-Bars (H1) aggregiert auf Tagesbasis.")

    pdf.savefig(fig)
    plt.close(fig)


def add_model_params_page(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Eigene Seite mit den wichtigsten XGBoost-Parametern für beide Stufen."""
    model_params = results.get("model_params")
    if not model_params:
        return

    fig = plt.figure(figsize=(8.27, 11.69))
    fig.clf()

    y = 0.9
    line_height = 0.03

    def write(text: str, *, size: int = 10, bold: bool = False, max_width: int = 100) -> None:
        nonlocal y
        for line in textwrap.wrap(str(text), width=max_width):
            if bold:
                fig.text(0.04, y, line, fontsize=size, weight="bold")
            else:
                fig.text(0.04, y, line, fontsize=size)
            y -= line_height

    write("Modell-Parameter (XGBoost)", size=14, bold=True)
    y -= line_height

    sig = model_params.get("signal", {})
    dir_params = model_params.get("direction", {})

    write("Signal-Modell (Stufe 1):", bold=True)
    write(f"- objective: {sig.get('objective')}")
    write(f"- max_depth: {sig.get('max_depth')}")
    write(f"- learning_rate: {sig.get('learning_rate')}")
    write(f"- n_estimators: {sig.get('n_estimators')}")
    write(f"- subsample: {sig.get('subsample')}")
    write(f"- colsample_bytree: {sig.get('colsample_bytree')}")
    write(f"- scale_pos_weight: {sig.get('scale_pos_weight')}")
    y -= line_height

    write("Richtungs-Modell (Stufe 2):", bold=True)
    write(f"- objective: {dir_params.get('objective')}")
    write(f"- max_depth: {dir_params.get('max_depth')}")
    write(f"- learning_rate: {dir_params.get('learning_rate')}")
    write(f"- n_estimators: {dir_params.get('n_estimators')}")
    write(f"- subsample: {dir_params.get('subsample')}")
    write(f"- colsample_bytree: {dir_params.get('colsample_bytree')}")
    write(f"- scale_pos_weight: {dir_params.get('scale_pos_weight')}")
    y -= line_height

    mc_params = model_params.get("multiclass")
    if isinstance(mc_params, dict) and mc_params:
        write("Multiclass-Baseline (optional, 3-Klassen):", bold=True)
        write(f"- objective: {mc_params.get('objective')}")
        write(f"- num_class: {mc_params.get('num_class')}")
        write(f"- max_depth: {mc_params.get('max_depth')}")
        write(f"- learning_rate: {mc_params.get('learning_rate')}")
        write(f"- n_estimators: {mc_params.get('n_estimators')}")
        write(f"- subsample: {mc_params.get('subsample')}")
        write(f"- colsample_bytree: {mc_params.get('colsample_bytree')}")

    pdf.savefig(fig)
    plt.close(fig)


def _plot_binary_metrics(pdf: PdfPages, results: Dict[str, Any], key: str, pos_label: str, title: str) -> None:
    """Hilfsfunktion: Balkenplot für Precision/Recall/F1 einer positiven Klasse."""
    metrics = results[key]
    splits = ["train", "val", "test"]

    def _safe_stats(report: Dict[str, Any], label: str) -> Dict[str, float]:
        """Return stats for a class label; fall back to NaN if missing (e.g. empty split / single-class)."""
        if not isinstance(report, dict):
            report = {}
        stats = report.get(label)
        if not isinstance(stats, dict):
            # sklearn's output_dict uses string labels; keep a defensive fallback anyway.
            stats = report.get(str(label))
        if not isinstance(stats, dict):
            return {"precision": float("nan"), "recall": float("nan"), "f1-score": float("nan")}
        return {
            "precision": float(stats.get("precision", float("nan"))),
            "recall": float(stats.get("recall", float("nan"))),
            "f1-score": float(stats.get("f1-score", float("nan"))),
        }

    prec = []
    rec = []
    f1 = []

    for split in splits:
        rep = metrics[split]["report"]
        stats = _safe_stats(rep, pos_label)
        prec.append(stats["precision"])
        rec.append(stats["recall"])
        f1.append(stats["f1-score"])

    x = np.arange(len(splits))
    width = 0.25

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - width, prec, width, label="precision", color="#4c72b0")
    ax.bar(x, rec, width, label="recall", color="#55a868")
    ax.bar(x + width, f1, width, label="f1", color="#c44e52")

    ax.set_xticks(x)
    ax.set_xticklabels(splits)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Precision, Recall und F1 der positiven Klasse je Split (train/val/test). "
        "Hinweis: leere/degenerierte Splits werden als NaN dargestellt.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)


def _add_binary_tables_page(
    pdf: PdfPages,
    results: Dict[str, Any],
    key: str,
    pos_label: str,
    title: str,
) -> None:
    """Erstellt eine Seite mit einer Tabelle für Precision/Recall/F1 der positiven Klasse.

    Die Tabelle enthält pro Split (train/val/test) eine Zeile.
    """
    metrics = results[key]
    splits = ["train", "val", "test"]

    def _safe_stats(report: Dict[str, Any], label: str) -> Dict[str, float]:
        if not isinstance(report, dict):
            report = {}
        stats = report.get(label)
        if not isinstance(stats, dict):
            stats = report.get(str(label))
        if not isinstance(stats, dict):
            return {
                "precision": float("nan"),
                "recall": float("nan"),
                "f1-score": float("nan"),
                "support": float("nan"),
            }
        return {
            "precision": float(stats.get("precision", float("nan"))),
            "recall": float(stats.get("recall", float("nan"))),
            "f1-score": float(stats.get("f1-score", float("nan"))),
            "support": float(stats.get("support", float("nan"))),
        }

    rows = []
    for split in splits:
        rep = metrics[split]["report"]
        stats = _safe_stats(rep, pos_label)
        rows.append(
            [
                split,
                stats["precision"],
                stats["recall"],
                stats["f1-score"],
                stats["support"],
            ]
        )

    fig, ax = plt.subplots(figsize=(8.27, 3.5))
    ax.axis("off")
    ax.set_title(title, fontsize=12, weight="bold", pad=10)

    col_labels = ["split", "precision", "recall", "f1", "support"]
    table = ax.table(
        cellText=[[f"{v:.3f}" if isinstance(v, float) else v for v in row] for row in rows],
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.1, 1.3)
    fig.text(
        0.01,
        0.02,
        "Tabelle: Kennzahlen der positiven Klasse (precision/recall/F1/support) für train/val/test.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)


def add_signal_page(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Fügt zwei Seiten mit Kennzahlen für das Signal-Modell hinzu.

    - Balkendiagramm Precision/Recall/F1 für Klasse 'move'
    - Tabellarische Übersicht der Scores pro Split
    """
    # Schwelle des Signal-Modells falls vorhanden
    sig_thr = None
    try:
        sig_thr = float(results["signal"]["val"].get("threshold"))
    except Exception:
        sig_thr = None

    if sig_thr is not None:
        title_plot = f"Signal-Modell – Kennzahlen für Klasse 'move' (train/val/test, thr={sig_thr:.2f})"
        title_table = f"Signal-Modell – Tabelle (Klasse 'move', thr={sig_thr:.2f})"
    else:
        title_plot = "Signal-Modell – Kennzahlen für Klasse 'move' (train/val/test)"
        title_table = "Signal-Modell – Tabelle (Klasse 'move')"

    _plot_binary_metrics(
        pdf,
        results,
        key="signal",
        pos_label="move",
        title=title_plot,
    )
    _add_binary_tables_page(
        pdf,
        results,
        key="signal",
        pos_label="move",
        title=title_table,
    )


def add_direction_page(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Fügt zwei Seiten mit Kennzahlen für das Richtungs-Modell hinzu.

    - Balkendiagramm Precision/Recall/F1 für Klasse 'up'
    - Tabellarische Übersicht der Scores pro Split
    """
    _plot_binary_metrics(
        pdf,
        results,
        key="direction",
        pos_label="up",
        title="Richtungs-Modell – Kennzahlen für Klasse 'up' (train/val/test)",
    )
    _add_binary_tables_page(
        pdf,
        results,
        key="direction",
        pos_label="up",
        title="Richtungs-Modell – Tabelle (Klasse 'up')",
    )


def add_combined_page(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Fügt eine Seite mit der kombinierten 3-Klassen-Auswertung hinzu."""
    combined = results["combined_test"]["report"]
    classes = ["neutral", "up", "down"]

    prec = [combined[c]["precision"] for c in classes]
    rec = [combined[c]["recall"] for c in classes]

    x = np.arange(len(classes))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - width / 2, prec, width, label="precision", color="#8172b3")
    ax.bar(x + width / 2, rec, width, label="recall", color="#ccb974")

    ax.set_xticks(x)
    ax.set_xticklabels(classes)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Kombinierte Test-Auswertung – neutral / up / down")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Precision und Recall der kombinierten 3-Klassen-Vorhersage (neutral/up/down) auf dem Test-Split.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)


def add_combined_table_page(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Tabellarische Übersicht der kombinierten 3-Klassen-Metriken (Test)."""
    combined = results["combined_test"]["report"]
    classes = ["neutral", "up", "down"]

    rows = []
    for cls in classes:
        stats = combined[cls]
        rows.append(
            [
                cls,
                round(stats.get("precision", 0.0), 3),
                round(stats.get("recall", 0.0), 3),
                round(stats.get("f1-score", 0.0), 3),
                int(stats.get("support", 0)),
            ]
        )

    fig, ax = plt.subplots(figsize=(8.27, 3.5))
    ax.axis("off")
    ax.set_title(
        "Kombiniertes Modell – Tabelle (Test, neutral/up/down)",
        fontsize=12,
        weight="bold",
        pad=10,
    )

    table = ax.table(
        cellText=rows,
        colLabels=["klasse", "precision", "recall", "f1", "support"],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.1, 1.2)

    fig.text(
        0.01,
        0.02,
        "Tabelle: Kennzahlen der drei Klassen (neutral/up/down) "
        "des kombinierten Modells auf dem Test-Split.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)


def add_multiclass_pages(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Adds pages for an optional 3-class baseline model (neutral/up/down)."""
    mc = results.get("multiclass")
    if not isinstance(mc, dict):
        return

    splits = ["train", "val", "test"]

    def _macro_stats(rep: Dict[str, Any]) -> tuple[float, float, float]:
        if not isinstance(rep, dict):
            return float("nan"), float("nan"), float("nan")
        stats = rep.get("macro avg", {})
        if not isinstance(stats, dict):
            return float("nan"), float("nan"), float("nan")
        return (
            float(stats.get("precision", float("nan"))),
            float(stats.get("recall", float("nan"))),
            float(stats.get("f1-score", float("nan"))),
        )

    macro_prec = []
    macro_rec = []
    macro_f1 = []
    for split in splits:
        rep = mc.get(split, {}).get("report", {})
        p, r, f = _macro_stats(rep)
        macro_prec.append(p)
        macro_rec.append(r)
        macro_f1.append(f)

    x = np.arange(len(splits))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - width, macro_prec, width, label="macro precision", color="#4c72b0")
    ax.bar(x, macro_rec, width, label="macro recall", color="#55a868")
    ax.bar(x + width, macro_f1, width, label="macro f1", color="#c44e52")
    ax.set_xticks(x)
    ax.set_xticklabels(splits)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Multiclass-Baseline – Macro-Kennzahlen (neutral / up / down)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Macro Precision/Recall/F1 der 3-Klassen-Baseline je Split. "
        "Macro = gleiches Gewicht für neutral/up/down.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)

    # Table (Test) – per class
    rep_test = mc.get("test", {}).get("report", {})
    if isinstance(rep_test, dict):
        classes = ["neutral", "up", "down"]
        rows = []
        for cls in classes:
            stats = rep_test.get(cls, {})
            if not isinstance(stats, dict):
                stats = {}
            rows.append(
                [
                    cls,
                    round(float(stats.get("precision", 0.0)), 3),
                    round(float(stats.get("recall", 0.0)), 3),
                    round(float(stats.get("f1-score", 0.0)), 3),
                    int(stats.get("support", 0) or 0),
                ]
            )

        fig, ax = plt.subplots(figsize=(8.27, 3.5))
        ax.axis("off")
        ax.set_title(
            "Multiclass-Baseline – Tabelle (Test, neutral/up/down)",
            fontsize=12,
            weight="bold",
            pad=10,
        )
        table = ax.table(
            cellText=rows,
            colLabels=["klasse", "precision", "recall", "f1", "support"],
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.1, 1.2)
        fig.text(
            0.01,
            0.02,
            "Tabelle: Kennzahlen der drei Klassen (neutral/up/down) "
            "der Multiclass-Baseline auf dem Test-Split.",
            fontsize=8,
        )
        pdf.savefig(fig)
        plt.close(fig)


def add_confusion_pages(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Fügt Confusion-Matrix-Seiten für Signal-, Richtungs- und Kombi-Modell hinzu.

    - Signal: train/val/test (2x2) auf einer Seite
    - Richtung: train/val/test (2x2) auf einer Seite
    - Kombiniert: Test (3-Klassen) auf einer Seite
    """
    sns.set(style="white")

    def _normalize_cm(cm_raw: Any, n: int) -> tuple[np.ndarray, bool]:
        """Return an (n,n) confusion matrix; flag True if original was missing/invalid."""
        try:
            cm = np.array(cm_raw, dtype=int)
        except Exception:
            return np.zeros((n, n), dtype=int), True
        if cm.shape != (n, n):
            return np.zeros((n, n), dtype=int), True
        return cm, False

    # ---------------- Signal: neutral vs. move (train/val/test) ----------------
    splits = ["train", "val", "test"]
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
    for ax, split in zip(axes, splits):
        cm, missing = _normalize_cm(results["signal"][split].get("confusion_matrix"), 2)
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=["neutral", "move"],
            yticklabels=["neutral", "move"],
            ax=ax,
        )
        suffix = " (keine Daten)" if missing else ""
        ax.set_title(f"Signal – {split}{suffix}")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
    plt.tight_layout(rect=(0.02, 0.10, 0.98, 0.95))
    fig.text(
        0.01,
        0.02,
        "Abbildung: Confusion-Matrizen des Signal-Modells (neutral vs move) "
        "für Train-, Validierungs- und Test-Split.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)

    # ---------------- Richtung: down vs. up (train/val/test) -------------------
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
    for ax, split in zip(axes, splits):
        cm, missing = _normalize_cm(results["direction"][split].get("confusion_matrix"), 2)
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Reds",
            xticklabels=["down", "up"],
            yticklabels=["down", "up"],
            ax=ax,
        )
        suffix = " (keine Daten)" if missing else ""
        ax.set_title(f"Richtung – {split}{suffix}")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
    plt.tight_layout(rect=(0.02, 0.10, 0.98, 0.95))
    fig.text(
        0.01,
        0.02,
        "Abbildung: Confusion-Matrizen des Richtungs-Modells (down vs up) "
        "für Train-, Validierungs- und Test-Split.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)

    # ---------------- Multiclass baseline: neutral / up / down (train/val/test) -------------------
    mc = results.get("multiclass")
    if isinstance(mc, dict) and any(isinstance(mc.get(s), dict) for s in splits):
        fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
        for ax, split in zip(axes, splits):
            cm, missing = _normalize_cm(mc.get(split, {}).get("confusion_matrix"), 3)
            sns.heatmap(
                cm,
                annot=True,
                fmt="d",
                cmap="Greens",
                xticklabels=["neutral", "up", "down"],
                yticklabels=["neutral", "up", "down"],
                ax=ax,
            )
            suffix = " (keine Daten)" if missing else ""
            ax.set_title(f"Multiclass – {split}{suffix}")
            ax.set_xlabel("Predicted")
            ax.set_ylabel("True")
        plt.tight_layout(rect=(0.02, 0.10, 0.98, 0.95))
        fig.text(
            0.01,
            0.02,
            "Abbildung: Confusion-Matrizen der 3-Klassen-Baseline (neutral / up / down) "
            "für Train-, Validierungs- und Test-Split.",
            fontsize=8,
        )
        pdf.savefig(fig)
        plt.close(fig)

    # ---------------- Kombiniert: neutral / up / down (Test) -------------------
    cm_combined, missing = _normalize_cm(results.get("combined_test", {}).get("confusion_matrix"), 3)
    fig, ax = plt.subplots(figsize=(4.5, 4.0))
    sns.heatmap(
        cm_combined,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=["neutral", "up", "down"],
        yticklabels=["neutral", "up", "down"],
        ax=ax,
    )
    suffix = " (keine Daten)" if missing else ""
    ax.set_title(f"Confusion Matrix – Test (neutral / up / down){suffix}")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    # etwas Platz am unteren Rand für eine zweizeilige Caption lassen
    plt.tight_layout(rect=(0.02, 0.14, 0.98, 0.95))
    fig.text(
        0.01,
        0.03,
        "Abbildung: Confusion-Matrix des kombinierten Modells (neutral/up/down)\n"
        "auf dem Test-Split.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)


def add_confusion_tables_page(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Fügt eine Seite mit TN/FP/FN/TP-Tabellen für Signal- und Richtungsmodell hinzu."""
    rows = []
    for model_key, model_name in [
        ("signal", "signal"),
        ("direction", "direction"),
    ]:
        for split in ["train", "val", "test"]:
            cm = np.array(results[model_key][split]["confusion_matrix"])
            if cm.shape == (2, 2):
                tn, fp, fn, tp = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
                rows.append(
                    [
                        model_name,
                        split,
                        int(tn),
                        int(fp),
                        int(fn),
                        int(tp),
                    ]
                )

    if not rows:
        return

    fig, ax = plt.subplots(figsize=(8.27, 3.5))
    ax.axis("off")
    ax.set_title(
        "Konfusionsmatrizen – Zählwerte (TN/FP/FN/TP)",
        fontsize=12,
        weight="bold",
        pad=10,
    )

    col_labels = ["modell", "split", "TN", "FP", "FN", "TP"]
    # Spaltenbreiten leicht begrenzen, damit die Tabelle komplett auf die Seite passt.
    col_widths = [0.14, 0.14, 0.12, 0.12, 0.12, 0.12]
    table = ax.table(
        cellText=rows,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    # Etwas kleiner skalieren, damit links/rechts nichts abgeschnitten wird.
    table.scale(1.1, 1.3)
    fig.text(
        0.01,
        0.03,
        "Tabelle: Zählwerte der Konfusionsmatrizen (TN/FP/FN/TP)\n"
        "für Signal- und Richtungs-Modell je Split.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)


def add_misclassification_summary_page(pdf: PdfPages, preds: pd.DataFrame) -> None:
    """Fügt eine kompakte Übersicht zu wichtigsten Fehlklassifikationen hinzu.

    Fokus:
    - Kombinierter Test (neutral/up/down): False Positives für up und down.
    - Signal-Test (neutral vs move): False Positives für move.
    """
    # Sicherstellen, dass die relevanten Spalten im richtigen Typ vorliegen
    df = preds.copy()
    df["label_true"] = df["label_true"].astype(str)
    df["combined_pred"] = df["combined_pred"].astype(str)
    df["signal_pred"] = df["signal_pred"].astype(int)

    rows = []

    def format_counts(counts: pd.Series) -> str:
        parts = []
        for lab in ["neutral", "up", "down"]:
            if lab in counts.index:
                cnt = int(counts[lab])
                parts.append(f"{lab}:{cnt}")
        return ", ".join(parts) if parts else "-"

    # Kombinierter Test: False Positives für up / down
    for pred_class in ["up", "down"]:
        mask = (df["combined_pred"] == pred_class) & (df["label_true"] != pred_class)
        total = int(mask.sum())
        counts = df.loc[mask, "label_true"].value_counts()
        rows.append(
            {
                "task": "combined",
                "predicted": pred_class,
                "total_fp": total,
                "true_label_breakdown": format_counts(counts),
            }
        )

    # Signal-Test: False Positives für move (pred=1, true=neutral)
    signal_true = np.where(df["label_true"].isin(["up", "down"]), 1, 0)
    df["signal_true"] = signal_true
    mask_fp_move = (df["signal_pred"] == 1) & (df["signal_true"] == 0)
    total_fp_move = int(mask_fp_move.sum())
    counts_move = df.loc[mask_fp_move, "label_true"].value_counts()
    rows.append(
        {
            "task": "signal",
            "predicted": "move",
            "total_fp": total_fp_move,
            "true_label_breakdown": format_counts(counts_move),
        }
    )

    if not rows:
        return

    df_rows = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(8.27, 3.0))
    ax.axis("off")
    ax.set_title(
        "Fehlklassifikationen – Übersicht (False Positives)",
        fontsize=12,
        weight="bold",
        pad=10,
    )

    table = ax.table(
        cellText=df_rows.values,
        colLabels=df_rows.columns.tolist(),
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.1, 1.2)

    fig.text(
        0.01,
        0.02,
        "Tabelle: Zusammenfassung der wichtigsten False-Positive-Fälle "
        "für kombinierten Test (neutral/up/down) und Signal-Test (neutral vs move).",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)


def _format_date_axis_monthly(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for label in ax.get_xticklabels():
        label.set_rotation(30)
        label.set_ha("right")


def add_misclassification_timeline_pages(
    pdf: PdfPages,
    df: pd.DataFrame,
    preds: pd.DataFrame,
    project_root: Path,
    exp_config: Dict[str, Any],
    results: Dict[str, Any],
) -> None:
    """Zeigt, *wo* Fehlklassifikationen im Testzeitraum liegen (auf der Preis-Zeitachse).

    Seiten:
    1) Combined-Fehler (true label vs combined_pred) als Marker auf dem Close-Verlauf
    2) Signal-False-Positives (signal_pred=1, aber true=neutral) als Marker
    """
    df_price = _ensure_close_with_labels(df, project_root, exp_config)
    cfg = results.get("config", {})
    test_start = pd.to_datetime(cfg.get("test_start"))

    if "date" not in df_price.columns or "Close" not in df_price.columns:
        return

    df_test = df_price[df_price["date"] >= test_start].copy()
    preds_local = preds.copy()
    preds_local["date"] = pd.to_datetime(preds_local["date"])
    preds_test = preds_local[preds_local["date"] >= test_start].copy()
    if preds_test.empty:
        return

    merged = preds_test.merge(df_test[["date", "Close"]], on="date", how="left").dropna(subset=["Close"])
    if merged.empty:
        return

    merged["label_true"] = merged["label_true"].astype(str)
    merged["combined_pred"] = merged["combined_pred"].astype(str)

    # -----------------------------
    # 1) Combined-Fehler (3 Klassen)
    # -----------------------------
    errors = merged[merged["label_true"] != merged["combined_pred"]].copy()
    if errors.empty:
        fig, ax = plt.subplots(figsize=(8.27, 3.0))
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "Keine Fehlklassifikationen im kombinierten Test (neutral/up/down).",
            ha="center",
            va="center",
        )
        fig.text(
            0.01,
            0.02,
            "Abbildung: Es wurden im Testzeitraum keine Abweichungen zwischen true label und combined_pred gefunden.",
            fontsize=8,
        )
        pdf.savefig(fig)
        plt.close(fig)
    else:
        errors["error_type"] = errors["label_true"] + "→" + errors["combined_pred"]
        total = len(merged)
        total_err = len(errors)

        style_map = {
            "neutral→up": ("#1b9e77", "^"),
            "neutral→down": ("#d95f02", "v"),
            "up→neutral": ("#7570b3", "o"),
            "down→neutral": ("#e7298a", "o"),
            "up→down": ("#e41a1c", "x"),
            "down→up": ("#377eb8", "x"),
        }

        fig, ax = plt.subplots(figsize=(11.69, 5.0))
        ax.plot(df_test["date"], df_test["Close"], color="lightgray", linewidth=1.2, label="Close (Test)")

        for err_type, group in errors.groupby("error_type"):
            color, marker = style_map.get(err_type, ("#333333", "x"))
            ax.scatter(
                group["date"],
                group["Close"],
                s=35,
                color=color,
                marker=marker,
                alpha=0.9,
                label=f"{err_type} (n={len(group)})",
            )

        ax.set_title(
            f"Fehlklassifikationen (combined) im Test – Positionen auf der Preiszeitreihe "
            f"(n={total_err}/{total} = {total_err/total:.1%})"
        )
        ax.set_xlabel("Datum")
        ax.set_ylabel("Close")
        _format_date_axis_monthly(ax)
        ax.legend(loc="upper left", fontsize=8, ncol=2)
        plt.tight_layout()
        fig.text(
            0.01,
            0.02,
            "Abbildung: Jede Markierung ist ein Testtag, an dem der kombinierte Output (combined_pred) "
            "vom true label abweicht. Farben/Marker zeigen den Fehlertyp true→pred.",
            fontsize=8,
        )
        pdf.savefig(fig)
        plt.close(fig)

    # -----------------------------------------
    # 2) Signal-False-Positives (move statt neutral)
    # -----------------------------------------
    if "signal_pred" in merged.columns:
        merged_sig = merged.copy()
        merged_sig["signal_pred"] = merged_sig["signal_pred"].astype(int)
        merged_sig["signal_true"] = np.where(merged_sig["label_true"].isin(["up", "down"]), 1, 0)
        fp_move = merged_sig[(merged_sig["signal_pred"] == 1) & (merged_sig["signal_true"] == 0)].copy()

        if fp_move.empty:
            fig, ax = plt.subplots(figsize=(8.27, 3.0))
            ax.axis("off")
            ax.text(
                0.5,
                0.5,
                "Keine Signal-False-Positives (move) im Test (true=neutral).",
                ha="center",
                va="center",
            )
            fig.text(
                0.01,
                0.02,
                "Abbildung: Das Signal-Modell hat im Test keine neutralen Tage fälschlich als 'move' markiert.",
                fontsize=8,
            )
            pdf.savefig(fig)
            plt.close(fig)
        else:
            fig, ax = plt.subplots(figsize=(11.69, 4.6))
            ax.plot(df_test["date"], df_test["Close"], color="lightgray", linewidth=1.2, label="Close (Test)")
            ax.scatter(
                fp_move["date"],
                fp_move["Close"],
                s=40,
                color="#e41a1c",
                marker="x",
                alpha=0.9,
                label=f"signal FP: pred=move, true=neutral (n={len(fp_move)})",
            )
            ax.set_title("Signal-False-Positives im Test – Positionen auf der Preiszeitreihe")
            ax.set_xlabel("Datum")
            ax.set_ylabel("Close")
            _format_date_axis_monthly(ax)
            ax.legend(loc="upper left", fontsize=9)
            plt.tight_layout()
            fig.text(
                0.01,
                0.02,
                "Abbildung: Markierte Testtage, an denen das Signal-Modell (neutral vs move) "
                "fälschlich ein Trade-Signal gegeben hat (pred=move), obwohl der Tag im Labeling neutral ist.",
                fontsize=8,
            )
            pdf.savefig(fig)
            plt.close(fig)


def _compute_trade_return(
    date: pd.Timestamp,
    pred_label: str,
    true_label: str,
    fx_df: pd.DataFrame,
    label_params: Dict[str, Any],
) -> float:
    """Berechnet die prozentuale Rendite eines Trades (ohne Einsatz).

    Konvention:
    - Return ist relativ zum Einstiegskurs (z. B. 0.01 = +1 %).
    - Bei neutraler Vorhersage (pred_label='neutral') wird 0.0 zurückgegeben.
    - Wenn true_label='neutral' und eine Position eröffnet wird, wird
      konservativ angenommen, dass der Stop-Loss getroffen wird.
    """
    pred_label = str(pred_label)
    true_label = str(true_label)

    if pred_label == "neutral":
        return 0.0

    horizon = int(label_params.get("horizon_days", 4))
    up_thr = float(label_params.get("up_threshold", 0.0))
    down_thr = float(label_params.get("down_threshold", 0.0))
    max_adv = label_params.get("max_adverse_move_pct", 0.01) or 0.01

    # worst case für Trades auf eigentlich neutrale Tage: Stop-Loss
    if true_label == "neutral":
        return -float(max_adv)

    try:
        idx = fx_df.index.get_loc(date)
    except KeyError:
        return 0.0

    if idx + horizon >= len(fx_df):
        return 0.0

    segment = fx_df["Close"].iloc[idx : idx + horizon + 1].to_numpy()
    entry = segment[0]

    if pred_label == "up":
        sl_level = entry * (1 - max_adv)
        tp_level = entry * (1 + up_thr)
        for price in segment[1:]:
            if price <= sl_level:
                return -float(max_adv)
            if price >= tp_level:
                return float(up_thr)
        # kein TP/SL innerhalb des Fensters: Return am Horizontende
        return float((segment[-1] - entry) / entry)

    if pred_label == "down":
        sl_level = entry * (1 + max_adv)
        tp_level = entry * (1 + down_thr)
        for price in segment[1:]:
            if price >= sl_level:
                return -float(max_adv)
            if price <= tp_level:
                # down_thr ist negativ -> Gewinn ist -down_thr (positiv)
                return float(-down_thr)
        # kein TP/SL innerhalb des Fensters: Return am Horizontende
        return float((entry - segment[-1]) / entry)

    # Fallback (sollte praktisch nicht vorkommen)
    return 0.0


def _compute_trade_return_tp_or_horizon_no_sl(
    date: pd.Timestamp,
    pred_label: str,
    true_label: str,
    fx_df: pd.DataFrame,
    label_params: Dict[str, Any],
) -> float:
    """Variante Tradesimulation: Take-Profit oder Horizontende, kein Stop-Loss.

    Regel:
    - pred_label='neutral' -> kein Trade -> 0.0
    - pred_label in {'up','down'}:
        - Wenn die jeweilige Schwelle innerhalb des Horizonts erreicht wird:
            -> Trade wird sofort mit exakt der Schwellen-Rendite geschlossen.
        - Sonst:
            -> Trade wird am Ende des Horizonts geschlossen (Return am Horizontende).

    Hinweis:
    - ``true_label`` wird hier NICHT für worst-case Heuristiken verwendet.
      Diese Variante ist bewusst einfacher/optimistischer als die SL+TP-Variante.
    """
    pred_label = str(pred_label)
    if pred_label == "neutral":
        return 0.0

    horizon = int(label_params.get("horizon_days", 4))
    up_thr = float(label_params.get("up_threshold", 0.0))
    down_thr = float(label_params.get("down_threshold", 0.0))

    try:
        idx = fx_df.index.get_loc(date)
    except KeyError:
        return 0.0

    if idx + horizon >= len(fx_df):
        return 0.0

    segment = fx_df["Close"].iloc[idx : idx + horizon + 1].to_numpy()
    entry = float(segment[0])

    if pred_label == "up":
        tp_level = entry * (1 + up_thr)
        for price in segment[1:]:
            if float(price) >= tp_level:
                return float(up_thr)
        return float((segment[-1] - entry) / entry)

    if pred_label == "down":
        tp_level = entry * (1 + down_thr)
        for price in segment[1:]:
            if float(price) <= tp_level:
                return float(-down_thr)
        return float((entry - segment[-1]) / entry)

    return 0.0


def _compute_trade_outcome(
    date: pd.Timestamp,
    pred_label: str,
    true_label: str,
    fx_df: pd.DataFrame,
    label_params: Dict[str, Any],
    *,
    variant: str,
) -> tuple[float, pd.Timestamp]:
    """Wie _compute_trade_return*, aber liefert zusätzlich das Exit-Datum.

    variant:
        - "sl_tp": Stop-Loss + Take-Profit (wie _compute_trade_return)
        - "tp_only": Take-Profit oder Horizontende, kein Stop-Loss (wie _compute_trade_return_tp_or_horizon_no_sl)

    Wichtig:
        Das Exit-Datum ist das Datum des Close, an dem die Regel auslöst (oder Horizontende).
        Falls das Datum nicht in fx_df liegt oder das Segment nicht vollständig ist, wird (0.0, date) geliefert.
    """
    pred_label = str(pred_label)
    true_label = str(true_label)
    variant = str(variant)

    if pred_label == "neutral":
        return 0.0, date

    horizon = int(label_params.get("horizon_days", 4))
    up_thr = float(label_params.get("up_threshold", 0.0))
    down_thr = float(label_params.get("down_threshold", 0.0))

    try:
        idx = fx_df.index.get_loc(date)
    except KeyError:
        return 0.0, date

    if idx + horizon >= len(fx_df):
        return 0.0, date

    segment = fx_df["Close"].iloc[idx : idx + horizon + 1].to_numpy()
    entry = float(segment[0])
    exit_horizon = fx_df.index[idx + horizon]

    if variant == "tp_only":
        if pred_label == "up":
            tp_level = entry * (1 + up_thr)
            for i, price in enumerate(segment[1:], start=1):
                if float(price) >= tp_level:
                    return float(up_thr), fx_df.index[idx + i]
            return float((segment[-1] - entry) / entry), exit_horizon

        if pred_label == "down":
            tp_level = entry * (1 + down_thr)
            for i, price in enumerate(segment[1:], start=1):
                if float(price) <= tp_level:
                    return float(-down_thr), fx_df.index[idx + i]
            return float((entry - segment[-1]) / entry), exit_horizon

        return 0.0, date

    # Default: sl_tp (Variante 1)
    max_adv = label_params.get("max_adverse_move_pct", 0.01) or 0.01

    # worst case für Trades auf eigentlich neutrale Tage: Stop-Loss (sofort verbucht)
    if true_label == "neutral":
        return -float(max_adv), date

    if pred_label == "up":
        sl_level = entry * (1 - float(max_adv))
        tp_level = entry * (1 + up_thr)
        for i, price in enumerate(segment[1:], start=1):
            if float(price) <= sl_level:
                return -float(max_adv), fx_df.index[idx + i]
            if float(price) >= tp_level:
                return float(up_thr), fx_df.index[idx + i]
        return float((segment[-1] - entry) / entry), exit_horizon

    if pred_label == "down":
        sl_level = entry * (1 + float(max_adv))
        tp_level = entry * (1 + down_thr)
        for i, price in enumerate(segment[1:], start=1):
            if float(price) >= sl_level:
                return -float(max_adv), fx_df.index[idx + i]
            if float(price) <= tp_level:
                return float(-down_thr), fx_df.index[idx + i]
        return float((entry - segment[-1]) / entry), exit_horizon

    return 0.0, date


def _add_trade_simulation_rule_page(
    pdf: PdfPages,
    label_params: Dict[str, Any],
    *,
    title: str,
    bullets: list[str],
) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111)
    ax.axis("off")

    y = 0.92
    fig.text(0.06, y, "Tradesimulation – Regel", fontsize=18, weight="bold")
    y -= 0.06
    fig.text(0.06, y, title, fontsize=13, weight="bold")
    y -= 0.05

    lp = label_params or {}
    fig.text(
        0.06,
        y,
        f"Parameter: horizon_days={lp.get('horizon_days')}, up_threshold={lp.get('up_threshold')}, "
        f"down_threshold={lp.get('down_threshold')}, max_adverse_move_pct={lp.get('max_adverse_move_pct')}",
        fontsize=11,
    )
    y -= 0.06

    for line in bullets:
        fig.text(0.06, y, f"- {line}", fontsize=11)
        y -= 0.035

    fig.text(
        0.06,
        0.08,
        "Hinweis: Diese Simulation arbeitet (wie bisher) close-basiert. Intraday-Trigger (High/Low) sind hier nicht abgebildet.",
        fontsize=10,
        alpha=0.85,
    )
    pdf.savefig(fig)
    plt.close(fig)


def _add_trade_simulation_pages_variant(
    pdf: PdfPages,
    preds: pd.DataFrame,
    fx_df: pd.DataFrame,
    exp_config: Dict[str, Any],
    *,
    trade_return_fn,
    settle_at_exit: bool = False,
    outcome_variant: str | None = None,
    variant_name: str | None = None,
    model_prefix: str = "",
) -> None:
    """Fügt Seiten zur Tradesimulation (Strategie A/B/C) in den Report ein.

    Strategien:
    - A: fixer Einsatz pro Trade (100 CHF)
    - B: fixer Anteil am Kapital (10%)
    - C: Einsatz via FLEX (risk_per_trade in [0,1]) -> stake = risk * 10% * Kapital
    """
    label_params = exp_config.get("label_params", {})
    title_prefix = f"{model_prefix}{variant_name}: " if variant_name else model_prefix

    df = preds.copy().sort_values("date")

    df["date"] = pd.to_datetime(df["date"])
    df["label_true"] = df["label_true"].astype(str)
    df["combined_pred"] = df["combined_pred"].astype(str)

    if settle_at_exit:
        if outcome_variant is None:
            raise ValueError("outcome_variant muss gesetzt sein, wenn settle_at_exit=True.")

        outcomes = [
            _compute_trade_outcome(dt, pred, true, fx_df, label_params, variant=outcome_variant)
            for dt, pred, true in zip(df["date"], df["combined_pred"], df["label_true"])
        ]
        df["trade_return"] = [r for r, _ in outcomes]
        exit_raw = [ex for _, ex in outcomes]

        dates = pd.DatetimeIndex(df["date"].tolist())

        def book_date(exit_dt: pd.Timestamp) -> pd.Timestamp | pd.NaT:
            # Exit kann (je nach horizon_days) nach dem letzten Test-Tag liegen.
            # Damit die Settlement-Variante nicht NaT produziert (und offene Trades "verschwinden"),
            # buchen wir dann konservativ auf den letzten verfügbaren Test-Tag.
            if len(dates) == 0:
                return pd.NaT
            i = dates.searchsorted(pd.Timestamp(exit_dt))
            if i >= len(dates):
                return dates[-1]
            return dates[i]

        df["exit_booked"] = [
            book_date(ex) if pred in {"up", "down"} else pd.NaT
            for pred, ex in zip(df["combined_pred"], exit_raw)
        ]
    else:
        # Trade-Return (in %) pro Tag
        df["trade_return"] = [
            trade_return_fn(dt, pred, true, fx_df, label_params)
            for dt, pred, true in zip(df["date"], df["combined_pred"], df["label_true"])
        ]

    # Strategie A: fixer Einsatz (100 CHF bei up, 100 CHF bei down)
    df["stake_fixed"] = np.where(
        df["combined_pred"] == "up",
        100.0,
        np.where(df["combined_pred"] == "down", 100.0, 0.0),
    )
    df["pnl_fixed"] = df["stake_fixed"] * df["trade_return"]

    # Strategie A mit Hebel 20: P&L skaliert mit Faktor 20
    df["pnl_fixed_lev20"] = df["pnl_fixed"] * 20.0
    # Entry-basierte P&L behalten (für Kostenmatrix / Winner-Loser-Counts / Totals)
    df["pnl_fixed_entry"] = df["pnl_fixed"]
    df["pnl_fixed_lev20_entry"] = df["pnl_fixed_lev20"]

    trades_mask = df["stake_fixed"] > 0
    trades_df = df[trades_mask]

    total_pnl_fixed = trades_df["pnl_fixed_entry"].sum()
    n_trades = int(trades_mask.sum())
    n_up_trades = int((trades_df["combined_pred"] == "up").sum())
    n_down_trades = int((trades_df["combined_pred"] == "down").sum())
    n_win = int((trades_df["pnl_fixed_entry"] > 0).sum())
    n_loss = int((trades_df["pnl_fixed_entry"] < 0).sum())

    total_pnl_fixed_lev20 = float(df.loc[trades_mask, "pnl_fixed_lev20_entry"].sum())

    # Strategie B: 10 % des Vermögens je Trade (ohne Hebel)
    start_capital = 1000.0
    frac = 0.10
    capital_before: list[float] = []
    capital_after: list[float] = []
    capital = start_capital
    pnl_b: list[float] = []

    # Strategie B mit Hebel 20: paralleler Kapitalverlauf
    capital_after_lev20: list[float] = []
    capital_lev20 = start_capital

    if settle_at_exit:
        pending: dict[pd.Timestamp, float] = {}
        pending_lev20: dict[pd.Timestamp, float] = {}
        pnl_b_lev20_daily: list[float] = []
        stake_b_entry: list[float] = []
        stake_b_entry_lev20: list[float] = []
        pnl_b_trade_lev20: list[float] = []
        # Strategie C (FLEX)
        pending_c: dict[pd.Timestamp, float] = {}
        pnl_c: list[float] = []
        capital_after_c: list[float] = []
        stake_c_entry: list[float] = []
        cap_c = float(start_capital)
        open_exits_c: list[pd.Timestamp] = []

        # Setup FLEX (optional)
        flex_ok = False
        flex_cfg = None
        flex_note: str | None = None
        if {"signal_prob", "direction_prob_up"}.issubset(set(df.columns)):
            try:
                import re
                import shutil
                import subprocess

                from src.risk.flex_engine import FlexConfig, evaluate_risk

                flex_cfg = FlexConfig(
                    flex_cmd=os.environ.get("FLEX_CMD", "flex"),
                    rule_path=Path("rules/risk.flex"),
                    extra_args=(),
                    mode=os.environ.get("FLEX_MODE", "auto"),
                )
                resolved = shutil.which(flex_cfg.flex_cmd)
                if resolved:
                    try:
                        proc = subprocess.run([resolved, "--version"], text=True, capture_output=True, check=False)
                        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
                        if re.search(r"\bflex\s+2\.", out, flags=re.IGNORECASE):
                            flex_note = (
                                f"FLEX_CMD='{flex_cfg.flex_cmd}' resolved to '{resolved}' (lex flex 2.x). "
                                "Nutze Python-Fallback; setze FLEX_CMD auf deine fuzzy-FLEX Engine, wenn du das CLI nutzen willst."
                            )
                            flex_cfg = FlexConfig(
                                flex_cmd=flex_cfg.flex_cmd,
                                pre_args=flex_cfg.pre_args,
                                rule_path=flex_cfg.rule_path,
                                extra_args=flex_cfg.extra_args,
                                mode="python",
                            )
                    except Exception:
                        pass
                flex_ok = True
            except Exception as e:
                flex_ok = False
                flex_note = f"FLEX init fehlgeschlagen: {type(e).__name__}: {str(e).splitlines()[0]}"
        else:
            flex_note = "FLEX deaktiviert: Predictions enthalten nicht 'signal_prob' und 'direction_prob_up'."

        # Volatilität aus Close-Returns (rolling std) und robust auf [0,1] normieren.
        dates_idx = pd.DatetimeIndex(df["date"].tolist())
        fx_close = pd.Series(fx_df["Close"]).copy()
        fx_close.index = pd.to_datetime(fx_close.index)
        vol_raw = fx_close.pct_change().rolling(14).std()
        vol_on_dates = vol_raw.reindex(dates_idx).astype(float)
        q05 = float(vol_on_dates.quantile(0.05))
        q95 = float(vol_on_dates.quantile(0.95))
        denom = (q95 - q05) if (q95 > q05) else 1.0
        vol_norm = ((vol_on_dates - q05) / denom).clip(0.0, 1.0).fillna(0.5).to_numpy()

        pred_arr = df["combined_pred"].astype(str).to_numpy()
        p_sig_arr = df["signal_prob"].astype(float).to_numpy() if "signal_prob" in df.columns else None
        p_up_arr = df["direction_prob_up"].astype(float).to_numpy() if "direction_prob_up" in df.columns else None

        for i, (dt, r, stake, exit_booked, pred) in enumerate(
            zip(df["date"], df["trade_return"], df["stake_fixed"], df["exit_booked"], pred_arr)
        ):
            capital_before.append(capital)
            realized = float(pending.pop(dt, 0.0))
            realized_lev20 = float(pending_lev20.pop(dt, 0.0))
            capital += realized
            capital_lev20 += realized_lev20
            pnl_b.append(realized)
            pnl_b_lev20_daily.append(realized_lev20)

            realized_c = float(pending_c.pop(dt, 0.0))
            cap_c += realized_c
            pnl_c.append(realized_c)
            open_exits_c = [ex for ex in open_exits_c if pd.Timestamp(ex) > pd.Timestamp(dt)]
            open_tr_c = float(min(len(open_exits_c), 5))

            if stake > 0 and pd.notna(exit_booked):
                stake_b = capital * frac
                stake_b_lev20 = capital_lev20 * frac
                stake_b_entry.append(stake_b)
                stake_b_entry_lev20.append(stake_b_lev20)

                pending[pd.Timestamp(exit_booked)] = pending.get(pd.Timestamp(exit_booked), 0.0) + stake_b * float(r)
                trade_pnl_lev20 = stake_b_lev20 * float(r) * 20.0
                pending_lev20[pd.Timestamp(exit_booked)] = pending_lev20.get(pd.Timestamp(exit_booked), 0.0) + trade_pnl_lev20
                pnl_b_trade_lev20.append(trade_pnl_lev20)

                # Strategie C: stake via FLEX risk_per_trade
                if flex_ok:
                    p_sig = float(p_sig_arr[i]) if p_sig_arr is not None else 0.0
                    p_up = float(p_up_arr[i]) if p_up_arr is not None else 0.5
                    dir_conf = p_up if pred == "up" else (1.0 - p_up)
                    sig_conf = float(max(0.0, min(1.0, p_sig * dir_conf)))
                    v = float(vol_norm[i]) if len(vol_norm) > i else 0.5
                    try:
                        risk = float(
                            evaluate_risk(
                                signal_confidence=sig_conf,
                                volatility=v,
                                open_trades=open_tr_c,
                                cfg=flex_cfg,  # type: ignore[arg-type]
                            )
                        )
                        risk = float(max(0.0, min(1.0, risk)))
                        stake_c = cap_c * frac * risk
                        stake_c_entry.append(stake_c)
                        pending_c[pd.Timestamp(exit_booked)] = pending_c.get(pd.Timestamp(exit_booked), 0.0) + stake_c * float(r)
                        open_exits_c.append(pd.Timestamp(exit_booked))
                    except Exception as e:
                        flex_ok = False
                        flex_note = f"FLEX evaluate fehlgeschlagen: {type(e).__name__}: {str(e).splitlines()[0]}"
                        stake_c_entry.append(0.0)
                else:
                    stake_c_entry.append(0.0)
            else:
                stake_b_entry.append(0.0)
                stake_b_entry_lev20.append(0.0)
                pnl_b_trade_lev20.append(0.0)
                stake_c_entry.append(0.0)

            capital_after.append(capital)
            capital_after_lev20.append(capital_lev20)
            capital_after_c.append(cap_c)

        df["stake_b_entry"] = stake_b_entry
        df["stake_b_entry_lev20"] = stake_b_entry_lev20
        df["pnl_b_trade_lev20"] = pnl_b_trade_lev20
        df["pnl_b_lev20"] = pnl_b_lev20_daily
        df["capital_after_c"] = capital_after_c
        df["stake_c_entry"] = stake_c_entry
        df["pnl_c"] = pnl_c
        if flex_note is not None:
            # keep it short for the PDF; avoid multi-line CLI spam inside table cells
            note = " ".join(str(flex_note).split())
            if len(note) > 180:
                note = note[:177] + "..."
            df.attrs["flex_note"] = note
    else:
        for r, stake in zip(df["trade_return"], df["stake_fixed"]):
            capital_before.append(capital)
            if stake > 0:
                new_capital = capital * (1.0 + frac * r)
                pnl_b.append(new_capital - capital)
                capital = new_capital
            else:
                pnl_b.append(0.0)
            capital_after.append(capital)
            # Variante mit Hebel 20: Return wird mit 20 skaliert
            if stake > 0:
                capital_lev20 = capital_lev20 * (1.0 + frac * r * 20.0)
            capital_after_lev20.append(capital_lev20)

    df["capital_before"] = capital_before
    df["capital_after"] = capital_after
    df["pnl_b"] = pnl_b
    df["capital_after_lev20"] = capital_after_lev20
    final_capital = float(capital)
    min_capital = float(min(capital_after) if capital_after else start_capital)
    final_capital_lev20 = float(capital_lev20)
    min_capital_lev20 = float(min(capital_after_lev20) if capital_after_lev20 else start_capital)
    if not settle_at_exit:
        # pro-Tag P&L für Strategie B mit Hebel 20
        prev_cap_lev20 = pd.Series(capital_after_lev20).shift(1).fillna(start_capital).to_numpy()
        pnl_b_lev20 = (np.array(capital_after_lev20) - prev_cap_lev20).tolist()
        df["pnl_b_lev20"] = pnl_b_lev20

    if settle_at_exit:
        # Settlement-am-Exit: daily P&L für Strategie A wird am Exit gebucht (überschreibt Plot-Serien).
        pnl_fixed_settle = np.zeros(len(df), dtype=float)
        for trade_flag, exit_booked, pnl_entry in zip(
            trades_mask.to_numpy(), df["exit_booked"], df["pnl_fixed_entry"]
        ):
            if bool(trade_flag) and pd.notna(exit_booked):
                j = df["date"].searchsorted(pd.Timestamp(exit_booked))
                if 0 <= j < len(pnl_fixed_settle):
                    pnl_fixed_settle[j] += float(pnl_entry)
        df["pnl_fixed"] = pnl_fixed_settle.tolist()
        df["pnl_fixed_lev20"] = (pnl_fixed_settle * 20.0).tolist()

    # Kostenmatrizen für Strategie A (fixer Einsatz, ohne Hebel)
    labels_order = ["neutral", "up", "down"]
    cost_total_rows = []
    cost_mean_rows = []
    for true_lab in labels_order:
        for pred_lab in labels_order:
            mask = (df["label_true"] == true_lab) & (df["combined_pred"] == pred_lab)
            cnt = int(mask.sum())
            total = float(df.loc[mask, "pnl_fixed_entry"].sum())
            mean = float(total / cnt) if cnt > 0 else 0.0
            cost_total_rows.append([true_lab, pred_lab, cnt, total])
            cost_mean_rows.append([true_lab, pred_lab, mean])

    cost_total = pd.DataFrame(
        cost_total_rows, columns=["label_true", "combined_pred", "count", "sum_chf"]
    )
    cost_mean = pd.DataFrame(
        cost_mean_rows, columns=["label_true", "combined_pred", "mean_chf"]
    )

    # Seite 1: Zusammenfassung beider Strategien
    summary_rows = [
        ["Strategy", "Kennzahl", "Wert"],
        ["A (fixer Einsatz)", "Anzahl Trades", n_trades],
        ["A (fixer Einsatz)", "Einsatz up / down (CHF)", "100 / 100"],
        ["A (fixer Einsatz)", "Trades up / down", f"{n_up_trades} / {n_down_trades}"],
        ["A (fixer Einsatz)", "Gewinner / Verlierer", f"{n_win} / {n_loss}"],
        ["A (fixer Einsatz)", "Gesamt-P&L (CHF)", f"{total_pnl_fixed:.2f}"],
        ["A (fixer Einsatz, Hebel 20)", "Gesamt-P&L (CHF)", f"{total_pnl_fixed_lev20:.2f}"],
        ["B (10% vom Kapital)", "Startkapital (CHF)", f"{start_capital:.2f}"],
        ["B (10% vom Kapital)", "Endkapital (CHF)", f"{final_capital:.2f}"],
        ["B (10% vom Kapital)", "Minimum Kapital (CHF)", f"{min_capital:.2f}"],
        ["B (10% vom Kapital, Hebel 20)", "Endkapital (CHF)", f"{final_capital_lev20:.2f}"],
        ["B (10% vom Kapital, Hebel 20)", "Minimum Kapital (CHF)", f"{min_capital_lev20:.2f}"],
    ]
    # Strategie C Summary (nur wenn settle_at_exit und wir die C-Serien haben)
    if settle_at_exit and "capital_after_c" in df.columns:
        cap_c_series = df["capital_after_c"].astype(float).to_numpy()
        final_c = float(cap_c_series[-1]) if len(cap_c_series) else start_capital
        min_c = float(np.min(cap_c_series)) if len(cap_c_series) else start_capital
        stake_c = df.get("stake_c_entry", pd.Series([0.0] * len(df))).astype(float).to_numpy()
        mean_stake_c = float(np.mean(stake_c[stake_c > 0])) if np.any(stake_c > 0) else 0.0
        summary_rows += [
            ["C (FLEX)", "Endkapital (CHF)", f"{final_c:.2f}"],
            ["C (FLEX)", "Minimum Kapital (CHF)", f"{min_c:.2f}"],
            ["C (FLEX)", "Ø Einsatz pro Trade (CHF)", f"{mean_stake_c:.2f}"],
            ["C (FLEX)", "FLEX_CMD", os.environ.get("FLEX_CMD", "flex")],
        ]
        flex_note = str(df.attrs.get("flex_note") or "")

    fig, ax = plt.subplots(figsize=(8.27, 3.5))
    ax.axis("off")
    ax.set_title(f"{title_prefix}Tradesimulation – Strategien A/B/C (Test-Split)", fontsize=12, weight="bold", pad=10)

    table = ax.table(
        cellText=summary_rows[1:],
        colLabels=summary_rows[0],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.1, 1.2)

    fig.text(
        0.01,
        0.03,
        "Tabelle: Zusammenfassung der Tradesimulation auf dem Test-Split.\n"
        "Strategie A: fixer Einsatz pro Trade (100 CHF bei up, 100 CHF bei down).\n"
        "Strategie B: 10 % des aktuellen Vermögens pro Trade (optional mit Hebel 20).\n"
        "Strategie C: Einsatz via FLEX (symbolische Regeln, risk_per_trade in [0,1]).",
        fontsize=8,
    )
    if settle_at_exit and flex_note:
        fig.text(0.01, 0.01, f"FLEX Hinweis: {flex_note}", fontsize=7, alpha=0.85)
    pdf.savefig(fig)
    plt.close(fig)

    # Optional: Vergleichsseiten B vs C nur für Variante 3 (TP-only + Settlement am Exit)
    if settle_at_exit and variant_name == "Variante 3" and "capital_after_c" in df.columns:
        try:
            cap_b = df["capital_after"].astype(float).to_numpy()
            cap_c = df["capital_after_c"].astype(float).to_numpy()
            stake_b = df.get("stake_b_entry", pd.Series([0.0] * len(df))).astype(float).to_numpy()
            stake_c = df.get("stake_c_entry", pd.Series([0.0] * len(df))).astype(float).to_numpy()
            delta = cap_c - cap_b

            fig, (ax1, ax2) = plt.subplots(
                2, 1, figsize=(11.69, 6.5), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
            )
            ax1.plot(df["date"], cap_b, label="Strategie B (fix 10%)", linewidth=2)
            ax1.plot(df["date"], cap_c, label="Strategie C (FLEX)", linewidth=2)
            ax1.axhline(start_capital, color="black", linewidth=1, alpha=0.4)
            ax1.set_title(
                f"{title_prefix}Strategie B vs C – Kapitalverlauf (Variante 3, Test-Split)",
                fontsize=13,
                weight="bold",
            )
            ax1.set_ylabel("Kapital (CHF)")
            ax1.legend()
            ax2.bar(df["date"], delta, width=3.0, color=np.where(delta >= 0, "#2ca02c", "#d62728"), alpha=0.8)
            ax2.axhline(0.0, color="black", linewidth=1)
            ax2.set_ylabel("Δ (C−B)\n(CHF)")
            ax2.set_xlabel("Datum")
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(11.69, 4.5))
            ax.scatter(df["date"][stake_b > 0], stake_b[stake_b > 0], s=18, alpha=0.85, label="B: Einsatz (fix 10%)")
            ax.scatter(df["date"][stake_c > 0], stake_c[stake_c > 0], s=18, alpha=0.85, label="C: Einsatz (FLEX)")
            ax.set_title(f"{title_prefix}Einsatz pro Trade – Strategie B vs C (Variante 3)", fontsize=13, weight="bold")
            ax.set_xlabel("Datum")
            ax.set_ylabel("Einsatz (CHF)")
            ax.legend()
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)
        except Exception as e:
            fig = plt.figure(figsize=(11.69, 3.5))
            fig.patch.set_facecolor("white")
            ax = fig.add_subplot(111)
            ax.axis("off")
            fig.text(0.06, 0.78, f"{title_prefix}Strategie B vs C – Vergleich", fontsize=14, weight="bold")
            fig.text(0.06, 0.60, "Vergleichsgrafik konnte nicht erzeugt werden.", fontsize=11)
            fig.text(0.06, 0.48, f"Fehler: {e}", fontsize=9, alpha=0.85)
            fig.text(0.06, 0.18, "Tipp: prüfe FLEX_CMD/FLEX_MODE und ob Predictions signal_prob/direction_prob_up enthalten.", fontsize=10)
            pdf.savefig(fig)
            plt.close(fig)

    # Seite 2: Kostenmatrix – durchschnittliche Kosten pro Fall (Strategie A)
    if not cost_mean.empty:
        fig, ax = plt.subplots(figsize=(8.27, 3.5))
        ax.axis("off")
        ax.set_title(
            f"{title_prefix}Kostenmatrix – durchschnittliche Kosten pro Fall (Strategie A, Test-Split)",
            fontsize=12,
            weight="bold",
            pad=10,
        )

        mean_table = ax.table(
            cellText=cost_mean.values,
            colLabels=cost_mean.columns.tolist(),
            loc="center",
            cellLoc="center",
        )
        mean_table.auto_set_font_size(False)
        mean_table.set_fontsize(8)
        mean_table.scale(1.1, 1.2)

        fig.text(
            0.01,
            0.03,
            "Tabelle: durchschnittliche Kosten (CHF) pro Fall für jede Kombination\n"
            "aus wahrem Label und vorhergesagtem Label (Strategie A, fixer Einsatz).",
            fontsize=8,
        )
        pdf.savefig(fig)
        plt.close(fig)

    # Seite 3: Kostenmatrix – Gesamtkosten und Anzahl Trades (Strategie A)
    if not cost_total.empty:
        fig, ax = plt.subplots(figsize=(8.27, 3.5))
        ax.axis("off")
        ax.set_title(
            f"{title_prefix}Kostenmatrix – Gesamtkosten und Anzahl Trades (Strategie A, Test-Split)",
            fontsize=12,
            weight="bold",
            pad=10,
        )

        total_table = ax.table(
            cellText=cost_total.values,
            colLabels=cost_total.columns.tolist(),
            loc="center",
            cellLoc="center",
        )
        total_table.auto_set_font_size(False)
        total_table.set_fontsize(8)
        total_table.scale(1.1, 1.2)

        fig.text(
            0.01,
            0.03,
            "Tabelle: Anzahl Fälle und Gesamt-P&L (CHF) auf dem Test-Split\n"
            "für jede Kombination aus wahrem Label und vorhergesagtem Label (Strategie A).",
            fontsize=8,
        )
        pdf.savefig(fig)
        plt.close(fig)

    # Seite 4: Strategie A vs B – Kapital (ohne Hebel) + Differenz (unten), damit alles gut lesbar ist.
    # (Twin-Axis war zu eng, deshalb 2 Subplots auf einer Seite.)
    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(11.69, 6.2),  # A4 quer, höher für Achsen/Labels
        sharex=True,
        gridspec_kw={"height_ratios": [3.0, 1.2]},
    )

    # Strategie A als Kapitalverlauf (Startkapital + kumulierter P&L aus fixer Einsatz-Logik)
    capital_a = start_capital + df["pnl_fixed"].cumsum()
    capital_b = df["capital_after"]
    diff_ba = capital_b - capital_a

    ax_top.plot(
        df["date"],
        capital_a,
        label="Strategie A (fixer Einsatz) – Kapital",
        color="#4c72b0",
        linewidth=2.0,
    )
    ax_top.plot(
        df["date"],
        capital_b,
        label="Strategie B (10% Kapital) – Kapital",
        color="#c44e52",
        linewidth=2.0,
    )
    ax_top.set_title(
        f"{title_prefix}Strategie A vs B – Verlauf des Kapitals (ohne Hebel, Test-Split)",
        fontsize=13,
        weight="bold",
        pad=10,
    )
    ax_top.set_ylabel("Kapital (CHF)")
    ax_top.grid(alpha=0.3)
    ax_top.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax_top.legend(loc="upper left", fontsize=9, framealpha=0.9)

    ax_bot.bar(
        df["date"],
        diff_ba,
        width=2.0,  # etwas breiter als 1 Tag, damit Balken sichtbarer sind
        color="#8172b2",
        alpha=0.35,
    )
    ax_bot.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax_bot.set_ylabel("Δ (B−A)\n(CHF)")
    ax_bot.set_xlabel("Datum")
    ax_bot.grid(alpha=0.2)
    ax_bot.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))

    # X-Achse: monatlich, aber nicht zu dicht
    ax_bot.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax_bot.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")

    # Layout: genug Platz unten für X-Ticks + Caption
    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.24, hspace=0.08)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Oben Kapitalverlauf (CHF) für Strategie A und B ohne Hebel. "
        "Unten Balken: Differenz Δ = (B − A) je Tag.",
        fontsize=9,
    )

    pdf.savefig(fig)
    plt.close(fig)

    # Seite 5: Strategie A vs B – kumulierter P&L (ohne Hebel, oben) + Differenz (unten)
    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(11.69, 6.2),
        gridspec_kw={"height_ratios": [3.0, 1.2]},
        sharex=True,
    )

    pnl_a = df["pnl_fixed"].cumsum()  # Strategie A: fixer Einsatz
    pnl_b_cum = df["capital_after"] - start_capital  # Strategie B: 10% Kapital
    diff_pnl_ba = pnl_b_cum - pnl_a

    ax_top.plot(
        df["date"],
        pnl_a,
        label="Strategie A (fixer Einsatz) – P&L",
        color="#4c72b0",
        linewidth=2.0,
    )
    ax_top.plot(
        df["date"],
        pnl_b_cum,
        label="Strategie B (10% Kapital) – P&L",
        color="#c44e52",
        linewidth=2.0,
    )
    ax_top.set_title(
        "Strategie A vs B – kumulierter P&L (ohne Hebel, Test-Split)",
        fontsize=13,
        weight="bold",
        pad=10,
    )
    ax_top.set_ylabel("P&L (CHF)")
    ax_top.grid(alpha=0.3)
    ax_top.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax_top.legend(loc="upper left", fontsize=9, framealpha=0.9)

    ax_bot.bar(
        df["date"],
        diff_pnl_ba,
        width=2.0,
        color="#8172b2",
        alpha=0.35,
    )
    ax_bot.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax_bot.set_ylabel("Δ (B−A)\n(CHF)")
    ax_bot.set_xlabel("Datum")
    ax_bot.grid(alpha=0.2)
    ax_bot.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax_bot.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax_bot.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")

    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.24, hspace=0.08)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Oben kumulierter Gewinn/Verlust (P&L, CHF) für Strategie A und B ohne Hebel. "
        "Unten Balken: Differenz Δ = (B − A) je Tag.",
        fontsize=9,
    )
    pdf.savefig(fig)
    plt.close(fig)

    # Seite 6: kumulierter P&L als Punkte (A vs B, ohne Hebel) + Differenz (unten)
    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(11.69, 6.2),
        gridspec_kw={"height_ratios": [3.0, 1.2]},
        sharex=True,
    )
    ax_top.scatter(
        df["date"],
        pnl_a,
        label="Strategie A (fixer Einsatz) – kumulierter P&L",
        color="#4c72b0",
        s=18,
        alpha=0.85,
    )
    ax_top.scatter(
        df["date"],
        pnl_b_cum,
        label="Strategie B (10% Kapital) – kumulierter P&L",
        color="#c44e52",
        s=18,
        alpha=0.85,
    )
    ax_top.set_title(
        f"{title_prefix}Strategie A vs B – kumulierter Gewinn (P&L) als Punkte (ohne Hebel, Test-Split)",
        fontsize=13,
        weight="bold",
        pad=10,
    )
    ax_top.set_ylabel("P&L (CHF)")
    ax_top.grid(alpha=0.3)
    ax_top.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax_top.legend(loc="upper left", fontsize=10, framealpha=0.9)

    ax_bot.bar(
        df["date"],
        diff_pnl_ba,
        width=2.0,
        color="#8172b2",
        alpha=0.35,
    )
    ax_bot.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax_bot.set_ylabel("Δ (B−A)\n(CHF)")
    ax_bot.set_xlabel("Datum")
    ax_bot.grid(alpha=0.2)
    ax_bot.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax_bot.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax_bot.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")

    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.24, hspace=0.08)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Oben kumulierter Gewinn/Verlust (P&L) als Punkte. Unten Balken: Differenz Δ = (B − A) je Tag.",
        fontsize=9,
    )
    pdf.savefig(fig)
    plt.close(fig)

    # Seite 7: Strategie A vs B – Kapital (Hebel 20) + Differenz (unten)
    capital_a_lev20 = start_capital + df["pnl_fixed_lev20"].cumsum()
    capital_b_lev20 = df["capital_after_lev20"]
    diff_ba_lev20 = capital_b_lev20 - capital_a_lev20

    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(11.69, 6.2),
        gridspec_kw={"height_ratios": [3.0, 1.2]},
        sharex=True,
    )
    ax_top.plot(
        df["date"],
        capital_a_lev20,
        label="Strategie A (fixer Einsatz) – Kapital (Hebel 20)",
        color="#4c72b0",
        linewidth=2.0,
    )
    ax_top.plot(
        df["date"],
        capital_b_lev20,
        label="Strategie B (10% Kapital) – Kapital (Hebel 20)",
        color="#c44e52",
        linewidth=2.0,
    )
    ax_top.set_title(
        f"{title_prefix}Strategie A vs B – Verlauf des Kapitals (Hebel 20, Test-Split)",
        fontsize=13,
        weight="bold",
        pad=10,
    )
    ax_top.set_ylabel("Kapital (CHF)")
    ax_top.grid(alpha=0.3)
    ax_top.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax_top.legend(loc="upper left", fontsize=9, framealpha=0.9)

    ax_bot.bar(
        df["date"],
        diff_ba_lev20,
        width=2.0,
        color="#8172b2",
        alpha=0.35,
    )
    ax_bot.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax_bot.set_ylabel("Δ (B−A)\n(CHF)")
    ax_bot.set_xlabel("Datum")
    ax_bot.grid(alpha=0.2)
    ax_bot.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax_bot.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax_bot.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")

    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.24, hspace=0.08)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Oben Kapitalverlauf (CHF) für Strategie A und B mit Hebel 20. "
        "Unten Balken: Differenz Δ = (B − A) je Tag.",
        fontsize=9,
    )
    pdf.savefig(fig)
    plt.close(fig)

    # Seite 8: Strategie A vs B – kumulierter P&L (Hebel 20, oben) + Differenz (unten)
    pnl_a_lev20 = df["pnl_fixed_lev20"].cumsum()
    pnl_b_cum_lev20 = df["capital_after_lev20"] - start_capital
    diff_pnl_ba_lev20 = pnl_b_cum_lev20 - pnl_a_lev20

    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(11.69, 6.2),
        gridspec_kw={"height_ratios": [3.0, 1.2]},
        sharex=True,
    )
    ax_top.plot(
        df["date"],
        pnl_a_lev20,
        label="Strategie A (fixer Einsatz) – P&L (Hebel 20)",
        color="#4c72b0",
        linewidth=2.0,
    )
    ax_top.plot(
        df["date"],
        pnl_b_cum_lev20,
        label="Strategie B (10% Kapital) – P&L (Hebel 20)",
        color="#c44e52",
        linewidth=2.0,
    )
    ax_top.set_title(
        f"{title_prefix}Strategie A vs B – kumulierter P&L (Hebel 20, Test-Split)",
        fontsize=13,
        weight="bold",
        pad=10,
    )
    ax_top.set_ylabel("P&L (CHF)")
    ax_top.grid(alpha=0.3)
    ax_top.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax_top.legend(loc="upper left", fontsize=9, framealpha=0.9)

    ax_bot.bar(
        df["date"],
        diff_pnl_ba_lev20,
        width=2.0,
        color="#8172b2",
        alpha=0.35,
    )
    ax_bot.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax_bot.set_ylabel("Δ (B−A)\n(CHF)")
    ax_bot.set_xlabel("Datum")
    ax_bot.grid(alpha=0.2)
    ax_bot.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax_bot.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax_bot.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")

    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.24, hspace=0.08)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Oben kumulierter Gewinn/Verlust (P&L, CHF) für Strategie A und B mit Hebel 20. "
        "Unten Balken: Differenz Δ = (B − A) je Tag.",
        fontsize=9,
    )
    pdf.savefig(fig)
    plt.close(fig)

    # Seite 9: kumulierter P&L als Punkte (A vs B, Hebel 20) + Differenz (unten)
    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(11.69, 6.2),
        gridspec_kw={"height_ratios": [3.0, 1.2]},
        sharex=True,
    )
    ax_top.scatter(
        df["date"],
        pnl_a_lev20,
        label="Strategie A (fixer Einsatz) – kumulierter P&L (Hebel 20)",
        color="#4c72b0",
        s=18,
        alpha=0.85,
    )
    ax_top.scatter(
        df["date"],
        pnl_b_cum_lev20,
        label="Strategie B (10% Kapital) – kumulierter P&L (Hebel 20)",
        color="#c44e52",
        s=18,
        alpha=0.85,
    )
    ax_top.set_title(
        f"{title_prefix}Strategie A vs B – kumulierter Gewinn (P&L) als Punkte (Hebel 20, Test-Split)",
        fontsize=13,
        weight="bold",
        pad=10,
    )
    ax_top.set_ylabel("P&L (CHF)")
    ax_top.grid(alpha=0.3)
    ax_top.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax_top.legend(loc="upper left", fontsize=10, framealpha=0.9)

    ax_bot.bar(
        df["date"],
        diff_pnl_ba_lev20,
        width=2.0,
        color="#8172b2",
        alpha=0.35,
    )
    ax_bot.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax_bot.set_ylabel("Δ (B−A)\n(CHF)")
    ax_bot.set_xlabel("Datum")
    ax_bot.grid(alpha=0.2)
    ax_bot.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax_bot.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax_bot.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")

    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.24, hspace=0.08)
    fig.text(
        0.01,
        0.02,
        "Abbildung: Oben kumulierter Gewinn/Verlust (P&L) als Punkte. Unten Balken: Differenz Δ = (B − A) je Tag.",
        fontsize=9,
    )
    pdf.savefig(fig)
    plt.close(fig)

    # Zusätzliche Analyse: Gewinn pro Trade über Zeit (Hebel 20), als Balken
    trades = df[df["stake_fixed"] > 0].copy()
    if settle_at_exit and "exit_booked" in trades.columns:
        trades = trades[pd.notna(trades["exit_booked"])].copy()
    if not trades.empty:
        fig, (ax_a, ax_b) = plt.subplots(
            2,
            1,
            figsize=(11.69, 6.6),
            sharex=True,
            gridspec_kw={"height_ratios": [1.0, 1.0]},
        )

        def bar_signed(ax: plt.Axes, x: pd.Series, y: pd.Series, title: str) -> None:
            colors = np.where(y >= 0, "#1b9e77", "#d95f02")
            ax.bar(x, y, width=2.0, color=colors, alpha=0.65)
            ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
            ax.set_title(title, fontsize=11, weight="bold", pad=6)
            ax.set_ylabel("P&L pro Trade (CHF)")
            ax.grid(alpha=0.2)
            ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

        if settle_at_exit and "exit_booked" in trades.columns:
            x_trade = trades["exit_booked"]
            pnl_a_trade = trades["pnl_fixed_lev20_entry"]
            pnl_b_trade = trades["pnl_b_trade_lev20"]
            caption = (
                "Abbildung: Balken zeigen den Gewinn/Verlust pro Trade am Exit-Datum (Settlement). "
                "Grün = Gewinn, Orange = Verlust. Hebel 20 ist bereits eingerechnet."
            )
        else:
            x_trade = trades["date"]
            pnl_a_trade = trades["pnl_fixed_lev20"]
            pnl_b_trade = trades["pnl_b_lev20"]
            caption = (
                "Abbildung: Balken zeigen den Gewinn/Verlust pro Trade (nur Tage mit Trade). "
                "Grün = Gewinn, Orange = Verlust. Hebel 20 ist bereits eingerechnet."
            )

        # Strategie A: fixer Einsatz, Hebel 20
        bar_signed(
            ax_a,
            x_trade,
            pnl_a_trade,
            f"{title_prefix}Strategie A – Gewinn pro Trade (Hebel 20, nur Trade-Tage)",
        )

        # Strategie B: 10% Kapital, Hebel 20
        bar_signed(
            ax_b,
            x_trade,
            pnl_b_trade,
            f"{title_prefix}Strategie B – Gewinn pro Trade (Hebel 20, nur Trade-Tage)",
        )
        ax_b.set_xlabel("Datum")
        ax_b.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax_b.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        for tick in ax_b.get_xticklabels():
            tick.set_rotation(30)
            tick.set_ha("right")

        fig.subplots_adjust(left=0.10, right=0.98, top=0.92, bottom=0.24, hspace=0.20)
        fig.text(
            0.01,
            0.02,
            caption,
            fontsize=9,
        )
        pdf.savefig(fig)
        plt.close(fig)

    # Zusätzliche Analyse: Gewinn pro Monat (Hebel 20), als Balken
    df_month = df.copy()
    df_month["month"] = df_month["date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        df_month.groupby("month", as_index=False)[["pnl_fixed_lev20", "pnl_b_lev20"]]
        .sum()
        .sort_values("month")
    )
    if not monthly.empty:
        fig, ax = plt.subplots(figsize=(11.69, 4.8))
        x = np.arange(len(monthly))
        width = 0.42
        ax.bar(
            x - width / 2,
            monthly["pnl_fixed_lev20"],
            width=width,
            color="#4c72b0",
            alpha=0.75,
            label="Strategie A (Hebel 20)",
        )
        ax.bar(
            x + width / 2,
            monthly["pnl_b_lev20"],
            width=width,
            color="#c44e52",
            alpha=0.75,
            label="Strategie B (Hebel 20)",
        )
        ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
        ax.set_title(f"{title_prefix}Gewinn pro Monat (Hebel 20, Test-Split)", fontsize=13, weight="bold")
        ax.set_xlabel("Monat")
        ax.set_ylabel("P&L pro Monat (CHF)")
        ax.grid(alpha=0.2)
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
        ax.set_xticks(x)
        ax.set_xticklabels([d.strftime("%Y-%m") for d in monthly["month"]], rotation=30, ha="right")
        ax.legend(loc="upper left", fontsize=10, framealpha=0.9)
        fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.28)
        fig.text(
            0.01,
            0.02,
            "Abbildung: Summe der Tages-P&L je Monat. Hebel 20 ist bereits eingerechnet.",
            fontsize=9,
        )
        pdf.savefig(fig)
        plt.close(fig)

    # Projektion: 5 Jahre Fortsetzung via Bootstrap-Monte-Carlo (keine Prognose!)
    # Idee: wir resampeln die beobachteten Tages-P&L (inkl. 0-Tage ohne Trades),
    # damit Trade-Frequenz und Gewinn/Verlust-Verteilung ähnlich bleiben.
    n_days = 5 * 252  # ca. Handelstage
    n_paths = 200
    if len(df) >= 30:
        rng = np.random.default_rng(42)
        pnl_a_day_lev20 = df["pnl_fixed_lev20"].to_numpy()
        pnl_b_day_lev20_arr = df["pnl_b_lev20"].to_numpy()

        paths_a = np.empty((n_paths, n_days), dtype=float)
        paths_b = np.empty((n_paths, n_days), dtype=float)
        for i in range(n_paths):
            sample_idx = rng.integers(0, len(df), size=n_days)
            paths_a[i] = pnl_a_day_lev20[sample_idx].cumsum()
            paths_b[i] = pnl_b_day_lev20_arr[sample_idx].cumsum()

        pcts = [10, 50, 90]
        qa = np.percentile(paths_a, pcts, axis=0)
        qb = np.percentile(paths_b, pcts, axis=0)
        t = np.arange(1, n_days + 1)

        fig, ax = plt.subplots(figsize=(11.69, 5.2))
        ax.fill_between(t, qa[0], qa[2], color="#4c72b0", alpha=0.18, label="A: 10–90% Band")
        ax.plot(t, qa[1], color="#4c72b0", linewidth=2.0, label="A: Median")
        ax.fill_between(t, qb[0], qb[2], color="#c44e52", alpha=0.18, label="B: 10–90% Band")
        ax.plot(t, qb[1], color="#c44e52", linewidth=2.0, label="B: Median")

        ax.set_title(f"{title_prefix}5-Jahres-Projektion (Bootstrap-Monte-Carlo, Hebel 20)", fontsize=13, weight="bold")
        ax.set_xlabel("Handelstage in der Zukunft (~5 Jahre)")
        ax.set_ylabel("Kumulierter P&L (CHF)")
        ax.grid(alpha=0.2)
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
        ax.legend(loc="upper left", fontsize=10, framealpha=0.9, ncol=2)
        fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.18)
        fig.text(
            0.01,
            0.02,
            "Abbildung: Keine echte Prognose. Es wird angenommen, dass die Verteilung der Tages-Ergebnisse "
            "aus dem Testzeitraum (inkl. Tage ohne Trades) in der Zukunft ähnlich bleibt. "
            "Gezeigt sind Median und 10–90% Band über 200 Simulationen.",
            fontsize=9,
        )
        pdf.savefig(fig)
        plt.close(fig)

    # Seite 10: kumulierter P&L für Strategie A (fixer Einsatz)
    fig, ax = plt.subplots(figsize=(11.69, 4.6))
    ax.plot(df["date"], pnl_a, label="ohne Hebel", color="#4c72b0", linewidth=2.0)
    ax.plot(df["date"], pnl_a_lev20, label="mit Hebel 20", color="#c44e52", linestyle="--", linewidth=2.0)
    ax.set_title(f"{title_prefix}Strategie A – kumulierter P&L (Test-Split)", fontsize=13, weight="bold")
    ax.set_xlabel("Datum")
    ax.set_ylabel("P&L (CHF)")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=10)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")
    plt.tight_layout()
    fig.text(
        0.01,
        0.03,
        "Abbildung: kumulierter Gewinn/Verlust (P&L) für Strategie A (fixer Einsatz) "
        "mit und ohne Hebel 20 auf dem Test-Split.",
        fontsize=9,
    )
    pdf.savefig(fig)
    plt.close(fig)

    # Seite 11: kumulierter P&L für Strategie B (10% Kapital)
    fig, ax = plt.subplots(figsize=(11.69, 4.6))
    pnl_b_lev20 = df["capital_after_lev20"] - start_capital
    ax.plot(df["date"], pnl_b_cum, label="ohne Hebel", color="#4c72b0", linewidth=2.0)
    ax.plot(df["date"], pnl_b_lev20, label="mit Hebel 20", color="#c44e52", linestyle="--", linewidth=2.0)
    ax.set_title(f"{title_prefix}Strategie B – kumulierter P&L (Test-Split)", fontsize=13, weight="bold")
    ax.set_xlabel("Datum")
    ax.set_ylabel("P&L (CHF)")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=10)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")
    plt.tight_layout()
    fig.text(
        0.01,
        0.03,
        "Abbildung: kumulierter Gewinn/Verlust (P&L) für Strategie B (10% des aktuellen Kapitals pro Trade) "
        "mit und ohne Hebel 20 auf dem Test-Split.",
        fontsize=9,
    )
    pdf.savefig(fig)
    plt.close(fig)



def add_trade_simulation_pages(
    pdf: PdfPages,
    preds: pd.DataFrame,
    fx_df: pd.DataFrame,
    exp_config: Dict[str, Any],
    *,
    pred_col: str = "combined_pred",
    model_prefix: str = "",
) -> None:
    """Fügt Seiten zur Tradesimulation (Strategie A/B/C) in den Report ein.

    Neu: Wir erzeugen die Tradesimulation bewusst in mehreren Varianten, damit man
    sieht, wie sensitiv die Resultate auf die Closing-Regel und auf den Settlement-Zeitpunkt reagieren.
    """
    label_params = exp_config.get("label_params", {})

    if pred_col not in preds.columns:
        raise KeyError(
            f"pred_col='{pred_col}' nicht in Predictions-CSV gefunden. "
            f"Verfügbare Spalten: {sorted(list(preds.columns))}"
        )

    preds_use = preds
    if pred_col != "combined_pred":
        preds_use = preds.copy()
        preds_use["combined_pred"] = preds_use[pred_col].astype(str)

    _add_trade_simulation_rule_page(
        pdf,
        label_params,
        title=f"{model_prefix}Variante 1: SL + TP (wie bisher)",
        bullets=[
            "Stop-Loss und Take-Profit werden innerhalb des Fensters geprüft (close-basiert).",
            "Wenn weder SL noch TP getroffen wird: Exit am Horizontende (t+horizon_days).",
            "Sonderfall: true_label='neutral' aber Trade -> konservativ Stop-Loss-Annahme (wie bisher).",
        ],
    )
    _add_trade_simulation_pages_variant(
        pdf,
        preds_use,
        fx_df,
        exp_config,
        trade_return_fn=_compute_trade_return,
        variant_name="Variante 1",
        model_prefix=model_prefix,
    )

    _add_trade_simulation_rule_page(
        pdf,
        label_params,
        title=f"{model_prefix}Variante 2: TP-only (kein Stop-Loss, sonst Horizontende)",
        bullets=[
            "Wenn die Label-Schwelle (TP) innerhalb des Fensters erreicht wird: Exit sofort mit TP-Return.",
            "Kein Stop-Loss: wenn TP nicht erreicht wird, wird am Horizontende geschlossen (Return am Horizontende).",
            "Diese Variante ist bewusst vereinfacht/optimistischer und dient als Vergleich.",
        ],
    )
    _add_trade_simulation_pages_variant(
        pdf,
        preds_use,
        fx_df,
        exp_config,
        trade_return_fn=_compute_trade_return_tp_or_horizon_no_sl,
        variant_name="Variante 2",
        model_prefix=model_prefix,
    )

    _add_trade_simulation_rule_page(
        pdf,
        label_params,
        title=f"{model_prefix}Variante 3: TP-only + Settlement am Exit-Datum (Timing realistisch)",
        bullets=[
            "Trade wird am Tag t eröffnet (Signal up/down).",
            "Exit-Datum: erster TP-Hit per Close, sonst Horizontende.",
            "Gewinn/Verlust wird erst am Exit-Datum im Konto verbucht (nicht am Einstiegstag).",
            "Zwischen-Trades nutzen deshalb nicht vorzeitig Gewinne/Verluste aus noch offenen Trades.",
        ],
    )
    _add_trade_simulation_pages_variant(
        pdf,
        preds_use,
        fx_df,
        exp_config,
        trade_return_fn=_compute_trade_return_tp_or_horizon_no_sl,
        settle_at_exit=True,
        outcome_variant="tp_only",
        variant_name="Variante 3",
        model_prefix=model_prefix,
    )

    # Strategie C wird innerhalb von _add_trade_simulation_pages_variant (bei Variante 3) als Vergleich B vs C erzeugt.


def add_distributions_page(pdf: PdfPages, df: pd.DataFrame) -> None:
    """Fügt eine Seite mit den Verteilungen von label, signal und direction hinzu."""
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
    sns.countplot(x="label", data=df, ax=axes[0], order=["neutral", "up", "down"])
    axes[0].set_title("Label-Verteilung (neutral / up / down)")
    axes[0].set_xlabel("label")
    axes[0].set_ylabel("Anzahl")

    sns.countplot(x="signal", data=df, ax=axes[1], order=[0, 1])
    axes[1].set_title("Signal-Verteilung (0=neutral, 1=move)")
    axes[1].set_xlabel("signal")
    axes[1].set_ylabel("Anzahl")

    df_sig = df[df["signal"] == 1]
    if df_sig.empty:
        axes[2].text(
            0.5,
            0.5,
            "Keine Tage mit signal==1 im Datensatz.",
            ha="center",
            va="center",
            fontsize=9,
        )
        axes[2].set_axis_off()
    else:
        sns.countplot(
            x="direction",
            data=df_sig,
            ax=axes[2],
            order=[0, 1],
        )
        axes[2].set_title("Richtung-Verteilung (nur signal==1)")
        axes[2].set_xlabel("direction (0=down, 1=up)")
        axes[2].set_ylabel("Anzahl")

    plt.tight_layout()
    fig.text(
        0.01,
        0.02,
        "Abbildung: Klassenverteilungen für label, signal und direction im vollständigen Trainingsdatensatz.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)


def add_label_distribution_pages(pdf: PdfPages, df: pd.DataFrame, results: Dict[str, Any]) -> None:
    """Fügt Seiten zur Label-Verteilung (gesamt + Splits) hinzu."""
    cfg = results.get("config", {})
    test_start = pd.to_datetime(cfg.get("test_start"))
    train_frac = float(cfg.get("train_frac_within_pretest", 0.8))

    splits = split_train_val_test(df, test_start, train_frac)

    # ---------- Seite 1: Gesamte Label-Verteilung ----------
    labels_order = ["neutral", "up", "down"]
    counts_overall = df["label"].value_counts().reindex(labels_order).fillna(0).astype(int)

    fig, (ax_plot, ax_tab) = plt.subplots(
        2,
        1,
        figsize=(8.27, 6.0),
        gridspec_kw={"height_ratios": [2.0, 1.0]},
    )

    sns.countplot(x="label", data=df, order=labels_order, ax=ax_plot)
    ax_plot.set_title("Label-Verteilung – gesamter Datensatz")
    ax_plot.set_xlabel("label")
    ax_plot.set_ylabel("Anzahl")

    ax_tab.axis("off")
    rows = [[lab, int(counts_overall[lab])] for lab in labels_order]
    table = ax_tab.table(
        cellText=rows,
        colLabels=["label", "count"],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.1, 1.2)

    fig.text(
        0.01,
        0.02,
        "Abbildung/Tabelle: Verteilung der Zielvariable 'label' (neutral/up/down) im gesamten Datensatz.",
        fontsize=8,
    )
    plt.tight_layout(rect=(0, 0.05, 1, 1))
    pdf.savefig(fig)
    plt.close(fig)

    # ---------- Seite 2: Label-Verteilung nach Splits ----------
    rows_split = []
    for split_name in ["train", "val", "test"]:
        split_df = splits.get(split_name)
        if split_df is None or split_df.empty:
            counts = pd.Series(0, index=labels_order)
        else:
            counts = split_df["label"].value_counts().reindex(labels_order).fillna(0).astype(int)
        rows_split.append(
            [split_name, int(counts["neutral"]), int(counts["up"]), int(counts["down"])]
        )

    df_counts = pd.DataFrame(
        rows_split, columns=["split", "neutral", "up", "down"]
    )
    df_melt = df_counts.melt(
        id_vars="split",
        value_vars=labels_order,
        var_name="label",
        value_name="count",
    )

    fig, (ax_plot2, ax_tab2) = plt.subplots(
        2,
        1,
        figsize=(8.27, 6.0),
        gridspec_kw={"height_ratios": [2.0, 1.0]},
    )

    sns.barplot(
        x="label",
        y="count",
        hue="split",
        data=df_melt,
        order=labels_order,
        ax=ax_plot2,
    )
    ax_plot2.set_title("Label-Verteilung nach Splits (train/val/test)")
    ax_plot2.set_xlabel("label")
    ax_plot2.set_ylabel("Anzahl")
    ax_plot2.legend(title="split")

    ax_tab2.axis("off")
    table2 = ax_tab2.table(
        cellText=df_counts.values,
        colLabels=df_counts.columns.tolist(),
        loc="center",
        cellLoc="center",
    )
    table2.auto_set_font_size(False)
    table2.set_fontsize(8)
    table2.scale(1.1, 1.2)

    fig.text(
        0.01,
        0.02,
        "Abbildung/Tabelle: Label-Verteilung getrennt nach Trainings-, Validierungs- und Test-Split.",
        fontsize=8,
    )
    plt.tight_layout(rect=(0, 0.05, 1, 1))
    pdf.savefig(fig)
    plt.close(fig)


def add_price_with_labels_page(
    pdf: PdfPages,
    df: pd.DataFrame,
    project_root: Path,
    exp_config: Dict[str, Any],
) -> None:
    """Fügt eine Seite mit der EURUSD-Zeitreihe und hervorgehobenen up/down-Tagen hinzu.

    Falls der Trainingsdatensatz keine Close-Spalte enthält, wird sie aus der
    entsprechenden Label-Datei (eurusd_labels__<EXP_ID>.csv) ergänzt.
    """
    df_plot = df.copy()

    if "Close" not in df_plot.columns:
        # Close-Kurse aus der Label-Datei ergänzen
        safe_id = str(exp_config.get("exp_id")).replace(" ", "_")
        fx_dir = project_root / "data" / "processed" / "fx"
        labels_path = fx_dir / f"eurusd_labels__{safe_id}.csv"
        if not labels_path.is_file():
            # Fallback: aktuelle Standarddatei
            labels_path = fx_dir / "eurusd_labels.csv"
        if labels_path.is_file():
            fx = pd.read_csv(labels_path, parse_dates=["Date"])
            fx = fx.rename(columns={"Date": "date"})
            df_plot = df_plot.merge(fx[["date", "Close"]], on="date", how="left")
        else:
            # Wenn auch das scheitert, brechen wir diese Seite kontrolliert ab.
            print("[warn] Keine Close-Kurse gefunden – überspringe Preis-Zeitreihe im Report.")
            return

    df_2020 = df_plot[df_plot["date"] >= "2020-01-01"].copy()

    mask_up = df_2020["label"] == "up"
    mask_down = df_2020["label"] == "down"
    mask_neutral = df_2020["label"] == "neutral"

    fig, ax = plt.subplots(figsize=(10, 3.5))

    ax.plot(df_2020["date"], df_2020["Close"], color="lightgray", label="Close")

    ax.scatter(
        df_2020.loc[mask_neutral, "date"],
        df_2020.loc[mask_neutral, "Close"],
        color="gray",
        s=8,
        alpha=0.5,
        label="neutral",
    )
    ax.scatter(
        df_2020.loc[mask_up, "date"],
        df_2020.loc[mask_up, "Close"],
        color="green",
        s=20,
        label="up",
    )
    ax.scatter(
        df_2020.loc[mask_down, "date"],
        df_2020.loc[mask_down, "Close"],
        color="red",
        s=20,
        label="down",
    )

    ax.set_xlabel("Datum")
    ax.set_ylabel("EURUSD Close")
    ax.set_title("EURUSD-Zeitreihe mit hervorgehobenen up/down-Tagen (ab 2020)")
    ax.legend()
    plt.tight_layout()
    fig.text(
        0.01,
        0.02,
        "Abbildung: EURUSD-Schlusskurs mit markierten up-/down-Tagen im betrachteten Zeitraum.",
        fontsize=8,
    )

    pdf.savefig(fig)
    plt.close(fig)


def add_price_with_splits_page(
    pdf: PdfPages,
    df: pd.DataFrame,
    project_root: Path,
    exp_config: Dict[str, Any],
    results: Dict[str, Any],
) -> None:
    """Fügt eine Seite mit der kompletten Preiszeitreihe + Train/Val/Test-Markierungen hinzu."""
    cfg = results.get("config", {})
    test_start = pd.to_datetime(cfg.get("test_start"))
    train_frac = float(cfg.get("train_frac_within_pretest", 0.8))

    # Sicherstellen, dass Close-Kurse vorhanden sind
    df_plot = _ensure_close_with_labels(df, project_root, exp_config)

    # Splits nach derselben Logik wie beim Training rekonstruieren
    splits = split_train_val_test(df_plot, test_start, train_frac)
    train_df = splits["train"]
    val_df = splits["val"]
    test_df = splits["test"]

    train_end = train_df["date"].max() if not train_df.empty else pd.NaT
    val_end = val_df["date"].max() if not val_df.empty else pd.NaT
    test_begin = test_df["date"].min() if not test_df.empty else pd.NaT

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(df_plot["date"], df_plot["Close"], color="lightgray", label="Close")

    # Hintergründe für Train / Val / Test
    ymin, ymax = ax.get_ylim()
    start_all = df_plot["date"].min()
    end_all = df_plot["date"].max()

    # Train-Bereich (falls vorhanden)
    if pd.notna(train_end):
        ax.axvspan(start_all, train_end, color="#d9f0d3", alpha=0.3, label="Train")

    # Val-Bereich nur, wenn Val-Split nicht leer ist (sonst wäre val_end=NaT -> Plot-Fehler)
    if pd.notna(train_end) and pd.notna(val_end):
        ax.axvspan(train_end, val_end, color="#fee0b6", alpha=0.3, label="Val")

    # Test-Bereich (falls vorhanden)
    if pd.notna(test_begin):
        ax.axvspan(test_begin, end_all, color="#deebf7", alpha=0.3, label="Test")

    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Datum")
    ax.set_ylabel("EURUSD Close")
    ax.set_title("EURUSD-Zeitreihe mit Train/Val/Test-Bereichen")
    # Nur einzigartige Labels in der Legende
    handles, labels = ax.get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    ax.legend(uniq.values(), uniq.keys(), loc="upper left")

    plt.tight_layout()
    fig.text(
        0.01,
        0.02,
        "Abbildung: EURUSD-Schlusskurs über den gesamten Zeitraum mit farblich markierten "
        "Trainings-, Validierungs- und Testphasen.",
        fontsize=8,
    )
    pdf.savefig(fig)
    plt.close(fig)


def _ensure_close_with_labels(
    df: pd.DataFrame, project_root: Path, exp_config: Dict[str, Any]
) -> pd.DataFrame:
    """Hilfsfunktion: sorgt dafür, dass df die Spalte 'Close' enthält.

    Falls nötig, werden Close-Kurse aus der Label-Datei ergänzt.
    """
    df_plot = df.copy()
    needed = [c for c in ["Close", "High", "Low"] if c not in df_plot.columns]
    if not needed:
        return df_plot

    safe_id = str(exp_config.get("exp_id")).replace(" ", "_")
    fx_dir = project_root / "data" / "processed" / "fx"
    labels_path = fx_dir / f"eurusd_labels__{safe_id}.csv"
    if not labels_path.is_file():
        labels_path = fx_dir / "eurusd_labels.csv"
    if labels_path.is_file():
        fx = pd.read_csv(labels_path, parse_dates=["Date"])
        fx = fx.rename(columns={"Date": "date"})
        cols = ["date"] + [c for c in needed if c in fx.columns]
        df_plot = df_plot.merge(fx[cols], on="date", how="left")
    else:
        print("[warn] Keine Close-Kurse gefunden – Segmentplots übersprungen.")
    return df_plot


def _plot_segment_overlays(
    pdf: PdfPages,
    df_price: pd.DataFrame,
    start_dates: pd.Series,
    horizon_steps: int,
    label_name: str,
    color: str,
    title: str,
    caption: str,
    max_segments: int | None = 25,
    segments_per_page: int = 25,
    up_threshold: float | None = None,
    down_threshold: float | None = None,
) -> None:
    """Zeigt mehrere Segmente (t..t+horizon) über der Zeitreihe als Overlay.

    Alle Segmente werden – konsistent mit der Label-Logik – nur dann gezeichnet,
    wenn ein vollständiger Pfad t..t+horizon existiert (keine gekürzten Segmente).

    Optional kann für up/down zusätzlich der Ziel-Threshold eingezeichnet werden:
    - up:   Close_t * (1 + up_threshold)   als blaues Dreieck nach oben
    - down: Close_t * (1 + down_threshold) als blaues Dreieck nach unten
    """
    # einheitlicher Stil (weißes Hintergrund, dezentes Gitter)
    sns.set_style("whitegrid")
    if start_dates.empty:
        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.text(0.5, 0.5, f"Keine Segmente für label='{label_name}'.", ha="center", va="center")
        ax.axis("off")
        fig.text(0.01, 0.02, caption, fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)
        return

    df = df_price.sort_values("date").set_index("date")
    idx = df.index

    start_dates = pd.to_datetime(start_dates)
    start_dates = [d for d in start_dates if d in idx]
    if max_segments is not None:
        start_dates = start_dates[:max_segments]

    if not start_dates:
        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.text(0.5, 0.5, f"Keine Segmente für label='{label_name}'.", ha="center", va="center")
        ax.axis("off")
        fig.text(0.01, 0.02, caption, fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)
        return

    segments_per_page = max(1, int(segments_per_page))
    total_pages = int(np.ceil(len(start_dates) / segments_per_page))

    ymin = float(df["Close"].min())
    ymax = float(df["Close"].max())
    pad = 0.02 * (ymax - ymin) if ymax > ymin else 0.001

    for page_start in range(0, len(start_dates), segments_per_page):
        page_dates = start_dates[page_start : page_start + segments_per_page]
        page_no = page_start // segments_per_page + 1

        fig, ax = plt.subplots(figsize=(11.69, 5.2))
        ax.set_facecolor("white")
        ax.plot(df.index, df["Close"], color="lightgray", linewidth=1.0, label="Close (Test)")
        ax.set_ylim(ymin - pad, ymax + pad)
        _format_date_axis_monthly(ax)

        show_thr_label = True

        for t0 in page_dates:
            pos = idx.get_loc(t0)
            end_pos = pos + horizon_steps
            if end_pos >= len(idx):
                continue
            seg = df.iloc[pos : end_pos + 1]
            start_close = seg["Close"].iloc[0]

            ax.plot(seg.index, seg["Close"], color=color, linewidth=1.6, alpha=0.65)
            ax.scatter(seg.index[0], seg["Close"].iloc[0], color=color, s=18, alpha=0.9)
            ax.scatter(seg.index[-1], seg["Close"].iloc[-1], color=color, s=26, marker="x", alpha=0.9)

            # Threshold-Markierung (optional)
            if label_name == "up" and up_threshold is not None:
                thr = start_close * (1.0 + up_threshold)
                ax.scatter(
                    seg.index[-1],
                    thr,
                    color="blue",
                    marker="^",
                    s=28,
                    alpha=0.9,
                    label="up-threshold" if show_thr_label else None,
                )
                show_thr_label = False
            elif label_name == "down" and down_threshold is not None:
                thr = start_close * (1.0 + down_threshold)
                ax.scatter(
                    seg.index[-1],
                    thr,
                    color="blue",
                    marker="v",
                    s=28,
                    alpha=0.9,
                    label="down-threshold" if show_thr_label else None,
                )
                show_thr_label = False

        page_title = title
        if total_pages > 1:
            page_title += f" – Seite {page_no}/{total_pages}"
        ax.set_title(page_title)
        ax.set_xlabel("Datum")
        ax.set_ylabel("Close")

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            uniq = dict(zip(labels, handles))
            ax.legend(uniq.values(), uniq.keys(), loc="upper left", fontsize=9, ncol=2)

        plt.tight_layout()
        fig.text(0.01, 0.02, caption, fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)


def _plot_segment_rel_small_multiples(
    pdf: PdfPages,
    df_price: pd.DataFrame,
    start_dates: pd.Series,
    horizon_steps: int,
    label_name: str,
    caption: str,
    max_segments: int | None = 16,
    up_threshold: float | None = None,
    down_threshold: float | None = None,
    max_adverse_move_pct: float | None = None,
    labels_for_dates: Dict[pd.Timestamp, str] | None = None,
) -> None:
    """Small-Multiples: rel. Verlauf 0..horizon_steps für gegebene Starttage.

    Einheitliches Layout:
    - Immer 3 Reihen x 2 Spalten pro Seite (6 Panels).
    - y-Achse von -5 % bis +5 % mit festen Ticks.
    - Auch bei wenigen Segmenten bleiben Panel-Größen konstant; leere Panels
      werden ausgeblendet.
    """
    sns.set_style("whitegrid")

    df = df_price.sort_values("date").set_index("date")
    idx = df.index

    start_dates = pd.to_datetime(start_dates)
    start_dates = [d for d in start_dates if d in idx]
    if max_segments is not None:
        start_dates = start_dates[:max_segments]

    segments: list[tuple[str, range, np.ndarray, np.ndarray | None, np.ndarray | None]] = []
    for t0 in start_dates:
        pos = idx.get_loc(t0)
        end_pos = pos + horizon_steps
        if end_pos >= len(idx):
            continue
        seg = df.iloc[pos : end_pos + 1]
        start_close = seg["Close"].iloc[0]
        rel_close = seg["Close"] / start_close - 1.0
        rel_low = None
        rel_high = None
        if "Low" in seg.columns and "High" in seg.columns:
            low = seg["Low"].to_numpy(dtype=float, copy=False)
            high = seg["High"].to_numpy(dtype=float, copy=False)
            if np.isfinite(low).any() and np.isfinite(high).any():
                rel_low = low / float(start_close) - 1.0
                rel_high = high / float(start_close) - 1.0
        if labels_for_dates is not None:
            seg_label = labels_for_dates.get(t0, str(t0))
        else:
            seg_label = seg.index[0]
        segments.append((str(seg_label), range(len(rel_close)), rel_close.to_numpy(), rel_low, rel_high))

    if not segments:
        fig, ax = plt.subplots(figsize=(8.27, 3.0))
        ax.text(0.5, 0.5, f"Keine Segmente für label='{label_name}'.", ha="center", va="center")
        ax.axis("off")
        fig.text(0.01, 0.035, caption, fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)
        return

    # y-Achse: dynamisch zoomen, damit kleine Änderungen besser sichtbar sind.
    def _collect_vals(seg: tuple[str, range, np.ndarray, np.ndarray | None, np.ndarray | None]) -> np.ndarray:
        _, _, rel, lo, hi = seg
        parts = [rel]
        if lo is not None:
            parts.append(lo)
        if hi is not None:
            parts.append(hi)
        return np.concatenate(parts)

    all_vals = np.concatenate([_collect_vals(s) for s in segments]) if segments else np.array([0.0])
    max_abs = float(np.nanmax(np.abs(all_vals))) if all_vals.size else 0.0
    thr_abs = 0.0
    if up_threshold is not None:
        thr_abs = max(thr_abs, abs(float(up_threshold)))
    if down_threshold is not None:
        thr_abs = max(thr_abs, abs(float(down_threshold)))
    if max_adverse_move_pct is not None:
        thr_abs = max(thr_abs, abs(float(max_adverse_move_pct)))

    # Mindestens ±1% und so wählen, dass Threshold-Linien immer im Plot liegen.
    y_lim = max(max_abs * 1.25, thr_abs * 1.1, 0.01)
    if y_lim <= 0:
        y_lim = 0.01
    yticks = list(np.linspace(-y_lim, y_lim, 5))

    segments_per_page = 6
    nrows, ncols = 3, 2

    for page_start in range(0, len(segments), segments_per_page):
        page_segments = segments[page_start : page_start + segments_per_page]

        fig, axes = plt.subplots(
            nrows,
            ncols,
            figsize=(7.5, 8.5),  # etwas schmaler, dafür höher
            sharex=True,
            sharey=True,
        )
        axes_flat = axes.flatten()

        # Standardformatierung für alle Achsen
        show_thr_up_label = True
        show_thr_down_label = True
        show_adv_label = True
        show_hilo_label = True
        for ax in axes_flat:
            ax.set_ylim(-y_lim, y_lim)
            ax.set_yticks(yticks)
            ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=1))
            ax.grid(True, alpha=0.3)
            # X-Ticks immer 0..horizon_steps, damit die Skala einheitlich ist
            xticks = list(range(horizon_steps + 1))
            ax.set_xticks(xticks)
            ax.set_xticklabels([str(t) for t in xticks])
            ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.5)
            if up_threshold is not None:
                ax.axhline(
                    float(up_threshold),
                    color="#1f78b4",
                    linestyle="--",
                    linewidth=1.0,
                    alpha=0.75,
                    label="up-threshold" if show_thr_up_label else None,
                )
                show_thr_up_label = False
            if down_threshold is not None:
                ax.axhline(
                    float(down_threshold),
                    color="#1f78b4",
                    linestyle=":",
                    linewidth=1.0,
                    alpha=0.75,
                    label="down-threshold" if show_thr_down_label else None,
                )
                show_thr_down_label = False

            # Optional: Adverse-Move-Grenze sichtbar machen (hilft beim Verständnis,
            # warum ein Tag trotz großer Endbewegung als neutral gelabelt sein kann).
            if max_adverse_move_pct is not None and float(max_adverse_move_pct) > 0:
                adv = float(max_adverse_move_pct)
                name = str(label_name).lower()
                plot_up_adv = ("up" in name) and ("down" not in name)
                plot_down_adv = ("down" in name) and ("up" not in name)
                # fallback: wenn unklar, beide zeigen
                if not plot_up_adv and not plot_down_adv:
                    plot_up_adv = True
                    plot_down_adv = True

                if plot_up_adv:
                    ax.axhline(
                        -adv,
                        color="#e31a1c",
                        linestyle="-.",
                        linewidth=1.0,
                        alpha=0.7,
                        label="adverse-limit (up)" if show_adv_label else None,
                    )
                    show_adv_label = False
                if plot_down_adv:
                    ax.axhline(
                        adv,
                        color="#e31a1c",
                        linestyle="-.",
                        linewidth=1.0,
                        alpha=0.7,
                        label="adverse-limit (down)" if show_adv_label else None,
                    )
                    show_adv_label = False

        # Segmente plotten
        for ax, (label, steps, rel_values, rel_low, rel_high) in zip(axes_flat, page_segments):
            x = np.array(list(steps), dtype=int)
            if (
                rel_low is not None
                and rel_high is not None
                and len(rel_low) == len(x)
                and len(rel_high) == len(x)
            ):
                ax.fill_between(
                    x,
                    rel_low,
                    rel_high,
                    color="#9e9e9e",
                    alpha=0.20,
                    linewidth=0.0,
                    label="High–Low" if show_hilo_label else None,
                )
                show_hilo_label = False

            ax.plot(x, rel_values, marker="o", color="#4c72b0", linewidth=2.0)
            ax.set_title(label, fontsize=8)

        # übrige Achsen leeren, aber Größe unverändert lassen
        for ax in axes_flat[len(page_segments) :]:
            ax.axis("off")

        # Achsenlabels setzen
        for i, ax in enumerate(axes_flat):
            row = i // ncols
            col = i % ncols
            if not ax.has_data():
                continue
            # X-Achsen-Beschriftung immer setzen, damit sie auch bei nur einer Reihe sichtbar ist
            ax.set_xlabel("Schritt (Handelstage)")
            # Y-Achsen-Beschriftung nur in der ersten Spalte, um Überfüllung zu vermeiden
            if col == 0:
                ax.set_ylabel("rel_close (%)")
            else:
                ax.set_ylabel("")

        title = f"Relativer Verlauf der Segmente (label='{label_name}')"
        if len(segments) > segments_per_page:
            page_no = page_start // segments_per_page + 1
            title += f" – Seite {page_no}"
        fig.suptitle(title, y=0.97)
        handles, labels = axes_flat[0].get_legend_handles_labels()
        if handles:
            uniq = dict(zip(labels, handles))
            fig.legend(
                uniq.values(),
                uniq.keys(),
                loc="lower center",
                ncol=min(3, len(uniq)),
                fontsize=8,
                frameon=False,
                bbox_to_anchor=(0.5, 0.10),
            )
        # mehr Platz nach unten für X-Tick-Labels lassen
        fig.tight_layout(rect=(0.06, 0.22, 0.98, 0.90))

        fig.text(0.01, 0.035, caption, fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)


def add_label_segment_pages(
    pdf: PdfPages,
    df: pd.DataFrame,
    project_root: Path,
    exp_config: Dict[str, Any],
    results: Dict[str, Any],
) -> None:
    """Fügt Segment-Overlays für up/down im Test-Zeitraum hinzu."""
    df_price = _ensure_close_with_labels(df, project_root, exp_config)
    cfg = results.get("config", {})
    test_start = pd.to_datetime(cfg.get("test_start"))
    horizon = int(cfg.get("horizon_days", 4))
    up_thr = cfg.get("up_threshold")
    down_thr = cfg.get("down_threshold")

    df_test = df_price[df_price["date"] >= test_start].copy()

    up_dates = df_test.loc[df_test["label"] == "up", "date"]
    down_dates = df_test.loc[df_test["label"] == "down", "date"]

    _plot_segment_overlays(
        pdf,
        df_test,
        up_dates,
        horizon_steps=horizon,
        label_name="up",
        color="green",
        title="EURUSD-Segmente mit label='up' (Test-Split)",
        caption="Abbildung: Preis-Segmente t..t+horizon für alle Testtage mit true label 'up'.",
        max_segments=None,
        segments_per_page=25,
        up_threshold=up_thr,
        down_threshold=down_thr,
    )
    _plot_segment_rel_small_multiples(
        pdf,
        df_test,
        up_dates,
        horizon_steps=horizon,
        label_name="up",
        caption="Abbildung: Relativer Verlauf der Close-Preise für alle Testtage mit true label 'up'.",
        max_segments=None,
        up_threshold=up_thr,
        down_threshold=down_thr,
        max_adverse_move_pct=cfg.get("max_adverse_move_pct"),
    )

    _plot_segment_overlays(
        pdf,
        df_test,
        down_dates,
        horizon_steps=horizon,
        label_name="down",
        color="red",
        title="EURUSD-Segmente mit label='down' (Test-Split)",
        caption="Abbildung: Preis-Segmente t..t+horizon für alle Testtage mit true label 'down'.",
        max_segments=None,
        segments_per_page=25,
        up_threshold=up_thr,
        down_threshold=down_thr,
    )
    _plot_segment_rel_small_multiples(
        pdf,
        df_test,
        down_dates,
        horizon_steps=horizon,
        label_name="down",
        caption="Abbildung: Relativer Verlauf der Close-Preise für alle Testtage mit true label 'down'.",
        max_segments=None,
        up_threshold=up_thr,
        down_threshold=down_thr,
        max_adverse_move_pct=cfg.get("max_adverse_move_pct"),
    )


def add_misclassified_neutral_segment_pages(
    pdf: PdfPages,
    df: pd.DataFrame,
    preds: pd.DataFrame,
    project_root: Path,
    exp_config: Dict[str, Any],
    results: Dict[str, Any],
) -> None:
    """Relativer Verlauf für true=neutral, aber als up/down klassifiziert (kombinierter Test).

    Es werden ausschließlich Testdaten betrachtet (ab test_start).
    """
    df_price = _ensure_close_with_labels(df, project_root, exp_config)
    cfg = results.get("config", {})
    test_start = pd.to_datetime(cfg.get("test_start"))
    horizon = int(cfg.get("horizon_days", 4))
    up_thr = cfg.get("up_threshold")
    down_thr = cfg.get("down_threshold")

    df_test = df_price[df_price["date"] >= test_start].copy()

    # Sicherstellen, dass Datumstypen kompatibel sind
    preds_local = preds.copy()
    preds_local["date"] = pd.to_datetime(preds_local["date"])

    # Nur Test-Daten (sollten ohnehin nur Testdaten sein, aber zur Sicherheit schneiden wir)
    preds_test = preds_local[preds_local["date"] >= test_start].copy()

    # true neutral, predicted up
    neutral_up = preds_test[
        (preds_test["label_true"] == "neutral") & (preds_test["combined_pred"] == "up")
    ]
    if neutral_up.empty:
        fig, ax = plt.subplots(figsize=(8.27, 2.5))
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "Keine Fälle: true=neutral, predicted=up im kombinierten Test.",
            ha="center",
            va="center",
        )
        fig.text(
            0.01,
            0.02,
            "Abbildung: Es gibt keine Testtage, an denen ein neutraler Tag fälschlich als 'up' klassifiziert wurde.",
            fontsize=8,
        )
        pdf.savefig(fig)
        plt.close(fig)
    else:
        dates_up = neutral_up["date"]
        labels_for_dates_up = {
            pd.to_datetime(d): f"{pd.to_datetime(d).date()} (neutral→up)" for d in dates_up
        }
        _plot_segment_rel_small_multiples(
            pdf,
            df_test,
            dates_up,
            horizon_steps=horizon,
            label_name="neutral→up",
            caption=(
                "Abbildung: Relativer Verlauf der Close-Preise für alle Testtage "
                "mit true label 'neutral', die im kombinierten Test als 'up' klassifiziert wurden."
            ),
            up_threshold=up_thr,
            down_threshold=down_thr,
            max_adverse_move_pct=cfg.get("max_adverse_move_pct"),
            labels_for_dates=labels_for_dates_up,
        )

    # true neutral, predicted down
    neutral_down = preds_test[
        (preds_test["label_true"] == "neutral") & (preds_test["combined_pred"] == "down")
    ]
    if neutral_down.empty:
        fig, ax = plt.subplots(figsize=(8.27, 2.5))
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "Keine Fälle: true=neutral, predicted=down im kombinierten Test.",
            ha="center",
            va="center",
        )
        fig.text(
            0.01,
            0.02,
            "Abbildung: Es gibt keine Testtage, an denen ein neutraler Tag fälschlich als 'down' klassifiziert wurde.",
            fontsize=8,
        )
        pdf.savefig(fig)
        plt.close(fig)
    else:
        dates_down = neutral_down["date"]
        labels_for_dates_down = {
            pd.to_datetime(d): f"{pd.to_datetime(d).date()} (neutral→down)" for d in dates_down
        }
        _plot_segment_rel_small_multiples(
            pdf,
            df_test,
            dates_down,
            horizon_steps=horizon,
            label_name="neutral→down",
            caption=(
                "Abbildung: Relativer Verlauf der Close-Preise für alle Testtage "
                "mit true label 'neutral', die im kombinierten Test als 'down' klassifiziert wurden."
            ),
            up_threshold=up_thr,
            down_threshold=down_thr,
            max_adverse_move_pct=cfg.get("max_adverse_move_pct"),
            labels_for_dates=labels_for_dates_down,
        )


def add_feature_importance_pages(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Fügt Seiten mit Feature-Importances für Signal- und Richtungs-Modell hinzu.

    Erwartet, dass in results['model_params'] für beide Modelle
    ein Eintrag 'feature_importances_' (Liste von floats) vorhanden ist.
    """
    cfg = results.get("config", {})
    feature_cols = cfg.get("feature_cols")
    model_params = results.get("model_params")

    if not feature_cols or not model_params:
        return

    def plot_single(fi: list[float], title: str, color: str, caption: str) -> None:
        fi_arr = np.array(fi)
        order = np.argsort(fi_arr)[::-1]
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.bar(range(len(order)), fi_arr[order], color=color)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([feature_cols[i] for i in order], rotation=45, ha="right")
        ax.set_ylabel("Importance")
        ax.set_title(title)
        plt.tight_layout()
        fig.text(0.01, 0.02, caption, fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)

    sig_params = model_params.get("signal", {})
    sig_fi = sig_params.get("feature_importances_")
    if isinstance(sig_fi, list) and len(sig_fi) == len(feature_cols):
        plot_single(
            sig_fi,
            "Feature Importance – Signal-Modell",
            color="#7b3294",
            caption="Abbildung: Wichtigkeit der Features für das Signal-Modell (neutral vs move).",
        )

    dir_params = model_params.get("direction", {})
    dir_fi = dir_params.get("feature_importances_")
    if isinstance(dir_fi, list) and len(dir_fi) == len(feature_cols):
        plot_single(
            dir_fi,
            "Feature Importance – Richtungs-Modell",
            color="#c2a5cf",
            caption="Abbildung: Wichtigkeit der Features für das Richtungs-Modell (down vs up).",
        )

    mc_params = model_params.get("multiclass", {})
    mc_fi = mc_params.get("feature_importances_") if isinstance(mc_params, dict) else None
    if isinstance(mc_fi, list) and len(mc_fi) == len(feature_cols):
        plot_single(
            mc_fi,
            "Feature Importance – Multiclass-Baseline",
            color="#5ab4ac",
            caption="Abbildung: Wichtigkeit der Features für die 3-Klassen-Baseline (neutral/up/down).",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF-Report für Zwei-Stufen-XGBoost-Experiment erzeugen.")
    parser.add_argument(
        "--exp-id",
        type=str,
        required=True,
        help="Experiment-ID, z. B. 'v1_h4_thr0p5pct_strict'.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optionaler Ausgabepfad für das PDF. "
        "Standard: notebooks/results/two_stage__<EXP_ID>_report.pdf",
    )
    args = parser.parse_args()

    project_root = find_project_root()
    exp_id = args.exp_id

    exp_config, results = load_experiment_files(project_root, exp_id)
    df = load_training_dataset(project_root, results)

    results_dir = project_root / "notebooks" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    if args.output is not None:
        pdf_path = args.output
    else:
        safe_id = exp_id.replace(" ", "_")
        pdf_path = results_dir / f"two_stage__{safe_id}_report.pdf"

    with PdfPages(pdf_path) as pdf:
        # 1) Einordnung & Metadaten
        add_title_page(pdf, exp_id, exp_config, results)
        add_legend_page(pdf)
        add_model_params_page(pdf, results)
        add_features_page(pdf, results)
        add_config_dump_pages(pdf, exp_id, exp_config, results)

        # 2) Datenübersicht
        add_distributions_page(pdf, df)
        add_label_distribution_pages(pdf, df, results)
        add_price_with_splits_page(pdf, df, project_root, exp_config, results)
        add_price_with_labels_page(pdf, df, project_root, exp_config)
        add_label_segment_pages(pdf, df, project_root, exp_config, results)

        # 3) Modelle & Metriken
        add_signal_page(pdf, results)
        add_direction_page(pdf, results)
        add_combined_page(pdf, results)
        add_combined_table_page(pdf, results)
        add_multiclass_pages(pdf, results)
        add_confusion_pages(pdf, results)
        add_confusion_tables_page(pdf, results)

        # 4) Fehlklassifikationen & zusätzliche Segment-Analysen (falls Predictions vorliegen)
        preds = load_predictions(project_root, exp_id)
        if preds is not None:
            add_misclassification_summary_page(pdf, preds)
            add_misclassification_timeline_pages(pdf, df, preds, project_root, exp_config, results)
            add_misclassified_neutral_segment_pages(pdf, df, preds, project_root, exp_config, results)

            fx_labels = load_fx_labels_for_exp(project_root, exp_id)
            if fx_labels is not None:
                add_trade_simulation_pages(pdf, preds, fx_labels, exp_config)
                if "multiclass_pred" in preds.columns:
                    add_trade_simulation_pages(
                        pdf,
                        preds,
                        fx_labels,
                        exp_config,
                        pred_col="multiclass_pred",
                        model_prefix="Multiclass-Baseline – ",
                    )

        add_feature_importance_pages(pdf, results)

    print(f"[ok] Report gespeichert unter: {pdf_path}")


if __name__ == "__main__":
    main()
