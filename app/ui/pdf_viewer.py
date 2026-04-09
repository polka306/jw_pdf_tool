"""PDF 미리보기 위젯 — QGraphicsView 기반.

Phase 3: 어노테이션 도구(텍스트/사각형/타원/선) 마우스 이벤트 처리 추가.
"""

from __future__ import annotations

from copy import copy

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

    zoom_changed          = pyqtSignal(float)   # 줌 비율 변경
    page_changed          = pyqtSignal(int)     # 페이지 변경 (0-based)
    annotation_added      = pyqtSignal()        # 어노테이션 추가됨 (호환용, main_window에서 emit)
    annotation_requested  = pyqtSignal(object, str)  # (annotate_fn, description) — Undo 지원

    MIN_ZOOM  = 0.25
    MAX_ZOOM  = 4.0
    ZOOM_STEP = 0.15

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._doc: PdfDocument | None = None
        self._current_page: int = 0
        self._zoom: float = 1.5

        # ── 비동기 렌더링 엔진 ────────────────────────────────────────────────
        self._render_engine = None
        self._zoom_debounce_timer = None
        self._last_pixmap: QPixmap | None = None  # 즉시 스케일용

        # ── 어노테이션 상태 ───────────────────────────────────────────────────
        self._current_tool: AnnotationTool = AnnotationTool.SELECT
        self._annot_style: AnnotationStyle = AnnotationStyle()
        self._drag_start: QPointF | None = None
        self._preview_item: QGraphicsItem | None = None

        self._view_mode: str = "single"  # "single", "continuous", "two_page"
        self._selected_text: str = ""

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # debounce 타이머 (줌 변경 시 150ms 후 정밀 렌더)
        from PyQt6.QtCore import QTimer
        self._zoom_debounce_timer = QTimer(self)
        self._zoom_debounce_timer.setSingleShot(True)
        self._zoom_debounce_timer.setInterval(150)
        self._zoom_debounce_timer.timeout.connect(self._on_debounce_render)

    # ── 공개 API ──────────────────────────────────────────────────────────────

    def set_document(self, doc: PdfDocument) -> None:
        self._doc = doc
        self._current_page = 0
        self.set_tool(AnnotationTool.SELECT)
        self._init_render_engine()
        self._render_current()

    def clear(self) -> None:
        if self._render_engine:
            self._render_engine.shutdown()
            self._render_engine = None
        self._doc = None
        self._current_page = 0
        self._last_pixmap = None
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
        old_zoom = self._zoom
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        self.zoom_changed.emit(self._zoom)

        # 즉시 스케일: 기존 pixmap을 확대/축소하여 표시 (빠름)
        if self._last_pixmap and old_zoom > 0:
            scale = self._zoom / old_zoom
            scaled = self._last_pixmap.scaled(
                int(self._last_pixmap.width() * scale),
                int(self._last_pixmap.height() * scale),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            self._scene.clear()
            self._preview_item = None
            self._scene.addPixmap(scaled)
            self._scene.setSceneRect(scaled.rect().toRectF())

        # debounce: 150ms 후 정밀 렌더
        if self._zoom_debounce_timer:
            self._zoom_debounce_timer.start()

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

    # ── 보기 모드 ─────────────────────────────────────────────────────────────

    @property
    def view_mode(self) -> str:
        return self._view_mode

    def set_view_mode(self, mode: str) -> None:
        """보기 모드 변경: "single", "continuous", "two_page"."""
        self._view_mode = mode
        self._render_current()

    # ── 텍스트 선택/복사 ──────────────────────────────────────────────────────

    def get_selected_text(self) -> str:
        """현재 선택된 텍스트 반환."""
        return self._selected_text

    def copy_selected_text(self) -> None:
        """선택된 텍스트를 클립보드에 복사."""
        from PyQt6.QtWidgets import QApplication
        if self._selected_text:
            QApplication.clipboard().setText(self._selected_text)

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
        """마우스 릴리즈 시 어노테이션 요청 시그널을 발생시킵니다.

        실제 PDF 수정은 main_window의 커맨드 매니저가 처리합니다 (Undo 지원).
        """
        if self._doc is None or not self._doc.is_open:
            return

        # 최소 크기 미만이면 무시 (실수 클릭 방지)
        if abs(start.x() - end.x()) < 3 and abs(start.y() - end.y()) < 3:
            return

        x1, y1 = self._scene_to_pdf(start)
        x2, y2 = self._scene_to_pdf(end)
        page_idx = self._current_page
        tool = self._current_tool
        style = copy(self._annot_style)  # 현재 스타일 스냅샷

        from app.core import annotator

        tool_labels = {
            AnnotationTool.RECT:    "사각형 추가",
            AnnotationTool.ELLIPSE: "타원 추가",
            AnnotationTool.LINE:    "선 추가",
        }

        def do_annotate() -> None:
            pg = self._doc.raw[page_idx]
            if tool == AnnotationTool.RECT:
                annotator.add_rect(pg, x1, y1, x2, y2, style)
            elif tool == AnnotationTool.ELLIPSE:
                annotator.add_ellipse(pg, x1, y1, x2, y2, style)
            elif tool == AnnotationTool.LINE:
                annotator.add_line(pg, x1, y1, x2, y2, style)

        self.annotation_requested.emit(do_annotate, tool_labels.get(tool, "어노테이션 추가"))

    def _handle_text_annotation(self, scene_pos: QPointF) -> None:
        """TEXT 도구: 클릭 위치에 텍스트 입력 다이얼로그를 표시합니다."""
        if self._doc is None or not self._doc.is_open:
            return

        text, ok = QInputDialog.getText(self, "텍스트 입력", "내용을 입력하세요:")
        if not ok or not text.strip():
            return

        x, y = self._scene_to_pdf(scene_pos)
        page_idx = self._current_page
        txt = text.strip()
        style = copy(self._annot_style)

        from app.core.annotator import add_text

        def do_annotate() -> None:
            add_text(self._doc.raw[page_idx], x, y, txt, style)

        self.annotation_requested.emit(do_annotate, "텍스트 추가")

    def refresh_page(self) -> None:
        """현재 페이지를 재렌더링합니다 (Undo/Redo 후 호출)."""
        # 세대 카운터 증가 → 캐시 무효화
        if self._doc and hasattr(self._doc, 'increment_generation'):
            self._doc.increment_generation(self._current_page)
            if self._render_engine:
                gen = self._doc.get_generation(self._current_page)
                self._render_engine.set_generation(self._current_page, gen)
        self._render_current()

    # ── 렌더링 ────────────────────────────────────────────────────────────────

    def _init_render_engine(self) -> None:
        """RenderEngine 초기화 또는 재초기화."""
        if self._doc is None or not self._doc.is_open or not self._doc.path:
            return
        try:
            from app.ui.render_engine import RenderEngine
            if self._render_engine:
                self._render_engine.shutdown()
            self._render_engine = RenderEngine()
            self._render_engine.load_document(self._doc.path)
            self._render_engine.render_complete.connect(self._on_async_render_done)
        except Exception:
            self._render_engine = None

    def _render_current(self) -> None:
        if self._doc is None or not self._doc.is_open:
            return

        # 비동기 엔진이 있으면 비동기 렌더 시도
        if self._render_engine:
            # 캐시 히트 확인
            cached = self._render_engine.get_cached(self._current_page, self._zoom)
            if cached:
                self._display_png(cached)
                # 프리페치도 요청
                self._render_engine.request_render(
                    self._current_page, self._zoom, prefetch=True
                )
                return

            # 캐시 미스 — 비동기 요청
            self._render_engine.request_render(
                self._current_page, self._zoom, prefetch=True, priority=True
            )

            # 즉시 표시할 게 없으면 동기 폴백 (첫 렌더 시)
            if self._last_pixmap is None:
                self._render_sync()
            return

        # 비동기 엔진 없음 → 동기 렌더
        self._render_sync()

    def _render_sync(self) -> None:
        """동기 렌더링 (폴백)."""
        if self._doc is None or not self._doc.is_open:
            return
        png_bytes = self._doc.render_page(self._current_page, zoom=self._zoom)
        self._display_png(png_bytes)

    def _display_png(self, png_bytes: bytes) -> None:
        """PNG 데이터를 화면에 표시."""
        pixmap = QPixmap.fromImage(QImage.fromData(png_bytes))
        self._last_pixmap = pixmap
        self._scene.clear()
        self._preview_item = None
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect().toRectF())

    def _on_async_render_done(self, page_idx: int, zoom: float, png_bytes: bytes) -> None:
        """비동기 렌더 완료 콜백."""
        # 현재 보고 있는 페이지/줌과 일치할 때만 표시
        if page_idx == self._current_page and abs(zoom - self._zoom) < 0.01:
            self._display_png(png_bytes)

    def _on_debounce_render(self) -> None:
        """줌 debounce 타이머 만료 → 정밀 렌더."""
        self._render_current()
