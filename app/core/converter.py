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

SUPPORTED_MARKDOWN_EXTS: frozenset[str] = frozenset({
    ".md", ".markdown", ".mkd", ".mdown",
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


# ── Pandoc 탐지 ──────────────────────────────────────────────────────────────

_PANDOC_CANDIDATES: list[str] = [
    r"C:\Program Files\Pandoc\pandoc.exe",
    r"C:\Program Files (x86)\Pandoc\pandoc.exe",
]


def find_pandoc() -> str | None:
    """Pandoc 실행 파일 경로를 반환합니다. 찾지 못하면 None."""
    # 1. 환경 변수 우선
    env_path = os.environ.get("PANDOC_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. 표준 설치 경로
    for candidate in _PANDOC_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate

    # 3. AppData\Local\Pandoc (winget/scoop 설치 시)
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        local_pandoc = os.path.join(local_app, "Pandoc", "pandoc.exe")
        if os.path.isfile(local_pandoc):
            return local_pandoc

    # 4. PATH 탐지
    return shutil.which("pandoc")


def is_pandoc_available() -> bool:
    """Pandoc 사용 가능 여부를 반환합니다."""
    return find_pandoc() is not None


# ── Markdown → PDF ───────────────────────────────────────────────────────────

def _resolve_md_image_paths(text: str, base_dir: str) -> str:
    """Markdown 내 상대 이미지 경로를 절대 경로로 변환합니다."""
    import re

    def _resolve(m):
        alt, rel_path = m.group(1), m.group(2)
        abs_path = os.path.normpath(os.path.join(base_dir, rel_path))
        return f"![{alt}]({abs_path})"

    # ![alt](relative/path) 패턴 — http(s):// 및 절대 경로 제외
    return re.sub(
        r'!\[([^\]]*)\]\((?!https?://|[A-Za-z]:\\|/)([^)]+)\)',
        _resolve,
        text,
    )


def _read_and_merge_markdown(md_paths: list[str]) -> tuple[str, str]:
    """여러 Markdown 파일을 하나로 합치고, (합친 텍스트, 첫 파일 디렉토리)를 반환합니다."""
    parts: list[str] = []
    first_dir = os.path.dirname(os.path.abspath(md_paths[0]))
    for path in md_paths:
        base_dir = os.path.dirname(os.path.abspath(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        content = _resolve_md_image_paths(content, base_dir)
        parts.append(content)
    return "\n\n---\n\n".join(parts), first_dir


def _convert_markdown_pandoc(
    md_text: str,
    output_path: str,
    resource_dir: str,
) -> bool:
    """Pandoc으로 Markdown을 PDF로 변환합니다. 성공하면 True."""
    pandoc = find_pandoc()
    if pandoc is None:
        return False

    import tempfile
    tmp_md = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False,
    )
    try:
        tmp_md.write(md_text)
        tmp_md.close()

        # 기본 명령 — Pandoc이 적절한 PDF 엔진을 자동 선택
        cmd = [
            pandoc,
            tmp_md.name,
            "-o", output_path,
            f"--resource-path={resource_dir}",
            "--highlight-style=tango",
            "-V", "geometry:margin=2.5cm",
            "-V", "mainfont=Malgun Gothic",
            "-V", "monofont=Consolas",
        ]

        kwargs: dict = {
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "timeout": 120,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(cmd, **kwargs)
        if result.returncode == 0 and os.path.exists(output_path):
            return True

        # xelatex 엔진을 명시적으로 지정하여 재시도
        cmd_xelatex = cmd + ["--pdf-engine=xelatex"]
        result = subprocess.run(cmd_xelatex, **kwargs)
        if result.returncode == 0 and os.path.exists(output_path):
            return True

        return False
    finally:
        try:
            os.unlink(tmp_md.name)
        except OSError:
            pass


_MD_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: "Malgun Gothic", "맑은 고딕", sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
  }}
  h1 {{ font-size: 22pt; border-bottom: 2px solid #333; padding-bottom: 6px; }}
  h2 {{ font-size: 18pt; border-bottom: 1px solid #999; padding-bottom: 4px; }}
  h3 {{ font-size: 14pt; }}
  code {{
    font-family: "Consolas", "D2Coding", monospace;
    background: #f4f4f4;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 10pt;
  }}
  pre {{
    background: #f4f4f4;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
  }}
  pre code {{
    background: none;
    padding: 0;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
  }}
  th, td {{
    border: 1px solid #ccc;
    padding: 6px 10px;
    text-align: left;
  }}
  th {{
    background: #f0f0f0;
    font-weight: bold;
  }}
  blockquote {{
    border-left: 4px solid #ccc;
    margin: 8px 0;
    padding: 4px 16px;
    color: #666;
  }}
  hr {{
    border: none;
    border-top: 1px solid #ccc;
    margin: 24px 0;
  }}
  img {{
    max-width: 100%;
  }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def _convert_markdown_fitz(md_text: str, output_path: str) -> str:
    """Python (markdown + fitz.Story)으로 Markdown을 PDF로 변환합니다."""
    import markdown as md_lib
    import fitz

    html_body = md_lib.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "attr_list"],
    )
    full_html = _MD_HTML_TEMPLATE.format(body=html_body)

    story = fitz.Story(html=full_html)
    writer = fitz.DocumentWriter(output_path)
    mediabox = fitz.paper_rect("a4")
    where = mediabox + fitz.Rect(54, 54, -54, -54)  # ~1.9cm 마진

    more = True
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()

    writer.close()
    return output_path


def convert_markdown_to_pdf(md_paths: list[str], output_path: str) -> str:
    """Markdown 파일을 PDF로 변환합니다.

    Pandoc이 설치되어 있으면 고품질 변환을 수행하고,
    없거나 실패하면 Python 기본 변환(markdown + fitz)으로 폴백합니다.

    반환값: output_path (str)
    """
    if not md_paths:
        raise ValueError("변환할 Markdown 파일이 없습니다.")

    md_text, resource_dir = _read_and_merge_markdown(md_paths)

    # 1차: Pandoc 시도
    if _convert_markdown_pandoc(md_text, output_path, resource_dir):
        return output_path

    # 2차: Python 폴백
    return _convert_markdown_fitz(md_text, output_path)


# ── PDF → 이미지 내보내기 ──────────────────────────────────────────────────────

def export_pages_to_images(
    pdf_path: str,
    output_dir: str,
    *,
    fmt: str = "png",
    dpi: int = 150,
    page_indices: list[int] | None = None,
    color_mode: str = "color",
) -> list[str]:
    """PDF 페이지를 이미지 파일로 내보내기.

    color_mode: "color", "grayscale", "bw"

    Parameters
    ----------
    pdf_path : str
        입력 PDF 파일 경로.
    output_dir : str
        출력 디렉토리.
    fmt : str
        출력 형식 ("png", "jpg", "tiff").
    dpi : int
        해상도.
    page_indices : list[int] | None
        내보낼 페이지 인덱스. None이면 전체.

    Returns
    -------
    list[str]
        생성된 이미지 파일 경로 목록.
    """
    import fitz as fitz_mod

    doc = fitz_mod.open(pdf_path)
    stem = Path(pdf_path).stem
    zoom = dpi / 72.0
    mat = fitz_mod.Matrix(zoom, zoom)

    indices = page_indices or list(range(len(doc)))
    files: list[str] = []

    for idx in indices:
        page = doc[idx]
        if color_mode == "grayscale":
            pix = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz_mod.csGRAY)
        else:
            pix = page.get_pixmap(matrix=mat, alpha=False)

        # 흑백 변환 (1bit)
        if color_mode == "bw":
            from PIL import Image as PILImage
            import io
            img = PILImage.open(io.BytesIO(pix.tobytes("png")))
            img = img.convert("1")  # 1-bit black & white
            bw_path = os.path.join(output_dir, f"{stem}_page{idx + 1}.{fmt.lower()}")
            img.save(bw_path)
            files.append(bw_path)
            continue

        ext = fmt.lower()
        if ext == "jpg":
            ext_save = "jpeg"
        else:
            ext_save = ext

        filename = f"{stem}_page{idx + 1}.{fmt.lower()}"
        filepath = os.path.join(output_dir, filename)

        if ext_save == "jpeg":
            pix.save(filepath, output=ext_save)
        else:
            pix.save(filepath)

        files.append(filepath)

    doc.close()
    return files


# ── PDF → 텍스트 내보내기 ──────────────────────────────────────────────────────

def export_pdf_to_text(
    pdf_path: str,
    output_path: str,
    *,
    page_indices: list[int] | None = None,
    output_format: str = "txt",
) -> str:
    """PDF에서 텍스트를 추출하여 파일로 저장.

    Parameters
    ----------
    output_format : str
        "txt" 또는 "docx".
    """
    import fitz as fitz_mod

    doc = fitz_mod.open(pdf_path)
    indices = page_indices or list(range(len(doc)))

    texts: list[str] = []
    for idx in indices:
        page = doc[idx]
        texts.append(page.get_text())

    doc.close()

    if output_format == "docx":
        _write_docx(output_path, texts)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(texts))

    return output_path


def _write_docx(output_path: str, texts: list[str]) -> None:
    """텍스트를 간단한 DOCX 파일로 저장 (python-docx 없이 ZIP 기반)."""
    import zipfile
    from xml.etree.ElementTree import Element, SubElement, tostring

    # DOCX는 ZIP 기반 XML
    NSMAP = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    body = Element(f"{{{NSMAP}}}body")
    document = Element(f"{{{NSMAP}}}document")
    document.append(body)

    for text in texts:
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            p = SubElement(body, f"{{{NSMAP}}}p")
            r = SubElement(p, f"{{{NSMAP}}}r")
            t = SubElement(r, f"{{{NSMAP}}}t")
            t.text = line

    doc_xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + tostring(document)

    content_types = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    rels = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", doc_xml)
