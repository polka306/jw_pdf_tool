"""PdfViewer 위젯 테스트 (pytest-qt, offscreen 모드)."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt

from app.core.pdf_document import PdfDocument
from app.ui.pdf_viewer import PdfViewer


@pytest.fixture
def viewer(qtbot):
    """PdfViewer 인스턴스."""
    w = PdfViewer()
    qtbot.addWidget(w)
    return w


@pytest.fixture
def loaded_viewer(qtbot, pdf_3pages):
    """PDF가 로드된 PdfViewer."""
    doc = PdfDocument()
    doc.open(pdf_3pages)
    w = PdfViewer()
    qtbot.addWidget(w)
    w.set_document(doc)
    yield w, doc
    doc.close()


class TestPdfViewerInit:
    def test_initial_state(self, viewer):
        assert viewer.current_page == 0
        assert viewer.zoom == 1.5

    def test_clear_on_empty(self, viewer):
        viewer.clear()
        assert viewer.current_page == 0


class TestPdfViewerDocument:
    def test_set_document_shows_first_page(self, loaded_viewer):
        w, _ = loaded_viewer
        assert w.current_page == 0

    def test_goto_page_changes_current(self, loaded_viewer):
        w, _ = loaded_viewer
        w.goto_page(2)
        assert w.current_page == 2

    def test_goto_page_out_of_range_ignored(self, loaded_viewer):
        w, _ = loaded_viewer
        w.goto_page(0)
        w.goto_page(99)  # 범위 초과
        assert w.current_page == 0

    def test_page_changed_signal(self, loaded_viewer, qtbot):
        w, _ = loaded_viewer
        with qtbot.waitSignal(w.page_changed, timeout=1000) as blocker:
            w.goto_page(1)
        assert blocker.args == [1]


class TestPdfViewerZoom:
    def test_zoom_in_increases_zoom(self, loaded_viewer):
        w, _ = loaded_viewer
        before = w.zoom
        w.zoom_in()
        assert w.zoom > before

    def test_zoom_out_decreases_zoom(self, loaded_viewer):
        w, _ = loaded_viewer
        before = w.zoom
        w.zoom_out()
        assert w.zoom < before

    def test_zoom_clamped_to_min(self, loaded_viewer):
        w, _ = loaded_viewer
        w.set_zoom(0.001)
        assert w.zoom == PdfViewer.MIN_ZOOM

    def test_zoom_clamped_to_max(self, loaded_viewer):
        w, _ = loaded_viewer
        w.set_zoom(999.0)
        assert w.zoom == PdfViewer.MAX_ZOOM

    def test_zoom_changed_signal(self, loaded_viewer, qtbot):
        w, _ = loaded_viewer
        with qtbot.waitSignal(w.zoom_changed, timeout=1000):
            w.zoom_in()


class TestSceneToPdf:
    """_scene_to_pdf() 좌표 변환 정확도 테스트 (어노테이션 좌표 수정 검증)."""

    def test_origin_maps_to_origin_on_normal_page(self, loaded_viewer):
        """rotation=0 페이지에서 (0, 0) → (0, 0)이어야 합니다."""
        from PyQt6.QtCore import QPointF
        w, _ = loaded_viewer
        w.set_zoom(1.0)
        x, y = w._scene_to_pdf(QPointF(0, 0))
        assert x == pytest.approx(0.0)
        assert y == pytest.approx(0.0)

    def test_coord_scales_with_zoom_on_normal_page(self, loaded_viewer):
        """zoom=2.0 시 scene (200, 100) → pdf (100, 50)이어야 합니다."""
        from PyQt6.QtCore import QPointF
        w, _ = loaded_viewer
        w.set_zoom(2.0)
        x, y = w._scene_to_pdf(QPointF(200, 100))
        assert x == pytest.approx(100.0)
        assert y == pytest.approx(50.0)

    def test_coord_within_page_bounds_on_normal_page(self, loaded_viewer):
        """변환된 좌표가 페이지 MediaBox 안에 있어야 합니다."""
        from PyQt6.QtCore import QPointF
        import fitz
        w, doc = loaded_viewer
        w.set_zoom(1.0)
        page = doc.raw[0]
        pw, ph = page.rect.width, page.rect.height
        # 페이지 중앙 클릭 (scene 좌표 = pdf 좌표 when zoom=1, rotation=0)
        cx, cy = pw / 2, ph / 2
        x, y = w._scene_to_pdf(QPointF(cx, cy))
        assert 0 <= x <= pw
        assert 0 <= y <= ph

    def test_rotated_page_coord_within_bounds(self, qtbot, tmp_path):
        """/Rotate 90 페이지에서 변환된 좌표가 MediaBox 안에 있어야 합니다."""
        import fitz
        from PyQt6.QtCore import QPointF
        # /Rotate 90 PDF 생성
        path = str(tmp_path / "rotated.pdf")
        raw = fitz.open()
        page = raw.new_page(width=595, height=842)
        page.set_rotation(90)
        raw.save(path)
        raw.close()

        from app.core.pdf_document import PdfDocument
        doc = PdfDocument()
        doc.open(path)
        w = PdfViewer()
        qtbot.addWidget(w)
        w.set_document(doc)
        w.set_zoom(1.0)

        # 화면상 가운데 클릭 (display 기준)
        disp_page = doc.raw[0]
        # display rect (rotation 적용 후)
        drect = disp_page.rect
        cx, cy = drect.width / 2, drect.height / 2
        x, y = w._scene_to_pdf(QPointF(cx, cy))

        # 변환 결과가 원본 MediaBox 안에 있어야 함
        mbox = disp_page.mediabox
        assert mbox.x0 <= x <= mbox.x1
        assert mbox.y0 <= y <= mbox.y1
        doc.close()
