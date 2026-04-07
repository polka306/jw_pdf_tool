"""TC-355: 빈 PDF→양식 생성→저장→채우기→JSON 내보내기."""

from __future__ import annotations

import json
import fitz
import pytest


class TestTC355FormCreateExport:

    def test_tc355_create_fill_export(self, tmp_path):
        from app.core.form_handler import add_form_field, write_form_field, export_form_data

        # 빈 PDF
        doc = fitz.open()
        doc.new_page(width=595, height=842)
        blank = str(tmp_path / "blank.pdf")
        doc.save(blank)
        doc.close()

        # 양식 필드 생성
        with_field = str(tmp_path / "with_fields.pdf")
        add_form_field(blank, with_field, "company", "text", fitz.Rect(72, 100, 300, 125))

        # 필드 채우기
        filled = str(tmp_path / "filled.pdf")
        write_form_field(with_field, filled, "company", "Anthropic")

        # JSON 내보내기
        json_path = str(tmp_path / "export.json")
        export_form_data(filled, json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data.get("company") == "Anthropic"
