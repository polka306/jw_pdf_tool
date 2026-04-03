"""공통 monkeypatch 헬퍼 모듈.

Unit/Component/E2E 전체에서 공유하는 단일 헬퍼.
monkeypatch 경로 규칙: 사용되는 모듈 기준 (예: "app.ui.main_window.QFileDialog...").
"""

from __future__ import annotations

import os

from PyQt6.QtWidgets import QMessageBox

from app.core.annotator import AnnotationTool


# ── PDF 로드 헬퍼 ──────────────────────────────────────────────────────────

def load_pdf_directly(win, path: str) -> None:
    """QFileDialog 없이 MainWindow에 PDF를 직접 로드한다."""
    win._doc.open(path)
    win._cmd_mgr.clear()
    win._page_panel.load_document(win._doc)
    win._viewer.set_document(win._doc)
    win._toolbar.set_document_loaded(True)
    win._toolbar.set_tool_checked(AnnotationTool.SELECT)
    win._update_page_status(0)
    win._toolbar.update_zoom_display(win._viewer.zoom)
    win._lbl_file.setText(os.path.basename(path))
    win._update_undo_actions()
    win._sync_annot_style()


# ── QFileDialog 패치 ──────────────────────────────────────────────────────

def patch_file_dialog_open(monkeypatch, return_path: str | None = None):
    """QFileDialog.getOpenFileName을 패치."""
    result = ("", "") if return_path is None else (return_path, "PDF 파일 (*.pdf)")
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getOpenFileName",
        lambda *a, **kw: result,
    )


def patch_file_dialog_save(monkeypatch, return_path: str | None = None):
    """QFileDialog.getSaveFileName을 패치."""
    result = ("", "") if return_path is None else (return_path, "PDF 파일 (*.pdf)")
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getSaveFileName",
        lambda *a, **kw: result,
    )


# ── QMessageBox 패치 ─────────────────────────────────────────────────────

def patch_message_box_yes(monkeypatch):
    """QMessageBox.question -> Yes."""
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.Yes,
    )


def patch_message_box_no(monkeypatch):
    """QMessageBox.question -> No."""
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.No,
    )


def patch_message_box_warning(monkeypatch):
    """QMessageBox.warning 호출을 감지."""
    warnings: list = []
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.warning",
        lambda *a, **kw: warnings.append(a),
    )
    return warnings


def patch_message_box_critical(monkeypatch):
    """QMessageBox.critical 호출을 감지."""
    errors: list = []
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.critical",
        lambda *a, **kw: errors.append(a),
    )
    return errors


# ── QColorDialog 패치 ────────────────────────────────────────────────────

def patch_color_dialog(monkeypatch, r=0, g=0, b=255):
    """QColorDialog.getColor를 패치 (toolbar 모듈 기준 경로)."""
    from PyQt6.QtGui import QColor
    monkeypatch.setattr(
        "app.ui.toolbar.QColorDialog.getColor",
        lambda *a, **kw: QColor(r, g, b),
    )


def patch_color_dialog_cancel(monkeypatch):
    """QColorDialog.getColor 취소 (invalid QColor 반환)."""
    from PyQt6.QtGui import QColor
    monkeypatch.setattr(
        "app.ui.toolbar.QColorDialog.getColor",
        lambda *a, **kw: QColor(),
    )


# ── QInputDialog 패치 ────────────────────────────────────────────────────

def patch_input_dialog(monkeypatch, text: str = "테스트 텍스트", ok: bool = True):
    """QInputDialog.getText를 패치 (pdf_viewer 모듈 기준 경로)."""
    monkeypatch.setattr(
        "app.ui.pdf_viewer.QInputDialog.getText",
        lambda *a, **kw: (text, ok),
    )


def patch_input_dialog_cancel(monkeypatch):
    """QInputDialog.getText 취소."""
    monkeypatch.setattr(
        "app.ui.pdf_viewer.QInputDialog.getText",
        lambda *a, **kw: ("", False),
    )


# ── InsertDialog 대체 ────────────────────────────────────────────────────

class FakeInsertDialog:
    """InsertDialog 대체용."""

    def __init__(self, parent, source_path="", indices=None):
        self._source_path = source_path
        self._indices = indices or []

    def exec(self):
        return 1  # Accepted

    def source_path(self):
        return self._source_path

    def selected_indices(self):
        return self._indices


def patch_insert_dialog(monkeypatch, source_path: str, indices: list[int]):
    """InsertDialog를 모킹하여 특정 소스/인덱스를 반환."""
    class _Fake(FakeInsertDialog):
        def __init__(self, parent):
            super().__init__(parent, source_path, indices)
    monkeypatch.setattr("app.ui.main_window.InsertDialog", _Fake)


def patch_insert_dialog_cancel(monkeypatch):
    """InsertDialog를 모킹하여 취소."""
    class _FakeCancel(FakeInsertDialog):
        def __init__(self, parent):
            super().__init__(parent)
        def exec(self):
            return 0  # Rejected
    monkeypatch.setattr("app.ui.main_window.InsertDialog", _FakeCancel)
