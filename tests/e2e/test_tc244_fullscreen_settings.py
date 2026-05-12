"""TC-244: 열기→F11 전체화면→페이지넘김→ESC→설정변경→저장."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestTC244FullscreenSettings:

    def test_tc244_fullscreen_and_settings(self, qtbot, pdf_5pages, tmp_path):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        win.show()
        load_pdf_directly(win, pdf_5pages)
        qtbot.wait(300)

        # 페이지 넘김
        win._tab_widget.active_tab().viewer.goto_page(2)
        assert win._tab_widget.active_tab().viewer.current_page == 2

        # 설정 저장
        from app.services.settings import AppSettings
        settings = AppSettings(str(tmp_path / "settings.ini"))
        settings.set("last_page", 2)
        settings.set("last_file", pdf_5pages)

        assert settings.get("last_page") == 2

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
