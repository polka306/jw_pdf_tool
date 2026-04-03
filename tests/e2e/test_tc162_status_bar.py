"""TC-162: 상태바 정보 종합 확인."""

from __future__ import annotations

from app.core.annotator import AnnotationTool
from tests.helpers import load_pdf_directly


class TestTC162:
    """TC-162: 상태바 정보 종합 확인."""

    def test_statusbar_shows_page_info(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=5))
        assert "1 / 5" in win._lbl_page.text()

    def test_statusbar_updates_on_page_change(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=5))
        win._viewer.goto_page(3)
        assert "4 / 5" in win._lbl_page.text()

    def test_statusbar_shows_zoom(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))
        win._viewer.zoom_in()
        zoom_pct = round(win._viewer.zoom * 100)
        assert str(zoom_pct) in win._lbl_zoom.text()

    def test_statusbar_shows_tool_name(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))

        assert "선택" in win._lbl_tool.text()

        win._on_tool_changed(AnnotationTool.RECT)
        assert "사각형" in win._lbl_tool.text()

        win._on_tool_changed(AnnotationTool.TEXT)
        assert "텍스트" in win._lbl_tool.text()

    def test_statusbar_shows_filename(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))
        assert win._lbl_file.text() != ""
