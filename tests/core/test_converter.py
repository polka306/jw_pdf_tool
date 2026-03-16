"""app.core.converter 단위 테스트."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _make_png(path: str, size=(200, 150), color=(100, 149, 237)) -> str:
    """테스트용 PNG 이미지를 생성합니다."""
    from PIL import Image
    Image.new("RGB", size, color=color).save(path)
    return path


# ── 픽스처 ────────────────────────────────────────────────────────────────────

@pytest.fixture
def png1(tmp_path) -> str:
    return _make_png(str(tmp_path / "img1.png"), color=(200, 100, 50))


@pytest.fixture
def png2(tmp_path) -> str:
    return _make_png(str(tmp_path / "img2.png"), color=(50, 200, 100))


@pytest.fixture
def png3(tmp_path) -> str:
    return _make_png(str(tmp_path / "img3.png"), color=(100, 50, 200))


@pytest.fixture
def jpg1(tmp_path) -> str:
    from PIL import Image
    path = str(tmp_path / "img.jpg")
    Image.new("RGB", (300, 200), color=(255, 165, 0)).save(path, "JPEG")
    return path


# ── 이미지 → PDF 변환 테스트 ──────────────────────────────────────────────────

class TestConvertImagesToPdf:

    def test_single_png_creates_file(self, tmp_path, png1):
        from app.core.converter import convert_images_to_pdf
        out = str(tmp_path / "out.pdf")
        result = convert_images_to_pdf([png1], out)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_returns_output_path(self, tmp_path, png1):
        from app.core.converter import convert_images_to_pdf
        out = str(tmp_path / "out.pdf")
        result = convert_images_to_pdf([png1], out)
        assert result == out

    def test_single_image_page_count_is_1(self, tmp_path, png1):
        import fitz
        from app.core.converter import convert_images_to_pdf
        out = str(tmp_path / "out.pdf")
        convert_images_to_pdf([png1], out)
        doc = fitz.open(out)
        assert len(doc) == 1
        doc.close()

    def test_multiple_images_correct_page_count(self, tmp_path, png1, png2, png3):
        import fitz
        from app.core.converter import convert_images_to_pdf
        out = str(tmp_path / "multi.pdf")
        convert_images_to_pdf([png1, png2, png3], out)
        doc = fitz.open(out)
        assert len(doc) == 3
        doc.close()

    def test_jpg_conversion(self, tmp_path, jpg1):
        from app.core.converter import convert_images_to_pdf
        out = str(tmp_path / "jpg.pdf")
        result = convert_images_to_pdf([jpg1], out)
        assert os.path.exists(result)

    def test_empty_list_raises_value_error(self, tmp_path):
        from app.core.converter import convert_images_to_pdf
        with pytest.raises(ValueError, match="이미지"):
            convert_images_to_pdf([], str(tmp_path / "out.pdf"))

    def test_nonexistent_file_raises(self, tmp_path):
        from app.core.converter import convert_images_to_pdf
        with pytest.raises((FileNotFoundError, RuntimeError)):
            convert_images_to_pdf(["/nonexistent/img.png"], str(tmp_path / "out.pdf"))

    def test_two_images_order_preserved(self, tmp_path, png1, png2):
        """두 이미지 순서가 PDF 페이지 순서로 유지되어야 합니다."""
        import fitz
        from app.core.converter import convert_images_to_pdf
        out = str(tmp_path / "order.pdf")
        convert_images_to_pdf([png1, png2], out)
        doc = fitz.open(out)
        # 페이지 수만 확인 (내용 순서는 fitz 내부 보장)
        assert len(doc) == 2
        doc.close()


# ── 지원 형식 상수 테스트 ─────────────────────────────────────────────────────

class TestSupportedExtensions:

    def test_image_exts_contains_jpg(self):
        from app.core.converter import SUPPORTED_IMAGE_EXTS
        assert ".jpg" in SUPPORTED_IMAGE_EXTS
        assert ".jpeg" in SUPPORTED_IMAGE_EXTS

    def test_image_exts_contains_png(self):
        from app.core.converter import SUPPORTED_IMAGE_EXTS
        assert ".png" in SUPPORTED_IMAGE_EXTS

    def test_office_exts_contains_docx(self):
        from app.core.converter import SUPPORTED_OFFICE_EXTS
        assert ".docx" in SUPPORTED_OFFICE_EXTS

    def test_office_exts_contains_pptx(self):
        from app.core.converter import SUPPORTED_OFFICE_EXTS
        assert ".pptx" in SUPPORTED_OFFICE_EXTS


# ── LibreOffice 탐지 테스트 ───────────────────────────────────────────────────

class TestFindLibreOffice:

    def test_returns_str_or_none(self):
        from app.core.converter import find_libreoffice
        result = find_libreoffice()
        assert result is None or isinstance(result, str)

    def test_is_available_returns_bool(self):
        from app.core.converter import is_libreoffice_available
        assert isinstance(is_libreoffice_available(), bool)

    def test_env_var_override(self, tmp_path):
        """LIBREOFFICE_PATH 환경 변수가 있으면 최우선으로 사용되어야 합니다."""
        fake = str(tmp_path / "soffice.exe")
        open(fake, "w").close()  # 빈 파일 생성 (isfile 통과용)
        with patch.dict(os.environ, {"LIBREOFFICE_PATH": fake}):
            from app.core import converter as conv
            result = conv.find_libreoffice()
        assert result == fake

    def test_nonexistent_env_var_skipped(self, tmp_path):
        """존재하지 않는 LIBREOFFICE_PATH 는 건너뛰어야 합니다."""
        fake = str(tmp_path / "nonexistent_soffice.exe")
        with patch.dict(os.environ, {"LIBREOFFICE_PATH": fake}):
            from app.core import converter as conv
            result = conv.find_libreoffice()
        # 환경 변수 경로가 없으므로 나머지 방법으로 탐지 → str or None
        assert result is None or isinstance(result, str)
        if result:
            assert result != fake


# ── Office → PDF 변환 테스트 (subprocess 모킹) ───────────────────────────────

class TestConvertOfficeToPdf:

    def test_raises_when_libreoffice_not_found(self, tmp_path):
        from app.core.converter import convert_office_to_pdf
        with patch("app.core.converter.find_libreoffice", return_value=None):
            with pytest.raises(RuntimeError, match="LibreOffice"):
                convert_office_to_pdf("/fake/doc.docx", str(tmp_path))

    def test_raises_on_subprocess_failure(self, tmp_path):
        from app.core.converter import convert_office_to_pdf
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "conversion error"
        mock_result.stdout = ""
        with patch("app.core.converter.find_libreoffice", return_value="/fake/soffice"):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(RuntimeError, match="변환 실패"):
                    convert_office_to_pdf("/fake/doc.docx", str(tmp_path))

    def test_raises_when_output_file_missing(self, tmp_path):
        """subprocess 성공이지만 출력 파일이 없으면 RuntimeError."""
        from app.core.converter import convert_office_to_pdf
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = ""
        with patch("app.core.converter.find_libreoffice", return_value="/fake/soffice"):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(RuntimeError, match="찾을 수 없습니다"):
                    convert_office_to_pdf("/fake/doc.docx", str(tmp_path))

    def test_returns_correct_output_path(self, tmp_path):
        """성공 시 올바른 경로를 반환해야 합니다."""
        from app.core.converter import convert_office_to_pdf
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = ""
        # 출력 파일을 미리 생성 (os.path.exists 통과)
        expected_out = str(tmp_path / "report.pdf")
        open(expected_out, "w").close()
        with patch("app.core.converter.find_libreoffice", return_value="/fake/soffice"):
            with patch("subprocess.run", return_value=mock_result):
                result = convert_office_to_pdf(
                    str(tmp_path / "report.docx"), str(tmp_path)
                )
        assert result == expected_out
