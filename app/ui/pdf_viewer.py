"""PDF 미리보기 위젯 — QGraphicsView 기반."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QWheelEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView

from app.core.pdf_document import PdfDocument


class PdfViewer(QGraphicsView):
    """현재 페이지를 렌더링해 보여주는 뷰어 위젯.

    - Ctrl + 스크롤: 줌 인/아웃
    - 줌 범위: 25% ~ 400%
    """

    zoom_changed = pyqtSignal(float)  # 줌 비율 변경 시 emit (0.25 ~ 4.0)
    page_changed = pyqtSignal(int)    # 페이지 변경 시 emit (0-based index)

    MIN_ZOOM = 0.25
    MAX_ZOOM = 4.0
    ZOOM_STEP = 0.15  # 스크롤 한 번당 줌 변화량

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._doc: PdfDocument | None = None
        self._current_page: int = 0
        self._zoom: float = 1.5

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # 뷰어 기본 설정
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setRenderHint(self.renderHints())
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def set_document(self, doc: PdfDocument) -> None:
        """문서를 연결하고 첫 페이지를 표시합니다."""
        self._doc = doc
        self._current_page = 0
        self._render_current()

    def clear(self) -> None:
        """뷰어를 초기화합니다."""
        self._doc = None
        self._current_page = 0
        self._scene.clear()

    def goto_page(self, page_idx: int) -> None:
        """지정 페이지로 이동합니다."""
        if self._doc is None:
            return
        if not (0 <= page_idx < self._doc.page_count):
            return
        self._current_page = page_idx
        self._render_current()
        self.page_changed.emit(page_idx)

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_zoom(self, zoom: float) -> None:
        """줌 비율을 설정합니다 (0.25 ~ 4.0)."""
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        self._render_current()
        self.zoom_changed.emit(self._zoom)

    def zoom_in(self) -> None:
        self.set_zoom(self._zoom + self.ZOOM_STEP)

    def zoom_out(self) -> None:
        self.set_zoom(self._zoom - self.ZOOM_STEP)

    def zoom_fit(self) -> None:
        """뷰 크기에 맞게 줌을 조정합니다."""
        if self._doc is None:
            return
        w, h = self._doc.get_page_size(self._current_page)
        view_w = self.viewport().width() - 20
        view_h = self.viewport().height() - 20
        zoom = min(view_w / w, view_h / h)
        self.set_zoom(zoom)

    # ------------------------------------------------------------------
    # 이벤트
    # ------------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Ctrl + 스크롤로 줌, 일반 스크롤은 스크롤바."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    # ------------------------------------------------------------------
    # 내부 렌더링
    # ------------------------------------------------------------------

    def _render_current(self) -> None:
        """현재 페이지를 씬에 그립니다."""
        if self._doc is None or not self._doc.is_open:
            return

        png_bytes = self._doc.render_page(self._current_page, zoom=self._zoom)
        image = QImage.fromData(png_bytes)
        pixmap = QPixmap.fromImage(image)

        self._scene.clear()
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect().toRectF())
