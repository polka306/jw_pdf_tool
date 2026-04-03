"""TC-155: PDF 열기 -> 어노테이션 추가 -> 저장 -> 재열기 확인."""

from __future__ import annotations

import fitz

from app.core.annotator import AnnotationStyle, add_text, add_rect, add_ellipse
from tests.helpers import load_pdf_directly


class TestTC155:
    """TC-155: PDF 열기 -> 어노테이션 추가 -> 저장 -> 재열기 확인."""

    def test_annotations_persist_after_save_and_reopen(
        self, main_window, pdf_factory, tmp_path
    ):
        win = main_window
        original_path = pdf_factory(num_pages=2)
        save_path = str(tmp_path / "annotated.pdf")

        # 1) 문서 로드
        load_pdf_directly(win, original_path)
        assert win._doc.is_open
        assert win._doc.page_count == 2

        # 2) 어노테이션 추가 전 drawings/text 기록 (상대적 비교용)
        page_idx = 0
        before_drawings = len(win._doc.raw[page_idx].get_drawings())
        before_text = win._doc.raw[page_idx].get_text()

        # 3) 텍스트 어노테이션 추가 (_on_annotation_requested 경유)
        style = AnnotationStyle(color=(1.0, 0.0, 0.0))

        def annotate_text():
            add_text(win._doc.raw[page_idx], 100, 200, "E2E Test", style)

        win._on_annotation_requested(annotate_text, "텍스트 추가")

        # 4) 사각형 어노테이션 추가
        def annotate_rect():
            add_rect(win._doc.raw[page_idx], 50, 300, 200, 400, style)

        win._on_annotation_requested(annotate_rect, "사각형 추가")

        # 5) 다른 이름으로 저장
        win._doc.save(save_path)

        # 6) 재열기하여 어노테이션 존재 확인 (fitz 직접 사용)
        verify_doc = fitz.open(save_path)
        try:
            page = verify_doc[0]

            # 상대적 비교: 추가 전보다 drawings가 증가했는지 확인
            after_drawings = len(page.get_drawings())
            assert after_drawings > before_drawings, \
                f"사각형 어노테이션 미반영: before={before_drawings}, after={after_drawings}"

            # 텍스트 어노테이션은 고유 문자열로 검증
            assert "E2E Test" in page.get_text(), "텍스트 어노테이션이 저장되지 않았음"
            assert "E2E Test" not in before_text, "테스트 전제 실패: 이미 텍스트가 존재"
        finally:
            verify_doc.close()

    def test_rect_and_ellipse_persist(self, main_window, pdf_factory, tmp_path):
        """사각형 + 타원 어노테이션이 저장/재열기 후에도 유지되는지 확인."""
        win = main_window
        path = pdf_factory(num_pages=1)
        save_path = str(tmp_path / "shapes.pdf")

        load_pdf_directly(win, path)

        style = AnnotationStyle()
        page_idx = 0
        before_drawings = len(win._doc.raw[page_idx].get_drawings())

        def add_rect_fn():
            add_rect(win._doc.raw[page_idx], 50, 50, 200, 150, style)

        def add_ellipse_fn():
            add_ellipse(win._doc.raw[page_idx], 250, 50, 450, 200, style)

        win._on_annotation_requested(add_rect_fn, "사각형")
        win._on_annotation_requested(add_ellipse_fn, "타원")

        win._doc.save(save_path)

        doc2 = fitz.open(save_path)
        try:
            after_drawings = len(doc2[page_idx].get_drawings())
            assert after_drawings >= before_drawings + 2, \
                f"사각형+타원 미반영: before={before_drawings}, after={after_drawings}"
        finally:
            doc2.close()
