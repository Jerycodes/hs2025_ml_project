from __future__ import annotations

from src.risk.flex_engine import FlexConfig, evaluate_risk


def main() -> None:
    # CONFIGURE ME:
    # If your FLEX binary needs extra flags (e.g. "--json"), put them here.
    cfg = FlexConfig(
        flex_cmd="flex",
        rule_path="rules/risk.flex",  # type: ignore[arg-type]
        extra_args=(),
        mode="auto",
    )

    cases = [
        # high confidence, low vol, few trades -> high risk
        dict(signal_confidence=0.9, volatility=0.2, open_trades=1),
        # medium everything -> medium risk
        dict(signal_confidence=0.5, volatility=0.5, open_trades=2),
        # high vol OR many open trades -> low risk
        dict(signal_confidence=0.8, volatility=0.9, open_trades=4),
    ]

    for i, c in enumerate(cases, 1):
        r = evaluate_risk(**c, cfg=cfg)
        print(f"case {i}: {c} -> risk_per_trade={r:.4f}")


if __name__ == "__main__":
    main()

