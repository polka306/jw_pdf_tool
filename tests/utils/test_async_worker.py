"""TC-184: 범용 비동기 워커 테스트."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestAsyncWorker:
    """utils/async_worker.py — AsyncWorker 테스트."""

    # TC-184: 작업 완료 시그널
    def test_tc184_finished_signal(self, qtbot):
        from app.utils.async_worker import AsyncWorker

        result_box = []

        def task():
            return 42

        worker = AsyncWorker(task)
        worker.finished.connect(lambda val: result_box.append(val))
        worker.start()

        qtbot.waitUntil(lambda: len(result_box) >= 1, timeout=5000)
        assert result_box[0] == 42

    def test_tc184_error_signal(self, qtbot):
        from app.utils.async_worker import AsyncWorker

        errors = []

        def failing_task():
            raise ValueError("test error")

        worker = AsyncWorker(failing_task)
        worker.error.connect(lambda e: errors.append(e))
        worker.start()

        qtbot.waitUntil(lambda: len(errors) >= 1, timeout=5000)
        assert "test error" in str(errors[0])
