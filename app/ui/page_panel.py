"""썸네일 패널 위젯 — 드래그앤드롭 순서변경, 다중선택, 컨텍스트 메뉴 포함."""

from __future__ import annotations

from PyQt6.QtCore import QModelIndex, QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.pdf_document import PdfDocument

THUMB_WIDTH = 120


# ── 백그라운드 썸네일 로더 ─────────────────────────────────────────────────────

class _ThumbnailLoader(QThread):
    """파일을 독립적으로 열어 썸네일을 백그라운드에서 순차 생성합니다.

    메인 스레드의 PdfDocument와 별도 fitz.Document를 사용하므로 스레드 안전.
    """

    thumbnail_ready = pyqtSignal(int, bytes)   # (page_idx, png_bytes)

    def __init__(self, path: str, page_count: int, thumb_width: int, parent=None):
        super().__init__(parent)
        self._path = path
        self._page_count = page_count
        self._thumb_width = thumb_width
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        import fitz
        try:
            doc = fitz.open(self._path)
        except Exception:
            return
        for i in range(self._page_count):
            if self._cancelled:
                break
            try:
                page = doc[i]
                zoom = self._thumb_width / page.rect.width
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                self.thumbnail_ready.emit(i, pix.tobytes("png"))
            except Exception:
                pass
        doc.close()


# ── 드래그앤드롭 리스트 ────────────────────────────────────────────────────────

class _DraggableList(QListWidget):
    """드래그앤드롭으로 페이지 순서를 변경할 수 있는 리스트 위젯.

    항목을 드래그해서 놓으면 page_moved(from_idx, to_idx) 시그널을 emit합니다.
    """

    page_moved = pyqtSignal(int, int)  # (from_idx, to_idx)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._drag_row = -1

    def mousePressEvent(self, event) -> None:
        item = self.itemAt(event.pos())
        self._drag_row = self.row(item) if item else -1
        super().mousePressEvent(event)

    def dropEvent(self, event) -> None:
        # PyQt6: QDropEvent.pos() 제거됨 → position().toPoint() 사용
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)
        drop_row = self.row(target_item) if target_item else self.count() - 1

        from_row = self._drag_row
        super().dropEvent(event)

        # 실제 이동된 위치 = 드롭 후 현재 선택된 행
        to_row = self.currentRow()
        if from_row >= 0 and from_row != to_row:
            self.page_moved.emit(from_row, to_row)


# ── 페이지 패널 ────────────────────────────────────────────────────────────────

class PagePanel(QWidget):
    """페이지 썸네일 패널.

    시그널:
        page_selected(int)      — 썸네일 단일 클릭 시 이동할 페이지 인덱스
        page_moved(int, int)    — 드래그앤드롭으로 순서 변경 (from, to)
        delete_requested(list)  — 선택 페이지 삭제 요청 (인덱스 목록)
        extract_requested(list) — 선택 페이지 추출 요청 (인덱스 목록)
        insert_requested(int)   — 페이지 삽입 요청 (삽입 위치, 0-based)
    """

    page_selected = pyqtSignal(int)
    page_moved = pyqtSignal(int, int)
    delete_requested = pyqtSignal(list)
    extract_requested = pyqtSignal(list)
    insert_requested = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._doc: PdfDocument | None = None
        self._loader: _ThumbnailLoader | None = None
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI 초기화
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("페이지")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(28)
        header.setStyleSheet(
            "background:#2d2d2d; color:#cccccc; font-size:12px; border-bottom:1px solid #444;"
        )
        layout.addWidget(header)

        self._list = _DraggableList()
        self._list.setFixedWidth(THUMB_WIDTH + 24)
        self._list.setIconSize(QSize(THUMB_WIDTH, int(THUMB_WIDTH * 1.5)))  # A4 세로 비율 기준 최대치
        self._list.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._list.setStyleSheet(
            """
            QListWidget {
                background: #1e1e1e;
                border: none;
            }
            QListWidget::item {
                color: #cccccc;
                padding: 6px 4px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background: #0e5a8a;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background: #2a4a5e;
            }
            """
        )
        self._list.currentRowChanged.connect(self._on_row_changed)
        self._list.page_moved.connect(self.page_moved)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._list)

        self.setFixedWidth(THUMB_WIDTH + 24)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def load_document(self, doc: PdfDocument) -> None:
        """문서를 로드합니다. 썸네일은 백그라운드에서 순차 생성됩니다."""
        self._doc = doc
        self._cancel_loader()

        # placeholder 아이템 즉시 추가 (빠른 응답)
        self._list.blockSignals(True)
        self._list.clear()
        ph_size = QSize(THUMB_WIDTH + 8, int(THUMB_WIDTH * 1.5) + 22)
        for i in range(doc.page_count):
            item = QListWidgetItem()
            item.setText(f"{i + 1}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            item.setSizeHint(ph_size)
            self._list.addItem(item)
        self._list.blockSignals(False)
        self._list.setCurrentRow(0)

        # 백그라운드 로더 시작
        if doc.path:
            self._loader = _ThumbnailLoader(doc.path, doc.page_count, THUMB_WIDTH, self)
            self._loader.thumbnail_ready.connect(self._on_thumbnail_ready)
            self._loader.start()

    def reload_all(self) -> None:
        """모든 썸네일을 새로 렌더링합니다 (페이지 편집 후 사용).

        진행 중인 백그라운드 로더를 취소하고 동기 렌더링합니다.
        UI 응답성을 위해 각 썸네일 렌더링 후 이벤트를 처리합니다.
        """
        if self._doc is None:
            return
        self._cancel_loader()
        current = self._list.currentRow()
        self._list.blockSignals(True)
        self._list.clear()
        for i in range(self._doc.page_count):
            self._list.addItem(self._make_item(i))
            QApplication.processEvents()  # UI 응답 유지
        self._list.blockSignals(False)
        target = min(current, self._doc.page_count - 1)
        self._list.setCurrentRow(max(0, target))

    def reload_page(self, page_idx: int) -> None:
        """특정 페이지 썸네일만 갱신합니다 (어노테이션 추가 후 사용)."""
        if self._doc is None:
            return
        item = self._list.item(page_idx)
        if item is None:
            return
        png_bytes = self._doc.render_page_thumbnail(page_idx, thumb_width=THUMB_WIDTH)
        pixmap = QPixmap.fromImage(QImage.fromData(png_bytes))
        item.setIcon(QIcon(pixmap))
        item.setSizeHint(QSize(THUMB_WIDTH + 8, pixmap.height() + 22))

    def clear(self) -> None:
        self._cancel_loader()
        self._doc = None
        self._list.clear()

    def set_current_page(self, page_idx: int) -> None:
        """외부에서 현재 페이지를 설정합니다 (시그널 없음)."""
        self._list.blockSignals(True)
        self._list.setCurrentRow(page_idx)
        self._list.blockSignals(False)

    def selected_indices(self) -> list[int]:
        """현재 선택된 페이지 인덱스 목록을 반환합니다."""
        return sorted(self._list.row(item) for item in self._list.selectedItems())

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _cancel_loader(self) -> None:
        if self._loader is not None:
            self._loader.cancel()
            self._loader.wait()
            self._loader = None

    def _on_thumbnail_ready(self, idx: int, png_bytes: bytes) -> None:
        item = self._list.item(idx)
        if item is None:
            return
        pixmap = QPixmap.fromImage(QImage.fromData(png_bytes))
        item.setIcon(QIcon(pixmap))
        item.setSizeHint(QSize(THUMB_WIDTH + 8, pixmap.height() + 22))

    def _make_item(self, page_idx: int) -> QListWidgetItem:
        png_bytes = self._doc.render_page_thumbnail(page_idx, thumb_width=THUMB_WIDTH)
        pixmap = QPixmap.fromImage(QImage.fromData(png_bytes))
        item = QListWidgetItem()
        item.setIcon(QIcon(pixmap))
        item.setText(f"{page_idx + 1}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        item.setSizeHint(QSize(THUMB_WIDTH + 8, pixmap.height() + 22))
        return item

    def _on_row_changed(self, row: int) -> None:
        if row >= 0:
            self.page_selected.emit(row)

    def _show_context_menu(self, pos) -> None:
        indices = self.selected_indices()
        if not indices:
            return

        menu = QMenu(self)
        act_delete = menu.addAction("선택 페이지 삭제")
        act_extract = menu.addAction("선택 페이지 추출...")
        menu.addSeparator()
        act_insert_before = menu.addAction("이 위치 앞에 페이지 삽입...")
        act_insert_end = menu.addAction("맨 끝에 페이지 삽입...")

        act = menu.exec(self._list.mapToGlobal(pos))

        if act == act_delete:
            self.delete_requested.emit(indices)
        elif act == act_extract:
            self.extract_requested.emit(indices)
        elif act == act_insert_before:
            insert_at = indices[0]  # 선택 중 가장 앞 페이지 앞에 삽입
            self.insert_requested.emit(insert_at)
        elif act == act_insert_end:
            self.insert_requested.emit(self._doc.page_count if self._doc else 0)
