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

    def build_user_prompt(
        self,
        frame: CaptureFrame,
        previous_summary: str,
        previous_comments: list[str] | None = None,
    ) -> str:
        ocr_text = frame.ocr_text or ""
        recent_comment_text = "\n".join(
            f"- {comment}"
            for comment in (previous_comments or [])
            if comment.strip()
        )

        return f"""
        Analyze the current screenshot and generate danmaku-style reaction comments.

        You are given four kinds of information:

        1. Previous context:
        This may include an overall summary and recent scene history.
        Use this to understand the current screen as part of an ongoing scene.

        2. OCR text:
        This is text extracted from the dialogue/subtitle area.
        It may be incomplete or contain recognition errors.
        If the screenshot shows only part of a sentence, use the previous context
        and OCR text to infer the likely full meaning.

        3. Current screenshot:
        Use this for visual information such as characters, location, emotion,
        UI state, and action.

        4. Recent generated comments:
        These are comments that were already shown recently.
        Use them only to avoid repetition.

        Previous context:
        {previous_summary or "(none)"}

        Current OCR text:
        {ocr_text or "(none)"}

        Recent generated comments:
        {recent_comment_text or "(none)"}

        Return strict JSON with this schema:
        {{
          "comments": ["short comment", "short comment"],
          "long_comments": ["longer reaction comment"],
          "summary": "updated context summary for the next request"
        }}

        Rules:
        - Generate comments that react to the whole situation, not only the current screenshot.
        - The current screenshot is the most important source of truth.
        - If previous context conflicts with the current screenshot, trust the current screenshot.
        - If the current screenshot appears to be a new scene, topic, video, game,
          menu, or page, ignore outdated previous context.
        - If this is a clear scene change, start the summary with "[SCENE_CHANGE] ".
        - If dialogue text is cut off, combine current OCR, previous context, and the screenshot.
        - Do not over-focus on visible UI details unless they are important.
        - Do not invent dialogue, names, or events that are not supported by the image or context.
        - Do not repeat recent generated comments.
        - Avoid near-duplicates that only change particles, punctuation, or laughter.
        - comments: 3 to 6 short Korean danmaku/tvple-style reactions.
        - long_comments: 0 to 1 slightly longer Korean reaction.
        - summary: 1 short sentence preserving only important continuity for the next request.
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
        frame,
        previous_summary="A character entered the scene.",
        previous_comments=["ㅋㅋㅋ 뭐야", "이건 좀 웃기네"],
    ))


if __name__ == "__main__":
    main()
