"""Validated subprocess bridge to the WebCMD CLI."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import WEBCMD_BIN, WEBCMD_TIMEOUT


def execute_webcmd(
    adapter_name: str,
    args_dict: dict[str, Any] | None = None,
    profile: str | None = None,
    session: str | None = None,
    raw_flags: str = "",
) -> Any:
    """Run ``webcmd run <adapter> -f json`` and decode its JSON stdout."""
    if not adapter_name or any(character in adapter_name for character in "\r\n\x00"):
        raise ValueError("adapter_name must be a non-empty single-line value")

    command = [WEBCMD_BIN, "run", adapter_name, "-f", "json"]
    for key, value in (args_dict or {}).items():
        if value is None or value is False:
            continue
        flag = str(key).replace("_", "-")
        command.append(f"--{flag}")
        if value is not True:
            command.append(str(value))
    if profile:
        command.extend(["--profile", profile])
    if session:
        command.extend(["--session", session])
    if raw_flags:
        command.extend(shlex.split(raw_flags, posix=False))

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=os.environ.copy(),
        )
        stdout, stderr = process.communicate(timeout=WEBCMD_TIMEOUT)
        return_code = process.returncode
    except FileNotFoundError as exc:
        raise RuntimeError(f"WebCMD executable not found: {WEBCMD_BIN}") from exc
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.communicate()
        raise RuntimeError(f"WebCMD timed out after {WEBCMD_TIMEOUT} seconds") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not start WebCMD: {exc}") from exc

    if return_code != 0:
        detail = (stderr or stdout).strip()
        raise RuntimeError(f"WebCMD failed with exit code {return_code}: {detail}")
    output = stdout.strip()
    if not output:
        raise RuntimeError("WebCMD returned no JSON output")
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"WebCMD returned invalid JSON: {exc}") from exc
