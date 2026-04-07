"""디지털 서명 다이얼로그."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class SignatureDialog(QDialog):
    """디지털 서명 다이얼로그."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("디지털 서명")
        self.setMinimumWidth(400)
        self._cert_path = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 인증서 선택
        cert_row = QLabel("(선택 안 됨)")
        self._lbl_cert = cert_row
        form.addRow("인증서:", self._lbl_cert)

        btn_cert = QPushButton("인증서 선택 (.p12/.pfx)...")
        btn_cert.clicked.connect(self._select_cert)
        form.addRow(btn_cert)

        self._edit_password = QLineEdit()
        self._edit_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._edit_password.setPlaceholderText("인증서 비밀번호")
        form.addRow("비밀번호:", self._edit_password)

        self._edit_reason = QLineEdit()
        self._edit_reason.setPlaceholderText("서명 사유 (선택)")
        form.addRow("서명 사유:", self._edit_reason)

        layout.addLayout(form)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _select_cert(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "인증서 선택", "", "PKCS#12 (*.p12 *.pfx)"
        )
        if path:
            self._cert_path = path
            self._lbl_cert.setText(path.split("/")[-1].split("\\")[-1])

    def cert_path(self) -> str:
        return self._cert_path

    def cert_password(self) -> str:
        return self._edit_password.text()

    def reason(self) -> str:
        return self._edit_reason.text()
