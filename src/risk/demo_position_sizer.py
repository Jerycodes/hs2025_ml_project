from __future__ import annotations

from pathlib import Path

from src.risk.flex_engine import FlexConfig
from src.risk.position_sizer import PositionSizingConfig, size_trade_chf


def main() -> None:
    # CONFIGURE ME:
    # - If your FLEX binary needs flags (e.g. "--json"), set extra_args.
    # - If you want to force a specific mode, set mode="kv" or mode="json".
    flex = FlexConfig(
        flex_cmd="flex",
        rule_path=Path("rules/risk.flex"),
        extra_args=(),
        mode="auto",
    )

    cfg = PositionSizingConfig(
        max_position_frac_of_equity=0.02,  # 2% of equity at risk_per_trade=1.0
        min_position_chf=0.0,
        max_position_chf=None,
        round_to_chf=1.0,
        flex=flex,
    )

    account = dict(equity_chf=10_000.0, free_margin_chf=8_000.0)

    # Example: outputs coming from your two-stage model:
    # - p_move: Stage 1 (signal)
    # - p_up:   Stage 2 (direction)
    # - direction: subsymbolic decision (up/down)
    cases = [
        dict(direction="up", p_move=0.85, p_up=0.70, volatility=0.20, open_trades=1),
        dict(direction="down", p_move=0.75, p_up=0.40, volatility=0.30, open_trades=2),
        dict(direction="up", p_move=0.55, p_up=0.55, volatility=0.80, open_trades=4),
    ]

    for i, c in enumerate(cases, 1):
        res = size_trade_chf(**c, **account, cfg=cfg)
        print(
            f"case {i}: dir={res.direction} "
            f"signal_conf={res.signal_confidence:.3f} "
            f"risk={res.risk_per_trade:.3f} "
            f"max_stake={res.max_stake_chf:.2f} CHF "
            f"-> stake={res.stake_chf:.2f} CHF"
        )


if __name__ == "__main__":
    main()

