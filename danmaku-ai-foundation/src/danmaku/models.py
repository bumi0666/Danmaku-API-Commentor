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

    # Overlay settings
    font_family: str = "Malgun Gothic"
    font_size: int = 40
    max_simultaneous_comments: int = 15
    overlay_top_ratio: float = 0.05
    overlay_bottom_ratio: float = 0.45


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
