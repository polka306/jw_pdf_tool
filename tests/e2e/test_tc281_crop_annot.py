"""TC-281: 열기→크롭→어노테이션→저장→재열기."""

from __future__ import annotations

import os
import fitz
import pytest


class TestTC281CropAnnot:

    def test_tc281_crop_then_annotate_save(self, tmp_path, pdf_3pages):
        from app.core.page_editor import crop_page
        from app.core.annotator import add_rect, AnnotationStyle

        doc = fitz.open(pdf_3pages)

        # 크롭
        crop_page(doc, 0, fitz.Rect(50, 50, 400, 600))
        assert doc[0].cropbox.width < doc[0].mediabox.width

        # 어노테이션
        style = AnnotationStyle(color=(1, 0, 0), line_width=2.0)
        add_rect(doc[0], 60, 60, 200, 150, style)

        # 저장
        save_path = str(tmp_path / "crop_annot.pdf")
        doc.save(save_path, garbage=4, deflate=True)
        doc.close()

        # 재열기
        doc2 = fitz.open(save_path)
        assert doc2[0].cropbox.width < doc2[0].mediabox.width
        drawings = doc2[0].get_drawings()
        assert len(drawings) > 0
        doc2.close()
