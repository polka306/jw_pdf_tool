"""TC-378 ~ TC-379: 리댁션(민감정보 삭제) 단위 테스트."""

from __future__ import annotations

import fitz
import pytest


class TestRedaction:

    # TC-378: 영역 지정 → 검은 사각형 대체
    def test_tc378_redact_area(self, tmp_path):
        from app.core.security import redact_area

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), "Sensitive SSN: 123-45-6789", fontsize=14)
        path = str(tmp_path / "sensitive.pdf")
        doc.save(path)
        doc.close()

        out = str(tmp_path / "redacted.pdf")
        redact_area(path, out, 0, fitz.Rect(200, 85, 400, 110))

        doc2 = fitz.open(out)
        assert doc2.page_count == 1
        doc2.close()

    # TC-379: 텍스트 완전 삭제 확인
    def test_tc379_text_removed(self, tmp_path):
        from app.core.security import redact_area

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), "Secret: ABCDEF", fontsize=14)
        path = str(tmp_path / "secret.pdf")
        doc.save(path)
        doc.close()

        out = str(tmp_path / "redacted.pdf")
        redact_area(path, out, 0, fitz.Rect(50, 85, 400, 115))

        doc2 = fitz.open(out)
        text = doc2[0].get_text()
        assert "ABCDEF" not in text
        doc2.close()
