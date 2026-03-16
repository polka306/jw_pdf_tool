"""PdfDocument 단위 테스트."""

from __future__ import annotations

import pytest

from app.core.pdf_document import PdfDocument


class TestPdfDocumentOpen:
    def test_open_valid_file(self, pdf_3pages):
        doc = PdfDocument()
        doc.open(pdf_3pages)
        assert doc.is_open
        assert doc.page_count == 3
        assert doc.path == pdf_3pages
        doc.close()

    def test_open_invalid_file_raises(self, tmp_path):
        doc = PdfDocument()
        with pytest.raises(Exception):
            doc.open(str(tmp_path / "nonexistent.pdf"))

    def test_close_clears_state(self, pdf_3pages):
        doc = PdfDocument()
        doc.open(pdf_3pages)
        doc.close()
        assert not doc.is_open
        assert doc.page_count == 0
        assert doc.path is None

    def test_reopen_replaces_previous(self, pdf_3pages, pdf_5pages):
        doc = PdfDocument()
        doc.open(pdf_3pages)
        doc.open(pdf_5pages)
        assert doc.page_count == 5
        doc.close()


class TestPdfDocumentRender:
    def test_render_page_returns_bytes(self, open_doc):
        data = open_doc.render_page(0)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_render_page_png_header(self, open_doc):
        data = open_doc.render_page(0)
        # PNG 파일은 \x89PNG로 시작
        assert data[:4] == b"\x89PNG"

    def test_render_page_zoom_affects_size(self, open_doc):
        small = open_doc.render_page(0, zoom=0.5)
        large = open_doc.render_page(0, zoom=2.0)
        assert len(large) > len(small)

    def test_render_thumbnail_returns_bytes(self, open_doc):
        data = open_doc.render_page_thumbnail(0, thumb_width=100)
        assert isinstance(data, bytes)
        assert data[:4] == b"\x89PNG"

    def test_get_page_size_returns_positive(self, open_doc):
        w, h = open_doc.get_page_size(0)
        assert w > 0
        assert h > 0

    def test_requires_open_raises_when_closed(self):
        doc = PdfDocument()
        with pytest.raises(RuntimeError, match="열린 PDF 문서가 없습니다"):
            doc.render_page(0)


class TestPdfDocumentSave:
    def test_save_overwrites_original(self, open_doc, tmp_path):
        save_path = str(tmp_path / "saved.pdf")
        open_doc.save(save_path)
        # 저장된 파일이 다시 열리는지 확인
        doc2 = PdfDocument()
        doc2.open(save_path)
        assert doc2.page_count == open_doc.page_count
        doc2.close()

    def test_save_without_path_raises_if_no_original(self):
        doc = PdfDocument()
        # _doc가 None이므로 RuntimeError
        with pytest.raises(RuntimeError):
            doc.save()
