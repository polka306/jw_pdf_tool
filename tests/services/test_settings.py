"""TC-213 ~ TC-216: 설정 관리 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestSettings:
    """services/settings.py — QSettings 래퍼 테스트."""

    # TC-213: 값 저장 → 읽기
    def test_tc213_save_and_load(self, tmp_path):
        from app.services.settings import AppSettings

        settings = AppSettings(str(tmp_path / "test_settings.ini"))
        settings.set("theme", "dark")
        settings.set("zoom_default", 1.5)

        assert settings.get("theme") == "dark"
        assert settings.get("zoom_default") == 1.5

    # TC-214: 기본값 폴백
    def test_tc214_default_fallback(self, tmp_path):
        from app.services.settings import AppSettings

        settings = AppSettings(str(tmp_path / "test_settings.ini"))

        result = settings.get("nonexistent_key", default="fallback_value")
        assert result == "fallback_value"

    # TC-215: 최근 파일 목록 추가
    def test_tc215_recent_files(self, tmp_path):
        from app.services.settings import AppSettings

        settings = AppSettings(str(tmp_path / "test_settings.ini"))

        # 12개 추가 → 최대 10개 유지
        for i in range(12):
            settings.add_recent_file(f"C:/path/file_{i}.pdf")

        recent = settings.get_recent_files()
        assert len(recent) == 10
        # 가장 최근 파일이 첫 번째
        assert recent[0] == "C:/path/file_11.pdf"

    # TC-216: 존재하지 않는 파일 필터
    def test_tc216_filter_missing_files(self, tmp_path):
        from app.services.settings import AppSettings

        settings = AppSettings(str(tmp_path / "test_settings.ini"))

        # 존재하는 파일과 존재하지 않는 파일 추가
        real_file = str(tmp_path / "real.pdf")
        with open(real_file, "w") as f:
            f.write("dummy")

        settings.add_recent_file(real_file)
        settings.add_recent_file("C:/nonexistent/fake.pdf")

        recent = settings.get_recent_files(filter_existing=True)
        assert real_file in recent
        assert "C:/nonexistent/fake.pdf" not in recent
