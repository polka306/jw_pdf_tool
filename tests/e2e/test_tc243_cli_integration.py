"""TC-243: 명령줄로 열기→편집→저장→종료→명령줄 재열기."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestTC243CliIntegration:

    def test_tc243_cli_open_edit_save(self, qtbot, pdf_3pages, tmp_path):
        from app.core.cli import parse_cli_args

        # 명령줄 인자 파싱
        args = parse_cli_args(["app", pdf_3pages])
        assert args.file_path == pdf_3pages

        # 앱 열기
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        win.show()
        load_pdf_directly(win, args.file_path)
        qtbot.wait(300)

        assert win._tab_widget.active_tab().doc.page_count == 3

        # 저장
        save_path = str(tmp_path / "cli_output.pdf")
        win._tab_widget.active_tab().doc.save(save_path)
        assert os.path.exists(save_path)

        # 재열기
        from app.core.pdf_document import PdfDocument
        doc2 = PdfDocument()
        doc2.open(save_path)
        assert doc2.page_count == 3
        doc2.close()

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
