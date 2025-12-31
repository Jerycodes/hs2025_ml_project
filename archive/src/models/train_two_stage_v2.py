"""v2 Zwei-Stufen-Training + Trading-Thresholds (getrennt vom bestehenden System)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from src.models.train_xgboost_two_stage import (
    build_direction_targets,
    build_signal_targets,
    get_feature_cols,
    load_dataset,
    split_train_val_test,
    train_xgb_binary,
)


@dataclass(frozen=True)
class ThresholdSearchConfig:
    thr_min: float = 0.3
    thr_max: float = 0.7
    thr_step: float = 0.025
    min_pred_down: int = 5
    min_pred_up: int = 5

    def grid(self) -> np.ndarray:
        return np.arange(self.thr_min, self.thr_max + 1e-9, self.thr_step)


def _cost_per_trade(
    true_label: str,
    pred_label: str,
    *,
    stake_up: float,
    stake_down: float,
    tp_pct: float,
    sl_pct: float,
) -> float:
    """Sehr einfache, deterministische Kostenfunktion.

    - korrekter Trade: +stake * tp_pct
    - falscher Trade (oder Trade auf neutral): -stake * sl_pct
    - kein Trade: 0
    """
    true_label = str(true_label)
    pred_label = str(pred_label)

    if pred_label == "neutral":
        return 0.0

    if pred_label == "up":
        if true_label == "up":
            return stake_up * tp_pct
        return -stake_up * sl_pct

    if pred_label == "down":
        if true_label == "down":
            return stake_down * tp_pct
        return -stake_down * sl_pct

    return 0.0


def _combined_pred_from_thresholds(
    signal_prob: np.ndarray,
    dir_prob_up: np.ndarray,
    *,
    sig_thr_trade: float,
    thr_down: float,
    thr_up: float,
) -> np.ndarray:
    pred = np.full(len(signal_prob), "neutral", dtype=object)
    mask_trade = signal_prob >= sig_thr_trade
    pred[mask_trade & (dir_prob_up >= thr_up)] = "up"
    pred[mask_trade & (dir_prob_up <= thr_down)] = "down"
    return pred


def tune_direction_thresholds_cost_based(
    *,
    signal_pred_val: np.ndarray,
    dir_prob_val_all: np.ndarray,
    true_labels_val: np.ndarray,
    search: ThresholdSearchConfig,
    stake_up: float,
    stake_down: float,
    tp_pct: float,
    sl_pct: float,
) -> Tuple[float, float, float]:
    """Sucht (thr_down, thr_up) via P&L auf Val, mit Constraints gegen Degeneration."""
    candidates = search.grid()
    best_pnl = -1e18
    best = (0.4, 0.6)

    # nur Tage, wo Stufe-1 überhaupt einen Trade zulässt
    idx = np.where(signal_pred_val == 1)[0]
    if len(idx) == 0:
        return best[0], best[1], best_pnl

    for thr_down in candidates:
        for thr_up in candidates:
            if thr_down >= thr_up:
                continue

            pred = np.full(len(idx), "neutral", dtype=object)
            prob = dir_prob_val_all[idx]
            pred[prob >= thr_up] = "up"
            pred[prob <= thr_down] = "down"

            # Constraints: erzwinge, dass beide Richtungen überhaupt vorkommen können.
            n_up = int((pred == "up").sum())
            n_down = int((pred == "down").sum())
            if n_up < search.min_pred_up or n_down < search.min_pred_down:
                continue

            pnl = 0.0
            for t, p in zip(true_labels_val[idx], pred):
                pnl += _cost_per_trade(
                    t,
                    p,
                    stake_up=stake_up,
                    stake_down=stake_down,
                    tp_pct=tp_pct,
                    sl_pct=sl_pct,
                )
            if pnl > best_pnl:
                best_pnl = pnl
                best = (float(thr_down), float(thr_up))

    return best[0], best[1], float(best_pnl)


def tune_signal_trade_threshold_cost_based(
    *,
    signal_prob_val: np.ndarray,
    dir_prob_val_all: np.ndarray,
    true_labels_val: np.ndarray,
    thr_down: float,
    thr_up: float,
    search: ThresholdSearchConfig,
    stake_up: float,
    stake_down: float,
    tp_pct: float,
    sl_pct: float,
) -> Tuple[float, float]:
    """Sucht sig_thr_trade via P&L auf Val (bei fixen Direction-Thresholds)."""
    best_thr = 0.5
    best_pnl = -1e18
    for thr_sig in search.grid():
        pred = _combined_pred_from_thresholds(
            signal_prob_val,
            dir_prob_val_all,
            sig_thr_trade=float(thr_sig),
            thr_down=thr_down,
            thr_up=thr_up,
        )
        pnl = 0.0
        for t, p in zip(true_labels_val, pred):
            pnl += _cost_per_trade(
                t,
                p,
                stake_up=stake_up,
                stake_down=stake_down,
                tp_pct=tp_pct,
                sl_pct=sl_pct,
            )
        if pnl > best_pnl:
            best_pnl = pnl
            best_thr = float(thr_sig)
    return best_thr, float(best_pnl)


def binary_metrics_dict(
    y_true: np.ndarray, y_prob: np.ndarray, threshold: float, target_names: list[str]
) -> Dict[str, Any]:
    if y_true is None or len(y_true) == 0:
        return {"threshold": float(threshold), "report": {}, "confusion_matrix": []}
    y_pred = (y_prob >= threshold).astype(int)
    report = classification_report(
        y_true,
        y_pred,
        target_names=target_names,
        output_dict=True,
        digits=3,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred).tolist()
    return {"threshold": float(threshold), "report": report, "confusion_matrix": cm}


def train_two_stage_v2(
    *,
    dataset_path: Path,
    test_start: str = "2025-01-01",
    train_frac_within_pretest: float = 0.8,
    feature_cols: list[str] | None = None,
    search: ThresholdSearchConfig | None = None,
    stake_up: float = 100.0,
    stake_down: float = 100.0,
    tp_pct: float = 0.02,
    sl_pct: float = 0.01,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    df = load_dataset(dataset_path)
    if feature_cols is None:
        feature_cols = get_feature_cols(df)
    if search is None:
        search = ThresholdSearchConfig()

    splits = split_train_val_test(
        df, pd.to_datetime(test_start), train_frac_within_pretest=train_frac_within_pretest
    )

    # --- Stage 1: Signal ---
    y_train_signal = build_signal_targets(splits["train"]).to_numpy()
    y_val_signal = build_signal_targets(splits["val"]).to_numpy()
    y_test_signal = build_signal_targets(splits["test"]).to_numpy()

    X_train_signal = splits["train"][feature_cols]
    X_val_signal = splits["val"][feature_cols]
    X_test_signal = splits["test"][feature_cols]

    model_signal = train_xgb_binary(X_train_signal, y_train_signal, X_val_signal, y_val_signal)

    p_train_signal = model_signal.predict_proba(X_train_signal)[:, 1]
    p_val_signal = model_signal.predict_proba(X_val_signal)[:, 1]
    p_test_signal = model_signal.predict_proba(X_test_signal)[:, 1]

    SIGNAL_THRESHOLD = 0.5
    signal_metrics = {
        "train": binary_metrics_dict(y_train_signal, p_train_signal, SIGNAL_THRESHOLD, ["neutral", "move"]),
        "val": binary_metrics_dict(y_val_signal, p_val_signal, SIGNAL_THRESHOLD, ["neutral", "move"]),
        "test": binary_metrics_dict(y_test_signal, p_test_signal, SIGNAL_THRESHOLD, ["neutral", "move"]),
    }

    # --- Stage 2: Direction (only move days) ---
    X_train_dir, y_train_dir = build_direction_targets(splits["train"], feature_cols=feature_cols)
    X_val_dir, y_val_dir = build_direction_targets(splits["val"], feature_cols=feature_cols)
    X_test_dir, y_test_dir = build_direction_targets(splits["test"], feature_cols=feature_cols)

    model_dir = train_xgb_binary(X_train_dir, y_train_dir, X_val_dir, y_val_dir, scale_pos_weight=1.0)

    p_train_dir = model_dir.predict_proba(X_train_dir)[:, 1]
    p_val_dir = model_dir.predict_proba(X_val_dir)[:, 1]
    p_test_dir = model_dir.predict_proba(X_test_dir)[:, 1]

    # Direction threshold tuned for *both* directions is tricky; keep 0.5 for diagnostic metrics.
    DIR_THRESHOLD = 0.5
    direction_metrics = {
        "train": binary_metrics_dict(y_train_dir, p_train_dir, DIR_THRESHOLD, ["down", "up"]),
        "val": binary_metrics_dict(y_val_dir, p_val_dir, DIR_THRESHOLD, ["down", "up"]),
        "test": binary_metrics_dict(y_test_dir, p_test_dir, DIR_THRESHOLD, ["down", "up"]),
    }

    # --- Trading thresholds (Val-based, constrained) ---
    labels_val = splits["val"]["label"].to_numpy()
    signal_pred_val = (p_val_signal >= SIGNAL_THRESHOLD).astype(int)
    dir_prob_val_all = model_dir.predict_proba(splits["val"][feature_cols])[:, 1]

    thr_down, thr_up, pnl_dir = tune_direction_thresholds_cost_based(
        signal_pred_val=signal_pred_val,
        dir_prob_val_all=dir_prob_val_all,
        true_labels_val=labels_val,
        search=search,
        stake_up=stake_up,
        stake_down=stake_down,
        tp_pct=tp_pct,
        sl_pct=sl_pct,
    )

    sig_thr_trade, pnl_sig = tune_signal_trade_threshold_cost_based(
        signal_prob_val=p_val_signal,
        dir_prob_val_all=dir_prob_val_all,
        true_labels_val=labels_val,
        thr_down=thr_down,
        thr_up=thr_up,
        search=search,
        stake_up=stake_up,
        stake_down=stake_down,
        tp_pct=tp_pct,
        sl_pct=sl_pct,
    )

    # --- Combined test evaluation ---
    X_test_all = splits["test"][feature_cols]
    signal_prob_test = model_signal.predict_proba(X_test_all)[:, 1]
    dir_prob_test = model_dir.predict_proba(X_test_all)[:, 1]
    combined_pred = _combined_pred_from_thresholds(
        signal_prob_test, dir_prob_test, sig_thr_trade=sig_thr_trade, thr_down=thr_down, thr_up=thr_up
    )
    combined_true = splits["test"]["label"].to_numpy()

    combined_report = classification_report(
        combined_true,
        combined_pred,
        labels=["neutral", "up", "down"],
        output_dict=True,
        digits=3,
        zero_division=0,
    )
    combined_cm = confusion_matrix(
        combined_true, combined_pred, labels=["neutral", "up", "down"]
    ).tolist()

    results: Dict[str, Any] = {
        "config": {
            "dataset_path": str(dataset_path),
            "feature_cols": feature_cols,
            "test_start": test_start,
            "train_frac_within_pretest": float(train_frac_within_pretest),
            "signal_threshold": SIGNAL_THRESHOLD,
            "direction_threshold": DIR_THRESHOLD,
            "signal_threshold_trade": float(sig_thr_trade),
            "direction_threshold_down": float(thr_down),
            "direction_threshold_up": float(thr_up),
            "threshold_search": {
                "thr_min": search.thr_min,
                "thr_max": search.thr_max,
                "thr_step": search.thr_step,
                "min_pred_down": search.min_pred_down,
                "min_pred_up": search.min_pred_up,
            },
            "cost_model": {
                "stake_up": stake_up,
                "stake_down": stake_down,
                "tp_pct": tp_pct,
                "sl_pct": sl_pct,
                "pnl_dir_val": float(pnl_dir),
                "pnl_sig_val": float(pnl_sig),
            },
        },
        "signal": signal_metrics,
        "direction": direction_metrics,
        "combined_test": {
            "report": combined_report,
            "confusion_matrix": combined_cm,
            "labels": ["neutral", "up", "down"],
        },
        "model_params": {
            "signal": {**model_signal.get_xgb_params(), "feature_importances_": model_signal.feature_importances_.tolist()},
            "direction": {**model_dir.get_xgb_params(), "feature_importances_": model_dir.feature_importances_.tolist()},
        },
    }

    pred_df = pd.DataFrame(
        {
            "date": splits["test"]["date"].to_numpy(),
            "label_true": combined_true,
            "signal_prob": signal_prob_test.astype(float),
            "direction_prob_up": dir_prob_test.astype(float),
            "combined_pred": combined_pred,
        }
    )
    return results, pred_df

