from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AppSettings:
    """Runtime settings shared across modules."""

    capture_interval_seconds: int = 6
    model_name: str = "gemini-2.0-flash-lite"
    api_key: str = ""
    use_dummy_api: bool = True

    # Overlay settings
    font_family: str = "Malgun Gothic"
    font_size: int = 40
    max_simultaneous_comments: int = 15
    overlay_top_ratio: float = 0.05
    overlay_bottom_ratio: float = 0.45

    # Capture settings
    capture_output_dir: Path = Path("temp_captures")
    capture_filename: str = "latest_capture.png"


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
            comments=["きた！", "いいね", "かわいい"],
            long_comments=["これからどうなるんだろう"],
            summary=f"Fallback response used{suffix}.",
        )
