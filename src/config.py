"""Environment configuration and project paths."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(Path(BASE_DIR) / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in the project .env file.")

USER_MEMORY_PATH = os.path.join(BASE_DIR, "data", "user_memory.json")
# Backward-compatible name used by the memory module.
MEMORY_PATH = os.path.join(BASE_DIR, "data", "user_memory.json")
ADAPTERS_PATH = os.path.join(BASE_DIR, "adapters")
WEBCMD_BIN = "webcmd.cmd"
WEBCMD_TIMEOUT = 60