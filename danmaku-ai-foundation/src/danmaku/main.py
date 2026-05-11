from __future__ import annotations

import sys
import threading

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication

from danmaku.api.llm_client import GeminiLLMClient
from danmaku.capture.capture_service import CaptureService
from danmaku.config import load_settings_from_env
from danmaku.models import AppSettings, CommentBatch
from danmaku.overlay.overlay_window import OverlayWindow
from danmaku.ui.settings_window import SettingsWindow


class AppSignals(QObject):
    comments_ready = pyqtSignal(object)
    error = pyqtSignal(str)


class DanmakuApp:
    """
    Application coordinator.

    This class is the glue between:
    - UI
    - capture
    - API
    - overlay
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
            filename=self.settings.capture_filename,
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
        self.llm_client = self._build_llm_client()

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
        thread = threading.Thread(target=self._capture_and_generate_worker, daemon=True)
        thread.start()

    def _capture_and_generate_worker(self) -> None:
        try:
            frame = self.capture_service.capture()
            batch = self.llm_client.generate_comments(
                frame=frame,
                previous_summary=self.previous_summary,
            )
            self.signals.comments_ready.emit(batch)
        except Exception as exc:
            self.signals.error.emit(str(exc))

    def _on_comments_ready(self, batch: CommentBatch) -> None:
        self.is_busy = False
        if batch.summary:
            self.previous_summary = batch.summary
        self.overlay.add_comment_batch(batch)

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
