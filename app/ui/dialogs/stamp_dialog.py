"""스탬프 선택 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class StampDialog(QDialog):
    """텍스트/이미지 스탬프 선택 다이얼로그."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("스탬프")
        self.setMinimumWidth(400)
        self._image_path: str = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()

        # 텍스트 스탬프
        text_tab = QWidget()
        text_layout = QFormLayout(text_tab)

        self._combo_preset = QComboBox()
        self._combo_preset.addItems(["직접 입력", "승인", "반려", "검토 완료", "긴급",
                                     "APPROVED", "REJECTED", "DRAFT"])
        self._combo_preset.currentTextChanged.connect(self._on_preset)
        text_layout.addRow("프리셋:", self._combo_preset)

        self._edit_text = QLineEdit("APPROVED")
        text_layout.addRow("텍스트:", self._edit_text)

        self._spin_fontsize = QSpinBox()
        self._spin_fontsize.setRange(8, 72)
        self._spin_fontsize.setValue(24)
        text_layout.addRow("크기:", self._spin_fontsize)

        self._spin_rotate = QSpinBox()
        self._spin_rotate.setRange(-180, 180)
        self._spin_rotate.setValue(0)
        text_layout.addRow("회전(도):", self._spin_rotate)

        self._spin_opacity = QDoubleSpinBox()
        self._spin_opacity.setRange(0.0, 1.0)
        self._spin_opacity.setSingleStep(0.1)
        self._spin_opacity.setValue(1.0)
        text_layout.addRow("투명도:", self._spin_opacity)

        self._tabs.addTab(text_tab, "텍스트 스탬프")

        # 이미지 스탬프
        img_tab = QWidget()
        img_layout = QFormLayout(img_tab)

        self._lbl_image = QLabel("(선택 안 됨)")
        img_layout.addRow("파일:", self._lbl_image)

        btn_browse = QPushButton("이미지 선택...")
        btn_browse.clicked.connect(self._browse_image)
        img_layout.addRow(btn_browse)

        self._tabs.addTab(img_tab, "이미지 스탬프")

        layout.addWidget(self._tabs)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _on_preset(self, text: str) -> None:
        if text != "직접 입력":
            self._edit_text.setText(text)

    def _browse_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "스탬프 이미지 선택", "", "이미지 (*.png *.jpg *.jpeg)"
        )
        if path:
            self._image_path = path
            self._lbl_image.setText(path.split("/")[-1].split("\\")[-1])

    def is_text_stamp(self) -> bool:
        return self._tabs.currentIndex() == 0

    def stamp_text(self) -> str:
        return self._edit_text.text()

    def fontsize(self) -> int:
        return self._spin_fontsize.value()

    def rotation(self) -> int:
        return self._spin_rotate.value()

    def opacity(self) -> float:
        return self._spin_opacity.value()

    def image_path(self) -> str:
        return self._image_path
