"""TC-242: 열기→북마크 클릭→페이지 이동→텍스트 선택→복사."""

from __future__ import annotations

import os
import fitz
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestTC242BookmarkText:

    def test_tc242_bookmark_navigate_and_text(self, tmp_path):
        from app.core.search_engine import parse_bookmarks, extract_text_in_rect

        # 북마크 + 텍스트 PDF 생성
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 100), f"Chapter {i+1} content here", fontsize=14)
        toc = [[1, "Chapter 1", 1], [1, "Chapter 2", 2], [1, "Chapter 3", 3]]
        doc.set_toc(toc)
        pdf_path = str(tmp_path / "bm_text.pdf")
        doc.save(pdf_path)
        doc.close()

        # 북마크 파싱
        bookmarks = parse_bookmarks(pdf_path)
        assert len(bookmarks) == 3
        assert bookmarks[1].page_idx == 1  # Chapter 2

        # 해당 페이지 텍스트 추출
        text = extract_text_in_rect(pdf_path, 1, fitz.Rect(60, 85, 400, 115))
        assert "Chapter 2" in text
