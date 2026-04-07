"""TC-245 ~ TC-249: 페이지 회전 단위 테스트."""

from __future__ import annotations

import fitz
import pytest


class TestPageRotation:
    """page_editor.py — 페이지 회전 테스트."""

    @pytest.fixture
    def doc5(self, pdf_5pages):
        doc = fitz.open(pdf_5pages)
        yield doc
        doc.close()

    # TC-245: 90° 시계방향 회전
    def test_tc245_rotate_90(self, doc5):
        from app.core.page_editor import rotate_page

        rotate_page(doc5, 0, 90)
        assert doc5[0].rotation == 90

    # TC-246: 180° 회전
    def test_tc246_rotate_180(self, doc5):
        from app.core.page_editor import rotate_page

        rotate_page(doc5, 0, 180)
        assert doc5[0].rotation == 180

    # TC-247: 270° 회전
    def test_tc247_rotate_270(self, doc5):
        from app.core.page_editor import rotate_page

        rotate_page(doc5, 0, 270)
        assert doc5[0].rotation == 270

    # TC-248: 이미 회전된 페이지에 추가 회전
    def test_tc248_cumulative_rotation(self, doc5):
        from app.core.page_editor import rotate_page

        rotate_page(doc5, 0, 90)
        rotate_page(doc5, 0, 90)
        assert doc5[0].rotation == 180

    # TC-249: Undo → 원래 rotation 복원
    def test_tc249_rotation_undo(self, doc5):
        from app.core.page_editor import rotate_page

        original = doc5[0].rotation
        rotate_page(doc5, 0, 90)
        assert doc5[0].rotation == (original + 90) % 360

        rotate_page(doc5, 0, -90)
        assert doc5[0].rotation == original
