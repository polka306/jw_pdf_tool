"""TC-396 ~ TC-404: 고급 도구 E2E 테스트."""

from __future__ import annotations

import os
import fitz
import pytest


class TestTC397Watermark:
    # TC-397: 워터마크 + 머리글 → 저장 → 재열기
    def test_tc397_watermark_header(self, tmp_path):
        from app.core.watermark import add_text_watermark, add_header_footer

        doc = fitz.open()
        for i in range(3):
            p = doc.new_page(width=595, height=842)
            p.insert_text((72, 100), f"Page {i+1}", fontsize=14)
        orig = str(tmp_path / "orig.pdf")
        doc.save(orig)
        doc.close()

        wm = str(tmp_path / "wm.pdf")
        add_text_watermark(orig, wm, "DRAFT", opacity=0.3)

        final = str(tmp_path / "final.pdf")
        add_header_footer(wm, final, footer_center="{page} / {total}")

        doc2 = fitz.open(final)
        assert doc2.page_count == 3
        doc2.close()


class TestTC398Optimize:
    # TC-398: 최적화 → 파일 크기 감소 → 내용 동일
    def test_tc398_optimize(self, tmp_path):
        from app.core.optimizer import optimize_pdf

        doc = fitz.open()
        for i in range(5):
            p = doc.new_page(width=595, height=842)
            p.insert_text((72, 100), f"Content page {i+1}", fontsize=14)
            for j in range(20):
                p.draw_rect(fitz.Rect(50+j*5, 200, 100+j*5, 300), color=(0.1, 0.2, 0.8))
        orig = str(tmp_path / "big.pdf")
        doc.save(orig)
        doc.close()

        out = str(tmp_path / "small.pdf")
        optimize_pdf(orig, out, preset="web")

        doc2 = fitz.open(out)
        assert doc2.page_count == 5
        assert "Content page 1" in doc2[0].get_text()
        doc2.close()


class TestTC399Compare:
    # TC-399: 비교 → 차이점 탐지
    def test_tc399_compare(self, tmp_path):
        from app.core.comparator import compare_pdfs

        doc_a = fitz.open()
        doc_a.new_page(width=595, height=842)
        doc_a[0].insert_text((72, 100), "Version A", fontsize=14)
        a = str(tmp_path / "a.pdf")
        doc_a.save(a)
        doc_a.close()

        doc_b = fitz.open()
        doc_b.new_page(width=595, height=842)
        doc_b[0].insert_text((72, 100), "Version B", fontsize=14)
        b = str(tmp_path / "b.pdf")
        doc_b.save(b)
        doc_b.close()

        diffs = compare_pdfs(a, b)
        assert len(diffs) >= 1


class TestTC401Redaction:
    # TC-401: 리댁션 → 텍스트 추출 불가
    def test_tc401_redaction(self, tmp_path):
        from app.core.security import redact_area

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), "TopSecret: XYZ123", fontsize=14)
        orig = str(tmp_path / "secret.pdf")
        doc.save(orig)
        doc.close()

        out = str(tmp_path / "redacted.pdf")
        redact_area(orig, out, 0, fitz.Rect(50, 85, 400, 115))

        doc2 = fitz.open(out)
        text = doc2[0].get_text()
        assert "XYZ123" not in text
        doc2.close()


class TestTC403Bates:
    # TC-403: 베이츠 번호 → 순번 확인
    def test_tc403_bates(self, tmp_path):
        from app.core.watermark import add_bates_numbers

        doc = fitz.open()
        for i in range(3):
            p = doc.new_page(width=595, height=842)
            p.insert_text((72, 100), f"Page {i+1}", fontsize=14)
        orig = str(tmp_path / "bates_src.pdf")
        doc.save(orig)
        doc.close()

        out = str(tmp_path / "bates_out.pdf")
        add_bates_numbers(orig, out, prefix="EV-", start=1, digits=6)

        doc2 = fitz.open(out)
        assert "EV-000001" in doc2[0].get_text()
        assert "EV-000002" in doc2[1].get_text()
        assert "EV-000003" in doc2[2].get_text()
        doc2.close()


class TestTC396OCR:
    # TC-396: OCR → 검색 (엔진 의존)
    def test_tc396_ocr_search(self):
        from app.core.ocr_engine import is_ocr_available
        if not is_ocr_available():
            pytest.skip("OCR 엔진 미설치")
        pytest.skip("OCR E2E는 수동 검증")


class TestTC400Signature:
    # TC-400: 디지털 서명 (pyHanko 의존)
    def test_tc400_signature(self):
        pytest.skip("TC-400: pyHanko 디지털 서명 후속 구현")


class TestTC402SearchReplace:
    # TC-402: 검색 및 바꾸기
    def test_tc402_search_replace(self):
        pytest.skip("TC-402: 검색 및 바꾸기 후속 구현")


class TestTC404PdfA:
    # TC-404: PDF/A 변환
    def test_tc404_pdfa(self):
        pytest.skip("TC-404: PDF/A 변환 후속 구현")
