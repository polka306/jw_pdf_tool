"""PDF 분할 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)


class SplitDialog(QDialog):
    """PDF 분할 설정 다이얼로그."""

    def __init__(self, parent=None, page_count: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle("PDF 분할")
        self.setMinimumWidth(400)
        self._page_count = page_count
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"전체 페이지: {self._page_count}"))

        self._radio_count = QRadioButton("N페이지마다 분할")
        self._radio_count.setChecked(True)
        layout.addWidget(self._radio_count)

        count_row = QHBoxLayout()
        count_row.addSpacing(20)
        self._spin_count = QSpinBox()
        self._spin_count.setRange(1, max(self._page_count, 1))
        self._spin_count.setValue(1)
        count_row.addWidget(QLabel("페이지 수:"))
        count_row.addWidget(self._spin_count)
        count_row.addStretch()
        layout.addLayout(count_row)

        self._radio_bookmark = QRadioButton("북마크 기준 분할")
        layout.addWidget(self._radio_bookmark)

        self._group = QButtonGroup(self)
        self._group.addButton(self._radio_count)
        self._group.addButton(self._radio_bookmark)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def split_mode(self) -> str:
        if self._radio_bookmark.isChecked():
            return "bookmark"
        return "count"

    def pages_per_split(self) -> int:
        return self._spin_count.value()
