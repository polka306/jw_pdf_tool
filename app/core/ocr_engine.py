"""OCR 엔진 — Tesseract / Windows OCR 통합."""

from __future__ import annotations

import shutil
import sys


def is_ocr_available() -> bool:
    """OCR 엔진이 사용 가능한지 확인."""
    return _get_engine() != "none"


def get_ocr_engine_name() -> str:
    """사용 가능한 OCR 엔진 이름 반환."""
    return _get_engine()


def _get_engine() -> str:
    """사용 가능한 OCR 엔진 탐지."""
    # 1순위: Tesseract
    if shutil.which("tesseract"):
        return "tesseract"

    # 2순위: Windows OCR (winocr)
    if sys.platform == "win32":
        try:
            import winocr  # noqa: F401
            return "winocr"
        except ImportError:
            pass

    return "none"


def ocr_page(
    pdf_path: str,
    page_idx: int,
    *,
    lang: str = "eng",
    dpi: int = 300,
) -> str:
    """PDF 페이지에서 OCR로 텍스트 추출."""
    engine = _get_engine()

    if engine == "tesseract":
        return _ocr_tesseract(pdf_path, page_idx, lang=lang, dpi=dpi)
    elif engine == "winocr":
        return _ocr_winocr(pdf_path, page_idx, dpi=dpi)
    else:
        raise RuntimeError("OCR 엔진이 설치되어 있지 않습니다.")


def add_ocr_layer(
    input_path: str,
    output_path: str,
    *,
    lang: str = "eng",
    dpi: int = 300,
    page_indices: list[int] | None = None,
) -> None:
    """PDF에 OCR 텍스트 레이어 추가."""
    import fitz

    doc = fitz.open(input_path)
    indices = page_indices or list(range(len(doc)))

    for idx in indices:
        text = ocr_page(input_path, idx, lang=lang, dpi=dpi)
        if text.strip():
            page = doc[idx]
            # 투명 텍스트 레이어로 삽입
            page.insert_text(
                (72, 50),
                text,
                fontsize=1,  # 매우 작게 (비가시)
                color=(1, 1, 1),  # 흰색 (비가시)
                render_mode=3,  # 비가시 렌더
            )

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


def _ocr_tesseract(pdf_path: str, page_idx: int, *, lang: str, dpi: int) -> str:
    """Tesseract OCR."""
    import fitz
    import subprocess
    import tempfile
    import os

    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    img_path = tempfile.mktemp(suffix=".png")
    pix.save(img_path)
    doc.close()

    try:
        result = subprocess.run(
            ["tesseract", img_path, "-", "-l", lang],
            capture_output=True, text=True, timeout=60,
        )
        return result.stdout
    finally:
        try:
            os.unlink(img_path)
        except OSError:
            pass


def _ocr_winocr(pdf_path: str, page_idx: int, *, dpi: int) -> str:
    """Windows OCR (winocr)."""
    import fitz
    import asyncio

    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_bytes = pix.tobytes("png")
    doc.close()

    try:
        import winocr

        async def _recognize():
            result = await winocr.recognize_pil(img_bytes, lang="en")
            return result.text

        loop = asyncio.new_event_loop()
        text = loop.run_until_complete(_recognize())
        loop.close()
        return text
    except Exception:
        return ""
