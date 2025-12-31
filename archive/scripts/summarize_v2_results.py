"""Sammelt und vergleicht v2-Experiment-Ergebnisse.

Liest pro EXP_ID (v2) die Artefakte aus `data/processed/v2/`:
- Results JSON:     `data/processed/v2/results/two_stage__<EXP_ID>.json`
- Predictions CSV: `data/processed/v2/results/two_stage__<EXP_ID>_predictions.csv`
- Labels CSV:      `data/processed/v2/fx/eurusd_labels__<EXP_ID>.csv` (optional)
- Manifest JSON:   `data/processed/v2/results/two_stage__<EXP_ID>_manifest.json` (optional)

Schreibt eine aggregierte Summary als CSV (und optional Markdown) unter:
`data/processed/v2/summary/`.

Beispiel:
    python3 -m scripts.summarize_v2_results
    python3 -m scripts.summarize_v2_results --filter at_v2__yahoo
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

from src.experiments.v2_config import DATA_PROCESSED_V2


RESULTS_DIR = DATA_PROCESSED_V2 / "results"
FX_DIR = DATA_PROCESSED_V2 / "fx"
SUMMARY_DIR = DATA_PROCESSED_V2 / "summary"


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _safe_get(d: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _flatten(prefix: str, d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, (dict, list)):
            out[key] = json.dumps(v, ensure_ascii=False)
        else:
            out[key] = v
    return out


def iter_exp_ids(results_dir: Path) -> Iterable[str]:
    for p in sorted(results_dir.glob("two_stage__*.json")):
        name = p.name
        if name.endswith("_manifest.json"):
            continue
        exp_id = name[len("two_stage__") : -len(".json")]
        yield exp_id


def load_predictions(exp_id: str) -> pd.DataFrame | None:
    p = RESULTS_DIR / f"two_stage__{exp_id}_predictions.csv"
    if not p.is_file():
        return None
    return pd.read_csv(p, parse_dates=["date"])


def load_labels(exp_id: str) -> pd.DataFrame | None:
    p = FX_DIR / f"eurusd_labels__{exp_id}.csv"
    if not p.is_file():
        return None
    return pd.read_csv(p, parse_dates=["Date"])


def _counts(series: pd.Series) -> Dict[str, int]:
    vc = series.value_counts(dropna=False)
    return {str(k): int(v) for k, v in vc.items()}


def summarize_one(exp_id: str) -> Dict[str, Any]:
    res_path = RESULTS_DIR / f"two_stage__{exp_id}.json"
    res = _read_json(res_path)
    cfg = res.get("config", {})

    row: Dict[str, Any] = {
        "exp_id": exp_id,
        "price_source": cfg.get("price_source"),
        "label_mode": cfg.get("label_mode"),
        "test_start": cfg.get("test_start"),
        "train_frac_within_pretest": cfg.get("train_frac_within_pretest"),
        "signal_threshold_trade": cfg.get("signal_threshold_trade"),
        "direction_threshold_down": cfg.get("direction_threshold_down"),
        "direction_threshold_up": cfg.get("direction_threshold_up"),
        "config_path": cfg.get("config_path"),
        "report_path": cfg.get("report_path"),
        "manifest_path": cfg.get("manifest_path"),
    }

    # Metrics (signal/direction): positive classes as stored in report dict
    for model_key, pos_name in [("signal", "move"), ("direction", "up")]:
        for split in ["train", "val", "test"]:
            rep = _safe_get(res, [model_key, split, "report"], {}) or {}
            cls = rep.get(pos_name, {}) if isinstance(rep, dict) else {}
            row[f"{model_key}_precision_{split}"] = cls.get("precision")
            row[f"{model_key}_recall_{split}"] = cls.get("recall")
            row[f"{model_key}_f1_{split}"] = cls.get("f1-score")

    # Combined test report
    comb_rep = _safe_get(res, ["combined_test", "report"], {}) or {}
    if isinstance(comb_rep, dict):
        for cls_name in ["neutral", "up", "down"]:
            cls = comb_rep.get(cls_name, {})
            if isinstance(cls, dict):
                row[f"combined_precision_{cls_name}"] = cls.get("precision")
                row[f"combined_recall_{cls_name}"] = cls.get("recall")
                row[f"combined_f1_{cls_name}"] = cls.get("f1-score")
                row[f"combined_support_{cls_name}"] = cls.get("support")
        macro = comb_rep.get("macro avg", {})
        if isinstance(macro, dict):
            row["combined_f1_macro"] = macro.get("f1-score")
            row["combined_precision_macro"] = macro.get("precision")
            row["combined_recall_macro"] = macro.get("recall")

    # Prediction distributions
    pred = load_predictions(exp_id)
    if pred is not None and len(pred):
        row["test_rows"] = int(len(pred))
        row["test_true_counts"] = json.dumps(_counts(pred["label_true"]), ensure_ascii=False)
        row["test_pred_counts"] = json.dumps(_counts(pred["combined_pred"]), ensure_ascii=False)

        # “Down predicted?” quick diagnostic
        row["test_pred_down"] = int((pred["combined_pred"] == "down").sum())
        row["test_pred_up"] = int((pred["combined_pred"] == "up").sum())

    # Label distributions (whole dataset)
    lab = load_labels(exp_id)
    if lab is not None and "label" in lab.columns:
        row["label_counts_all"] = json.dumps(_counts(lab["label"]), ensure_ascii=False)

    # Store some raw params for traceability (as JSON strings)
    dp = cfg.get("data_params") if isinstance(cfg, dict) else None
    lp = cfg.get("label_params") if isinstance(cfg, dict) else None
    if isinstance(dp, dict):
        row.update(_flatten("data_", dp))
    if isinstance(lp, dict):
        row.update(_flatten("label_", lp))

    return row


def to_markdown_table(df: pd.DataFrame, *, limit: int = 30) -> str:
    if df.empty:
        return "_no results_"
    view = df.head(limit).copy()
    # Keep it readable
    cols = [
        "exp_id",
        "price_source",
        "label_mode",
        "combined_f1_macro",
        "combined_f1_up",
        "combined_f1_down",
        "signal_f1_test",
        "direction_f1_test",
        "test_pred_down",
        "report_path",
    ]
    cols = [c for c in cols if c in view.columns]
    table = view[cols].fillna("").astype(str)

    # Minimal Markdown table (kein tabulate dependency)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = ["| " + " | ".join(table.iloc[i].tolist()) + " |" for i in range(len(table))]
    return "\n".join([header, sep, *rows])


def main() -> None:
    ap = argparse.ArgumentParser(description="v2 Ergebnisse zusammenfassen.")
    ap.add_argument("--filter", type=str, default=None, help="Nur EXP_IDs, die dieses Substring enthalten.")
    ap.add_argument("--sort", type=str, default="combined_f1_macro", help="Sortierspalte (absteigend).")
    ap.add_argument("--out-csv", type=Path, default=None, help="Output CSV Pfad (default: data/processed/v2/summary/v2_summary.csv).")
    ap.add_argument("--out-md", type=Path, default=None, help="Optionaler Output Markdown Pfad.")
    args = ap.parse_args()

    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = args.out_csv or (SUMMARY_DIR / "v2_summary.csv")
    out_md = args.out_md or (SUMMARY_DIR / "v2_summary.md")

    rows: List[Dict[str, Any]] = []
    for exp_id in iter_exp_ids(RESULTS_DIR):
        if args.filter and args.filter not in exp_id:
            continue
        try:
            rows.append(summarize_one(exp_id))
        except Exception as e:
            rows.append({"exp_id": exp_id, "error": str(e)})

    df = pd.DataFrame(rows)
    if args.sort in df.columns:
        df = df.sort_values(args.sort, ascending=False, na_position="last")

    df.to_csv(out_csv, index=False)
    out_md.write_text(to_markdown_table(df), encoding="utf-8")

    print("[ok] wrote:", out_csv)
    print("[ok] wrote:", out_md)
    print("[info] rows:", len(df))


if __name__ == "__main__":
    main()
