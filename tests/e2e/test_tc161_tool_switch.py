"""TC-161: 어노테이션 메뉴에서 도구 전환 후 작업 수행."""

from __future__ import annotations

from app.core.annotator import AnnotationTool, AnnotationStyle, add_rect, add_ellipse
from tests.helpers import load_pdf_directly


class TestTC161:
    """TC-161: 어노테이션 메뉴에서 도구 전환 후 작업 수행."""

    def test_menu_tool_switch_enables_drawing(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=1)
        load_pdf_directly(win, path)

        style = AnnotationStyle()
        page_idx = 0

        # 1) 사각형 도구로 전환 (QAction trigger = 실제 메뉴 클릭 시뮬레이션)
        win._toolbar._tool_actions[AnnotationTool.RECT].trigger()
        assert win._tab_widget.active_tab().viewer._current_tool == AnnotationTool.RECT

        # 2) 사각형 그리기
        before_rect = len(win._tab_widget.active_tab().doc.raw[page_idx].get_drawings())

        def add_rect_fn():
            add_rect(win._tab_widget.active_tab().doc.raw[page_idx], 50, 50, 200, 150, style)

        win._on_annotation_requested(add_rect_fn, "사각형")
        drawings_after_rect = len(win._tab_widget.active_tab().doc.raw[page_idx].get_drawings())
        assert drawings_after_rect > before_rect

        # 3) 타원 도구 전환
        win._toolbar._tool_actions[AnnotationTool.ELLIPSE].trigger()
        assert win._tab_widget.active_tab().viewer._current_tool == AnnotationTool.ELLIPSE

        # 4) 타원 그리기
        def add_ellipse_fn():
            add_ellipse(win._tab_widget.active_tab().doc.raw[page_idx], 250, 50, 450, 200, style)

        win._on_annotation_requested(add_ellipse_fn, "타원")
        drawings_after_ellipse = len(win._tab_widget.active_tab().doc.raw[page_idx].get_drawings())
        assert drawings_after_ellipse > drawings_after_rect

        # 5) 선택 도구 복귀
        win._toolbar._tool_actions[AnnotationTool.SELECT].trigger()
        assert win._tab_widget.active_tab().viewer._current_tool == AnnotationTool.SELECT
