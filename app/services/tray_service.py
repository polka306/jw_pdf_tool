"""시스템 트레이 서비스."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QApplication


class TrayService(QObject):
    """시스템 트레이 아이콘 관리.

    Signals
    -------
    toggle_requested()
        트레이 아이콘 클릭 시 윈도우 토글 요청.
    quit_requested()
        트레이 메뉴에서 종료 선택.
    """

    toggle_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._menu = QMenu()
        self._setup_menu()

        self._tray: QSystemTrayIcon | None = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = QSystemTrayIcon(self)
            self._tray.setContextMenu(self._menu)
            self._tray.activated.connect(self._on_activated)

    def _setup_menu(self) -> None:
        show_action = QAction("열기", self)
        show_action.triggered.connect(self.toggle_requested.emit)
        self._menu.addAction(show_action)

        self._menu.addSeparator()

        quit_action = QAction("종료", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(quit_action)

    def is_available(self) -> bool:
        """시스템 트레이 사용 가능 여부."""
        return QSystemTrayIcon.isSystemTrayAvailable()

    def get_menu(self) -> QMenu:
        return self._menu

    def show(self) -> None:
        if self._tray:
            self._tray.show()

    def hide(self) -> None:
        if self._tray:
            self._tray.hide()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_requested.emit()
