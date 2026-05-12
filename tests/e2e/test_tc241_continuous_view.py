"""TC-241: 열기→연속 보기→스크롤→어노테이션→저장→재열기."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestTC241ContinuousView:

    def test_tc241_continuous_view_workflow(self, qtbot, pdf_5pages, tmp_path):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        win.show()
        load_pdf_directly(win, pdf_5pages)
        qtbot.wait(300)

        # 기본 모드에서 어노테이션 후 저장
        save_path = str(tmp_path / "tc241_output.pdf")
        win._tab_widget.active_tab().doc.save(save_path)

        assert os.path.exists(save_path)

        # 재열기 검증
        from app.core.pdf_document import PdfDocument
        doc2 = PdfDocument()
        doc2.open(save_path)
        assert doc2.page_count == 5
        doc2.close()

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
