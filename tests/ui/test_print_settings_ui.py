"""TC-444 ~ TC-451: 가상 프린터 UI 테스트."""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestPrintSettingsUI:

    # TC-444 ~ TC-451: PrintSettingsDialog (skip — 다이얼로그 후속)
    @pytest.mark.parametrize("tc", [444, 445, 446, 447, 448, 449, 450, 451])
    def test_tc_print_settings(self, tc):
        pytest.skip(f"TC-{tc}: PrintSettingsDialog 후속 구현")
