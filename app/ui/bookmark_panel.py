"""북마크(아웃라인) 트리 패널."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from app.core.search_engine import Bookmark, parse_bookmarks


class BookmarkPanel(QWidget):
    """PDF 북마크를 트리 구조로 표시하는 패널.

    Signals
    -------
    page_requested(page_idx: int)
        북마크 클릭 시 해당 페이지로 이동 요청.
    """

    page_requested = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemClicked.connect(self._on_item_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)

        self._bookmarks: list[Bookmark] = []

    def load_bookmarks(self, pdf_path: str) -> None:
        """PDF에서 북마크를 로드하여 트리에 표시."""
        self._tree.clear()
        self._bookmarks = parse_bookmarks(pdf_path)
        self._populate_tree(self._bookmarks, None)

    def clear(self) -> None:
        """트리 초기화."""
        self._tree.clear()
        self._bookmarks = []

    def _populate_tree(
        self,
        bookmarks: list[Bookmark],
        parent: QTreeWidgetItem | None,
    ) -> None:
        """북마크 목록을 트리 위젯에 재귀적으로 추가."""
        for bm in bookmarks:
            if parent is None:
                item = QTreeWidgetItem(self._tree)
            else:
                item = QTreeWidgetItem(parent)

            item.setText(0, bm.title)
            item.setData(0, 100, bm.page_idx)  # role=100에 페이지 번호 저장

            if bm.children:
                self._populate_tree(bm.children, item)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """트리 항목 클릭 시 페이지 이동 시그널 발생."""
        page_idx = item.data(0, 100)
        if page_idx is not None:
            self.page_requested.emit(page_idx)
