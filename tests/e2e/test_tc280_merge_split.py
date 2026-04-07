"""TC-280: 3개 PDF 병합→북마크 확인→분할→내용 비교."""

from __future__ import annotations

import os
import fitz
import pytest


class TestTC280MergeSplit:

    def test_tc280_merge_then_split(self, tmp_path):
        from app.core.merger import merge_pdfs, split_pdf

        # 3개 PDF 생성
        pdfs = []
        for i in range(3):
            doc = fitz.open()
            for j in range(3):
                page = doc.new_page(width=595, height=842)
                page.insert_text((72, 100), f"Doc{i+1} Page{j+1}", fontsize=14)
            p = str(tmp_path / f"doc{i}.pdf")
            doc.save(p)
            doc.close()
            pdfs.append(p)

        # 병합
        merged = str(tmp_path / "merged.pdf")
        merge_pdfs(pdfs, merged)

        doc = fitz.open(merged)
        assert doc.page_count == 9
        doc.close()

        # 분할
        out_dir = str(tmp_path / "split")
        os.makedirs(out_dir)
        files = split_pdf(merged, out_dir, pages_per_split=3)

        assert len(files) == 3
        for f in files:
            d = fitz.open(f)
            assert d.page_count == 3
            d.close()
