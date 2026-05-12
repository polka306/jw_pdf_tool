"""PdfTabWidget 단위 테스트."""
from __future__ import annotations
import pytest
from PyQt6.QtWidgets import QMessageBox
from app.ui.pdf_tab_widget import PdfTabWidget
from app.ui.pdf_tab_page import PdfTabPage

@pytest.fixture
def tab_widget(qtbot):
    w = PdfTabWidget()
    qtbot.addWidget(w)
    yield w
    w.close_all()

class TestPdfTabWidgetOpen:
    def test_open_pdf_creates_tab(self, tab_widget, pdf_3pages):
        tab_widget.open_pdf(pdf_3pages)
        assert tab_widget.count() == 1

    def test_open_pdf_returns_tab_page(self, tab_widget, pdf_3pages):
        tab = tab_widget.open_pdf(pdf_3pages)
        assert isinstance(tab, PdfTabPage)

    def test_open_multiple_pdfs(self, tab_widget, pdf_1page, pdf_3pages):
        tab_widget.open_pdf(pdf_1page)
        tab_widget.open_pdf(pdf_3pages)
        assert tab_widget.count() == 2

    def test_active_tab_none_when_empty(self, tab_widget):
        assert tab_widget.active_tab() is None

    def test_active_tab_after_open(self, tab_widget, pdf_3pages):
        tab = tab_widget.open_pdf(pdf_3pages)
        assert tab_widget.active_tab() is tab

    def test_open_with_page(self, tab_widget, pdf_3pages):
        tab = tab_widget.open_pdf(pdf_3pages, page=1)
        assert tab.viewer.current_page == 1

class TestPdfTabWidgetClose:
    def test_close_tab_removes_it(self, tab_widget, pdf_1page, monkeypatch):
        monkeypatch.setattr(QMessageBox, "question",
                            lambda *a, **kw: QMessageBox.StandardButton.No)
        tab_widget.open_pdf(pdf_1page)
        tab_widget.close_tab(0)
        assert tab_widget.count() == 0

    def test_close_tab_adds_to_recent(self, tab_widget, pdf_1page, monkeypatch):
        monkeypatch.setattr(QMessageBox, "question",
                            lambda *a, **kw: QMessageBox.StandardButton.No)
        tab_widget.open_pdf(pdf_1page)
        tab_widget.close_tab(0)
        assert len(tab_widget._recent_closed) == 1

    def test_reopen_last_closed(self, tab_widget, pdf_1page, monkeypatch):
        monkeypatch.setattr(QMessageBox, "question",
                            lambda *a, **kw: QMessageBox.StandardButton.No)
        tab_widget.open_pdf(pdf_1page)
        tab_widget.close_tab(0)
        tab_widget.reopen_last_closed()
        assert tab_widget.count() == 1

class TestPdfTabWidgetActiveTabChanged:
    def test_signal_emitted_on_open(self, tab_widget, pdf_1page):
        received = []
        tab_widget.active_tab_changed.connect(received.append)
        tab_widget.open_pdf(pdf_1page)
        assert len(received) == 1
        assert isinstance(received[0], PdfTabPage)

    def test_signal_emitted_on_switch(self, tab_widget, pdf_1page, pdf_3pages):
        tab_widget.open_pdf(pdf_1page)
        tab_widget.open_pdf(pdf_3pages)
        received = []
        tab_widget.active_tab_changed.connect(received.append)
        tab_widget.setCurrentIndex(0)
        assert len(received) == 1
