"""TC-282: 열기→PDF→이미지 내보내기→이미지 확인."""

from __future__ import annotations

import os
import fitz
import pytest


class TestTC282ExportImages:

    def test_tc282_export_then_verify(self, tmp_path, pdf_3pages):
        from app.core.converter import export_pages_to_images

        out_dir = str(tmp_path / "exports")
        os.makedirs(out_dir)

        files = export_pages_to_images(pdf_3pages, out_dir, fmt="png", dpi=150)

        assert len(files) == 3
        for f in files:
            assert os.path.exists(f)
            assert os.path.getsize(f) > 1000  # 최소 1KB
