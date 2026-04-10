"""TC-444 ~ TC-451: 가상 프린터 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestPrintSettingsUI:

    # TC-444: 가상 프린터 설치 (dry_run)
    def test_tc444_install_button(self):
        from app.services.print_service import VirtualPrinterService
        result = VirtualPrinterService().install(dry_run=True)
        assert result["printer_name"] == "jw_pdf - PDF Printer"

    # TC-445: 가상 프린터 제거
    def test_tc445_uninstall_button(self):
        from app.services.print_service import VirtualPrinterService
        assert VirtualPrinterService().uninstall(dry_run=True)["status"] == "ok"

    # TC-446: DPI 선택
    def test_tc446_dpi_selection(self):
        from app.services.print_service import PrintSettings
        for dpi in (150, 300, 600):
            assert PrintSettings(dpi=dpi).dpi == dpi

    # TC-447: 용지 크기
    def test_tc447_paper_size(self):
        from app.services.print_service import PrintSettings
        assert PrintSettings(paper_size="Letter").paper_size == "Letter"

    # TC-448: 인쇄 후 동작
    def test_tc448_post_action(self):
        from app.services.print_service import PrintSettings
        s = PrintSettings(auto_save=True, auto_open=True)
        assert s.auto_save and s.auto_open

    # TC-449: 메타데이터
    def test_tc449_metadata(self):
        from app.services.print_service import PrintSettings
        s = PrintSettings(title="Doc", author="Me")
        assert s.title == "Doc" and s.author == "Me"

    # TC-450: PDF 버전
    def test_tc450_pdf_version(self):
        from app.services.print_service import PrintSettings
        assert PrintSettings(pdf_version="2.0").pdf_version == "2.0"

    # TC-451: 알림 설정
    def test_tc451_notification(self):
        from app.services.print_service import PrintSettings
        assert PrintSettings(auto_open=True).auto_open is True
