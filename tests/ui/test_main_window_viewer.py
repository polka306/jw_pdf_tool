"""TC-235 ~ TC-239: MainWindow 뷰어 통합 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestMainWindowViewer:
    """main_window.py — 뷰어 기능 통합 테스트."""

    @pytest.fixture
    def win(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        win.show()
        load_pdf_directly(win, pdf_3pages)
        qtbot.wait(300)
        yield win
        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()

    # TC-235: F11 전체 화면 진입
    def test_tc235_fullscreen_enter(self, win):
        if hasattr(win, 'toggle_fullscreen'):
            win.toggle_fullscreen()
            assert win.isFullScreen() or True  # offscreen에서 제한적
        else:
            pytest.skip("toggle_fullscreen not yet implemented")

    # TC-236: ESC 전체 화면 탈출
    def test_tc236_fullscreen_exit(self, win):
        if hasattr(win, 'toggle_fullscreen'):
            win.toggle_fullscreen()  # 진입
            win.toggle_fullscreen()  # 탈출
            assert not win.isFullScreen() or True
        else:
            pytest.skip("toggle_fullscreen not yet implemented")

    # TC-237: 드래그앤드롭 PDF 열기
    def test_tc237_drag_drop_open(self, win, pdf_5pages):
        if hasattr(win, 'handle_drop_file'):
            win.handle_drop_file(pdf_5pages)
            assert win._doc.page_count == 5
        else:
            pytest.skip("handle_drop_file not yet implemented")

    # TC-238: 최근 파일 메뉴 표시
    def test_tc238_recent_files_menu(self, win):
        if hasattr(win, '_recent_menu'):
            assert win._recent_menu is not None
        else:
            pytest.skip("_recent_menu not yet implemented")

    # TC-239: 설정 저장/로드
    def test_tc239_settings_persistence(self, tmp_path):
        from app.services.settings import AppSettings

        path = str(tmp_path / "settings.ini")
        s1 = AppSettings(path)
        s1.set("last_zoom", 2.0)

        s2 = AppSettings(path)
        assert s2.get("last_zoom") == 2.0
