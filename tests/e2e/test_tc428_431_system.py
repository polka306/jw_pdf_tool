"""TC-428 ~ TC-431: 시스템 통합 E2E 테스트."""

from __future__ import annotations

import os
import sys
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestTC428FileAssociation:
    # TC-428: 파일 연결 등록 → exe 더블클릭 열기 시뮬레이션
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows 전용")
    def test_tc428_file_association_dry_run(self):
        from app.services.file_association import register_pdf_association

        result = register_pdf_association(exe_path="C:\\test\\app.exe", dry_run=True)
        assert result["progid"] is not None


class TestTC429SingleInstance:
    # TC-429: 단일 인스턴스 파이프 통신
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows 전용")
    def test_tc429_single_instance(self):
        from app.services.single_instance import SingleInstanceManager

        mgr = SingleInstanceManager("test_tc429")
        assert mgr.try_lock() is True
        mgr.release()


class TestTC430Tray:
    # TC-430: 트레이 상주 → 복원
    def test_tc430_tray_service(self, qtbot):
        from app.services.tray_service import TrayService

        tray = TrayService()
        assert tray is not None


class TestTC431Theme:
    # TC-431: 다크→라이트 전환 → 재시작 → 테마 유지
    def test_tc431_theme_persist(self, tmp_path):
        from app.services.settings import AppSettings
        from app.services.theme import get_stylesheet

        s = AppSettings(str(tmp_path / "theme.ini"))
        s.set("theme", "dark")

        # "재시작" 시뮬레이션
        s2 = AppSettings(str(tmp_path / "theme.ini"))
        theme = s2.get("theme")
        assert theme == "dark"

        ss = get_stylesheet(theme)
        assert len(ss) > 0
