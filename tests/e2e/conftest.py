"""E2E 테스트 전용 픽스처."""

from __future__ import annotations

import fitz
import pytest
from PIL import Image


@pytest.fixture
def pdf_factory(tmp_path):
    """다양한 조건의 테스트 PDF를 생성하는 팩토리 픽스처.

    매개변수:
        num_pages: 페이지 수
        rotations: {page_idx: degrees} 회전 설정
        with_annotations: 기본 어노테이션 포함 여부
        page_texts: 각 페이지에 삽입할 텍스트 리스트
    """
    _counter = [0]

    def _create(
        num_pages: int = 3,
        *,
        rotations: dict[int, int] | None = None,
        with_annotations: bool = False,
        page_texts: list[str] | None = None,
    ) -> str:
        doc = fitz.open()
        for i in range(num_pages):
            page = doc.new_page(width=595, height=842)
            text = (page_texts[i] if page_texts and i < len(page_texts)
                    else f"Page {i + 1}")
            page.insert_text((72, 100), text, fontsize=24)

            if rotations and i in rotations:
                page.set_rotation(rotations[i])

            if with_annotations:
                page.draw_rect(fitz.Rect(50, 200, 200, 300), color=(1, 0, 0), width=2)

        _counter[0] += 1
        path = str(tmp_path / f"test_{num_pages}p_{_counter[0]}.pdf")
        doc.save(path)
        doc.close()
        return path

    return _create


@pytest.fixture
def image_factory(tmp_path):
    """테스트용 이미지 파일을 생성하는 팩토리."""

    def _create(
        name: str = "test.png",
        size: tuple[int, int] = (200, 150),
        color: tuple[int, int, int] = (100, 149, 237),
    ) -> str:
        path = str(tmp_path / name)
        Image.new("RGB", size, color=color).save(path)
        return path

    return _create
