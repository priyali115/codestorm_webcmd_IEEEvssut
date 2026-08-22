"""Environment configuration and project paths for Universal AI Browser Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ADAPTERS_PATH = os.path.join(BASE_DIR, "adapters")
USER_MEMORY_PATH = os.path.join(DATA_DIR, "user_memory.json")
MEMORY_PATH = USER_MEMORY_PATH

# Load environment variables from .env if present
load_dotenv(Path(BASE_DIR) / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# OS-aware WebCMD CLI binary resolution
if os.name == "nt":
    WEBCMD_BIN = os.getenv("WEBCMD_BIN", "webcmd.cmd")
else:
    WEBCMD_BIN = os.getenv("WEBCMD_BIN", "webcmd")

WEBCMD_TIMEOUT = int(os.getenv("WEBCMD_TIMEOUT", "60"))