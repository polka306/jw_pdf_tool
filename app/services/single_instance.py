"""단일 인스턴스 관리 — Named Mutex 기반."""

from __future__ import annotations

import sys


class SingleInstanceManager:
    """앱의 단일 인스턴스를 보장하는 매니저.

    Windows에서는 Named Mutex를 사용하여 중복 실행을 감지합니다.
    """

    def __init__(self, name: str = "PDFEditTool_SingleInstance") -> None:
        self._name = name
        self._handle = None
        self._locked = False

    def try_lock(self) -> bool:
        """잠금 시도. True이면 첫 번째 인스턴스."""
        if sys.platform != "win32":
            return True

        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32

        self._handle = kernel32.CreateMutexW(None, True, self._name)
        last_error = kernel32.GetLastError()

        if last_error == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle(self._handle)
            self._handle = None
            self._locked = False
            return False

        self._locked = True
        return True

    def release(self) -> None:
        """잠금 해제."""
        if self._handle and sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.ReleaseMutex(self._handle)
            kernel32.CloseHandle(self._handle)
            self._handle = None
            self._locked = False

    def send_message(self, message: str) -> bool:
        """실행 중인 인스턴스에 메시지 전달 (간단 구현)."""
        # 실제 구현은 Named Pipe 또는 Socket 사용
        # 여기서는 기본 구현만 제공
        return self._locked

    @property
    def is_locked(self) -> bool:
        return self._locked
