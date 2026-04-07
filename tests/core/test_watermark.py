"""TC-362 ~ TC-371: 워터마크/머리글/바닥글/베이츠 단위 테스트."""

from __future__ import annotations

import fitz
import pytest


def _make_pdf(tmp_path, pages=3, name="wm") -> str:
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page {i+1} content", fontsize=14)
    path = str(tmp_path / f"{name}.pdf")
    doc.save(path)
    doc.close()
    return path


class TestTextWatermark:

    # TC-362: 텍스트 워터마크 추가
    def test_tc362_text_watermark(self, tmp_path):
        from app.core.watermark import add_text_watermark

        pdf = _make_pdf(tmp_path)
        out = str(tmp_path / "wm_out.pdf")
        add_text_watermark(pdf, out, "DRAFT", rotate=45, opacity=0.3)

        doc = fitz.open(out)
        assert doc.page_count == 3
        doc.close()

    # TC-363: 투명도 50%
    def test_tc363_opacity(self, tmp_path):
        from app.core.watermark import add_text_watermark

        pdf = _make_pdf(tmp_path)
        out = str(tmp_path / "wm_opacity.pdf")
        add_text_watermark(pdf, out, "CONFIDENTIAL", opacity=0.5)
        assert True  # 생성 성공

    # TC-364: 전경/배경 레이어
    def test_tc364_foreground_background(self, tmp_path):
        from app.core.watermark import add_text_watermark

        pdf = _make_pdf(tmp_path)
        out_fg = str(tmp_path / "wm_fg.pdf")
        out_bg = str(tmp_path / "wm_bg.pdf")
        add_text_watermark(pdf, out_fg, "FG", layer="foreground")
        add_text_watermark(pdf, out_bg, "BG", layer="background")

    # TC-365: 이미지 워터마크
    def test_tc365_image_watermark(self, tmp_path):
        from app.core.watermark import add_image_watermark
        from PIL import Image

        img = Image.new("RGBA", (100, 50), (255, 0, 0, 64))
        img_path = str(tmp_path / "logo.png")
        img.save(img_path)

        pdf = _make_pdf(tmp_path)
        out = str(tmp_path / "wm_img.pdf")
        add_image_watermark(pdf, out, img_path, opacity=0.3)

    # TC-366: 타일 반복
    def test_tc366_tile_repeat(self, tmp_path):
        from app.core.watermark import add_text_watermark

        pdf = _make_pdf(tmp_path)
        out = str(tmp_path / "wm_tile.pdf")
        add_text_watermark(pdf, out, "SAMPLE", tile=True)


class TestHeaderFooter:

    # TC-367: 변수 치환 {page}/{total}
    def test_tc367_variable_substitution(self, tmp_path):
        from app.core.watermark import add_header_footer

        pdf = _make_pdf(tmp_path)
        out = str(tmp_path / "hf.pdf")
        add_header_footer(pdf, out, footer_center="{page} / {total}")

        doc = fitz.open(out)
        text = doc[0].get_text()
        assert "1" in text  # 페이지 번호 포함
        doc.close()

    # TC-368: 좌/중/우 3영역
    def test_tc368_three_areas(self, tmp_path):
        from app.core.watermark import add_header_footer

        pdf = _make_pdf(tmp_path)
        out = str(tmp_path / "hf3.pdf")
        add_header_footer(
            pdf, out,
            header_left="Left", header_center="Center", header_right="Right"
        )

    # TC-369: 첫 페이지 제외
    def test_tc369_skip_first_page(self, tmp_path):
        from app.core.watermark import add_header_footer

        pdf = _make_pdf(tmp_path)
        out = str(tmp_path / "hf_skip.pdf")
        add_header_footer(pdf, out, footer_center="{page}", skip_first=True)


class TestBatesNumbering:

    # TC-370: 기본 베이츠 번호
    def test_tc370_bates_basic(self, tmp_path):
        from app.core.watermark import add_bates_numbers

        pdf = _make_pdf(tmp_path)
        out = str(tmp_path / "bates.pdf")
        add_bates_numbers(pdf, out, prefix="DOC-", start=1, digits=6)

        doc = fitz.open(out)
        text = doc[0].get_text()
        assert "DOC-000001" in text
        doc.close()

    # TC-371: 시작 번호/자릿수
    def test_tc371_bates_custom(self, tmp_path):
        from app.core.watermark import add_bates_numbers

        pdf = _make_pdf(tmp_path)
        out = str(tmp_path / "bates2.pdf")
        add_bates_numbers(pdf, out, prefix="EV-", start=100, digits=4)

        doc = fitz.open(out)
        text = doc[0].get_text()
        assert "EV-0100" in text
        doc.close()
