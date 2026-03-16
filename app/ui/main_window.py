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

from app.core import page_editor
from app.core.pdf_document import PdfDocument
from app.ui.dialogs.insert_dialog import InsertDialog
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
        self._toolbar = MainToolBar(self)
        self.addToolBar(self._toolbar)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._page_panel = PagePanel(self._splitter)
        self._viewer = PdfViewer(self._splitter)
        self._splitter.addWidget(self._page_panel)
        self._splitter.addWidget(self._viewer)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self.setCentralWidget(self._splitter)

        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._lbl_page = QLabel("페이지: -")
        self._lbl_zoom = QLabel("줌: -")
        self._lbl_file = QLabel("")
        self._status_bar.addWidget(self._lbl_page)
        self._status_bar.addWidget(QLabel("  |  "))
        self._status_bar.addWidget(self._lbl_zoom)
        self._status_bar.addPermanentWidget(self._lbl_file)

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

        # 편집 메뉴
        edit_menu = menu_bar.addMenu("편집(&E)")
        edit_menu.addAction(self._toolbar._act_delete)
        edit_menu.addAction(self._toolbar._act_extract)
        edit_menu.addAction(self._toolbar._act_insert)

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
        self._toolbar.delete_page_requested.connect(self._delete_selected_pages)
        self._toolbar.extract_page_requested.connect(self._extract_selected_pages)
        self._toolbar.insert_page_requested.connect(self._insert_pages_at_current)

        # 뷰어 → 상태바/툴바
        self._viewer.zoom_changed.connect(self._on_zoom_changed)
        self._viewer.page_changed.connect(self._on_page_changed)

        # 썸네일 패널 → 뷰어 / 페이지 편집
        self._page_panel.page_selected.connect(self._on_thumbnail_selected)
        self._page_panel.page_moved.connect(self._on_page_moved)
        self._page_panel.delete_requested.connect(self._delete_pages)
        self._page_panel.extract_requested.connect(self._extract_pages)
        self._page_panel.insert_requested.connect(self._insert_pages)

    # ------------------------------------------------------------------
    # 파일 작업
    # ------------------------------------------------------------------

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "PDF 파일 열기", "", "PDF 파일 (*.pdf);;모든 파일 (*)"
        )
        if not path:
            return
        try:
            self._doc.open(path)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일을 열 수 없습니다:\n{e}")
            return

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
            self, "다른 이름으로 저장", "", "PDF 파일 (*.pdf)"
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
    # 페이지 편집
    # ------------------------------------------------------------------

    def _on_page_moved(self, from_idx: int, to_idx: int) -> None:
        """썸네일 드래그앤드롭으로 페이지 순서 변경."""
        if not self._doc.is_open:
            return
        page_editor.move_page(self._doc.raw, from_idx, to_idx)
        # 썸네일은 QListWidget이 이미 시각적으로 이동시킴 — 번호만 갱신
        self._page_panel.reload_all()
        self._viewer.goto_page(to_idx)
        self._status_bar.showMessage(
            f"페이지 {from_idx + 1} → {to_idx + 1} 이동", 2000
        )

    def _delete_selected_pages(self) -> None:
        indices = self._page_panel.selected_indices()
        self._delete_pages(indices)

    def _delete_pages(self, indices: list[int]) -> None:
        if not indices or not self._doc.is_open:
            return
        if self._doc.page_count <= len(indices):
            QMessageBox.warning(self, "삭제 불가", "모든 페이지를 삭제할 수 없습니다.")
            return

        page_nums = ", ".join(str(i + 1) for i in sorted(indices))
        reply = QMessageBox.question(
            self,
            "페이지 삭제",
            f"페이지 {page_nums}을(를) 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        page_editor.delete_pages(self._doc.raw, indices)
        self._refresh_after_edit()
        self._status_bar.showMessage(f"{len(indices)}개 페이지 삭제됨", 2000)

    def _extract_selected_pages(self) -> None:
        indices = self._page_panel.selected_indices()
        self._extract_pages(indices)

    def _extract_pages(self, indices: list[int]) -> None:
        if not indices or not self._doc.is_open:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "페이지 추출 — 저장 위치 선택", "", "PDF 파일 (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            page_editor.extract_pages(self._doc.raw, indices, path)
            self._status_bar.showMessage(
                f"{len(indices)}개 페이지 추출 완료 → {os.path.basename(path)}", 3000
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"추출 실패:\n{e}")

    def _insert_pages_at_current(self) -> None:
        """툴바 버튼: 현재 페이지 뒤에 삽입."""
        insert_at = self._viewer.current_page + 1
        self._insert_pages(insert_at)

    def _insert_pages(self, insert_before: int) -> None:
        if not self._doc.is_open:
            return

        dlg = InsertDialog(self)
        if dlg.exec() != InsertDialog.DialogCode.Accepted:
            return

        source_path = dlg.source_path()
        source_indices = dlg.selected_indices()
        if not source_path or not source_indices:
            return

        try:
            page_editor.insert_pages_from_file(
                self._doc.raw, source_path, source_indices, insert_before
            )
            self._refresh_after_edit()
            self._status_bar.showMessage(
                f"{len(source_indices)}개 페이지 삽입 완료 (위치: {insert_before + 1}페이지 앞)",
                3000,
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"삽입 실패:\n{e}")

    # ------------------------------------------------------------------
    # 편집 후 UI 갱신
    # ------------------------------------------------------------------

    def _refresh_after_edit(self) -> None:
        """페이지 편집 후 썸네일과 뷰어를 갱신합니다."""
        current = self._viewer.current_page
        self._page_panel.reload_all()
        # 현재 페이지가 범위를 벗어나면 마지막 페이지로
        target = min(current, self._doc.page_count - 1)
        self._viewer.goto_page(max(0, target))
        self._update_page_status(self._viewer.current_page)

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
