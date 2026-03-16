"""PdfViewer 위젯 테스트 (pytest-qt, offscreen 모드)."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt

from app.core.pdf_document import PdfDocument
from app.ui.pdf_viewer import PdfViewer


@pytest.fixture
def viewer(qtbot):
    """PdfViewer 인스턴스."""
    w = PdfViewer()
    qtbot.addWidget(w)
    return w


@pytest.fixture
def loaded_viewer(qtbot, pdf_3pages):
    """PDF가 로드된 PdfViewer."""
    doc = PdfDocument()
    doc.open(pdf_3pages)
    w = PdfViewer()
    qtbot.addWidget(w)
    w.set_document(doc)
    yield w, doc
    doc.close()


class TestPdfViewerInit:
    def test_initial_state(self, viewer):
        assert viewer.current_page == 0
        assert viewer.zoom == 1.5

    def test_clear_on_empty(self, viewer):
        viewer.clear()
        assert viewer.current_page == 0


class TestPdfViewerDocument:
    def test_set_document_shows_first_page(self, loaded_viewer):
        w, _ = loaded_viewer
        assert w.current_page == 0

    def test_goto_page_changes_current(self, loaded_viewer):
        w, _ = loaded_viewer
        w.goto_page(2)
        assert w.current_page == 2

    def test_goto_page_out_of_range_ignored(self, loaded_viewer):
        w, _ = loaded_viewer
        w.goto_page(0)
        w.goto_page(99)  # 범위 초과
        assert w.current_page == 0

    def test_page_changed_signal(self, loaded_viewer, qtbot):
        w, _ = loaded_viewer
        with qtbot.waitSignal(w.page_changed, timeout=1000) as blocker:
            w.goto_page(1)
        assert blocker.args == [1]


class TestPdfViewerZoom:
    def test_zoom_in_increases_zoom(self, loaded_viewer):
        w, _ = loaded_viewer
        before = w.zoom
        w.zoom_in()
        assert w.zoom > before

    def test_zoom_out_decreases_zoom(self, loaded_viewer):
        w, _ = loaded_viewer
        before = w.zoom
        w.zoom_out()
        assert w.zoom < before

    def test_zoom_clamped_to_min(self, loaded_viewer):
        w, _ = loaded_viewer
        w.set_zoom(0.001)
        assert w.zoom == PdfViewer.MIN_ZOOM

    def test_zoom_clamped_to_max(self, loaded_viewer):
        w, _ = loaded_viewer
        w.set_zoom(999.0)
        assert w.zoom == PdfViewer.MAX_ZOOM

    def test_zoom_changed_signal(self, loaded_viewer, qtbot):
        w, _ = loaded_viewer
        with qtbot.waitSignal(w.zoom_changed, timeout=1000):
            w.zoom_in()
