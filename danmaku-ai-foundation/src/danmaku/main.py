from __future__ import annotations

import json
import sys
import threading
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication

from danmaku.api.llm_client import GeminiLLMClient
from danmaku.capture.capture_service import CaptureService
from danmaku.config import load_settings_from_env
from danmaku.models import AppSettings, CaptureFrame, CommentBatch
from danmaku.overlay.overlay_window import OverlayWindow
from danmaku.ui.settings_window import SettingsWindow


class AppSignals(QObject):
    comments_ready = pyqtSignal(object)
    error = pyqtSignal(str)


class DanmakuApp:
    """
    Application coordinator.

    This class connects:
    - UI
    - capture
    - API
    - overlay
    - testing logs
    """

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.previous_summary = ""
        self.is_running = False
        self.is_busy = False

        self.signals = AppSignals()
        self.signals.comments_ready.connect(self._on_comments_ready)
        self.signals.error.connect(self._on_error)

        self.capture_service = CaptureService(
            output_dir=self.settings.capture_output_dir,
            target_window_title=self.settings.target_window_title,
        )

        self.llm_client = self._build_llm_client()

        self.overlay = OverlayWindow(settings=self.settings)
        self.settings_window = SettingsWindow(settings=self.settings)

        self.settings_window.start_requested.connect(self.start)
        self.settings_window.stop_requested.connect(self.stop)

        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self._trigger_capture_and_api)

    def show(self) -> None:
        self.settings_window.show()

    def start(self) -> None:
        self.settings_window.apply_to_settings()
        self.capture_service.set_target_window_title(
            self.settings.target_window_title)
        self.llm_client = self._build_llm_client()

        print("[app] starting")
        print(f"[app] dummy_api={self.settings.use_dummy_api}")
        print(f"[app] api_key_set={bool(self.settings.api_key)}")
        print(f"[app] model={self.settings.model_name}")
        print(
            f"[app] capture_dir={self.settings.capture_output_dir.resolve()}")
        print(
            f"[app] comment_log_dir={self.settings.comment_log_dir.resolve()}")
        print(
            f"[app] target_window={self.settings.target_window_title or 'Full screen'}")

        interval_ms = self.settings.capture_interval_seconds * 1000
        self.capture_timer.start(interval_ms)
        self.overlay.show()
        self.is_running = True
        self.settings_window.set_running(True)

        self._trigger_capture_and_api()

    def stop(self) -> None:
        self.capture_timer.stop()
        self.overlay.hide()
        self.is_running = False
        self.settings_window.set_running(False)
        print("[app] stopped")

    def _build_llm_client(self) -> GeminiLLMClient:
        return GeminiLLMClient(
            api_key=self.settings.api_key,
            model_name=self.settings.model_name,
            use_dummy_api=self.settings.use_dummy_api,
        )

    def _trigger_capture_and_api(self) -> None:
        if not self.is_running or self.is_busy:
            return

        self.is_busy = True
        thread = threading.Thread(
            target=self._capture_and_generate_worker, daemon=True)
        thread.start()

    def _capture_and_generate_worker(self) -> None:
        try:
            frame = self.capture_service.capture()
            print(f"[capture] saved {frame.image_path}")

            batch = self.llm_client.generate_comments(
                frame=frame,
                previous_summary=self.previous_summary,
            )

            self.signals.comments_ready.emit(
                {
                    "frame": frame,
                    "batch": batch,
                }
            )
        except Exception as exc:
            self.signals.error.emit(str(exc))

    def _on_comments_ready(self, payload: object) -> None:
        self.is_busy = False

        data = payload if isinstance(payload, dict) else {}
        frame = data.get("frame")
        batch = data.get("batch")

        if not isinstance(frame, CaptureFrame):
            print("[app] invalid frame payload")
            return

        if not isinstance(batch, CommentBatch):
            print("[app] invalid comment batch payload")
            return

        if batch.summary:
            self.previous_summary = batch.summary

        self.overlay.add_comment_batch(batch)

        if self.settings.save_comments:
            self._save_comment_batch(frame, batch)

    def _save_comment_batch(self, frame: CaptureFrame, batch: CommentBatch) -> None:
        self.settings.comment_log_dir.mkdir(parents=True, exist_ok=True)

        log_path = self.settings.comment_log_dir / "comments.jsonl"

        record = {
            "logged_at": datetime.now().isoformat(timespec="seconds"),
            "capture_timestamp": frame.timestamp,
            "image_path": str(frame.image_path),
            "ocr_text": frame.ocr_text,
            "comments": batch.comments,
            "long_comments": batch.long_comments,
            "summary": batch.summary,
            "used_dummy_api": self.settings.use_dummy_api,
            "model": self.settings.model_name,
        }

        with log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"[comments] saved {log_path}")

    def _on_error(self, message: str) -> None:
        self.is_busy = False
        print(f"[app] error: {message}")


def main() -> None:
    app = QApplication(sys.argv)
    settings = load_settings_from_env()
    danmaku_app = DanmakuApp(settings=settings)
    danmaku_app.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
