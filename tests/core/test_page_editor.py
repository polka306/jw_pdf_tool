"""page_editor 단위 테스트."""

from __future__ import annotations

import os

import fitz
import pytest

from app.core import page_editor
from app.core.pdf_document import PdfDocument


@pytest.fixture
def raw_doc(pdf_5pages):
    """fitz.Document를 직접 반환합니다 (page_editor는 raw doc을 받음)."""
    doc = fitz.open(pdf_5pages)
    yield doc
    doc.close()


class TestMovePage:
    def test_move_forward(self, raw_doc):
        # 0→2: PyMuPDF move_page(0, 2)는 원본 인덱스 기준으로 삽입
        # [P0,P1,P2,P3,P4] → P0 제거 후 원본 위치 2 앞에 삽입 → [P1,P0,P2,P3,P4]
        # 즉 P0은 최종적으로 index 1에 위치함
        original_text = raw_doc[0].get_text()
        page_editor.move_page(raw_doc, 0, 2)
        assert raw_doc[1].get_text() == original_text

    def test_move_backward(self, raw_doc):
        original_text = raw_doc[4].get_text()
        page_editor.move_page(raw_doc, 4, 1)
        assert raw_doc[1].get_text() == original_text

    def test_move_same_position_no_change(self, raw_doc):
        original_text = raw_doc[2].get_text()
        page_editor.move_page(raw_doc, 2, 2)
        assert raw_doc[2].get_text() == original_text

    def test_page_count_unchanged_after_move(self, raw_doc):
        before = len(raw_doc)
        page_editor.move_page(raw_doc, 0, 3)
        assert len(raw_doc) == before


class TestDeletePages:
    def test_delete_single_page(self, raw_doc):
        before = len(raw_doc)
        page_editor.delete_pages(raw_doc, [0])
        assert len(raw_doc) == before - 1

    def test_delete_multiple_pages(self, raw_doc):
        before = len(raw_doc)
        page_editor.delete_pages(raw_doc, [0, 2, 4])
        assert len(raw_doc) == before - 3

    def test_delete_empty_list_no_change(self, raw_doc):
        before = len(raw_doc)
        page_editor.delete_pages(raw_doc, [])
        assert len(raw_doc) == before

    def test_delete_preserves_other_pages(self, raw_doc):
        # 페이지 1(index 1) 텍스트 기억 후 0번 삭제 → 새 0번이 예전 1번이어야 함
        text_p1 = raw_doc[1].get_text()
        page_editor.delete_pages(raw_doc, [0])
        assert raw_doc[0].get_text() == text_p1


class TestExtractPages:
    def test_extract_creates_file(self, raw_doc, tmp_path):
        out = str(tmp_path / "extracted.pdf")
        page_editor.extract_pages(raw_doc, [0, 2], out)
        assert os.path.exists(out)

    def test_extract_correct_page_count(self, raw_doc, tmp_path):
        out = str(tmp_path / "extracted.pdf")
        page_editor.extract_pages(raw_doc, [0, 1, 2], out)
        result = fitz.open(out)
        assert len(result) == 3
        result.close()

    def test_extract_single_page(self, raw_doc, tmp_path):
        out = str(tmp_path / "single.pdf")
        text_p2 = raw_doc[2].get_text()
        page_editor.extract_pages(raw_doc, [2], out)
        result = fitz.open(out)
        assert len(result) == 1
        assert result[0].get_text() == text_p2
        result.close()

    def test_extract_deduplicates_indices(self, raw_doc, tmp_path):
        out = str(tmp_path / "dedup.pdf")
        page_editor.extract_pages(raw_doc, [0, 0, 1], out)
        result = fitz.open(out)
        assert len(result) == 2  # 0, 1만
        result.close()


class TestInsertPagesFromFile:
    def test_insert_at_beginning(self, raw_doc, pdf_3pages, tmp_path):
        before_count = len(raw_doc)
        page_editor.insert_pages_from_file(raw_doc, pdf_3pages, [0, 1], insert_before=0)
        assert len(raw_doc) == before_count + 2

    def test_insert_at_end(self, raw_doc, pdf_3pages):
        before_count = len(raw_doc)
        page_editor.insert_pages_from_file(
            raw_doc, pdf_3pages, [0], insert_before=before_count
        )
        assert len(raw_doc) == before_count + 1

    def test_insert_in_middle(self, raw_doc, pdf_3pages):
        before_count = len(raw_doc)
        page_editor.insert_pages_from_file(raw_doc, pdf_3pages, [0, 1, 2], insert_before=2)
        assert len(raw_doc) == before_count + 3

    def test_inserted_content_is_correct(self, raw_doc, pdf_3pages):
        src = fitz.open(pdf_3pages)
        src_text = src[0].get_text()
        src.close()

        page_editor.insert_pages_from_file(raw_doc, pdf_3pages, [0], insert_before=0)
        assert raw_doc[0].get_text() == src_text
