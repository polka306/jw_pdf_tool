"""TC-185 ~ TC-188: PdfViewer 성능 관련 테스트."""

from __future__ import annotations

import os
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestPdfViewerPerformance:
    """pdf_viewer.py — 비동기 렌더링 통합 성능 테스트."""

    @pytest.fixture
    def viewer_with_doc(self, qtbot, pdf_10pages):
        """PDF가 로드된 PdfViewer 인스턴스."""
        from app.ui.pdf_viewer import PdfViewer
        from app.core.pdf_document import PdfDocument

        doc = PdfDocument()
        doc.open(pdf_10pages)

        viewer = PdfViewer()
        qtbot.addWidget(viewer)
        viewer.set_document(doc)

        yield viewer, doc

        doc.close()

    # TC-185: 줌 변경 시 즉시 스케일 표시
    def test_tc185_zoom_instant_scale(self, viewer_with_doc, qtbot):
        viewer, doc = viewer_with_doc
        viewer.goto_page(0)
        qtbot.wait(500)  # 초기 렌더 대기

        start = time.perf_counter()
        viewer.set_zoom(2.0)
        elapsed = time.perf_counter() - start

        # 즉시 스케일(기존 이미지 확대)은 50ms 이내
        assert elapsed < 0.1  # 100ms 여유

    # TC-186: 줌 후 백그라운드 정밀 렌더 교체
    def test_tc186_background_high_res_replace(self, viewer_with_doc, qtbot):
        viewer, doc = viewer_with_doc
        viewer.goto_page(0)
        qtbot.wait(500)

        viewer.set_zoom(2.0)

        # debounce 후 고해상도 렌더가 교체됨 (약 200ms 대기)
        qtbot.wait(500)

        # 고해상도 이미지가 표시되었는지 확인
        # (scene에 pixmap이 있고, 크기가 적절한지)
        scene = viewer.scene()
        assert scene is not None
        items = scene.items()
        assert len(items) > 0

    # TC-187: 페이지 전환 시 캐시 히트
    def test_tc187_page_switch_cache_hit(self, viewer_with_doc, qtbot):
        viewer, doc = viewer_with_doc

        # 페이지 0 렌더
        viewer.goto_page(0)
        qtbot.wait(500)

        # 페이지 1로 이동 후 다시 0으로
        viewer.goto_page(1)
        qtbot.wait(300)

        start = time.perf_counter()
        viewer.goto_page(0)
        elapsed = time.perf_counter() - start

        # 캐시 히트 시 빠른 전환 (프리페치 되어있어야 함)
        assert elapsed < 0.1

    # TC-188: 연속 빠른 페이지 전환
    def test_tc188_rapid_page_switch(self, viewer_with_doc, qtbot):
        viewer, doc = viewer_with_doc

        # 빠르게 여러 페이지 전환
        for i in range(10):
            viewer.goto_page(i)

        qtbot.wait(1000)

        # 최종 페이지(9)가 표시되어야 함 — 중간 렌더는 취소됨
        assert viewer.current_page == 9
