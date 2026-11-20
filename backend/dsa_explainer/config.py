"""Settings, read from environment variables or a .env file (see .env.example).

Everything the app writes lives in one data folder, HOME:
  - from a source checkout: the repository root (models/, outputs/, cache/, .env next to backend/)
  - when installed as a package: ~/.dsa-explainer
  - either way, the DSA_HOME environment variable overrides it.
Choices made in the app (settings.json in HOME) are applied on top by dsa_explainer.settings.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

VERSION = "0.2.0"

PACKAGE_DIR = Path(__file__).resolve().parent
_SOURCE_ROOT = PACKAGE_DIR.parents[1]  # backend/dsa_explainer -> backend -> repository root
IS_SOURCE_CHECKOUT = PACKAGE_DIR.parent.name == "backend" and (_SOURCE_ROOT / "backend").is_dir()
HOME = Path(os.getenv("DSA_HOME") or (_SOURCE_ROOT if IS_SOURCE_CHECKOUT else Path.home() / ".dsa-explainer"))
ROOT = HOME  # older name, kept for scripts
load_dotenv(HOME / ".env")

# Language model: any provider with an OpenAI-compatible chat API.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash")
LLM_FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "")  # used once LLM_MODEL's daily allowance runs out
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.4"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "180"))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "4"))  # first plan + repairs

# Narration voice: Kokoro-82M, run locally through ONNX.
KOKORO_MODEL = HOME / os.getenv("KOKORO_MODEL", "models/kokoro/kokoro-v1.0.onnx")
KOKORO_VOICES = HOME / os.getenv("KOKORO_VOICES", "models/kokoro/voices-v1.0.bin")
KOKORO_VOICE = os.getenv("KOKORO_VOICE", "af_heart")

RENDER_WORKERS = int(os.getenv("RENDER_WORKERS", str(max(1, min(4, (os.cpu_count() or 2) // 2)))))
DEFAULT_QUALITY = os.getenv("DEFAULT_QUALITY", "draft")

OUTPUT_DIR = HOME / "outputs"  # one folder per lesson
CACHE_DIR = HOME / "cache"  # narration audio and video clips, reused across lessons
SETTINGS_FILE = HOME / "settings.json"
PLANS_DIR = PACKAGE_DIR / "plans"  # verified lesson plans that render without an API key

HOST = os.getenv("DSA_HOST", "127.0.0.1")  # local only by default: the app is not meant to be exposed
PORT = int(os.getenv("DSA_PORT", "8000"))
