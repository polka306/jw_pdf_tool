"""메인 윈도우."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QWidget,
)

from app.core.pdf_document import PdfDocument
from app.ui.page_panel import PagePanel
from app.ui.pdf_viewer import PdfViewer
from app.ui.toolbar import MainToolBar


class MainWindow(QMainWindow):
    """PDF 편집 툴 메인 윈도우."""

    APP_TITLE = "PDF 편집 툴"

    def __init__(self) -> None:
        super().__init__()
        self._doc = PdfDocument()
        self._setup_ui()
        self._connect_signals()
        self.setWindowTitle(self.APP_TITLE)
        self.resize(1200, 800)

    # ------------------------------------------------------------------
    # UI 초기화
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        # 툴바
        self._toolbar = MainToolBar(self)
        self.addToolBar(self._toolbar)

        # 중앙 위젯 — 스플리터로 썸네일 | 뷰어 분리
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        self._page_panel = PagePanel(self._splitter)
        self._viewer = PdfViewer(self._splitter)

        self._splitter.addWidget(self._page_panel)
        self._splitter.addWidget(self._viewer)
        self._splitter.setStretchFactor(0, 0)  # 썸네일: 고정
        self._splitter.setStretchFactor(1, 1)  # 뷰어: 확장

        self.setCentralWidget(self._splitter)

        # 상태바
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._lbl_page = QLabel("페이지: -")
        self._lbl_zoom = QLabel("줌: -")
        self._lbl_file = QLabel("")
        self._status_bar.addWidget(self._lbl_page)
        self._status_bar.addWidget(QLabel("  |  "))
        self._status_bar.addWidget(self._lbl_zoom)
        self._status_bar.addPermanentWidget(self._lbl_file)

        # 메뉴바
        self._setup_menu()

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()

        # 파일 메뉴
        file_menu = menu_bar.addMenu("파일(&F)")
        file_menu.addAction(self._toolbar._act_open)
        file_menu.addAction(self._toolbar._act_save)
        file_menu.addSeparator()
        act_save_as = file_menu.addAction("다른 이름으로 저장(&A)...")
        act_save_as.triggered.connect(self._save_as)
        file_menu.addSeparator()
        act_quit = file_menu.addAction("종료(&Q)")
        act_quit.triggered.connect(self.close)

        # 보기 메뉴
        view_menu = menu_bar.addMenu("보기(&V)")
        view_menu.addAction(self._toolbar._act_zoom_in)
        view_menu.addAction(self._toolbar._act_zoom_out)
        view_menu.addAction(self._toolbar._act_zoom_fit)

    # ------------------------------------------------------------------
    # 시그널 연결
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # 툴바 → 윈도우
        self._toolbar.open_requested.connect(self._open_file)
        self._toolbar.save_requested.connect(self._save_file)
        self._toolbar.zoom_in_requested.connect(self._viewer.zoom_in)
        self._toolbar.zoom_out_requested.connect(self._viewer.zoom_out)
        self._toolbar.zoom_fit_requested.connect(self._viewer.zoom_fit)
        self._toolbar.zoom_value_changed.connect(self._viewer.set_zoom)

        # 뷰어 → 상태바/툴바
        self._viewer.zoom_changed.connect(self._on_zoom_changed)
        self._viewer.page_changed.connect(self._on_page_changed)

        # 썸네일 패널 → 뷰어
        self._page_panel.page_selected.connect(self._on_thumbnail_selected)

    # ------------------------------------------------------------------
    # 파일 작업
    # ------------------------------------------------------------------

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "PDF 파일 열기",
            "",
            "PDF 파일 (*.pdf);;모든 파일 (*)",
        )
        if not path:
            return

        try:
            self._doc.open(path)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일을 열 수 없습니다:\n{e}")
            return

        # UI 업데이트
        self._page_panel.load_document(self._doc)
        self._viewer.set_document(self._doc)
        self._toolbar.set_document_loaded(True)
        self._update_title(path)
        self._update_page_status(0)
        self._toolbar.update_zoom_display(self._viewer.zoom)
        self._lbl_file.setText(os.path.basename(path))

    def _save_file(self) -> None:
        if not self._doc.is_open:
            return
        try:
            self._doc.save()
            self._status_bar.showMessage("저장 완료", 2000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")

    def _save_as(self) -> None:
        if not self._doc.is_open:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "다른 이름으로 저장",
            "",
            "PDF 파일 (*.pdf)",
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            self._doc.save(path)
            self._update_title(path)
            self._lbl_file.setText(os.path.basename(path))
            self._status_bar.showMessage("저장 완료", 2000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")

    # ------------------------------------------------------------------
    # 이벤트 핸들러
    # ------------------------------------------------------------------

    def _on_zoom_changed(self, zoom: float) -> None:
        self._lbl_zoom.setText(f"줌: {round(zoom * 100)}%")
        self._toolbar.update_zoom_display(zoom)

    def _on_page_changed(self, page_idx: int) -> None:
        self._update_page_status(page_idx)
        self._page_panel.set_current_page(page_idx)

    def _on_thumbnail_selected(self, page_idx: int) -> None:
        self._viewer.goto_page(page_idx)

    # ------------------------------------------------------------------
    # 유틸
    # ------------------------------------------------------------------

    def _update_title(self, path: str) -> None:
        self.setWindowTitle(f"{os.path.basename(path)} — {self.APP_TITLE}")

    def _update_page_status(self, page_idx: int) -> None:
        total = self._doc.page_count if self._doc.is_open else 0
        self._lbl_page.setText(f"페이지: {page_idx + 1} / {total}")

    def closeEvent(self, event) -> None:
        self._doc.close()
        event.accept()
