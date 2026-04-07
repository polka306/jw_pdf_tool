"""TC-321: 스티키 노트 추가→내용 입력→저장→재열기→내용 확인."""

from __future__ import annotations

import fitz
import pytest


class TestTC321StickyNote:

    def test_tc321_sticky_note_persist(self, tmp_path):
        from app.core.annotator import add_sticky_note

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)

        add_sticky_note(page, fitz.Point(200, 300), "Important note here!")

        save_path = str(tmp_path / "tc321.pdf")
        doc.save(save_path)
        doc.close()

        doc2 = fitz.open(save_path)
        annots = list(doc2[0].annots())
        assert len(annots) >= 1
        found = any("Important note here!" in a.info.get("content", "") for a in annots)
        assert found
        doc2.close()
