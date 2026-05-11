import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class DanmakuLabel(QLabel):
    def __init__(self, text, parent=None, start_x=0, start_y=0, speed=5):
        super().__init__(text, parent)
        self.x_pos = start_x
        self.y_pos = start_y
        self.speed = speed

        # 1. Font Styling (Large, Bold)
        font = QFont("Malgun Gothic", 40, QFont.Bold)
        self.setFont(font)
        self.setStyleSheet("color: white;")

        # 2. Text Outline (Using Drop Shadow to make it readable on any background)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(2)
        shadow.setColor(Qt.black)
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

        self.move(int(self.x_pos), int(self.y_pos))
        self.show()

    def update_position(self):
        # Move left by 'speed' pixels
        self.x_pos -= self.speed
        self.move(int(self.x_pos), int(self.y_pos))

        # Return False if it moved off the left side of the screen
        if self.x_pos < -self.width():
            return False
        return True


class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 1. Window Configuration: Transparent, Always on Top, Click-Through
        self.setWindowFlags(Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 2. Fit to Screen
        screen_geometry = QApplication.primaryScreen().geometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()
        self.setGeometry(0, 0, self.screen_width, self.screen_height)

        self.active_labels = []

        # 3. Animation Timer (Updates UI roughly at 60 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_labels)
        self.anim_timer.start(16)

        # 4. Dummy Text Spawner Timer (Simulates receiving API data)
        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self.spawn_dummy_text)
        self.spawn_timer.start(1500)  # Spawns a new comment every 1.5 seconds

        # Sample dummy data
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
            "最高！"
        ]

    def spawn_dummy_text(self):
        # Pick random text, random lane (upper half of screen), and random speed
        text = random.choice(self.dummy_comments)
        start_y = random.randint(20, int(self.screen_height * 0.4))
        speed = random.randint(4, 8)

        # Create label and add to tracking list
        new_label = DanmakuLabel(
            text, self, start_x=self.screen_width, start_y=start_y, speed=speed)
        self.active_labels.append(new_label)

    def animate_labels(self):
        # Iterate backwards to safely remove items while looping
        for label in reversed(self.active_labels):
            is_visible = label.update_position()

            # If off-screen, destroy the label to free up memory
            if not is_visible:
                self.active_labels.remove(label)
                label.deleteLater()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OverlayWindow()
    window.show()
    sys.exit(app.exec_())
