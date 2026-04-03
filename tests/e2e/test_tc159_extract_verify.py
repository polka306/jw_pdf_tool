"""TC-159: 페이지 추출 -> 추출된 PDF 열기 -> 내용 확인."""

from __future__ import annotations

import fitz

from app.core import page_editor
from tests.helpers import load_pdf_directly


class TestTC159:
    """TC-159: 페이지 추출 -> 추출된 PDF 열기 -> 내용 확인."""

    def test_extracted_pdf_contains_correct_pages(
        self, main_window, pdf_factory, tmp_path
    ):
        win = main_window
        path = pdf_factory(
            num_pages=5,
            page_texts=["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
        )
        extract_path = str(tmp_path / "extracted.pdf")

        load_pdf_directly(win, path)

        # 1) 2~4페이지(idx 1,2,3) 추출
        page_editor.extract_pages(win._doc.raw, [1, 2, 3], extract_path)

        # 2) 추출된 PDF 검증
        extracted = fitz.open(extract_path)
        try:
            assert extracted.page_count == 3
            assert "Beta" in extracted[0].get_text()
            assert "Gamma" in extracted[1].get_text()
            assert "Delta" in extracted[2].get_text()
        finally:
            extracted.close()

        # 3) 원본은 변경되지 않았는지 확인
        assert win._doc.raw.page_count == 5

    def test_extract_single_page_content(self, main_window, pdf_factory, tmp_path):
        """단일 페이지 추출 후 내용 일치 확인."""
        win = main_window
        path = pdf_factory(num_pages=5, page_texts=["A", "B", "C", "D", "E"])
        extract_path = str(tmp_path / "single.pdf")

        load_pdf_directly(win, path)
        original_text = win._doc.raw[2].get_text().strip()

        page_editor.extract_pages(win._doc.raw, [2], extract_path)

        result = fitz.open(extract_path)
        try:
            assert result.page_count == 1
            assert result[0].get_text().strip() == original_text
        finally:
            result.close()
