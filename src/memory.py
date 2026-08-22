"""Small, atomic JSON-backed user memory store."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import MEMORY_PATH

MEMORY_FILE = Path(MEMORY_PATH)


def _read() -> dict[str, Any]:
    if not MEMORY_FILE.exists():
        return {}
    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read user memory at {MEMORY_FILE}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("User memory must contain a JSON object")
    return value


def load_memory() -> dict[str, Any]:
    """Return a defensive copy of all persisted memory."""
    return deepcopy(_read())


def _write(value: dict[str, Any]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_path = tempfile.mkstemp(
        prefix=f"{MEMORY_FILE.stem}.", suffix=".tmp", dir=MEMORY_FILE.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, MEMORY_FILE)
    except OSError as exc:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise RuntimeError(f"Could not write user memory at {MEMORY_FILE}: {exc}") from exc


def update_memory(key: str, data: dict[str, Any]) -> dict[str, Any]:
    """Merge a top-level memory section and persist it atomically."""
    if not key or not isinstance(data, dict):
        raise ValueError("key must be non-empty and data must be a dictionary")
    memory = _read()
    existing = memory.get(key, {})
    if existing is not None and not isinstance(existing, dict):
        raise ValueError(f"Memory section {key!r} is not an object")
    merged = {**(existing or {}), **deepcopy(data)}
    memory[key] = merged
    _write(memory)
    return deepcopy(merged)


def get_student_profile() -> dict[str, Any]:
    return deepcopy(_read().get("student_profile", {}))


def get_billing_accounts() -> dict[str, Any]:
    return deepcopy(_read().get("billing_accounts", {}))


def get_healthcare_preferences() -> dict[str, Any]:
    return deepcopy(_read().get("healthcare_preferences", {}))
