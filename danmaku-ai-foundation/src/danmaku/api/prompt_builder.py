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
        Analyze the current screenshot and generate danmaku-style reaction comments.

        You are given three kinds of information:

        1. Previous context:
        This may include an overall summary and recent scene history.
        Use this to understand the current screen as part of an ongoing scene.

        2. OCR text:
        This is text extracted from the dialogue/subtitle area.
        It may be incomplete or contain recognition errors.
        If the screenshot shows only part of a sentence, use the previous context and OCR text to infer the likely full meaning.

        3. Current screenshot:
        Use this for visual information such as characters, location, emotion, UI state, and action.

        Previous context:
        {previous_summary or "(none)"}

        Current OCR text:
        {ocr_text or "(none)"}

        Return strict JSON with this schema:
        {{
        "comments": ["short comment", "short comment"],
        "long_comments": ["longer reaction comment"],
        "summary": "updated context summary for the next request"
        }}

        Rules:
        - Generate comments that react to the whole situation, not only the current screenshot.
        - If dialogue text is cut off, combine current OCR, previous context, and the screenshot.
        - Do not over-focus on visible UI details unless they are important.
        - comments: 4 to 8 short Korean danmaku/tvple-style reactions.
        - long_comments: 1 to 2 slightly longer Korean reactions.
        - summary: 1 to 2 sentences summarizing the current situation and preserving important continuity.
        - The summary should be useful for understanding the next screenshot.
        - Do not include Markdown.
        - Do not include explanations outside JSON.
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
