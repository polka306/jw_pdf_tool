"""플랫폼 추상화 유틸 — Windows 의존 코드 중앙화."""

from __future__ import annotations

import os
import sys


def get_korean_font_path() -> str | None:
    """한글 폰트(맑은 고딕) 경로를 반환. 없으면 None."""
    if sys.platform != "win32":
        return None

    windir = os.environ.get("WINDIR", r"C:\Windows")
    candidates = [
        os.path.join(windir, "Fonts", "malgun.ttf"),
        os.path.join(windir, "Fonts", "malgunsl.ttf"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def get_korean_bold_font_path() -> str | None:
    """한글 볼드 폰트(맑은 고딕 Bold) 경로를 반환. 없으면 None."""
    if sys.platform != "win32":
        return None

    windir = os.environ.get("WINDIR", r"C:\Windows")
    path = os.path.join(windir, "Fonts", "malgunbd.ttf")
    return path if os.path.isfile(path) else None
