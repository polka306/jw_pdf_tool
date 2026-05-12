"""MainWindow 멀티탭 통합 테스트."""
from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QFileDialog

from app.ui.main_window import MainWindow
from app.ui.pdf_tab_widget import PdfTabWidget


@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    yield w
    for i in range(w._tab_widget.count() - 1, -1, -1):
        tab = w._tab_widget.widget(i)
        if hasattr(tab, "cleanup"):
            tab.cleanup()
        w._tab_widget.removeTab(i)


class TestMainWindowHasTabWidget:
    def test_has_tab_widget(self, win):
        assert hasattr(win, "_tab_widget")
        assert isinstance(win._tab_widget, PdfTabWidget)

    def test_no_single_doc_attr(self, win):
        assert not hasattr(win, "_doc")

    def test_no_single_viewer_attr(self, win):
        assert not hasattr(win, "_viewer")

    def test_no_single_cmd_mgr_attr(self, win):
        assert not hasattr(win, "_cmd_mgr")


class TestMainWindowOpenInTab:
    def test_open_file_creates_tab(self, win, pdf_3pages, monkeypatch):
        monkeypatch.setattr(QFileDialog, "getOpenFileName",
                            lambda *a, **kw: (pdf_3pages, ""))
        win._open_file()
        assert win._tab_widget.count() == 1

    def test_open_two_files_creates_two_tabs(self, win, pdf_1page, pdf_3pages, monkeypatch):
        paths = [pdf_1page, pdf_3pages]
        idx = [0]

        def fake_open(*a, **kw):
            p = paths[idx[0] % 2]
            idx[0] += 1
            return (p, "")
        monkeypatch.setattr(QFileDialog, "getOpenFileName", fake_open)
        win._open_file()
        win._open_file()
        assert win._tab_widget.count() == 2

    def test_title_updates_on_open(self, win, pdf_3pages, monkeypatch):
        monkeypatch.setattr(QFileDialog, "getOpenFileName",
                            lambda *a, **kw: (pdf_3pages, ""))
        win._open_file()
        assert os.path.basename(pdf_3pages) in win.windowTitle()


class TestMainWindowTabSwitch:
    def test_title_updates_on_tab_switch(self, win, pdf_1page, pdf_3pages, monkeypatch):
        paths = [pdf_1page, pdf_3pages]
        idx = [0]

        def fake_open(*a, **kw):
            p = paths[idx[0] % 2]
            idx[0] += 1
            return (p, "")
        monkeypatch.setattr(QFileDialog, "getOpenFileName", fake_open)
        win._open_file()
        win._open_file()
        win._tab_widget.setCurrentIndex(0)
        assert os.path.basename(pdf_1page) in win.windowTitle()

    def test_active_tab_none_when_empty(self, win):
        assert win._tab_widget.active_tab() is None
        assert win._tab_widget.count() == 0
