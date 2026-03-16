"""툴바 위젯."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QColor, QIcon, QKeySequence, QPixmap
from PyQt6.QtWidgets import (
    QColorDialog,
    QDoubleSpinBox,
    QLabel,
    QSpinBox,
    QToolBar,
    QWidget,
)

from app.core.annotator import AnnotationTool


class MainToolBar(QToolBar):
    """메인 윈도우 툴바."""

    # 파일
    open_requested  = pyqtSignal()
    save_requested  = pyqtSignal()

    # 줌
    zoom_in_requested   = pyqtSignal()
    zoom_out_requested  = pyqtSignal()
    zoom_fit_requested  = pyqtSignal()
    zoom_value_changed  = pyqtSignal(float)

    # 페이지 편집
    delete_page_requested  = pyqtSignal()
    extract_page_requested = pyqtSignal()
    insert_page_requested  = pyqtSignal()

    # 어노테이션
    tool_changed   = pyqtSignal(AnnotationTool)
    color_changed  = pyqtSignal(tuple)   # (r, g, b) 0.0~1.0
    width_changed  = pyqtSignal(float)

    def __init__(self, parent=None) -> None:
        super().__init__("메인 툴바", parent)
        self.setMovable(False)
        self._annot_color: QColor = QColor(255, 0, 0)  # 기본 빨강
        self._setup_actions()

    # ── UI 구성 ───────────────────────────────────────────────────────────────

    def _setup_actions(self) -> None:
        # ── 파일 ──────────────────────────────────────────────────────────────
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

        # ── 페이지 편집 ───────────────────────────────────────────────────────
        self._act_delete = QAction("삭제", self)
        self._act_delete.setShortcut(QKeySequence("Delete"))
        self._act_delete.setToolTip("선택한 페이지 삭제 (Delete)")
        self._act_delete.setEnabled(False)
        self._act_delete.triggered.connect(self.delete_page_requested)
        self.addAction(self._act_delete)

        self._act_extract = QAction("추출", self)
        self._act_extract.setToolTip("선택한 페이지를 새 PDF로 추출")
        self._act_extract.setEnabled(False)
        self._act_extract.triggered.connect(self.extract_page_requested)
        self.addAction(self._act_extract)

        self._act_insert = QAction("삽입", self)
        self._act_insert.setToolTip("다른 PDF에서 페이지 삽입")
        self._act_insert.setEnabled(False)
        self._act_insert.triggered.connect(self.insert_page_requested)
        self.addAction(self._act_insert)

        self.addSeparator()

        # ── 어노테이션 도구 (배타적 선택) ─────────────────────────────────────
        self._tool_group = QActionGroup(self)
        self._tool_group.setExclusive(True)

        tool_defs = [
            ("선택",   AnnotationTool.SELECT,  "선택/스크롤 모드 (Escape)"),
            ("텍스트", AnnotationTool.TEXT,    "텍스트 삽입"),
            ("사각형", AnnotationTool.RECT,    "사각형 그리기"),
            ("타원",   AnnotationTool.ELLIPSE, "타원 그리기"),
            ("선",     AnnotationTool.LINE,    "선 그리기"),
        ]
        self._tool_actions: dict[AnnotationTool, QAction] = {}
        for label, tool, tip in tool_defs:
            act = QAction(label, self)
            act.setToolTip(tip)
            act.setCheckable(True)
            act.setEnabled(False)
            act.setData(tool)
            self._tool_group.addAction(act)
            self.addAction(act)
            self._tool_actions[tool] = act

        # 선택 도구를 기본으로 체크
        self._tool_actions[AnnotationTool.SELECT].setChecked(True)
        self._tool_group.triggered.connect(self._on_tool_action)

        # Escape 단축키로 SELECT로 복귀
        self._tool_actions[AnnotationTool.SELECT].setShortcut(QKeySequence("Escape"))

        self.addSeparator()

        # ── 어노테이션 스타일 ─────────────────────────────────────────────────
        self.addWidget(QLabel("  색:"))
        self._btn_color = QAction("■", self)
        self._btn_color.setToolTip("어노테이션 색상 선택")
        self._btn_color.setEnabled(False)
        self._btn_color.triggered.connect(self._pick_color)
        self.addAction(self._btn_color)
        self._update_color_icon()

        self.addWidget(QLabel("  굵기:"))
        self._width_spin = QDoubleSpinBox()
        self._width_spin.setRange(0.5, 20.0)
        self._width_spin.setValue(2.0)
        self._width_spin.setSingleStep(0.5)
        self._width_spin.setFixedWidth(60)
        self._width_spin.setEnabled(False)
        self._width_spin.valueChanged.connect(self.width_changed)
        self.addWidget(self._width_spin)

        self.addSeparator()

        # ── 줌 ────────────────────────────────────────────────────────────────
        self.addWidget(QLabel("  줌:"))

        self._act_zoom_out = QAction("－", self)
        self._act_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        self._act_zoom_out.setToolTip("줌 아웃 (Ctrl+-)")
        self._act_zoom_out.setEnabled(False)
        self._act_zoom_out.triggered.connect(self.zoom_out_requested)
        self.addAction(self._act_zoom_out)

        self._zoom_spin = QSpinBox()
        self._zoom_spin.setRange(25, 400)
        self._zoom_spin.setValue(150)
        self._zoom_spin.setSuffix("%")
        self._zoom_spin.setFixedWidth(82)
        self._zoom_spin.setEnabled(False)
        self._zoom_spin.valueChanged.connect(lambda v: self.zoom_value_changed.emit(v / 100.0))
        self.addWidget(self._zoom_spin)

        self._act_zoom_in = QAction("＋", self)
        self._act_zoom_in.setShortcut(QKeySequence("Ctrl+="))
        self._act_zoom_in.setToolTip("줌 인 (Ctrl+=)")
        self._act_zoom_in.setEnabled(False)
        self._act_zoom_in.triggered.connect(self.zoom_in_requested)
        self.addAction(self._act_zoom_in)

        self._act_zoom_fit = QAction("맞춤", self)
        self._act_zoom_fit.setShortcut(QKeySequence("Ctrl+0"))
        self._act_zoom_fit.setToolTip("화면에 맞게 (Ctrl+0)")
        self._act_zoom_fit.setEnabled(False)
        self._act_zoom_fit.triggered.connect(self.zoom_fit_requested)
        self.addAction(self._act_zoom_fit)

        self.addWidget(QWidget())  # 오른쪽 여백

    # ── 공개 API ──────────────────────────────────────────────────────────────

    def set_document_loaded(self, loaded: bool) -> None:
        self._act_save.setEnabled(loaded)
        self._act_delete.setEnabled(loaded)
        self._act_extract.setEnabled(loaded)
        self._act_insert.setEnabled(loaded)
        self._act_zoom_in.setEnabled(loaded)
        self._act_zoom_out.setEnabled(loaded)
        self._act_zoom_fit.setEnabled(loaded)
        self._zoom_spin.setEnabled(loaded)
        self._btn_color.setEnabled(loaded)
        self._width_spin.setEnabled(loaded)
        for act in self._tool_actions.values():
            act.setEnabled(loaded)

    def update_zoom_display(self, zoom: float) -> None:
        self._zoom_spin.blockSignals(True)
        self._zoom_spin.setValue(round(zoom * 100))
        self._zoom_spin.blockSignals(False)

    def set_tool_checked(self, tool: AnnotationTool) -> None:
        """외부에서 도구 버튼 체크 상태를 동기화합니다."""
        act = self._tool_actions.get(tool)
        if act:
            act.setChecked(True)

    # ── 내부 슬롯 ─────────────────────────────────────────────────────────────

    def _on_tool_action(self, action: QAction) -> None:
        tool: AnnotationTool = action.data()
        self.tool_changed.emit(tool)

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._annot_color, self, "어노테이션 색상 선택")
        if color.isValid():
            self._annot_color = color
            self._update_color_icon()
            rgb = (color.redF(), color.greenF(), color.blueF())
            self.color_changed.emit(rgb)

    def _update_color_icon(self) -> None:
        """색상 버튼의 아이콘을 현재 색상으로 업데이트합니다."""
        px = QPixmap(16, 16)
        px.fill(self._annot_color)
        self._btn_color.setIcon(QIcon(px))

    @property
    def current_annot_color(self) -> tuple[float, float, float]:
        return (
            self._annot_color.redF(),
            self._annot_color.greenF(),
            self._annot_color.blueF(),
        )

    @property
    def current_annot_width(self) -> float:
        return self._width_spin.value()
