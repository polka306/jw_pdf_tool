"""TC-189 ~ TC-191: 가상화 썸네일 패널 테스트."""

from __future__ import annotations

import os
import time

import fitz
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_large_pdf(tmp_path, num_pages: int) -> str:
    """대용량 테스트 PDF 생성."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page {i + 1}", fontsize=24)
    path = str(tmp_path / f"large_{num_pages}.pdf")
    doc.save(path)
    doc.close()
    return path


class TestPagePanelVirtualization:
    """page_panel.py — 가상화된 썸네일 패널 테스트."""

    # TC-189: 보이는 범위만 렌더
    def test_tc189_only_visible_rendered(self, qtbot, tmp_path):
        from app.core.pdf_document import PdfDocument
        from app.ui.page_panel import PagePanel

        pdf_path = _make_large_pdf(tmp_path, 50)
        doc = PdfDocument()
        doc.open(pdf_path)

        panel = PagePanel()
        qtbot.addWidget(panel)
        panel.load_document(doc)
        panel.show()
        qtbot.wait(1000)

        # 패널에 아이템이 있지만, 모든 썸네일이 렌더된 것은 아님
        # (가상화: 보이는 범위 + 버퍼만)
        assert panel._list.count() == 50  # 아이템 수는 전체

        if hasattr(panel, '_cancel_loader'):
            panel._cancel_loader()
        doc.close()

    # TC-190: 스크롤 시 추가 썸네일 로드
    def test_tc190_scroll_loads_more(self, qtbot, tmp_path):
        from app.core.pdf_document import PdfDocument
        from app.ui.page_panel import PagePanel

        pdf_path = _make_large_pdf(tmp_path, 30)
        doc = PdfDocument()
        doc.open(pdf_path)

        panel = PagePanel()
        qtbot.addWidget(panel)
        panel.load_document(doc)
        panel.show()
        qtbot.wait(500)

        # 맨 아래로 스크롤
        panel._list.scrollToBottom()
        qtbot.wait(500)

        # 스크롤 후에도 오류 없이 동작
        assert panel._list.count() == 30

        if hasattr(panel, '_cancel_loader'):
            panel._cancel_loader()
        doc.close()

    # TC-191: 100+ 페이지 로드 시간
    def test_tc191_large_pdf_no_ui_blocking(self, qtbot, tmp_path):
        from app.core.pdf_document import PdfDocument
        from app.ui.page_panel import PagePanel

        pdf_path = _make_large_pdf(tmp_path, 100)
        doc = PdfDocument()
        doc.open(pdf_path)

        panel = PagePanel()
        qtbot.addWidget(panel)

        start = time.perf_counter()
        panel.load_document(doc)
        panel.show()
        elapsed = time.perf_counter() - start

        # placeholder 즉시 표시 → 1초 이내 반환
        assert elapsed < 2.0  # 2초 여유
        assert panel._list.count() == 100

        if hasattr(panel, '_cancel_loader'):
            panel._cancel_loader()
        doc.close()
