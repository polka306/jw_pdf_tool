"""TC-416 ~ TC-419: 업데이터/테마 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestUpdater:

    # TC-416: 버전 비교 (현재 < 최신)
    def test_tc416_newer_version(self):
        from app.services.updater import compare_versions

        assert compare_versions("1.0.0", "2.0.0") < 0  # 업데이트 필요

    # TC-417: 동일 버전
    def test_tc417_same_version(self):
        from app.services.updater import compare_versions

        assert compare_versions("2.0.0", "2.0.0") == 0  # 업데이트 없음


class TestTheme:

    # TC-418: 다크 → 라이트 전환
    def test_tc418_theme_switch(self):
        from app.services.theme import get_stylesheet

        dark = get_stylesheet("dark")
        light = get_stylesheet("light")
        assert dark != light
        assert "#1e1e1e" in dark or "background" in dark.lower()

    # TC-419: 테마 설정 저장/로드
    def test_tc419_theme_persistence(self, tmp_path):
        from app.services.settings import AppSettings

        s = AppSettings(str(tmp_path / "theme.ini"))
        s.set("theme", "light")
        assert s.get("theme") == "light"
