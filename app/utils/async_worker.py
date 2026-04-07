"""범용 비동기 워커 — QThread 기반 단일 작업 실행."""

from __future__ import annotations

from typing import Any, Callable

from PyQt6.QtCore import QThread, pyqtSignal


class AsyncWorker(QThread):
    """함수를 백그라운드 스레드에서 실행하고 결과를 시그널로 전달.

    Signals
    -------
    finished(result)
        작업 정상 완료 시 결과 전달.
    error(exception)
        작업 실패 시 예외 전달.
    """

    finished = pyqtSignal(object)
    error = pyqtSignal(object)

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)
