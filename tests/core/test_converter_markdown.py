"""Markdown → PDF 변환 테스트."""

from __future__ import annotations

import os

import fitz
import pytest

from app.core.converter import (
    SUPPORTED_MARKDOWN_EXTS,
    convert_markdown_to_pdf,
    find_pandoc,
    is_pandoc_available,
)


# ── Pandoc 탐지 ──────────────────────────────────────────────────────────────


class TestFindPandoc:
    def test_returns_str_or_none(self):
        result = find_pandoc()
        assert result is None or isinstance(result, str)

    def test_is_available_returns_bool(self):
        assert isinstance(is_pandoc_available(), bool)

    def test_env_var_override(self, tmp_path, monkeypatch):
        fake = str(tmp_path / "pandoc.exe")
        with open(fake, "w") as f:
            f.write("fake")
        monkeypatch.setenv("PANDOC_PATH", fake)
        assert find_pandoc() == fake

    def test_nonexistent_env_var_skipped(self, monkeypatch):
        monkeypatch.setenv("PANDOC_PATH", "/no/such/pandoc")
        result = find_pandoc()
        # 실제 PATH에 있으면 str, 아니면 None
        assert result is None or isinstance(result, str)


class TestSupportedMarkdownExts:
    def test_contains_md(self):
        assert ".md" in SUPPORTED_MARKDOWN_EXTS

    def test_contains_markdown(self):
        assert ".markdown" in SUPPORTED_MARKDOWN_EXTS


# ── 변환 테스트 (Python 폴백) ────────────────────────────────────────────────


@pytest.fixture
def simple_md(tmp_path) -> str:
    path = str(tmp_path / "test.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Hello World\n\nThis is a test.\n")
    return path


@pytest.fixture
def korean_md(tmp_path) -> str:
    path = str(tmp_path / "korean.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# 한글 테스트\n\n이것은 한국어 Markdown 문서입니다.\n")
    return path


@pytest.fixture
def table_md(tmp_path) -> str:
    path = str(tmp_path / "table.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "# 표 테스트\n\n"
            "| 이름 | 값 |\n"
            "|------|----|\n"
            "| A | 1 |\n"
            "| B | 2 |\n"
        )
    return path


@pytest.fixture
def code_md(tmp_path) -> str:
    path = str(tmp_path / "code.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "# 코드 블록\n\n"
            "```python\n"
            "def hello():\n"
            '    print("Hello")\n'
            "```\n"
        )
    return path


class TestConvertMarkdownToPdf:
    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="Markdown"):
            convert_markdown_to_pdf([], "out.pdf")

    def test_single_md_creates_file(self, simple_md, tmp_path, monkeypatch):
        # Pandoc 비활성화 → Python 폴백 강제
        monkeypatch.setattr("app.core.converter.find_pandoc", lambda: None)
        out = str(tmp_path / "output.pdf")
        result = convert_markdown_to_pdf([simple_md], out)
        assert os.path.exists(result)
        doc = fitz.open(result)
        try:
            assert doc.page_count >= 1
            text = doc[0].get_text()
            assert "Hello World" in text
        finally:
            doc.close()

    def test_korean_text_renders(self, korean_md, tmp_path, monkeypatch):
        monkeypatch.setattr("app.core.converter.find_pandoc", lambda: None)
        out = str(tmp_path / "korean.pdf")
        result = convert_markdown_to_pdf([korean_md], out)
        assert os.path.exists(result)
        doc = fitz.open(result)
        try:
            assert doc.page_count >= 1
        finally:
            doc.close()

    def test_table_renders(self, table_md, tmp_path, monkeypatch):
        monkeypatch.setattr("app.core.converter.find_pandoc", lambda: None)
        out = str(tmp_path / "table.pdf")
        result = convert_markdown_to_pdf([table_md], out)
        assert os.path.exists(result)
        doc = fitz.open(result)
        try:
            assert doc.page_count >= 1
        finally:
            doc.close()

    def test_code_block_renders(self, code_md, tmp_path, monkeypatch):
        monkeypatch.setattr("app.core.converter.find_pandoc", lambda: None)
        out = str(tmp_path / "code.pdf")
        result = convert_markdown_to_pdf([code_md], out)
        assert os.path.exists(result)

    def test_multiple_files_concatenated(self, simple_md, korean_md, tmp_path, monkeypatch):
        monkeypatch.setattr("app.core.converter.find_pandoc", lambda: None)
        out = str(tmp_path / "multi.pdf")
        result = convert_markdown_to_pdf([simple_md, korean_md], out)
        doc = fitz.open(result)
        try:
            assert doc.page_count >= 1
            all_text = "".join(doc[i].get_text() for i in range(doc.page_count))
            assert "Hello World" in all_text
        finally:
            doc.close()


class TestConvertMarkdownPandocPath:
    def test_pandoc_used_when_available(self, simple_md, tmp_path, monkeypatch):
        """Pandoc이 설치되어 있으면 Pandoc 경로가 호출되는지 확인."""
        calls = []

        monkeypatch.setattr(
            "app.core.converter.find_pandoc",
            lambda: "/fake/pandoc",
        )

        class FakeResult:
            returncode = 0
            stderr = ""
            stdout = ""

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            # 출력 파일 생성 (Pandoc 성공 시뮬레이션)
            for i, arg in enumerate(cmd):
                if arg == "-o" and i + 1 < len(cmd):
                    open(cmd[i + 1], "w").close()
                    break
            return FakeResult()

        monkeypatch.setattr("subprocess.run", fake_run)

        out = str(tmp_path / "pandoc_out.pdf")
        convert_markdown_to_pdf([simple_md], out)
        assert len(calls) >= 1
        assert "/fake/pandoc" in calls[0]

    def test_fallback_when_pandoc_fails(self, simple_md, tmp_path, monkeypatch):
        """Pandoc 실패 시 Python 폴백이 동작하는지 확인."""
        monkeypatch.setattr(
            "app.core.converter.find_pandoc",
            lambda: "/fake/pandoc",
        )

        class FailResult:
            returncode = 1
            stderr = "error"
            stdout = ""

        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: FailResult(),
        )

        out = str(tmp_path / "fallback.pdf")
        result = convert_markdown_to_pdf([simple_md], out)
        assert os.path.exists(result)
        doc = fitz.open(result)
        try:
            assert doc.page_count >= 1
        finally:
            doc.close()
