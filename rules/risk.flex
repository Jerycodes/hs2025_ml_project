// Fuzzy rule set for risk sizing.
//
// Note: Different "FLEX" tools use different syntaxes. This file is IEC 61131-7
// FCL-like (common across many fuzzy engines). If your FLEX CLI expects a
// different format, adapt this file accordingly.
//
// Variables:
//   Inputs:  signal_confidence (0..1), volatility (0..1), open_trades (0..5)
//   Output:  risk_per_trade (0..1)
//
// Defuzzification: centroid / center of gravity (COG).

FUNCTION_BLOCK risk

VAR_INPUT
  signal_confidence : REAL;
  volatility        : REAL;
  open_trades       : REAL;
  equity            : REAL;
END_VAR

VAR_OUTPUT
  risk_per_trade    : REAL;
END_VAR

FUZZIFY signal_confidence
  // High starts earlier to allow higher stakes when the model is "relatively sure".
  TERM low    := (0.00, 1.00) (0.50, 0.00);
  TERM medium := (0.35, 0.00) (0.65, 1.00) (0.85, 0.00);
  TERM high   := (0.72, 0.00) (1.00, 1.00);
END_FUZZIFY

FUZZIFY volatility
  TERM low    := (0.00, 1.00) (0.40, 0.00);
  TERM medium := (0.20, 0.00) (0.50, 1.00) (0.80, 0.00);
  TERM high   := (0.60, 0.00) (1.00, 1.00);
END_FUZZIFY

FUZZIFY open_trades
  TERM few    := (0.0, 1.0) (2.0, 0.0);
  TERM medium := (1.0, 0.0) (2.5, 1.0) (4.0, 0.0);
  TERM many   := (3.0, 0.0) (5.0, 1.0);
END_FUZZIFY

FUZZIFY equity
  // equity is normalized to [0,1], where 0.5 ~ "reference equity".
  TERM low    := (0.00, 1.00) (0.45, 0.00);
  TERM high   := (0.55, 0.00) (1.00, 1.00);
END_FUZZIFY

DEFUZZIFY risk_per_trade
  // More contrast: very low vs very high outputs.
  TERM low    := (0.00, 1.00) (0.20, 0.00);
  TERM medium := (0.15, 0.00) (0.50, 1.00) (0.85, 0.00);
  TERM high   := (0.75, 0.00) (1.00, 1.00);

  METHOD  : COG;
  DEFAULT : 0.00;
END_DEFUZZIFY

RULEBLOCK risk_rules
  AND  : MIN;
  OR   : MAX;
  ACT  : MIN;
  ACCU : MAX;

  RULE 1 : IF signal_confidence IS high AND volatility IS low AND open_trades IS few
           THEN risk_per_trade IS high;

  RULE 2 : IF signal_confidence IS medium AND volatility IS medium
           THEN risk_per_trade IS medium;

  RULE 3 : IF volatility IS high OR open_trades IS many
           THEN risk_per_trade IS low;

  RULE 4 : IF signal_confidence IS low
           THEN risk_per_trade IS low;

  // Equity boost (only if setup isn't "bad")
  RULE 5 : IF equity IS high AND signal_confidence IS high AND volatility IS medium
           THEN risk_per_trade IS high;
  RULE 6 : IF equity IS high AND signal_confidence IS medium AND volatility IS low AND open_trades IS few
           THEN risk_per_trade IS high;
  RULE 7 : IF equity IS low
           THEN risk_per_trade IS low;

  // Confidence gating (more decisive sizing)
  RULE 8 : IF signal_confidence IS high AND volatility IS low
           THEN risk_per_trade IS high;
  RULE 9 : IF signal_confidence IS low
           THEN risk_per_trade IS low;
END_RULEBLOCK

END_FUNCTION_BLOCK
