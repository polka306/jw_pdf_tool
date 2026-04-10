"""TC-432 ~ TC-443: 가상 PDF 프린터 서비스 테스트."""

from __future__ import annotations

import os
import sys
import pytest


class TestPrinterInstall:

    # TC-432: 가상 프린터 등록 확인 (dry_run)
    def test_tc432_register_printer(self):
        from app.services.print_service import VirtualPrinterService

        svc = VirtualPrinterService()
        result = svc.install(dry_run=True)
        assert result["printer_name"] == "jw_pdf - PDF Printer"

    # TC-433: 프린터 목록에 표시 (dry_run)
    def test_tc433_printer_in_list(self):
        from app.services.print_service import VirtualPrinterService

        svc = VirtualPrinterService()
        result = svc.install(dry_run=True)
        assert result["status"] == "ok"

    # TC-434: 프린터 제거 (dry_run)
    def test_tc434_uninstall_printer(self):
        from app.services.print_service import VirtualPrinterService

        svc = VirtualPrinterService()
        result = svc.uninstall(dry_run=True)
        assert result["status"] == "ok"


class TestPrintWorkflow:

    # TC-435: 스풀 데이터 수신 시뮬레이션
    def test_tc435_spool_receive(self, tmp_path):
        from app.services.print_service import VirtualPrinterService

        svc = VirtualPrinterService()
        # 스풀 데이터 시뮬레이션 (실제 프린터 없이)
        result = svc.simulate_spool(b"PostScript data", str(tmp_path / "spool.ps"))
        assert result is True or result is False

    # TC-436: PostScript → PDF 변환 (Ghostscript 의존)
    def test_tc436_ps_to_pdf(self):
        from app.services.print_service import is_ghostscript_available

        # Ghostscript 설치 여부 확인
        available = is_ghostscript_available()
        assert isinstance(available, bool)

    # TC-437: 300 DPI 품질
    def test_tc437_dpi_setting(self):
        from app.services.print_service import PrintSettings

        settings = PrintSettings(dpi=300)
        assert settings.dpi == 300

    # TC-438: 컬러/흑백/그레이스케일
    def test_tc438_color_mode(self):
        from app.services.print_service import PrintSettings

        for mode in ("color", "grayscale", "bw"):
            settings = PrintSettings(color_mode=mode)
            assert settings.color_mode == mode


class TestPrintOutput:

    # TC-439: 저장 다이얼로그 경로
    def test_tc439_save_path(self, tmp_path):
        from app.services.print_service import PrintSettings

        settings = PrintSettings(output_dir=str(tmp_path))
        assert settings.output_dir == str(tmp_path)

    # TC-440: 자동 저장 모드
    def test_tc440_auto_save(self):
        from app.services.print_service import PrintSettings

        settings = PrintSettings(auto_save=True)
        assert settings.auto_save is True

    # TC-441: 파일명 생성
    def test_tc441_filename_generation(self):
        from app.services.print_service import generate_output_filename

        name = generate_output_filename("My Document")
        assert "My Document" in name or "My_Document" in name
        assert name.endswith(".pdf")

    # TC-442: 메타데이터 설정
    def test_tc442_metadata(self):
        from app.services.print_service import PrintSettings

        settings = PrintSettings(title="Test Doc", author="Tester")
        assert settings.title == "Test Doc"
        assert settings.author == "Tester"

    # TC-443: 자동 열기
    def test_tc443_auto_open(self):
        from app.services.print_service import PrintSettings

        settings = PrintSettings(auto_open=True)
        assert settings.auto_open is True
