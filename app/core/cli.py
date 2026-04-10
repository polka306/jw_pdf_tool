"""명령줄 인자 파서."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass
class CliArgs:
    """파싱된 CLI 인자."""
    file_path: str | None = None


def parse_cli_args(argv: list[str] | None = None) -> CliArgs:
    """명령줄 인자를 파싱.

    Parameters
    ----------
    argv : list[str] | None
        인자 리스트. None이면 sys.argv 사용.
    """
    parser = argparse.ArgumentParser(description="jw_pdf")
    parser.add_argument("file", nargs="?", default=None, help="열 PDF 파일 경로")

    if argv is not None:
        args = parser.parse_args(argv[1:])  # 첫 번째는 프로그램 이름
    else:
        args = parser.parse_args()

    return CliArgs(file_path=args.file)
