"""TC-183: 플랫폼 유틸 테스트."""

from __future__ import annotations

import sys

import pytest


class TestPlatformUtils:
    """utils/platform.py — 플랫폼 추상화 테스트."""

    # TC-183: Windows 폰트 경로 감지
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows 전용 테스트")
    def test_tc183_windows_font_path(self):
        from app.utils.platform import get_korean_font_path

        path = get_korean_font_path()
        assert path is not None
        assert "malgun" in path.lower()
