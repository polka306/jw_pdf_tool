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
    DeletePagesCommand,
    InsertPagesCommand,
    MovePageCommand,
)
from app.ui.dialogs.insert_dialog import InsertDialog
from app.ui.page_panel import PagePanel
from app.ui.pdf_tab_page import PdfTabPage
from app.ui.pdf_tab_widget import PdfTabWidget
from app.ui.toolbar import MainToolBar


class MainWindow(QMainWindow):
    """jw_pdf 메인 윈도우."""

    APP_TITLE = "jw_pdf"

    def __init__(self) -> None:
        super().__init__()
        self._is_fullscreen = False
        self._recent_menu = None
        self._search_bar = None
        self._bookmark_panel = None
        self._prev_tab: PdfTabPage | None = None
        self._setup_ui()
        self._connect_signals()
        self.setWindowTitle(f"{self.APP_TITLE} v{__version__}")
        self.resize(1200, 800)
        self.setAcceptDrops(True)

    # ── UI 초기화 ─────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

        self._toolbar = MainToolBar(self)
        self.addToolBar(self._toolbar)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # 좌측: 썸네일 + 북마크 탭
        self._side_tabs = QTabWidget()
        self._page_panel = PagePanel()
        self._side_tabs.addTab(self._page_panel, "썸네일")

        try:
            from app.ui.bookmark_panel import BookmarkPanel
            self._bookmark_panel = BookmarkPanel()
            self._side_tabs.addTab(self._bookmark_panel, "북마크")
        except ImportError:
            pass

        self._splitter.addWidget(self._side_tabs)

        # 우측: 검색바 + PDF 탭 위젯
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        try:
            from app.ui.search_bar import SearchBar
            self._search_bar = SearchBar()
            self._search_bar.hide()
            right_layout.addWidget(self._search_bar)
        except ImportError:
            pass

        self._tab_widget = PdfTabWidget()
        right_layout.addWidget(self._tab_widget)

        self._splitter.addWidget(right_widget)
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
        act_close_tab = file_menu.addAction("탭 닫기(&W)")
        act_close_tab.setShortcut(QKeySequence("Ctrl+W"))
        act_close_tab.triggered.connect(
            lambda: self._tab_widget.close_tab(self._tab_widget.currentIndex())
            if self._tab_widget.currentIndex() >= 0 else None
        )
        act_reopen = file_menu.addAction("마지막 탭 다시 열기(&T)")
        act_reopen.setShortcut(QKeySequence("Ctrl+Shift+T"))
        act_reopen.triggered.connect(self._tab_widget.reopen_last_closed)
        file_menu.addSeparator()

        # 최근 파일
        self._recent_menu = file_menu.addMenu("최근 파일(&R)")
        self._update_recent_menu()

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

        # ── 편집 추가: 검색 ──────────────────────────────────────────────────
        edit_menu.addSeparator()
        act_search = QAction("검색(&F)...", self)
        act_search.setShortcut(QKeySequence("Ctrl+F"))
        act_search.triggered.connect(self._toggle_search_bar)
        edit_menu.addAction(act_search)

        # ── 편집 추가: 탭 복제 / 분리 ────────────────────────────────────────
        edit_menu.addSeparator()
        act_dup = QAction("탭 복제(&D)", self)
        act_dup.setShortcut(QKeySequence("Ctrl+Shift+D"))
        act_dup.triggered.connect(
            lambda: self._tab_widget.duplicate_tab(self._tab_widget.currentIndex())
            if self._tab_widget.currentIndex() >= 0 else None
        )
        edit_menu.addAction(act_dup)

        act_detach = QAction("새 창으로 분리(&N)", self)
        act_detach.setShortcut(QKeySequence("Ctrl+Shift+N"))
        act_detach.triggered.connect(
            lambda: self._tab_widget.detach_tab(self._tab_widget.currentIndex())
            if self._tab_widget.currentIndex() >= 0 else None
        )
        edit_menu.addAction(act_detach)

        # ── 보기 ──────────────────────────────────────────────────────────────
        view_menu = menu_bar.addMenu("보기(&V)")
        view_menu.addAction(self._toolbar._act_zoom_in)
        view_menu.addAction(self._toolbar._act_zoom_out)
        view_menu.addAction(self._toolbar._act_zoom_fit)
        view_menu.addSeparator()

        act_prev = QAction("이전 페이지(&[)", self)
        act_prev.setShortcut(QKeySequence("PgUp"))
        act_prev.triggered.connect(self._goto_prev_page)
        view_menu.addAction(act_prev)

        act_next = QAction("다음 페이지(&])", self)
        act_next.setShortcut(QKeySequence("PgDown"))
        act_next.triggered.connect(self._goto_next_page)
        view_menu.addAction(act_next)

        view_menu.addSeparator()
        act_fullscreen = QAction("전체 화면(&F)", self)
        act_fullscreen.setShortcut(QKeySequence("F11"))
        act_fullscreen.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(act_fullscreen)

        view_menu.addSeparator()
        act_next_tab = QAction("다음 탭", self)
        act_next_tab.setShortcut(QKeySequence("Ctrl+Tab"))
        act_next_tab.triggered.connect(self._next_tab)
        view_menu.addAction(act_next_tab)

        act_prev_tab = QAction("이전 탭", self)
        act_prev_tab.setShortcut(QKeySequence("Ctrl+Shift+Tab"))
        act_prev_tab.triggered.connect(self._prev_tab_action)
        view_menu.addAction(act_prev_tab)

        for i in range(1, 10):
            act = QAction(f"탭 {i}(&{i})", self)
            act.setShortcut(QKeySequence(f"Ctrl+{i}"))
            act.triggered.connect(lambda checked, n=i: self._goto_tab(n - 1))
            view_menu.addAction(act)

        # ── 페이지 ────────────────────────────────────────────────────────────
        page_menu = menu_bar.addMenu("페이지(&P)")
        act_rotate_cw = QAction("시계방향 회전(&R)", self)
        act_rotate_cw.setShortcut(QKeySequence("Ctrl+R"))
        act_rotate_cw.triggered.connect(self._rotate_cw)
        page_menu.addAction(act_rotate_cw)

        act_rotate_ccw = QAction("반시계방향 회전(&L)", self)
        act_rotate_ccw.setShortcut(QKeySequence("Ctrl+Shift+R"))
        act_rotate_ccw.triggered.connect(self._rotate_ccw)
        page_menu.addAction(act_rotate_ccw)

        page_menu.addSeparator()
        act_merge = QAction("병합...(&M)", self)
        act_merge.setShortcut(QKeySequence("Ctrl+Shift+M"))
        act_merge.triggered.connect(self._open_merge_dialog)
        page_menu.addAction(act_merge)

        act_split = QAction("분할...(&S)", self)
        act_split.triggered.connect(self._open_split_dialog)
        page_menu.addAction(act_split)

        # ── 어노테이션 ────────────────────────────────────────────────────────
        annot_menu = menu_bar.addMenu("어노테이션(&A)")
        for tool, act in self._toolbar._tool_actions.items():
            annot_menu.addAction(act)
        annot_menu.addSeparator()
        act_stamp = annot_menu.addAction("스탬프...(&S)")
        act_stamp.triggered.connect(self._open_stamp_dialog)

        # ── 도구 ──────────────────────────────────────────────────────────────
        tools_menu = menu_bar.addMenu("도구(&T)")
        act_convert = tools_menu.addAction("변환...(&C)")
        act_convert.setShortcut("Ctrl+Shift+C")
        act_convert.triggered.connect(self._open_convert_dialog)
        tools_menu.addSeparator()
        tools_menu.addAction("OCR 텍스트 인식...(&O)").triggered.connect(self._open_ocr_dialog)
        tools_menu.addAction("최적화...(&P)").triggered.connect(self._open_optimize_dialog)
        tools_menu.addAction("비교...(&D)").triggered.connect(self._open_compare_dialog)
        tools_menu.addAction("워터마크...(&W)").triggered.connect(self._open_watermark_dialog)

        # ── 보안 ──────────────────────────────────────────────────────────────
        security_menu = menu_bar.addMenu("보안(&S)")
        security_menu.addAction("암호 설정...(&E)").triggered.connect(self._open_security_dialog)
        security_menu.addAction("디지털 서명...(&G)").triggered.connect(self._open_signature_dialog)

        # ── 도움말 ────────────────────────────────────────────────────────────
        help_menu = menu_bar.addMenu("도움말(&H)")
        act_settings = help_menu.addAction("설정...(&S)")
        act_settings.triggered.connect(self._open_settings_dialog)
        help_menu.addSeparator()
        act_about = help_menu.addAction("정보(&A)...")
        act_about.triggered.connect(self._show_about)

    # ── 시그널 연결 ───────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        # 파일
        self._toolbar.open_requested.connect(self._open_file)
        self._toolbar.save_requested.connect(self._save_file)

        # 줌
        self._toolbar.zoom_in_requested.connect(self._zoom_in)
        self._toolbar.zoom_out_requested.connect(self._zoom_out)
        self._toolbar.zoom_fit_requested.connect(self._zoom_fit)
        self._toolbar.zoom_value_changed.connect(self._set_zoom)

        # 페이지 편집
        self._toolbar.delete_page_requested.connect(self._delete_selected_pages)
        self._toolbar.extract_page_requested.connect(self._extract_selected_pages)
        self._toolbar.insert_page_requested.connect(self._insert_pages_at_current)
        self._page_panel.page_selected.connect(self._on_thumbnail_selected)
        self._page_panel.page_moved.connect(self._on_page_moved)
        self._page_panel.delete_requested.connect(self._delete_pages)
        self._page_panel.extract_requested.connect(self._extract_pages)
        self._page_panel.insert_requested.connect(self._insert_pages)

        # 어노테이션
        self._toolbar.tool_changed.connect(self._on_tool_changed)
        self._toolbar.color_changed.connect(self._on_color_changed)
        self._toolbar.width_changed.connect(self._on_width_changed)
        self._toolbar.text_font_changed.connect(self._on_text_font_changed)
        self._toolbar.text_size_changed.connect(self._on_text_size_changed)
        self._toolbar.text_bold_changed.connect(self._on_text_bold_changed)
        self._toolbar.text_italic_changed.connect(self._on_text_italic_changed)

        # 검색바
        if self._search_bar:
            self._search_bar.search_requested.connect(self._on_search_requested)
            self._search_bar.next_requested.connect(self._on_search_next)
            self._search_bar.prev_requested.connect(self._on_search_prev)

        # 북마크 패널
        if self._bookmark_panel:
            self._bookmark_panel.page_requested.connect(self._on_bookmark_page_requested)

        # 변환
        self._toolbar.convert_requested.connect(self._open_convert_dialog)

        # 탭
        self._tab_widget.active_tab_changed.connect(self._on_active_tab_changed)

    # ── 활성 탭 ───────────────────────────────────────────────────────────────

    def _active_tab(self) -> PdfTabPage | None:
        return self._tab_widget.active_tab()

    def _on_active_tab_changed(self, tab: PdfTabPage | None) -> None:
        if self._prev_tab is not None:
            try:
                self._prev_tab.viewer.zoom_changed.disconnect(self._on_zoom_changed)
                self._prev_tab.viewer.page_changed.disconnect(self._on_page_changed)
                self._prev_tab.viewer.annotation_requested.disconnect(self._on_annotation_requested)
            except (TypeError, RuntimeError):
                pass
        self._prev_tab = tab

        if tab is None:
            self.setWindowTitle(f"{self.APP_TITLE} v{__version__}")
            self._lbl_file.setText("")
            self._lbl_page.setText("페이지: -")
            self._lbl_zoom.setText("줌: -")
            self._toolbar.set_document_loaded(False)
            self._update_undo_actions(tab)
            return

        tab.viewer.zoom_changed.connect(self._on_zoom_changed)
        tab.viewer.page_changed.connect(self._on_page_changed)
        tab.viewer.annotation_requested.connect(self._on_annotation_requested)

        if tab.doc.is_open:
            self._page_panel.load_document(tab.doc)
            if self._bookmark_panel:
                self._bookmark_panel.load_bookmarks(tab.path)
            self._update_title(tab.path)
            self._lbl_file.setText(os.path.basename(tab.path))
            self._toolbar.set_document_loaded(True)
        else:
            self.setWindowTitle(f"{self.APP_TITLE} v{__version__}")
            self._lbl_file.setText("")
            self._toolbar.set_document_loaded(False)

        if self._search_bar:
            if tab.search_query:
                self._search_bar.show()
            else:
                self._search_bar.hide()

        self._update_page_status(tab.viewer.current_page)
        self._toolbar.update_zoom_display(tab.viewer.zoom)
        self._toolbar.set_tool_checked(AnnotationTool.SELECT)
        self._sync_annot_style()
        self._update_undo_actions(tab)

    # ── 줌 위임 ───────────────────────────────────────────────────────────────

    def _zoom_in(self) -> None:
        tab = self._active_tab()
        if tab:
            tab.viewer.zoom_in()

    def _zoom_out(self) -> None:
        tab = self._active_tab()
        if tab:
            tab.viewer.zoom_out()

    def _zoom_fit(self) -> None:
        tab = self._active_tab()
        if tab:
            tab.viewer.zoom_fit()

    def _set_zoom(self, zoom: float) -> None:
        tab = self._active_tab()
        if tab:
            tab.viewer.set_zoom(zoom)

    def _on_bookmark_page_requested(self, page: int) -> None:
        tab = self._active_tab()
        if tab:
            tab.viewer.goto_page(page)

    def _goto_prev_page(self) -> None:
        tab = self._active_tab()
        if tab:
            tab.viewer.goto_page(tab.viewer.current_page - 1)

    def _goto_next_page(self) -> None:
        tab = self._active_tab()
        if tab:
            tab.viewer.goto_page(tab.viewer.current_page + 1)

    # ── 탭 이동 ───────────────────────────────────────────────────────────────

    def _next_tab(self) -> None:
        n = self._tab_widget.count()
        if n < 2:
            return
        self._tab_widget.setCurrentIndex((self._tab_widget.currentIndex() + 1) % n)

    def _prev_tab_action(self) -> None:
        n = self._tab_widget.count()
        if n < 2:
            return
        self._tab_widget.setCurrentIndex((self._tab_widget.currentIndex() - 1) % n)

    def _goto_tab(self, index: int) -> None:
        if 0 <= index < self._tab_widget.count():
            self._tab_widget.setCurrentIndex(index)

    # ── 파일 작업 ─────────────────────────────────────────────────────────────

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "PDF 파일 열기", "", "PDF 파일 (*.pdf);;모든 파일 (*)"
        )
        if not path:
            return
        try:
            self._tab_widget.open_pdf(path)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일을 열 수 없습니다:\n{e}")
            return
        self._add_recent_file(path)

    def _save_file(self) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        try:
            tab.doc.save()
            self._status_bar.showMessage("저장 완료", 2000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")

    def _save_as(self) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "다른 이름으로 저장", "", "PDF 파일 (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            tab.doc.save(path)
            self._update_title(path)
            self._lbl_file.setText(os.path.basename(path))
            self._status_bar.showMessage("저장 완료", 2000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")

    # ── 페이지 편집 ───────────────────────────────────────────────────────────

    def _on_page_moved(self, from_idx: int, to_idx: int) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        cmd = MovePageCommand(tab.doc.raw, from_idx, to_idx)
        tab.cmd_mgr.execute(cmd)
        self._refresh_after_edit()
        tab.viewer.goto_page(min(to_idx, tab.doc.page_count - 1))
        self._status_bar.showMessage(f"페이지 {from_idx + 1} → {to_idx + 1} 이동", 2000)
        self._update_undo_actions(tab)

    def _delete_selected_pages(self) -> None:
        self._delete_pages(self._page_panel.selected_indices())

    def _delete_pages(self, indices: list[int]) -> None:
        tab = self._active_tab()
        if not indices or tab is None or not tab.doc.is_open:
            return
        if tab.doc.page_count <= len(indices):
            QMessageBox.warning(self, "삭제 불가", "모든 페이지를 삭제할 수 없습니다.")
            return
        page_nums = ", ".join(str(i + 1) for i in sorted(indices))
        reply = QMessageBox.question(
            self, "페이지 삭제", f"페이지 {page_nums}을(를) 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        cmd = DeletePagesCommand(tab.doc.raw, indices)
        tab.cmd_mgr.execute(cmd)
        self._refresh_after_edit()
        self._status_bar.showMessage(f"{len(indices)}개 페이지 삭제됨", 2000)
        self._update_undo_actions(tab)

    def _extract_selected_pages(self) -> None:
        self._extract_pages(self._page_panel.selected_indices())

    def _extract_pages(self, indices: list[int]) -> None:
        tab = self._active_tab()
        if not indices or tab is None or not tab.doc.is_open:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "페이지 추출 — 저장 위치 선택", "", "PDF 파일 (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            page_editor.extract_pages(tab.doc.raw, indices, path)
            self._status_bar.showMessage(
                f"{len(indices)}개 페이지 추출 → {os.path.basename(path)}", 3000
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"추출 실패:\n{e}")

    def _insert_pages_at_current(self) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        self._insert_pages(tab.viewer.current_page + 1)

    def _insert_pages(self, insert_before: int) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        dlg = InsertDialog(self)
        if dlg.exec() != InsertDialog.DialogCode.Accepted:
            return
        source_path = dlg.source_path()
        source_indices = dlg.selected_indices()
        if not source_path or not source_indices:
            return
        try:
            cmd = InsertPagesCommand(tab.doc.raw, source_path, source_indices, insert_before)
            tab.cmd_mgr.execute(cmd)
            self._refresh_after_edit()
            self._status_bar.showMessage(f"{len(source_indices)}개 페이지 삽입 완료", 3000)
            self._update_undo_actions(tab)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"삽입 실패:\n{e}")

    def _refresh_after_edit(self) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        current = tab.viewer.current_page
        self._page_panel.reload_all()
        target = min(current, tab.doc.page_count - 1)
        tab.viewer.goto_page(max(0, target))
        self._update_page_status(tab.viewer.current_page)

    # ── 어노테이션 ───────────────────────────────────────────────────────────

    def _on_tool_changed(self, tool: AnnotationTool) -> None:
        tab = self._active_tab()
        if tab:
            tab.viewer.set_tool(tool)
        self._toolbar.set_text_tool_active(tool == AnnotationTool.TEXT)
        tool_names = {
            AnnotationTool.SELECT:  "선택",
            AnnotationTool.TEXT:    "텍스트",
            AnnotationTool.RECT:    "사각형",
            AnnotationTool.ELLIPSE: "타원",
            AnnotationTool.LINE:    "선",
        }
        self._lbl_tool.setText(f"도구: {tool_names.get(tool, '')}")

    def _on_color_changed(self, rgb: tuple) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        style = tab.viewer.annotation_style
        style.color = rgb
        tab.viewer.set_annotation_style(style)

    def _on_width_changed(self, width: float) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        style = tab.viewer.annotation_style
        style.line_width = width
        tab.viewer.set_annotation_style(style)

    def _on_text_font_changed(self, family: str) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        style = tab.viewer.annotation_style
        style.font_family = family
        tab.viewer.set_annotation_style(style)

    def _on_text_size_changed(self, size: float) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        style = tab.viewer.annotation_style
        style.font_size = size
        tab.viewer.set_annotation_style(style)

    def _on_text_bold_changed(self, bold: bool) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        style = tab.viewer.annotation_style
        style.bold = bold
        tab.viewer.set_annotation_style(style)

    def _on_text_italic_changed(self, italic: bool) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        style = tab.viewer.annotation_style
        style.italic = italic
        tab.viewer.set_annotation_style(style)

    def _on_annotation_requested(self, annotate_fn, description: str) -> None:
        """PdfViewer에서 어노테이션 요청 시 커맨드로 래핑해 실행합니다."""
        tab = self._active_tab()
        if tab is None:
            return
        cmd = AddAnnotationCommand(
            tab.doc.raw, tab.viewer.current_page, annotate_fn, description
        )
        tab.cmd_mgr.execute(cmd)
        tab.viewer.refresh_page()
        self._page_panel.reload_page(tab.viewer.current_page)
        self._status_bar.showMessage(f"{description} — Ctrl+Z로 취소 가능", 3000)
        tab.viewer.annotation_added.emit()  # 호환용
        self._update_undo_actions(tab)

    # ── Undo / Redo ───────────────────────────────────────────────────────────

    def _undo(self) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        desc = tab.cmd_mgr.undo()
        if desc is None:
            return
        self._full_undo_redo_refresh()
        self._status_bar.showMessage(f"실행 취소: {desc}", 2000)
        self._update_undo_actions(tab)

    def _redo(self) -> None:
        tab = self._active_tab()
        if tab is None:
            return
        desc = tab.cmd_mgr.redo()
        if desc is None:
            return
        self._full_undo_redo_refresh()
        self._status_bar.showMessage(f"다시 실행: {desc}", 2000)
        self._update_undo_actions(tab)

    def _full_undo_redo_refresh(self) -> None:
        """Undo/Redo 후 UI 전체 갱신."""
        self._refresh_after_edit()
        tab = self._active_tab()
        if tab:
            tab.viewer.refresh_page()

    def _update_undo_actions(self, tab: PdfTabPage | None = None) -> None:
        """Undo/Redo 액션 활성화 상태와 텍스트를 갱신합니다."""
        if tab is None:
            tab = self._active_tab()
        can_undo = tab.cmd_mgr.can_undo if tab else False
        can_redo = tab.cmd_mgr.can_redo if tab else False
        self._act_undo.setEnabled(can_undo)
        self._act_redo.setEnabled(can_redo)
        u_desc = tab.cmd_mgr.undo_description if tab else None
        r_desc = tab.cmd_mgr.redo_description if tab else None
        self._act_undo.setText(f"실행 취소: {u_desc}(&Z)" if u_desc else "실행 취소(&Z)")
        self._act_redo.setText(f"다시 실행: {r_desc}(&Y)" if r_desc else "다시 실행(&Y)")

    # ── 변환 ─────────────────────────────────────────────────────────────────

    def _open_convert_dialog(self) -> None:
        from app.ui.dialogs.convert_dialog import ConvertDialog
        dlg = ConvertDialog(self)
        dlg.conversion_done.connect(self._open_converted_pdfs)
        dlg.exec()

    def _open_converted_pdfs(self, output_paths: list) -> None:
        """변환 완료 후 결과 PDF들을 새 탭에서 엽니다."""
        for path in output_paths:
            try:
                self._tab_widget.open_pdf(path)
            except Exception as exc:
                QMessageBox.critical(self, "오류", f"변환된 파일을 열 수 없습니다:\n{exc}")

    def _sync_annot_style(self) -> None:
        """툴바의 현재 색상/굵기/텍스트 스타일을 활성 탭 뷰어 스타일에 동기화합니다."""
        tab = self._active_tab()
        if tab is None:
            return
        style = AnnotationStyle(
            color=self._toolbar.current_annot_color,
            line_width=self._toolbar.current_annot_width,
            font_size=self._toolbar.current_font_size,
            font_family=self._toolbar.current_font_family,
            bold=self._toolbar.current_bold,
            italic=self._toolbar.current_italic,
        )
        tab.viewer.set_annotation_style(style)

    # ── 이벤트 핸들러 ─────────────────────────────────────────────────────────

    def _on_zoom_changed(self, zoom: float) -> None:
        self._lbl_zoom.setText(f"줌: {round(zoom * 100)}%")
        self._toolbar.update_zoom_display(zoom)

    def _on_page_changed(self, page_idx: int) -> None:
        self._update_page_status(page_idx)
        self._page_panel.set_current_page(page_idx)

    def _on_thumbnail_selected(self, page_idx: int) -> None:
        tab = self._active_tab()
        if tab:
            tab.viewer.goto_page(page_idx)

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
        tab = self._active_tab()
        total = tab.doc.page_count if tab and tab.doc.is_open else 0
        self._lbl_page.setText(f"페이지: {page_idx + 1} / {total}" if total else "페이지: -")

    # ── 전체 화면 ─────────────────────────────────────────────────────────────

    def toggle_fullscreen(self) -> None:
        """전체 화면 토글."""
        if self._is_fullscreen:
            self.showNormal()
            self._toolbar.show()
            self._side_tabs.show()
            self._status_bar.show()
            self.menuBar().show()
            self._is_fullscreen = False
        else:
            self._toolbar.hide()
            self._side_tabs.hide()
            self._status_bar.hide()
            self.menuBar().hide()
            self.showFullScreen()
            self._is_fullscreen = True

    # ── 드래그 앤 드롭 ────────────────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith(".pdf") for u in urls):
                event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self._open_in_new_tab(path)
                self._add_recent_file(path)

    def handle_drop_file(self, path: str) -> None:
        """드래그앤드롭/외부 요청으로 파일 열기."""
        self._open_in_new_tab(path)
        self._add_recent_file(path)

    def _open_in_new_tab(self, path: str) -> None:
        try:
            self._tab_widget.open_pdf(path)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일을 열 수 없습니다:\n{e}")

    # ── 검색 ─────────────────────────────────────────────────────────────────

    def _toggle_search_bar(self) -> None:
        """검색바 표시/숨기기 토글."""
        if self._search_bar is None:
            return
        if self._search_bar.isVisible():
            self._search_bar.close_bar()
            tab = self._active_tab()
            if tab:
                tab.search_results = []
                tab.search_idx = -1
                tab.search_query = ""
        else:
            self._search_bar.show()
            self._search_bar.focus_input()

    def _on_search_requested(self, text: str) -> None:
        """검색 실행."""
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open or not text:
            return
        try:
            from app.core.search_engine import SearchEngine
            engine = SearchEngine(tab.doc.path)
            tab.search_results = engine.search(
                text,
                case_sensitive=self._search_bar.is_case_sensitive(),
                whole_word=self._search_bar.is_whole_word(),
                regex=self._search_bar.is_regex(),
            )
            tab.search_query = text
            tab.search_idx = 0 if tab.search_results else -1
            self._search_bar.set_result_count(
                len(tab.search_results), max(0, tab.search_idx)
            )
            if tab.search_results:
                tab.viewer.goto_page(tab.search_results[0].page_idx)
            self._status_bar.showMessage(f"검색: {len(tab.search_results)}개 매칭", 2000)
        except Exception as e:
            self._status_bar.showMessage(f"검색 오류: {e}", 3000)

    def _on_search_next(self) -> None:
        """다음 검색 결과."""
        tab = self._active_tab()
        if tab is None or not tab.search_results:
            return
        tab.search_idx = (tab.search_idx + 1) % len(tab.search_results)
        self._search_bar.set_result_count(len(tab.search_results), tab.search_idx)
        tab.viewer.goto_page(tab.search_results[tab.search_idx].page_idx)

    def _on_search_prev(self) -> None:
        """이전 검색 결과."""
        tab = self._active_tab()
        if tab is None or not tab.search_results:
            return
        tab.search_idx = (tab.search_idx - 1) % len(tab.search_results)
        self._search_bar.set_result_count(len(tab.search_results), tab.search_idx)
        tab.viewer.goto_page(tab.search_results[tab.search_idx].page_idx)

    # ── 페이지 회전 ───────────────────────────────────────────────────────────

    def _rotate_cw(self) -> None:
        """현재 페이지 시계방향 90° 회전."""
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        page_editor.rotate_page(tab.doc.raw, tab.viewer.current_page, 90)
        self._refresh_after_edit()
        self._status_bar.showMessage("시계방향 90° 회전", 2000)

    def _rotate_ccw(self) -> None:
        """현재 페이지 반시계방향 90° 회전."""
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        page_editor.rotate_page(tab.doc.raw, tab.viewer.current_page, -90)
        self._refresh_after_edit()
        self._status_bar.showMessage("반시계방향 90° 회전", 2000)

    # ── 병합 ─────────────────────────────────────────────────────────────────

    def _open_merge_dialog(self) -> None:
        """PDF 병합 — 간단 구현 (파일 선택 → 병합)."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "병합할 PDF 파일 선택", "", "PDF 파일 (*.pdf)"
        )
        if not paths or len(paths) < 2:
            return
        out_path, _ = QFileDialog.getSaveFileName(
            self, "병합 결과 저장", "", "PDF 파일 (*.pdf)"
        )
        if not out_path:
            return
        if not out_path.lower().endswith(".pdf"):
            out_path += ".pdf"
        try:
            from app.core.merger import merge_pdfs
            merge_pdfs(paths, out_path)
            self._status_bar.showMessage(f"병합 완료: {os.path.basename(out_path)}", 3000)
            reply = QMessageBox.question(
                self, "병합 완료", "병합된 PDF를 열겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.handle_drop_file(out_path)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"병합 실패:\n{e}")

    # ── 최근 파일 ─────────────────────────────────────────────────────────────

    def _add_recent_file(self, path: str) -> None:
        """최근 파일 목록에 추가."""
        try:
            from app.services.settings import AppSettings
            settings = AppSettings()
            settings.add_recent_file(path)
            self._update_recent_menu()
        except Exception:
            pass

    def _update_recent_menu(self) -> None:
        """최근 파일 메뉴 갱신."""
        if self._recent_menu is None:
            return
        self._recent_menu.clear()
        try:
            from app.services.settings import AppSettings
            settings = AppSettings()
            recent = settings.get_recent_files()
            for path in recent[:10]:
                act = self._recent_menu.addAction(os.path.basename(path))
                act.setData(path)
                act.triggered.connect(lambda checked, p=path: self._open_in_new_tab(p))
            if not recent:
                self._recent_menu.addAction("(없음)").setEnabled(False)
        except Exception:
            self._recent_menu.addAction("(없음)").setEnabled(False)

    # ── 분할 ─────────────────────────────────────────────────────────────────

    def _open_split_dialog(self) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        from app.ui.dialogs.split_dialog import SplitDialog
        dlg = SplitDialog(self, page_count=tab.doc.page_count)
        if dlg.exec() != SplitDialog.DialogCode.Accepted:
            return
        out_dir = QFileDialog.getExistingDirectory(self, "분할 결과 저장 폴더")
        if not out_dir:
            return
        try:
            from app.core.merger import split_pdf
            kwargs = {}
            if dlg.split_mode() == "bookmark":
                kwargs["by_bookmarks"] = True
            else:
                kwargs["pages_per_split"] = dlg.pages_per_split()
            files = split_pdf(tab.doc.path, out_dir, **kwargs)
            self._status_bar.showMessage(f"분할 완료: {len(files)}개 파일", 3000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"분할 실패:\n{e}")

    # ── 스탬프 ────────────────────────────────────────────────────────────────

    def _open_stamp_dialog(self) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        from app.ui.dialogs.stamp_dialog import StampDialog
        import fitz
        dlg = StampDialog(self)
        if dlg.exec() != StampDialog.DialogCode.Accepted:
            return
        page = tab.doc.raw[tab.viewer.current_page]
        if dlg.is_text_stamp():
            from app.core.stamp import add_text_stamp
            center = fitz.Point(page.rect.width / 2, page.rect.height / 2)
            add_text_stamp(page, center, dlg.stamp_text(),
                           fontsize=dlg.fontsize(), rotate=dlg.rotation(),
                           opacity=dlg.opacity())
        elif dlg.image_path():
            from app.core.stamp import add_image_stamp
            add_image_stamp(page, fitz.Rect(100, 100, 300, 300), dlg.image_path())
        tab.viewer.refresh_page()
        self._page_panel.reload_page(tab.viewer.current_page)
        self._status_bar.showMessage("스탬프 추가됨", 2000)

    # ── OCR ────────────────────────────────────────────────────────────────────

    def _open_ocr_dialog(self) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        from app.ui.dialogs.ocr_dialog import OcrDialog
        dlg = OcrDialog(self, page_count=tab.doc.page_count)
        if dlg.exec() != OcrDialog.DialogCode.Accepted:
            return
        try:
            from app.core.ocr_engine import add_ocr_layer
            out_path, _ = QFileDialog.getSaveFileName(self, "OCR 결과 저장", "", "PDF (*.pdf)")
            if out_path:
                add_ocr_layer(tab.doc.path, out_path, lang=dlg.language(), dpi=dlg.dpi())
                self._status_bar.showMessage("OCR 완료", 3000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"OCR 실패:\n{e}")

    # ── 최적화 ────────────────────────────────────────────────────────────────

    def _open_optimize_dialog(self) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        from app.ui.dialogs.optimize_dialog import OptimizeDialog
        file_size = os.path.getsize(tab.doc.path) if tab.doc.path else 0
        dlg = OptimizeDialog(self, current_size=file_size)
        if dlg.exec() != OptimizeDialog.DialogCode.Accepted:
            return
        out_path, _ = QFileDialog.getSaveFileName(self, "최적화 결과 저장", "", "PDF (*.pdf)")
        if not out_path:
            return
        try:
            from app.core.optimizer import optimize_pdf
            optimize_pdf(tab.doc.path, out_path, preset=dlg.preset())
            new_size = os.path.getsize(out_path)
            self._status_bar.showMessage(f"최적화 완료: {new_size / 1024:.0f} KB", 3000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"최적화 실패:\n{e}")

    # ── 비교 ──────────────────────────────────────────────────────────────────

    def _open_compare_dialog(self) -> None:
        from app.ui.dialogs.compare_dialog import CompareDialog
        tab = self._active_tab()
        current = tab.doc.path if tab and tab.doc.is_open else ""
        CompareDialog(self, current_path=current).exec()

    # ── 워터마크 ──────────────────────────────────────────────────────────────

    def _open_watermark_dialog(self) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        from app.ui.dialogs.watermark_dialog import WatermarkDialog
        dlg = WatermarkDialog(self)
        if dlg.exec() != WatermarkDialog.DialogCode.Accepted:
            return
        out_path, _ = QFileDialog.getSaveFileName(self, "결과 저장", "", "PDF (*.pdf)")
        if not out_path:
            return
        try:
            if dlg.current_tab() == 0:
                from app.core.watermark import add_text_watermark
                add_text_watermark(tab.doc.path, out_path, dlg.watermark_text(),
                                   opacity=dlg.opacity(), rotate=dlg.rotation(),
                                   tile=dlg.is_tile())
            else:
                from app.core.watermark import add_header_footer
                add_header_footer(tab.doc.path, out_path, **dlg.header_footer_settings())
            self._status_bar.showMessage("적용 완료", 3000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"실패:\n{e}")

    # ── 보안 ──────────────────────────────────────────────────────────────────

    def _open_security_dialog(self) -> None:
        tab = self._active_tab()
        if tab is None or not tab.doc.is_open:
            return
        from app.ui.dialogs.security_dialog import SecurityDialog
        dlg = SecurityDialog(self)
        if dlg.exec() != SecurityDialog.DialogCode.Accepted:
            return
        out_path, _ = QFileDialog.getSaveFileName(self, "암호화 저장", "", "PDF (*.pdf)")
        if not out_path:
            return
        try:
            from app.core.security import encrypt_pdf
            encrypt_pdf(tab.doc.path, out_path,
                        user_password=dlg.user_password(),
                        owner_password=dlg.owner_password(),
                        algorithm=dlg.algorithm(),
                        permissions=dlg.permissions())
            self._status_bar.showMessage("암호 설정 완료", 3000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"암호 설정 실패:\n{e}")

    # ── 서명 ──────────────────────────────────────────────────────────────────

    def _open_signature_dialog(self) -> None:
        from app.ui.dialogs.signature_dialog import SignatureDialog
        dlg = SignatureDialog(self)
        if dlg.exec() != SignatureDialog.DialogCode.Accepted:
            return
        self._status_bar.showMessage("디지털 서명: pyHanko 통합 후 사용 가능", 3000)

    # ── 설정 ──────────────────────────────────────────────────────────────────

    def _open_settings_dialog(self) -> None:
        try:
            from app.services.settings import AppSettings
            from app.ui.dialogs.settings_dialog import SettingsDialog
            settings = AppSettings()
            dlg = SettingsDialog(self, settings=settings)
            if dlg.exec() == SettingsDialog.DialogCode.Accepted:
                from app.services.theme import get_stylesheet
                from PyQt6.QtWidgets import QApplication
                QApplication.instance().setStyleSheet(get_stylesheet(dlg.theme()))
                self._status_bar.showMessage("설정 저장됨", 2000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 오류:\n{e}")

    # ── 닫기 ─────────────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        # 앱 종료 시에는 저장 확인 없이 즉시 정리한다.
        for i in range(self._tab_widget.count() - 1, -1, -1):
            tab = self._tab_widget.widget(i)
            if isinstance(tab, PdfTabPage):
                tab.cleanup()
            self._tab_widget.removeTab(i)
        event.accept()
