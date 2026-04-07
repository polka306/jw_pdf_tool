"""QSettings 기반 앱 설정 관리."""

from __future__ import annotations

import os
from typing import Any

from PyQt6.QtCore import QSettings


class AppSettings:
    """앱 설정 래퍼 — INI 파일 기반.

    Parameters
    ----------
    path : str | None
        설정 파일 경로. None이면 기본 경로 사용.
    """

    MAX_RECENT = 10

    def __init__(self, path: str | None = None) -> None:
        if path:
            self._settings = QSettings(path, QSettings.Format.IniFormat)
        else:
            self._settings = QSettings("PDFEditor", "PDFEditTool")

    # ------------------------------------------------------------------
    # 일반 키-값
    # ------------------------------------------------------------------

    def set(self, key: str, value: Any) -> None:
        """설정 값 저장."""
        self._settings.setValue(key, value)
        self._settings.sync()

    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 읽기. 없으면 default 반환."""
        val = self._settings.value(key)
        if val is None:
            return default
        return val

    # ------------------------------------------------------------------
    # 최근 파일
    # ------------------------------------------------------------------

    def add_recent_file(self, path: str) -> None:
        """최근 파일 목록에 추가. 최대 MAX_RECENT개 유지."""
        recent = self._get_recent_list()

        # 이미 있으면 제거 후 앞에 추가
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)

        # 최대 개수 제한
        recent = recent[:self.MAX_RECENT]

        self._settings.setValue("recent_files", recent)
        self._settings.sync()

    def get_recent_files(self, *, filter_existing: bool = False) -> list[str]:
        """최근 파일 목록 반환."""
        recent = self._get_recent_list()

        if filter_existing:
            recent = [p for p in recent if os.path.isfile(p)]

        return recent

    def _get_recent_list(self) -> list[str]:
        """내부: 최근 파일 리스트 읽기."""
        val = self._settings.value("recent_files")
        if val is None:
            return []
        if isinstance(val, str):
            return [val] if val else []
        if isinstance(val, list):
            return list(val)
        return []
