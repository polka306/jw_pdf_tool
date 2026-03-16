"""PagePanel 위젯 테스트."""

from __future__ import annotations

import pytest

from app.core.pdf_document import PdfDocument
from app.ui.page_panel import PagePanel


@pytest.fixture
def panel(qtbot):
    w = PagePanel()
    qtbot.addWidget(w)
    return w


@pytest.fixture
def loaded_panel(qtbot, pdf_3pages):
    doc = PdfDocument()
    doc.open(pdf_3pages)
    w = PagePanel()
    qtbot.addWidget(w)
    w.load_document(doc)
    yield w, doc
    doc.close()


class TestPagePanelLoad:
    def test_load_shows_correct_item_count(self, loaded_panel):
        w, doc = loaded_panel
        assert w._list.count() == doc.page_count

    def test_first_item_selected_after_load(self, loaded_panel):
        w, _ = loaded_panel
        assert w._list.currentRow() == 0

    def test_clear_removes_items(self, loaded_panel):
        w, _ = loaded_panel
        w.clear()
        assert w._list.count() == 0


class TestPagePanelNavigation:
    def test_set_current_page_no_signal(self, loaded_panel, qtbot):
        w, _ = loaded_panel
        # set_current_page는 시그널을 발생시키지 않아야 함
        signals_received = []
        w.page_selected.connect(lambda idx: signals_received.append(idx))
        w.set_current_page(2)
        assert w._list.currentRow() == 2
        assert signals_received == []

    def test_selected_indices_single(self, loaded_panel):
        w, _ = loaded_panel
        w._list.setCurrentRow(1)
        assert w.selected_indices() == [1]

    def test_page_selected_signal_on_click(self, loaded_panel, qtbot):
        w, _ = loaded_panel
        with qtbot.waitSignal(w.page_selected, timeout=1000) as blocker:
            w._list.setCurrentRow(2)
        assert blocker.args == [2]


class TestPagePanelReload:
    def test_reload_preserves_selection(self, loaded_panel):
        w, _ = loaded_panel
        w._list.setCurrentRow(1)
        w.reload_all()
        assert w._list.currentRow() == 1

    def test_reload_after_page_count_change(self, qtbot, pdf_3pages, tmp_path):
        import fitz
        doc = PdfDocument()
        doc.open(pdf_3pages)
        w = PagePanel()
        qtbot.addWidget(w)
        w.load_document(doc)

        # 문서에서 페이지 하나 삭제 후 reload
        doc.raw.delete_page(2)
        w.reload_all()
        assert w._list.count() == 2
        doc.close()
