"""텍스트 검색 엔진 + 북마크 파서 + 텍스트 추출."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import fitz


# ── 검색 결과 ──────────────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    """검색 매칭 하나."""
    page_idx: int
    rect: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    text: str = ""


# ── 검색 엔진 ──────────────────────────────────────────────────────────────────

class SearchEngine:
    """PDF 텍스트 검색."""

    def __init__(self, pdf_path: str) -> None:
        self._path = pdf_path

    def search(
        self,
        query: str,
        *,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex: bool = False,
        page_range: tuple[int, int] | None = None,
    ) -> list[SearchResult]:
        """PDF 내 텍스트 검색."""
        if not query:
            return []

        doc = fitz.open(self._path)
        results: list[SearchResult] = []

        start_page = page_range[0] if page_range else 0
        end_page = page_range[1] if page_range else len(doc) - 1

        for page_idx in range(start_page, min(end_page + 1, len(doc))):
            page = doc[page_idx]

            if regex:
                matches = self._regex_search(page, query, page_idx)
            else:
                matches = self._text_search(
                    page, query, page_idx,
                    case_sensitive=case_sensitive,
                    whole_word=whole_word,
                )
            results.extend(matches)

        doc.close()
        return results

    def _text_search(
        self,
        page: fitz.Page,
        query: str,
        page_idx: int,
        *,
        case_sensitive: bool,
        whole_word: bool,
    ) -> list[SearchResult]:
        """일반 텍스트 검색."""
        flags = 0
        if not case_sensitive:
            # PyMuPDF search_for는 기본적으로 대소문자 무시
            pass

        rects = page.search_for(query)

        if case_sensitive:
            # 대소문자 구분: 텍스트를 직접 확인하여 필터링
            text = page.get_text()
            if query not in text:
                rects = []

        if whole_word:
            # 전체 단어 필터: 앞뒤 경계 확인
            text = page.get_text()
            pattern = rf"\b{re.escape(query)}\b"
            flags_re = 0 if case_sensitive else re.IGNORECASE
            word_matches = list(re.finditer(pattern, text, flags_re))
            rects = rects[:len(word_matches)]

        return [
            SearchResult(
                page_idx=page_idx,
                rect=(r.x0, r.y0, r.x1, r.y1),
            )
            for r in rects
        ]

    def _regex_search(
        self,
        page: fitz.Page,
        pattern: str,
        page_idx: int,
    ) -> list[SearchResult]:
        """정규식 검색."""
        text = page.get_text()
        results = []
        try:
            for match in re.finditer(pattern, text):
                # 매칭된 텍스트의 위치 찾기
                rects = page.search_for(match.group())
                for r in rects:
                    results.append(SearchResult(
                        page_idx=page_idx,
                        rect=(r.x0, r.y0, r.x1, r.y1),
                        text=match.group(),
                    ))
                    break  # 첫 번째 위치만
        except re.error:
            pass  # 잘못된 정규식 무시
        return results


# ── 북마크 파서 ────────────────────────────────────────────────────────────────

@dataclass
class Bookmark:
    """북마크(아웃라인) 항목."""
    title: str
    page_idx: int  # 0-indexed
    level: int = 1
    children: list[Bookmark] = field(default_factory=list)


def parse_bookmarks(pdf_path: str) -> list[Bookmark]:
    """PDF 아웃라인을 트리 구조로 파싱."""
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()  # [[level, title, page], ...]
    doc.close()

    if not toc:
        return []

    root: list[Bookmark] = []
    stack: list[tuple[int, Bookmark]] = []  # (level, bookmark)

    for level, title, page_num in toc:
        bm = Bookmark(
            title=title,
            page_idx=page_num - 1,  # 1-indexed → 0-indexed
            level=level,
        )

        # 스택에서 현재 레벨 이상인 항목 제거
        while stack and stack[-1][0] >= level:
            stack.pop()

        if stack:
            # 부모에 자식으로 추가
            stack[-1][1].children.append(bm)
        else:
            # 최상위
            root.append(bm)

        stack.append((level, bm))

    return root


# ── 텍스트 추출 ────────────────────────────────────────────────────────────────

def extract_text_in_rect(
    pdf_path: str,
    page_idx: int,
    rect: fitz.Rect,
) -> str:
    """PDF 페이지의 특정 영역 내 텍스트를 추출."""
    doc = fitz.open(pdf_path)
    if page_idx >= len(doc):
        doc.close()
        return ""
    page = doc[page_idx]
    text = page.get_textbox(rect)
    doc.close()
    return text
