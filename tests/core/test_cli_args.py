"""TC-221: 명령줄 인자 테스트."""

from __future__ import annotations

import pytest


class TestCliArgs:
    """main.py — 명령줄 인자 파싱 테스트."""

    # TC-221: 유효한 PDF 경로
    def test_tc221_valid_pdf_path(self, pdf_3pages):
        from app.core.cli import parse_cli_args

        args = parse_cli_args(["app", pdf_3pages])
        assert args.file_path == pdf_3pages

    def test_tc221_no_args(self):
        from app.core.cli import parse_cli_args

        args = parse_cli_args(["app"])
        assert args.file_path is None

    def test_tc221_nonexistent_file(self):
        from app.core.cli import parse_cli_args

        args = parse_cli_args(["app", "C:/nonexistent.pdf"])
        assert args.file_path == "C:/nonexistent.pdf"  # 파싱은 성공, 검증은 별도
