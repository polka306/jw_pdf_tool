"""PdfTabPage 단위 테스트."""
from __future__ import annotations
import pytest
from PyQt6.QtWidgets import QApplication
from app.ui.pdf_tab_page import PdfTabPage

@pytest.fixture
def tab_page(qapp):
    page = PdfTabPage()
    yield page
    page.cleanup()

class TestPdfTabPageInit:
    def test_initial_state(self, tab_page):
        assert not tab_page.doc.is_open
        assert tab_page.viewer is not None
        assert tab_page.cmd_mgr is not None
        assert tab_page.search_query == ""
        assert tab_page.search_results == []
        assert tab_page.search_idx == -1

    def test_tab_title_no_doc(self, tab_page):
        assert tab_page.tab_title == "새 탭"

    def test_is_modified_no_doc(self, tab_page):
        assert not tab_page.is_modified

class TestPdfTabPageLoad:
    def test_load_opens_doc(self, tab_page, pdf_3pages):
        tab_page.load(pdf_3pages)
        assert tab_page.doc.is_open
        assert tab_page.doc.path == pdf_3pages

    def test_load_sets_tab_title(self, tab_page, pdf_3pages):
        import os
        tab_page.load(pdf_3pages)
        assert tab_page.tab_title == os.path.basename(pdf_3pages)

    def test_load_with_page(self, tab_page, pdf_3pages):
        tab_page.load(pdf_3pages, page=1)
        assert tab_page.viewer.current_page == 1

    def test_cleanup_closes_doc(self, tab_page, pdf_3pages):
        tab_page.load(pdf_3pages)
        tab_page.cleanup()
        assert not tab_page.doc.is_open

    def test_path_property(self, tab_page, pdf_3pages):
        tab_page.load(pdf_3pages)
        assert tab_page.path == pdf_3pages
