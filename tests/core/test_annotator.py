"""annotator 단위 테스트."""

from __future__ import annotations

import fitz
import pytest

from app.core.annotator import (
    AnnotationStyle,
    AnnotationTool,
    _resolve_font,
    add_ellipse,
    add_line,
    add_rect,
    add_text,
)


@pytest.fixture
def blank_page(tmp_path):
    """단일 빈 페이지 fitz.Document를 반환합니다."""
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    yield doc[0], doc
    doc.close()


def _render_bytes(page: fitz.Page) -> bytes:
    return page.get_pixmap(matrix=fitz.Matrix(1, 1)).tobytes("png")


# ── AnnotationStyle 기본값 ─────────────────────────────────────────────────────

class TestAnnotationStyle:
    def test_default_color_is_red(self):
        s = AnnotationStyle()
        assert s.color == (1.0, 0.0, 0.0)

    def test_default_fill_is_none(self):
        assert AnnotationStyle().fill_color is None

    def test_custom_values(self):
        s = AnnotationStyle(color=(0, 0, 1), line_width=5.0, font_size=20.0)
        assert s.color == (0, 0, 1)
        assert s.line_width == 5.0
        assert s.font_size == 20.0

    def test_default_font_family_is_helv(self):
        assert AnnotationStyle().font_family == "helv"

    def test_default_bold_italic_false(self):
        s = AnnotationStyle()
        assert s.bold is False
        assert s.italic is False


# ── _resolve_font ─────────────────────────────────────────────────────────────

class TestResolveFont:
    def test_helv_regular(self):
        name, file = _resolve_font(AnnotationStyle(font_family="helv"))
        assert name == "Helvetica"
        assert file is None

    def test_helv_bold(self):
        name, file = _resolve_font(AnnotationStyle(font_family="helv", bold=True))
        assert name == "Helvetica-Bold"
        assert file is None

    def test_helv_italic(self):
        name, file = _resolve_font(AnnotationStyle(font_family="helv", italic=True))
        assert name == "Helvetica-Oblique"
        assert file is None

    def test_helv_bold_italic(self):
        name, file = _resolve_font(AnnotationStyle(font_family="helv", bold=True, italic=True))
        assert name == "Helvetica-BoldOblique"
        assert file is None

    def test_tiro_regular(self):
        name, file = _resolve_font(AnnotationStyle(font_family="tiro"))
        assert name == "Times-Roman"
        assert file is None

    def test_tiro_bold(self):
        name, file = _resolve_font(AnnotationStyle(font_family="tiro", bold=True))
        assert name == "Times-Bold"
        assert file is None

    def test_tiro_italic(self):
        name, file = _resolve_font(AnnotationStyle(font_family="tiro", italic=True))
        assert name == "Times-Italic"
        assert file is None

    def test_tiro_bold_italic(self):
        name, file = _resolve_font(AnnotationStyle(font_family="tiro", bold=True, italic=True))
        assert name == "Times-BoldItalic"
        assert file is None

    def test_cour_regular(self):
        name, file = _resolve_font(AnnotationStyle(font_family="cour"))
        assert name == "Courier"
        assert file is None

    def test_unknown_family_falls_back_to_helv(self):
        name, file = _resolve_font(AnnotationStyle(font_family="unknown"))
        assert name == "Helvetica"
        assert file is None

    def test_korean_returns_path_or_helv_fallback(self):
        """한글 폰트가 없으면 Helvetica로 폴백합니다."""
        name, file = _resolve_font(AnnotationStyle(font_family="korean"))
        # 폰트 파일이 있으면 경로, 없으면 Helvetica 폴백
        assert name in ("KoreanFont", "KoreanBold", "Helvetica")


# ── AnnotationTool 열거형 ─────────────────────────────────────────────────────

class TestAnnotationTool:
    def test_all_tools_defined(self):
        tools = {AnnotationTool.SELECT, AnnotationTool.TEXT,
                 AnnotationTool.RECT, AnnotationTool.ELLIPSE, AnnotationTool.LINE}
        assert len(tools) == 5

    def test_tools_are_distinct(self):
        assert AnnotationTool.SELECT != AnnotationTool.RECT
        assert AnnotationTool.TEXT != AnnotationTool.LINE


# ── add_rect ──────────────────────────────────────────────────────────────────

class TestAddRect:
    def test_changes_page_content(self, blank_page):
        page, _ = blank_page
        before = _render_bytes(page)
        add_rect(page, 50, 50, 200, 150, AnnotationStyle())
        after = _render_bytes(page)
        assert before != after

    def test_normalized_coords(self, blank_page):
        """x2 < x1 이어도 정상 동작해야 합니다."""
        page, _ = blank_page
        add_rect(page, 200, 150, 50, 50, AnnotationStyle())  # 반전된 좌표
        rendered = _render_bytes(page)
        assert rendered  # 예외 없이 렌더링

    def test_custom_color(self, blank_page):
        page, _ = blank_page
        before = _render_bytes(page)
        add_rect(page, 50, 50, 200, 150, AnnotationStyle(color=(0.0, 1.0, 0.0)))
        after = _render_bytes(page)
        assert before != after

    def test_with_fill(self, blank_page):
        page, _ = blank_page
        before = _render_bytes(page)
        add_rect(page, 50, 50, 200, 150, AnnotationStyle(fill_color=(0.9, 0.9, 0.0)))
        after = _render_bytes(page)
        assert before != after

    def test_multiple_rects(self, blank_page):
        page, _ = blank_page
        style = AnnotationStyle()
        add_rect(page, 10, 10, 100, 100, style)
        add_rect(page, 200, 200, 400, 350, style)
        rendered = _render_bytes(page)
        assert rendered


# ── add_ellipse ───────────────────────────────────────────────────────────────

class TestAddEllipse:
    def test_changes_page_content(self, blank_page):
        page, _ = blank_page
        before = _render_bytes(page)
        add_ellipse(page, 50, 50, 250, 200, AnnotationStyle())
        after = _render_bytes(page)
        assert before != after

    def test_normalized_coords(self, blank_page):
        page, _ = blank_page
        add_ellipse(page, 250, 200, 50, 50, AnnotationStyle())
        assert _render_bytes(page)

    def test_circle_shape(self, blank_page):
        """정사각형 rect를 쓰면 원이 됩니다."""
        page, _ = blank_page
        add_ellipse(page, 100, 100, 200, 200, AnnotationStyle())
        assert _render_bytes(page)


# ── add_line ──────────────────────────────────────────────────────────────────

class TestAddLine:
    def test_changes_page_content(self, blank_page):
        page, _ = blank_page
        before = _render_bytes(page)
        add_line(page, 50, 50, 400, 400, AnnotationStyle())
        after = _render_bytes(page)
        assert before != after

    def test_horizontal_line(self, blank_page):
        page, _ = blank_page
        add_line(page, 50, 200, 500, 200, AnnotationStyle())
        assert _render_bytes(page)

    def test_vertical_line(self, blank_page):
        page, _ = blank_page
        add_line(page, 200, 50, 200, 700, AnnotationStyle())
        assert _render_bytes(page)

    def test_thick_line(self, blank_page):
        page, _ = blank_page
        add_line(page, 50, 50, 400, 400, AnnotationStyle(line_width=10.0))
        assert _render_bytes(page)


# ── add_text ──────────────────────────────────────────────────────────────────

class TestAddText:
    def test_changes_page_content(self, blank_page):
        page, _ = blank_page
        before = _render_bytes(page)
        add_text(page, 100, 200, "Hello", AnnotationStyle())
        after = _render_bytes(page)
        assert before != after

    def test_empty_string_no_crash(self, blank_page):
        page, _ = blank_page
        add_text(page, 100, 200, "", AnnotationStyle())
        assert _render_bytes(page)

    def test_korean_text(self, blank_page):
        """한글 텍스트가 예외 없이 삽입되어야 합니다."""
        page, _ = blank_page
        add_text(page, 100, 200, "한글 텍스트", AnnotationStyle())
        assert _render_bytes(page)

    def test_large_font(self, blank_page):
        page, _ = blank_page
        add_text(page, 100, 200, "Big Text", AnnotationStyle(font_size=48.0))
        assert _render_bytes(page)

    def test_custom_color(self, blank_page):
        page, _ = blank_page
        before = _render_bytes(page)
        add_text(page, 100, 200, "Blue", AnnotationStyle(color=(0.0, 0.0, 1.0)))
        after = _render_bytes(page)
        assert before != after


# ── add_text — 스타일 변형 ────────────────────────────────────────────────────

class TestAddTextStyled:
    def test_helv_bold(self, blank_page):
        page, _ = blank_page
        add_text(page, 100, 200, "Bold Text", AnnotationStyle(font_family="helv", bold=True))
        assert _render_bytes(page)

    def test_helv_italic(self, blank_page):
        page, _ = blank_page
        add_text(page, 100, 200, "Italic", AnnotationStyle(font_family="helv", italic=True))
        assert _render_bytes(page)

    def test_helv_bold_italic(self, blank_page):
        page, _ = blank_page
        add_text(page, 100, 200, "BoldItalic", AnnotationStyle(font_family="helv", bold=True, italic=True))
        assert _render_bytes(page)

    def test_times_roman(self, blank_page):
        page, _ = blank_page
        add_text(page, 100, 200, "Times", AnnotationStyle(font_family="tiro"))
        assert _render_bytes(page)

    def test_courier(self, blank_page):
        page, _ = blank_page
        add_text(page, 100, 200, "Courier", AnnotationStyle(font_family="cour"))
        assert _render_bytes(page)

    def test_bold_produces_different_render(self, blank_page):
        """Bold 텍스트와 Regular 텍스트는 렌더링이 달라야 합니다."""
        page, _ = blank_page
        add_text(page, 100, 200, "Sample", AnnotationStyle(font_family="helv"))
        regular_render = _render_bytes(page)

        page2, _ = blank_page
        add_text(page2, 100, 200, "Sample", AnnotationStyle(font_family="helv", bold=True))
        bold_render = _render_bytes(page2)

        assert regular_render != bold_render

    def test_korean_style_no_crash(self, blank_page):
        """한글 폰트 스타일이 예외 없이 동작해야 합니다 (폰트 유무 무관)."""
        page, _ = blank_page
        add_text(page, 100, 200, "Korean Style", AnnotationStyle(font_family="korean"))
        assert _render_bytes(page)


# ── 복합 시나리오 ─────────────────────────────────────────────────────────────

class TestCombined:
    def test_multiple_annotation_types_on_same_page(self, blank_page):
        page, _ = blank_page
        style = AnnotationStyle()
        add_rect(page, 50, 50, 200, 150, style)
        add_ellipse(page, 250, 50, 450, 200, style)
        add_line(page, 50, 300, 500, 300, style)
        add_text(page, 100, 500, "Test Label", style)
        rendered = _render_bytes(page)
        assert rendered

    def test_annotations_saved_in_pdf(self, blank_page, tmp_path):
        """어노테이션이 저장된 PDF에서도 유지되는지 확인합니다."""
        page, doc = blank_page
        add_rect(page, 50, 50, 200, 150, AnnotationStyle())
        out_path = str(tmp_path / "annotated.pdf")
        doc.save(out_path)

        # 다시 열어서 렌더링 — 어노테이션이 포함된 이미지여야 함
        doc2 = fitz.open(out_path)
        pix = doc2[0].get_pixmap()
        assert pix.width > 0
        doc2.close()
