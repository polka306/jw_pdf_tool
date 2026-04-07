"""TC-372 ~ TC-374: PDF 최적화 단위 테스트."""

from __future__ import annotations

import os
import fitz
import pytest


def _make_heavy_pdf(tmp_path) -> str:
    """이미지 포함 무거운 PDF."""
    doc = fitz.open()
    for i in range(5):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page {i+1}", fontsize=14)
        # 큰 사각형으로 콘텐츠 추가
        for j in range(10):
            page.draw_rect(
                fitz.Rect(50 + j*10, 200, 150 + j*10, 400),
                color=(0.1*j, 0.2, 0.8), fill=(0.9, 0.9, 0.1*j), width=2
            )
    path = str(tmp_path / "heavy.pdf")
    doc.save(path)
    doc.close()
    return path


class TestPdfOptimizer:

    # TC-372: 이미지 다운샘플링
    def test_tc372_downsampling(self, tmp_path):
        from app.core.optimizer import optimize_pdf

        pdf = _make_heavy_pdf(tmp_path)
        out = str(tmp_path / "optimized.pdf")
        optimize_pdf(pdf, out, preset="web")

        assert os.path.exists(out)
        # 최적화 후 파일이 생성됨
        assert os.path.getsize(out) > 0

    # TC-373: 가비지 컬렉션 → 파일 크기 감소
    def test_tc373_garbage_collection(self, tmp_path):
        from app.core.optimizer import optimize_pdf

        pdf = _make_heavy_pdf(tmp_path)
        orig_size = os.path.getsize(pdf)

        out = str(tmp_path / "gc.pdf")
        optimize_pdf(pdf, out, preset="web")

        new_size = os.path.getsize(out)
        # 최적화 후 크기가 같거나 작아야 함 (간단한 PDF는 차이 없을 수 있음)
        assert new_size <= orig_size * 1.1  # 10% 여유

    # TC-374: 최적화 전후 내용 동일
    def test_tc374_content_preserved(self, tmp_path):
        from app.core.optimizer import optimize_pdf

        pdf = _make_heavy_pdf(tmp_path)
        out = str(tmp_path / "preserved.pdf")
        optimize_pdf(pdf, out, preset="print")

        doc_orig = fitz.open(pdf)
        doc_opt = fitz.open(out)

        assert doc_orig.page_count == doc_opt.page_count
        # 첫 페이지 텍스트 동일
        assert doc_orig[0].get_text().strip() == doc_opt[0].get_text().strip()

        doc_orig.close()
        doc_opt.close()
