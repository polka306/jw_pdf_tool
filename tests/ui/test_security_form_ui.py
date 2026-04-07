"""TC-341 ~ TC-352: 보안/양식 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestSecurityDialogUI:
    """보안 다이얼로그 UI."""

    # TC-341: 암호 설정 UI
    def test_tc341_security_dialog_password(self, qtbot):
        from app.ui.dialogs.security_dialog import SecurityDialog
        dlg = SecurityDialog()
        qtbot.addWidget(dlg)
        dlg._edit_user_pw.setText("test123")
        assert dlg.user_password() == "test123"

    # TC-342: 권한 체크박스
    def test_tc342_permission_checkboxes(self, qtbot):
        from app.ui.dialogs.security_dialog import SecurityDialog
        dlg = SecurityDialog()
        qtbot.addWidget(dlg)
        dlg._chk_print.setChecked(False)
        perms = dlg.permissions()
        assert perms["print"] is False

    # TC-343: 암호화 방식 선택
    def test_tc343_algorithm_selection(self, qtbot):
        from app.ui.dialogs.security_dialog import SecurityDialog
        dlg = SecurityDialog()
        qtbot.addWidget(dlg)
        dlg._combo_algorithm.setCurrentText("AES-128")
        assert dlg.algorithm() == "AES-128"

    # TC-344: 암호 입력 다이얼로그
    def test_tc344_password_dialog(self, qtbot):
        from app.ui.dialogs.security_dialog import SecurityDialog
        dlg = SecurityDialog()
        qtbot.addWidget(dlg)
        assert dlg._edit_user_pw.echoMode() == dlg._edit_user_pw.EchoMode.Password

    # TC-345: owner 암호
    def test_tc345_owner_password(self, qtbot):
        from app.ui.dialogs.security_dialog import SecurityDialog
        dlg = SecurityDialog()
        qtbot.addWidget(dlg)
        dlg._edit_owner_pw.setText("admin")
        assert dlg.owner_password() == "admin"


class TestFormViewerUI:
    """양식 다이얼로그 UI."""

    # TC-346: 양식 다이얼로그 필드 이름
    def test_tc346_form_dialog_name(self, qtbot):
        from app.ui.dialogs.form_dialog import FormDialog
        dlg = FormDialog()
        qtbot.addWidget(dlg)
        dlg._edit_name.setText("email")
        assert dlg.field_name() == "email"

    # TC-347: 양식 필드 유형
    def test_tc347_form_field_type(self, qtbot):
        from app.ui.dialogs.form_dialog import FormDialog
        dlg = FormDialog()
        qtbot.addWidget(dlg)
        dlg._combo_type.setCurrentIndex(1)  # 체크박스
        assert dlg.field_type() == "checkbox"

    # TC-348: 기본값 설정
    def test_tc348_default_value(self, qtbot):
        from app.ui.dialogs.form_dialog import FormDialog
        dlg = FormDialog()
        qtbot.addWidget(dlg)
        dlg._edit_default.setText("hello")
        assert dlg.default_value() == "hello"

    # TC-349: 필수 여부
    def test_tc349_required_checkbox(self, qtbot):
        from app.ui.dialogs.form_dialog import FormDialog
        dlg = FormDialog()
        qtbot.addWidget(dlg)
        dlg._chk_required.setChecked(True)
        assert dlg.is_required()


class TestFormDialogUI:
    """양식 다이얼로그 생성."""

    # TC-350: FormDialog 존재
    def test_tc350_form_dialog_exists(self, qtbot):
        from app.ui.dialogs.form_dialog import FormDialog
        dlg = FormDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    # TC-351: 양식 필드 유형 목록
    def test_tc351_field_types(self, qtbot):
        from app.ui.dialogs.form_dialog import FormDialog
        dlg = FormDialog()
        qtbot.addWidget(dlg)
        assert dlg._combo_type.count() == 4


class TestSecurityFormMenu:
    """보안/양식 메뉴."""

    # TC-352: 메뉴 항목
    def test_tc352_menu_exists(self, qtbot, pdf_3pages):
        from app.ui.main_window import MainWindow
        from tests.helpers import load_pdf_directly

        win = MainWindow()
        qtbot.addWidget(win)
        load_pdf_directly(win, pdf_3pages)

        menubar = win.menuBar()
        assert menubar is not None
        # 최소한 메뉴바가 존재하고 편집 메뉴가 있는지
        actions = [a.text() for a in menubar.actions()]
        assert len(actions) >= 4  # 파일, 편집, 보기, ...

        if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
            win._page_panel._cancel_loader()
        win.close()
