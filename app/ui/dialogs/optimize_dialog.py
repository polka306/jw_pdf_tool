"""PDF 최적화 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)


class OptimizeDialog(QDialog):
    """PDF 최적화 설정 다이얼로그."""

    def __init__(self, parent=None, current_size: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle("PDF 최적화")
        self.setMinimumWidth(350)
        self._current_size = current_size
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        if self._current_size > 0:
            size_mb = self._current_size / (1024 * 1024)
            layout.addWidget(QLabel(f"현재 파일 크기: {size_mb:.1f} MB"))

        form = QFormLayout()
        self._combo_preset = QComboBox()
        self._combo_preset.addItems(["웹 최적화 (작은 크기)", "인쇄 최적화 (높은 품질)", "사용자 정의"])
        form.addRow("프리셋:", self._combo_preset)
        layout.addLayout(form)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def preset(self) -> str:
        idx = self._combo_preset.currentIndex()
        return ["web", "print", "custom"][idx]
