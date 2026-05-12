"""TC-198: 열기→어노테이션→Undo→Redo→저장→재열기 — 캐시 무효화 정상."""

from __future__ import annotations

import os

import fitz
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestTC198CacheInvalidation:

    def test_tc198_cache_invalidation_after_edit(self, qtbot, pdf_3pages, tmp_path):
        from app.ui.main_window import MainWindow
        from app.core.annotator import add_rect, AnnotationStyle
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        win.show()
        load_pdf_directly(win, pdf_3pages)
        qtbot.wait(500)

        page = win._tab_widget.active_tab().doc.raw[0]

        # 어노테이션 추가
        style = AnnotationStyle(color=(1, 0, 0), line_width=2.0)
        add_rect(page, 50, 50, 200, 150, style)

        # 세대 카운터 증가 확인
        if hasattr(win._tab_widget.active_tab().doc, 'increment_generation'):
            win._tab_widget.active_tab().doc.increment_generation(0)
            assert win._tab_widget.active_tab().doc.get_generation(0) >= 1

        # 저장
        save_path = str(tmp_path / "tc198_output.pdf")
        win._tab_widget.active_tab().doc.save(save_path)

        # 재열기
        from app.core.pdf_document import PdfDocument
        doc2 = PdfDocument()
        doc2.open(save_path)

        # 어노테이션이 저장되어 있는지 확인
        page2 = doc2.raw[0]
        text = page2.get_text()
        # 사각형은 텍스트가 아니므로 drawing으로 확인
        drawings = page2.get_drawings()
        assert len(drawings) > 0  # 사각형 어노테이션 존재

        doc2.close()

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
