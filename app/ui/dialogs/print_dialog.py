"""인쇄 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class PrintDialog(QDialog):
    """PDF 인쇄 설정 다이얼로그."""

    def __init__(self, parent=None, page_count: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle("인쇄")
        self.setMinimumWidth(400)
        self._page_count = page_count
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._combo_range = QComboBox()
        self._combo_range.addItems(["전체", "현재 페이지", "범위 지정"])
        form.addRow("페이지 범위:", self._combo_range)

        self._edit_range = QLineEdit()
        self._edit_range.setPlaceholderText("예: 1-5, 8, 10-12")
        form.addRow("페이지:", self._edit_range)

        self._spin_copies = QSpinBox()
        self._spin_copies.setRange(1, 99)
        self._spin_copies.setValue(1)
        form.addRow("매수:", self._spin_copies)

        layout.addLayout(form)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def page_range_mode(self) -> str:
        return ["all", "current", "custom"][self._combo_range.currentIndex()]

    def custom_range(self) -> str:
        return self._edit_range.text()

    def copies(self) -> int:
        return self._spin_copies.value()
