"""PDF 병합/분할 로직."""

from __future__ import annotations

import os
from pathlib import Path

import fitz


def merge_pdfs(
    pdf_paths: list[str],
    output_path: str,
    *,
    keep_bookmarks: bool = False,
    page_ranges: list[tuple[int, int]] | None = None,
) -> None:
    """여러 PDF를 하나로 병합.

    Parameters
    ----------
    pdf_paths : list[str]
        입력 PDF 파일 경로 목록.
    output_path : str
        출력 PDF 파일 경로.
    keep_bookmarks : bool
        True이면 원본 북마크를 유지.
    page_ranges : list[tuple[int, int]] | None
        각 파일별 페이지 범위 (0-indexed, inclusive). None이면 전체.
    """
    if not pdf_paths:
        raise ValueError("병합할 PDF 파일이 없습니다.")

    merged = fitz.open()
    all_toc: list[list] = []
    page_offset = 0

    for i, path in enumerate(pdf_paths):
        src = fitz.open(path)

        if page_ranges and i < len(page_ranges):
            from_page, to_page = page_ranges[i]
            merged.insert_pdf(src, from_page=from_page, to_page=to_page)
            added = to_page - from_page + 1
        else:
            merged.insert_pdf(src)
            added = len(src)

        if keep_bookmarks:
            toc = src.get_toc()
            for entry in toc:
                entry[2] += page_offset  # 페이지 번호 오프셋
                all_toc.append(entry)

        page_offset += added
        src.close()

    if keep_bookmarks and all_toc:
        merged.set_toc(all_toc)

    merged.save(output_path, garbage=4, deflate=True)
    merged.close()


def split_pdf(
    pdf_path: str,
    output_dir: str,
    *,
    pages_per_split: int | None = None,
    ranges: list[tuple[int, int]] | None = None,
    by_bookmarks: bool = False,
) -> list[str]:
    """PDF를 여러 파일로 분할.

    Returns
    -------
    list[str]
        생성된 파일 경로 목록.
    """
    doc = fitz.open(pdf_path)
    total = len(doc)
    stem = Path(pdf_path).stem
    output_files: list[str] = []

    if by_bookmarks:
        split_points = _get_bookmark_split_points(doc)
    elif ranges:
        split_points = ranges
    elif pages_per_split:
        split_points = []
        for start in range(0, total, pages_per_split):
            end = min(start + pages_per_split - 1, total - 1)
            split_points.append((start, end))
    else:
        # 기본: 페이지당 1파일
        split_points = [(i, i) for i in range(total)]

    for idx, (start, end) in enumerate(split_points):
        out = fitz.open()
        out.insert_pdf(doc, from_page=start, to_page=end)
        out_path = os.path.join(output_dir, f"{stem}_part{idx + 1}.pdf")
        out.save(out_path, garbage=4, deflate=True)
        out.close()
        output_files.append(out_path)

    doc.close()
    return output_files


def _get_bookmark_split_points(doc: fitz.Document) -> list[tuple[int, int]]:
    """북마크(레벨 1) 기준 분할 포인트."""
    toc = doc.get_toc()
    total = len(doc)

    # 레벨 1 북마크의 시작 페이지
    starts = [entry[2] - 1 for entry in toc if entry[0] == 1]  # 1-indexed → 0-indexed

    if not starts:
        return [(0, total - 1)]

    points = []
    for i, start in enumerate(starts):
        if i + 1 < len(starts):
            end = starts[i + 1] - 1
        else:
            end = total - 1
        points.append((start, end))

    return points
