from __future__ import annotations

import os
import sys
from pathlib import Path

from danmaku.models import AppSettings


def resource_path(relative_path: str) -> Path:
    """
    Return an absolute path for bundled files.

    Works both in normal Python execution and after PyInstaller packaging.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path.cwd() / relative_path


def load_text_file(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def load_settings_from_env() -> AppSettings:
    """
    Load basic settings from environment variables.

    Do not hardcode real API keys in the source code.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    use_dummy_raw = os.getenv("DANMAKU_USE_DUMMY_API", "true").strip().lower()

    return AppSettings(
        capture_interval_seconds=int(os.getenv("CAPTURE_INTERVAL_SECONDS", "6")),
        model_name=os.getenv("MODEL_NAME", "gemini-2.0-flash-lite"),
        api_key=api_key,
        use_dummy_api=use_dummy_raw in {"1", "true", "yes", "y"} or not api_key,
    )
