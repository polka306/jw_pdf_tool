"""탭 하나의 독립적인 PDF 뷰어 유닛."""
from __future__ import annotations

import os

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.core.command_manager import CommandManager
from app.core.pdf_document import PdfDocument
from app.ui.pdf_viewer import PdfViewer


class PdfTabPage(QWidget):
    """탭 하나 = 독립적인 PdfDocument + PdfViewer + CommandManager."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.doc = PdfDocument()
        self.cmd_mgr = CommandManager()
        self.viewer = PdfViewer()
        self.search_query: str = ""
        self.search_results: list = []
        self.search_idx: int = -1
        self._setup_layout()

    def _setup_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.viewer)

    @property
    def path(self) -> str | None:
        return self.doc.path

    @property
    def is_modified(self) -> bool:
        return self.cmd_mgr.can_undo

    @property
    def tab_title(self) -> str:
        if not self.doc.is_open or not self.doc.path:
            return "새 탭"
        name = os.path.basename(self.doc.path)
        return f"● {name}" if self.is_modified else name

    def load(self, path: str, page: int = 0, zoom: float = 1.0) -> None:
        """PDF 파일을 열고 지정 페이지·줌으로 초기화한다."""
        self.viewer.clear()  # 기존 렌더 엔진 스레드 종료
        self.doc.open(path)
        self.viewer.set_document(self.doc)
        self.cmd_mgr.clear()
        if page > 0:
            self.viewer.goto_page(page)
        if zoom != 1.0:
            self.viewer.set_zoom(zoom)

    def cleanup(self) -> None:
        """리소스를 해제한다. 탭 닫기 전에 호출해야 한다."""
        try:
            self.viewer.clear()  # 렌더 엔진 스레드 종료
        except RuntimeError:
            # Qt C++ 객체가 이미 삭제된 경우 (DetachedWindow 등에서 소유권 이전 후)
            pass
        self.doc.close()
