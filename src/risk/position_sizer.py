"""
Position sizing that connects your two-stage model output to the FLEX fuzzy rules.

Goal
----
Given a directional trade decision (up/down) plus model probabilities and a few
account inputs, compute a CHF stake amount.

Pipeline
--------
Stage 1 (signal model):        p_move  in [0,1]
Stage 2 (direction model):     p_up    in [0,1]
Trade direction:               'up' or 'down'

We combine Stage 1 + Stage 2 into a single confidence score:
  direction_conf = p_up            if direction == 'up'
                   1 - p_up        if direction == 'down'
  signal_confidence = p_move * direction_conf

Then FLEX returns risk_per_trade in [0,1]. Finally we map it to CHF:
  max_stake_chf = equity_chf * max_position_frac_of_equity
  max_stake_chf = min(max_stake_chf, free_margin_chf)  (if provided)
  stake_chf = risk_per_trade * max_stake_chf

CONFIGURE ME
------------
- max_position_frac_of_equity: how much of equity you allow per trade at risk_per_trade=1.0
- min_position_chf / max_position_chf: optional clamps
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.risk.flex_engine import FlexConfig, evaluate_risk

Direction = Literal["up", "down"]


@dataclass(frozen=True)
class PositionSizingConfig:
    max_position_frac_of_equity: float = 0.02  # 2% of equity at risk_per_trade=1.0
    min_position_chf: float = 0.0
    max_position_chf: float | None = None
    round_to_chf: float = 1.0  # 1.0 => round to whole CHF; 0.01 => cents
    flex: FlexConfig = FlexConfig()


@dataclass(frozen=True)
class PositionSizingResult:
    direction: Direction
    signal_confidence: float
    risk_per_trade: float
    max_stake_chf: float
    stake_chf: float


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _round_to(x: float, step: float) -> float:
    if step <= 0:
        return float(x)
    return round(float(x) / float(step)) * float(step)


def compute_signal_confidence(
    *,
    p_move: float,
    p_up: float,
    direction: Direction,
) -> float:
    if not (0.0 <= p_move <= 1.0):
        raise ValueError("p_move must be in [0,1]")
    if not (0.0 <= p_up <= 1.0):
        raise ValueError("p_up must be in [0,1]")
    direction_conf = p_up if direction == "up" else (1.0 - p_up)
    return float(_clamp(p_move * direction_conf, 0.0, 1.0))


def size_trade_chf(
    *,
    direction: Direction,
    p_move: float,
    p_up: float,
    volatility: float,
    open_trades: int,
    equity_chf: float,
    free_margin_chf: float | None = None,
    cfg: PositionSizingConfig = PositionSizingConfig(),
) -> PositionSizingResult:
    """
    Compute a CHF stake amount for a single trade.

    volatility: normalized to [0,1] (your own normalization; e.g. ATR percentile).
    open_trades: integer count (0..5 recommended, but we allow any >=0 and clamp to 5).
    """
    if equity_chf <= 0:
        raise ValueError("equity_chf must be > 0")
    if free_margin_chf is not None and free_margin_chf <= 0:
        raise ValueError("free_margin_chf must be > 0 if provided")

    open_trades_f = float(_clamp(float(open_trades), 0.0, 5.0))
    vol_f = float(_clamp(float(volatility), 0.0, 1.0))

    signal_conf = compute_signal_confidence(p_move=p_move, p_up=p_up, direction=direction)
    risk = evaluate_risk(
        signal_confidence=signal_conf,
        volatility=vol_f,
        open_trades=open_trades_f,
        cfg=cfg.flex,
    )

    max_stake = float(equity_chf) * float(cfg.max_position_frac_of_equity)
    if free_margin_chf is not None:
        max_stake = min(max_stake, float(free_margin_chf))
    if cfg.max_position_chf is not None:
        max_stake = min(max_stake, float(cfg.max_position_chf))
    max_stake = max(0.0, max_stake)

    stake = float(risk) * max_stake
    stake = max(float(cfg.min_position_chf), stake)
    if cfg.max_position_chf is not None:
        stake = min(float(cfg.max_position_chf), stake)
    stake = _round_to(stake, cfg.round_to_chf)

    return PositionSizingResult(
        direction=direction,
        signal_confidence=signal_conf,
        risk_per_trade=float(risk),
        max_stake_chf=max_stake,
        stake_chf=stake,
    )

