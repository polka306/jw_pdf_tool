"""TC-164: 문서 미열림 상태에서 편집 기능 비활성화."""

from __future__ import annotations

from app.core.annotator import AnnotationTool


class TestTC164:
    """TC-164: 문서 미열림 상태에서 편집 기능 비활성화."""

    def test_actions_disabled_without_document(self, main_window):
        win = main_window

        # 저장 비활성
        assert not win._toolbar._act_save.isEnabled()

        # 페이지 편집 비활성
        assert not win._toolbar._act_delete.isEnabled()
        assert not win._toolbar._act_extract.isEnabled()
        assert not win._toolbar._act_insert.isEnabled()

        # Undo/Redo 비활성
        assert not win._act_undo.isEnabled()
        assert not win._act_redo.isEnabled()

    def test_annotation_tools_disabled_without_document(self, main_window):
        """어노테이션 도구 버튼이 비활성화 상태여야 합니다."""
        win = main_window
        for tool, action in win._toolbar._tool_actions.items():
            if tool != AnnotationTool.SELECT:
                assert not action.isEnabled(), \
                    f"문서 미열림 시 {tool} 도구가 활성화되어 있습니다"

    def test_open_button_is_enabled(self, main_window):
        """열기 버튼만 활성화 상태여야 합니다."""
        win = main_window
        assert win._toolbar._act_open.isEnabled()
