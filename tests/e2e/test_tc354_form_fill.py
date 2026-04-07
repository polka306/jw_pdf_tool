"""TC-354: 양식 PDF 열기→필드 채우기→저장→재열기→값 확인."""

from __future__ import annotations

import fitz
import pytest


class TestTC354FormFill:

    def test_tc354_fill_form_and_verify(self, tmp_path):
        from app.core.form_handler import read_form_fields, write_form_field

        # 양식 PDF 생성
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        w = fitz.Widget()
        w.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        w.field_name = "username"
        w.field_value = ""
        w.rect = fitz.Rect(72, 100, 300, 125)
        page.add_widget(w)
        path = str(tmp_path / "form.pdf")
        doc.save(path)
        doc.close()

        # 필드 채우기
        filled = str(tmp_path / "filled.pdf")
        write_form_field(path, filled, "username", "testuser")

        # 재열기 확인
        fields = read_form_fields(filled)
        username = [f for f in fields if f.name == "username"]
        assert len(username) == 1
        assert username[0].value == "testuser"
