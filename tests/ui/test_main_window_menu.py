"""MainWindow 메뉴/툴바 구조 테스트 -- TC-130~TC-143."""

from __future__ import annotations

import pytest

from app.core.annotator import AnnotationTool
from app.ui.main_window import MainWindow


def _menu_texts(win, menu_title_fragment: str) -> list[str]:
    """메뉴바에서 특정 메뉴의 액션 텍스트 목록을 반환합니다."""
    for action in win.menuBar().actions():
        if menu_title_fragment in action.text():
            menu = action.menu()
            if menu:
                return [a.text() for a in menu.actions() if not a.isSeparator()]
    return []


class TestMainLayout:
    def test_main_layout_has_splitter(self, main_window):
        """TC-130: 메인 레이아웃에 스플리터가 존재."""
        from PyQt6.QtWidgets import QSplitter
        assert isinstance(main_window._splitter, QSplitter)


class TestFileMenu:
    def test_file_menu_items(self, main_window):
        """TC-131: 파일 메뉴 항목 확인."""
        texts = _menu_texts(main_window, "파일")
        text_str = " ".join(texts)
        assert "열기" in text_str
        assert "저장" in text_str
        assert "다른 이름으로 저장" in text_str
        assert "종료" in text_str


class TestEditMenu:
    def test_edit_menu_items(self, main_window):
        """TC-132: 편집 메뉴 항목 확인."""
        texts = _menu_texts(main_window, "편집")
        text_str = " ".join(texts)
        assert "실행 취소" in text_str or "취소" in text_str
        assert "다시 실행" in text_str
        assert "삭제" in text_str
        assert "추출" in text_str
        assert "삽입" in text_str


class TestViewMenu:
    def test_view_menu_items(self, main_window):
        """TC-133: 보기 메뉴 항목 확인."""
        texts = _menu_texts(main_window, "보기")
        text_str = " ".join(texts)
        # 줌 인/아웃/맞춤 + 이전/다음 페이지
        assert len(texts) >= 3
        assert "이전 페이지" in text_str or "이전" in text_str
        assert "다음 페이지" in text_str or "다음" in text_str


class TestAnnotationMenu:
    def test_annotation_menu_items(self, main_window):
        """TC-134: 어노테이션 메뉴 항목 확인."""
        texts = _menu_texts(main_window, "어노테이션")
        text_str = " ".join(texts)
        assert "선택" in text_str
        assert "텍스트" in text_str
        assert "사각형" in text_str
        assert "타원" in text_str
        assert "선" in text_str


class TestToolsMenu:
    def test_tools_menu_items(self, main_window):
        """TC-135: 도구 메뉴 항목 확인."""
        texts = _menu_texts(main_window, "도구")
        text_str = " ".join(texts)
        assert "변환" in text_str


class TestHelpMenu:
    def test_help_menu_items(self, main_window):
        """TC-136: 도움말 메뉴 항목 확인."""
        texts = _menu_texts(main_window, "도움말")
        text_str = " ".join(texts)
        assert "정보" in text_str


class TestToolbarFileActions:
    def test_toolbar_file_actions(self, main_window):
        """TC-137: 툴바 파일 관련 액션 존재."""
        assert main_window._toolbar._act_open is not None
        assert main_window._toolbar._act_save is not None


class TestToolbarPageEditActions:
    def test_toolbar_page_edit_actions(self, main_window):
        """TC-138: 툴바 페이지 편집 액션 존재."""
        assert main_window._toolbar._act_delete is not None
        assert main_window._toolbar._act_extract is not None
        assert main_window._toolbar._act_insert is not None
        assert main_window._toolbar._act_convert is not None


class TestKeyboardShortcuts:
    def test_keyboard_shortcut_bindings(self, main_window):
        """TC-143: 주요 단축키 바인딩 확인."""
        shortcuts = {
            main_window._toolbar._act_open: "O",
            main_window._toolbar._act_save: "S",
            main_window._toolbar._act_zoom_in: "=",
            main_window._toolbar._act_zoom_out: "-",
            main_window._toolbar._act_zoom_fit: "0",
        }
        for action, expected_key in shortcuts.items():
            actual = action.shortcut().toString()
            assert expected_key in actual, \
                f"{action.text()}: expected '{expected_key}' in '{actual}'"

        # Undo/Redo 단축키 확인
        undo_shortcut = main_window._act_undo.shortcut().toString()
        assert "Z" in undo_shortcut.upper()

        redo_shortcut = main_window._act_redo.shortcut().toString()
        assert "Y" in redo_shortcut.upper() or "Z" in redo_shortcut.upper()
