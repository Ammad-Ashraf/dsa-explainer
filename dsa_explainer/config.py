"""Settings, read from environment variables or a .env file (see .env.example)."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Language model: any provider with an OpenAI-compatible chat API.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash")
LLM_FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "")  # used once LLM_MODEL's daily allowance runs out
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.4"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "180"))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "4"))  # first plan + repairs

# Narration voice: Kokoro-82M, run locally through ONNX.
KOKORO_MODEL = ROOT / os.getenv("KOKORO_MODEL", "models/kokoro/kokoro-v1.0.onnx")
KOKORO_VOICES = ROOT / os.getenv("KOKORO_VOICES", "models/kokoro/voices-v1.0.bin")
KOKORO_VOICE = os.getenv("KOKORO_VOICE", "af_heart")

RENDER_WORKERS = int(os.getenv("RENDER_WORKERS", str(max(1, min(4, (os.cpu_count() or 2) // 2)))))

OUTPUT_DIR = ROOT / "outputs"
CACHE_DIR = ROOT / "cache"
EXAMPLES_DIR = ROOT / "examples"
