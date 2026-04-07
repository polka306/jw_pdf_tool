"""TC-375 ~ TC-377: PDF 비교 단위 테스트."""

from __future__ import annotations

import fitz
import pytest


class TestPdfComparator:

    # TC-375: 동일 PDF → 차이 없음
    def test_tc375_identical_pdfs(self, tmp_path):
        from app.core.comparator import compare_pdfs

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), "Same content", fontsize=14)
        path = str(tmp_path / "same.pdf")
        doc.save(path)
        doc.close()

        diffs = compare_pdfs(path, path)
        assert len(diffs) == 0

    # TC-376: 텍스트 변경 → diff 결과
    def test_tc376_text_change(self, tmp_path):
        from app.core.comparator import compare_pdfs

        # PDF A
        doc_a = fitz.open()
        page_a = doc_a.new_page(width=595, height=842)
        page_a.insert_text((72, 100), "Original text here", fontsize=14)
        path_a = str(tmp_path / "a.pdf")
        doc_a.save(path_a)
        doc_a.close()

        # PDF B (다른 텍스트)
        doc_b = fitz.open()
        page_b = doc_b.new_page(width=595, height=842)
        page_b.insert_text((72, 100), "Modified text here", fontsize=14)
        path_b = str(tmp_path / "b.pdf")
        doc_b.save(path_b)
        doc_b.close()

        diffs = compare_pdfs(path_a, path_b)
        assert len(diffs) >= 1
        assert diffs[0].page_idx == 0

    # TC-377: 페이지 추가/삭제 감지
    def test_tc377_page_count_diff(self, tmp_path):
        from app.core.comparator import compare_pdfs

        # PDF A: 2페이지
        doc_a = fitz.open()
        for i in range(2):
            p = doc_a.new_page(width=595, height=842)
            p.insert_text((72, 100), f"Page {i+1}", fontsize=14)
        path_a = str(tmp_path / "2pages.pdf")
        doc_a.save(path_a)
        doc_a.close()

        # PDF B: 3페이지
        doc_b = fitz.open()
        for i in range(3):
            p = doc_b.new_page(width=595, height=842)
            p.insert_text((72, 100), f"Page {i+1}", fontsize=14)
        path_b = str(tmp_path / "3pages.pdf")
        doc_b.save(path_b)
        doc_b.close()

        diffs = compare_pdfs(path_a, path_b)
        # 페이지 수 차이가 diff에 포함
        assert any(d.diff_type == "page_count" for d in diffs)
