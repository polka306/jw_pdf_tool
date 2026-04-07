"""OCR 설정/실행 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class OcrDialog(QDialog):
    """OCR 텍스트 인식 다이얼로그."""

    def __init__(self, parent=None, page_count: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle("OCR 텍스트 인식")
        self.setMinimumWidth(400)
        self._page_count = page_count
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 엔진 상태
        from app.core.ocr_engine import get_ocr_engine_name
        engine = get_ocr_engine_name()
        status = f"OCR 엔진: {engine}" if engine != "none" else "OCR 엔진 미설치"
        self._lbl_status = QLabel(status)
        layout.addWidget(self._lbl_status)

        form = QFormLayout()

        self._combo_lang = QComboBox()
        self._combo_lang.addItems(["eng", "kor", "kor+eng", "jpn", "chi_sim"])
        form.addRow("언어:", self._combo_lang)

        self._spin_dpi = QSpinBox()
        self._spin_dpi.setRange(72, 600)
        self._spin_dpi.setValue(300)
        form.addRow("DPI:", self._spin_dpi)

        self._combo_range = QComboBox()
        self._combo_range.addItems(["전체 페이지", "현재 페이지"])
        form.addRow("범위:", self._combo_range)

        layout.addLayout(form)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._btn_cancel = QPushButton("취소")
        self._btn_cancel.setVisible(False)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        if engine == "none":
            self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout.addWidget(self._buttons)

    def language(self) -> str:
        return self._combo_lang.currentText()

    def dpi(self) -> int:
        return self._spin_dpi.value()

    def is_all_pages(self) -> bool:
        return self._combo_range.currentIndex() == 0
