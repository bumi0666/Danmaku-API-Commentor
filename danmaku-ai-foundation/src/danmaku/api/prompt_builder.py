from __future__ import annotations

from danmaku.config import load_text_file, resource_path
from danmaku.models import CaptureFrame


class PromptBuilder:
    """Builds prompts for danmaku comment generation."""

    def __init__(self, system_prompt_path: str = "prompts/system_prompt.txt") -> None:
        self.system_prompt_path = system_prompt_path

    def build_system_prompt(self) -> str:
        default_prompt = (
            "You generate short Korean danmaku/tvple-style reaction comments from a game "
            "or video screenshot. Return strict JSON only."
        )
        return load_text_file(resource_path(self.system_prompt_path), default_prompt)

    def build_user_prompt(self, frame: CaptureFrame, previous_summary: str) -> str:
        ocr_text = frame.ocr_text or ""

        return f"""
        Generate Korean danmaku-style reactions for this screenshot.
        Use previous context and OCR only when helpful.

        Previous context:
        {previous_summary or "(none)"}

        OCR text:
        {ocr_text or "(none)"}

        Return strict JSON only:
        {{
          "comments": ["short reaction"],
          "long_comments": ["slightly longer reaction"],
          "summary": "1 short sentence for next request"
        }}

        Rules:
        - comments: 3 to 6 short Korean audience reactions.
        - long_comments: 0 to 1 casual Korean reaction.
        - summary: concise, preserve only important continuity.
        - No Markdown or extra text.
        """.strip()


def main() -> None:
    from pathlib import Path
    from danmaku.models import CaptureFrame

    builder = PromptBuilder()
    frame = CaptureFrame(image_path=Path("example.png"),
                         timestamp=0, ocr_text="こんにちは")
    print("SYSTEM PROMPT:")
    print(builder.build_system_prompt())
    print("\nUSER PROMPT:")
    print(builder.build_user_prompt(
        frame, previous_summary="A character entered the scene."))


if __name__ == "__main__":
    main()
