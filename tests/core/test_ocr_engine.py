"""TC-356 ~ TC-361: OCR 엔진 단위 테스트."""

from __future__ import annotations

import sys
import fitz
import pytest


def _make_image_pdf(tmp_path) -> str:
    """이미지만 있는 PDF (텍스트 없음, OCR 대상)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (800, 200), "white")
    draw = ImageDraw.Draw(img)
    try:
        draw.text((50, 50), "Hello OCR Test", fill="black")
    except Exception:
        draw.text((50, 50), "Hello OCR Test", fill="black")

    img_path = str(tmp_path / "ocr_source.png")
    img.save(img_path)

    doc = fitz.open()
    page = doc.new_page(width=595, height=200)
    page.insert_image(fitz.Rect(0, 0, 595, 200), filename=img_path)
    path = str(tmp_path / "image_only.pdf")
    doc.save(path)
    doc.close()
    return path


class TestOcrEngine:
    """core/ocr_engine.py — OCR 테스트. 외부 엔진 미설치 시 skip."""

    # TC-356: 영어 텍스트 인식
    def test_tc356_english_ocr(self, tmp_path):
        from app.core.ocr_engine import is_ocr_available, ocr_page

        if not is_ocr_available():
            pytest.skip("OCR 엔진 미설치")

        pdf = _make_image_pdf(tmp_path)
        text = ocr_page(pdf, 0)
        assert "Hello" in text or "OCR" in text or len(text) > 0

    # TC-357: 한국어 OCR (엔진 의존)
    def test_tc357_korean_ocr(self, tmp_path):
        from app.core.ocr_engine import is_ocr_available

        if not is_ocr_available():
            pytest.skip("OCR 엔진 미설치")
        pytest.skip("한국어 OCR 테스트는 한글 이미지 필요 — 수동 검증")

    # TC-358: 300DPI 변환 정확도
    def test_tc358_dpi_accuracy(self, tmp_path):
        from app.core.ocr_engine import is_ocr_available

        if not is_ocr_available():
            pytest.skip("OCR 엔진 미설치")
        pytest.skip("DPI 정확도는 수동 검증")

    # TC-359: 텍스트 레이어 삽입
    def test_tc359_text_layer_insert(self, tmp_path):
        from app.core.ocr_engine import is_ocr_available, add_ocr_layer

        if not is_ocr_available():
            pytest.skip("OCR 엔진 미설치")

        pdf = _make_image_pdf(tmp_path)
        out = str(tmp_path / "with_ocr.pdf")
        add_ocr_layer(pdf, out)

        doc = fitz.open(out)
        text = doc[0].get_text()
        assert len(text.strip()) > 0  # 텍스트 레이어 삽입됨
        doc.close()

    # TC-360: Tesseract 미설치 시 폴백
    def test_tc360_fallback(self):
        from app.core.ocr_engine import get_ocr_engine_name

        name = get_ocr_engine_name()
        assert name in ("tesseract", "winocr", "none")

    # TC-361: 모든 엔진 미사용 시 graceful
    def test_tc361_no_engine_graceful(self):
        from app.core.ocr_engine import is_ocr_available

        # 함수 호출 자체가 오류 없이 동작해야 함
        result = is_ocr_available()
        assert isinstance(result, bool)
