"""TC-158: 이미지 -> PDF 변환 -> 열기 -> 어노테이션 -> 저장."""

from __future__ import annotations

import os

import fitz

from app.core.converter import convert_images_to_pdf
from app.core.annotator import AnnotationStyle, add_text, add_rect
from tests.helpers import load_pdf_directly


class TestTC158:
    """TC-158: 이미지 -> PDF 변환 -> 열기 -> 어노테이션 -> 저장."""

    def test_converted_pdf_accepts_annotations(
        self, main_window, image_factory, tmp_path
    ):
        win = main_window
        img1 = image_factory("img1.png", color=(200, 100, 50))
        img2 = image_factory("img2.png", color=(50, 200, 100))
        img3 = image_factory("img3.png", color=(100, 50, 200))
        converted_path = str(tmp_path / "converted.pdf")
        save_path = str(tmp_path / "annotated_converted.pdf")

        # 1) 이미지 -> PDF 변환
        convert_images_to_pdf([img1, img2, img3], converted_path)
        assert os.path.exists(converted_path)

        # 2) 변환된 PDF 열기
        load_pdf_directly(win, converted_path)
        assert win._doc.page_count == 3

        # 3) 어노테이션 추가 전 상태 기록
        page_idx = 0
        before_drawings = len(win._doc.raw[page_idx].get_drawings())
        before_text = win._doc.raw[page_idx].get_text()

        # 4) 어노테이션 추가 (_on_annotation_requested 경유)
        style = AnnotationStyle()

        def annotate_text():
            add_text(win._doc.raw[page_idx], 50, 50, "Converted!", style)

        win._on_annotation_requested(annotate_text, "텍스트")

        def annotate_rect():
            add_rect(win._doc.raw[page_idx], 10, 70, 150, 130, style)

        win._on_annotation_requested(annotate_rect, "사각형")

        # 5) 저장 및 검증
        win._doc.save(save_path)

        verify_doc = fitz.open(save_path)
        try:
            assert verify_doc.page_count == 3
            page = verify_doc[0]
            assert "Converted!" in page.get_text(), "텍스트 어노테이션 미반영"
            assert "Converted!" not in before_text, "테스트 전제 실패"
            after_drawings = len(page.get_drawings())
            assert after_drawings > before_drawings, \
                f"사각형 어노테이션 미반영: before={before_drawings}, after={after_drawings}"
        finally:
            verify_doc.close()
