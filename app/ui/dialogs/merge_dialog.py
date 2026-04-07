"""PDF 병합 다이얼로그."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class MergeDialog(QDialog):
    """여러 PDF를 병합하는 다이얼로그."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PDF 병합")
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("병합할 PDF 파일 목록:"))

        self._list = QListWidget()
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("파일 추가")
        self._btn_add.clicked.connect(self._add_files)
        btn_row.addWidget(self._btn_add)

        self._btn_remove = QPushButton("제거")
        self._btn_remove.clicked.connect(self._remove_selected)
        btn_row.addWidget(self._btn_remove)

        self._btn_up = QPushButton("▲")
        self._btn_up.clicked.connect(self._move_up)
        btn_row.addWidget(self._btn_up)

        self._btn_down = QPushButton("▼")
        self._btn_down.clicked.connect(self._move_down)
        btn_row.addWidget(self._btn_down)

        layout.addLayout(btn_row)

        self._chk_bookmarks = QCheckBox("북마크 유지")
        self._chk_bookmarks.setChecked(True)
        layout.addWidget(self._chk_bookmarks)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "PDF 파일 선택", "", "PDF (*.pdf)")
        for p in paths:
            item = QListWidgetItem(os.path.basename(p))
            item.setData(Qt.ItemDataRole.UserRole, p)
            self._list.addItem(item)

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

    def file_paths(self) -> list[str]:
        return [self._list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self._list.count())]

    def keep_bookmarks(self) -> bool:
        return self._chk_bookmarks.isChecked()
