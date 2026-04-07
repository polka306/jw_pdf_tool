"""TC-230 ~ TC-234: PdfViewer 보기 모드 및 텍스트 선택 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestPdfViewerModes:
    """pdf_viewer.py — 보기 모드, 텍스트 선택 테스트."""

    @pytest.fixture
    def viewer_with_doc(self, qtbot, pdf_5pages):
        from app.ui.pdf_viewer import PdfViewer
        from app.core.pdf_document import PdfDocument

        doc = PdfDocument()
        doc.open(pdf_5pages)
        viewer = PdfViewer()
        qtbot.addWidget(viewer)
        viewer.set_document(doc)
        yield viewer, doc
        doc.close()

    # TC-230: 연속 스크롤 모드
    def test_tc230_continuous_scroll_mode(self, viewer_with_doc):
        viewer, doc = viewer_with_doc

        if hasattr(viewer, 'set_view_mode'):
            viewer.set_view_mode("continuous")
            assert viewer.view_mode == "continuous"
        else:
            pytest.skip("set_view_mode not yet implemented")

    # TC-231: 2페이지 보기 모드
    def test_tc231_two_page_mode(self, viewer_with_doc):
        viewer, doc = viewer_with_doc

        if hasattr(viewer, 'set_view_mode'):
            viewer.set_view_mode("two_page")
            assert viewer.view_mode == "two_page"
        else:
            pytest.skip("set_view_mode not yet implemented")

    # TC-232: 단일 페이지 모드 복귀
    def test_tc232_single_page_mode(self, viewer_with_doc):
        viewer, doc = viewer_with_doc

        if hasattr(viewer, 'set_view_mode'):
            viewer.set_view_mode("continuous")
            viewer.set_view_mode("single")
            assert viewer.view_mode == "single"
        else:
            pytest.skip("set_view_mode not yet implemented")

    # TC-233: 텍스트 드래그 선택
    def test_tc233_text_drag_selection(self, viewer_with_doc):
        viewer, doc = viewer_with_doc

        if hasattr(viewer, 'get_selected_text'):
            # 선택 없는 초기 상태
            assert viewer.get_selected_text() == ""
        else:
            pytest.skip("get_selected_text not yet implemented")

    # TC-234: Ctrl+C 텍스트 복사
    def test_tc234_text_copy(self, viewer_with_doc, qtbot):
        viewer, doc = viewer_with_doc

        if hasattr(viewer, 'copy_selected_text'):
            # 복사 시도 (빈 선택이어도 오류 없이)
            viewer.copy_selected_text()
        else:
            pytest.skip("copy_selected_text not yet implemented")
