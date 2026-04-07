"""양식 필드 속성 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)


class FormDialog(QDialog):
    """양식 필드 생성/편집 다이얼로그."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("양식 필드")
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._edit_name = QLineEdit()
        self._edit_name.setPlaceholderText("필드 이름")
        form.addRow("이름:", self._edit_name)

        self._combo_type = QComboBox()
        self._combo_type.addItems(["텍스트", "체크박스", "드롭다운", "라디오"])
        form.addRow("유형:", self._combo_type)

        self._edit_default = QLineEdit()
        self._edit_default.setPlaceholderText("기본값")
        form.addRow("기본값:", self._edit_default)

        self._chk_required = QCheckBox("필수 입력")
        form.addRow(self._chk_required)

        layout.addLayout(form)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def field_name(self) -> str:
        return self._edit_name.text()

    def field_type(self) -> str:
        return ["text", "checkbox", "combobox", "radiobutton"][self._combo_type.currentIndex()]

    def default_value(self) -> str:
        return self._edit_default.text()

    def is_required(self) -> bool:
        return self._chk_required.isChecked()
