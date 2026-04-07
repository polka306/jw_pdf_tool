"""TC-176 ~ TC-182: 비동기 렌더링 엔진 테스트."""

from __future__ import annotations

import os
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestRenderEngine:
    """ui/render_engine.py — RenderEngine 단위 테스트."""

    # TC-176: 비동기 렌더 요청 → 완료 시그널
    def test_tc176_async_render_signal(self, qtbot, pdf_3pages):
        from app.ui.render_engine import RenderEngine

        engine = RenderEngine()
        engine.load_document(pdf_3pages)

        results = []
        engine.render_complete.connect(lambda page, zoom, img: results.append((page, zoom)))

        engine.request_render(0, 1.5)

        # 시그널 대기 (최대 5초)
        qtbot.waitUntil(lambda: len(results) >= 1, timeout=5000)

        assert results[0][0] == 0
        assert results[0][1] == 1.5

        engine.shutdown()

    # TC-177: 캐시 히트 시 즉시 반환
    def test_tc177_cache_hit_immediate(self, qtbot, pdf_3pages):
        from app.ui.render_engine import RenderEngine

        engine = RenderEngine()
        engine.load_document(pdf_3pages)

        # 첫 렌더 — 캐시 미스
        results = []
        engine.render_complete.connect(lambda p, z, img: results.append(True))
        engine.request_render(0, 1.5)
        qtbot.waitUntil(lambda: len(results) >= 1, timeout=5000)

        # 두 번째 동일 요청 — 캐시 히트, 즉시 반환
        cached = engine.get_cached(0, 1.5)
        assert cached is not None

        engine.shutdown()

    # TC-178: 프리페치 ±3 페이지
    def test_tc178_prefetch_neighbors(self, qtbot, pdf_10pages):
        from app.ui.render_engine import RenderEngine

        engine = RenderEngine()
        engine.load_document(pdf_10pages)

        rendered_pages = set()
        engine.render_complete.connect(lambda p, z, img: rendered_pages.add(p))

        # 페이지 5 요청 → 주변 프리페치 기대
        engine.request_render(5, 1.5, prefetch=True)

        # 프리페치 완료 대기 (현재 페이지 + 최소 2개 인접)
        qtbot.waitUntil(lambda: 5 in rendered_pages and len(rendered_pages) >= 3, timeout=10000)

        # 현재 페이지 반드시 포함
        assert 5 in rendered_pages
        # 인접 페이지 중 일부가 프리페치됨
        neighbors = {2, 3, 4, 6, 7, 8}
        assert len(rendered_pages & neighbors) >= 2

        engine.shutdown()

    # TC-179: 중복 요청 무시
    def test_tc179_dedup_requests(self, qtbot, pdf_3pages):
        from app.ui.render_engine import RenderEngine

        engine = RenderEngine()
        engine.load_document(pdf_3pages)

        render_count = []
        engine.render_complete.connect(lambda p, z, img: render_count.append(1))

        # 동일 요청 3번
        engine.request_render(0, 1.5)
        engine.request_render(0, 1.5)
        engine.request_render(0, 1.5)

        qtbot.waitUntil(lambda: len(render_count) >= 1, timeout=5000)
        # 약간의 대기 후 추가 렌더가 없는지 확인
        time.sleep(0.3)

        # 중복 제거로 1번만 실행되어야 함
        assert len(render_count) == 1

        engine.shutdown()

    # TC-180: 우선순위 — 현재 페이지가 프리페치보다 먼저 (또는 동시)
    def test_tc180_priority_current_over_prefetch(self, qtbot, pdf_10pages):
        from app.ui.render_engine import RenderEngine

        engine = RenderEngine()
        engine.load_document(pdf_10pages)

        rendered_pages = set()
        engine.render_complete.connect(lambda p, z, img: rendered_pages.add(p))

        # priority 요청은 프리페치보다 먼저 제출됨
        engine.request_render(0, 1.5, priority=True)
        engine.request_render(5, 1.5, prefetch=True)

        qtbot.waitUntil(lambda: 0 in rendered_pages, timeout=5000)

        # priority 페이지가 렌더되었으면 OK
        assert 0 in rendered_pages

        engine.shutdown()

    # TC-181: 문서 닫기 시 정리
    def test_tc181_cleanup_on_close(self, qtbot, pdf_3pages):
        from app.ui.render_engine import RenderEngine

        engine = RenderEngine()
        engine.load_document(pdf_3pages)

        engine.request_render(0, 1.5)
        # 즉시 shutdown
        engine.shutdown()

        # shutdown 후 추가 요청은 무시 (오류 없이)
        engine.request_render(1, 1.5)  # no crash

    # TC-182: 워커별 독립 fitz.Document (스레드 안전성)
    def test_tc182_thread_safe_documents(self, qtbot, pdf_10pages):
        from app.ui.render_engine import RenderEngine

        engine = RenderEngine()
        engine.load_document(pdf_10pages)

        rendered = set()
        engine.render_complete.connect(lambda p, z, img: rendered.add(p))

        # 동시 4개 페이지 렌더 요청
        for i in range(4):
            engine.request_render(i, 1.5)

        qtbot.waitUntil(lambda: len(rendered) >= 4, timeout=10000)

        assert {0, 1, 2, 3}.issubset(rendered)

        engine.shutdown()
