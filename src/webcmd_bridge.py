"""Validated subprocess bridge to the WebCMD CLI with Playwright browser & Node fallback."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from typing import Any

# Ensure project root is in sys.path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import ADAPTERS_PATH, BASE_DIR, WEBCMD_BIN, WEBCMD_TIMEOUT


def resolve_adapter_path(adapter_input: str) -> str:
    """Resolve an adapter short name or relative path to a valid absolute filepath."""
    if not adapter_input:
        raise ValueError("Adapter name or path cannot be empty.")
    
    if adapter_input.endswith(".js") or os.path.sep in adapter_input or "/" in adapter_input:
        full_path = os.path.abspath(os.path.join(BASE_DIR, adapter_input)) if not os.path.isabs(adapter_input) else adapter_input
    else:
        full_path = os.path.join(ADAPTERS_PATH, f"{adapter_input}.js")

    if not os.path.exists(full_path):
        if not full_path.endswith(".js") and os.path.exists(f"{full_path}.js"):
            full_path = f"{full_path}.js"
        else:
            raise FileNotFoundError(f"Adapter file not found at: {full_path}")
    return full_path


def parse_json_from_output(stdout: str) -> Any:
    """Extract and parse structured JSON from CLI stdout, handling extraneous log text."""
    stdout_trimmed = stdout.strip()
    if not stdout_trimmed:
        raise ValueError("Empty output received from process stdout.")

    # Try direct parse
    try:
        return json.loads(stdout_trimmed)
    except json.JSONDecodeError:
        pass

    # Extract JSON object using regex if preceded/followed by logs
    json_match = re.search(r"(\{.*\}|\[.*\])", stdout_trimmed, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    for line in reversed(stdout_trimmed.splitlines()):
        line = line.strip()
        if (line.startswith("{") and line.endswith("}")) or (line.startswith("[") and line.endswith("]")):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not parse valid JSON from output:\n{stdout_trimmed[:500]}")


def execute_webcmd(
    adapter_name: str,
    args_dict: dict[str, Any] | None = None,
    profile: str | None = None,
    session: str | None = None,
    raw_flags: str = "",
) -> Any:
    """Run `webcmd --session <id> browser run --file <adapter.js> -f json` with robust fallback."""
    adapter_path = resolve_adapter_path(adapter_name)
    
    # Base command positioning: webcmd [--session ...] [--profile ...] browser run --file ...
    if os.name == "nt":
        command = ["cmd", "/c", WEBCMD_BIN]
    else:
        command = [WEBCMD_BIN]

    if session:
        command.extend(["--session", session])
    if profile:
        command.extend(["--profile", profile])

    command.extend(["browser", "run", "--file", adapter_path, "-f", "json"])

    # Convert args_dict to CLI flags
    for key, value in (args_dict or {}).items():
        if value is None or value is False:
            continue
        flag = str(key).replace("_", "-")
        command.append(f"--{flag}")
        if value is True:
            continue
        if isinstance(value, (dict, list)):
            command.append(json.dumps(value))
        else:
            command.append(str(value))

    if raw_flags:
        command.extend(shlex.split(raw_flags, posix=(os.name != "nt")))

    # Attempt WebCMD CLI browser execution first
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
        if process.returncode == 0 and stdout.strip():
            try:
                parsed = parse_json_from_output(stdout)
                # If webcmd browser wrapper returns {"ok": true, ...}
                if isinstance(parsed, dict) and "ok" in parsed and "result" in parsed:
                    if parsed.get("result"):
                        try:
                            return json.loads(parsed["result"])
                        except Exception:
                            return parsed["result"]
                return parsed
            except ValueError:
                pass
    except Exception:
        pass

    # Direct Node.js fallback if WebCMD CLI is unavailable or fails
    node_command = ["node", adapter_path]
    for key, value in (args_dict or {}).items():
        if value is None or value is False:
            continue
        flag = str(key).replace("_", "-")
        node_command.append(f"--{flag}")
        if value is not True:
            if isinstance(value, (dict, list)):
                node_command.append(json.dumps(value))
            else:
                node_command.append(str(value))

    try:
        node_process = subprocess.Popen(
            node_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=os.environ.copy(),
        )
        stdout, stderr = node_process.communicate(timeout=WEBCMD_TIMEOUT)
        if node_process.returncode == 0:
            return parse_json_from_output(stdout)
        else:
            raise RuntimeError(f"Node adapter failed with exit code {node_process.returncode}: {stderr.strip()}")
    except FileNotFoundError as exc:
        raise RuntimeError("Neither WebCMD CLI nor Node.js could be executed.") from exc
    except Exception as exc:
        raise RuntimeError(f"Execution failed for adapter {adapter_name}: {exc}") from exc
