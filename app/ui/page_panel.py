"""썸네일 패널 위젯 — 왼쪽 사이드바에 페이지 목록 표시."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QSizePolicy, QVBoxLayout, QWidget

from app.core.pdf_document import PdfDocument

THUMB_WIDTH = 120
ITEM_PADDING = 16  # 아이템 위아래 여백


class PagePanel(QWidget):
    """페이지 썸네일 리스트 패널.

    사용자가 썸네일을 클릭하면 page_selected 시그널이 emit됩니다.
    """

    page_selected = pyqtSignal(int)  # 선택된 페이지 인덱스 (0-based)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._doc: PdfDocument | None = None
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI 초기화
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 헤더 라벨
        header = QLabel("페이지")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(28)
        header.setStyleSheet(
            "background: #2d2d2d; color: #cccccc; font-size: 12px; border-bottom: 1px solid #444;"
        )
        layout.addWidget(header)

        # 썸네일 리스트
        self._list = QListWidget()
        self._list.setFixedWidth(THUMB_WIDTH + 24)
        self._list.setSpacing(4)
        self._list.setIconSize(self._list.iconSize())  # 기본값 유지, 아이템에서 설정
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
        layout.addWidget(self._list)

        self.setFixedWidth(THUMB_WIDTH + 24)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def load_document(self, doc: PdfDocument) -> None:
        """문서를 로드하고 모든 썸네일을 생성합니다."""
        self._doc = doc
        self._list.clear()

        for i in range(doc.page_count):
            item = self._make_item(i)
            self._list.addItem(item)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def clear(self) -> None:
        self._doc = None
        self._list.clear()

    def set_current_page(self, page_idx: int) -> None:
        """외부에서 현재 페이지를 설정합니다 (시그널 발생 없음)."""
        self._list.blockSignals(True)
        self._list.setCurrentRow(page_idx)
        self._list.blockSignals(False)

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _make_item(self, page_idx: int) -> QListWidgetItem:
        """썸네일 아이템을 생성합니다."""
        png_bytes = self._doc.render_page_thumbnail(page_idx, thumb_width=THUMB_WIDTH)
        image = QImage.fromData(png_bytes)
        pixmap = QPixmap.fromImage(image)

        item = QListWidgetItem()
        item.setIcon(self._pixmap_to_icon(pixmap))
        item.setText(f"{page_idx + 1}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        item.setSizeHint(self._list.sizeHint())
        return item

    @staticmethod
    def _pixmap_to_icon(pixmap: QPixmap):
        from PyQt6.QtGui import QIcon
        return QIcon(pixmap)

    def _on_row_changed(self, row: int) -> None:
        if row >= 0:
            self.page_selected.emit(row)
