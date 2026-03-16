"""페이지 삽입 다이얼로그 — 다른 PDF 파일에서 페이지를 선택해 삽입."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import fitz  # PyMuPDF

THUMB_WIDTH = 110


class InsertDialog(QDialog):
    """다른 PDF에서 삽입할 페이지를 선택하는 다이얼로그.

    사용 예:
        dlg = InsertDialog(parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            source_path = dlg.source_path()
            indices = dlg.selected_indices()
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._source_path: str | None = None
        self._source_doc: fitz.Document | None = None
        self.setWindowTitle("페이지 삽입")
        self.setMinimumSize(400, 520)
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI 초기화
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 파일 선택 영역
        file_row = QHBoxLayout()
        self._lbl_file = QLabel("파일을 선택하세요")
        self._lbl_file.setStyleSheet("color: #888;")
        btn_browse = QPushButton("PDF 파일 선택...")
        btn_browse.clicked.connect(self._browse_file)
        file_row.addWidget(self._lbl_file, 1)
        file_row.addWidget(btn_browse)
        layout.addLayout(file_row)

        # 안내 라벨
        self._lbl_hint = QLabel("삽입할 페이지를 선택하세요 (Ctrl/Shift로 다중 선택)")
        self._lbl_hint.setStyleSheet("color: #aaa; font-size: 11px;")
        self._lbl_hint.setVisible(False)
        layout.addWidget(self._lbl_hint)

        # 썸네일 리스트
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._list.setViewMode(QListWidget.ViewMode.IconMode)
        self._list.setIconSize(self._list.iconSize())
        self._list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._list.setGridSize(self._list.gridSize())
        self._list.setSpacing(6)
        self._list.setStyleSheet(
            """
            QListWidget { background:#1e1e1e; border:1px solid #444; }
            QListWidget::item { color:#ccc; border:1px solid transparent; }
            QListWidget::item:selected { background:#0e5a8a; border:1px solid #1a8ac4; }
            """
        )
        layout.addWidget(self._list, 1)

        # 선택 개수 표시
        self._lbl_count = QLabel("0개 선택됨")
        self._lbl_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._lbl_count.setStyleSheet("color:#aaa; font-size:11px;")
        layout.addWidget(self._lbl_count)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)

        # 확인 / 취소 버튼
        self._btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("삽입")
        self._btn_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self._btn_box.accepted.connect(self.accept)
        self._btn_box.rejected.connect(self.reject)
        layout.addWidget(self._btn_box)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def source_path(self) -> str | None:
        return self._source_path

    def selected_indices(self) -> list[int]:
        """선택된 페이지 인덱스 목록 (0-based)."""
        return sorted(self._list.row(item) for item in self._list.selectedItems())

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "삽입할 PDF 파일 선택", "", "PDF 파일 (*.pdf)"
        )
        if not path:
            return
        self._load_source(path)

    def _load_source(self, path: str) -> None:
        if self._source_doc:
            self._source_doc.close()
        self._source_doc = fitz.open(path)
        self._source_path = path
        self._lbl_file.setText(path.split("/")[-1].split("\\")[-1])
        self._lbl_file.setStyleSheet("color: #eee;")
        self._lbl_hint.setVisible(True)

        self._list.clear()
        for i in range(len(self._source_doc)):
            item = self._make_item(i)
            self._list.addItem(item)

    def _make_item(self, page_idx: int) -> QListWidgetItem:
        page = self._source_doc[page_idx]
        zoom = THUMB_WIDTH / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        pixmap = QPixmap.fromImage(QImage.fromData(pix.tobytes("png")))

        item = QListWidgetItem()
        item.setIcon(QIcon(pixmap))
        item.setText(f"p.{page_idx + 1}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        item.setSizeHint(pixmap.size().__class__(THUMB_WIDTH + 8, int(THUMB_WIDTH * 1.4) + 20))
        return item

    def _on_selection_changed(self) -> None:
        count = len(self._list.selectedItems())
        self._lbl_count.setText(f"{count}개 선택됨")
        self._btn_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(count > 0)

    def closeEvent(self, event) -> None:
        if self._source_doc:
            self._source_doc.close()
        super().closeEvent(event)
