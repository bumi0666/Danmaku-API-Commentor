from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from danmaku.models import AppSettings


class SettingsWindow(QWidget):
    """Minimal control window for the MVP."""

    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings

        self.setWindowTitle("Danmaku AI Settings")
        self.setMinimumWidth(420)

        self.status_label = QLabel("Status: stopped")

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("GEMINI_API_KEY")
        self.api_key_input.setText(settings.api_key)

        self.model_input = QLineEdit()
        self.model_input.setText(settings.model_name)

        self.dummy_checkbox = QCheckBox("Use dummy API responses")
        self.dummy_checkbox.setChecked(settings.use_dummy_api)

        self.interval_input = QSpinBox()
        self.interval_input.setRange(2, 60)
        self.interval_input.setValue(settings.capture_interval_seconds)
        self.interval_input.setSuffix(" sec")

        self.font_size_input = QSpinBox()
        self.font_size_input.setRange(12, 96)
        self.font_size_input.setValue(settings.font_size)

        form = QFormLayout()
        form.addRow("Gemini API key", self.api_key_input)
        form.addRow("Model", self.model_input)
        form.addRow("Capture interval", self.interval_input)
        form.addRow("Overlay font size", self.font_size_input)
        form.addRow("", self.dummy_checkbox)

        group = QGroupBox("Runtime settings")
        group.setLayout(form)

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")

        button_row = QHBoxLayout()
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)

        layout = QVBoxLayout()
        layout.addWidget(group)
        layout.addWidget(self.status_label)
        layout.addLayout(button_row)
        self.setLayout(layout)

        self.start_button.clicked.connect(self._on_start_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)

    def apply_to_settings(self) -> None:
        self.settings.api_key = self.api_key_input.text().strip()
        self.settings.model_name = self.model_input.text().strip()
        self.settings.use_dummy_api = self.dummy_checkbox.isChecked()
        self.settings.capture_interval_seconds = self.interval_input.value()
        self.settings.font_size = self.font_size_input.value()

    def set_running(self, is_running: bool) -> None:
        self.status_label.setText("Status: running" if is_running else "Status: stopped")

    def _on_start_clicked(self) -> None:
        self.apply_to_settings()
        self.set_running(True)
        self.start_requested.emit()

    def _on_stop_clicked(self) -> None:
        self.set_running(False)
        self.stop_requested.emit()


def main() -> None:
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = SettingsWindow(AppSettings())
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
