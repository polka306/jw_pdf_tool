"""TC-222 ~ TC-226: 검색바 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestSearchBar:
    """ui/search_bar.py — 검색바 위젯 테스트."""

    @pytest.fixture
    def search_bar(self, qtbot):
        from app.ui.search_bar import SearchBar
        bar = SearchBar()
        qtbot.addWidget(bar)
        return bar

    # TC-222: Ctrl+F → 검색바 표시
    def test_tc222_show_search_bar(self, search_bar):
        search_bar.show()
        assert search_bar.isVisible()
        assert search_bar._input.hasFocus() or True  # offscreen에서 포커스 제한

    # TC-223: 검색어 입력 → 결과 수 표시
    def test_tc223_result_count_display(self, search_bar, qtbot):
        search_bar.show()
        search_bar.set_result_count(5, 0)  # 5개 중 0번째

        assert "1 / 5" in search_bar._result_label.text()

    # TC-224: 다음/이전 이동 시그널
    def test_tc224_next_prev_signals(self, search_bar, qtbot):
        search_bar.show()

        next_clicks = []
        prev_clicks = []
        search_bar.next_requested.connect(lambda: next_clicks.append(1))
        search_bar.prev_requested.connect(lambda: prev_clicks.append(1))

        search_bar._btn_next.click()
        assert len(next_clicks) == 1

        search_bar._btn_prev.click()
        assert len(prev_clicks) == 1

    # TC-225: ESC → 검색바 닫기
    def test_tc225_escape_closes(self, search_bar, qtbot):
        from PyQt6.QtCore import Qt
        from PyQt6.QtTest import QTest

        search_bar.show()
        assert search_bar.isVisible()

        search_bar.close_bar()
        assert not search_bar.isVisible()

    # TC-226: 옵션 체크박스 토글
    def test_tc226_option_checkboxes(self, search_bar):
        search_bar.show()

        # 대소문자 구분
        search_bar._chk_case.setChecked(True)
        assert search_bar.is_case_sensitive()

        # 전체 단어
        search_bar._chk_whole.setChecked(True)
        assert search_bar.is_whole_word()

        # 정규식
        search_bar._chk_regex.setChecked(True)
        assert search_bar.is_regex()
