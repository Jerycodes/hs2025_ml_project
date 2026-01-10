"""
Minimal Python wrapper for a FLEX fuzzy engine CLI.

You likely need to adjust how the CLI is called (args / stdin / output format).
Look for the "CONFIGURE ME" sections below.

Supported modes
---------------
Mode A (key=value args):
  flex rules/risk.flex signal_confidence=0.8 volatility=0.2 open_trades=1
  -> expects output containing: risk_per_trade=<number>

Mode B (JSON over stdin):
  echo '{"signal_confidence":0.8,"volatility":0.2,"open_trades":1}' | flex rules/risk.flex --json
  -> expects JSON output containing: {"risk_per_trade": 0.42}

How to test which mode fits your FLEX binary
--------------------------------------------
1) Try Mode A manually:
   `flex rules/risk.flex signal_confidence=0.8 volatility=0.2 open_trades=1`
2) Try Mode B manually (you may need flags like --json):
   `echo '{"signal_confidence":0.8,"volatility":0.2,"open_trades":1}' | flex rules/risk.flex --json`
3) Set `FLEX_MODE` below to "kv" or "json" once you know what works.

Notes
-----
- On macOS, `flex` often refers to the lexical-analyzer generator (flex 2.x), not a fuzzy engine.
  In that case, this wrapper auto-falls back to a built-in fuzzy implementation unless you force
  `mode="kv"`/`mode="json"`.
- If your FLEX engine is a Java JAR, use `flex_cmd="java"` + `pre_args=("-jar", "/path/to/FLEX.jar")`.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Mode = Literal["auto", "kv", "json", "python"]


class FlexEngineError(RuntimeError):
    pass


@dataclass(frozen=True)
class FlexConfig:
    # --- CONFIGURE ME ---
    # Command/binary name. If you installed it elsewhere, use an absolute path.
    flex_cmd: str = "flex"
    # Optional fixed args inserted before the rule file.
    # Example: flex_cmd="java", pre_args=("-jar", "/path/to/FLEX.jar")
    pre_args: tuple[str, ...] = ()
    # Path to the rule file.
    rule_path: Path = Path("rules/risk.flex")
    # Extra args. Example for JSON mode: ["--json"]
    extra_args: tuple[str, ...] = ()
    # Which mode to use. "auto" tries JSON first, then key=value.
    mode: Mode = "auto"


def _looks_like_lex_flex(cmd: str) -> bool:
    """
    On macOS `/usr/bin/flex` is commonly the *lexical-analyzer generator* (flex 2.x),
    not a fuzzy-logic engine. If users keep the default `flex_cmd="flex"`, we try to
    detect this and avoid calling the wrong binary.
    """
    resolved = shutil.which(cmd)
    if not resolved:
        return False
    if Path(resolved).name != "flex":
        return False
    try:
        proc = subprocess.run([resolved, "--version"], text=True, capture_output=True, check=False)
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    except Exception:
        return False
    return bool(re.search(r"\bflex\s+2\.", out, flags=re.IGNORECASE))


def _python_fuzzy_risk(signal_confidence: float, volatility: float, open_trades: float, equity: float) -> float:
    """
    Minimal Mamdani-style fuzzy inference (hard-coded membership functions + rules).
    This is a fallback if no compatible FLEX CLI is configured.
    """

    def clamp(x: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, x))

    def left_shoulder(x: float, a: float, b: float) -> float:
        if x <= a:
            return 1.0
        if x >= b:
            return 0.0
        return (b - x) / (b - a)

    def right_shoulder(x: float, a: float, b: float) -> float:
        if x <= a:
            return 0.0
        if x >= b:
            return 1.0
        return (x - a) / (b - a)

    def triangle(x: float, a: float, b: float, c: float) -> float:
        if x <= a or x >= c:
            return 0.0
        if x == b:
            return 1.0
        if x < b:
            return (x - a) / (b - a)
        return (c - x) / (c - b)

    # ========== INPUT FUZZIFIKATION ==========
    # Die Eingabewerte werden auf ihre jeweiligen Universen geklemmt.
    sc = clamp(signal_confidence, 0.0, 1.0)   # Signal-Konfidenz: 0=unsicher, 1=sehr sicher
    vol = clamp(volatility, 0.0, 1.0)          # Volatilität: 0=ruhig, 1=sehr volatil
    ot = clamp(open_trades, 0.0, 5.0)          # Offene Trades: 0-5 (mehr = höheres Exposure)
    eq = clamp(equity, 0.0, 1.0)               # Normalisiertes Kapital: 0=wenig, 1=viel

    # ========== MEMBERSHIP-FUNKTIONEN FÜR SIGNAL_CONFIDENCE ==========
    # Die Grenzen wurden so gewählt, dass "high" bereits ab ~72% Konfidenz beginnt,
    # da typische XGBoost-Wahrscheinlichkeiten selten >85% erreichen.
    # - low:  [0.0, 0.50] - Modell ist unsicher (< 50% → eher kein Trade)
    # - med:  [0.35, 0.65, 0.85] - mittlere Sicherheit
    # - high: [0.72, 1.0] - Modell ist zuversichtlich (ab 72% → grössere Positionen)
    sc_low = left_shoulder(sc, 0.0, 0.50)
    sc_med = triangle(sc, 0.35, 0.65, 0.85)
    sc_high = right_shoulder(sc, 0.72, 1.0)

    # ========== MEMBERSHIP-FUNKTIONEN FÜR VOLATILITY ==========
    # Bei hoher Volatilität sollte das Risiko reduziert werden.
    # - low:  [0.0, 0.4] - ruhiger Markt → kann grössere Positionen eingehen
    # - med:  [0.2, 0.5, 0.8] - moderate Volatilität
    # - high: [0.6, 1.0] - turbulenter Markt → konservatives Position Sizing
    vol_low = left_shoulder(vol, 0.0, 0.4)
    vol_med = triangle(vol, 0.2, 0.5, 0.8)
    vol_high = right_shoulder(vol, 0.6, 1.0)

    # ========== MEMBERSHIP-FUNKTIONEN FÜR OPEN_TRADES ==========
    # Mehr offene Positionen → bereits exponiert → kleinere neue Positionen.
    # - few:  [0.0, 2.0] - wenig Exposure → kann mehr riskieren
    # - med:  [1.0, 2.5, 4.0] - moderates Exposure
    # - many: [3.0, 5.0] - viele offene Trades → konservativ
    ot_few = left_shoulder(ot, 0.0, 2.0)
    ot_med = triangle(ot, 1.0, 2.5, 4.0)
    ot_many = right_shoulder(ot, 3.0, 5.0)

    # ========== MEMBERSHIP-FUNKTIONEN FÜR EQUITY ==========
    # Mehr Kapital erlaubt grössere Positionen, aber nur bei gutem Setup.
    # - low:  [0.0, 0.45] - unter Referenz → konservativ
    # - high: [0.55, 1.0] - über Referenz → kann mehr riskieren
    eq_low = left_shoulder(eq, 0.0, 0.45)
    eq_high = right_shoulder(eq, 0.55, 1.0)

    # ========== FUZZY-REGELN (Mamdani-Inferenz) ==========
    # Operatoren: AND=min, OR=max, Implikation=min, Aggregation=max
    #
    # Die Regeln implementieren typische Trading-Risk-Management-Prinzipien:
    # - Hohe Konfidenz + niedrige Volatilität + wenig Exposure → höheres Risiko erlaubt
    # - Hohe Volatilität ODER viele offene Trades → Risiko reduzieren
    # - Niedrige Konfidenz → immer konservativ handeln
    #
    # Basisregeln:
    r1_high = min(sc_high, vol_low, ot_few)  # Regel 1: Ideales Setup → hohes Risiko
    r2_med = min(sc_med, vol_med)            # Regel 2: Durchschnittliches Setup → mittleres Risiko
    r3_low = max(vol_high, ot_many)          # Regel 3: Risikofaktoren hoch → niedriges Risiko
    r4_low = max(r3_low, sc_low)             # Regel 4: Unsicherheit → niedriges Risiko

    # Kapital-abhängige Regeln:
    # Bei mehr Kapital kann man bei gutem Setup höheres Risiko eingehen.
    # Bei wenig Kapital sollte man immer konservativ bleiben.
    r5_high = min(eq_high, sc_high, vol_med)                 # Regel 5: Kapital hoch + gutes Signal
    r6_high = min(eq_high, sc_med, vol_low, ot_few)          # Regel 6: Kapital hoch + ruhiger Markt
    r7_low = eq_low                                          # Regel 7: Kapital niedrig → konservativ

    # Konfidenz-basierte Regeln (für entschiedenere Sizing-Entscheidungen):
    r8_high = min(sc_high, vol_low)                          # Regel 8: Hohes Vertrauen + ruhiger Markt
    r9_low = sc_low                                          # Regel 9: Niedriges Vertrauen → immer konservativ

    # ========== REGEL-AGGREGATION ==========
    # Aktivierungsgrade für jede Output-Kategorie (max-Aggregation)
    deg_low = clamp(max(r4_low, r7_low, r9_low, 0.0), 0.0, 1.0)
    deg_med = clamp(max(r2_med, 0.0), 0.0, 1.0)
    deg_high = clamp(max(r1_high, r5_high, r6_high, r8_high, 0.0), 0.0, 1.0)

    # ========== DEFUZZIFIKATION (Centroid-Methode) ==========
    # Die Centroid-Methode berechnet den Schwerpunkt der aggregierten Output-Menge.
    # Wir diskretisieren das Output-Universum [0,1] in 1001 Punkte für ausreichende
    # numerische Genauigkeit (Fehler < 0.1%).
    num = 0.0  # Zähler für gewichtete Summe
    den = 0.0  # Nenner für Normalisierung
    for i in range(0, 1001):
        x = i / 1000.0
        # Output-Membership-Funktionen mit stärkerem Kontrast zwischen low und high:
        # - low:  [0.0, 0.20] → risiko-avers (kleiner Bereich am unteren Ende)
        # - med:  [0.15, 0.50, 0.85] → moderates Risiko (breiter mittlerer Bereich)
        # - high: [0.75, 1.0] → risiko-freudig (kleiner Bereich am oberen Ende)
        mu_low = min(deg_low, left_shoulder(x, 0.0, 0.20))
        mu_med = min(deg_med, triangle(x, 0.15, 0.50, 0.85))
        mu_high = min(deg_high, right_shoulder(x, 0.75, 1.0))
        mu = max(mu_low, mu_med, mu_high)
        num += x * mu
        den += mu
    if den <= 0.0:
        return 0.0  # Fallback: kein Risiko wenn alle Regeln inaktiv
    return clamp(num / den, 0.0, 1.0)


def _validate_inputs(signal_confidence: float, volatility: float, open_trades: float) -> None:
    if not (0.0 <= signal_confidence <= 1.0):
        raise ValueError("signal_confidence must be in [0, 1]")
    if not (0.0 <= volatility <= 1.0):
        raise ValueError("volatility must be in [0, 1]")
    if not (0.0 <= open_trades <= 5.0):
        raise ValueError("open_trades must be in [0, 5]")


def _parse_risk_from_json(stdout: str) -> float:
    obj = json.loads(stdout)
    if isinstance(obj, dict) and "risk_per_trade" in obj:
        return float(obj["risk_per_trade"])
    raise FlexEngineError("JSON output did not contain 'risk_per_trade'.")


_KV_RE = re.compile(r"\brisk_per_trade\s*=\s*([0-9]*\.?[0-9]+)\b")


def _parse_risk_from_text(stdout: str) -> float:
    m = _KV_RE.search(stdout)
    if not m:
        raise FlexEngineError("Could not parse 'risk_per_trade=<number>' from CLI output.")
    return float(m.group(1))


def _run(cmd: list[str], *, stdin_text: str | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            input=stdin_text,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as e:
        raise FlexEngineError(
            f"FLEX CLI not found: {cmd[0]!r}. Configure FlexConfig.flex_cmd or install the binary."
        ) from e


def evaluate_risk(
    signal_confidence: float,
    volatility: float,
    open_trades: float,
    equity: float | None = None,
    *,
    cfg: FlexConfig = FlexConfig(),
) -> float:
    """
    Returns risk_per_trade in [0, 1].
    Raises FlexEngineError on CLI or parsing failures.
    """
    _validate_inputs(signal_confidence, volatility, open_trades)
    eq = 0.5 if equity is None else float(equity)
    if not (0.0 <= eq <= 1.0):
        raise ValueError("equity must be in [0, 1]")

    if not cfg.rule_path.exists():
        raise FlexEngineError(f"Rule file not found: {cfg.rule_path}")

    if cfg.mode == "python":
        return _python_fuzzy_risk(signal_confidence, volatility, open_trades, eq)

    payload = {
        "signal_confidence": float(signal_confidence),
        "volatility": float(volatility),
        "open_trades": float(open_trades),
        "equity": float(eq),
    }

    if _looks_like_lex_flex(cfg.flex_cmd):
        if cfg.mode == "auto":
            return _python_fuzzy_risk(signal_confidence, volatility, open_trades, eq)
        raise FlexEngineError(
            "FLEX_CMD seems to point to the *lexical analyzer generator* (flex 2.x), not a fuzzy engine.\n"
            "Fix: set FLEX_CMD to your fuzzy FLEX binary (or use cfg.mode='python' for the built-in fallback).\n"
            f"Resolved: {shutil.which(cfg.flex_cmd)!r}"
        )

    base_cmd = [cfg.flex_cmd, *cfg.pre_args, str(cfg.rule_path), *cfg.extra_args]

    def try_json() -> float:
        proc = _run(base_cmd, stdin_text=json.dumps(payload))
        if proc.returncode != 0:
            raise FlexEngineError(
                "FLEX JSON call failed.\n"
                f"cmd: {' '.join(base_cmd)}\n"
                f"stderr:\n{proc.stderr.strip()}"
            )
        return _parse_risk_from_json(proc.stdout.strip())

    def try_kv() -> float:
        kv_args = [f"{k}={v}" for k, v in payload.items()]
        proc = _run([*base_cmd, *kv_args], stdin_text=None)
        if proc.returncode != 0:
            raise FlexEngineError(
                "FLEX key=value call failed.\n"
                f"cmd: {' '.join([*base_cmd, *kv_args])}\n"
                f"stderr:\n{proc.stderr.strip()}"
            )
        return _parse_risk_from_text(proc.stdout.strip())

    last_err: Exception | None = None
    if cfg.mode in ("auto", "json"):
        try:
            risk = try_json()
            return max(0.0, min(1.0, float(risk)))
        except Exception as e:
            last_err = e
            if cfg.mode == "json":
                raise

    if cfg.mode in ("auto", "kv"):
        try:
            risk = try_kv()
            return max(0.0, min(1.0, float(risk)))
        except Exception as e:
            last_err = e
            if cfg.mode == "kv":
                raise

    if cfg.mode == "auto":
        return _python_fuzzy_risk(signal_confidence, volatility, open_trades, eq)

    raise FlexEngineError(f"All FLEX modes failed. Last error: {last_err}") from last_err
