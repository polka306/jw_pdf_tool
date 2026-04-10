"""가상 PDF 프린터 서비스."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime


PRINTER_NAME = "jw_pdf - PDF Printer"


@dataclass
class PrintSettings:
    """인쇄 설정."""
    dpi: int = 300
    color_mode: str = "color"  # "color", "grayscale", "bw"
    paper_size: str = "A4"
    pdf_version: str = "1.7"
    output_dir: str = ""
    auto_save: bool = False
    auto_open: bool = False
    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""


class VirtualPrinterService:
    """가상 PDF 프린터 관리.

    실제 프린터 드라이버 설치는 Ghostscript + Redmon 조합이 필요하며,
    관리자 권한이 필요합니다. dry_run 모드에서는 결과만 시뮬레이션합니다.
    """

    def install(self, *, dry_run: bool = False) -> dict:
        """가상 프린터 설치."""
        result = {
            "printer_name": PRINTER_NAME,
            "status": "ok",
        }

        if dry_run:
            return result

        # 실제 설치: Ghostscript + Redmon 포트 모니터 필요
        # 관리자 권한 필요 (UAC)
        # 여기서는 기본 구현만 제공
        return result

    def uninstall(self, *, dry_run: bool = False) -> dict:
        """가상 프린터 제거."""
        if dry_run:
            return {"status": "ok"}
        return {"status": "ok"}

    def simulate_spool(self, data: bytes, output_path: str) -> bool:
        """스풀 데이터 수신 시뮬레이션."""
        try:
            with open(output_path, "wb") as f:
                f.write(data)
            return True
        except Exception:
            return False


def is_ghostscript_available() -> bool:
    """Ghostscript가 설치되어 있는지 확인."""
    return shutil.which("gswin64c") is not None or shutil.which("gs") is not None


def generate_output_filename(
    document_name: str,
    *,
    add_timestamp: bool = False,
) -> str:
    """출력 파일명 생성."""
    # 파일명에 사용할 수 없는 문자 제거
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in document_name)
    safe_name = safe_name.strip()

    if add_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{safe_name}_{ts}.pdf"

    return f"{safe_name}.pdf"
