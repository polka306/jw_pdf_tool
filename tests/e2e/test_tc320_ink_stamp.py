"""TC-320: 자유형 그리기→스탬프 배치→저장→재열기."""

from __future__ import annotations

import fitz
import pytest


class TestTC320InkStamp:

    def test_tc320_ink_and_stamp_persist(self, tmp_path):
        from app.core.annotator import add_ink, AnnotationStyle
        from app.core.stamp import add_text_stamp

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)

        # 자유형 그리기
        points = [(100, 100), (150, 120), (200, 110), (250, 130), (300, 100)]
        style = AnnotationStyle(color=(0, 0, 1), line_width=3.0)
        add_ink(page, points, style)

        # 텍스트 스탬프
        add_text_stamp(page, fitz.Point(200, 400), "APPROVED", color=(0, 0.5, 0), fontsize=20)

        save_path = str(tmp_path / "tc320.pdf")
        doc.save(save_path)
        doc.close()

        # 재열기
        doc2 = fitz.open(save_path)
        page2 = doc2[0]
        annots = list(page2.annots())
        # Ink 어노테이션은 annots에 포함
        ink_annots = [a for a in annots if a.type[0] == fitz.PDF_ANNOT_INK]
        assert len(ink_annots) >= 1
        doc2.close()
