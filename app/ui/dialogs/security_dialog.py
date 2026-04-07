"""PDF 암호/권한 설정 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)


class SecurityDialog(QDialog):
    """PDF 암호 설정 다이얼로그."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PDF 보안 설정")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 암호 그룹
        pw_group = QGroupBox("비밀번호")
        pw_layout = QFormLayout(pw_group)

        self._edit_user_pw = QLineEdit()
        self._edit_user_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit_user_pw.setPlaceholderText("문서 열기 비밀번호")
        pw_layout.addRow("열기 암호:", self._edit_user_pw)

        self._edit_owner_pw = QLineEdit()
        self._edit_owner_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit_owner_pw.setPlaceholderText("권한 비밀번호 (선택)")
        pw_layout.addRow("권한 암호:", self._edit_owner_pw)

        layout.addWidget(pw_group)

        # 암호화 방식
        enc_group = QGroupBox("암호화")
        enc_layout = QFormLayout(enc_group)

        self._combo_algorithm = QComboBox()
        self._combo_algorithm.addItems(["AES-256", "AES-128", "RC4-128"])
        enc_layout.addRow("알고리즘:", self._combo_algorithm)

        layout.addWidget(enc_group)

        # 권한 그룹
        perm_group = QGroupBox("권한 설정")
        perm_layout = QVBoxLayout(perm_group)

        self._chk_print = QCheckBox("인쇄 허용")
        self._chk_print.setChecked(True)
        perm_layout.addWidget(self._chk_print)

        self._chk_copy = QCheckBox("복사 허용")
        self._chk_copy.setChecked(True)
        perm_layout.addWidget(self._chk_copy)

        self._chk_modify = QCheckBox("편집 허용")
        self._chk_modify.setChecked(True)
        perm_layout.addWidget(self._chk_modify)

        layout.addWidget(perm_group)

        # 버튼
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def user_password(self) -> str:
        return self._edit_user_pw.text()

    def owner_password(self) -> str:
        return self._edit_owner_pw.text()

    def algorithm(self) -> str:
        return self._combo_algorithm.currentText()

    def permissions(self) -> dict[str, bool]:
        return {
            "print": self._chk_print.isChecked(),
            "copy": self._chk_copy.isChecked(),
            "modify": self._chk_modify.isChecked(),
        }
