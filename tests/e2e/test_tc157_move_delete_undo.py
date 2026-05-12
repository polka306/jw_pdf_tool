"""TC-157: 페이지 순서변경 -> 삭제 -> Undo x2 -> 원래 상태 복원."""

from __future__ import annotations

from app.core.command_manager import MovePageCommand, DeletePagesCommand
from tests.helpers import load_pdf_directly


class TestTC157:
    """TC-157: 페이지 순서변경 -> 삭제 -> Undo x2 -> 원래 상태 복원."""

    def test_double_undo_restores_original(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(
            num_pages=3,
            page_texts=["PageA", "PageB", "PageC"],
        )
        load_pdf_directly(win, path)

        def get_texts():
            return [
                win._tab_widget.active_tab().doc.raw[i].get_text().strip()
                for i in range(win._tab_widget.active_tab().doc.raw.page_count)
            ]

        original_texts = get_texts()

        # 1) 0번 페이지를 2번 위치로 이동
        cmd_move = MovePageCommand(win._tab_widget.active_tab().doc.raw, 0, 2)
        win._tab_widget.active_tab().cmd_mgr.execute(cmd_move)
        win._refresh_after_edit()
        assert get_texts() != original_texts  # 순서가 변경됨

        # 2) 현재 1번 페이지 삭제
        cmd_del = DeletePagesCommand(win._tab_widget.active_tab().doc.raw, [1])
        win._tab_widget.active_tab().cmd_mgr.execute(cmd_del)
        win._refresh_after_edit()
        assert win._tab_widget.active_tab().doc.raw.page_count == 2

        # 3) Undo (삭제 취소) — win._undo()로 UI 새로고침 포함
        win._undo()
        assert win._tab_widget.active_tab().doc.raw.page_count == 3

        # 4) Undo (이동 취소)
        win._undo()
        assert get_texts() == original_texts  # 원본 복원 확인
