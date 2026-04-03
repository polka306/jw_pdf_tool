"""TC-166: Command 패턴 4종 Undo/Redo 순차 검증."""

from __future__ import annotations

from app.core.annotator import AnnotationStyle, add_rect
from app.core.command_manager import (
    AddAnnotationCommand,
    DeletePagesCommand,
    InsertPagesCommand,
    MovePageCommand,
)
from tests.helpers import load_pdf_directly


class TestTC166:
    """TC-166: Command 패턴 4종 Undo/Redo 순차 검증."""

    def _get_page_texts(self, doc):
        return [doc[i].get_text().strip() for i in range(doc.page_count)]

    def test_move_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=5, page_texts=["A", "B", "C", "D", "E"])
        load_pdf_directly(win, path)

        original = self._get_page_texts(win._doc.raw)

        cmd = MovePageCommand(win._doc.raw, 0, 3)
        win._cmd_mgr.execute(cmd)
        moved = self._get_page_texts(win._doc.raw)
        assert moved != original

        win._cmd_mgr.undo()
        assert self._get_page_texts(win._doc.raw) == original

        win._cmd_mgr.redo()
        assert self._get_page_texts(win._doc.raw) == moved

    def test_delete_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=5, page_texts=["A", "B", "C", "D", "E"])
        load_pdf_directly(win, path)

        cmd = DeletePagesCommand(win._doc.raw, [1])
        win._cmd_mgr.execute(cmd)
        assert win._doc.raw.page_count == 4

        win._cmd_mgr.undo()
        assert win._doc.raw.page_count == 5
        assert "B" in win._doc.raw[1].get_text()

        win._cmd_mgr.redo()
        assert win._doc.raw.page_count == 4

    def test_insert_undo_redo(self, main_window, pdf_factory):
        win = main_window
        main_path = pdf_factory(num_pages=3, page_texts=["M1", "M2", "M3"])
        source_path = pdf_factory(num_pages=2, page_texts=["S1", "S2"])
        load_pdf_directly(win, main_path)

        cmd = InsertPagesCommand(win._doc.raw, source_path, [0], insert_before=1)
        win._cmd_mgr.execute(cmd)
        assert win._doc.raw.page_count == 4

        win._cmd_mgr.undo()
        assert win._doc.raw.page_count == 3

        win._cmd_mgr.redo()
        assert win._doc.raw.page_count == 4
        assert "S1" in win._doc.raw[1].get_text()

    def test_annotation_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=1)
        load_pdf_directly(win, path)

        style = AnnotationStyle()
        initial_drawings = len(win._doc.raw[0].get_drawings())

        def annotate():
            add_rect(win._doc.raw[0], 10, 10, 100, 100, style)

        cmd = AddAnnotationCommand(win._doc.raw, 0, annotate, "사각형")
        win._cmd_mgr.execute(cmd)
        after_add = len(win._doc.raw[0].get_drawings())
        assert after_add > initial_drawings

        win._cmd_mgr.undo()
        assert len(win._doc.raw[0].get_drawings()) == initial_drawings

        win._cmd_mgr.redo()
        assert len(win._doc.raw[0].get_drawings()) == after_add

    def test_all_four_sequential_undo(self, main_window, pdf_factory):
        """4종 작업을 순차 실행 후 4회 Undo로 원상 복원."""
        win = main_window
        main_path = pdf_factory(num_pages=5, page_texts=["A", "B", "C", "D", "E"])
        source_path = pdf_factory(num_pages=2, page_texts=["S1", "S2"])
        load_pdf_directly(win, main_path)

        original_count = win._doc.raw.page_count
        original_texts = self._get_page_texts(win._doc.raw)
        original_drawings = len(win._doc.raw[0].get_drawings())

        # 1) 이동
        win._cmd_mgr.execute(MovePageCommand(win._doc.raw, 0, 2))
        win._refresh_after_edit()

        # 2) 삭제
        win._cmd_mgr.execute(DeletePagesCommand(win._doc.raw, [0]))
        win._refresh_after_edit()

        # 3) 삽입
        win._cmd_mgr.execute(
            InsertPagesCommand(win._doc.raw, source_path, [0], insert_before=0)
        )
        win._refresh_after_edit()

        # 4) 어노테이션
        style = AnnotationStyle()

        def add_fn():
            add_rect(win._doc.raw[0], 10, 10, 100, 100, style)

        cmd = AddAnnotationCommand(win._doc.raw, 0, add_fn, "사각형")
        win._cmd_mgr.execute(cmd)

        # 4회 Undo -> 원본 복원
        for _ in range(4):
            win._undo()

        assert win._doc.raw.page_count == original_count
        assert self._get_page_texts(win._doc.raw) == original_texts
