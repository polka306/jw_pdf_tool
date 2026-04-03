"""pytest 공통 픽스처."""

from __future__ import annotations

import os
import tempfile

import fitz
import pytest

# ── 헤드리스 Qt 설정 (디스플레이 없이 위젯 테스트 가능) ──────────────────────
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ── PDF 생성 헬퍼 ──────────────────────────────────────────────────────────────

def _make_pdf(num_pages: int, tmp_path) -> str:
    """지정한 페이지 수의 테스트 PDF를 생성하고 경로를 반환합니다."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)  # A4 pt
        page.insert_text((72, 100), f"Page {i + 1}", fontsize=24)
        # 페이지마다 작은 사각형 그려서 시각적으로 구별
        page.draw_rect(
            fitz.Rect(50, 50, 200, 150),
            color=(0.2 * (i % 5), 0.3, 0.8),
            width=2,
        )
    path = str(tmp_path / f"test_{num_pages}pages.pdf")
    doc.save(path)
    doc.close()
    return path


# ── 픽스처 ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def pdf_1page(tmp_path) -> str:
    """1페이지짜리 테스트 PDF 경로."""
    return _make_pdf(1, tmp_path)


@pytest.fixture
def pdf_3pages(tmp_path) -> str:
    """3페이지짜리 테스트 PDF 경로."""
    return _make_pdf(3, tmp_path)


@pytest.fixture
def pdf_5pages(tmp_path) -> str:
    """5페이지짜리 테스트 PDF 경로."""
    return _make_pdf(5, tmp_path)


@pytest.fixture
def pdf_10pages(tmp_path) -> str:
    """10페이지짜리 테스트 PDF 경로."""
    return _make_pdf(10, tmp_path)


@pytest.fixture
def corrupt_pdf(tmp_path) -> str:
    """손상된 파일 경로 (PDF가 아닌 내용)."""
    path = str(tmp_path / "corrupt.pdf")
    with open(path, "wb") as f:
        f.write(b"This is not a PDF file at all!")
    return path


@pytest.fixture
def text_file(tmp_path) -> str:
    """PDF가 아닌 텍스트 파일 경로."""
    path = str(tmp_path / "readme.txt")
    with open(path, "w") as f:
        f.write("hello world")
    return path


@pytest.fixture
def open_doc(pdf_3pages):
    """열려 있는 PdfDocument 인스턴스 (3페이지)."""
    from app.core.pdf_document import PdfDocument
    doc = PdfDocument()
    doc.open(pdf_3pages)
    yield doc
    doc.close()


@pytest.fixture
def main_window(qtbot):
    """MainWindow 인스턴스. teardown에서 QThread 정리 + close."""
    from app.ui.main_window import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    yield win
    if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
        win._page_panel._cancel_loader()
    win.close()
