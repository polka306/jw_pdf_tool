"""PDF 미리보기 위젯 — QGraphicsView 기반.

Phase 3: 어노테이션 도구(텍스트/사각형/타원/선) 마우스 이벤트 처리 추가.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QImage,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QInputDialog,
)

import fitz  # PyMuPDF — derotation_matrix용

from app.core.annotator import AnnotationStyle, AnnotationTool
from app.core.pdf_document import PdfDocument


class PdfViewer(QGraphicsView):
    """현재 페이지를 렌더링해 보여주는 뷰어 위젯.

    - Ctrl + 스크롤: 줌 인/아웃 (25% ~ 400%)
    - 어노테이션 도구 선택 후 드래그: 도형/선 그리기
    - TEXT 도구 선택 후 클릭: 텍스트 입력 다이얼로그
    """

    zoom_changed       = pyqtSignal(float)   # 줌 비율 변경
    page_changed       = pyqtSignal(int)     # 페이지 변경 (0-based)
    annotation_added   = pyqtSignal()        # 어노테이션이 페이지에 추가됨

    MIN_ZOOM  = 0.25
    MAX_ZOOM  = 4.0
    ZOOM_STEP = 0.15

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._doc: PdfDocument | None = None
        self._current_page: int = 0
        self._zoom: float = 1.5

        # ── 어노테이션 상태 ───────────────────────────────────────────────────
        self._current_tool: AnnotationTool = AnnotationTool.SELECT
        self._annot_style: AnnotationStyle = AnnotationStyle()
        self._drag_start: QPointF | None = None
        self._preview_item: QGraphicsItem | None = None

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    # ── 공개 API ──────────────────────────────────────────────────────────────

    def set_document(self, doc: PdfDocument) -> None:
        self._doc = doc
        self._current_page = 0
        self.set_tool(AnnotationTool.SELECT)
        self._render_current()

    def clear(self) -> None:
        self._doc = None
        self._current_page = 0
        self._scene.clear()

    def goto_page(self, page_idx: int) -> None:
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

    # ── 줌 ───────────────────────────────────────────────────────────────────

    def set_zoom(self, zoom: float) -> None:
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        self._render_current()
        self.zoom_changed.emit(self._zoom)

    def zoom_in(self) -> None:
        self.set_zoom(self._zoom + self.ZOOM_STEP)

    def zoom_out(self) -> None:
        self.set_zoom(self._zoom - self.ZOOM_STEP)

    def zoom_fit(self) -> None:
        if self._doc is None:
            return
        w, h = self._doc.get_page_size(self._current_page)
        view_w = self.viewport().width() - 20
        view_h = self.viewport().height() - 20
        self.set_zoom(min(view_w / w, view_h / h))

    # ── 어노테이션 도구 ───────────────────────────────────────────────────────

    def set_tool(self, tool: AnnotationTool) -> None:
        """현재 어노테이션 도구를 변경합니다."""
        self._current_tool = tool
        self._remove_preview()
        self._drag_start = None

        if tool == AnnotationTool.SELECT:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            cursor = {
                AnnotationTool.TEXT:    Qt.CursorShape.IBeamCursor,
                AnnotationTool.RECT:    Qt.CursorShape.CrossCursor,
                AnnotationTool.ELLIPSE: Qt.CursorShape.CrossCursor,
                AnnotationTool.LINE:    Qt.CursorShape.CrossCursor,
            }.get(tool, Qt.CursorShape.CrossCursor)
            self.setCursor(cursor)

    def set_annotation_style(self, style: AnnotationStyle) -> None:
        self._annot_style = style

    @property
    def current_tool(self) -> AnnotationTool:
        return self._current_tool

    @property
    def annotation_style(self) -> AnnotationStyle:
        return self._annot_style

    # ── 마우스 이벤트 ─────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._current_tool == AnnotationTool.SELECT:
            super().mousePressEvent(event)
            return

        scene_pos = self.mapToScene(event.pos())

        if self._current_tool == AnnotationTool.TEXT:
            self._handle_text_annotation(scene_pos)
        else:
            self._drag_start = scene_pos
            self._remove_preview()
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._current_tool == AnnotationTool.SELECT or self._drag_start is None:
            super().mouseMoveEvent(event)
            return
        self._update_preview(self._drag_start, self.mapToScene(event.pos()))
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if (
            event.button() != Qt.MouseButton.LeftButton
            or self._current_tool == AnnotationTool.SELECT
            or self._drag_start is None
        ):
            super().mouseReleaseEvent(event)
            return

        end = self.mapToScene(event.pos())
        self._finalize_annotation(self._drag_start, end)
        self._drag_start = None
        self._remove_preview()
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    # ── 어노테이션 내부 처리 ──────────────────────────────────────────────────

    def _scene_to_pdf(self, pt: QPointF) -> tuple[float, float]:
        """Scene 좌표 → PyMuPDF 드로잉 좌표 변환.

        get_pixmap(Matrix(zoom,zoom))은 page 회전을 자동 적용한 screen 좌표로
        렌더링한다.  Shape API(draw_rect/insert_text 등)는 document 좌표계(page
        rotation 이전 MediaBox 기준, y 아래 방향)를 사용하므로
        page.derotation_matrix로 screen → document 변환이 필요하다.
        rotation=0인 페이지에서는 derotation_matrix가 항등행렬이므로
        단순 /zoom 과 동일하다.
        """
        screen_x = pt.x() / self._zoom
        screen_y = pt.y() / self._zoom
        if self._doc is None or not self._doc.is_open:
            return screen_x, screen_y
        page = self._doc.raw[self._current_page]
        doc_pt = fitz.Point(screen_x, screen_y) * page.derotation_matrix
        return doc_pt.x, doc_pt.y

    def _make_pen(self) -> QPen:
        r, g, b = self._annot_style.color
        pen = QPen(QColor(int(r * 255), int(g * 255), int(b * 255)))
        pen.setWidthF(self._annot_style.line_width * self._zoom)
        return pen

    def _update_preview(self, start: QPointF, end: QPointF) -> None:
        """드래그 중 임시 미리보기 아이템을 씬에 추가합니다."""
        self._remove_preview()
        pen = self._make_pen()

        tool = self._current_tool
        if tool == AnnotationTool.RECT:
            from PyQt6.QtCore import QRectF
            item = QGraphicsRectItem(QRectF(start, end).normalized())
            item.setPen(pen)
        elif tool == AnnotationTool.ELLIPSE:
            from PyQt6.QtCore import QRectF
            item = QGraphicsEllipseItem(QRectF(start, end).normalized())
            item.setPen(pen)
        elif tool == AnnotationTool.LINE:
            item = QGraphicsLineItem(start.x(), start.y(), end.x(), end.y())
            item.setPen(pen)
        else:
            return

        item.setOpacity(0.7)
        self._scene.addItem(item)
        self._preview_item = item

    def _remove_preview(self) -> None:
        if self._preview_item is not None:
            self._scene.removeItem(self._preview_item)
            self._preview_item = None

    def _finalize_annotation(self, start: QPointF, end: QPointF) -> None:
        """마우스 릴리즈 시 실제 어노테이션을 PDF 페이지에 기록합니다."""
        if self._doc is None or not self._doc.is_open:
            return

        # 최소 크기 미만이면 무시 (실수 클릭 방지)
        if abs(start.x() - end.x()) < 3 and abs(start.y() - end.y()) < 3:
            return

        x1, y1 = self._scene_to_pdf(start)
        x2, y2 = self._scene_to_pdf(end)
        page = self._doc.raw[self._current_page]

        from app.core import annotator
        tool = self._current_tool
        style = self._annot_style

        if tool == AnnotationTool.RECT:
            annotator.add_rect(page, x1, y1, x2, y2, style)
        elif tool == AnnotationTool.ELLIPSE:
            annotator.add_ellipse(page, x1, y1, x2, y2, style)
        elif tool == AnnotationTool.LINE:
            annotator.add_line(page, x1, y1, x2, y2, style)

        self._render_current()
        self.annotation_added.emit()

    def _handle_text_annotation(self, scene_pos: QPointF) -> None:
        """TEXT 도구: 클릭 위치에 텍스트 입력 다이얼로그를 표시합니다."""
        if self._doc is None or not self._doc.is_open:
            return

        text, ok = QInputDialog.getText(self, "텍스트 입력", "내용을 입력하세요:")
        if not ok or not text.strip():
            return

        x, y = self._scene_to_pdf(scene_pos)
        page = self._doc.raw[self._current_page]

        from app.core.annotator import add_text
        add_text(page, x, y, text.strip(), self._annot_style)

        self._render_current()
        self.annotation_added.emit()

    # ── 렌더링 ────────────────────────────────────────────────────────────────

    def _render_current(self) -> None:
        if self._doc is None or not self._doc.is_open:
            return
        png_bytes = self._doc.render_page(self._current_page, zoom=self._zoom)
        pixmap = QPixmap.fromImage(QImage.fromData(png_bytes))
        self._scene.clear()
        self._preview_item = None  # clear() 로 이미 제거됨
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect().toRectF())
