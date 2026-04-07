"""TC-200 ~ TC-208: 검색 엔진 단위 테스트."""

from __future__ import annotations

import fitz
import pytest


def _make_searchable_pdf(tmp_path, texts: list[str] | None = None) -> str:
    """검색 가능한 텍스트가 포함된 PDF 생성."""
    doc = fitz.open()
    if texts is None:
        texts = [
            "Hello World. This is page 1. 안녕하세요.",
            "Page 2 has some numbers: 123-4567 and email@test.com",
            "Page 3 UPPERCASE lowercase MiXeD case",
        ]
    for i, text in enumerate(texts):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), text, fontsize=12)
    path = str(tmp_path / "searchable.pdf")
    doc.save(path)
    doc.close()
    return path


class TestSearchEngine:
    """core/search_engine.py — 텍스트 검색 테스트."""

    # TC-200: 영어 키워드 검색
    def test_tc200_english_keyword(self, tmp_path):
        from app.core.search_engine import SearchEngine

        pdf_path = _make_searchable_pdf(tmp_path)
        engine = SearchEngine(pdf_path)
        results = engine.search("Hello")

        assert len(results) >= 1
        assert results[0].page_idx == 0
        assert results[0].rect is not None

    # TC-201: 한글 키워드 검색
    def test_tc201_korean_keyword(self, tmp_path):
        from app.core.search_engine import SearchEngine
        from app.utils.platform import get_korean_font_path
        import sys

        if sys.platform == "win32" and get_korean_font_path():
            # 한글 폰트로 PDF 생성
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)
            fontpath = get_korean_font_path()
            page.insert_text((72, 100), "안녕하세요 테스트입니다", fontsize=14,
                             fontname="korean", fontfile=fontpath)
            pdf_path = str(tmp_path / "korean.pdf")
            doc.save(pdf_path)
            doc.close()

            engine = SearchEngine(pdf_path)
            results = engine.search("안녕하세요")
            assert len(results) >= 1
            assert results[0].page_idx == 0
        else:
            pytest.skip("한글 폰트 미설치")

    # TC-202: 대소문자 구분 옵션
    def test_tc202_case_sensitivity(self, tmp_path):
        from app.core.search_engine import SearchEngine

        pdf_path = _make_searchable_pdf(tmp_path)
        engine = SearchEngine(pdf_path)

        # 대소문자 무시 (기본)
        results_insensitive = engine.search("hello", case_sensitive=False)
        # 대소문자 구분
        results_sensitive = engine.search("hello", case_sensitive=True)

        assert len(results_insensitive) >= 1  # "Hello" 매칭
        assert len(results_sensitive) == 0      # "hello" 정확 매칭 없음

    # TC-203: 전체 단어 일치 옵션
    def test_tc203_whole_word(self, tmp_path):
        from app.core.search_engine import SearchEngine

        pdf_path = _make_searchable_pdf(tmp_path)
        engine = SearchEngine(pdf_path)

        # 부분 매칭
        results_partial = engine.search("page", case_sensitive=False)
        # 전체 단어
        results_whole = engine.search("page", whole_word=True, case_sensitive=False)

        # "page" 부분 매칭은 더 많거나 같을 수 있음
        assert len(results_partial) >= len(results_whole)

    # TC-204: 정규식 검색
    def test_tc204_regex_search(self, tmp_path):
        from app.core.search_engine import SearchEngine

        pdf_path = _make_searchable_pdf(tmp_path)
        engine = SearchEngine(pdf_path)
        results = engine.search(r"\d{3}-\d{4}", regex=True)

        assert len(results) >= 1  # "123-4567" 매칭
        assert results[0].page_idx == 1

    # TC-205: 빈 문자열 검색
    def test_tc205_empty_search(self, tmp_path):
        from app.core.search_engine import SearchEngine

        pdf_path = _make_searchable_pdf(tmp_path)
        engine = SearchEngine(pdf_path)
        results = engine.search("")

        assert results == []

    # TC-206: 페이지 범위 지정 검색
    def test_tc206_page_range(self, tmp_path):
        from app.core.search_engine import SearchEngine

        pdf_path = _make_searchable_pdf(tmp_path)
        engine = SearchEngine(pdf_path)
        results = engine.search("page", case_sensitive=False, page_range=(1, 2))

        # 페이지 1~2만 검색 (0-indexed)
        for r in results:
            assert 1 <= r.page_idx <= 2

    # TC-207: 매칭 없는 검색어
    def test_tc207_no_match(self, tmp_path):
        from app.core.search_engine import SearchEngine

        pdf_path = _make_searchable_pdf(tmp_path)
        engine = SearchEngine(pdf_path)
        results = engine.search("zzzznonexistent")

        assert results == []

    # TC-208: 100페이지 검색 성능 (1초 이내)
    def test_tc208_performance_100pages(self, tmp_path):
        import time

        texts = [f"Page {i+1} content with keyword searchable text" for i in range(100)]
        pdf_path = _make_searchable_pdf(tmp_path, texts)

        from app.core.search_engine import SearchEngine
        engine = SearchEngine(pdf_path)

        start = time.perf_counter()
        results = engine.search("keyword")
        elapsed = time.perf_counter() - start

        assert len(results) == 100
        assert elapsed < 2.0  # 2초 여유 (목표 1초)
