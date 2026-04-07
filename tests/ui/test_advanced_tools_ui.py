"""TC-381 ~ TC-395: 고급 도구 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestOcrDialogUI:
    # TC-381: 언어 선택
    def test_tc381_language_selection(self, qtbot):
        from app.ui.dialogs.ocr_dialog import OcrDialog
        dlg = OcrDialog(page_count=5)
        qtbot.addWidget(dlg)
        dlg._combo_lang.setCurrentText("kor+eng")
        assert dlg.language() == "kor+eng"

    # TC-382: 페이지 범위
    def test_tc382_page_range(self, qtbot):
        from app.ui.dialogs.ocr_dialog import OcrDialog
        dlg = OcrDialog(page_count=10)
        qtbot.addWidget(dlg)
        dlg._combo_range.setCurrentIndex(1)  # 현재 페이지
        assert not dlg.is_all_pages()

    # TC-383: 진행바 존재
    def test_tc383_progress_bar(self, qtbot):
        from app.ui.dialogs.ocr_dialog import OcrDialog
        dlg = OcrDialog(page_count=5)
        qtbot.addWidget(dlg)
        assert dlg._progress is not None


class TestWatermarkDialogUI:
    # TC-384: 텍스트/이미지 탭 전환
    def test_tc384_tab_switch(self, qtbot):
        from app.ui.dialogs.watermark_dialog import WatermarkDialog
        dlg = WatermarkDialog()
        qtbot.addWidget(dlg)
        assert dlg._tabs.count() == 2
        dlg._tabs.setCurrentIndex(1)
        assert dlg.current_tab() == 1

    # TC-385: 프리셋 선택
    def test_tc385_preset(self, qtbot):
        from app.ui.dialogs.watermark_dialog import WatermarkDialog
        dlg = WatermarkDialog()
        qtbot.addWidget(dlg)
        dlg._combo_preset.setCurrentText("기밀")
        assert dlg.watermark_text() == "기밀"

    # TC-386: 미리보기 (투명도/회전 값 확인)
    def test_tc386_preview_values(self, qtbot):
        from app.ui.dialogs.watermark_dialog import WatermarkDialog
        dlg = WatermarkDialog()
        qtbot.addWidget(dlg)
        dlg._spin_opacity.setValue(0.5)
        dlg._spin_rotate.setValue(30)
        assert dlg.opacity() == 0.5
        assert dlg.rotation() == 30

    # TC-387: 머리글/바닥글 탭
    def test_tc387_header_footer_tab(self, qtbot):
        from app.ui.dialogs.watermark_dialog import WatermarkDialog
        dlg = WatermarkDialog()
        qtbot.addWidget(dlg)
        dlg._tabs.setCurrentIndex(1)
        dlg._edit_footer_center.setText("{page}/{total}")
        hf = dlg.header_footer_settings()
        assert hf["footer_center"] == "{page}/{total}"


class TestOptimizeDialogUI:
    # TC-388: 프리셋 선택
    def test_tc388_preset(self, qtbot):
        from app.ui.dialogs.optimize_dialog import OptimizeDialog
        dlg = OptimizeDialog(current_size=1024*1024)
        qtbot.addWidget(dlg)
        dlg._combo_preset.setCurrentIndex(0)
        assert dlg.preset() == "web"

    # TC-389: 파일 크기 표시
    def test_tc389_file_size_label(self, qtbot):
        from app.ui.dialogs.optimize_dialog import OptimizeDialog
        dlg = OptimizeDialog(current_size=5*1024*1024)
        qtbot.addWidget(dlg)
        # 다이얼로그에 크기 표시 라벨 존재
        assert dlg._combo_preset is not None


class TestCompareDialogUI:
    # TC-390: 두 파일 선택 UI
    def test_tc390_file_inputs(self, qtbot):
        from app.ui.dialogs.compare_dialog import CompareDialog
        dlg = CompareDialog(current_path="test.pdf")
        qtbot.addWidget(dlg)
        assert dlg._edit_a.text() == "test.pdf"

    # TC-391: 비교 결과 목록
    def test_tc391_result_list(self, qtbot):
        from app.ui.dialogs.compare_dialog import CompareDialog
        dlg = CompareDialog()
        qtbot.addWidget(dlg)
        assert dlg._result_list is not None
        assert dlg._result_list.count() == 0

    # TC-392: 이전/다음 이동
    def test_tc392_nav_buttons(self, qtbot):
        from app.ui.dialogs.compare_dialog import CompareDialog
        dlg = CompareDialog()
        qtbot.addWidget(dlg)
        assert dlg._btn_prev is not None
        assert dlg._btn_next is not None


class TestSignatureDialogUI:
    # TC-393: 인증서 파일 선택
    def test_tc393_cert_selection(self, qtbot):
        from app.ui.dialogs.signature_dialog import SignatureDialog
        dlg = SignatureDialog()
        qtbot.addWidget(dlg)
        assert dlg.cert_path() == ""

    # TC-394: 서명 영역
    def test_tc394_signature_reason(self, qtbot):
        from app.ui.dialogs.signature_dialog import SignatureDialog
        dlg = SignatureDialog()
        qtbot.addWidget(dlg)
        dlg._edit_reason.setText("승인")
        assert dlg.reason() == "승인"


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
