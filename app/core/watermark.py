"""워터마크, 머리글/바닥글, 베이츠 번호."""

from __future__ import annotations

import fitz


def add_text_watermark(
    input_path: str,
    output_path: str,
    text: str,
    *,
    color: tuple[float, float, float] = (0.5, 0.5, 0.5),
    fontsize: float = 60.0,
    rotate: float = 45.0,
    opacity: float = 0.3,
    layer: str = "foreground",
    page_indices: list[int] | None = None,
    tile: bool = False,
) -> None:
    """텍스트 워터마크를 모든 페이지에 추가."""
    doc = fitz.open(input_path)
    indices = page_indices or list(range(len(doc)))

    for idx in indices:
        page = doc[idx]
        rect = page.rect

        if tile:
            # 타일 반복
            y = 100
            while y < rect.height:
                x = 50
                while x < rect.width:
                    _insert_watermark_text(page, fitz.Point(x, y), text,
                                           color, fontsize, rotate, opacity, layer)
                    x += 200
                y += 150
        else:
            # 중앙 배치
            cx = rect.width / 2
            cy = rect.height / 2
            _insert_watermark_text(page, fitz.Point(cx, cy), text,
                                   color, fontsize, rotate, opacity, layer)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


def _insert_watermark_text(page, point, text, color, fontsize, rotate, opacity, layer):
    """워터마크 텍스트 삽입 헬퍼."""
    shape = page.new_shape()
    morph = (point, fitz.Matrix(rotate)) if rotate else None
    shape.insert_text(point, text, fontsize=fontsize, color=color, morph=morph)
    shape.finish(color=color, fill_opacity=opacity, stroke_opacity=opacity)

    if layer == "background":
        shape.commit(overlay=False)
    else:
        shape.commit(overlay=True)


def add_image_watermark(
    input_path: str,
    output_path: str,
    image_path: str,
    *,
    opacity: float = 0.3,
    page_indices: list[int] | None = None,
) -> None:
    """이미지 워터마크를 모든 페이지에 추가."""
    doc = fitz.open(input_path)
    indices = page_indices or list(range(len(doc)))

    for idx in indices:
        page = doc[idx]
        rect = page.rect
        # 중앙에 이미지 배치 (50% 크기)
        w = rect.width * 0.5
        h = rect.height * 0.3
        x = (rect.width - w) / 2
        y = (rect.height - h) / 2
        img_rect = fitz.Rect(x, y, x + w, y + h)
        page.insert_image(img_rect, filename=image_path, overlay=True)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


def add_header_footer(
    input_path: str,
    output_path: str,
    *,
    header_left: str = "",
    header_center: str = "",
    header_right: str = "",
    footer_left: str = "",
    footer_center: str = "",
    footer_right: str = "",
    fontsize: float = 10.0,
    color: tuple[float, float, float] = (0.3, 0.3, 0.3),
    skip_first: bool = False,
    margin: float = 36.0,
) -> None:
    """머리글/바닥글 추가. {page}, {total}, {date}, {filename} 변수 치환."""
    import datetime

    doc = fitz.open(input_path)
    total = len(doc)
    today = datetime.date.today().isoformat()
    filename = input_path.split("/")[-1].split("\\")[-1]

    for idx in range(total):
        if skip_first and idx == 0:
            continue

        page = doc[idx]
        rect = page.rect

        def _sub(template: str) -> str:
            return (template
                    .replace("{page}", str(idx + 1))
                    .replace("{total}", str(total))
                    .replace("{date}", today)
                    .replace("{filename}", filename))

        shape = page.new_shape()

        # 머리글
        y_header = margin
        if header_left:
            shape.insert_text(fitz.Point(margin, y_header), _sub(header_left),
                              fontsize=fontsize, color=color)
        if header_center:
            text = _sub(header_center)
            x = rect.width / 2 - len(text) * fontsize * 0.3
            shape.insert_text(fitz.Point(x, y_header), text, fontsize=fontsize, color=color)
        if header_right:
            text = _sub(header_right)
            x = rect.width - margin - len(text) * fontsize * 0.6
            shape.insert_text(fitz.Point(x, y_header), text, fontsize=fontsize, color=color)

        # 바닥글
        y_footer = rect.height - margin / 2
        if footer_left:
            shape.insert_text(fitz.Point(margin, y_footer), _sub(footer_left),
                              fontsize=fontsize, color=color)
        if footer_center:
            text = _sub(footer_center)
            x = rect.width / 2 - len(text) * fontsize * 0.3
            shape.insert_text(fitz.Point(x, y_footer), text, fontsize=fontsize, color=color)
        if footer_right:
            text = _sub(footer_right)
            x = rect.width - margin - len(text) * fontsize * 0.6
            shape.insert_text(fitz.Point(x, y_footer), text, fontsize=fontsize, color=color)

        shape.commit()

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


def add_bates_numbers(
    input_path: str,
    output_path: str,
    *,
    prefix: str = "",
    suffix: str = "",
    start: int = 1,
    digits: int = 6,
    fontsize: float = 10.0,
    color: tuple[float, float, float] = (0.0, 0.0, 0.0),
    position: str = "bottom_right",
    margin: float = 36.0,
) -> None:
    """베이츠 번호를 각 페이지에 삽입."""
    doc = fitz.open(input_path)

    for idx in range(len(doc)):
        page = doc[idx]
        rect = page.rect
        number = start + idx
        bates = f"{prefix}{number:0{digits}d}{suffix}"

        if position == "bottom_right":
            x = rect.width - margin - len(bates) * fontsize * 0.6
            y = rect.height - margin / 2
        elif position == "bottom_left":
            x = margin
            y = rect.height - margin / 2
        else:
            x = rect.width / 2 - len(bates) * fontsize * 0.3
            y = rect.height - margin / 2

        page.insert_text(fitz.Point(x, y), bates, fontsize=fontsize, color=color)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
