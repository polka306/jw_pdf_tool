"""TC-262 ~ TC-264: PDF→이미지/텍스트 변환 테스트."""

from __future__ import annotations

import os
import fitz
import pytest


def _make_text_pdf(tmp_path) -> str:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 100), "Export test content page 1", fontsize=14)
    path = str(tmp_path / "export_test.pdf")
    doc.save(path)
    doc.close()
    return path


class TestPdfToImage:
    """converter.py — PDF→이미지 변환 테스트."""

    # TC-262: PNG 300DPI 내보내기
    def test_tc262_export_png_300dpi(self, tmp_path):
        from app.core.converter import export_pages_to_images

        pdf_path = _make_text_pdf(tmp_path)
        out_dir = str(tmp_path / "images")
        os.makedirs(out_dir)

        files = export_pages_to_images(pdf_path, out_dir, fmt="png", dpi=300)

        assert len(files) == 1
        assert files[0].endswith(".png")
        assert os.path.getsize(files[0]) > 0

    # TC-263: JPG 150DPI 내보내기
    def test_tc263_export_jpg_150dpi(self, tmp_path):
        from app.core.converter import export_pages_to_images

        pdf_path = _make_text_pdf(tmp_path)
        out_dir = str(tmp_path / "images_jpg")
        os.makedirs(out_dir)

        files = export_pages_to_images(pdf_path, out_dir, fmt="jpg", dpi=150)

        assert len(files) == 1
        assert files[0].endswith(".jpg")
        # JPG는 일반적으로 PNG보다 작음
        assert os.path.getsize(files[0]) > 0


class TestPdfToText:
    """converter.py — PDF→텍스트 추출 테스트."""

    # TC-264: 텍스트 추출
    def test_tc264_extract_text(self, tmp_path):
        from app.core.converter import export_pdf_to_text

        pdf_path = _make_text_pdf(tmp_path)
        out_path = str(tmp_path / "output.txt")

        export_pdf_to_text(pdf_path, out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Export test content" in content
