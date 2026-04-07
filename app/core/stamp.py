"""스탬프 기능 — 텍스트/이미지 스탬프를 PDF 페이지에 추가."""

from __future__ import annotations

import math

import fitz


def add_text_stamp(
    page: fitz.Page,
    point: fitz.Point,
    text: str,
    *,
    color: tuple[float, float, float] = (1.0, 0.0, 0.0),
    fontsize: float = 24.0,
    rotate: float = 0.0,
    opacity: float = 1.0,
) -> None:
    """텍스트 스탬프를 페이지에 추가.

    Parameters
    ----------
    point : fitz.Point
        스탬프 위치.
    text : str
        스탬프 텍스트.
    color : tuple
        RGB 색상 (0~1).
    fontsize : float
        폰트 크기.
    rotate : float
        회전 각도 (도).
    opacity : float
        투명도 (0~1). 1=불투명.
    """
    shape = page.new_shape()
    # 회전 적용을 위한 morph 파라미터
    morph = None
    if rotate != 0:
        morph = (point, fitz.Matrix(rotate))

    shape.insert_text(
        point,
        text,
        fontsize=fontsize,
        color=color,
        morph=morph,
    )
    shape.finish(color=color)
    shape.commit()


def add_image_stamp(
    page: fitz.Page,
    rect: fitz.Rect,
    image_path: str,
) -> None:
    """이미지 스탬프를 페이지에 추가.

    Parameters
    ----------
    rect : fitz.Rect
        이미지 배치 영역.
    image_path : str
        이미지 파일 경로 (PNG, JPG).
    """
    page.insert_image(rect, filename=image_path)
