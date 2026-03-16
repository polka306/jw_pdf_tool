"""메인 윈도우."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
)

from app.__version__ import __version__
from app.core import page_editor
from app.core.annotator import AnnotationStyle, AnnotationTool
from app.core.command_manager import (
    AddAnnotationCommand,
    CommandManager,
    DeletePagesCommand,
    InsertPagesCommand,
    MovePageCommand,
)
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
        self._cmd_mgr = CommandManager()
        self._setup_ui()
        self._connect_signals()
        self.setWindowTitle(f"{self.APP_TITLE} v{__version__}")
        self.resize(1200, 800)

    # ── UI 초기화 ─────────────────────────────────────────────────────────────

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
        self._lbl_tool = QLabel("도구: 선택")
        self._lbl_file = QLabel("")
        self._status_bar.addWidget(self._lbl_page)
        self._status_bar.addWidget(QLabel("  |  "))
        self._status_bar.addWidget(self._lbl_zoom)
        self._status_bar.addWidget(QLabel("  |  "))
        self._status_bar.addWidget(self._lbl_tool)
        self._status_bar.addPermanentWidget(self._lbl_file)

        self._setup_menu()

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()

        # ── 파일 ──────────────────────────────────────────────────────────────
        file_menu = menu_bar.addMenu("파일(&F)")
        file_menu.addAction(self._toolbar._act_open)
        file_menu.addAction(self._toolbar._act_save)
        file_menu.addSeparator()
        act_save_as = file_menu.addAction("다른 이름으로 저장(&A)...")
        act_save_as.triggered.connect(self._save_as)
        file_menu.addSeparator()
        act_quit = file_menu.addAction("종료(&Q)")
        act_quit.triggered.connect(self.close)

        # ── 편집 ──────────────────────────────────────────────────────────────
        edit_menu = menu_bar.addMenu("편집(&E)")

        self._act_undo = QAction("실행 취소(&Z)", self)
        self._act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self._act_undo.setEnabled(False)
        self._act_undo.triggered.connect(self._undo)
        edit_menu.addAction(self._act_undo)

        self._act_redo = QAction("다시 실행(&Y)", self)
        self._act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self._act_redo.setEnabled(False)
        self._act_redo.triggered.connect(self._redo)
        edit_menu.addAction(self._act_redo)

        edit_menu.addSeparator()
        edit_menu.addAction(self._toolbar._act_delete)
        edit_menu.addAction(self._toolbar._act_extract)
        edit_menu.addAction(self._toolbar._act_insert)

        # ── 보기 ──────────────────────────────────────────────────────────────
        view_menu = menu_bar.addMenu("보기(&V)")
        view_menu.addAction(self._toolbar._act_zoom_in)
        view_menu.addAction(self._toolbar._act_zoom_out)
        view_menu.addAction(self._toolbar._act_zoom_fit)
        view_menu.addSeparator()

        act_prev = QAction("이전 페이지(&[)", self)
        act_prev.setShortcut(QKeySequence("PgUp"))
        act_prev.triggered.connect(lambda: self._viewer.goto_page(self._viewer.current_page - 1))
        view_menu.addAction(act_prev)

        act_next = QAction("다음 페이지(&])", self)
        act_next.setShortcut(QKeySequence("PgDown"))
        act_next.triggered.connect(lambda: self._viewer.goto_page(self._viewer.current_page + 1))
        view_menu.addAction(act_next)

        # ── 어노테이션 ────────────────────────────────────────────────────────
        annot_menu = menu_bar.addMenu("어노테이션(&A)")
        for tool, act in self._toolbar._tool_actions.items():
            annot_menu.addAction(act)

        # ── 도구 ──────────────────────────────────────────────────────────────
        tools_menu = menu_bar.addMenu("도구(&T)")
        act_convert = tools_menu.addAction("변환...(&C)")
        act_convert.setShortcut("Ctrl+Shift+C")
        act_convert.triggered.connect(self._open_convert_dialog)

        # ── 도움말 ────────────────────────────────────────────────────────────
        help_menu = menu_bar.addMenu("도움말(&H)")
        act_about = help_menu.addAction("정보(&A)...")
        act_about.triggered.connect(self._show_about)

    # ── 시그널 연결 ───────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        # 파일
        self._toolbar.open_requested.connect(self._open_file)
        self._toolbar.save_requested.connect(self._save_file)

        # 줌
        self._toolbar.zoom_in_requested.connect(self._viewer.zoom_in)
        self._toolbar.zoom_out_requested.connect(self._viewer.zoom_out)
        self._toolbar.zoom_fit_requested.connect(self._viewer.zoom_fit)
        self._toolbar.zoom_value_changed.connect(self._viewer.set_zoom)
        self._viewer.zoom_changed.connect(self._on_zoom_changed)

        # 페이지 편집
        self._toolbar.delete_page_requested.connect(self._delete_selected_pages)
        self._toolbar.extract_page_requested.connect(self._extract_selected_pages)
        self._toolbar.insert_page_requested.connect(self._insert_pages_at_current)
        self._page_panel.page_selected.connect(self._on_thumbnail_selected)
        self._page_panel.page_moved.connect(self._on_page_moved)
        self._page_panel.delete_requested.connect(self._delete_pages)
        self._page_panel.extract_requested.connect(self._extract_pages)
        self._page_panel.insert_requested.connect(self._insert_pages)
        self._viewer.page_changed.connect(self._on_page_changed)

        # 어노테이션
        self._toolbar.tool_changed.connect(self._on_tool_changed)
        self._toolbar.color_changed.connect(self._on_color_changed)
        self._toolbar.width_changed.connect(self._on_width_changed)
        self._viewer.annotation_requested.connect(self._on_annotation_requested)

        # 변환
        self._toolbar.convert_requested.connect(self._open_convert_dialog)

    # ── 파일 작업 ─────────────────────────────────────────────────────────────

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

        self._cmd_mgr.clear()
        self._page_panel.load_document(self._doc)
        self._viewer.set_document(self._doc)
        self._toolbar.set_document_loaded(True)
        self._toolbar.set_tool_checked(AnnotationTool.SELECT)
        self._update_title(path)
        self._update_page_status(0)
        self._toolbar.update_zoom_display(self._viewer.zoom)
        self._lbl_file.setText(os.path.basename(path))
        self._update_undo_actions()
        # 초기 어노테이션 스타일 동기화
        self._sync_annot_style()

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

    # ── 페이지 편집 ───────────────────────────────────────────────────────────

    def _on_page_moved(self, from_idx: int, to_idx: int) -> None:
        if not self._doc.is_open:
            return
        cmd = MovePageCommand(self._doc.raw, from_idx, to_idx)
        self._cmd_mgr.execute(cmd)
        self._refresh_after_edit()
        self._viewer.goto_page(min(to_idx, self._doc.page_count - 1))
        self._status_bar.showMessage(f"페이지 {from_idx + 1} → {to_idx + 1} 이동", 2000)
        self._update_undo_actions()

    def _delete_selected_pages(self) -> None:
        self._delete_pages(self._page_panel.selected_indices())

    def _delete_pages(self, indices: list[int]) -> None:
        if not indices or not self._doc.is_open:
            return
        if self._doc.page_count <= len(indices):
            QMessageBox.warning(self, "삭제 불가", "모든 페이지를 삭제할 수 없습니다.")
            return
        page_nums = ", ".join(str(i + 1) for i in sorted(indices))
        reply = QMessageBox.question(
            self, "페이지 삭제", f"페이지 {page_nums}을(를) 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        cmd = DeletePagesCommand(self._doc.raw, indices)
        self._cmd_mgr.execute(cmd)
        self._refresh_after_edit()
        self._status_bar.showMessage(f"{len(indices)}개 페이지 삭제됨", 2000)
        self._update_undo_actions()

    def _extract_selected_pages(self) -> None:
        self._extract_pages(self._page_panel.selected_indices())

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
                f"{len(indices)}개 페이지 추출 → {os.path.basename(path)}", 3000
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"추출 실패:\n{e}")

    def _insert_pages_at_current(self) -> None:
        self._insert_pages(self._viewer.current_page + 1)

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
            cmd = InsertPagesCommand(self._doc.raw, source_path, source_indices, insert_before)
            self._cmd_mgr.execute(cmd)
            self._refresh_after_edit()
            self._status_bar.showMessage(f"{len(source_indices)}개 페이지 삽입 완료", 3000)
            self._update_undo_actions()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"삽입 실패:\n{e}")

    def _refresh_after_edit(self) -> None:
        current = self._viewer.current_page
        self._page_panel.reload_all()
        target = min(current, self._doc.page_count - 1)
        self._viewer.goto_page(max(0, target))
        self._update_page_status(self._viewer.current_page)

    # ── 어노테이션 ───────────────────────────────────────────────────────────

    def _on_tool_changed(self, tool: AnnotationTool) -> None:
        self._viewer.set_tool(tool)
        tool_names = {
            AnnotationTool.SELECT:  "선택",
            AnnotationTool.TEXT:    "텍스트",
            AnnotationTool.RECT:    "사각형",
            AnnotationTool.ELLIPSE: "타원",
            AnnotationTool.LINE:    "선",
        }
        self._lbl_tool.setText(f"도구: {tool_names.get(tool, '')}")

    def _on_color_changed(self, rgb: tuple) -> None:
        style = self._viewer.annotation_style
        style.color = rgb
        self._viewer.set_annotation_style(style)

    def _on_width_changed(self, width: float) -> None:
        style = self._viewer.annotation_style
        style.line_width = width
        self._viewer.set_annotation_style(style)

    def _on_annotation_requested(self, annotate_fn, description: str) -> None:
        """PdfViewer에서 어노테이션 요청 시 커맨드로 래핑해 실행합니다."""
        cmd = AddAnnotationCommand(
            self._doc.raw, self._viewer.current_page, annotate_fn, description
        )
        self._cmd_mgr.execute(cmd)
        self._viewer.refresh_page()
        self._page_panel.reload_page(self._viewer.current_page)
        self._status_bar.showMessage(f"{description} — Ctrl+Z로 취소 가능", 3000)
        self._viewer.annotation_added.emit()  # 호환용
        self._update_undo_actions()

    # ── Undo / Redo ───────────────────────────────────────────────────────────

    def _undo(self) -> None:
        desc = self._cmd_mgr.undo()
        if desc is None:
            return
        self._full_undo_redo_refresh()
        self._status_bar.showMessage(f"실행 취소: {desc}", 2000)
        self._update_undo_actions()

    def _redo(self) -> None:
        desc = self._cmd_mgr.redo()
        if desc is None:
            return
        self._full_undo_redo_refresh()
        self._status_bar.showMessage(f"다시 실행: {desc}", 2000)
        self._update_undo_actions()

    def _full_undo_redo_refresh(self) -> None:
        """Undo/Redo 후 UI 전체 갱신."""
        self._refresh_after_edit()
        self._viewer.refresh_page()

    def _update_undo_actions(self) -> None:
        """Undo/Redo 액션 활성화 상태와 텍스트를 갱신합니다."""
        can_undo = self._cmd_mgr.can_undo
        can_redo = self._cmd_mgr.can_redo
        self._act_undo.setEnabled(can_undo)
        self._act_redo.setEnabled(can_redo)
        u_desc = self._cmd_mgr.undo_description
        r_desc = self._cmd_mgr.redo_description
        self._act_undo.setText(f"실행 취소: {u_desc}(&Z)" if u_desc else "실행 취소(&Z)")
        self._act_redo.setText(f"다시 실행: {r_desc}(&Y)" if r_desc else "다시 실행(&Y)")

    # ── 변환 ─────────────────────────────────────────────────────────────────

    def _open_convert_dialog(self) -> None:
        from app.ui.dialogs.convert_dialog import ConvertDialog
        dlg = ConvertDialog(self)
        dlg.conversion_done.connect(self._open_converted_pdf)
        dlg.exec()

    def _open_converted_pdf(self, output_paths: list) -> None:
        """변환 완료 후 결과 PDF를 뷰어에서 엽니다."""
        if not output_paths:
            return
        path = output_paths[0]
        try:
            self._doc.open(path)
        except Exception as exc:
            QMessageBox.critical(self, "오류", f"변환된 파일을 열 수 없습니다:\n{exc}")
            return
        self._cmd_mgr.clear()
        self._page_panel.load_document(self._doc)
        self._viewer.set_document(self._doc)
        self._toolbar.set_document_loaded(True)
        self._toolbar.set_tool_checked(AnnotationTool.SELECT)
        self._update_title(path)
        self._update_page_status(0)
        self._toolbar.update_zoom_display(self._viewer.zoom)
        self._lbl_file.setText(os.path.basename(path))
        self._update_undo_actions()
        self._sync_annot_style()

    def _sync_annot_style(self) -> None:
        """툴바의 현재 색상/굵기를 뷰어 스타일에 동기화합니다."""
        style = AnnotationStyle(
            color=self._toolbar.current_annot_color,
            line_width=self._toolbar.current_annot_width,
        )
        self._viewer.set_annotation_style(style)

    # ── 이벤트 핸들러 ─────────────────────────────────────────────────────────

    def _on_zoom_changed(self, zoom: float) -> None:
        self._lbl_zoom.setText(f"줌: {round(zoom * 100)}%")
        self._toolbar.update_zoom_display(zoom)

    def _on_page_changed(self, page_idx: int) -> None:
        self._update_page_status(page_idx)
        self._page_panel.set_current_page(page_idx)

    def _on_thumbnail_selected(self, page_idx: int) -> None:
        self._viewer.goto_page(page_idx)

    # ── 유틸 ─────────────────────────────────────────────────────────────────

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            f"{self.APP_TITLE} 정보",
            f"<b>{self.APP_TITLE}</b> v{__version__}<br><br>"
            f"Python + PyQt6 기반 개인용 PDF 편집 애플리케이션<br><br>"
            f"<b>기술 스택:</b><br>"
            f"&nbsp; PyMuPDF (fitz) — PDF 렌더링/어노테이션<br>"
            f"&nbsp; PyQt6 — GUI 프레임워크<br>"
            f"&nbsp; pikepdf — PDF 페이지 편집<br>"
            f"&nbsp; Pillow — 이미지 처리",
        )

    def _update_title(self, path: str) -> None:
        self.setWindowTitle(f"{os.path.basename(path)} — {self.APP_TITLE} v{__version__}")

    def _update_page_status(self, page_idx: int) -> None:
        total = self._doc.page_count if self._doc.is_open else 0
        self._lbl_page.setText(f"페이지: {page_idx + 1} / {total}")

    def closeEvent(self, event) -> None:
        self._doc.close()
        event.accept()
