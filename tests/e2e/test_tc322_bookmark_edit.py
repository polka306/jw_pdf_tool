"""TC-322: 북마크 추가×3→삭제×1→순서변경→저장→재열기→트리 확인."""

from __future__ import annotations

import fitz
import pytest


class TestTC322BookmarkEdit:

    def test_tc322_bookmark_edit_workflow(self, tmp_path):
        from app.core.search_engine import parse_bookmarks

        doc = fitz.open()
        for i in range(5):
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 100), f"Page {i+1}", fontsize=14)

        # 북마크 3개 추가
        toc = [
            [1, "Introduction", 1],
            [1, "Chapter 1", 2],
            [1, "Chapter 2", 4],
        ]
        doc.set_toc(toc)

        # 삭제: Chapter 1 제거
        toc = [t for t in toc if t[1] != "Chapter 1"]
        # 순서 변경: Chapter 2를 앞으로
        toc = [toc[1], toc[0]]  # Chapter 2, Introduction
        doc.set_toc(toc)

        save_path = str(tmp_path / "tc322.pdf")
        doc.save(save_path)
        doc.close()

        # 재열기 검증
        bm = parse_bookmarks(save_path)
        assert len(bm) == 2
        assert bm[0].title == "Chapter 2"
        assert bm[1].title == "Introduction"
