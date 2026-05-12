"""QTabWidget 확장 — 멀티 PDF 탭 컨테이너."""
from __future__ import annotations

from collections import deque

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QTabWidget

from app.ui.pdf_tab_page import PdfTabPage


class PdfTabWidget(QTabWidget):
    """여러 PdfTabPage를 관리하는 탭 컨테이너."""

    active_tab_changed = pyqtSignal(object)  # PdfTabPage | None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self._recent_closed: deque[tuple[str, int, float]] = deque(maxlen=10)
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self._on_current_changed)
        self.tabBar().setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.tabBar().customContextMenuRequested.connect(
            self._show_tab_context_menu
        )

    # ── 공개 API ─────────────────────────────────────────────────────────

    def open_pdf(self, path: str, page: int = 0, zoom: float = 1.0) -> PdfTabPage:
        """새 탭으로 PDF를 연다."""
        tab = PdfTabPage()
        tab.load(path, page, zoom)
        idx = self.addTab(tab, tab.tab_title)
        self.setTabToolTip(idx, path)
        self.setCurrentIndex(idx)
        return tab

    def active_tab(self) -> PdfTabPage | None:
        """현재 활성 탭 반환. 탭이 없으면 None."""
        widget = self.currentWidget()
        return widget if isinstance(widget, PdfTabPage) else None

    def close_tab(self, index: int) -> None:
        """탭을 닫는다. 미저장 변경이 있으면 사용자에게 확인한다."""
        tab = self.widget(index)
        if not isinstance(tab, PdfTabPage):
            return
        if tab.is_modified:
            reply = QMessageBox.question(
                self, "저장 확인",
                f"{tab.tab_title}\n\n변경 사항을 저장하겠습니까?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save:
                tab.doc.save()
        if tab.doc.is_open and tab.path:
            self._recent_closed.append(
                (tab.path, tab.viewer.current_page, tab.viewer.zoom)
            )
        tab.cleanup()
        self.removeTab(index)

    def reopen_last_closed(self) -> None:
        """최근 닫은 탭을 다시 연다."""
        if not self._recent_closed:
            return
        path, page, zoom = self._recent_closed.pop()
        self.open_pdf(path, page, zoom)

    def duplicate_tab(self, index: int) -> None:
        """탭을 복제한다 (같은 경로, 같은 페이지·줌)."""
        tab = self.widget(index)
        if not isinstance(tab, PdfTabPage) or not tab.doc.is_open:
            return
        self.open_pdf(tab.path, tab.viewer.current_page, tab.viewer.zoom)

    def detach_tab(self, index: int) -> None:
        """탭을 독립 창으로 분리한다."""
        from app.ui.detached_window import DetachedWindow
        tab = self.widget(index)
        if not isinstance(tab, PdfTabPage):
            return
        self.removeTab(index)
        win = DetachedWindow(tab, self)
        win.reattach_requested.connect(self._reattach_tab)
        win.show()

    def close_all(self) -> None:
        """모든 탭을 닫는다."""
        for i in range(self.count() - 1, -1, -1):
            self.close_tab(i)

    # ── 내부 슬롯 ────────────────────────────────────────────────────────

    def _on_tab_close_requested(self, index: int) -> None:
        self.close_tab(index)

    def _on_current_changed(self, index: int) -> None:
        self.active_tab_changed.emit(self.active_tab())

    def _reattach_tab(self, tab: PdfTabPage) -> None:
        idx = self.addTab(tab, tab.tab_title)
        if tab.doc.is_open and tab.path:
            self.setTabToolTip(idx, tab.path)
        self.setCurrentIndex(idx)

    def _show_tab_context_menu(self, pos) -> None:
        from PyQt6.QtWidgets import QApplication, QMenu
        index = self.tabBar().tabAt(pos)
        if index < 0:
            return
        menu = QMenu(self)
        menu.addAction("닫기").triggered.connect(
            lambda: self.close_tab(index)
        )
        menu.addAction("다른 탭 모두 닫기").triggered.connect(
            lambda: self._close_others(index)
        )
        menu.addAction("오른쪽 탭 모두 닫기").triggered.connect(
            lambda: self._close_right(index)
        )
        menu.addSeparator()
        menu.addAction("복제").triggered.connect(
            lambda: self.duplicate_tab(index)
        )
        menu.addAction("새 창으로 열기").triggered.connect(
            lambda: self.detach_tab(index)
        )
        tab = self.widget(index)
        if isinstance(tab, PdfTabPage) and tab.doc.is_open and tab.path:
            menu.addSeparator()
            menu.addAction("파일 경로 복사").triggered.connect(
                lambda: QApplication.clipboard().setText(tab.path)
            )
        menu.exec(self.tabBar().mapToGlobal(pos))

    def _close_others(self, keep_index: int) -> None:
        for i in range(self.count() - 1, -1, -1):
            if i != keep_index:
                self.close_tab(i)

    def _close_right(self, from_index: int) -> None:
        for i in range(self.count() - 1, from_index, -1):
            self.close_tab(i)
