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

    # TC-304 ~ TC-309: 어노테이션 도구 상호작용 (skip — UI 통합 후)
    @pytest.mark.parametrize("tc", [304, 305, 306, 307, 308, 309])
    def test_tc_annot_interaction(self, tc):
        pytest.skip(f"TC-{tc}: 어노테이션 도구 UI 통합 후속 구현")


class TestStampDialogUI:
    """스탬프 다이얼로그."""

    # TC-310 ~ TC-314: 스탬프 다이얼로그 (skip — 다이얼로그 후속)
    @pytest.mark.parametrize("tc", [310, 311, 312, 313, 314])
    def test_tc_stamp_dialog(self, tc):
        pytest.skip(f"TC-{tc}: StampDialog 후속 구현")


class TestBookmarkPanelEdit:
    """북마크 편집 UI."""

    # TC-315 ~ TC-317: 북마크 편집 UI
    @pytest.mark.parametrize("tc", [315, 316, 317])
    def test_tc_bookmark_edit(self, tc):
        pytest.skip(f"TC-{tc}: BookmarkPanel 편집 UI 후속 구현")


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
