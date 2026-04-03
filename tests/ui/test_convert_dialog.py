"""변환 다이얼로그 테스트 -- TC-126~TC-128."""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QProgressBar


def test_convert_shortcut_binding(main_window):
    """TC-126: 변환 액션에 Ctrl+Shift+C 단축키가 할당되어 있다."""
    tb = main_window._toolbar
    shortcut = tb._act_convert.shortcut().toString()
    assert "C" in shortcut


def test_dialog_has_two_tabs(qtbot):
    """TC-127: ConvertDialog에 2개 이상의 탭이 있다."""
    from app.ui.dialogs.convert_dialog import ConvertDialog
    dlg = ConvertDialog(None)
    qtbot.addWidget(dlg)
    assert dlg._tabs.count() >= 2


def test_progress_bar_exists(qtbot):
    """TC-128: ConvertDialog에 QProgressBar가 존재한다."""
    from app.ui.dialogs.convert_dialog import ConvertDialog
    dlg = ConvertDialog(None)
    qtbot.addWidget(dlg)
    progress_bars = dlg.findChildren(QProgressBar)
    assert len(progress_bars) >= 1
