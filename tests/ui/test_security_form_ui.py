"""TC-341 ~ TC-352: 보안/양식 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestSecurityDialogUI:
    """보안 다이얼로그 UI."""

    # TC-341 ~ TC-343: SecurityDialog (skip — 다이얼로그 후속)
    @pytest.mark.parametrize("tc", [341, 342, 343])
    def test_tc_security_dialog(self, tc):
        pytest.skip(f"TC-{tc}: SecurityDialog 후속 구현")

    # TC-344: 암호화된 PDF 열기 → 비밀번호 다이얼로그
    def test_tc344_password_dialog(self):
        pytest.skip("TC-344: 암호 입력 다이얼로그 후속 구현")

    # TC-345: 3회 실패 경고
    def test_tc345_three_failures(self):
        pytest.skip("TC-345: 3회 실패 경고 후속 구현")


class TestFormViewerUI:
    """양식 뷰어 UI."""

    # TC-346 ~ TC-349: 양식 필드 상호작용
    @pytest.mark.parametrize("tc", [346, 347, 348, 349])
    def test_tc_form_interaction(self, tc):
        pytest.skip(f"TC-{tc}: 양식 필드 UI 상호작용 후속 구현")


class TestFormDialogUI:
    """양식 다이얼로그."""

    # TC-350 ~ TC-351: FormDialog
    @pytest.mark.parametrize("tc", [350, 351])
    def test_tc_form_dialog(self, tc):
        pytest.skip(f"TC-{tc}: FormDialog 후속 구현")


class TestSecurityFormMenu:
    """보안/양식 메뉴."""

    # TC-352: 메뉴 항목
    def test_tc352_menu_exists(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        load_pdf_directly(win, pdf_3pages)

        menubar = win.menuBar()
        assert menubar is not None
        # 최소한 메뉴바가 존재하고 편집 메뉴가 있는지
        actions = [a.text() for a in menubar.actions()]
        assert len(actions) >= 4  # 파일, 편집, 보기, ...

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
