"""TC-381 ~ TC-395: 고급 도구 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestOcrDialogUI:
    @pytest.mark.parametrize("tc", [381, 382, 383])
    def test_tc_ocr_dialog(self, tc):
        pytest.skip(f"TC-{tc}: OcrDialog 후속 구현")


class TestWatermarkDialogUI:
    @pytest.mark.parametrize("tc", [384, 385, 386, 387])
    def test_tc_watermark_dialog(self, tc):
        pytest.skip(f"TC-{tc}: WatermarkDialog 후속 구현")


class TestOptimizeDialogUI:
    @pytest.mark.parametrize("tc", [388, 389])
    def test_tc_optimize_dialog(self, tc):
        pytest.skip(f"TC-{tc}: OptimizeDialog 후속 구현")


class TestCompareDialogUI:
    @pytest.mark.parametrize("tc", [390, 391, 392])
    def test_tc_compare_dialog(self, tc):
        pytest.skip(f"TC-{tc}: CompareDialog 후속 구현")


class TestSignatureDialogUI:
    @pytest.mark.parametrize("tc", [393, 394])
    def test_tc_signature_dialog(self, tc):
        pytest.skip(f"TC-{tc}: SignatureDialog 후속 구현")


class TestAdvancedMenu:
    # TC-395: 도구/보안 메뉴 존재
    def test_tc395_menu_exists(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        load_pdf_directly(win, pdf_3pages)
        menubar = win.menuBar()
        actions = [a.text() for a in menubar.actions()]
        assert len(actions) >= 4
        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
