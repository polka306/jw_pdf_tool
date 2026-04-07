"""TC-217 ~ TC-220: 텍스트 선택 단위 테스트."""

from __future__ import annotations

import fitz
import pytest


def _make_text_pdf(tmp_path) -> str:
    """텍스트가 포함된 PDF 생성."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 100), "First line of text", fontsize=14)
    page.insert_text((72, 120), "Second line of text", fontsize=14)
    page.insert_text((72, 140), "Third line with 한글 텍스트", fontsize=14)
    path = str(tmp_path / "text_selection.pdf")
    doc.save(path)
    doc.close()
    return path


class TestTextSelection:
    """텍스트 선택/추출 기능 테스트."""

    # TC-217: 단일 행 텍스트 추출
    def test_tc217_single_line_extract(self, tmp_path):
        from app.core.search_engine import extract_text_in_rect

        pdf_path = _make_text_pdf(tmp_path)
        # "First line" 영역 대략적 좌표
        text = extract_text_in_rect(pdf_path, 0, fitz.Rect(60, 85, 300, 110))

        assert "First" in text

    # TC-218: 다중 행 텍스트 추출
    def test_tc218_multi_line_extract(self, tmp_path):
        from app.core.search_engine import extract_text_in_rect

        pdf_path = _make_text_pdf(tmp_path)
        # 여러 줄을 포함하는 넓은 영역
        text = extract_text_in_rect(pdf_path, 0, fitz.Rect(60, 85, 400, 155))

        assert "First" in text
        assert "Second" in text

    # TC-219: 빈 영역 선택
    def test_tc219_empty_area(self, tmp_path):
        from app.core.search_engine import extract_text_in_rect

        pdf_path = _make_text_pdf(tmp_path)
        # 텍스트 없는 영역
        text = extract_text_in_rect(pdf_path, 0, fitz.Rect(400, 400, 500, 500))

        assert text.strip() == ""

    # TC-220: 이미지 영역 선택
    def test_tc220_image_area(self, tmp_path):
        from app.core.search_engine import extract_text_in_rect

        # 이미지만 있는 PDF (텍스트 없음)
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.draw_rect(fitz.Rect(100, 100, 300, 300), color=(1, 0, 0), fill=(0, 0, 1))
        img_pdf = str(tmp_path / "image_only.pdf")
        doc.save(img_pdf)
        doc.close()

        text = extract_text_in_rect(img_pdf, 0, fitz.Rect(100, 100, 300, 300))
        assert text.strip() == ""
