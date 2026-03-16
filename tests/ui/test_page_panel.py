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


class TestPagePanelThumbnailFixes:
    """썸네일 관련 버그 수정 검증 테스트."""

    def test_icon_size_at_least_thumb_width(self, loaded_panel):
        """setIconSize 누락 버그 수정: 아이콘 크기가 THUMB_WIDTH 이상이어야 합니다."""
        from app.ui.page_panel import THUMB_WIDTH
        w, _ = loaded_panel
        icon_w = w._list.iconSize().width()
        assert icon_w >= THUMB_WIDTH, (
            f"iconSize().width()={icon_w} < THUMB_WIDTH={THUMB_WIDTH} "
            f"— setIconSize 미설정으로 16×16 고정되는 버그가 재발했을 수 있습니다."
        )

    def test_placeholder_items_appear_immediately_on_load(self, qtbot, pdf_3pages):
        """load_document 호출 직후 아이템이 즉시 생성되어야 합니다 (백그라운드 로딩)."""
        doc = PdfDocument()
        doc.open(pdf_3pages)
        w = PagePanel()
        qtbot.addWidget(w)
        w.load_document(doc)
        # 썸네일 로딩 완료 전에도 아이템 수 = 페이지 수여야 함
        assert w._list.count() == doc.page_count
        doc.close()

    def test_reload_page_keeps_item_count(self, loaded_panel):
        """reload_page 호출 후 아이템 수가 변하지 않아야 합니다."""
        w, doc = loaded_panel
        before = w._list.count()
        w.reload_page(0)
        assert w._list.count() == before

    def test_reload_page_preserves_text(self, loaded_panel):
        """reload_page 호출 후 페이지 번호 텍스트가 유지되어야 합니다."""
        w, _ = loaded_panel
        text_before = w._list.item(1).text()
        w.reload_page(1)
        assert w._list.item(1).text() == text_before

    def test_reload_page_out_of_range_no_crash(self, loaded_panel):
        """범위 밖 인덱스로 reload_page를 호출해도 크래시가 없어야 합니다."""
        w, _ = loaded_panel
        w.reload_page(999)  # should silently do nothing
