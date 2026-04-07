"""TC-259 ~ TC-261: 페이지 크롭 단위 테스트."""

from __future__ import annotations

import fitz
import pytest


class TestPageCrop:
    """page_editor.py — 페이지 크롭 테스트."""

    @pytest.fixture
    def doc3(self, pdf_3pages):
        doc = fitz.open(pdf_3pages)
        yield doc
        doc.close()

    # TC-259: CropBox 설정
    def test_tc259_set_cropbox(self, doc3):
        from app.core.page_editor import crop_page

        crop_page(doc3, 0, fitz.Rect(50, 50, 400, 600))

        page = doc3[0]
        cropbox = page.cropbox
        assert abs(cropbox.x0 - 50) < 1
        assert abs(cropbox.y0 - 50) < 1
        assert abs(cropbox.x1 - 400) < 1
        assert abs(cropbox.y1 - 600) < 1

    # TC-260: 원본 MediaBox 보존
    def test_tc260_mediabox_preserved(self, doc3):
        from app.core.page_editor import crop_page

        original_mediabox = doc3[0].mediabox
        crop_page(doc3, 0, fitz.Rect(50, 50, 400, 600))

        # MediaBox는 변경되지 않아야 함
        page = doc3[0]
        assert abs(page.mediabox.width - original_mediabox.width) < 1
        assert abs(page.mediabox.height - original_mediabox.height) < 1

    # TC-261: Undo → CropBox 복원
    def test_tc261_crop_undo(self, doc3):
        from app.core.page_editor import crop_page, reset_cropbox

        original_cropbox = doc3[0].cropbox
        crop_page(doc3, 0, fitz.Rect(100, 100, 300, 400))

        # 크롭 해제
        reset_cropbox(doc3, 0)

        page = doc3[0]
        assert abs(page.cropbox.width - original_cropbox.width) < 1
