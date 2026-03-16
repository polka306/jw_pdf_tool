"""CommandManager 및 커맨드 클래스 단위 테스트."""

from __future__ import annotations

import pytest
import fitz

from app.core.command_manager import (
    AddAnnotationCommand,
    CommandManager,
    DeletePagesCommand,
    InsertPagesCommand,
    MovePageCommand,
)


# ── 픽스처 ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def raw_3pages(tmp_path) -> fitz.Document:
    """3-page fitz.Document (메모리)."""
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page {i + 1}", fontsize=20)
    path = str(tmp_path / "raw.pdf")
    doc.save(path)
    doc.close()
    doc = fitz.open(path)
    yield doc
    doc.close()


@pytest.fixture
def cmd_mgr() -> CommandManager:
    return CommandManager()


# ── CommandManager 기본 동작 ──────────────────────────────────────────────────

class TestCommandManager:
    def test_initial_state_empty(self, cmd_mgr):
        assert not cmd_mgr.can_undo
        assert not cmd_mgr.can_redo
        assert cmd_mgr.undo_description is None
        assert cmd_mgr.redo_description is None

    def test_undo_when_empty_returns_none(self, cmd_mgr):
        assert cmd_mgr.undo() is None

    def test_redo_when_empty_returns_none(self, cmd_mgr):
        assert cmd_mgr.redo() is None

    def test_execute_enables_undo(self, cmd_mgr, raw_3pages):
        cmd = MovePageCommand(raw_3pages, 0, 2)
        cmd_mgr.execute(cmd)
        assert cmd_mgr.can_undo

    def test_execute_clears_redo(self, cmd_mgr, raw_3pages):
        # undo 후 redo 스택에 항목 있음
        cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 1))
        cmd_mgr.undo()
        assert cmd_mgr.can_redo
        # 새 커맨드 실행 → redo 스택 초기화
        cmd_mgr.execute(MovePageCommand(raw_3pages, 1, 2))
        assert not cmd_mgr.can_redo

    def test_clear_empties_both_stacks(self, cmd_mgr, raw_3pages):
        cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 2))
        cmd_mgr.undo()
        cmd_mgr.clear()
        assert not cmd_mgr.can_undo
        assert not cmd_mgr.can_redo

    def test_undo_returns_description(self, cmd_mgr, raw_3pages):
        cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 2))
        desc = cmd_mgr.undo()
        assert desc is not None
        assert "이동" in desc

    def test_redo_returns_description(self, cmd_mgr, raw_3pages):
        cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 2))
        cmd_mgr.undo()
        desc = cmd_mgr.redo()
        assert desc is not None


# ── MovePageCommand ───────────────────────────────────────────────────────────

class TestMovePageCommand:
    def test_execute_moves_page(self, raw_3pages):
        """페이지 0을 from=0, to=2로 이동 — fitz 는 'to 앞에 삽입' 의미.

        from < to 이면 제거 후 인덱스 이동으로 실제 위치 = to - 1.
        [P1,P2,P3] → move_page(0,2) → [P2, P1, P3]
        """
        def text_at(doc, idx):
            return doc[idx].get_text().strip()

        before_0 = text_at(raw_3pages, 0)
        cmd = MovePageCommand(raw_3pages, 0, 2)
        cmd.execute()
        # to=2, from<to → 실제 위치 to-1 = 1
        assert text_at(raw_3pages, 1) == before_0

    def test_undo_restores_order(self, raw_3pages):
        """이동 후 Undo → 원래 순서 복원."""
        def texts(doc):
            return [doc[i].get_text().strip() for i in range(doc.page_count)]

        original = texts(raw_3pages)
        cmd = MovePageCommand(raw_3pages, 0, 2)
        cmd.execute()
        cmd.undo()
        assert texts(raw_3pages) == original

    def test_same_index_is_noop(self, raw_3pages):
        """from == to이면 아무것도 변경되지 않아야 합니다."""
        def texts(doc):
            return [doc[i].get_text().strip() for i in range(doc.page_count)]

        original = texts(raw_3pages)
        cmd = MovePageCommand(raw_3pages, 1, 1)
        cmd.execute()
        assert texts(raw_3pages) == original

    def test_description_contains_page_numbers(self):
        doc = fitz.open()
        doc.new_page()
        doc.new_page()
        cmd = MovePageCommand(doc, 0, 1)
        assert "1" in cmd.description and "2" in cmd.description
        doc.close()


# ── DeletePagesCommand ────────────────────────────────────────────────────────

class TestDeletePagesCommand:
    def test_execute_reduces_page_count(self, raw_3pages):
        cmd = DeletePagesCommand(raw_3pages, [1])
        cmd.execute()
        assert raw_3pages.page_count == 2

    def test_undo_restores_page_count(self, raw_3pages):
        cmd = DeletePagesCommand(raw_3pages, [1])
        cmd.execute()
        cmd.undo()
        assert raw_3pages.page_count == 3

    def test_undo_restores_content(self, raw_3pages):
        """삭제된 페이지 내용이 복원되어야 합니다."""
        deleted_text = raw_3pages[1].get_text().strip()
        cmd = DeletePagesCommand(raw_3pages, [1])
        cmd.execute()
        cmd.undo()
        assert raw_3pages[1].get_text().strip() == deleted_text

    def test_delete_multiple_pages(self, raw_3pages):
        cmd = DeletePagesCommand(raw_3pages, [0, 2])
        cmd.execute()
        assert raw_3pages.page_count == 1

    def test_undo_multiple_pages(self, raw_3pages):
        cmd = DeletePagesCommand(raw_3pages, [0, 2])
        cmd.execute()
        cmd.undo()
        assert raw_3pages.page_count == 3

    def test_description_shows_count(self, raw_3pages):
        cmd = DeletePagesCommand(raw_3pages, [0, 1])
        assert "2" in cmd.description


# ── InsertPagesCommand ────────────────────────────────────────────────────────

class TestInsertPagesCommand:
    def test_execute_increases_page_count(self, raw_3pages, pdf_3pages):
        cmd = InsertPagesCommand(raw_3pages, pdf_3pages, [0], insert_before=0)
        cmd.execute()
        assert raw_3pages.page_count == 4

    def test_undo_removes_inserted_pages(self, raw_3pages, pdf_3pages):
        cmd = InsertPagesCommand(raw_3pages, pdf_3pages, [0, 1], insert_before=1)
        cmd.execute()
        cmd.undo()
        assert raw_3pages.page_count == 3

    def test_insert_at_beginning(self, raw_3pages, pdf_3pages):
        before_text = raw_3pages[0].get_text().strip()
        cmd = InsertPagesCommand(raw_3pages, pdf_3pages, [0], insert_before=0)
        cmd.execute()
        # 원래 첫 페이지는 1번으로 밀려남
        assert raw_3pages[1].get_text().strip() == before_text

    def test_description_shows_count(self, raw_3pages, pdf_3pages):
        cmd = InsertPagesCommand(raw_3pages, pdf_3pages, [0, 1], insert_before=0)
        assert "2" in cmd.description


# ── AddAnnotationCommand ──────────────────────────────────────────────────────

class TestAddAnnotationCommand:
    def test_execute_calls_annotate_fn(self, raw_3pages):
        called = []

        def annotate():
            called.append(True)

        cmd = AddAnnotationCommand(raw_3pages, 0, annotate)
        cmd.execute()
        assert len(called) == 1

    def test_undo_restores_page_content(self, raw_3pages):
        """어노테이션 추가 후 Undo → 원래 페이지 상태로 복원."""
        from app.core.annotator import AnnotationStyle, add_rect
        style = AnnotationStyle()
        page_idx = 0

        before_len = len(raw_3pages[page_idx].get_drawings())

        def annotate():
            add_rect(raw_3pages[page_idx], 50, 50, 200, 150, style)

        cmd = AddAnnotationCommand(raw_3pages, page_idx, annotate)
        cmd.execute()
        # 어노테이션 추가됨
        assert len(raw_3pages[page_idx].get_drawings()) > before_len

        cmd.undo()
        # 복원됨
        assert len(raw_3pages[page_idx].get_drawings()) == before_len

    def test_redo_reapplies_annotation(self, raw_3pages):
        """Undo 후 Redo → 어노테이션 재적용."""
        from app.core.annotator import AnnotationStyle, add_rect
        style = AnnotationStyle()
        page_idx = 0

        def annotate():
            add_rect(raw_3pages[page_idx], 10, 10, 100, 100, style)

        cmd = AddAnnotationCommand(raw_3pages, page_idx, annotate)
        cmd.execute()
        after_execute = len(raw_3pages[page_idx].get_drawings())

        cmd.undo()
        cmd.execute()  # redo equivalent
        assert len(raw_3pages[page_idx].get_drawings()) == after_execute

    def test_default_description(self, raw_3pages):
        cmd = AddAnnotationCommand(raw_3pages, 0, lambda: None)
        assert "어노테이션" in cmd.description

    def test_custom_description(self, raw_3pages):
        cmd = AddAnnotationCommand(raw_3pages, 0, lambda: None, description="사각형 추가")
        assert cmd.description == "사각형 추가"
