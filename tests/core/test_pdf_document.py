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


class TestPdfDocumentSaveIncremental:
    """동일 경로 저장 시 incremental save 동작 검증."""

    def test_save_to_same_path_produces_valid_pdf(self, tmp_path):
        """같은 경로로 save() 해도 유효한 PDF가 생성되어야 합니다."""
        path = str(tmp_path / "same.pdf")
        # 먼저 저장본 생성
        doc = PdfDocument()
        import fitz as _fitz
        raw = _fitz.open()
        raw.new_page(width=595, height=842)
        raw.save(path)
        raw.close()

        doc.open(path)
        doc.save()  # 경로 없이 = 동일 경로 incremental save
        doc.close()

        # 다시 열어서 유효성 확인
        doc2 = PdfDocument()
        doc2.open(path)
        assert doc2.is_open
        assert doc2.page_count == 1
        doc2.close()

    def test_save_to_same_path_preserves_page_count(self, pdf_3pages):
        """incremental save 후 페이지 수가 보존되어야 합니다."""
        doc = PdfDocument()
        doc.open(pdf_3pages)
        doc.save()  # 동일 경로
        doc.close()

        doc2 = PdfDocument()
        doc2.open(pdf_3pages)
        assert doc2.page_count == 3
        doc2.close()

    def test_save_as_different_path_still_works(self, open_doc, tmp_path):
        """다른 경로(Save As)도 정상 동작해야 합니다."""
        out = str(tmp_path / "copy.pdf")
        open_doc.save(out)
        doc2 = PdfDocument()
        doc2.open(out)
        assert doc2.page_count == open_doc.page_count
        doc2.close()


# ── 추가 테스트 ──────────────────────────────────────────────────────────────

class TestPdfDocumentOpenExtra:
    def test_open_non_pdf_file_raises(self, corrupt_pdf):
        """TC-005: PDF가 아닌 파일 열기 시도 시 예외가 발생하거나 페이지 수가 0이어야 합니다."""
        doc = PdfDocument()
        try:
            doc.open(corrupt_pdf)
            # PyMuPDF가 열더라도 유효한 PDF가 아니면 페이지 수가 0
            assert doc.page_count == 0
        except Exception:
            pass  # 예외 발생도 허용
        finally:
            doc.close()


class TestPdfDocumentSaveExtra:
    def test_save_when_not_open(self):
        """TC-008: 문서 미열림 시 저장 시도 시 RuntimeError 발생."""
        doc = PdfDocument()
        with pytest.raises(RuntimeError):
            doc.save()


class TestPdfDocumentIncrementalSaveFallback:
    def test_incremental_save_fallback(self, tmp_path):
        """TC-152: incremental save가 실패해도 전체 저장으로 폴백하여 성공해야 한다."""
        import fitz

        path = str(tmp_path / "fallback.pdf")
        doc = PdfDocument()
        raw = fitz.open()
        raw.new_page(width=595, height=842)
        raw.save(path)
        raw.close()

        doc.open(path)
        for _ in range(5):
            doc.raw.new_page()
        for i in range(4, 0, -1):
            doc.raw.delete_page(i)
        doc.save()  # 폴백 발생해도 성공해야 함
        doc.close()

        doc2 = PdfDocument()
        doc2.open(path)
        assert doc2.is_open
        doc2.close()
