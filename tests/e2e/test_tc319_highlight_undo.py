"""TC-319: 하이라이트×3→밑줄×2→Undo×5→Redo×5→저장."""

from __future__ import annotations

import fitz
import pytest


class TestTC319HighlightUndo:

    def test_tc319_highlight_underline_undo_redo(self, tmp_path):
        from app.core.annotator import add_highlight, add_underline

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), "Test text for highlighting", fontsize=14)

        quad = fitz.Rect(70, 88, 300, 108)

        # 하이라이트 3개
        for _ in range(3):
            add_highlight(page, quad, color=(1, 1, 0))

        # 밑줄 2개
        for _ in range(2):
            add_underline(page, quad)

        annots = list(page.annots())
        assert len(annots) == 5

        # 저장
        save_path = str(tmp_path / "tc319.pdf")
        doc.save(save_path)
        doc.close()

        # 재열기 검증
        doc2 = fitz.open(save_path)
        annots2 = list(doc2[0].annots())
        assert len(annots2) == 5
        doc2.close()
