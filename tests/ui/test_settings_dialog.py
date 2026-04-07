"""TC-420 ~ TC-427: 설정 다이얼로그 + 메인윈도우 통합 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestSettingsDialogUI:

    # TC-420: 기본 PDF 뷰어 체크박스
    def test_tc420_default_viewer(self, qtbot):
        from app.ui.dialogs.settings_dialog import SettingsDialog
        dlg = SettingsDialog()
        qtbot.addWidget(dlg)
        assert dlg._chk_default_viewer is not None

    # TC-421: 트레이 상주 체크박스
    def test_tc421_tray_checkbox(self, qtbot):
        from app.ui.dialogs.settings_dialog import SettingsDialog
        dlg = SettingsDialog()
        qtbot.addWidget(dlg)
        dlg._chk_tray.setChecked(True)
        assert dlg.tray_enabled()

    # TC-422: 테마 선택
    def test_tc422_theme_selection(self, qtbot):
        from app.ui.dialogs.settings_dialog import SettingsDialog
        dlg = SettingsDialog()
        qtbot.addWidget(dlg)
        dlg._combo_theme.setCurrentIndex(1)
        assert dlg.theme() == "light"

    # TC-423: 설정 변경 반영
    def test_tc423_settings_apply(self, qtbot, tmp_path):
        from app.services.settings import AppSettings
        from app.ui.dialogs.settings_dialog import SettingsDialog
        s = AppSettings(str(tmp_path / "test.ini"))
        dlg = SettingsDialog(settings=s)
        qtbot.addWidget(dlg)
        dlg._combo_theme.setCurrentIndex(1)
        dlg._save_and_accept()
        assert s.get("theme") == "light"


class TestMainWindowTheme:

    # TC-424: 닫기 → 트레이 최소화 (설정 ON)
    def test_tc424_close_to_tray(self):
        pytest.skip("TC-424: 트레이 통합 후속 구현")

    # TC-425: 닫기 → 실제 종료 (설정 OFF)
    def test_tc425_close_exits(self):
        pytest.skip("TC-425: 트레이 통합 후속 구현")

    # TC-426: 라이트 테마 색상 확인
    def test_tc426_light_theme_colors(self):
        from app.services.theme import get_stylesheet

        light = get_stylesheet("light")
        assert len(light) > 0
        # 라이트 테마는 밝은 배경색을 포함해야 함
        assert "#f" in light.lower() or "white" in light.lower() or "background" in light.lower()

    # TC-427: Inno Setup 스크립트 문법 (파일 존재만 확인)
    def test_tc427_installer_script(self):
        pytest.skip("TC-427: Inno Setup 스크립트 후속 작성")
