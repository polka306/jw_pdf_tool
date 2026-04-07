"""PDF 비교 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)


class CompareDialog(QDialog):
    """두 PDF를 비교하는 다이얼로그."""

    def __init__(self, parent=None, current_path: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("PDF 비교")
        self.setMinimumSize(500, 400)
        self._path_a = current_path
        self._path_b = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 파일 A
        row_a = QHBoxLayout()
        row_a.addWidget(QLabel("파일 A:"))
        self._edit_a = QLineEdit(self._path_a)
        self._edit_a.setReadOnly(True)
        row_a.addWidget(self._edit_a)
        btn_a = QPushButton("선택...")
        btn_a.clicked.connect(self._select_a)
        row_a.addWidget(btn_a)
        layout.addLayout(row_a)

        # 파일 B
        row_b = QHBoxLayout()
        row_b.addWidget(QLabel("파일 B:"))
        self._edit_b = QLineEdit()
        self._edit_b.setReadOnly(True)
        row_b.addWidget(self._edit_b)
        btn_b = QPushButton("선택...")
        btn_b.clicked.connect(self._select_b)
        row_b.addWidget(btn_b)
        layout.addLayout(row_b)

        # 결과 목록
        layout.addWidget(QLabel("비교 결과:"))
        self._result_list = QListWidget()
        layout.addWidget(self._result_list)

        # 버튼
        btn_row = QHBoxLayout()
        self._btn_compare = QPushButton("비교 실행")
        self._btn_compare.clicked.connect(self._run_compare)
        btn_row.addWidget(self._btn_compare)

        self._btn_prev = QPushButton("◀ 이전")
        self._btn_prev.clicked.connect(self._prev_diff)
        btn_row.addWidget(self._btn_prev)

        self._btn_next = QPushButton("다음 ▶")
        self._btn_next.clicked.connect(self._next_diff)
        btn_row.addWidget(self._btn_next)
        layout.addLayout(btn_row)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _select_a(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "파일 A 선택", "", "PDF (*.pdf)")
        if path:
            self._path_a = path
            self._edit_a.setText(path)

    def _select_b(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "파일 B 선택", "", "PDF (*.pdf)")
        if path:
            self._path_b = path
            self._edit_b.setText(path)

    def _run_compare(self) -> None:
        if not self._path_a or not self._path_b:
            return
        from app.core.comparator import compare_pdfs
        diffs = compare_pdfs(self._path_a, self._path_b)
        self._result_list.clear()
        if not diffs:
            self._result_list.addItem("차이 없음")
        for d in diffs:
            self._result_list.addItem(f"[{d.diff_type}] 페이지 {d.page_idx + 1}: {d.detail}")

    def _prev_diff(self) -> None:
        row = self._result_list.currentRow()
        if row > 0:
            self._result_list.setCurrentRow(row - 1)

    def _next_diff(self) -> None:
        row = self._result_list.currentRow()
        if row < self._result_list.count() - 1:
            self._result_list.setCurrentRow(row + 1)
