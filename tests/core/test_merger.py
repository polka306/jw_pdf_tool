"""TC-250 ~ TC-258: PDF 병합/분할 단위 테스트."""

from __future__ import annotations

import os
import fitz
import pytest


def _make_pdf(tmp_path, pages, name="test") -> str:
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Doc-{name} Page {i+1}", fontsize=14)
    path = str(tmp_path / f"{name}_{pages}p.pdf")
    doc.save(path)
    doc.close()
    return path


class TestPdfMerge:
    """core/merger.py — PDF 병합 테스트."""

    # TC-250: 2개 PDF 병합
    def test_tc250_merge_two(self, tmp_path):
        from app.core.merger import merge_pdfs

        pdf_a = _make_pdf(tmp_path, 3, "A")
        pdf_b = _make_pdf(tmp_path, 2, "B")
        out = str(tmp_path / "merged.pdf")

        merge_pdfs([pdf_a, pdf_b], out)

        doc = fitz.open(out)
        assert doc.page_count == 5
        doc.close()

    # TC-251: 3개 이상 다중 파일 병합
    def test_tc251_merge_multiple(self, tmp_path):
        from app.core.merger import merge_pdfs

        pdfs = [_make_pdf(tmp_path, 2, f"F{i}") for i in range(4)]
        out = str(tmp_path / "merged_multi.pdf")

        merge_pdfs(pdfs, out)

        doc = fitz.open(out)
        assert doc.page_count == 8
        doc.close()

    # TC-252: 북마크 유지 옵션
    def test_tc252_merge_keep_bookmarks(self, tmp_path):
        from app.core.merger import merge_pdfs

        # 북마크 있는 PDF 생성
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 100), f"Ch {i+1}", fontsize=14)
        doc.set_toc([[1, "Chapter 1", 1], [1, "Chapter 2", 2]])
        pdf_bm = str(tmp_path / "with_bm.pdf")
        doc.save(pdf_bm)
        doc.close()

        pdf_plain = _make_pdf(tmp_path, 2, "plain")
        out = str(tmp_path / "merged_bm.pdf")

        merge_pdfs([pdf_bm, pdf_plain], out, keep_bookmarks=True)

        doc = fitz.open(out)
        toc = doc.get_toc()
        assert len(toc) >= 2  # 북마크 보존
        doc.close()

    # TC-253: 페이지 범위 지정 병합
    def test_tc253_merge_page_range(self, tmp_path):
        from app.core.merger import merge_pdfs

        pdf_a = _make_pdf(tmp_path, 5, "range")
        out = str(tmp_path / "merged_range.pdf")

        merge_pdfs([pdf_a], out, page_ranges=[(1, 3)])  # 페이지 1~3만

        doc = fitz.open(out)
        assert doc.page_count == 3
        doc.close()

    # TC-254: 빈 파일 목록 → 오류
    def test_tc254_merge_empty_list(self, tmp_path):
        from app.core.merger import merge_pdfs

        out = str(tmp_path / "empty.pdf")
        with pytest.raises(ValueError):
            merge_pdfs([], out)


class TestPdfSplit:
    """core/merger.py — PDF 분할 테스트."""

    # TC-255: N페이지 단위 분할
    def test_tc255_split_by_count(self, tmp_path):
        from app.core.merger import split_pdf

        pdf = _make_pdf(tmp_path, 9, "split")
        out_dir = str(tmp_path / "split_out")
        os.makedirs(out_dir)

        files = split_pdf(pdf, out_dir, pages_per_split=3)

        assert len(files) == 3
        for f in files:
            doc = fitz.open(f)
            assert doc.page_count == 3
            doc.close()

    # TC-256: 페이지 범위 지정 분할
    def test_tc256_split_by_range(self, tmp_path):
        from app.core.merger import split_pdf

        pdf = _make_pdf(tmp_path, 10, "split_range")
        out_dir = str(tmp_path / "split_range_out")
        os.makedirs(out_dir)

        files = split_pdf(pdf, out_dir, ranges=[(0, 2), (5, 7)])

        assert len(files) == 2
        doc1 = fitz.open(files[0])
        assert doc1.page_count == 3  # 0,1,2
        doc1.close()

    # TC-257: 북마크 기준 분할
    def test_tc257_split_by_bookmark(self, tmp_path):
        from app.core.merger import split_pdf

        # 북마크 PDF 생성
        doc = fitz.open()
        for i in range(6):
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 100), f"Section {i+1}", fontsize=14)
        doc.set_toc([[1, "Part A", 1], [1, "Part B", 4]])
        pdf = str(tmp_path / "bm_split.pdf")
        doc.save(pdf)
        doc.close()

        out_dir = str(tmp_path / "bm_split_out")
        os.makedirs(out_dir)

        files = split_pdf(pdf, out_dir, by_bookmarks=True)

        assert len(files) >= 2

    # TC-258: 1페이지 PDF 분할
    def test_tc258_split_single_page(self, tmp_path):
        from app.core.merger import split_pdf

        pdf = _make_pdf(tmp_path, 1, "single")
        out_dir = str(tmp_path / "single_out")
        os.makedirs(out_dir)

        files = split_pdf(pdf, out_dir, pages_per_split=1)

        assert len(files) == 1
