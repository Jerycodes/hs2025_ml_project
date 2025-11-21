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

    # Tabelle mit zwei Spalten: Index und Feature-Name
    rows = [[i, col] for i, col in enumerate(feature_cols)]
    table = ax.table(
        cellText=rows,
        colLabels=["#", "feature_name"],
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.2, 1.2)

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

    write("Legende & Begriffe", size=14, bold=True)
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

    write("Feature-Abkürzungen (Auswahl):", bold=True)
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
    plt.tight_layout()
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
    plt.tight_layout()
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
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def add_confusion_tables_page(pdf: PdfPages, results: Dict[str, Any]) -> None:
    """Fügt eine Seite mit TN/FP/FN/TP-Tabellen für Signal- und Richtungsmodell hinzu."""
    rows = []
    for model_key, model_name in [("signal", "signal (neutral vs. move)"), ("direction", "direction (down vs. up)")]:
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
    table.scale(1.1, 1.2)

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

    sns.countplot(
        x="direction",
        data=df[df["signal"] == 1],
        ax=axes[2],
        order=[0, 1],
    )
    axes[2].set_title("Richtung-Verteilung (nur signal==1)")
    axes[2].set_xlabel("direction (0=down, 1=up)")
    axes[2].set_ylabel("Anzahl")

    plt.tight_layout()
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

    pdf.savefig(fig)
    plt.close(fig)


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

    def plot_single(fi: list[float], title: str, color: str) -> None:
        fi_arr = np.array(fi)
        order = np.argsort(fi_arr)[::-1]
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.bar(range(len(order)), fi_arr[order], color=color)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([feature_cols[i] for i in order], rotation=45, ha="right")
        ax.set_ylabel("Importance")
        ax.set_title(title)
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

    sig_params = model_params.get("signal", {})
    sig_fi = sig_params.get("feature_importances_")
    if isinstance(sig_fi, list) and len(sig_fi) == len(feature_cols):
        plot_single(sig_fi, "Feature Importance – Signal-Modell", color="#7b3294")

    dir_params = model_params.get("direction", {})
    dir_fi = dir_params.get("feature_importances_")
    if isinstance(dir_fi, list) and len(dir_fi) == len(feature_cols):
        plot_single(dir_fi, "Feature Importance – Richtungs-Modell", color="#c2a5cf")

    # Direction: down vs. up (nur Tage mit signal==1)
    cm_dir = np.array(results["direction"]["test"]["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(4, 4))
    sns.heatmap(
        cm_dir,
        annot=True,
        fmt="d",
        cmap="Reds",
        xticklabels=["down", "up"],
        yticklabels=["down", "up"],
        ax=ax,
    )
    ax.set_title("Confusion Matrix – Test (Richtung: down vs. up)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    pdf.savefig(fig)
    plt.close(fig)


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
        add_price_with_labels_page(pdf, df, project_root, exp_config)

        # 3) Modelle & Metriken
        add_signal_page(pdf, results)
        add_direction_page(pdf, results)
        add_combined_page(pdf, results)
        add_confusion_pages(pdf, results)
        add_confusion_tables_page(pdf, results)
        add_feature_importance_pages(pdf, results)

    print(f"[ok] Report gespeichert unter: {pdf_path}")


if __name__ == "__main__":
    main()
