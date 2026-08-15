#!/usr/bin/env python3
"""data.py — THE ONLY FILE THAT TOUCHES PANKAJ'S REAL DATA.

Reads HEER_DEMO and INDEX_PATHS from .env.
- HEER_DEMO=1 -> invented fixtures from data/demo (safe to screen-record)
- HEER_DEMO=0 -> real folders listed in INDEX_PATHS (read-only)

Everything else in the codebase goes through this module to reach data.
"""

import os
import sys

# Paths
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(BASE, "data", "demo")
MEMORY_DIR = os.path.join(BASE, "memory")
ENV_PATH = os.path.join(BASE, ".env")

# ---------------------------------------------------------------------------
# .env loading (stdlib only — no python-dotenv)
# ---------------------------------------------------------------------------


def _load_env():
    env = {}
    try:
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return env


_ENV = _load_env()


def env(key, default=""):
    """Read a value from .env, falling back to process env."""
    return _ENV.get(key, os.environ.get(key, default))


def demo_mode():
    """1 = demo fixtures, 0 = real folders. Defaults to demo."""
    return env("HEER_DEMO", "1") == "1"


def index_paths():
    """Real folders to index. Empty in demo mode."""
    raw = env("INDEX_PATHS", "")
    return [p.strip() for p in raw.split(",") if p.strip()]


def elevenlabs_key():
    return env("ELEVENLABS_API_KEY", "")


def elevenlabs_voice_id():
    return env("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")


def edge_tts_voice():
    """Free Microsoft Edge neural voice for TTS (no API key required)."""
    return env("EDGE_TTS_VOICE", "en-US-JennyNeural")


def asr_url():
    """OpenAI-compatible /audio/transcriptions endpoint (e.g. local Whisper)."""
    return env("ASR_API_URL", "")


def asr_key():
    return env("ASR_API_KEY", "")


def asr_model():
    return env("ASR_MODEL", "whisper-1")


def business_roots(business_id=None):
    """Per-business index paths.

    In demo mode, each business resolves to its own demo root
    (data/demo for the default AI agency, data/demo_businesses/<id>
    for additional demo businesses). In real mode, the business's
    configured data_root is used.
    """
    from . import business

    b = business.get_business(business_id) if business_id else business.current_business()
    if b is None:
        return []
    root = business.business_data_root(b["id"])
    if not root:
        return []
    if demo_mode():
        # Demo businesses live under data/demo_businesses/<id> unless they
        # explicitly point at the shared demo root.
        if b.get("id") == "ai_agency":
            return [DEMO_DIR]
        return [root]
    return [root]


def data_root(business_id=None):
    """The root directory this session reads from (scoped to a business)."""
    roots = business_roots(business_id)
    if not roots:
        return None
    return roots[0]


def all_roots(business_id=None):
    """All directories to index (demo or real), scoped to a business."""
    return business_roots(business_id)
