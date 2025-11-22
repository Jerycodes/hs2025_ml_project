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
from pathlib import Path
import textwrap
from typing import Dict, Any

import matplotlib.pyplot as plt
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


def add_title_page(pdf: PdfPages, exp_id: str, exp_config: Dict[str, Any], results: Dict[str, Any]) -> None:
    """Fügt eine Titelseite mit den wichtigsten Metadaten und einer Kurzbeschreibung hinzu."""
    cfg = results.get("config", {})
    label_params = exp_config.get("label_params", {})

    fig = plt.figure(figsize=(8.27, 11.69))  # A4-Hochformat in Zoll
    fig.clf()

    # y steuert die vertikale Position (von oben nach unten)
    y = 0.9
    # kleinerer Zeilenabstand, damit mehr Text auf die Seite passt
    line_height = 0.028

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
    y -= line_height

    write("Datensatz & Splits:", bold=True)
    # dataset_path kann sehr lang sein → enger umbrechen
    write(f"- dataset_path: {cfg.get('dataset_path')}", max_width=80)
    write(f"- test_start: {cfg.get('test_start')}")
    write(f"- train_frac_within_pretest: {cfg.get('train_frac_within_pretest')}")
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
    """Fügt eine Seite mit einer vollständigen Feature-Liste hinzu.

    So wird sichergestellt, dass alle genutzten Feature-Namen vollständig
    im Report sichtbar sind (ohne Abschneiden an der Titelseite).
    """
    cfg = results.get("config", {})
    feature_cols = cfg.get("feature_cols", [])
    if not feature_cols:
        return

    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.axis("off")
    ax.set_title("Verwendete Features (FEATURE_COLS)", fontsize=12, weight="bold", pad=10)

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

    table = ax.table(
        cellText=rows,
        colLabels=["#", "feature_name", "description"],
        loc="center",
        cellLoc="left",
        # etwas breitere feature_name-Spalte, dafür minimal weniger Platz für description
        colWidths=[0.05, 0.35, 0.60],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1.05, 1.15)

    pdf.savefig(fig)
    plt.close(fig)


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

    pdf.savefig(fig)
    plt.close(fig)


def _plot_binary_metrics(pdf: PdfPages, results: Dict[str, Any], key: str, pos_label: str, title: str) -> None:
    """Hilfsfunktion: Balkenplot für Precision/Recall/F1 einer positiven Klasse."""
    metrics = results[key]
    splits = ["train", "val", "test"]

    prec = []
    rec = []
    f1 = []

    for split in splits:
        rep = metrics[split]["report"]
        stats = rep[pos_label]
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
        "Abbildung: Precision, Recall und F1 der positiven Klasse je Split (train/val/test).",
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

    rows = []
    for split in splits:
        rep = metrics[split]["report"]
        stats = rep[pos_label]
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
    _plot_binary_metrics(
        pdf,
        results,
        key="signal",
        pos_label="move",
        title="Signal-Modell – Kennzahlen für Klasse 'move' (train/val/test)",
    )
    _add_binary_tables_page(
        pdf,
        results,
        key="signal",
        pos_label="move",
        title="Signal-Modell – Tabelle (Klasse 'move')",
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


def add_confusion_pages(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Fügt Confusion-Matrix-Seiten für Signal-, Richtungs- und Kombi-Modell hinzu.

    - Signal: train/val/test (2x2) auf einer Seite
    - Richtung: train/val/test (2x2) auf einer Seite
    - Kombiniert: Test (3-Klassen) auf einer Seite
    """
    sns.set(style="white")

    # ---------------- Signal: neutral vs. move (train/val/test) ----------------
    splits = ["train", "val", "test"]
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
    for ax, split in zip(axes, splits):
        cm = np.array(results["signal"][split]["confusion_matrix"])
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=["neutral", "move"],
            yticklabels=["neutral", "move"],
            ax=ax,
        )
        ax.set_title(f"Signal – {split}")
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
        cm = np.array(results["direction"][split]["confusion_matrix"])
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Reds",
            xticklabels=["down", "up"],
            yticklabels=["down", "up"],
            ax=ax,
        )
        ax.set_title(f"Richtung – {split}")
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

    # ---------------- Kombiniert: neutral / up / down (Test) -------------------
    cm_combined = np.array(results["combined_test"]["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    sns.heatmap(
        cm_combined,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=["neutral", "up", "down"],
        yticklabels=["neutral", "up", "down"],
        ax=ax,
    )
    ax.set_title("Confusion Matrix – Test (neutral / up / down)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    plt.tight_layout(rect=(0.02, 0.10, 0.98, 0.95))
    fig.text(
        0.01,
        0.02,
        "Abbildung: Confusion-Matrix des kombinierten Modells (neutral/up/down) auf dem Test-Split.",
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

    fig, ax = plt.subplots(figsize=(8.27, 4.0))
    ax.axis("off")
    ax.set_title("Konfusionsmatrizen – Zählwerte (TN/FP/FN/TP)", fontsize=12, weight="bold", pad=10)

    col_labels = ["modell", "split", "TN", "FP", "FN", "TP"]
    table = ax.table(
        cellText=rows,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.3, 1.3)

    fig.text(
        0.01,
        0.02,
        "Tabelle: Zählwerte der Konfusionsmatrizen (TN/FP/FN/TP) "
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


def _ensure_close_with_labels(
    df: pd.DataFrame, project_root: Path, exp_config: Dict[str, Any]
) -> pd.DataFrame:
    """Hilfsfunktion: sorgt dafür, dass df die Spalte 'Close' enthält.

    Falls nötig, werden Close-Kurse aus der Label-Datei ergänzt.
    """
    df_plot = df.copy()
    if "Close" in df_plot.columns:
        return df_plot

    safe_id = str(exp_config.get("exp_id")).replace(" ", "_")
    fx_dir = project_root / "data" / "processed" / "fx"
    labels_path = fx_dir / f"eurusd_labels__{safe_id}.csv"
    if not labels_path.is_file():
        labels_path = fx_dir / "eurusd_labels.csv"
    if labels_path.is_file():
        fx = pd.read_csv(labels_path, parse_dates=["Date"])
        fx = fx.rename(columns={"Date": "date"})
        df_plot = df_plot.merge(fx[["date", "Close"]], on="date", how="left")
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
    max_segments: int = 25,
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
    start_dates = [d for d in start_dates if d in idx][:max_segments]

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.set_facecolor("white")
    ax.plot(df.index, df["Close"], color="lightgray", linewidth=1, label="Close (gesamt)")

    show_thr_label = True

    for t0 in start_dates:
        pos = idx.get_loc(t0)
        end_pos = pos + horizon_steps
        if end_pos >= len(idx):
            # wie im Labeler: wenn nicht genug Zukunftsdaten vorhanden sind,
            # wird dieses Segment übersprungen
            continue
        seg = df.iloc[pos : end_pos + 1]
        start_close = seg["Close"].iloc[0]

        ax.plot(seg.index, seg["Close"], color=color, linewidth=2, alpha=0.8)
        ax.scatter(seg.index[0], seg["Close"].iloc[0], color=color, s=30)
        ax.scatter(seg.index[-1], seg["Close"].iloc[-1], color=color, s=50, marker="x")

        # Threshold-Markierung (optional)
        if label_name == "up" and up_threshold is not None:
            thr = start_close * (1.0 + up_threshold)
            ax.scatter(
                seg.index[-1],
                thr,
                color="blue",
                marker="^",
                s=40,
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
                s=40,
                label="down-threshold" if show_thr_label else None,
            )
            show_thr_label = False

    ax.set_title(title)
    ax.set_xlabel("Datum")
    ax.set_ylabel("Close")
    if not show_thr_label:
        ax.legend(loc="best", fontsize=8)
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
    max_segments: int = 16,
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
    start_dates = [d for d in start_dates if d in idx][:max_segments]

    segments: list[tuple[str, range, np.ndarray]] = []
    for t0 in start_dates:
        pos = idx.get_loc(t0)
        end_pos = pos + horizon_steps
        if end_pos >= len(idx):
            continue
        seg = df.iloc[pos : end_pos + 1]
        start_close = seg["Close"].iloc[0]
        rel = seg["Close"] / start_close - 1.0
        if labels_for_dates is not None:
            seg_label = labels_for_dates.get(t0, str(t0))
        else:
            seg_label = seg.index[0]
        segments.append((str(seg_label), range(len(rel)), rel.to_numpy()))

    if not segments:
        fig, ax = plt.subplots(figsize=(8.27, 3.0))
        ax.text(0.5, 0.5, f"Keine Segmente für label='{label_name}'.", ha="center", va="center")
        ax.axis("off")
        fig.text(0.01, 0.035, caption, fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)
        return

    if max_segments is not None:
        segments = segments[:max_segments]

    segments_per_page = 6
    nrows, ncols = 3, 2
    yticks = [-0.05, -0.025, 0.0, 0.025, 0.05]

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
        for ax in axes_flat:
            ax.set_ylim(yticks[0], yticks[-1])
            ax.set_yticks(yticks)
            ax.grid(True, alpha=0.3)
            # X-Ticks immer 0..horizon_steps, damit die Skala einheitlich ist
            xticks = list(range(horizon_steps + 1))
            ax.set_xticks(xticks)
            ax.set_xticklabels([str(t) for t in xticks])

        # Segmente plotten
        for ax, (label, steps, rel_values) in zip(axes_flat, page_segments):
            ax.plot(list(steps), rel_values, marker="o")
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
                ax.set_ylabel("rel_close")
            else:
                ax.set_ylabel("")

        title = f"Relativer Verlauf der Segmente (label='{label_name}')"
        if len(segments) > segments_per_page:
            page_no = page_start // segments_per_page + 1
            title += f" – Seite {page_no}"
        fig.suptitle(title, y=0.97)
        # mehr Platz nach unten für X-Tick-Labels lassen
        fig.tight_layout(rect=(0.06, 0.20, 0.98, 0.90))

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

        # 2) Datenübersicht
        add_distributions_page(pdf, df)
        add_label_distribution_pages(pdf, df, results)
        add_price_with_labels_page(pdf, df, project_root, exp_config)
        add_label_segment_pages(pdf, df, project_root, exp_config, results)

        # 3) Modelle & Metriken
        add_signal_page(pdf, results)
        add_direction_page(pdf, results)
        add_combined_page(pdf, results)
        add_combined_table_page(pdf, results)
        add_confusion_pages(pdf, results)
        add_confusion_tables_page(pdf, results)

        # 4) Fehlklassifikationen & zusätzliche Segment-Analysen (falls Predictions vorliegen)
        preds = load_predictions(project_root, exp_id)
        if preds is not None:
            add_misclassification_summary_page(pdf, preds)
            add_misclassified_neutral_segment_pages(pdf, df, preds, project_root, exp_config, results)

        add_feature_importance_pages(pdf, results)

    print(f"[ok] Report gespeichert unter: {pdf_path}")


if __name__ == "__main__":
    main()
