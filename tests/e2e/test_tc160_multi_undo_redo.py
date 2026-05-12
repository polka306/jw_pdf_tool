"""TC-160: 다중 어노테이션 -> 연속 Undo -> 연속 Redo."""

from __future__ import annotations

from app.core.annotator import AnnotationStyle, add_rect, add_text, add_line
from tests.helpers import load_pdf_directly


class TestTC160:
    """TC-160: 다중 어노테이션 -> 연속 Undo -> 연속 Redo."""

    def test_six_annotations_full_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=1)
        load_pdf_directly(win, path)

        style = AnnotationStyle(color=(1, 0, 0))
        page_idx = 0

        initial_drawings = len(win._tab_widget.active_tab().doc.raw[page_idx].get_drawings())

        # 사각형 3개 + 텍스트 2개 + 선 1개 = 6개 어노테이션
        annotations = [
            ("사각형1", lambda: add_rect(win._tab_widget.active_tab().doc.raw[page_idx], 10, 10, 100, 100, style)),
            ("사각형2", lambda: add_rect(win._tab_widget.active_tab().doc.raw[page_idx], 110, 10, 200, 100, style)),
            ("사각형3", lambda: add_rect(win._tab_widget.active_tab().doc.raw[page_idx], 210, 10, 300, 100, style)),
            ("텍스트1", lambda: add_text(win._tab_widget.active_tab().doc.raw[page_idx], 50, 200, "Text1", style)),
            ("텍스트2", lambda: add_text(win._tab_widget.active_tab().doc.raw[page_idx], 50, 300, "Text2", style)),
            ("선1",     lambda: add_line(win._tab_widget.active_tab().doc.raw[page_idx], 10, 400, 500, 400, style)),
        ]

        for desc, fn in annotations:
            win._on_annotation_requested(fn, desc)

        after_all = len(win._tab_widget.active_tab().doc.raw[page_idx].get_drawings())
        assert after_all > initial_drawings

        # Undo 6회 -> 원래 상태 (win._undo()로 UI 새로고침 포함)
        for _ in range(6):
            assert win._tab_widget.active_tab().cmd_mgr.can_undo
            win._undo()

        assert len(win._tab_widget.active_tab().doc.raw[page_idx].get_drawings()) == initial_drawings
        assert not win._tab_widget.active_tab().cmd_mgr.can_undo

        # Redo 6회 -> 다시 6개 어노테이션 상태
        for _ in range(6):
            assert win._tab_widget.active_tab().cmd_mgr.can_redo
            win._redo()

        assert len(win._tab_widget.active_tab().doc.raw[page_idx].get_drawings()) == after_all
        assert not win._tab_widget.active_tab().cmd_mgr.can_redo
