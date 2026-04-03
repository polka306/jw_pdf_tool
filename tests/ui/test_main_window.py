"""MainWindow 단위/컴포넌트 테스트."""

from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QMessageBox

from app.core.annotator import AnnotationTool
from app.ui.main_window import MainWindow
from tests.helpers import (
    FakeInsertDialog,
    load_pdf_directly,
    patch_file_dialog_open,
    patch_file_dialog_save,
    patch_insert_dialog_cancel,
    patch_message_box_no,
    patch_message_box_warning,
    patch_message_box_yes,
)


# -- TC-003~TC-014: 문서 관리 --


class TestDocumentOpen:
    def test_open_cancel(self, main_window, monkeypatch):
        """TC-003: 열기 대화상자 취소 시 문서가 열리지 않아야 한다."""
        patch_file_dialog_open(monkeypatch, return_path=None)
        main_window._open_file()
        assert not main_window._doc.is_open

    def test_ctrl_o_shortcut_binding(self, main_window):
        """TC-006: Ctrl+O 단축키 바인딩 확인."""
        shortcut = main_window._toolbar._act_open.shortcut().toString()
        assert "O" in shortcut.upper()


class TestDocumentSave:
    def test_save_disabled_without_doc(self, main_window):
        """TC-008: 문서 미열림 시 저장 버튼 비활성화."""
        assert not main_window._toolbar._act_save.isEnabled()

    def test_save_as(self, main_window, pdf_3pages, tmp_path, monkeypatch):
        """TC-010: 다른 이름으로 저장."""
        load_pdf_directly(main_window, pdf_3pages)
        save_path = str(tmp_path / "new_name.pdf")
        patch_file_dialog_save(monkeypatch, return_path=save_path)
        main_window._save_as()
        assert os.path.exists(save_path)

    def test_save_as_appends_pdf_ext(self, main_window, pdf_3pages, tmp_path, monkeypatch):
        """TC-011: .pdf 확장자 자동 추가."""
        load_pdf_directly(main_window, pdf_3pages)
        no_ext_path = str(tmp_path / "no_extension")
        patch_file_dialog_save(monkeypatch, return_path=no_ext_path)
        main_window._save_as()
        assert os.path.exists(no_ext_path + ".pdf")

    def test_save_as_cancel(self, main_window, pdf_3pages, monkeypatch):
        """TC-012: 다른 이름으로 저장 취소."""
        load_pdf_directly(main_window, pdf_3pages)
        patch_file_dialog_save(monkeypatch, return_path=None)
        main_window._save_as()  # 예외 없이 동작


class TestDocumentClose:
    def test_close_no_crash(self, main_window):
        """TC-013: 문서 없이 앱 종료 시 크래시 없음."""
        main_window.close()

    def test_close_with_doc_open(self, main_window, pdf_3pages):
        """TC-014: 문서 열린 상태에서 앱 종료."""
        load_pdf_directly(main_window, pdf_3pages)
        assert main_window._doc.is_open
        main_window.close()


# -- TC-049~TC-063: 페이지 편집 --


class TestPageDelete:
    def test_delete_single_page_blocked(self, main_window, pdf_1page, monkeypatch):
        """TC-049: 1페이지 문서에서 삭제 시도 → 경고."""
        load_pdf_directly(main_window, pdf_1page)
        warnings = patch_message_box_warning(monkeypatch)
        main_window._delete_pages([0])
        assert len(warnings) == 1
        assert main_window._doc.page_count == 1

    def test_delete_all_pages_blocked(self, main_window, tmp_path, monkeypatch):
        """TC-050: 2페이지 문서에서 전체 선택 삭제 시도 → 경고."""
        from tests.conftest import _make_pdf
        path = _make_pdf(2, tmp_path)
        load_pdf_directly(main_window, path)
        warnings = patch_message_box_warning(monkeypatch)
        main_window._delete_pages([0, 1])
        assert len(warnings) == 1
        assert main_window._doc.page_count == 2

    def test_delete_cancel(self, main_window, pdf_3pages, monkeypatch):
        """TC-052: 삭제 확인에서 No → 변경 없음."""
        load_pdf_directly(main_window, pdf_3pages)
        patch_message_box_no(monkeypatch)
        main_window._delete_pages([1])
        assert main_window._doc.page_count == 3

    def test_toolbar_delete_button(self, main_window, pdf_3pages, monkeypatch):
        """TC-053: 툴바 삭제 버튼으로 삭제."""
        load_pdf_directly(main_window, pdf_3pages)
        patch_message_box_yes(monkeypatch)
        main_window._page_panel._list.setCurrentRow(0)
        main_window._toolbar._act_delete.trigger()
        assert main_window._doc.page_count == 2


class TestPageExtract:
    def test_extract_cancel(self, main_window, pdf_3pages, monkeypatch):
        """TC-058: 추출 대화상자 취소."""
        load_pdf_directly(main_window, pdf_3pages)
        patch_file_dialog_save(monkeypatch, return_path=None)
        main_window._extract_pages([0])
        # 취소 시 예외 없이 동작


class TestPageInsert:
    def test_insert_cancel(self, main_window, pdf_3pages, monkeypatch):
        """TC-063: 삽입 대화상자 취소."""
        from app.ui.dialogs.insert_dialog import InsertDialog

        load_pdf_directly(main_window, pdf_3pages)

        class _FakeCancel:
            DialogCode = InsertDialog.DialogCode

            def __init__(self, parent):
                pass

            def exec(self):
                return 0  # Rejected

        monkeypatch.setattr("app.ui.main_window.InsertDialog", _FakeCancel)
        main_window._insert_pages(insert_before=0)
        assert main_window._doc.page_count == 3


# -- TC-100~TC-112: Undo/Redo --


class TestUndoRedo:
    def test_undo_via_action(self, main_window, pdf_3pages, monkeypatch):
        """TC-100: Undo 기본 동작."""
        load_pdf_directly(main_window, pdf_3pages)
        patch_message_box_yes(monkeypatch)
        main_window._delete_pages([0])
        assert main_window._doc.page_count == 2
        main_window._undo()
        assert main_window._doc.page_count == 3

    def test_undo_menu_dynamic_text(self, main_window, pdf_3pages, monkeypatch):
        """TC-108: Undo 메뉴 텍스트에 설명 포함."""
        load_pdf_directly(main_window, pdf_3pages)
        patch_message_box_yes(monkeypatch)
        main_window._delete_pages([0])
        text = main_window._act_undo.text()
        assert "실행 취소" in text
        assert "삭제" in text

    def test_redo_via_action(self, main_window, pdf_3pages, monkeypatch):
        """TC-109: Redo 기본 동작."""
        load_pdf_directly(main_window, pdf_3pages)
        patch_message_box_yes(monkeypatch)
        main_window._delete_pages([0])
        main_window._undo()
        assert main_window._doc.page_count == 3
        main_window._redo()
        assert main_window._doc.page_count == 2

    def test_new_action_clears_redo(self, main_window, pdf_3pages, monkeypatch):
        """TC-110: 새 액션 실행 시 Redo 스택 초기화."""
        load_pdf_directly(main_window, pdf_3pages)
        patch_message_box_yes(monkeypatch)
        main_window._delete_pages([0])
        main_window._undo()
        assert main_window._cmd_mgr.can_redo
        main_window._delete_pages([0])
        assert not main_window._cmd_mgr.can_redo


# -- TC-151: 어노테이션 후 단일 페이지 갱신 --


class TestAnnotationRefresh:
    def test_annotation_single_page_refresh(self, main_window, pdf_3pages):
        """TC-151: 어노테이션 추가 후 페이지 갱신 및 Undo 가능."""
        load_pdf_directly(main_window, pdf_3pages)
        from app.core.annotator import AnnotationStyle, add_rect
        page_idx = main_window._viewer.current_page

        def annotate():
            add_rect(main_window._doc.raw[page_idx], 50, 50, 200, 150, AnnotationStyle())

        main_window._on_annotation_requested(annotate, "사각형 추가")
        assert main_window._cmd_mgr.can_undo


# -- TC-064: 도구 전환 --


class TestToolSwitching:
    def test_tool_switching_updates_viewer(self, main_window, pdf_3pages):
        """TC-064: 도구 전환 시 뷰어의 _current_tool이 업데이트된다."""
        load_pdf_directly(main_window, pdf_3pages)
        toolbar = main_window._toolbar
        toolbar._tool_actions[AnnotationTool.TEXT].trigger()
        assert main_window._viewer._current_tool == AnnotationTool.TEXT
        toolbar._tool_actions[AnnotationTool.RECT].trigger()
        assert main_window._viewer._current_tool == AnnotationTool.RECT
        toolbar._tool_actions[AnnotationTool.SELECT].trigger()
        assert main_window._viewer._current_tool == AnnotationTool.SELECT
