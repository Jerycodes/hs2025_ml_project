from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping

from src.utils.io import DATA_PROCESSED


DATA_PROCESSED_V2 = DATA_PROCESSED / "v2"


def _pct_token(x: float) -> str:
    """Formats a decimal percent into a compact token, e.g. 0.02 -> '2p0pct'."""
    pct = abs(float(x)) * 100.0
    # keep one decimal (2.0, 0.4, 1.5) but compact as 2p0, 0p4, 1p5
    s = f"{pct:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", "p") + "pct"


def _float_token(x: float) -> str:
    """Formats a float into a compact token, e.g. 14 -> '14', 1.5 -> '1p5'."""
    s = f"{float(x):.3f}".rstrip("0").rstrip(".")
    return s.replace(".", "p")


def compose_exp_id_v2(cfg: Mapping[str, Any]) -> str:
    """Compose a readable EXP_ID from a single config mapping.

    The intent is that EXP_ID is always derived from the *same* config
    that is used for labeling/training/reporting, so mismatches are less likely.
    """
    base = str(cfg.get("base", "v2"))
    data = dict(cfg.get("data", {}))
    label = dict(cfg.get("label", {}))

    price_source = str(data.get("price_source", "yahoo"))
    cut = str(data.get("cut", "as_is"))

    horizon = int(label.get("horizon_days", 4))
    up_thr = float(label.get("up_threshold", 0.0))
    down_thr = float(label.get("down_threshold", 0.0))
    mode = str(label.get("mode", "close_path"))

    parts: list[str] = [base, price_source, f"h{horizon}", f"thr{_pct_token(up_thr)}"]
    if down_thr != -up_thr and down_thr != 0.0:
        parts.append(f"dn{_pct_token(down_thr)}")

    if mode != "close_path":
        parts.append(mode)

    if label.get("hit_within_horizon", False):
        parts.append("hit")
    if label.get("first_hit_wins", False):
        parts.append("first")

    if label.get("max_adverse_move_pct") is not None:
        parts.append(f"adv{_pct_token(float(label['max_adverse_move_pct']))}")

    if label.get("sl_mode"):
        parts.append(f"sl{label['sl_mode']}")
    if label.get("sl_pct") is not None:
        parts.append(f"sl{_pct_token(float(label['sl_pct']))}")
    if label.get("tp_pct") is not None:
        parts.append(f"tp{_pct_token(float(label['tp_pct']))}")
    if label.get("atr_window") is not None:
        parts.append(f"atr{int(label['atr_window'])}")
    if label.get("atr_mult") is not None:
        parts.append(f"atrm{_float_token(float(label['atr_mult']))}")

    if cut != "as_is":
        parts.append(f"cut{cut}")

    # Keep it filesystem-safe.
    safe = "__".join(parts).replace(" ", "_").replace("/", "_")
    return safe


@dataclass(frozen=True)
class ExperimentConfig:
    exp_id: str
    cfg: Dict[str, Any]

    @property
    def exp_dir(self) -> Path:
        return DATA_PROCESSED_V2 / "experiments"

    @property
    def labels_dir(self) -> Path:
        return DATA_PROCESSED_V2 / "fx"

    @property
    def datasets_dir(self) -> Path:
        return DATA_PROCESSED_V2 / "datasets"

    @property
    def results_dir(self) -> Path:
        return DATA_PROCESSED_V2 / "results"

    @property
    def reports_dir(self) -> Path:
        return DATA_PROCESSED_V2 / "reports"


def ensure_v2_dirs() -> None:
    for p in [
        DATA_PROCESSED_V2,
        DATA_PROCESSED_V2 / "experiments",
        DATA_PROCESSED_V2 / "fx",
        DATA_PROCESSED_V2 / "datasets",
        DATA_PROCESSED_V2 / "results",
        DATA_PROCESSED_V2 / "reports",
        DATA_PROCESSED_V2 / ".mplconfig",
    ]:
        p.mkdir(parents=True, exist_ok=True)


def save_experiment_config(cfg: Dict[str, Any], *, exp_id: str | None = None) -> ExperimentConfig:
    """Save config under data/processed/v2/experiments and return canonical object."""
    ensure_v2_dirs()

    cfg = dict(cfg)
    if exp_id is None:
        exp_id = compose_exp_id_v2(cfg)
    cfg["exp_id"] = exp_id
    cfg.setdefault("created_at", datetime.utcnow().isoformat(timespec="seconds") + "Z")

    path = DATA_PROCESSED_V2 / "experiments" / f"{exp_id}_config.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, sort_keys=True)
    return ExperimentConfig(exp_id=exp_id, cfg=cfg)


def load_experiment_config(exp_id: str) -> ExperimentConfig:
    path = DATA_PROCESSED_V2 / "experiments" / f"{exp_id}_config.json"
    if not path.is_file():
        raise FileNotFoundError(f"v2 config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    return ExperimentConfig(exp_id=exp_id, cfg=cfg)

