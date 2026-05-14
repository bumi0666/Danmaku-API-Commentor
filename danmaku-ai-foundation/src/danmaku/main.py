from __future__ import annotations

import json
import sys
import time
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
        self.summary_history: list[str] = []
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
        self._initialize_run_logging()
        self.capture_service = CaptureService(
            output_dir=self.settings.capture_output_dir,
            target_window_title=self.settings.target_window_title,
        )
        self.llm_client = self._build_llm_client()

        print("[app] starting")
        print(f"[app] dummy_api={self.settings.use_dummy_api}")
        print(f"[app] api_key_set={bool(self.settings.api_key)}")
        print(f"[app] model={self.settings.model_name}")
        print(f"[app] capture_dir={self.settings.capture_output_dir.resolve()}")
        print(f"[app] comment_log_path={self.settings.comment_log_path.resolve()}")
        print(f"[app] target_window={self.settings.target_window_title or 'Full screen'}")

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

    def _build_context_summary(self) -> str:
        """
        Build context sent to the LLM.

        Includes:
        - rolling summary of the overall situation
        - last 4 scene summaries
        """

        parts: list[str] = []

        if self.previous_summary:
            parts.append(
                "Overall context so far:\n"
                f"{self.previous_summary}"
            )

        recent = self.summary_history[-4:]

        if recent:
            recent_text = "\n".join(
                f"{index + 1}. {summary}"
                for index, summary in enumerate(recent)
            )

            parts.append(
                "Recent scene history, oldest to newest:\n"
                f"{recent_text}"
            )

        return "\n\n".join(parts)

    def _build_rolling_summary(self) -> str:
        """
        Build a bounded rolling summary from recent scene summaries.

        This is not perfect semantic compression, but it keeps enough continuity
        without sending unlimited history.
        """

        recent = self.summary_history[-8:]

        if not recent:
            return ""

        joined = " ".join(recent)

        max_chars = 1200

        if len(joined) <= max_chars:
            return joined

        return joined[-max_chars:]

    def _trigger_capture_and_api(self) -> None:
        if not self.is_running or self.is_busy:
            return

        self.is_busy = True
        thread = threading.Thread(
            target=self._capture_and_generate_worker, daemon=True)
        thread.start()

    def _capture_and_generate_worker(self) -> None:
        try:
            worker_started = time.perf_counter()

            capture_started = time.perf_counter()
            frame = self.capture_service.capture()
            capture_finished = time.perf_counter()

            image_size_kb = round(frame.image_path.stat().st_size / 1024, 1)
            print(f"[capture] saved {frame.image_path} ({image_size_kb} KB)")

            api_started = time.perf_counter()
            context_for_api = self._build_context_summary()

            print(
                "[context] "
                f"rolling_summary_chars={len(self.previous_summary)}, "
                f"history_count={len(self.summary_history)}, "
                f"context_sent_chars={len(context_for_api)}"
            )

            batch = self.llm_client.generate_comments(
                frame=frame,
                previous_summary=context_for_api,
            )

            api_finished = time.perf_counter()

            metrics = {
                "capture_duration_sec": round(capture_finished - capture_started, 3),
                "comment_after_capture_sec": round(api_finished - capture_finished, 3),
                "api_duration_sec": round(api_finished - api_started, 3),
                "total_worker_duration_sec": round(api_finished - worker_started, 3),
            }

            print(
                "[timing] "
                f"capture={metrics['capture_duration_sec']}s, "
                f"after_capture_to_comments={metrics['comment_after_capture_sec']}s, "
                f"total={metrics['total_worker_duration_sec']}s"
            )

            self.signals.comments_ready.emit(
                {
                    "frame": frame,
                    "batch": batch,
                    "metrics": metrics,
                    "context_sent": context_for_api,
                }
            )

        except Exception as exc:
            self.signals.error.emit(str(exc))

    def _on_comments_ready(self, payload: object) -> None:
        self.is_busy = False

        data = payload if isinstance(payload, dict) else {}
        frame = data.get("frame")
        batch = data.get("batch")
        metrics = data.get("metrics", {})
        context_sent = data.get("context_sent", "")

        if not isinstance(frame, CaptureFrame):
            print("[app] invalid frame payload")
            return

        if not isinstance(batch, CommentBatch):
            print("[app] invalid comment batch payload")
            return

        if batch.summary:
            clean_summary = batch.summary.strip()

            self.summary_history.append(clean_summary)
            self.summary_history = self.summary_history[-8:]

            self.previous_summary = self._build_rolling_summary()

            print(
                "[context] updated: "
                f"history_count={len(self.summary_history)}, "
                f"rolling_summary_chars={len(self.previous_summary)}"
            )

        self.overlay.add_comment_batch(batch)

        if self.settings.save_comments:
            self._save_comment_batch(frame, batch, metrics, context_sent)

    def _save_comment_batch(self,
                            frame: CaptureFrame,
                            batch: CommentBatch,
                            metrics: dict | None = None,
                            context_sent: str = "",
                            ) -> None:
        self.settings.comment_log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path = self.settings.comment_log_path   

        record = {
            "logged_at": datetime.now().isoformat(timespec="seconds"),
            "capture_timestamp": frame.timestamp,
            "image_path": str(frame.image_path),
            "ocr_text": frame.ocr_text,
            "comments": batch.comments,
            "long_comments": batch.long_comments,
            "summary": batch.summary,
            "summary_history": self.summary_history[-4:],
            "context_sent": context_sent,
            "used_dummy_api": self.settings.use_dummy_api,
            "model": self.settings.model_name,
            "timing": metrics or {},
        }

        with log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"[comments] saved {log_path}")

    def _initialize_run_logging(self) -> None:
        run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")

        self.settings.run_log_dir = self.settings.log_root_dir / run_id
        self.settings.capture_output_dir = self.settings.run_log_dir / "captures"
        self.settings.comment_log_path = self.settings.run_log_dir / "comments.jsonl"

        self.settings.capture_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[log] run_id={run_id}")
        print(f"[log] run_dir={self.settings.run_log_dir.resolve()}")
        print(
            f"[log] capture_dir={self.settings.capture_output_dir.resolve()}")
        print(f"[log] comments={self.settings.comment_log_path.resolve()}")

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
