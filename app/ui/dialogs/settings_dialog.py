"""앱 설정 다이얼로그."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    """앱 설정 다이얼로그."""

    def __init__(self, parent=None, settings=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setMinimumWidth(400)
        self._settings = settings
        self._setup_ui()
        self._load_current()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 일반
        general = QGroupBox("일반")
        g_layout = QFormLayout(general)

        self._combo_theme = QComboBox()
        self._combo_theme.addItems(["다크", "라이트"])
        g_layout.addRow("테마:", self._combo_theme)

        self._chk_tray = QCheckBox("시스템 트레이 상주")
        g_layout.addRow(self._chk_tray)

        self._chk_default_viewer = QCheckBox("PDF 파일 연결 등록 (.pdf)")
        self._chk_default_viewer.setToolTip(
            "PDF 파일을 본 프로그램으로 열 수 있도록 Windows에 등록합니다.\n"
            "Windows 11에서는 '연결 프로그램' 목록에 표시되며,\n"
            "기본 앱으로 설정하려면 Windows 설정에서 직접 변경해야 합니다."
        )
        g_layout.addRow(self._chk_default_viewer)

        # Windows 기본 앱 설정 열기 버튼
        self._btn_open_default_apps = QPushButton("Windows 기본 앱 설정 열기...")
        self._btn_open_default_apps.clicked.connect(self._open_windows_default_apps)
        g_layout.addRow(self._btn_open_default_apps)

        layout.addWidget(general)

        # 파일
        file_group = QGroupBox("파일")
        f_layout = QFormLayout(file_group)

        self._spin_recent = QSpinBox()
        self._spin_recent.setRange(0, 20)
        self._spin_recent.setValue(10)
        f_layout.addRow("최근 파일 수:", self._spin_recent)

        layout.addWidget(file_group)

        # 버튼
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._save_and_accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _load_current(self) -> None:
        if self._settings is None:
            return
        theme = self._settings.get("theme", "dark")
        self._combo_theme.setCurrentIndex(0 if theme == "dark" else 1)
        self._chk_tray.setChecked(bool(self._settings.get("tray_enabled", False)))
        self._chk_default_viewer.setChecked(
            bool(self._settings.get("file_assoc_registered", False))
        )

    def _save_and_accept(self) -> None:
        if self._settings:
            self._settings.set("theme", self.theme())
            self._settings.set("tray_enabled", self._chk_tray.isChecked())
            self._settings.set("max_recent", self._spin_recent.value())

            # 파일 연결 등록/해제
            self._apply_file_association()

        self.accept()

    def _apply_file_association(self) -> None:
        """파일 연결 체크박스 상태에 따라 등록/해제."""
        try:
            from app.services.file_association import (
                register_pdf_association,
                unregister_pdf_association,
            )

            checked = self._chk_default_viewer.isChecked()
            currently_registered = bool(
                self._settings.get("file_assoc_registered", False)
            )

            if checked and not currently_registered:
                exe_path = sys.executable
                register_pdf_association(exe_path=exe_path)
                self._settings.set("file_assoc_registered", True)
                QMessageBox.information(
                    self,
                    "파일 연결 등록 완료",
                    "PDF 파일이 본 프로그램과 연결되었습니다.\n\n"
                    "Windows 11에서 기본 앱으로 사용하려면\n"
                    "'Windows 기본 앱 설정 열기' 버튼을 클릭하여\n"
                    "Windows 설정에서 직접 변경하셔야 합니다.",
                )
            elif not checked and currently_registered:
                unregister_pdf_association()
                self._settings.set("file_assoc_registered", False)
        except Exception as e:
            QMessageBox.warning(
                self, "파일 연결 오류",
                f"파일 연결 작업 중 오류가 발생했습니다:\n{e}",
            )

    def _open_windows_default_apps(self) -> None:
        """Windows 11 기본 앱 설정 페이지를 엽니다."""
        if sys.platform != "win32":
            QMessageBox.information(self, "안내", "Windows 전용 기능입니다.")
            return
        try:
            import os
            os.startfile("ms-settings:defaultapps")
        except Exception as e:
            QMessageBox.warning(
                self, "오류",
                f"Windows 설정을 열 수 없습니다:\n{e}",
            )

    def theme(self) -> str:
        return "dark" if self._combo_theme.currentIndex() == 0 else "light"

    def tray_enabled(self) -> bool:
        return self._chk_tray.isChecked()
