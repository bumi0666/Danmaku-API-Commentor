from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from danmaku.models import CaptureFrame


class CaptureService:
    """
    Basic screen capture service.

    MVP behavior:
    - captures the whole primary screen
    - saves timestamped PNG files
    - returns CaptureFrame
    """

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(self) -> CaptureFrame:
        image_path = self._make_capture_path()
        self._capture_full_screen(image_path)

        return CaptureFrame(
            image_path=image_path,
            timestamp=time.time(),
            ocr_text=None,
        )

    def _make_capture_path(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return self.output_dir / f"capture_{timestamp}.png"

    def _capture_full_screen(self, output_path: Path) -> None:
        """
        Capture the full screen.

        Uses mss if available. Falls back to PIL.ImageGrab.
        """
        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                image.save(output_path)
                return
        except Exception:
            pass

        try:
            from PIL import ImageGrab

            image = ImageGrab.grab()
            image.save(output_path)
            return
        except Exception as exc:
            raise RuntimeError(f"Screen capture failed: {exc}") from exc


def main() -> None:
    service = CaptureService(output_dir=Path("logs/captures"))
    frame = service.capture()
    print(f"Captured: {frame.image_path.resolve()}")


if __name__ == "__main__":
    main()
