"""앱 설정 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    """앱 설정 다이얼로그."""

    def __init__(self, parent=None, settings=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setMinimumWidth(400)
        self._settings = settings
        self._setup_ui()
        self._load_current()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 일반
        general = QGroupBox("일반")
        g_layout = QFormLayout(general)

        self._combo_theme = QComboBox()
        self._combo_theme.addItems(["다크", "라이트"])
        g_layout.addRow("테마:", self._combo_theme)

        self._chk_tray = QCheckBox("시스템 트레이 상주")
        g_layout.addRow(self._chk_tray)

        self._chk_default_viewer = QCheckBox("기본 PDF 뷰어로 등록")
        g_layout.addRow(self._chk_default_viewer)

        layout.addWidget(general)

        # 파일
        file_group = QGroupBox("파일")
        f_layout = QFormLayout(file_group)

        self._spin_recent = QSpinBox()
        self._spin_recent.setRange(0, 20)
        self._spin_recent.setValue(10)
        f_layout.addRow("최근 파일 수:", self._spin_recent)

        layout.addWidget(file_group)

        # 버튼
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._save_and_accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _load_current(self) -> None:
        if self._settings is None:
            return
        theme = self._settings.get("theme", "dark")
        self._combo_theme.setCurrentIndex(0 if theme == "dark" else 1)
        self._chk_tray.setChecked(bool(self._settings.get("tray_enabled", False)))

    def _save_and_accept(self) -> None:
        if self._settings:
            self._settings.set("theme", self.theme())
            self._settings.set("tray_enabled", self._chk_tray.isChecked())
            self._settings.set("max_recent", self._spin_recent.value())
        self.accept()

    def theme(self) -> str:
        return "dark" if self._combo_theme.currentIndex() == 0 else "light"

    def tray_enabled(self) -> bool:
        return self._chk_tray.isChecked()
