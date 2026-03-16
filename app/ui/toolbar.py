"""툴바 위젯."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QLabel, QSpinBox, QToolBar, QWidget


class MainToolBar(QToolBar):
    """메인 윈도우 툴바.

    Phase 1: 파일 열기/저장, 줌 컨트롤
    Phase 2: 페이지 삭제/추출/삽입
    Phase 3에서 어노테이션 도구 버튼 추가 예정.
    """

    # 파일 작업
    open_requested = pyqtSignal()
    save_requested = pyqtSignal()

    # 줌
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    zoom_fit_requested = pyqtSignal()
    zoom_value_changed = pyqtSignal(float)

    # 페이지 편집
    delete_page_requested = pyqtSignal()
    extract_page_requested = pyqtSignal()
    insert_page_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__("메인 툴바", parent)
        self.setMovable(False)
        self._setup_actions()

    # ------------------------------------------------------------------
    # UI 구성
    # ------------------------------------------------------------------

    def _setup_actions(self) -> None:
        # --- 파일 그룹 ---
        self._act_open = QAction("열기", self)
        self._act_open.setShortcut(QKeySequence.StandardKey.Open)
        self._act_open.setToolTip("PDF 파일 열기 (Ctrl+O)")
        self._act_open.triggered.connect(self.open_requested)
        self.addAction(self._act_open)

        self._act_save = QAction("저장", self)
        self._act_save.setShortcut(QKeySequence.StandardKey.Save)
        self._act_save.setToolTip("저장 (Ctrl+S)")
        self._act_save.setEnabled(False)
        self._act_save.triggered.connect(self.save_requested)
        self.addAction(self._act_save)

        self.addSeparator()

        # --- 페이지 편집 그룹 ---
        self._act_delete = QAction("페이지 삭제", self)
        self._act_delete.setShortcut(QKeySequence("Delete"))
        self._act_delete.setToolTip("선택한 페이지 삭제 (Delete)")
        self._act_delete.setEnabled(False)
        self._act_delete.triggered.connect(self.delete_page_requested)
        self.addAction(self._act_delete)

        self._act_extract = QAction("페이지 추출", self)
        self._act_extract.setToolTip("선택한 페이지를 새 PDF로 추출")
        self._act_extract.setEnabled(False)
        self._act_extract.triggered.connect(self.extract_page_requested)
        self.addAction(self._act_extract)

        self._act_insert = QAction("페이지 삽입", self)
        self._act_insert.setToolTip("다른 PDF에서 페이지 삽입")
        self._act_insert.setEnabled(False)
        self._act_insert.triggered.connect(self.insert_page_requested)
        self.addAction(self._act_insert)

        self.addSeparator()

        # --- 줌 그룹 ---
        self.addWidget(QLabel("  줌:"))

        self._act_zoom_out = QAction("－", self)
        self._act_zoom_out.setToolTip("줌 아웃 (Ctrl+-)")
        self._act_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        self._act_zoom_out.setEnabled(False)
        self._act_zoom_out.triggered.connect(self.zoom_out_requested)
        self.addAction(self._act_zoom_out)

        self._zoom_spin = QSpinBox()
        self._zoom_spin.setRange(25, 400)
        self._zoom_spin.setValue(150)
        self._zoom_spin.setSuffix("%")
        self._zoom_spin.setFixedWidth(72)
        self._zoom_spin.setEnabled(False)
        self._zoom_spin.valueChanged.connect(
            lambda v: self.zoom_value_changed.emit(v / 100.0)
        )
        self.addWidget(self._zoom_spin)

        self._act_zoom_in = QAction("＋", self)
        self._act_zoom_in.setToolTip("줌 인 (Ctrl+=)")
        self._act_zoom_in.setShortcut(QKeySequence("Ctrl+="))
        self._act_zoom_in.setEnabled(False)
        self._act_zoom_in.triggered.connect(self.zoom_in_requested)
        self.addAction(self._act_zoom_in)

        self._act_zoom_fit = QAction("맞춤", self)
        self._act_zoom_fit.setToolTip("화면에 맞게 (Ctrl+0)")
        self._act_zoom_fit.setShortcut(QKeySequence("Ctrl+0"))
        self._act_zoom_fit.setEnabled(False)
        self._act_zoom_fit.triggered.connect(self.zoom_fit_requested)
        self.addAction(self._act_zoom_fit)

        spacer = QWidget()
        spacer.setFixedWidth(8)
        self.addWidget(spacer)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def set_document_loaded(self, loaded: bool) -> None:
        """문서 로드 여부에 따라 액션 활성/비활성."""
        self._act_save.setEnabled(loaded)
        self._act_delete.setEnabled(loaded)
        self._act_extract.setEnabled(loaded)
        self._act_insert.setEnabled(loaded)
        self._act_zoom_in.setEnabled(loaded)
        self._act_zoom_out.setEnabled(loaded)
        self._act_zoom_fit.setEnabled(loaded)
        self._zoom_spin.setEnabled(loaded)

    def update_zoom_display(self, zoom: float) -> None:
        """뷰어 줌 변경 시 스핀박스를 동기화합니다."""
        self._zoom_spin.blockSignals(True)
        self._zoom_spin.setValue(round(zoom * 100))
        self._zoom_spin.blockSignals(False)
