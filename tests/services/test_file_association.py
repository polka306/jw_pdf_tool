"""TC-405 ~ TC-408: 파일 확장자 연결 테스트."""

from __future__ import annotations

import sys
import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows 전용")
class TestFileAssociation:

    # TC-405: ProgID 레지스트리 등록
    def test_tc405_register_progid(self):
        from app.services.file_association import register_pdf_association, unregister_pdf_association

        # 등록 (테스트용 — 실제 레지스트리 변경)
        result = register_pdf_association(exe_path="C:\\test\\app.exe", dry_run=True)
        assert result["progid"] == "PDFEditTool.pdf"

    # TC-406: shell\open\command 경로
    def test_tc406_open_command(self):
        from app.services.file_association import register_pdf_association

        result = register_pdf_association(exe_path="C:\\test\\app.exe", dry_run=True)
        assert "C:\\test\\app.exe" in result["command"]
        assert '"%1"' in result["command"]

    # TC-407: 등록 해제
    def test_tc407_unregister(self):
        from app.services.file_association import unregister_pdf_association

        result = unregister_pdf_association(dry_run=True)
        assert result["status"] == "ok"

    # TC-408: DefaultIcon
    def test_tc408_default_icon(self):
        from app.services.file_association import register_pdf_association

        result = register_pdf_association(exe_path="C:\\test\\app.exe", dry_run=True)
        assert "icon" in result
