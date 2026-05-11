from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AppSettings:
    """Runtime settings shared across modules."""

    capture_interval_seconds: int = 6
    model_name: str = "gemini-2.5-flash-lite"
    api_key: str = ""
    use_dummy_api: bool = True

    # Testing / logging
    save_captures: bool = True
    save_comments: bool = True
    capture_output_dir: Path = Path("logs/captures")
    comment_log_dir: Path = Path("logs/comments")

    # Capture settings
    target_window_title: str = ""  # empty means full screen

    # Overlay settings
    font_family: str = "Malgun Gothic"
    font_size: int = 40

    max_simultaneous_comments: int = 15
    overlay_top_ratio: float = 0.05
    overlay_bottom_ratio: float = 0.3

    comment_spawn_interval_ms: int = 2200
    animation_interval_ms: int = 33
    min_comment_speed: float = 10.0
    max_comment_speed: float = 17.0


@dataclass(slots=True)
class CaptureFrame:
    """A captured screen frame, plus optional OCR text."""

    image_path: Path
    timestamp: float
    ocr_text: str | None = None


@dataclass(slots=True)
class CommentBatch:
    """Structured comments returned by the API module."""

    comments: list[str] = field(default_factory=list)
    long_comments: list[str] = field(default_factory=list)
    summary: str = ""

    @classmethod
    def fallback(cls, reason: str = "") -> "CommentBatch":
        suffix = f" ({reason})" if reason else ""
        return cls(
            comments=["API_ERROR", "fallback", "check_terminal"],
            long_comments=["API call failed, so fallback comments were used."],
            summary=f"Fallback response used{suffix}.",
        )
