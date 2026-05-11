from __future__ import annotations

from danmaku.config import load_text_file, resource_path
from danmaku.models import CaptureFrame


class PromptBuilder:
    """Builds prompts for danmaku comment generation."""

    def __init__(self, system_prompt_path: str = "prompts/system_prompt.txt") -> None:
        self.system_prompt_path = system_prompt_path

    def build_system_prompt(self) -> str:
        default_prompt = (
            "You generate short Japanese danmaku-style reaction comments from a game "
            "or video screenshot. Return strict JSON only."
        )
        return load_text_file(resource_path(self.system_prompt_path), default_prompt)

    def build_user_prompt(self, frame: CaptureFrame, previous_summary: str) -> str:
        ocr_text = frame.ocr_text or ""

        return f"""
Analyze the current screenshot and generate danmaku-style comments.

Previous summary:
{previous_summary or "(none)"}

OCR text from dialogue/subtitle region, may contain errors:
{ocr_text or "(none)"}

Return strict JSON with this schema:
{{
  "comments": ["short comment", "short comment"],
  "long_comments": ["longer reaction comment"],
  "summary": "brief summary for next request"
}}

Rules:
- comments: 8 to 12 short Japanese danmaku-style reactions.
- long_comments: 1 to 3 slightly longer Japanese reactions.
- summary: 1 to 2 sentences in English or Korean.
- Do not include Markdown.
- Do not include explanations outside JSON.
""".strip()


def main() -> None:
    from pathlib import Path
    from danmaku.models import CaptureFrame

    builder = PromptBuilder()
    frame = CaptureFrame(image_path=Path("example.png"), timestamp=0, ocr_text="こんにちは")
    print("SYSTEM PROMPT:")
    print(builder.build_system_prompt())
    print("\nUSER PROMPT:")
    print(builder.build_user_prompt(frame, previous_summary="A character entered the scene."))


if __name__ == "__main__":
    main()
