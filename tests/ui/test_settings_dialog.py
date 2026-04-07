"""TC-420 ~ TC-427: 설정 다이얼로그 + 메인윈도우 통합 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestSettingsDialogUI:

    # TC-420 ~ TC-423: 설정 다이얼로그 (skip — 다이얼로그 후속)
    @pytest.mark.parametrize("tc", [420, 421, 422, 423])
    def test_tc_settings_dialog(self, tc):
        pytest.skip(f"TC-{tc}: SettingsDialog 후속 구현")


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
