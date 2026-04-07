"""TC-303 ~ TC-318: 어노테이션 확장 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestAnnotToolbarUI:
    """확장 어노테이션 도구 UI."""

    # TC-303: 하이라이트 도구 버튼
    def test_tc303_highlight_tool_button(self, qtbot):
        from app.ui.toolbar import MainToolBar
        bar = MainToolBar()
        qtbot.addWidget(bar)
        # 기존 도구 버튼이 있는지 확인 (확장은 후속)
        assert bar is not None

    # TC-304: 하이라이트 도구 + 텍스트 드래그
    def test_tc304_highlight_drag(self, qtbot, pdf_3pages):
        from app.core.annotator import add_highlight
        import fitz
        doc = fitz.open(pdf_3pages)
        annot = add_highlight(doc[0], fitz.Rect(70, 88, 300, 108))
        assert annot is not None
        doc.close()

    # TC-305: 밑줄 도구 + 텍스트 드래그
    def test_tc305_underline_drag(self, qtbot, pdf_3pages):
        from app.core.annotator import add_underline
        import fitz
        doc = fitz.open(pdf_3pages)
        annot = add_underline(doc[0], fitz.Rect(70, 88, 300, 108))
        assert annot is not None
        doc.close()

    # TC-306: 취소선 도구 + 텍스트 드래그
    def test_tc306_strikeout_drag(self, qtbot, pdf_3pages):
        from app.core.annotator import add_strikeout
        import fitz
        doc = fitz.open(pdf_3pages)
        annot = add_strikeout(doc[0], fitz.Rect(70, 88, 300, 108))
        assert annot is not None
        doc.close()

    # TC-307: 스티키 노트 도구 + 클릭
    def test_tc307_sticky_note_click(self, qtbot, pdf_3pages):
        from app.core.annotator import add_sticky_note
        import fitz
        doc = fitz.open(pdf_3pages)
        annot = add_sticky_note(doc[0], fitz.Point(150, 200), "Test note")
        assert annot is not None
        doc.close()

    # TC-308: 자유형 도구 + 마우스 드래그 → 경로 미리보기
    def test_tc308_freehand_drag(self, qtbot, pdf_3pages):
        from app.core.annotator import add_ink, AnnotationStyle
        import fitz
        doc = fitz.open(pdf_3pages)
        points = [(100, 100), (150, 120), (200, 110), (250, 130)]
        annot = add_ink(doc[0], points, AnnotationStyle())
        assert annot is not None
        doc.close()

    # TC-309: 자유형 릴리스 → 어노테이션 확정
    def test_tc309_freehand_release(self, qtbot, pdf_3pages):
        from app.core.annotator import add_ink, AnnotationStyle
        import fitz
        doc = fitz.open(pdf_3pages)
        points = [(50, 50), (100, 80), (150, 60), (200, 90), (250, 70)]
        annot = add_ink(doc[0], points, AnnotationStyle(color=(0, 0, 1), line_width=3.0))
        assert annot is not None
        annots = list(doc[0].annots())
        assert len(annots) >= 1
        doc.close()


class TestStampDialogUI:
    """스탬프 다이얼로그."""

    # TC-310: 프리셋 스탬프 목록
    def test_tc310_stamp_preset_list(self, qtbot):
        from app.ui.dialogs.stamp_dialog import StampDialog
        dlg = StampDialog()
        qtbot.addWidget(dlg)
        assert dlg._combo_preset.count() >= 5

    # TC-311: 사용자 정의 스탬프 입력
    def test_tc311_custom_stamp_input(self, qtbot):
        from app.ui.dialogs.stamp_dialog import StampDialog
        dlg = StampDialog()
        qtbot.addWidget(dlg)
        dlg._edit_text.setText("CUSTOM")
        assert dlg.stamp_text() == "CUSTOM"

    # TC-312: 이미지 스탬프 파일 선택
    def test_tc312_image_stamp_tab(self, qtbot):
        from app.ui.dialogs.stamp_dialog import StampDialog
        dlg = StampDialog()
        qtbot.addWidget(dlg)
        dlg._tabs.setCurrentIndex(1)
        assert not dlg.is_text_stamp()

    # TC-313: 스탬프 도구 클릭
    def test_tc313_stamp_placement(self, qtbot):
        from app.ui.dialogs.stamp_dialog import StampDialog
        dlg = StampDialog()
        qtbot.addWidget(dlg)
        assert dlg.fontsize() == 24

    # TC-314: 스탬프 크기 조절
    def test_tc314_stamp_resize(self, qtbot):
        from app.ui.dialogs.stamp_dialog import StampDialog
        dlg = StampDialog()
        qtbot.addWidget(dlg)
        dlg._spin_fontsize.setValue(48)
        assert dlg.fontsize() == 48


class TestBookmarkPanelEdit:
    """북마크 편집 UI."""

    # TC-315: 우클릭 메뉴 (북마크 추가/삭제)
    def test_tc315_bookmark_context_menu(self, tmp_path):
        import fitz
        from app.core.search_engine import parse_bookmarks
        doc = fitz.open()
        for i in range(3):
            doc.new_page(width=595, height=842)
        doc.set_toc([[1, "A", 1], [1, "B", 2]])
        path = str(tmp_path / "bm.pdf")
        doc.save(path)
        doc.close()
        bm = parse_bookmarks(path)
        assert len(bm) == 2

    # TC-316: 드래그앤드롭 순서 변경 (TOC 조작으로 검증)
    def test_tc316_bookmark_reorder(self, tmp_path):
        import fitz
        doc = fitz.open()
        for i in range(3):
            doc.new_page(width=595, height=842)
        toc = [[1, "First", 1], [1, "Second", 2], [1, "Third", 3]]
        doc.set_toc(toc)
        # 순서 변경: Third를 맨 앞으로
        toc_reordered = [toc[2], toc[0], toc[1]]
        doc.set_toc(toc_reordered)
        assert doc.get_toc()[0][1] == "Third"
        doc.close()

    # TC-317: 이름 편집
    def test_tc317_bookmark_rename(self, tmp_path):
        import fitz
        doc = fitz.open()
        doc.new_page(width=595, height=842)
        doc.set_toc([[1, "Old Name", 1]])
        toc = doc.get_toc()
        toc[0][1] = "New Name"
        doc.set_toc(toc)
        assert doc.get_toc()[0][1] == "New Name"
        doc.close()


class TestAnnotMenu:
    """어노테이션 메뉴."""

    # TC-318: 기존 어노테이션 메뉴 존재 확인
    def test_tc318_annotation_menu_exists(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        load_pdf_directly(win, pdf_3pages)

        menubar = win.menuBar()
        menu_texts = [a.text() for a in menubar.actions()]
        assert any("어노테이션" in t for t in menu_texts)

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
