"""워터마크/머리글/바닥글 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class WatermarkDialog(QDialog):
    """워터마크/머리글/바닥글 설정 다이얼로그."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("워터마크 / 머리글·바닥글")
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()

        # 워터마크 탭
        wm_tab = QWidget()
        wm_layout = QFormLayout(wm_tab)

        self._edit_wm_text = QLineEdit("DRAFT")
        wm_layout.addRow("텍스트:", self._edit_wm_text)

        self._combo_preset = QComboBox()
        self._combo_preset.addItems(["직접 입력", "기밀", "사본", "DRAFT", "CONFIDENTIAL"])
        self._combo_preset.currentTextChanged.connect(self._on_preset_changed)
        wm_layout.addRow("프리셋:", self._combo_preset)

        self._spin_opacity = QDoubleSpinBox()
        self._spin_opacity.setRange(0.0, 1.0)
        self._spin_opacity.setSingleStep(0.1)
        self._spin_opacity.setValue(0.3)
        wm_layout.addRow("투명도:", self._spin_opacity)

        self._spin_rotate = QSpinBox()
        self._spin_rotate.setRange(-180, 180)
        self._spin_rotate.setValue(45)
        wm_layout.addRow("회전(도):", self._spin_rotate)

        self._chk_tile = QCheckBox("타일 반복")
        wm_layout.addRow(self._chk_tile)

        self._tabs.addTab(wm_tab, "워터마크")

        # 머리글/바닥글 탭
        hf_tab = QWidget()
        hf_layout = QFormLayout(hf_tab)

        self._edit_header_left = QLineEdit()
        self._edit_header_center = QLineEdit()
        self._edit_header_right = QLineEdit()
        hf_layout.addRow("머리글 좌:", self._edit_header_left)
        hf_layout.addRow("머리글 중:", self._edit_header_center)
        hf_layout.addRow("머리글 우:", self._edit_header_right)

        self._edit_footer_left = QLineEdit()
        self._edit_footer_center = QLineEdit("{page} / {total}")
        self._edit_footer_right = QLineEdit()
        hf_layout.addRow("바닥글 좌:", self._edit_footer_left)
        hf_layout.addRow("바닥글 중:", self._edit_footer_center)
        hf_layout.addRow("바닥글 우:", self._edit_footer_right)

        self._chk_skip_first = QCheckBox("첫 페이지 제외")
        hf_layout.addRow(self._chk_skip_first)

        self._tabs.addTab(hf_tab, "머리글/바닥글")

        layout.addWidget(self._tabs)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _on_preset_changed(self, text: str) -> None:
        if text != "직접 입력":
            self._edit_wm_text.setText(text)

    # 공개 API
    def watermark_text(self) -> str:
        return self._edit_wm_text.text()

    def opacity(self) -> float:
        return self._spin_opacity.value()

    def rotation(self) -> int:
        return self._spin_rotate.value()

    def is_tile(self) -> bool:
        return self._chk_tile.isChecked()

    def header_footer_settings(self) -> dict:
        return {
            "header_left": self._edit_header_left.text(),
            "header_center": self._edit_header_center.text(),
            "header_right": self._edit_header_right.text(),
            "footer_left": self._edit_footer_left.text(),
            "footer_center": self._edit_footer_center.text(),
            "footer_right": self._edit_footer_right.text(),
            "skip_first": self._chk_skip_first.isChecked(),
        }

    def current_tab(self) -> int:
        return self._tabs.currentIndex()
