"""PDF 보안 — 암호화/복호화."""

from __future__ import annotations

import fitz


# 알고리즘 매핑
_ALGORITHM_MAP = {
    "AES-256": fitz.PDF_ENCRYPT_AES_256,
    "AES-128": fitz.PDF_ENCRYPT_AES_128,
    "RC4-128": fitz.PDF_ENCRYPT_RC4_128,
}

# 권한 비트 매핑 (fitz 상수)
_PERM_PRINT = fitz.PDF_PERM_PRINT
_PERM_COPY = fitz.PDF_PERM_COPY
_PERM_MODIFY = fitz.PDF_PERM_MODIFY
_PERM_ANNOTATE = fitz.PDF_PERM_ANNOTATE


def encrypt_pdf(
    input_path: str,
    output_path: str,
    *,
    user_password: str = "",
    owner_password: str = "",
    algorithm: str = "AES-256",
    permissions: dict[str, bool] | None = None,
) -> None:
    """PDF 파일을 암호화하여 저장.

    Parameters
    ----------
    user_password : str
        문서 열기 비밀번호. 빈 문자열이면 비밀번호 없이 열기 가능.
    owner_password : str
        권한 비밀번호. 빈 문자열이면 user_password와 동일하게 설정.
    algorithm : str
        "AES-256", "AES-128", "RC4-128".
    permissions : dict
        {"print": bool, "copy": bool, "modify": bool, "annotate": bool}.
    """
    enc_method = _ALGORITHM_MAP.get(algorithm, fitz.PDF_ENCRYPT_AES_256)

    # 권한 비트 계산
    perm = fitz.PDF_PERM_ACCESSIBILITY  # 항상 허용
    if permissions is None:
        perm |= _PERM_PRINT | _PERM_COPY | _PERM_MODIFY | _PERM_ANNOTATE
    else:
        if permissions.get("print", True):
            perm |= _PERM_PRINT
        if permissions.get("copy", True):
            perm |= _PERM_COPY
        if permissions.get("modify", True):
            perm |= _PERM_MODIFY
        if permissions.get("annotate", True):
            perm |= _PERM_ANNOTATE

    if not owner_password:
        owner_password = user_password

    doc = fitz.open(input_path)
    doc.save(
        output_path,
        encryption=enc_method,
        user_pw=user_password,
        owner_pw=owner_password,
        permissions=perm,
    )
    doc.close()


def decrypt_pdf(
    input_path: str,
    output_path: str,
    *,
    password: str,
) -> None:
    """암호화된 PDF를 복호화하여 비암호화 상태로 저장.

    Raises
    ------
    ValueError
        비밀번호가 틀린 경우.
    """
    doc = fitz.open(input_path)

    if doc.is_encrypted:
        if not doc.authenticate(password):
            doc.close()
            raise ValueError("비밀번호가 올바르지 않습니다.")

    doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
    doc.close()


# ── 리댁션 ────────────────────────────────────────────────────────────────────

def redact_area(
    input_path: str,
    output_path: str,
    page_idx: int,
    rect: fitz.Rect,
) -> None:
    """PDF 페이지의 지정 영역을 영구 삭제(리댁션).

    해당 영역의 텍스트/이미지가 완전히 제거되고 검은 사각형으로 대체됩니다.
    """
    doc = fitz.open(input_path)
    page = doc[page_idx]

    # 리댁션 어노테이션 추가
    annot = page.add_redact_annot(rect, fill=(0, 0, 0))
    # 리댁션 적용 (영구 삭제)
    page.apply_redactions()

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
