from __future__ import annotations

import random
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QGraphicsDropShadowEffect, QLabel, QWidget

from danmaku.models import AppSettings, CommentBatch


class DanmakuLabel(QLabel):
    def __init__(
        self,
        text: str,
        parent: QWidget | None = None,
        start_x: int = 0,
        start_y: int = 0,
        speed: int = 5,
        settings: AppSettings | None = None,
    ) -> None:
        super().__init__(text, parent)

        self.settings = settings or AppSettings()
        self.x_pos = float(start_x)
        self.y_pos = float(start_y)
        self.speed = float(speed)

        font = QFont(self.settings.font_family, self.settings.font_size, QFont.Bold)
        self.setFont(font)
        self.setStyleSheet("color: white;")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(2)
        shadow.setColor(Qt.black)
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

        self.adjustSize()
        self.move(int(self.x_pos), int(self.y_pos))
        self.show()

    def update_position(self) -> bool:
        self.x_pos -= self.speed
        self.move(int(self.x_pos), int(self.y_pos))
        return self.x_pos >= -self.width()


class OverlayWindow(QWidget):
    def __init__(self, settings: AppSettings | None = None, enable_dummy_spawner: bool = False) -> None:
        super().__init__()

        self.settings = settings or AppSettings()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen_geometry = QApplication.primaryScreen().geometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()
        self.setGeometry(0, 0, self.screen_width, self.screen_height)

        self.active_labels: list[DanmakuLabel] = []

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_labels)
        self.anim_timer.start(16)

        self.spawn_timer: QTimer | None = None
        if enable_dummy_spawner:
            self.spawn_timer = QTimer(self)
            self.spawn_timer.timeout.connect(self.spawn_dummy_text)
            self.spawn_timer.start(1500)

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
        all_comments = [*batch.comments, *batch.long_comments]
        for index, comment in enumerate(all_comments):
            delay_ms = index * 300
            QTimer.singleShot(delay_ms, lambda c=comment: self.add_comment(c))

    def add_comment(self, text: str) -> None:
        if len(self.active_labels) >= self.settings.max_simultaneous_comments:
            oldest = self.active_labels.pop(0)
            oldest.deleteLater()

        top = int(self.screen_height * self.settings.overlay_top_ratio)
        bottom = int(self.screen_height * self.settings.overlay_bottom_ratio)
        start_y = random.randint(top, max(top + 1, bottom))
        speed = random.randint(4, 8)

        label = DanmakuLabel(
            text=text,
            parent=self,
            start_x=self.screen_width,
            start_y=start_y,
            speed=speed,
            settings=self.settings,
        )
        self.active_labels.append(label)

    def spawn_dummy_text(self) -> None:
        self.add_comment(random.choice(self.dummy_comments))

    def animate_labels(self) -> None:
        for label in reversed(self.active_labels):
            is_visible = label.update_position()
            if not is_visible:
                self.active_labels.remove(label)
                label.deleteLater()


def main() -> None:
    app = QApplication(sys.argv)
    window = OverlayWindow(enable_dummy_spawner=True)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
