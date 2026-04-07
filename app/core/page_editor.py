"""페이지 편집 로직 — PyMuPDF 기반."""

from __future__ import annotations

import fitz  # PyMuPDF


def move_page(doc: fitz.Document, from_idx: int, to_idx: int) -> None:
    """페이지를 from_idx에서 to_idx 위치로 이동합니다."""
    if from_idx == to_idx:
        return
    doc.move_page(from_idx, to_idx)


def delete_pages(doc: fitz.Document, indices: list[int]) -> None:
    """지정한 페이지들을 삭제합니다. 인덱스는 0-based."""
    if not indices:
        return
    # 뒤에서부터 삭제해야 앞 인덱스가 밀리지 않음
    for idx in sorted(set(indices), reverse=True):
        doc.delete_page(idx)


def extract_pages(
    doc: fitz.Document,
    indices: list[int],
    output_path: str,
) -> None:
    """선택한 페이지들을 새 PDF 파일로 추출합니다."""
    new_doc = fitz.open()
    for idx in sorted(set(indices)):
        new_doc.insert_pdf(doc, from_page=idx, to_page=idx)
    new_doc.save(output_path, garbage=4, deflate=True)
    new_doc.close()


def rotate_page(doc: fitz.Document, page_idx: int, degrees: int) -> None:
    """페이지를 지정 각도만큼 회전합니다.

    Parameters
    ----------
    degrees : int
        회전 각도. 90, 180, 270 또는 -90, -180, -270.
    """
    page = doc[page_idx]
    new_rotation = (page.rotation + degrees) % 360
    page.set_rotation(new_rotation)


def crop_page(doc: fitz.Document, page_idx: int, rect: fitz.Rect) -> None:
    """페이지의 CropBox를 설정합니다. MediaBox는 보존."""
    page = doc[page_idx]
    page.set_cropbox(rect)


def reset_cropbox(doc: fitz.Document, page_idx: int) -> None:
    """CropBox를 MediaBox로 리셋합니다."""
    page = doc[page_idx]
    page.set_cropbox(page.mediabox)


def insert_pages_from_file(
    doc: fitz.Document,
    source_path: str,
    source_indices: list[int],
    insert_before: int,
) -> None:
    """다른 PDF 파일의 페이지들을 insert_before 위치 앞에 삽입합니다.

    insert_before == doc.page_count 이면 맨 끝에 추가.
    """
    src = fitz.open(source_path)
    for offset, idx in enumerate(sorted(set(source_indices))):
        doc.insert_pdf(src, from_page=idx, to_page=idx, start_at=insert_before + offset)
    src.close()
