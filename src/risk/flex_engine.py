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
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Mode = Literal["auto", "kv", "json"]


class FlexEngineError(RuntimeError):
    pass


@dataclass(frozen=True)
class FlexConfig:
    # --- CONFIGURE ME ---
    # Command/binary name. If you installed it elsewhere, use an absolute path.
    flex_cmd: str = "flex"
    # Path to the rule file.
    rule_path: Path = Path("rules/risk.flex")
    # Extra args. Example for JSON mode: ["--json"]
    extra_args: tuple[str, ...] = ()
    # Which mode to use. "auto" tries JSON first, then key=value.
    mode: Mode = "auto"


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
    *,
    cfg: FlexConfig = FlexConfig(),
) -> float:
    """
    Returns risk_per_trade in [0, 1].
    Raises FlexEngineError on CLI or parsing failures.
    """
    _validate_inputs(signal_confidence, volatility, open_trades)

    if not cfg.rule_path.exists():
        raise FlexEngineError(f"Rule file not found: {cfg.rule_path}")

    payload = {
        "signal_confidence": float(signal_confidence),
        "volatility": float(volatility),
        "open_trades": float(open_trades),
    }

    base_cmd = [cfg.flex_cmd, str(cfg.rule_path), *cfg.extra_args]

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

    raise FlexEngineError(f"All FLEX modes failed. Last error: {last_err}") from last_err


