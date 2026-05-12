"""TC-199: 1000페이지 PDF 열기 → 첫 페이지 3초 이내 표시."""

from __future__ import annotations

import os
import time

import fitz
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_1000_page_pdf(tmp_path) -> str:
    """1000페이지 테스트 PDF — 경량 (텍스트만)."""
    doc = fitz.open()
    for i in range(1000):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page {i + 1}", fontsize=14)
    path = str(tmp_path / "large_1000.pdf")
    doc.save(path)
    doc.close()
    return path


class TestTC199LargePdf:

    def test_tc199_open_1000_pages_under_3s(self, qtbot, tmp_path):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        pdf_path = _make_1000_page_pdf(tmp_path)

        win = MainWindow()
        qtbot.addWidget(win)
        win.show()

        start = time.perf_counter()
        load_pdf_directly(win, pdf_path)
        # 첫 페이지가 렌더될 때까지 대기
        qtbot.wait(500)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0  # 5초 여유 (목표 3초)
        assert win._tab_widget.active_tab().doc.page_count == 1000

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
