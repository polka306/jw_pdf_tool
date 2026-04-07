"""TC-173 ~ TC-175: 세대(generation) 카운터 단위 테스트."""

from __future__ import annotations

import pytest


class TestGenerationCounter:
    """PdfDocument 세대 카운터 확장 테스트."""

    # TC-173: 초기값 0
    def test_tc173_initial_generation_zero(self, pdf_3pages):
        from app.core.pdf_document import PdfDocument

        doc = PdfDocument()
        doc.open(pdf_3pages)

        for i in range(doc.page_count):
            assert doc.get_generation(i) == 0

        doc.close()

    # TC-174: 어노테이션 후 해당 페이지만 증가
    def test_tc174_increment_on_annotation(self, pdf_3pages):
        from app.core.pdf_document import PdfDocument

        doc = PdfDocument()
        doc.open(pdf_3pages)

        doc.increment_generation(1)  # 페이지 1만 증가

        assert doc.get_generation(0) == 0  # 변경 없음
        assert doc.get_generation(1) == 1  # 증가됨
        assert doc.get_generation(2) == 0  # 변경 없음

        doc.increment_generation(1)  # 한번 더
        assert doc.get_generation(1) == 2

        doc.close()

    # TC-175: 페이지 삭제 후 인덱스 재매핑
    def test_tc175_reindex_after_delete(self, pdf_5pages):
        from app.core.pdf_document import PdfDocument

        doc = PdfDocument()
        doc.open(pdf_5pages)

        # 페이지 2에 generation 설정
        doc.increment_generation(2)  # gen=1
        doc.increment_generation(2)  # gen=2
        doc.increment_generation(4)  # 페이지 4도 gen=1

        # 페이지 1 삭제 → 기존 페이지2는 인덱스1이 됨
        doc.reindex_generations_after_delete([1])

        # 기존 페이지2(gen=2)는 이제 인덱스1
        assert doc.get_generation(1) == 2
        # 기존 페이지4(gen=1)는 이제 인덱스3
        assert doc.get_generation(3) == 1

        doc.close()
