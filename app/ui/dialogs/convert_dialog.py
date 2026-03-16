"""문서 변환 다이얼로그 — 이미지/Office 문서 → PDF."""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import QObject, QSize, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core import converter


# ── 백그라운드 변환 워커 ──────────────────────────────────────────────────────

class _ConvertWorker(QObject):
    """백그라운드에서 변환을 수행하는 워커 객체.

    QObject.moveToThread() 패턴을 사용합니다.
    """

    progress = pyqtSignal(int, str)   # (0~100, 상태 메시지)
    finished = pyqtSignal(list)       # 성공한 출력 경로 목록
    error    = pyqtSignal(str)        # 오류 메시지

    def __init__(
        self,
        mode: str,                    # "image" | "office"
        files: list[str],
        output_path: str,
    ) -> None:
        super().__init__()
        self._mode = mode
        self._files = files
        self._output_path = output_path
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            if self._mode == "image":
                self.progress.emit(10, "이미지 변환 중...")
                out = converter.convert_images_to_pdf(self._files, self._output_path)
                self.progress.emit(100, "완료")
                self.finished.emit([out])
            else:
                self.progress.emit(10, "LibreOffice 변환 중... (시간이 걸릴 수 있습니다)")
                out_dir = str(Path(self._output_path).parent)
                out = converter.convert_office_to_pdf(self._files[0], out_dir)
                self.progress.emit(100, "완료")
                self.finished.emit([out])
        except Exception as exc:
            self.error.emit(str(exc))


# ── 이미지 탭 ─────────────────────────────────────────────────────────────────

class _ImageTab(QWidget):
    """이미지 → PDF 변환 탭."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)

        # 버튼 행
        btn_row = QHBoxLayout()
        btn_add = QPushButton("이미지 추가...")
        btn_add.clicked.connect(self._add_images)
        btn_remove = QPushButton("선택 제거")
        btn_remove.clicked.connect(self._remove_selected)
        btn_up = QPushButton("▲")
        btn_up.setFixedWidth(32)
        btn_up.clicked.connect(self._move_up)
        btn_dn = QPushButton("▼")
        btn_dn.setFixedWidth(32)
        btn_dn.clicked.connect(self._move_down)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        btn_row.addWidget(btn_up)
        btn_row.addWidget(btn_dn)
        layout.addLayout(btn_row)

        # 파일 목록
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self._list, 1)

        exts = ", ".join(sorted(converter.SUPPORTED_IMAGE_EXTS))
        lbl = QLabel(f"지원 형식: {exts}")
        lbl.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(lbl)

    def _add_images(self) -> None:
        exts_filter = " ".join(f"*{e}" for e in sorted(converter.SUPPORTED_IMAGE_EXTS))
        paths, _ = QFileDialog.getOpenFileNames(
            self, "이미지 파일 선택", "",
            f"이미지 파일 ({exts_filter});;모든 파일 (*)"
        )
        for p in paths:
            self._list.addItem(QListWidgetItem(p))

    def _remove_selected(self) -> None:
        for item in self._list.selectedItems():
            self._list.takeItem(self._list.row(item))

    def _move_up(self) -> None:
        row = self._list.currentRow()
        if row > 0:
            item = self._list.takeItem(row)
            self._list.insertItem(row - 1, item)
            self._list.setCurrentRow(row - 1)

    def _move_down(self) -> None:
        row = self._list.currentRow()
        if row < self._list.count() - 1:
            item = self._list.takeItem(row)
            self._list.insertItem(row + 1, item)
            self._list.setCurrentRow(row + 1)

    def get_files(self) -> list[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]

    def is_ready(self) -> bool:
        return self._list.count() > 0


# ── Office 탭 ─────────────────────────────────────────────────────────────────

class _OfficeTab(QWidget):
    """Office 문서 → PDF 변환 탭."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)

        # LibreOffice 상태
        lo_ok = converter.is_libreoffice_available()
        if lo_ok:
            lo_path = converter.find_libreoffice()
            status_text = f"✔ LibreOffice 감지됨\n{lo_path}"
            status_color = "#4caf50"
        else:
            status_text = (
                "✘ LibreOffice 미설치 — Office 변환 기능을 사용하려면\n"
                "LibreOffice를 설치하거나 LIBREOFFICE_PATH 환경 변수를 설정하세요."
            )
            status_color = "#f44336"
        lbl_lo = QLabel(status_text)
        lbl_lo.setStyleSheet(f"color:{status_color}; font-size:11px; padding:4px;")
        lbl_lo.setWordWrap(True)
        layout.addWidget(lbl_lo)

        # 파일 목록
        btn_row = QHBoxLayout()
        btn_add = QPushButton("파일 추가...")
        btn_add.setEnabled(lo_ok)
        btn_add.clicked.connect(self._add_file)
        btn_remove = QPushButton("선택 제거")
        btn_remove.setEnabled(lo_ok)
        btn_remove.clicked.connect(self._remove_selected)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._list = QListWidget()
        self._list.setEnabled(lo_ok)
        layout.addWidget(self._list, 1)

        exts = ", ".join(sorted(converter.SUPPORTED_OFFICE_EXTS))
        lbl_exts = QLabel(f"지원 형식: {exts}")
        lbl_exts.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(lbl_exts)

    def _add_file(self) -> None:
        exts_filter = " ".join(f"*{e}" for e in sorted(converter.SUPPORTED_OFFICE_EXTS))
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Office 파일 선택", "",
            f"Office 파일 ({exts_filter});;모든 파일 (*)"
        )
        for p in paths:
            self._list.addItem(QListWidgetItem(p))

    def _remove_selected(self) -> None:
        for item in self._list.selectedItems():
            self._list.takeItem(self._list.row(item))

    def get_files(self) -> list[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]

    def is_ready(self) -> bool:
        return self._list.count() > 0 and converter.is_libreoffice_available()


# ── 변환 다이얼로그 ───────────────────────────────────────────────────────────

class ConvertDialog(QDialog):
    """문서 변환 다이얼로그.

    시그널:
        conversion_done(list[str]) — 변환 완료 후 사용자가 '열기'를 선택했을 때
                                     출력 PDF 경로 목록을 emit합니다.
    """

    conversion_done = pyqtSignal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("문서 변환 → PDF")
        self.setMinimumSize(520, 480)
        self._worker: _ConvertWorker | None = None
        self._thread: QThread | None = None
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI 초기화
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 탭
        self._tabs = QTabWidget()
        self._tab_image = _ImageTab()
        self._tab_office = _OfficeTab()
        self._tabs.addTab(self._tab_image,  "이미지 → PDF")
        self._tabs.addTab(self._tab_office, "문서 → PDF (LibreOffice)")
        layout.addWidget(self._tabs, 1)

        # 출력 경로
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("저장 위치:"))
        self._edit_output = QLineEdit()
        self._edit_output.setPlaceholderText("출력 PDF 파일 경로를 지정하세요")
        btn_out = QPushButton("...")
        btn_out.setFixedWidth(32)
        btn_out.clicked.connect(self._browse_output)
        out_row.addWidget(self._edit_output, 1)
        out_row.addWidget(btn_out)
        layout.addLayout(out_row)

        # 진행 표시
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color:#aaa; font-size:11px;")
        self._lbl_status.setVisible(False)
        layout.addWidget(self._lbl_status)

        # 버튼
        btn_row = QHBoxLayout()
        self._btn_convert = QPushButton("변환 시작")
        self._btn_convert.setDefault(True)
        self._btn_convert.clicked.connect(self._start_convert)
        self._btn_close = QPushButton("닫기")
        self._btn_close.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_convert)
        btn_row.addWidget(self._btn_close)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # 슬롯
    # ------------------------------------------------------------------

    def _browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "출력 PDF 저장 위치", "", "PDF 파일 (*.pdf)"
        )
        if path:
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            self._edit_output.setText(path)

    def _start_convert(self) -> None:
        output_path = self._edit_output.text().strip()
        if not output_path:
            QMessageBox.warning(self, "경고", "저장 위치를 지정하세요.")
            return
        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"

        idx = self._tabs.currentIndex()
        if idx == 0:
            files = self._tab_image.get_files()
            if not files:
                QMessageBox.warning(self, "경고", "변환할 이미지를 추가하세요.")
                return
            mode = "image"
        else:
            files = self._tab_office.get_files()
            if not files:
                QMessageBox.warning(self, "경고", "변환할 파일을 추가하세요.")
                return
            mode = "office"

        self._btn_convert.setEnabled(False)
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._lbl_status.setVisible(True)
        self._lbl_status.setText("변환 준비 중...")

        # 워커 + 스레드 설정
        self._worker = _ConvertWorker(mode, files, output_path)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_progress(self, value: int, message: str) -> None:
        self._progress.setValue(value)
        self._lbl_status.setText(message)

    def _on_finished(self, output_paths: list[str]) -> None:
        self._progress.setVisible(False)
        self._lbl_status.setVisible(False)
        self._btn_convert.setEnabled(True)

        if not output_paths:
            return

        path = output_paths[0]
        reply = QMessageBox.question(
            self,
            "변환 완료",
            f"PDF 변환이 완료되었습니다.\n\n{path}\n\n지금 열겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.conversion_done.emit(output_paths)
            self.accept()

    def _on_error(self, message: str) -> None:
        self._progress.setVisible(False)
        self._lbl_status.setVisible(False)
        self._btn_convert.setEnabled(True)
        QMessageBox.critical(self, "변환 오류", message)

    # ------------------------------------------------------------------
    # 이벤트
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        if self._thread and self._thread.isRunning():
            if self._worker:
                self._worker.cancel()
            self._thread.quit()
            self._thread.wait(3000)
        super().closeEvent(event)
