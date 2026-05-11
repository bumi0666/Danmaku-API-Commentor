from __future__ import annotations

import random
import sys
from collections import deque
from dataclasses import dataclass
from typing import Deque

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter
from PyQt5.QtWidgets import QApplication, QWidget

from danmaku.models import AppSettings, CommentBatch


@dataclass
class MovingComment:
    text: str
    x: float
    y: float
    speed: float
    width: int


class OverlayWindow(QWidget):
    """
    Optimized danmaku overlay.

    Instead of creating one QLabel per comment, this version draws all comments
    in a single QWidget using QPainter. This is much faster when many comments
    stay on screen for a long time.
    """

    def __init__(
        self,
        settings: AppSettings | None = None,
        enable_dummy_spawner: bool = False,
    ) -> None:
        super().__init__()

        self.settings = settings or AppSettings()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
            | Qt.Tool
        )

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        screen_geometry = QApplication.primaryScreen().geometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()
        self.setGeometry(0, 0, self.screen_width, self.screen_height)

        self.font = QFont(
            self.settings.font_family,
            self.settings.font_size,
            QFont.Bold,
        )
        self.font_metrics = QFontMetrics(self.font)

        self.active_comments: list[MovingComment] = []
        self.pending_comments: Deque[str] = deque()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animation_tick)
        self.animation_timer.start(
            getattr(self.settings, "animation_interval_ms", 33))

        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self._spawn_next_pending_comment)
        self.spawn_timer.start(
            getattr(self.settings, "comment_spawn_interval_ms", 1200))

        self.dummy_timer: QTimer | None = None
        if enable_dummy_spawner:
            self.dummy_timer = QTimer(self)
            self.dummy_timer.timeout.connect(self._enqueue_dummy_comment)
            self.dummy_timer.start(1500)

        self.dummy_comments = [
            "かわいい",
            "やったぜ",
            "仲間！",
            "これからどんな冒険が待ってるんだろうか",
            "てぇてぇ",
            "冒険始まる！",
            "神ゲー",
            "相棒との出会い、神",
            "いいなあ",
            "癒し",
            "相棒",
            "最高！",
        ]

    def add_comment_batch(self, batch: CommentBatch) -> None:
        """
        Queue comments so they appear separately over time.
        """
        comments = [*batch.comments, *batch.long_comments]

        for comment in comments:
            clean = str(comment).strip()
            if clean:
                self.pending_comments.append(clean)

    def add_comment(self, text: str) -> None:
        """
        Queue a single comment.
        """
        clean = str(text).strip()
        if clean:
            self.pending_comments.append(clean)

    def _enqueue_dummy_comment(self) -> None:
        self.pending_comments.append(random.choice(self.dummy_comments))

    def _spawn_next_pending_comment(self) -> None:
        if not self.pending_comments:
            return

        if len(self.active_comments) >= self.settings.max_simultaneous_comments:
            return

        text = self.pending_comments.popleft()
        self._spawn_comment_now(text)

    def _spawn_comment_now(self, text: str) -> None:
        top = int(self.screen_height * self.settings.overlay_top_ratio)
        bottom = int(self.screen_height * self.settings.overlay_bottom_ratio)

        y = random.randint(top, max(top + 1, bottom))

        width = self.font_metrics.horizontalAdvance(text)

        # Do not make long comments too slow.
        # Slow long comments stay on screen for too long and hurt performance.
        if len(text) >= 18:
            speed = random.uniform(5.0, 7.0)
        else:
            speed = random.uniform(4.0, 6.5)

        comment = MovingComment(
            text=text,
            x=float(self.screen_width),
            y=float(y),
            speed=speed,
            width=width,
        )

        self.active_comments.append(comment)

    def _animation_tick(self) -> None:
        next_active: list[MovingComment] = []

        for comment in self.active_comments:
            comment.x -= comment.speed

            if comment.x >= -comment.width:
                next_active.append(comment)

        self.active_comments = next_active
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setFont(self.font)

        for comment in self.active_comments:
            x = int(comment.x)
            y = int(comment.y)

            # Lightweight outline/shadow.
            painter.setPen(QColor(0, 0, 0, 220))
            painter.drawText(x + 2, y + 2, comment.text)
            painter.drawText(x - 1, y, comment.text)
            painter.drawText(x + 1, y, comment.text)

            painter.setPen(QColor(255, 255, 255, 255))
            painter.drawText(x, y, comment.text)


def main() -> None:
    app = QApplication(sys.argv)
    window = OverlayWindow(enable_dummy_spawner=True)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
