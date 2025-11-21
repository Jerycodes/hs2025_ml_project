"""Erzeugt einen PDF-Report für Up-Only / Down-Only-Experimente (s-Experimente).

Der Report fasst für eine gegebene EXP_ID die wichtigsten Metadaten,
Datensplits und Metriken der beiden Binärmodelle zusammen:

- up vs. not-up  (aus notebooks/results/up_only__<EXP_ID>.json)
- down vs. not-down (aus notebooks/results/down_only__<EXP_ID>.json)

Voraussetzungen:
- Data-Prep-Notebook wurde für diese EXP_ID ausgeführt
  -> es existiert data/processed/experiments/<EXP_ID>_config.json
- Up-/Down-Only-Notebooks wurden für diese EXP_ID ausgeführt
  -> es existieren notebooks/results/up_only__<EXP_ID>.json
     und notebooks/results/down_only__<EXP_ID>.json

Verwendung (aus Projektwurzel):

    python -m scripts.generate_updown_report --exp-id s1_h4_thr0p5pct_tol0p3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import seaborn as sns


def find_project_root(start: Path | None = None) -> Path:
    """Läuft von `start` nach oben, bis ein Ordner `src` gefunden wird.

    So können wir das Script aus beliebigen Unterordnern ausführen, ohne
    Pfade manuell anpassen zu müssen.
    """
    if start is None:
        start = Path.cwd()
    root = start
    while not (root / "src").is_dir():
        if root.parent == root:
            raise RuntimeError("Projektwurzel mit Unterordner 'src' nicht gefunden.")
        root = root.parent
    return root


def load_experiment_files(
    project_root: Path, exp_id: str
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Lädt Config- und Up-/Down-JSON für ein s-Experiment.

    Erwartet:
    - data/processed/experiments/<EXP_ID>_config.json
    - notebooks/results/up_only__<EXP_ID>.json
    - notebooks/results/down_only__<EXP_ID>.json
    """
    safe_id = exp_id.replace(" ", "_")

    cfg_path = (
        project_root / "data" / "processed" / "experiments" / f"{safe_id}_config.json"
    )
    up_path = project_root / "notebooks" / "results" / f"up_only__{safe_id}.json"
    down_path = project_root / "notebooks" / "results" / f"down_only__{safe_id}.json"

    if not cfg_path.is_file():
        raise FileNotFoundError(f"Config-Datei nicht gefunden: {cfg_path}")
    if not up_path.is_file():
        raise FileNotFoundError(f"Up-Result-Datei nicht gefunden: {up_path}")
    if not down_path.is_file():
        raise FileNotFoundError(f"Down-Result-Datei nicht gefunden: {down_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        exp_config = json.load(f)
    with up_path.open("r", encoding="utf-8") as f:
        up_results = json.load(f)
    with down_path.open("r", encoding="utf-8") as f:
        down_results = json.load(f)

    return exp_config, up_results, down_results


def load_training_dataset(project_root: Path, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Lädt den Trainingsdatensatz, dessen Pfad in cfg['dataset_path'] steht."""
    ds_path_str = cfg.get("dataset_path")
    if not ds_path_str:
        raise KeyError("dataset_path fehlt im config-Block.")
    ds_path = Path(ds_path_str)
    if not ds_path.is_file():
        ds_path = (project_root / ds_path).resolve()
    if not ds_path.is_file():
        raise FileNotFoundError(f"Trainingsdatensatz nicht gefunden: {ds_path}")

    df = pd.read_csv(ds_path, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def add_title_page(
    pdf: PdfPages,
    exp_id: str,
    exp_config: Dict[str, Any],
    up_cfg: Dict[str, Any],
) -> None:
    """Titelseite mit Label-Parametern, Datensatzpfad und Aufgabenbeschreibung."""
    label_params = exp_config.get("label_params", {})
    cfg = up_cfg.get("config", {})

    fig = plt.figure(figsize=(8.27, 11.69))  # A4 Hochformat
    fig.clf()

    y = 0.9
    line_height = 0.03

    def write(text: str, *, size: int = 10, bold: bool = False) -> None:
        nonlocal y
        if bold:
            fig.text(0.04, y, text, fontsize=size, weight="bold")
        else:
            fig.text(0.04, y, text, fontsize=size)
        y -= line_height

    write("Up-/Down-Only XGBoost – Experiment-Report", size=16, bold=True)
    write(f"Experiment-ID: {exp_id}", size=12)
    y -= line_height

    write("Dieses Dokument fasst die wichtigsten Parameter und Metriken", size=9)
    write("der Up-/Down-Only-Modelle für EURUSD-News zusammen.", size=9)
    y -= line_height

    write("Label-Parameter:", bold=True)
    write(f"- horizon_days: {label_params.get('horizon_days')}")
    write(f"- up_threshold: {label_params.get('up_threshold')}")
    write(f"- down_threshold: {label_params.get('down_threshold')}")
    write(f"- strict_monotonic: {label_params.get('strict_monotonic')}")
    if "max_adverse_move_pct" in label_params:
        write(f"- max_adverse_move_pct: {label_params.get('max_adverse_move_pct')}")
    y -= line_height

    write("Datensatz & Splits:", bold=True)
    write(f"- dataset_path: {cfg.get('dataset_path')}")
    write(f"- test_start: {cfg.get('test_start')}")
    write(f"- train_frac_within_pretest: {cfg.get('train_frac_within_pretest')}")

    pdf.savefig(fig)
    plt.close(fig)


def add_feature_page(pdf: PdfPages, up_cfg: Dict[str, Any]) -> None:
    """Liste aller verwendeten Features (feature_cols) als Tabelle."""
    feature_cols = up_cfg.get("config", {}).get("feature_cols", [])
    if not feature_cols:
        return

    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.axis("off")
    ax.set_title("Verwendete Features (FEATURE_COLS)", fontsize=12, weight="bold", pad=10)

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


def add_distributions_page(pdf: PdfPages, df: pd.DataFrame) -> None:
    """Verteilungen von label/signal/direction (wie im Zwei-Stufen-Report)."""
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


def _plot_binary_metrics(
    pdf: PdfPages,
    metrics: Dict[str, Any],
    model_name: str,
    pos_label_id: str,
    pos_label_name: str,
) -> None:
    """Balkendiagramm für Precision/Recall/F1 einer Binär-Klasse."""
    splits = ["train", "val", "test"]
    prec, rec, f1 = [], [], []

    for split in splits:
        rep = metrics[split]["report"]
        stats = rep.get(pos_label_id, {})
        prec.append(stats.get("precision", np.nan))
        rec.append(stats.get("recall", np.nan))
        f1.append(stats.get("f1-score", np.nan))

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
    ax.set_title(f"{model_name} – Kennzahlen für Klasse '{pos_label_name}'")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    pdf.savefig(fig)
    plt.close(fig)


def _add_binary_table_page(
    pdf: PdfPages,
    metrics: Dict[str, Any],
    model_name: str,
    pos_label_id: str,
    pos_label_name: str,
) -> None:
    """Tabelle Precision/Recall/F1 für eine Binär-Klasse über train/val/test."""
    splits = ["train", "val", "test"]
    rows = []
    for split in splits:
        rep = metrics[split]["report"]
        stats = rep.get(pos_label_id, {})
        rows.append(
            [
                split,
                stats.get("precision", np.nan),
                stats.get("recall", np.nan),
                stats.get("f1-score", np.nan),
                stats.get("support", np.nan),
            ]
        )

    fig, ax = plt.subplots(figsize=(8.27, 3.5))
    ax.axis("off")
    ax.set_title(
        f"{model_name} – Tabelle (Klasse '{pos_label_name}')",
        fontsize=12,
        weight="bold",
        pad=10,
    )

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


def add_up_down_pages(
    pdf: PdfPages,
    up_results: Dict[str, Any],
    down_results: Dict[str, Any],
) -> None:
    """Fügt je zwei Seiten für das Up- und Down-Modell hinzu."""
    up_metrics = up_results["up_model"]
    down_metrics = down_results["down_model"]

    _plot_binary_metrics(
        pdf,
        up_metrics,
        model_name="Up-Modell (up vs not-up)",
        pos_label_id="1",
        pos_label_name="up",
    )
    _add_binary_table_page(
        pdf,
        up_metrics,
        model_name="Up-Modell (up vs not-up)",
        pos_label_id="1",
        pos_label_name="up",
    )

    _plot_binary_metrics(
        pdf,
        down_metrics,
        model_name="Down-Modell (down vs not-down)",
        pos_label_id="1",
        pos_label_name="down",
    )
    _add_binary_table_page(
        pdf,
        down_metrics,
        model_name="Down-Modell (down vs not-down)",
        pos_label_id="1",
        pos_label_name="down",
    )


def add_confusion_page(
    pdf: PdfPages,
    up_results: Dict[str, Any],
    down_results: Dict[str, Any],
) -> None:
    """Konfusionsmatrizen (Test-Split) für Up- und Down-Modell."""
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
    sns.set(style="white")

    cm_up = np.array(up_results["up_model"]["test"]["confusion_matrix"])
    sns.heatmap(
        cm_up,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=["not-up", "up"],
        yticklabels=["not-up", "up"],
        ax=axes[0],
    )
    axes[0].set_title("Confusion Matrix – Test (up vs not-up)")
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("True")

    cm_down = np.array(down_results["down_model"]["test"]["confusion_matrix"])
    sns.heatmap(
        cm_down,
        annot=True,
        fmt="d",
        cmap="Reds",
        xticklabels=["not-down", "down"],
        yticklabels=["not-down", "down"],
        ax=axes[1],
    )
    axes[1].set_title("Confusion Matrix – Test (down vs not-down)")
    axes[1].set_xlabel("Predicted")
    axes[1].set_ylabel("True")

    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PDF-Report für Up-/Down-Only-XGBoost-Experimente erzeugen."
    )
    parser.add_argument(
        "--exp-id",
        type=str,
        required=True,
        help="Experiment-ID, z. B. 's1_h4_thr0p5pct_tol0p3'.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Optionaler Ausgabepfad für das PDF. "
            "Standard: notebooks/results/updown__<EXP_ID>_report.pdf"
        ),
    )
    args = parser.parse_args()

    project_root = find_project_root()
    exp_id = args.exp_id

    exp_config, up_results, down_results = load_experiment_files(project_root, exp_id)
    up_cfg = up_results.get("config", {})
    df = load_training_dataset(project_root, up_cfg)

    results_dir = project_root / "notebooks" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    if args.output is not None:
        pdf_path = args.output
    else:
        safe_id = exp_id.replace(" ", "_")
        pdf_path = results_dir / f"updown__{safe_id}_report.pdf"

    with PdfPages(pdf_path) as pdf:
        add_title_page(pdf, exp_id, exp_config, up_results)
        add_feature_page(pdf, up_results)
        add_distributions_page(pdf, df)
        add_up_down_pages(pdf, up_results, down_results)
        add_confusion_page(pdf, up_results, down_results)

    print(f"[ok] Up/Down-Report gespeichert unter: {pdf_path}")


if __name__ == "__main__":
    main()

