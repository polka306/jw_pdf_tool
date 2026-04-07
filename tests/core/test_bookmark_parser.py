"""TC-209 ~ TC-212: 북마크 파서 단위 테스트."""

from __future__ import annotations

import fitz
import pytest


def _make_pdf_with_bookmarks(tmp_path) -> str:
    """북마크가 있는 PDF 생성."""
    doc = fitz.open()
    for i in range(5):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Chapter {i + 1}", fontsize=24)

    # 북마크(아웃라인) 추가
    toc = [
        [1, "Chapter 1", 1],
        [1, "Chapter 2", 2],
        [2, "Section 2.1", 2],
        [2, "Section 2.2", 3],
        [1, "Chapter 3", 4],
        [2, "Section 3.1", 4],
        [3, "Subsection 3.1.1", 5],
    ]
    doc.set_toc(toc)
    path = str(tmp_path / "bookmarked.pdf")
    doc.save(path)
    doc.close()
    return path


def _make_pdf_no_bookmarks(tmp_path) -> str:
    """북마크 없는 PDF 생성."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 100), "No bookmarks", fontsize=24)
    path = str(tmp_path / "no_bookmarks.pdf")
    doc.save(path)
    doc.close()
    return path


class TestBookmarkParser:
    """core/search_engine.py 또는 별도 모듈 — 북마크 파싱."""

    # TC-209: 아웃라인 있는 PDF
    def test_tc209_parse_bookmarks(self, tmp_path):
        from app.core.search_engine import parse_bookmarks

        pdf_path = _make_pdf_with_bookmarks(tmp_path)
        bookmarks = parse_bookmarks(pdf_path)

        assert len(bookmarks) >= 3  # 최소 3개 최상위
        assert bookmarks[0].title == "Chapter 1"

    # TC-210: 아웃라인 없는 PDF
    def test_tc210_no_bookmarks(self, tmp_path):
        from app.core.search_engine import parse_bookmarks

        pdf_path = _make_pdf_no_bookmarks(tmp_path)
        bookmarks = parse_bookmarks(pdf_path)

        assert bookmarks == []

    # TC-211: 중첩 북마크 (3단계)
    def test_tc211_nested_bookmarks(self, tmp_path):
        from app.core.search_engine import parse_bookmarks

        pdf_path = _make_pdf_with_bookmarks(tmp_path)
        bookmarks = parse_bookmarks(pdf_path)

        # Chapter 2에 하위 항목이 있어야 함
        ch2 = [b for b in bookmarks if b.title == "Chapter 2"]
        assert len(ch2) == 1
        assert len(ch2[0].children) >= 2  # Section 2.1, 2.2

        # 3단계: Chapter 3 > Section 3.1 > Subsection 3.1.1
        ch3 = [b for b in bookmarks if b.title == "Chapter 3"]
        assert len(ch3) == 1
        assert len(ch3[0].children) >= 1  # Section 3.1
        assert len(ch3[0].children[0].children) >= 1  # Subsection 3.1.1

    # TC-212: 북마크 → 페이지 번호 매핑
    def test_tc212_bookmark_page_mapping(self, tmp_path):
        from app.core.search_engine import parse_bookmarks

        pdf_path = _make_pdf_with_bookmarks(tmp_path)
        bookmarks = parse_bookmarks(pdf_path)

        # Chapter 1 → page 0 (0-indexed)
        assert bookmarks[0].page_idx == 0
        # Chapter 2 → page 1
        assert bookmarks[1].page_idx == 1
