"""검색/바꾸기 바 위젯."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class SearchBar(QWidget):
    """PDF 텍스트 검색바.

    Signals
    -------
    search_requested(text: str)
        검색어 입력 시.
    next_requested()
        다음 매칭으로 이동.
    prev_requested()
        이전 매칭으로 이동.
    closed()
        검색바 닫힘.
    """

    search_requested = pyqtSignal(str)
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._connect()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self._input = QLineEdit()
        self._input.setPlaceholderText("검색...")
        layout.addWidget(self._input)

        self._result_label = QLabel("0 / 0")
        self._result_label.setMinimumWidth(60)
        layout.addWidget(self._result_label)

        self._btn_prev = QPushButton("◀")
        self._btn_prev.setFixedWidth(30)
        layout.addWidget(self._btn_prev)

        self._btn_next = QPushButton("▶")
        self._btn_next.setFixedWidth(30)
        layout.addWidget(self._btn_next)

        self._chk_case = QCheckBox("Aa")
        self._chk_case.setToolTip("대소문자 구분")
        layout.addWidget(self._chk_case)

        self._chk_whole = QCheckBox("W")
        self._chk_whole.setToolTip("전체 단어")
        layout.addWidget(self._chk_whole)

        self._chk_regex = QCheckBox(".*")
        self._chk_regex.setToolTip("정규식")
        layout.addWidget(self._chk_regex)

        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedWidth(30)
        layout.addWidget(self._btn_close)

    def _connect(self) -> None:
        self._input.returnPressed.connect(lambda: self.search_requested.emit(self._input.text()))
        self._btn_next.clicked.connect(self.next_requested.emit)
        self._btn_prev.clicked.connect(self.prev_requested.emit)
        self._btn_close.clicked.connect(self.close_bar)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def search_text(self) -> str:
        return self._input.text()

    def set_result_count(self, total: int, current_idx: int) -> None:
        """결과 표시 업데이트."""
        if total == 0:
            self._result_label.setText("0 / 0")
        else:
            self._result_label.setText(f"{current_idx + 1} / {total}")

    def is_case_sensitive(self) -> bool:
        return self._chk_case.isChecked()

    def is_whole_word(self) -> bool:
        return self._chk_whole.isChecked()

    def is_regex(self) -> bool:
        return self._chk_regex.isChecked()

    def close_bar(self) -> None:
        """검색바 숨기기."""
        self.hide()
        self.closed.emit()

    def focus_input(self) -> None:
        """입력 필드에 포커스."""
        self._input.setFocus()
        self._input.selectAll()
