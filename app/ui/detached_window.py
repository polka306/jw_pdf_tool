"""탭 분리 시 띄우는 독립 창."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QToolBar

from app.ui.pdf_tab_page import PdfTabPage


class DetachedWindow(QMainWindow):
    """분리된 PdfTabPage를 독립 창으로 표시한다."""

    reattach_requested = pyqtSignal(object)  # PdfTabPage

    def __init__(
        self,
        tab: PdfTabPage,
        tab_widget,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._tab = tab
        self._tab_widget = tab_widget
        self._reattached = False
        self.setWindowTitle(f"{tab.tab_title} — jw_pdf (분리됨)")
        # 탭을 컨테이너에 넣어 직접 소유권 이전을 피한다
        self._setup_central(tab)
        self._setup_toolbar()
        self.resize(900, 700)

    def _setup_central(self, tab: PdfTabPage) -> None:
        """탭을 중앙 위젯으로 설정한다."""
        self.setCentralWidget(tab)

    def _setup_toolbar(self) -> None:
        tb = QToolBar("뷰어", self)
        self.addToolBar(tb)
        act_zoom_in = tb.addAction("줌 +")
        act_zoom_in.triggered.connect(self._tab.viewer.zoom_in)
        act_zoom_out = tb.addAction("줌 -")
        act_zoom_out.triggered.connect(self._tab.viewer.zoom_out)
        act_zoom_fit = tb.addAction("페이지 맞춤")
        act_zoom_fit.triggered.connect(self._tab.viewer.zoom_fit)

    def closeEvent(self, event) -> None:
        if self._reattached:
            event.accept()
            return
        reply = QMessageBox.question(
            self,
            "창 닫기",
            "이 탭을 메인 창으로 되돌리겠습니까?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._reattached = True
            # 창이 닫힐 때 Qt가 탭을 삭제하지 않도록 소유권을 회수한다.
            tab = self.takeCentralWidget()
            tab.setParent(None)  # type: ignore[arg-type]
            self.reattach_requested.emit(tab)
            event.accept()
        elif reply == QMessageBox.StandardButton.No:
            # 소유권 회수 후 정리 (Qt 자동 삭제 전에 cleanup 호출)
            tab = self.takeCentralWidget()
            tab.setParent(None)  # type: ignore[arg-type]
            tab.cleanup()
            event.accept()
        else:
            event.ignore()
