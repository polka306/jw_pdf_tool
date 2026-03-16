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
    font_size: float = 14.0


# ── 한글 폰트 감지 (Windows) ──────────────────────────────────────────────────

def _find_korean_font() -> str | None:
    """Windows 환경에서 한글 지원 폰트 파일 경로를 반환합니다."""
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",    # Malgun Gothic
        "C:/Windows/Fonts/gulim.ttc",     # Gulim
        "C:/Windows/Fonts/batang.ttc",    # Batang
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


_KOREAN_FONT_PATH: str | None = _find_korean_font()


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
    """텍스트를 페이지에 삽입합니다. 한글 지원 폰트가 있으면 자동 적용합니다."""
    kwargs: dict = {
        "point": fitz.Point(x, y),
        "text": text,
        "fontsize": style.font_size,
        "color": style.color,
    }
    if _KOREAN_FONT_PATH:
        kwargs["fontfile"] = _KOREAN_FONT_PATH
        kwargs["fontname"] = "KoreanFont"

    page.insert_text(**kwargs)
