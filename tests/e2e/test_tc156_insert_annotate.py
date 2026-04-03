"""TC-156: 페이지 삽입 -> 삽입된 페이지에 어노테이션 -> 저장."""

from __future__ import annotations

import fitz

from app.core.annotator import AnnotationStyle, add_rect
from app.core.command_manager import InsertPagesCommand
from tests.helpers import load_pdf_directly


class TestTC156:
    """TC-156: 페이지 삽입 -> 삽입된 페이지에 어노테이션 -> 저장."""

    def test_annotation_on_inserted_page_persists(
        self, main_window, pdf_factory, tmp_path
    ):
        win = main_window
        main_pdf = pdf_factory(num_pages=2, page_texts=["Main1", "Main2"])
        source_pdf = pdf_factory(num_pages=3, page_texts=["Src1", "Src2", "Src3"])
        save_path = str(tmp_path / "inserted_annotated.pdf")

        load_pdf_directly(win, main_pdf)

        # 1) 페이지 삽입 (source의 0번 페이지를 main의 1번 앞에)
        cmd = InsertPagesCommand(win._doc.raw, source_pdf, [0], insert_before=1)
        win._cmd_mgr.execute(cmd)
        assert win._doc.raw.page_count == 3  # 2 + 1

        # 2) 삽입된 페이지(idx=1)에 어노테이션 추가
        style = AnnotationStyle(color=(0.0, 0.0, 1.0))
        inserted_idx = 1
        before_drawings = len(win._doc.raw[inserted_idx].get_drawings())

        def annotate():
            add_rect(win._doc.raw[inserted_idx], 50, 50, 200, 150, style)

        win._on_annotation_requested(annotate, "사각형")

        # 3) 저장 및 검증
        win._doc.save(save_path)

        verify_doc = fitz.open(save_path)
        try:
            assert verify_doc.page_count == 3
            inserted_page = verify_doc[1]
            assert len(inserted_page.get_drawings()) > before_drawings, \
                "삽입된 페이지에 어노테이션이 반영되지 않았음"
            assert "Src1" in inserted_page.get_text()
        finally:
            verify_doc.close()
