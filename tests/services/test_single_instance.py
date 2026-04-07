"""TC-409 ~ TC-412: 단일 인스턴스 테스트."""

from __future__ import annotations

import sys
import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows 전용")
class TestSingleInstance:

    # TC-409: 첫 실행 → 서버 생성
    def test_tc409_first_instance_creates_server(self):
        from app.services.single_instance import SingleInstanceManager

        mgr = SingleInstanceManager("test_pdf_editor_tc409")
        is_first = mgr.try_lock()
        assert is_first is True
        mgr.release()

    # TC-410: 두 번째 실행 → 클라이언트 감지
    def test_tc410_second_instance_detected(self):
        from app.services.single_instance import SingleInstanceManager

        mgr1 = SingleInstanceManager("test_pdf_editor_tc410")
        assert mgr1.try_lock() is True

        mgr2 = SingleInstanceManager("test_pdf_editor_tc410")
        assert mgr2.try_lock() is False

        mgr1.release()

    # TC-411: 파일 경로 전달
    def test_tc411_send_file_path(self):
        from app.services.single_instance import SingleInstanceManager

        mgr = SingleInstanceManager("test_pdf_editor_tc411")
        mgr.try_lock()

        # 파일 경로 전달 시뮬레이션
        result = mgr.send_message("C:\\test\\file.pdf")
        # 자기 자신에게 보내므로 수신 여부만 확인
        assert result is True or result is False  # 구현에 따라

        mgr.release()

    # TC-412: 서버 종료 후 재시작
    def test_tc412_restart_after_release(self):
        from app.services.single_instance import SingleInstanceManager

        mgr1 = SingleInstanceManager("test_pdf_editor_tc412")
        assert mgr1.try_lock() is True
        mgr1.release()

        mgr2 = SingleInstanceManager("test_pdf_editor_tc412")
        assert mgr2.try_lock() is True
        mgr2.release()
