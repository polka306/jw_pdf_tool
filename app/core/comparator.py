"""PDF 비교 — 텍스트 diff."""

from __future__ import annotations

from dataclasses import dataclass

import fitz


@dataclass
class DiffResult:
    """비교 결과 하나."""
    page_idx: int
    diff_type: str  # "text_change", "page_count", "page_added", "page_removed"
    detail: str = ""


def compare_pdfs(
    path_a: str,
    path_b: str,
) -> list[DiffResult]:
    """두 PDF의 텍스트를 페이지별로 비교."""
    doc_a = fitz.open(path_a)
    doc_b = fitz.open(path_b)

    diffs: list[DiffResult] = []

    # 페이지 수 차이
    if len(doc_a) != len(doc_b):
        diffs.append(DiffResult(
            page_idx=-1,
            diff_type="page_count",
            detail=f"A={len(doc_a)}, B={len(doc_b)}",
        ))

    # 공통 페이지 텍스트 비교
    common = min(len(doc_a), len(doc_b))
    for idx in range(common):
        text_a = doc_a[idx].get_text().strip()
        text_b = doc_b[idx].get_text().strip()

        if text_a != text_b:
            diffs.append(DiffResult(
                page_idx=idx,
                diff_type="text_change",
                detail=f"Page {idx + 1} text differs",
            ))

    doc_a.close()
    doc_b.close()
    return diffs
