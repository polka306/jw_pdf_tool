"""TC-163: 어노테이션 메뉴 도구 전환 시 툴바 동기화."""

from __future__ import annotations

from app.core.annotator import AnnotationTool
from tests.helpers import load_pdf_directly


class TestTC163:
    """TC-163: 어노테이션 메뉴 도구 전환 시 툴바 동기화."""

    def test_menu_action_syncs_toolbar(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))

        # 메뉴의 타원 액션을 직접 trigger
        ellipse_action = win._toolbar._tool_actions[AnnotationTool.ELLIPSE]
        ellipse_action.trigger()

        assert ellipse_action.isChecked()

        # 선택 액션으로 전환
        select_action = win._toolbar._tool_actions[AnnotationTool.SELECT]
        select_action.trigger()
        assert select_action.isChecked()
        assert not ellipse_action.isChecked()

    def test_all_tool_actions_are_exclusive(self, main_window, pdf_factory):
        """모든 도구 액션이 배타적 그룹에 속하는지 확인."""
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))

        for tool, action in win._toolbar._tool_actions.items():
            action.trigger()
            for other_tool, other_action in win._toolbar._tool_actions.items():
                if other_tool == tool:
                    assert other_action.isChecked()
                else:
                    assert not other_action.isChecked(), \
                        f"{tool} 활성 시 {other_tool}이 여전히 checked"
