"""PDF 양식(Form) 핸들러 — 필드 읽기/쓰기/생성/내보내기."""

from __future__ import annotations

import json
from dataclasses import dataclass

import fitz


# ── 양식 필드 데이터 ──────────────────────────────────────────────────────────

_TYPE_MAP = {
    fitz.PDF_WIDGET_TYPE_TEXT: "text",
    fitz.PDF_WIDGET_TYPE_CHECKBOX: "checkbox",
    fitz.PDF_WIDGET_TYPE_COMBOBOX: "combobox",
    fitz.PDF_WIDGET_TYPE_LISTBOX: "listbox",
    fitz.PDF_WIDGET_TYPE_RADIOBUTTON: "radiobutton",
}

# 일부 버전에서 없을 수 있는 상수
if hasattr(fitz, "PDF_WIDGET_TYPE_PUSHBUTTON"):
    _TYPE_MAP[fitz.PDF_WIDGET_TYPE_PUSHBUTTON] = "pushbutton"
if hasattr(fitz, "PDF_WIDGET_TYPE_SIGNATURE"):
    _TYPE_MAP[fitz.PDF_WIDGET_TYPE_SIGNATURE] = "signature"

_REVERSE_TYPE_MAP = {
    "text": fitz.PDF_WIDGET_TYPE_TEXT,
    "checkbox": fitz.PDF_WIDGET_TYPE_CHECKBOX,
    "combobox": fitz.PDF_WIDGET_TYPE_COMBOBOX,
    "listbox": fitz.PDF_WIDGET_TYPE_LISTBOX,
    "radiobutton": fitz.PDF_WIDGET_TYPE_RADIOBUTTON,
}


@dataclass
class FormField:
    """양식 필드 정보."""
    name: str
    field_type: str  # "text", "checkbox", "combobox", etc.
    value: str
    rect: tuple[float, float, float, float] | None = None
    choices: list[str] | None = None


# ── 읽기 ──────────────────────────────────────────────────────────────────────

def read_form_fields(pdf_path: str) -> list[FormField]:
    """PDF의 모든 양식 필드를 읽어 반환."""
    doc = fitz.open(pdf_path)
    fields: list[FormField] = []

    for page in doc:
        for widget in page.widgets():
            ft = _TYPE_MAP.get(widget.field_type, "unknown")
            fields.append(FormField(
                name=widget.field_name or "",
                field_type=ft,
                value=widget.field_value or "",
                rect=(widget.rect.x0, widget.rect.y0, widget.rect.x1, widget.rect.y1),
                choices=widget.choice_values if hasattr(widget, "choice_values") else None,
            ))

    doc.close()
    return fields


# ── 쓰기 ──────────────────────────────────────────────────────────────────────

def write_form_field(
    input_path: str,
    output_path: str,
    field_name: str,
    value: str,
) -> None:
    """양식 필드 값을 설정하고 저장."""
    doc = fitz.open(input_path)

    for page in doc:
        for widget in page.widgets():
            if widget.field_name == field_name:
                widget.field_value = value
                widget.update()

    doc.save(output_path)
    doc.close()


# ── 생성 ──────────────────────────────────────────────────────────────────────

def add_form_field(
    input_path: str,
    output_path: str,
    field_name: str,
    field_type: str,
    rect: fitz.Rect,
    *,
    page_idx: int = 0,
    default_value: str = "",
) -> None:
    """PDF에 양식 필드를 추가."""
    doc = fitz.open(input_path)
    page = doc[page_idx]

    widget = fitz.Widget()
    widget.field_type = _REVERSE_TYPE_MAP.get(field_type, fitz.PDF_WIDGET_TYPE_TEXT)
    widget.field_name = field_name
    widget.field_value = default_value
    widget.rect = rect

    page.add_widget(widget)

    doc.save(output_path)
    doc.close()


# ── 내보내기 ──────────────────────────────────────────────────────────────────

def export_form_data(
    pdf_path: str,
    output_path: str,
) -> None:
    """양식 데이터를 JSON으로 내보내기."""
    fields = read_form_fields(pdf_path)
    data = {f.name: f.value for f in fields if f.name}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
