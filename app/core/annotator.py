"""어노테이션 로직 — PyMuPDF Shape 기반.

draw_* 메서드는 페이지 콘텐츠 스트림에 직접 기록되므로
저장 시 모든 PDF 뷰어에서 표시됩니다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum, auto

import fitz  # PyMuPDF


# ── 도구 종류 ─────────────────────────────────────────────────────────────────

class AnnotationTool(Enum):
    SELECT   = auto()   # 선택/스크롤 (기본)
    TEXT     = auto()   # 텍스트 삽입
    RECT     = auto()   # 사각형
    ELLIPSE  = auto()   # 타원
    LINE     = auto()   # 선


# ── 스타일 ────────────────────────────────────────────────────────────────────

@dataclass
class AnnotationStyle:
    """어노테이션 스타일 설정."""
    color: tuple[float, float, float] = field(default_factory=lambda: (1.0, 0.0, 0.0))
    fill_color: tuple[float, float, float] | None = None
    line_width: float = 2.0
    # 텍스트 스타일
    font_size: float = 14.0
    font_family: str = "helv"  # "helv" | "tiro" | "cour" | "korean"
    bold: bool = False
    italic: bool = False


# ── 폰트 매핑 ─────────────────────────────────────────────────────────────────

# (regular, bold, italic, bolditalic) — PDF Base-14 font names
_FONT_MAP: dict[str, tuple[str, str, str, str]] = {
    "helv": ("Helvetica",  "Helvetica-Bold",  "Helvetica-Oblique",  "Helvetica-BoldOblique"),
    "tiro": ("Times-Roman","Times-Bold",       "Times-Italic",       "Times-BoldItalic"),
    "cour": ("Courier",    "Courier-Bold",     "Courier-Oblique",    "Courier-BoldOblique"),
}


def _find_korean_font() -> str | None:
    """Windows 환경에서 한글 지원 폰트 파일 경로를 반환합니다."""
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",    # Malgun Gothic Regular
        "C:/Windows/Fonts/gulim.ttc",
        "C:/Windows/Fonts/batang.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


_KOREAN_FONT_PATH: str | None = _find_korean_font()
_KOREAN_BOLD_PATH: str | None = (
    "C:/Windows/Fonts/malgunbd.ttf"
    if os.path.exists("C:/Windows/Fonts/malgunbd.ttf") else None
)


def _resolve_font(style: AnnotationStyle) -> tuple[str, str | None]:
    """(fontname, fontfile_or_None) 을 반환합니다.

    한글 폰트: TTF 파일 경로를 fontfile로 전달.
    Base-14 폰트: bold/italic 조합에 맞는 표준 폰트명 반환.
    """
    if style.font_family == "korean":
        if style.bold and _KOREAN_BOLD_PATH:
            return "KoreanBold", _KOREAN_BOLD_PATH
        if _KOREAN_FONT_PATH:
            return "KoreanFont", _KOREAN_FONT_PATH
        # 한글 폰트 없으면 Helvetica로 폴백
        variants = _FONT_MAP["helv"]
    else:
        variants = _FONT_MAP.get(style.font_family, _FONT_MAP["helv"])

    idx = (2 if style.italic else 0) + (1 if style.bold else 0)
    return variants[idx], None


# ── 어노테이션 함수 ───────────────────────────────────────────────────────────

def add_rect(
    page: fitz.Page,
    x1: float, y1: float,
    x2: float, y2: float,
    style: AnnotationStyle,
) -> None:
    """사각형을 페이지에 그립니다."""
    rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(color=style.color, fill=style.fill_color, width=style.line_width)
    shape.commit()


def add_ellipse(
    page: fitz.Page,
    x1: float, y1: float,
    x2: float, y2: float,
    style: AnnotationStyle,
) -> None:
    """타원을 페이지에 그립니다."""
    rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    shape = page.new_shape()
    shape.draw_oval(rect)
    shape.finish(color=style.color, fill=style.fill_color, width=style.line_width)
    shape.commit()


def add_line(
    page: fitz.Page,
    x1: float, y1: float,
    x2: float, y2: float,
    style: AnnotationStyle,
) -> None:
    """선을 페이지에 그립니다."""
    shape = page.new_shape()
    shape.draw_line(fitz.Point(x1, y1), fitz.Point(x2, y2))
    shape.finish(color=style.color, width=style.line_width)
    shape.commit()


def add_text(
    page: fitz.Page,
    x: float,
    y: float,
    text: str,
    style: AnnotationStyle,
) -> None:
    """텍스트를 페이지에 삽입합니다. 폰트 패밀리/굵기/기울기, 페이지 회전을 반영합니다."""
    fontname, fontfile = _resolve_font(style)
    kwargs: dict = {
        "point": fitz.Point(x, y),
        "text": text,
        "fontsize": style.font_size,
        "color": style.color,
        "fontname": fontname,
        "rotate": page.rotation,   # 페이지 /Rotate 값으로 텍스트 방향 보정
    }
    if fontfile:
        kwargs["fontfile"] = fontfile

    page.insert_text(**kwargs)


# ── 하이라이트/밑줄/취소선 (PDF 표준 어노테이션) ────────────────────────────────

def add_highlight(
    page: fitz.Page,
    quads,
    *,
    color: tuple[float, float, float] = (1.0, 1.0, 0.0),
) -> fitz.Annot:
    """텍스트 하이라이트 어노테이션 추가. quads는 Rect 또는 Quad."""
    annot = page.add_highlight_annot(quads)
    annot.set_colors(stroke=color)
    annot.update()
    return annot


def add_underline(
    page: fitz.Page,
    quads,
    *,
    color: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> fitz.Annot:
    """텍스트 밑줄 어노테이션 추가. quads는 Rect 또는 Quad."""
    annot = page.add_underline_annot(quads)
    annot.set_colors(stroke=color)
    annot.update()
    return annot


def add_strikeout(
    page: fitz.Page,
    quads,
    *,
    color: tuple[float, float, float] = (1.0, 0.0, 0.0),
) -> fitz.Annot:
    """텍스트 취소선 어노테이션 추가. quads는 Rect 또는 Quad."""
    annot = page.add_strikeout_annot(quads)
    annot.set_colors(stroke=color)
    annot.update()
    return annot


# ── 스티키 노트 (Text 어노테이션) ───────────────────────────────────────────

def add_sticky_note(
    page: fitz.Page,
    point: fitz.Point,
    content: str,
    *,
    icon: str = "Note",
) -> fitz.Annot:
    """스티키 노트(팝업 메모) 어노테이션 추가."""
    annot = page.add_text_annot(point, content, icon=icon)
    annot.update()
    return annot


# ── 자유형 그리기 (Ink 어노테이션) ───────────────────────────────────────────

def add_ink(
    page: fitz.Page,
    points: list[tuple[float, float]],
    style: AnnotationStyle,
    *,
    min_length: float = 3.0,
) -> fitz.Annot | None:
    """Ink(자유형 그리기) 어노테이션 추가.

    경로 길이가 min_length 미만이면 None 반환 (오클릭 방지).
    """
    if len(points) < 2:
        return None

    # 경로 총 길이 계산
    total = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        dy = points[i][1] - points[i - 1][1]
        total += (dx * dx + dy * dy) ** 0.5

    if total < min_length:
        return None

    # (x, y) 튜플 리스트로 변환 — add_ink_annot은 seq of seq of float pairs 요구
    annot = page.add_ink_annot([points])
    annot.set_colors(stroke=style.color)
    annot.set_border(width=style.line_width)
    annot.update()
    return annot
