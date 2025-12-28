"""v2 Pipeline Runner: Labels -> Dataset -> Two-Stage Training -> PDF Report.

Diese v2-Pipeline ist absichtlich getrennt vom bisherigen Notebook-/Script-Setup:
- schreibt ausschließlich nach `data/processed/v2/...`
- überschreibt keine "latest" Dateien in `data/processed/fx` oder `data/processed/datasets`

Usage:
    python3 -m scripts.run_two_stage_experiment_v2 --config data/processed/v2/experiments/<EXP_ID>_config.json
    python3 -m scripts.run_two_stage_experiment_v2 --exp-id <EXP_ID>
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.data.build_training_set_v2 import build_price_only_training_dataframe_from_labels, load_labels_csv, save_dataset_csv
from src.data.label_eurusd import label_eurusd
from src.data.label_eurusd_trade import TradeLabelParams, label_eurusd_trade
from src.experiments.v2_config import (
    DATA_PROCESSED_V2,
    ExperimentConfig,
    load_experiment_config,
    save_experiment_config,
)
from src.models.train_two_stage_v2 import ThresholdSearchConfig, train_two_stage_v2


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


def _ensure_mpl_config_dir() -> None:
    # Matplotlib versucht sonst in ~/.matplotlib zu schreiben (kann im Sandbox-Setup scheitern).
    mpl_dir = DATA_PROCESSED_V2 / ".mplconfig"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(mpl_dir)


def _generate_report_pdf(results: Dict[str, Any], *, exp_id: str, out_path: Path) -> None:
    _ensure_mpl_config_dir()

    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    def plot_cm(ax, cm, labels, title: str) -> None:
        ax.imshow(cm, cmap="Blues")
        ax.set_title(title, fontsize=10)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=8)
        for (i, j), v in pd.DataFrame(cm).stack().items():
            ax.text(j, i, int(v), ha="center", va="center", fontsize=8)

    cfg = results.get("config", {})
    signal = results.get("signal", {})
    direction = results.get("direction", {})
    combined = results.get("combined_test", {})
    data_params = cfg.get("data_params") or {}
    label_params = cfg.get("label_params") or {}
    threshold_search = cfg.get("threshold_search") or {}
    cost_model = cfg.get("cost_model") or {}

    with PdfPages(out_path) as pdf:
        # Page 1: Config summary
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.clf()
        y = 0.95

        def write(text: str, size: int = 10, bold: bool = False) -> None:
            nonlocal y
            fig.text(0.05, y, text, fontsize=size, weight="bold" if bold else "normal")
            y -= 0.03

        write("Two-Stage XGBoost – v2 Report", size=16, bold=True)
        write(f"EXP_ID: {exp_id}", size=12)
        y -= 0.02
        write("Run paths:", bold=True)
        for k in ["config_path", "labels_path", "dataset_path", "results_path", "predictions_path", "report_path", "manifest_path"]:
            if k in cfg:
                write(f"- {k}: {cfg.get(k)}", size=9)
        y -= 0.01

        write("Split/Thresholds:", bold=True)
        for k in ["test_start", "train_frac_within_pretest", "signal_threshold_trade", "direction_threshold_down", "direction_threshold_up"]:
            if k in cfg:
                write(f"- {k}: {cfg.get(k)}", size=9)
        y -= 0.01

        if threshold_search:
            write("Threshold search:", bold=True)
            for k, v in threshold_search.items():
                write(f"- {k}: {v}", size=9)
            y -= 0.01

        if cost_model:
            write("Cost model:", bold=True)
            for k, v in cost_model.items():
                write(f"- {k}: {v}", size=9)
            y -= 0.01

        y -= 0.02
        if data_params:
            write("Data params:", bold=True)
            for k, v in data_params.items():
                write(f"- {k}: {v}", size=9)
        y -= 0.02
        if label_params:
            write("Label params:", bold=True)
            for k, v in label_params.items():
                write(f"- {k}: {v}", size=9)

        pdf.savefig(fig)
        plt.close(fig)

        # Page 2: Confusion matrices
        fig, axes = plt.subplots(3, 3, figsize=(11, 7.5))
        fig.suptitle("Confusion Matrices", fontsize=14, weight="bold")

        # Signal matrices (neutral/move)
        for col, split in enumerate(["train", "val", "test"]):
            cm = (signal.get(split, {}) or {}).get("confusion_matrix", [])
            if cm:
                plot_cm(axes[0, col], cm, ["neutral", "move"], f"Signal – {split}")
            else:
                axes[0, col].axis("off")

        # Direction matrices (down/up)
        for col, split in enumerate(["train", "val", "test"]):
            cm = (direction.get(split, {}) or {}).get("confusion_matrix", [])
            if cm:
                plot_cm(axes[1, col], cm, ["down", "up"], f"Direction – {split}")
            else:
                axes[1, col].axis("off")

        # Combined test (neutral/up/down)
        for col in range(3):
            axes[2, col].axis("off")
        cmc = (combined or {}).get("confusion_matrix", [])
        if cmc:
            ax = axes[2, 1]
            ax.axis("on")
            plot_cm(ax, cmc, ["neutral", "up", "down"], "Combined – test (neutral/up/down)")

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        # Page 3: Full config dump (as JSON-ish text for auditability)
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.clf()
        fig.text(0.05, 0.96, f"EXP_ID: {exp_id}", fontsize=11, weight="bold")
        fig.text(0.05, 0.93, "Full config (from results['config']):", fontsize=10, weight="bold")

        import pprint

        text = pprint.pformat(cfg, width=110, compact=False, sort_dicts=True)
        fig.text(0.05, 0.90, text, fontsize=7, family="monospace", va="top")
        pdf.savefig(fig)
        plt.close(fig)


def run(cfg_obj: ExperimentConfig) -> None:
    cfg = cfg_obj.cfg
    exp_id = cfg_obj.exp_id
    data_cfg = dict(cfg.get("data", {}))
    label_cfg = dict(cfg.get("label", {}))
    model_cfg = dict(cfg.get("model", {}))

    # 1) Labels
    label_mode = str(label_cfg.get("mode", "close_path"))
    price_source = str(data_cfg.get("price_source", "yahoo"))
    drop_weekends = bool(data_cfg.get("drop_weekends", False))
    date_shift_days = int(data_cfg.get("date_shift_days", 0))

    labels_out = cfg_obj.labels_dir / f"eurusd_labels__{exp_id}.csv"

    if label_mode == "close_path":
        # passt 1:1 zur bisherigen label_eurusd-Logik
        params = dict(label_cfg)
        params.pop("mode", None)
        df_labels = label_eurusd(
            price_source=price_source,
            drop_weekends=drop_weekends,
            **params,
        )
    elif label_mode == "tp_sl":
        tlp = TradeLabelParams(
            horizon_days=int(label_cfg.get("horizon_days", 15)),
            entry=str(label_cfg.get("entry", "next_open")),
            tp_pct=float(label_cfg.get("tp_pct", 0.02)),
            sl_mode=str(label_cfg.get("sl_mode", "fixed_pct")),
            sl_pct=float(label_cfg.get("sl_pct", 0.01)),
            atr_window=int(label_cfg.get("atr_window", 14)),
            atr_mult=float(label_cfg.get("atr_mult", 1.0)),
            intraday_tie_breaker=str(label_cfg.get("intraday_tie_breaker", "stop")),
            conflict_policy=str(label_cfg.get("conflict_policy", "first")),
        )
        df_labels = label_eurusd_trade(
            price_source=price_source,
            drop_weekends=drop_weekends,
            date_shift_days=date_shift_days,
            params=tlp,
        )
    else:
        raise ValueError(f"Unbekannter label.mode='{label_mode}'.")

    labels_out.parent.mkdir(parents=True, exist_ok=True)
    df_labels.to_csv(labels_out)

    # 2) Dataset (price_only)
    df_lab_csv = load_labels_csv(labels_out)
    df_train = build_price_only_training_dataframe_from_labels(df_lab_csv)
    ds_out = cfg_obj.datasets_dir / f"eurusd_price_training__{exp_id}.csv"
    save_dataset_csv(df_train, ds_out)

    # 3) Train
    search = ThresholdSearchConfig(
        thr_min=float(model_cfg.get("thr_min", 0.3)),
        thr_max=float(model_cfg.get("thr_max", 0.7)),
        thr_step=float(model_cfg.get("thr_step", 0.025)),
        min_pred_down=int(model_cfg.get("min_pred_down", 5)),
        min_pred_up=int(model_cfg.get("min_pred_up", 5)),
    )

    tp_cost = float(model_cfg.get("tp_cost_pct", label_cfg.get("tp_pct", label_cfg.get("up_threshold", 0.02))))
    sl_cost = float(model_cfg.get("sl_cost_pct", label_cfg.get("sl_pct", label_cfg.get("max_adverse_move_pct", 0.01) or 0.01)))

    results, pred_df = train_two_stage_v2(
        dataset_path=ds_out,
        test_start=str(model_cfg.get("test_start", "2025-01-01")),
        train_frac_within_pretest=float(model_cfg.get("train_frac_within_pretest", 0.8)),
        feature_cols=model_cfg.get("feature_cols"),
        search=search,
        stake_up=float(model_cfg.get("stake_up", 100.0)),
        stake_down=float(model_cfg.get("stake_down", 100.0)),
        tp_pct=tp_cost,
        sl_pct=sl_cost,
    )

    res_json = cfg_obj.results_dir / f"two_stage__{exp_id}.json"
    res_pred = cfg_obj.results_dir / f"two_stage__{exp_id}_predictions.csv"
    # Manifest/Metadata (alles an einem Ort)
    manifest_path = cfg_obj.results_dir / f"two_stage__{exp_id}_manifest.json"

    # metrics csv (kurz)
    rows = []
    for model_key, pos_label in [("signal", "move"), ("direction", "up")]:
        for split in ["train", "val", "test"]:
            rep = results[model_key][split]["report"]
            cls = rep.get(pos_label, {})
            rows.append(
                {
                    "model": model_key,
                    "split": split,
                    "precision_pos": cls.get("precision"),
                    "recall_pos": cls.get("recall"),
                    "f1_pos": cls.get("f1-score"),
                }
            )
    metrics_df = pd.DataFrame(rows)
    metrics_path = cfg_obj.results_dir / f"two_stage__{exp_id}_metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)

    # 4) PDF
    pdf_path = cfg_obj.reports_dir / f"two_stage__{exp_id}.pdf"
    cfg_path = cfg_obj.exp_dir / f"{exp_id}_config.json"

    # Config-Block für Ergebnisse/PDF (aus einer Quelle)
    results_cfg = results.get("config", {})
    results_cfg["exp_id"] = exp_id
    results_cfg["price_source"] = price_source
    results_cfg["label_mode"] = label_mode
    results_cfg["data_params"] = data_cfg
    results_cfg["label_params"] = label_cfg
    results_cfg["config_path"] = str(cfg_path)
    results_cfg["labels_path"] = str(labels_out)
    results_cfg["dataset_path"] = str(ds_out)
    results_cfg["results_path"] = str(res_json)
    results_cfg["predictions_path"] = str(res_pred)
    results_cfg["report_path"] = str(pdf_path)
    results_cfg["manifest_path"] = str(manifest_path)
    results["config"] = results_cfg

    # Erst jetzt persistieren (damit paths garantiert im JSON/PDF landen)
    _write_json(res_json, results)
    pred_df.to_csv(res_pred, index=False)

    manifest = {
        "exp_id": exp_id,
        "config_path": str(cfg_path),
        "labels_path": str(labels_out),
        "dataset_path": str(ds_out),
        "results_path": str(res_json),
        "predictions_path": str(res_pred),
        "metrics_path": str(metrics_path),
        "report_path": str(pdf_path),
    }
    _write_json(manifest_path, manifest)

    _generate_report_pdf(results, exp_id=exp_id, out_path=pdf_path)

    print("[ok] v2 pipeline fertig:")
    print("   config:", DATA_PROCESSED_V2 / "experiments" / f"{exp_id}_config.json")
    print("   labels:", labels_out)
    print("   dataset:", ds_out)
    print("   results:", res_json)
    print("   preds  :", res_pred)
    print("   report :", pdf_path)
    print("   manifest:", manifest_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="v2 Two-Stage Experiment Runner.")
    parser.add_argument("--exp-id", type=str, default=None, help="Lädt config aus data/processed/v2/experiments/<EXP_ID>_config.json")
    parser.add_argument("--config", type=Path, default=None, help="Pfad zu einer v2 config JSON Datei (wird canonical gespeichert).")
    args = parser.parse_args()

    if args.exp_id:
        cfg_obj = load_experiment_config(args.exp_id)
    elif args.config:
        cfg = _read_json(args.config)
        cfg_obj = save_experiment_config(cfg, exp_id=cfg.get("exp_id"))
    else:
        raise SystemExit("Bitte --exp-id oder --config angeben.")

    run(cfg_obj)


if __name__ == "__main__":
    main()
