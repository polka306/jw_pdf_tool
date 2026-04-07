"""TC-353: 열기→암호 설정→저장→재열기→암호 입력→편집→암호 제거→저장."""

from __future__ import annotations

import fitz
import pytest


class TestTC353EncryptDecrypt:

    def test_tc353_full_encrypt_decrypt_workflow(self, tmp_path):
        from app.core.security import encrypt_pdf, decrypt_pdf

        # 원본 PDF
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), "Secret document", fontsize=14)
        orig = str(tmp_path / "orig.pdf")
        doc.save(orig)
        doc.close()

        # 암호 설정
        enc = str(tmp_path / "enc.pdf")
        encrypt_pdf(orig, enc, user_password="mypass")

        # 재열기 + 인증
        doc2 = fitz.open(enc)
        assert doc2.is_encrypted
        assert doc2.authenticate("mypass")
        assert "Secret" in doc2[0].get_text()
        doc2.close()

        # 암호 제거
        dec = str(tmp_path / "dec.pdf")
        decrypt_pdf(enc, dec, password="mypass")

        doc3 = fitz.open(dec)
        assert not doc3.is_encrypted
        assert "Secret" in doc3[0].get_text()
        doc3.close()
