"""DetachedWindow 단위 테스트."""
from __future__ import annotations
import pytest
from PyQt6.QtWidgets import QMessageBox
from app.ui.detached_window import DetachedWindow
from app.ui.pdf_tab_page import PdfTabPage
from app.ui.pdf_tab_widget import PdfTabWidget

@pytest.fixture
def tab_widget(qtbot):
    w = PdfTabWidget()
    qtbot.addWidget(w)
    yield w
    w.close_all()

@pytest.fixture
def loaded_tab(qtbot, pdf_3pages):
    tab = PdfTabPage()
    qtbot.addWidget(tab)
    tab.load(pdf_3pages)
    yield tab
    tab.cleanup()

class TestDetachedWindowInit:
    def test_creates_window_with_tab(self, qtbot, pdf_3pages, tab_widget, monkeypatch):
        monkeypatch.setattr(QMessageBox, "question",
                            lambda *a, **kw: QMessageBox.StandardButton.No)
        tab = PdfTabPage()
        tab.load(pdf_3pages)
        win = DetachedWindow(tab, tab_widget)
        qtbot.addWidget(win)
        assert win.centralWidget() is tab

    def test_window_title_contains_filename(self, qtbot, pdf_3pages, tab_widget, monkeypatch):
        monkeypatch.setattr(QMessageBox, "question",
                            lambda *a, **kw: QMessageBox.StandardButton.No)
        tab = PdfTabPage()
        tab.load(pdf_3pages)
        win = DetachedWindow(tab, tab_widget)
        qtbot.addWidget(win)
        assert ".pdf" in win.windowTitle()

class TestDetachedWindowReattach:
    def test_reattach_signal_emitted(self, qtbot, loaded_tab, tab_widget, monkeypatch):
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win = DetachedWindow(loaded_tab, tab_widget)
        qtbot.addWidget(win)
        received = []
        win.reattach_requested.connect(received.append)
        win.close()
        assert len(received) == 1
        assert received[0] is loaded_tab

    def test_no_reattach_on_discard(self, qtbot, loaded_tab, tab_widget, monkeypatch):
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.No
        )
        win = DetachedWindow(loaded_tab, tab_widget)
        qtbot.addWidget(win)
        received = []
        win.reattach_requested.connect(received.append)
        win.close()
        assert len(received) == 0
