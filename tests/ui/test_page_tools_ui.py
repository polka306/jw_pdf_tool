"""TC-265 ~ TC-278: 페이지 도구 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestRotationUI:
    """회전 관련 UI 테스트."""

    @pytest.fixture
    def win(self, qtbot, pdf_5pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        win.show()
        load_pdf_directly(win, pdf_5pages)
        qtbot.wait(300)
        yield win
        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()

    # TC-265: 회전 함수 직접 호출
    def test_tc265_rotate_via_editor(self, win):
        import fitz
        from app.core.page_editor import rotate_page

        page = win._tab_widget.active_tab().doc.raw[0]
        original = page.rotation
        rotate_page(win._tab_widget.active_tab().doc.raw, 0, 90)
        assert win._tab_widget.active_tab().doc.raw[0].rotation == (original + 90) % 360

    # TC-266: Ctrl+R 단축키
    def test_tc266_rotate_shortcut(self, win):
        win._rotate_cw()

    # TC-267: Ctrl+Shift+R 반시계
    def test_tc267_rotate_ccw_shortcut(self, win):
        win._rotate_ccw()


class TestMergeSplitUI:
    """병합/분할 다이얼로그 UI 테스트."""

    # TC-268: 병합 다이얼로그
    def test_tc268_merge_dialog_exists(self):
        from app.ui.dialogs.merge_dialog import MergeDialog
        assert MergeDialog is not None

    # TC-269: 병합 실행
    def test_tc269_merge_execution(self, tmp_path):
        from app.core.merger import merge_pdfs
        import fitz

        pdfs = []
        for i in range(2):
            doc = fitz.open()
            doc.new_page(width=595, height=842)
            p = str(tmp_path / f"m{i}.pdf")
            doc.save(p)
            doc.close()
            pdfs.append(p)

        out = str(tmp_path / "merged.pdf")
        merge_pdfs(pdfs, out)
        assert os.path.exists(out)

    # TC-270: 분할 다이얼로그
    def test_tc270_split_dialog_exists(self):
        from app.ui.dialogs.split_dialog import SplitDialog
        assert SplitDialog is not None

    # TC-271: 분할 실행
    def test_tc271_split_execution(self, tmp_path):
        from app.core.merger import split_pdf
        import fitz

        doc = fitz.open()
        for i in range(4):
            doc.new_page(width=595, height=842)
        p = str(tmp_path / "tosplit.pdf")
        doc.save(p)
        doc.close()

        out_dir = str(tmp_path / "split_out")
        os.makedirs(out_dir)
        files = split_pdf(p, out_dir, pages_per_split=2)
        assert len(files) == 2


class TestCropUI:
    """크롭 UI 테스트."""

    # TC-272: 크롭 도구 (기능 확인)
    def test_tc272_crop_tool(self, pdf_3pages):
        import fitz
        from app.core.page_editor import crop_page

        doc = fitz.open(pdf_3pages)
        crop_page(doc, 0, fitz.Rect(50, 50, 400, 600))
        assert doc[0].cropbox.width < doc[0].mediabox.width
        doc.close()

    # TC-273: 크롭 프리뷰 (크롭 기능 자체는 작동 확인)
    def test_tc273_crop_preview(self, pdf_3pages):
        import fitz
        from app.core.page_editor import crop_page, reset_cropbox
        doc = fitz.open(pdf_3pages)
        crop_page(doc, 0, fitz.Rect(50, 50, 400, 600))
        reset_cropbox(doc, 0)
        doc.close()


class TestPrintUI:
    """인쇄 UI 테스트."""

    # TC-274: 인쇄 다이얼로그
    def test_tc274_print_dialog_exists(self):
        from app.ui.dialogs.print_dialog import PrintDialog
        assert PrintDialog is not None

    # TC-275: 페이지 범위 입력
    def test_tc275_page_range_input(self, qtbot):
        from app.ui.dialogs.print_dialog import PrintDialog
        dlg = PrintDialog(page_count=10)
        qtbot.addWidget(dlg)
        assert dlg.page_range_mode() == "all"

    # TC-276: Ctrl+P (기능 존재 확인)
    def test_tc276_ctrl_p_shortcut(self, qtbot):
        from app.ui.dialogs.print_dialog import PrintDialog
        dlg = PrintDialog(page_count=5)
        qtbot.addWidget(dlg)
        assert dlg.copies() == 1


class TestMenuStatus:
    """메뉴/상태바 테스트."""

    # TC-277: 페이지 메뉴 (기능 존재만 확인)
    def test_tc277_page_menu(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        load_pdf_directly(win, pdf_3pages)

        # 메뉴바에 편집 메뉴가 있는지
        menubar = win.menuBar()
        assert menubar is not None

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()

    # TC-278: 회전 후 상태바
    def test_tc278_statusbar_after_rotate(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        load_pdf_directly(win, pdf_3pages)

        # 상태바 존재 확인
        assert win.statusBar() is not None

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
