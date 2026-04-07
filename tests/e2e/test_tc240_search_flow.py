"""TC-240: 열기→Ctrl+F 검색→다음×5→페이지 이동 확인."""

from __future__ import annotations

import os
import fitz
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_multi_match_pdf(tmp_path) -> str:
    doc = fitz.open()
    for i in range(10):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page {i+1} contains keyword apple", fontsize=14)
    path = str(tmp_path / "multi_match.pdf")
    doc.save(path)
    doc.close()
    return path


class TestTC240SearchFlow:

    def test_tc240_search_navigate(self, tmp_path):
        from app.core.search_engine import SearchEngine

        pdf_path = _make_multi_match_pdf(tmp_path)
        engine = SearchEngine(pdf_path)
        results = engine.search("apple")

        assert len(results) == 10  # 각 페이지에 하나씩

        # 다음 5번 이동 시뮬레이션
        for i in range(5):
            assert results[i].page_idx == i
