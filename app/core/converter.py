"""문서 변환 로직 — 이미지/Office 문서 → PDF.

app/core 규칙에 따라 UI 의존성 없는 순수 Python 로직만 포함합니다.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ── 지원 형식 ─────────────────────────────────────────────────────────────────

SUPPORTED_IMAGE_EXTS: frozenset[str] = frozenset({
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp",
})

SUPPORTED_OFFICE_EXTS: frozenset[str] = frozenset({
    ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".odt", ".ods", ".odp",
})

# ── 이미지 → PDF ──────────────────────────────────────────────────────────────

def convert_images_to_pdf(image_paths: list[str], output_path: str) -> str:
    """이미지 파일 목록을 페이지 순서대로 하나의 PDF로 변환합니다.

    PyMuPDF를 사용해 각 이미지를 PDF 페이지로 변환 후 병합합니다.
    반환값: output_path (str)
    """
    if not image_paths:
        raise ValueError("변환할 이미지가 없습니다.")

    import fitz

    pdf = fitz.open()
    for img_path in image_paths:
        try:
            img_doc = fitz.open(img_path)
        except Exception as exc:
            raise RuntimeError(f"이미지를 열 수 없습니다: {img_path}\n{exc}") from exc
        pdf_bytes = img_doc.convert_to_pdf()
        img_doc.close()
        img_pdf = fitz.open("pdf", pdf_bytes)
        pdf.insert_pdf(img_pdf)
        img_pdf.close()

    pdf.save(output_path, garbage=4, deflate=True)
    pdf.close()
    return output_path


# ── Office → PDF ──────────────────────────────────────────────────────────────

def convert_office_to_pdf(input_path: str, output_dir: str) -> str:
    """LibreOffice CLI를 사용해 Office 문서를 PDF로 변환합니다.

    반환값: 생성된 PDF 파일의 절대 경로
    LibreOffice 미설치 시 RuntimeError를 raise합니다.
    """
    soffice = find_libreoffice()
    if soffice is None:
        raise RuntimeError(
            "LibreOffice를 찾을 수 없습니다.\n"
            "https://www.libreoffice.org 에서 설치하거나\n"
            "LIBREOFFICE_PATH 환경 변수로 경로를 지정하세요."
        )

    cmd = [
        soffice,
        "--headless",
        "--norestore",          # 이전 세션 복구 팝업 방지
        "--convert-to", "pdf",
        "--outdir", output_dir,
        input_path,
    ]

    # Windows: 콘솔 창 팝업 방지
    kwargs: dict = {
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "timeout": 120,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"변환 실패:\n{result.stderr or result.stdout}")

    base = Path(input_path).stem
    output_path = str(Path(output_dir) / (base + ".pdf"))
    if not os.path.exists(output_path):
        raise RuntimeError(
            f"변환 후 파일을 찾을 수 없습니다: {output_path}\n"
            f"LibreOffice 출력:\n{result.stdout}"
        )
    return output_path


# ── LibreOffice 탐지 ──────────────────────────────────────────────────────────

_LO_CANDIDATES: list[str] = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]

_LO_GLOB_PATTERNS: list[str] = [
    r"C:\Program Files\LibreOffice*\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice*\program\soffice.exe",
]


def find_libreoffice() -> str | None:
    """LibreOffice 실행 파일 경로를 반환합니다. 찾지 못하면 None."""
    # 1. 환경 변수 우선
    env_path = os.environ.get("LIBREOFFICE_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. 표준 설치 경로
    for candidate in _LO_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate

    # 3. 버전 번호 포함 경로 (glob)
    for pattern in _LO_GLOB_PATTERNS:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]

    # 4. PATH 탐지
    return shutil.which("soffice")


def is_libreoffice_available() -> bool:
    """LibreOffice 사용 가능 여부를 반환합니다."""
    return find_libreoffice() is not None
