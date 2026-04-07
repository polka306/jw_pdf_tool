"""TC-279: 열기→회전→Undo→저장→재열기→rotation 확인."""

from __future__ import annotations

import os
import fitz
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestTC279RotateUndo:

    def test_tc279_rotate_save_reopen(self, tmp_path, pdf_3pages):
        from app.core.page_editor import rotate_page

        doc = fitz.open(pdf_3pages)
        assert doc[0].rotation == 0

        rotate_page(doc, 0, 90)
        assert doc[0].rotation == 90

        # Undo (역회전)
        rotate_page(doc, 0, -90)
        assert doc[0].rotation == 0

        # 90 회전 후 저장
        rotate_page(doc, 0, 90)
        save_path = str(tmp_path / "rotated.pdf")
        doc.save(save_path, garbage=4, deflate=True)
        doc.close()

        # 재열기
        doc2 = fitz.open(save_path)
        assert doc2[0].rotation == 90
        doc2.close()
