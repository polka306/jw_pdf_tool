"""TC-197: 열기→줌×5→페이지 전환×10→저장 — UI 프리징 없음."""

from __future__ import annotations

import os
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestTC197PerfWorkflow:

    def test_tc197_no_freeze_during_workflow(self, qtbot, pdf_10pages, tmp_path):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        win.show()
        load_pdf_directly(win, pdf_10pages)
        qtbot.wait(500)

        start = time.perf_counter()

        # 줌 변경 5회
        for zoom in [1.0, 1.5, 2.0, 1.5, 1.0]:
            if hasattr(win, '_viewer'):
                win._viewer.set_zoom(zoom)
            qtbot.wait(50)

        # 페이지 전환 10회
        for page in range(10):
            if hasattr(win, '_viewer'):
                win._viewer.goto_page(page)
            qtbot.wait(50)

        # 저장
        save_path = str(tmp_path / "perf_test_output.pdf")
        win._doc.save(save_path)

        total = time.perf_counter() - start

        # 전체 워크플로우가 10초 이내 (프리징 없음)
        assert total < 10.0
        assert os.path.exists(save_path)

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
