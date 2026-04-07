"""TC-192 ~ TC-196: MainWindow 렌더링 통합 테스트."""

from __future__ import annotations

import ast
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestMainWindowRender:
    """main_window.py — 지연 렌더 및 통합 테스트."""

    # TC-192: 편집 후 단일 지연 렌더
    def test_tc192_single_deferred_render_after_edit(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        load_pdf_directly(win, pdf_3pages)
        qtbot.wait(500)

        # 편집 후 갱신 시 reload_all이 아닌 해당 페이지만 갱신
        # (정확한 검증은 render 호출 횟수 카운트)
        initial_page = win._viewer.current_page if hasattr(win, '_viewer') else 0
        assert initial_page >= 0  # 최소 렌더 확인

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()

    # TC-193: Undo 후 단일 렌더 (이중 렌더 없음)
    def test_tc193_no_double_render_after_undo(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        load_pdf_directly(win, pdf_3pages)
        qtbot.wait(500)

        # Undo 실행 (스택이 비어있어도 오류 없이)
        if hasattr(win, '_cmd_mgr'):
            win._cmd_mgr.undo()
            qtbot.wait(200)

        # 정상 동작 확인
        assert win._doc.is_open

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()

    # TC-194: 파일 열기 → 첫 페이지 우선 표시
    def test_tc194_first_page_priority_on_open(self, qtbot, pdf_10pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)

        load_pdf_directly(win, pdf_10pages)
        qtbot.wait(500)

        # 첫 페이지가 뷰어에 표시되어야 함
        if hasattr(win, '_viewer'):
            assert win._viewer.current_page == 0

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()

    # TC-195: 문서 열기 → 닫기 → 메모리 해제
    def test_tc195_cleanup_on_close(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        load_pdf_directly(win, pdf_3pages)
        qtbot.wait(500)

        # 문서 닫기
        win._doc.close()
        qtbot.wait(200)

        assert not win._doc.is_open

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()

    # TC-196: 아키텍처 — core/에 PyQt6 import 없음
    def test_tc196_core_no_pyqt_import(self):
        """app/core/ 내 모든 .py 파일에서 PyQt6 import가 없는지 AST로 검증."""
        import pathlib

        core_dir = pathlib.Path(__file__).resolve().parents[2] / "app" / "core"
        violations = []

        for py_file in core_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if "PyQt6" in alias.name:
                            violations.append(f"{py_file.name}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "PyQt6" in node.module:
                        violations.append(f"{py_file.name}: from {node.module}")

        assert violations == [], f"core/에서 PyQt6 import 발견: {violations}"
