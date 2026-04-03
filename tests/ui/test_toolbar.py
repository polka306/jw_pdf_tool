"""MainToolBar 위젯 테스트."""

from __future__ import annotations

import pytest

from app.core.annotator import AnnotationTool
from app.ui.toolbar import MainToolBar


@pytest.fixture
def toolbar(qtbot):
    tb = MainToolBar()
    qtbot.addWidget(tb)
    tb.set_document_loaded(True)
    return tb


class TestToolBarAnnotation:
    def test_exclusive_tool_toggle(self, toolbar, qtbot):
        """TC-064: 도구 배타적 전환."""
        tb = toolbar
        tb._tool_actions[AnnotationTool.TEXT].trigger()
        assert tb._tool_actions[AnnotationTool.TEXT].isChecked()
        assert not tb._tool_actions[AnnotationTool.RECT].isChecked()

        tb._tool_actions[AnnotationTool.RECT].trigger()
        assert tb._tool_actions[AnnotationTool.RECT].isChecked()
        assert not tb._tool_actions[AnnotationTool.TEXT].isChecked()

        tb._tool_actions[AnnotationTool.ELLIPSE].trigger()
        assert tb._tool_actions[AnnotationTool.ELLIPSE].isChecked()
        assert not tb._tool_actions[AnnotationTool.RECT].isChecked()

    def test_escape_selects_tool(self, toolbar):
        """TC-065: SELECT 도구로 복귀 (QAction.trigger 방식)."""
        tb = toolbar
        tb._tool_actions[AnnotationTool.RECT].trigger()
        assert tb._tool_actions[AnnotationTool.RECT].isChecked()
        tb._tool_actions[AnnotationTool.SELECT].trigger()
        assert tb._tool_actions[AnnotationTool.SELECT].isChecked()
        assert not tb._tool_actions[AnnotationTool.RECT].isChecked()

    def test_tool_group_is_exclusive(self, toolbar):
        """TC-139: QActionGroup이 배타적인지 확인."""
        assert toolbar._tool_group.isExclusive()

    def test_width_change_signal(self, toolbar, qtbot):
        """TC-068: 선 굵기 변경 시그널."""
        with qtbot.waitSignal(toolbar.width_changed, timeout=1000):
            toolbar._width_spin.setValue(5.0)

    def test_width_min_value(self, toolbar):
        """TC-069: 선 굵기 최솟값."""
        assert toolbar._width_spin.minimum() == 0.5

    def test_width_max_value(self, toolbar):
        """TC-070: 선 굵기 최댓값."""
        assert toolbar._width_spin.maximum() == 20.0

    def test_font_size_min(self, toolbar):
        """TC-081: 폰트 크기 최솟값."""
        assert toolbar._font_size_spin.minimum() == 6

    def test_font_size_max(self, toolbar):
        """TC-082: 폰트 크기 최댓값."""
        assert toolbar._font_size_spin.maximum() == 72


class TestToolBarTextStyle:
    def test_text_style_visibility_toggle(self, toolbar):
        """TC-085: TEXT 도구 활성화/비활성화에 따른 스타일 컨트롤 토글."""
        tb = toolbar
        tb.set_text_tool_active(False)
        assert not tb._font_combo.isEnabled()
        assert not tb._font_size_spin.isEnabled()
        assert not tb._act_bold.isEnabled()
        assert not tb._act_italic.isEnabled()

        tb.set_text_tool_active(True)
        assert tb._font_combo.isEnabled()
        assert tb._font_size_spin.isEnabled()
        assert tb._act_bold.isEnabled()
        assert tb._act_italic.isEnabled()


class TestToolBarZoom:
    def test_zoom_controls_exist(self, toolbar):
        """TC-140: 줌 컨트롤 존재 및 범위."""
        assert toolbar._act_zoom_in is not None
        assert toolbar._act_zoom_out is not None
        assert toolbar._act_zoom_fit is not None
        assert toolbar._zoom_spin is not None
        assert toolbar._zoom_spin.minimum() == 25
        assert toolbar._zoom_spin.maximum() == 400
