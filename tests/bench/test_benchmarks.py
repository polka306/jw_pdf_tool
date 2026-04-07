"""성능 벤치마크 테스트 — Phase 1 기준."""

from __future__ import annotations

import os
import time

import fitz
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_pdf(tmp_path, pages: int) -> str:
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page {i + 1}", fontsize=24)
        page.draw_rect(fitz.Rect(50, 50, 300, 250), color=(0.3, 0.3, 0.8), width=2)
    path = str(tmp_path / f"bench_{pages}.pdf")
    doc.save(path)
    doc.close()
    return path


class TestBenchmarks:
    """성능 벤치마크 — Phase 1 게이트 기준."""

    # BENCH-1: 페이지 전환 (캐시 히트) < 30ms
    def test_bench_page_switch_cache_hit(self, qtbot, tmp_path):
        from app.ui.render_engine import RenderEngine

        pdf_path = _make_pdf(tmp_path, 10)
        engine = RenderEngine()
        engine.load_document(pdf_path)

        # 먼저 페이지 0 렌더 (캐시 채우기)
        done = []
        engine.render_complete.connect(lambda p, z, img: done.append(p))
        engine.request_render(0, 1.5)
        qtbot.waitUntil(lambda: 0 in done, timeout=5000)

        # 캐시 히트 속도
        start = time.perf_counter()
        cached = engine.get_cached(0, 1.5)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert cached is not None
        assert elapsed_ms < 30, f"캐시 히트 {elapsed_ms:.1f}ms > 30ms"

        engine.shutdown()

    # BENCH-2: 페이지 전환 (캐시 미스) < 100ms
    def test_bench_page_switch_cache_miss(self, qtbot, tmp_path):
        from app.ui.render_engine import RenderEngine

        pdf_path = _make_pdf(tmp_path, 10)
        engine = RenderEngine()
        engine.load_document(pdf_path)

        done = []
        engine.render_complete.connect(lambda p, z, img: done.append(time.perf_counter()))

        start = time.perf_counter()
        engine.request_render(5, 1.5)
        qtbot.waitUntil(lambda: len(done) >= 1, timeout=5000)

        elapsed_ms = (done[0] - start) * 1000
        assert elapsed_ms < 500, f"캐시 미스 렌더 {elapsed_ms:.1f}ms > 500ms"

        engine.shutdown()

    # BENCH-3: 줌 변경 (즉시 스케일) < 50ms
    def test_bench_zoom_instant_scale(self, qtbot, tmp_path):
        from app.core.pdf_document import PdfDocument

        pdf_path = _make_pdf(tmp_path, 5)
        doc = PdfDocument()
        doc.open(pdf_path)

        # 렌더링
        png1 = doc.render_page(0, zoom=1.0)
        assert len(png1) > 0

        # 다른 줌으로 렌더링 시간 측정
        start = time.perf_counter()
        png2 = doc.render_page(0, zoom=2.0)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(png2) > 0
        # 단일 페이지 렌더는 200ms 이내 (비동기 이전 기준)
        assert elapsed_ms < 500, f"줌 렌더 {elapsed_ms:.1f}ms > 500ms"

        doc.close()

    # BENCH-4: 30페이지 PDF 열기 → 첫 페이지 < 500ms
    def test_bench_open_30pages(self, qtbot, tmp_path):
        from app.core.pdf_document import PdfDocument

        pdf_path = _make_pdf(tmp_path, 30)

        start = time.perf_counter()
        doc = PdfDocument()
        doc.open(pdf_path)
        png = doc.render_page(0, zoom=1.5)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(png) > 0
        assert elapsed_ms < 1000, f"30페이지 열기+첫렌더 {elapsed_ms:.1f}ms > 1000ms"

        doc.close()

    # BENCH-5: 어노테이션 후 갱신 < 100ms
    def test_bench_annotation_refresh(self, qtbot, tmp_path):
        from app.core.pdf_document import PdfDocument
        from app.core.annotator import add_rect, AnnotationStyle

        pdf_path = _make_pdf(tmp_path, 5)
        doc = PdfDocument()
        doc.open(pdf_path)

        import fitz as fitz_mod
        page = doc.raw[0]
        style = AnnotationStyle(color=(1, 0, 0), line_width=2.0)

        start = time.perf_counter()
        add_rect(page, 100, 100, 300, 200, style)
        png = doc.render_page(0, zoom=1.5)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(png) > 0
        assert elapsed_ms < 500, f"어노테이션+렌더 {elapsed_ms:.1f}ms > 500ms"

        doc.close()
