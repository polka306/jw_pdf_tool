# 멀티 PDF 탭 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `MainWindow`가 여러 PDF를 탭으로 동시에 열 수 있도록 확장한다.

**Architecture:** `PdfTabPage`(탭 1개의 독립 유닛)를 `PdfTabWidget`(QTabWidget 확장)이 관리하고, `MainWindow`는 `active_tab()`에만 명령을 위임한다. 탭 전환 시 `active_tab_changed` 시그널로 사이드바를 재연결한다.

**Tech Stack:** PyQt6, PyMuPDF(fitz), pikepdf, Python 3.11+

---

## 파일 구조

| 경로 | 역할 |
|------|------|
| `app/ui/pdf_tab_page.py` | **새 파일** — 탭 하나의 독립 뷰어 유닛 |
| `app/ui/pdf_tab_widget.py` | **새 파일** — QTabWidget 확장, 탭 생명주기 |
| `app/ui/detached_window.py` | **새 파일** — 탭 분리 시 독립 창 |
| `app/ui/main_window.py` | **수정** — 단일 doc/viewer → PdfTabWidget |
| `tests/ui/test_pdf_tab_page.py` | **새 파일** — PdfTabPage 테스트 |
| `tests/ui/test_pdf_tab_widget.py` | **새 파일** — PdfTabWidget 테스트 |
| `tests/ui/test_detached_window.py` | **새 파일** — DetachedWindow 테스트 |
| `tests/ui/test_main_window_tabs.py` | **새 파일** — MainWindow 탭 통합 테스트 |

---

## Task 1: PdfTabPage — 탭 하나의 독립 유닛

**Files:**
- Create: `app/ui/pdf_tab_page.py`
- Create: `tests/ui/test_pdf_tab_page.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/ui/test_pdf_tab_page.py
"""PdfTabPage 단위 테스트."""
from __future__ import annotations
import pytest
from PyQt6.QtWidgets import QApplication
from app.ui.pdf_tab_page import PdfTabPage

@pytest.fixture
def tab_page(qapp):
    page = PdfTabPage()
    yield page
    page.cleanup()

class TestPdfTabPageInit:
    def test_initial_state(self, tab_page):
        assert not tab_page.doc.is_open
        assert tab_page.viewer is not None
        assert tab_page.cmd_mgr is not None
        assert tab_page.search_query == ""
        assert tab_page.search_results == []
        assert tab_page.search_idx == -1

    def test_tab_title_no_doc(self, tab_page):
        assert tab_page.tab_title == "새 탭"

    def test_is_modified_no_doc(self, tab_page):
        assert not tab_page.is_modified

class TestPdfTabPageLoad:
    def test_load_opens_doc(self, tab_page, pdf_3pages):
        tab_page.load(pdf_3pages)
        assert tab_page.doc.is_open
        assert tab_page.doc.path == pdf_3pages

    def test_load_sets_tab_title(self, tab_page, pdf_3pages):
        import os
        tab_page.load(pdf_3pages)
        assert tab_page.tab_title == os.path.basename(pdf_3pages)

    def test_load_with_page(self, tab_page, pdf_3pages):
        tab_page.load(pdf_3pages, page=1)
        assert tab_page.viewer.current_page == 1

    def test_cleanup_closes_doc(self, tab_page, pdf_3pages):
        tab_page.load(pdf_3pages)
        tab_page.cleanup()
        assert not tab_page.doc.is_open

    def test_path_property(self, tab_page, pdf_3pages):
        tab_page.load(pdf_3pages)
        assert tab_page.path == pdf_3pages
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd /home/jwkang/dev/02_PDF---
python -m pytest tests/ui/test_pdf_tab_page.py -v 2>&1 | head -20
```

예상 출력: `ImportError: cannot import name 'PdfTabPage'`

- [ ] **Step 3: PdfTabPage 구현**

```python
# app/ui/pdf_tab_page.py
"""탭 하나의 독립적인 PDF 뷰어 유닛."""
from __future__ import annotations

import os

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.core.command_manager import CommandManager
from app.core.pdf_document import PdfDocument
from app.ui.pdf_viewer import PdfViewer


class PdfTabPage(QWidget):
    """탭 하나 = 독립적인 PdfDocument + PdfViewer + CommandManager."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.doc = PdfDocument()
        self.cmd_mgr = CommandManager()
        self.viewer = PdfViewer()
        self.search_query: str = ""
        self.search_results: list = []
        self.search_idx: int = -1
        self._setup_layout()

    def _setup_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.viewer)

    # ── 프로퍼티 ─────────────────────────────────────────────────────────

    @property
    def path(self) -> str | None:
        return self.doc.path

    @property
    def is_modified(self) -> bool:
        return self.cmd_mgr.can_undo

    @property
    def tab_title(self) -> str:
        if not self.doc.is_open or not self.doc.path:
            return "새 탭"
        name = os.path.basename(self.doc.path)
        return f"● {name}" if self.is_modified else name

    # ── 공개 메서드 ──────────────────────────────────────────────────────

    def load(self, path: str, page: int = 0, zoom: float = 1.0) -> None:
        """PDF 파일을 열고 지정 페이지·줌으로 초기화한다."""
        self.doc.open(path)
        self.viewer.set_document(self.doc)
        self.cmd_mgr.clear()
        if page > 0:
            self.viewer.goto_page(page)
        if zoom != 1.0:
            self.viewer.set_zoom(zoom)

    def cleanup(self) -> None:
        """리소스를 해제한다. 탭 닫기 전에 호출해야 한다."""
        self.doc.close()
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/ui/test_pdf_tab_page.py -v
```

예상 출력: 모든 테스트 PASSED

- [ ] **Step 5: 커밋**

```bash
git add app/ui/pdf_tab_page.py tests/ui/test_pdf_tab_page.py
git commit -m "feat: PdfTabPage — 독립 탭 유닛 추가"
```

---

## Task 2: PdfTabWidget — 기본 탭 컨테이너 (열기/닫기/전환)

**Files:**
- Create: `app/ui/pdf_tab_widget.py`
- Create: `tests/ui/test_pdf_tab_widget.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/ui/test_pdf_tab_widget.py
"""PdfTabWidget 단위 테스트."""
from __future__ import annotations
import pytest
from PyQt6.QtWidgets import QMessageBox
from app.ui.pdf_tab_widget import PdfTabWidget
from app.ui.pdf_tab_page import PdfTabPage

@pytest.fixture
def tab_widget(qapp):
    w = PdfTabWidget()
    yield w
    w.close_all()

class TestPdfTabWidgetOpen:
    def test_open_pdf_creates_tab(self, tab_widget, pdf_3pages):
        tab_widget.open_pdf(pdf_3pages)
        assert tab_widget.count() == 1

    def test_open_pdf_returns_tab_page(self, tab_widget, pdf_3pages):
        tab = tab_widget.open_pdf(pdf_3pages)
        assert isinstance(tab, PdfTabPage)

    def test_open_multiple_pdfs(self, tab_widget, pdf_1page, pdf_3pages):
        tab_widget.open_pdf(pdf_1page)
        tab_widget.open_pdf(pdf_3pages)
        assert tab_widget.count() == 2

    def test_active_tab_none_when_empty(self, tab_widget):
        assert tab_widget.active_tab() is None

    def test_active_tab_after_open(self, tab_widget, pdf_3pages):
        tab = tab_widget.open_pdf(pdf_3pages)
        assert tab_widget.active_tab() is tab

    def test_open_with_page(self, tab_widget, pdf_3pages):
        tab = tab_widget.open_pdf(pdf_3pages, page=1)
        assert tab.viewer.current_page == 1

class TestPdfTabWidgetClose:
    def test_close_tab_removes_it(self, tab_widget, pdf_1page, monkeypatch):
        monkeypatch.setattr(QMessageBox, "question",
                            lambda *a, **kw: QMessageBox.StandardButton.No)
        tab_widget.open_pdf(pdf_1page)
        tab_widget.close_tab(0)
        assert tab_widget.count() == 0

    def test_close_tab_adds_to_recent(self, tab_widget, pdf_1page, monkeypatch):
        monkeypatch.setattr(QMessageBox, "question",
                            lambda *a, **kw: QMessageBox.StandardButton.No)
        tab_widget.open_pdf(pdf_1page)
        tab_widget.close_tab(0)
        assert len(tab_widget._recent_closed) == 1

    def test_reopen_last_closed(self, tab_widget, pdf_1page, monkeypatch):
        monkeypatch.setattr(QMessageBox, "question",
                            lambda *a, **kw: QMessageBox.StandardButton.No)
        tab_widget.open_pdf(pdf_1page)
        tab_widget.close_tab(0)
        tab_widget.reopen_last_closed()
        assert tab_widget.count() == 1

class TestPdfTabWidgetActiveTabChanged:
    def test_signal_emitted_on_open(self, tab_widget, pdf_1page):
        received = []
        tab_widget.active_tab_changed.connect(received.append)
        tab_widget.open_pdf(pdf_1page)
        assert len(received) == 1
        assert isinstance(received[0], PdfTabPage)

    def test_signal_emitted_on_switch(self, tab_widget, pdf_1page, pdf_3pages):
        tab_widget.open_pdf(pdf_1page)
        tab_widget.open_pdf(pdf_3pages)
        received = []
        tab_widget.active_tab_changed.connect(received.append)
        tab_widget.setCurrentIndex(0)
        assert len(received) == 1
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/ui/test_pdf_tab_widget.py -v 2>&1 | head -20
```

예상 출력: `ImportError: cannot import name 'PdfTabWidget'`

- [ ] **Step 3: PdfTabWidget 기본 구현**

```python
# app/ui/pdf_tab_widget.py
"""QTabWidget 확장 — 멀티 PDF 탭 컨테이너."""
from __future__ import annotations

from collections import deque

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QTabWidget

from app.ui.pdf_tab_page import PdfTabPage


class PdfTabWidget(QTabWidget):
    """여러 PdfTabPage를 관리하는 탭 컨테이너."""

    active_tab_changed = pyqtSignal(object)  # PdfTabPage | None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self._recent_closed: deque[tuple[str, int, float]] = deque(maxlen=10)
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self._on_current_changed)
        self.tabBar().setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.tabBar().customContextMenuRequested.connect(
            self._show_tab_context_menu
        )

    # ── 공개 API ─────────────────────────────────────────────────────────

    def open_pdf(self, path: str, page: int = 0, zoom: float = 1.0) -> PdfTabPage:
        """새 탭으로 PDF를 연다."""
        tab = PdfTabPage()
        tab.load(path, page, zoom)
        idx = self.addTab(tab, tab.tab_title)
        self.setTabToolTip(idx, path)
        self.setCurrentIndex(idx)
        return tab

    def active_tab(self) -> PdfTabPage | None:
        """현재 활성 탭 반환. 탭이 없으면 None."""
        widget = self.currentWidget()
        return widget if isinstance(widget, PdfTabPage) else None

    def close_tab(self, index: int) -> None:
        """탭을 닫는다. 미저장 변경이 있으면 사용자에게 확인한다."""
        tab = self.widget(index)
        if not isinstance(tab, PdfTabPage):
            return
        if tab.is_modified:
            reply = QMessageBox.question(
                self, "저장 확인",
                f"{tab.tab_title}\n\n변경 사항을 저장하겠습니까?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save:
                tab.doc.save()
        if tab.doc.is_open and tab.path:
            self._recent_closed.append(
                (tab.path, tab.viewer.current_page, tab.viewer.zoom)
            )
        tab.cleanup()
        self.removeTab(index)

    def reopen_last_closed(self) -> None:
        """최근 닫은 탭을 다시 연다."""
        if not self._recent_closed:
            return
        path, page, zoom = self._recent_closed.pop()
        self.open_pdf(path, page, zoom)

    def duplicate_tab(self, index: int) -> None:
        """탭을 복제한다 (같은 경로, 같은 페이지·줌)."""
        tab = self.widget(index)
        if not isinstance(tab, PdfTabPage) or not tab.doc.is_open:
            return
        self.open_pdf(tab.path, tab.viewer.current_page, tab.viewer.zoom)

    def detach_tab(self, index: int) -> None:
        """탭을 독립 창으로 분리한다."""
        from app.ui.detached_window import DetachedWindow
        tab = self.widget(index)
        if not isinstance(tab, PdfTabPage):
            return
        self.removeTab(index)
        win = DetachedWindow(tab, self)
        win.reattach_requested.connect(self._reattach_tab)
        win.show()

    def close_all(self) -> None:
        """모든 탭을 닫는다."""
        for i in range(self.count() - 1, -1, -1):
            self.close_tab(i)

    # ── 내부 슬롯 ────────────────────────────────────────────────────────

    def _on_tab_close_requested(self, index: int) -> None:
        self.close_tab(index)

    def _on_current_changed(self, index: int) -> None:
        self.active_tab_changed.emit(self.active_tab())

    def _reattach_tab(self, tab: PdfTabPage) -> None:
        idx = self.addTab(tab, tab.tab_title)
        if tab.doc.is_open and tab.path:
            self.setTabToolTip(idx, tab.path)
        self.setCurrentIndex(idx)

    def _show_tab_context_menu(self, pos) -> None:
        from PyQt6.QtWidgets import QApplication, QMenu
        index = self.tabBar().tabAt(pos)
        if index < 0:
            return
        menu = QMenu(self)
        menu.addAction("닫기").triggered.connect(
            lambda: self.close_tab(index)
        )
        menu.addAction("다른 탭 모두 닫기").triggered.connect(
            lambda: self._close_others(index)
        )
        menu.addAction("오른쪽 탭 모두 닫기").triggered.connect(
            lambda: self._close_right(index)
        )
        menu.addSeparator()
        menu.addAction("복제").triggered.connect(
            lambda: self.duplicate_tab(index)
        )
        menu.addAction("새 창으로 열기").triggered.connect(
            lambda: self.detach_tab(index)
        )
        tab = self.widget(index)
        if isinstance(tab, PdfTabPage) and tab.doc.is_open and tab.path:
            menu.addSeparator()
            menu.addAction("파일 경로 복사").triggered.connect(
                lambda: QApplication.clipboard().setText(tab.path)
            )
        menu.exec(self.tabBar().mapToGlobal(pos))

    def _close_others(self, keep_index: int) -> None:
        for i in range(self.count() - 1, -1, -1):
            if i != keep_index:
                self.close_tab(i)

    def _close_right(self, from_index: int) -> None:
        for i in range(self.count() - 1, from_index, -1):
            self.close_tab(i)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/ui/test_pdf_tab_widget.py -v
```

예상 출력: 모든 테스트 PASSED

- [ ] **Step 5: 커밋**

```bash
git add app/ui/pdf_tab_widget.py tests/ui/test_pdf_tab_widget.py
git commit -m "feat: PdfTabWidget — 탭 컨테이너 추가 (열기/닫기/전환/재열기)"
```

---

## Task 3: DetachedWindow — 탭 분리 창

**Files:**
- Create: `app/ui/detached_window.py`
- Create: `tests/ui/test_detached_window.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/ui/test_detached_window.py
"""DetachedWindow 단위 테스트."""
from __future__ import annotations
import pytest
from PyQt6.QtWidgets import QMessageBox
from app.ui.detached_window import DetachedWindow
from app.ui.pdf_tab_page import PdfTabPage
from app.ui.pdf_tab_widget import PdfTabWidget

@pytest.fixture
def tab_widget(qapp):
    w = PdfTabWidget()
    yield w
    w.close_all()

@pytest.fixture
def loaded_tab(pdf_3pages):
    tab = PdfTabPage()
    tab.load(pdf_3pages)
    yield tab
    tab.cleanup()

class TestDetachedWindowInit:
    def test_creates_window_with_tab(self, qapp, loaded_tab, tab_widget):
        win = DetachedWindow(loaded_tab, tab_widget)
        assert win.centralWidget() is loaded_tab
        win.close()

    def test_window_title_contains_filename(self, qapp, loaded_tab, tab_widget):
        win = DetachedWindow(loaded_tab, tab_widget)
        assert "test_3pages" in win.windowTitle() or ".pdf" in win.windowTitle()
        win.close()

class TestDetachedWindowReattach:
    def test_reattach_signal_emitted(self, qapp, loaded_tab, tab_widget, monkeypatch):
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win = DetachedWindow(loaded_tab, tab_widget)
        received = []
        win.reattach_requested.connect(received.append)
        win.close()
        assert len(received) == 1
        assert received[0] is loaded_tab

    def test_no_reattach_on_discard(self, qapp, loaded_tab, tab_widget, monkeypatch):
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.No
        )
        win = DetachedWindow(loaded_tab, tab_widget)
        received = []
        win.reattach_requested.connect(received.append)
        win.close()
        assert len(received) == 0
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/ui/test_detached_window.py -v 2>&1 | head -20
```

예상 출력: `ImportError: cannot import name 'DetachedWindow'`

- [ ] **Step 3: DetachedWindow 구현**

```python
# app/ui/detached_window.py
"""탭 분리 시 띄우는 독립 창."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QToolBar

from app.ui.pdf_tab_page import PdfTabPage


class DetachedWindow(QMainWindow):
    """분리된 PdfTabPage를 독립 창으로 표시한다."""

    reattach_requested = pyqtSignal(object)  # PdfTabPage

    def __init__(
        self,
        tab: PdfTabPage,
        tab_widget,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._tab = tab
        self._tab_widget = tab_widget
        self._reattached = False
        self.setWindowTitle(f"{tab.tab_title} — jw_pdf (분리됨)")
        self.setCentralWidget(tab)
        self._setup_toolbar()
        self.resize(900, 700)

    def _setup_toolbar(self) -> None:
        tb = QToolBar("뷰어", self)
        self.addToolBar(tb)
        act_zoom_in = tb.addAction("줌 +")
        act_zoom_in.triggered.connect(self._tab.viewer.zoom_in)
        act_zoom_out = tb.addAction("줌 -")
        act_zoom_out.triggered.connect(self._tab.viewer.zoom_out)
        act_zoom_fit = tb.addAction("페이지 맞춤")
        act_zoom_fit.triggered.connect(self._tab.viewer.zoom_fit)

    def closeEvent(self, event) -> None:
        if self._reattached:
            event.accept()
            return
        reply = QMessageBox.question(
            self,
            "창 닫기",
            "이 탭을 메인 창으로 되돌리겠습니까?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._reattached = True
            self.reattach_requested.emit(self._tab)
            event.accept()
        elif reply == QMessageBox.StandardButton.No:
            self._tab.cleanup()
            event.accept()
        else:
            event.ignore()
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/ui/test_detached_window.py -v
```

예상 출력: 모든 테스트 PASSED

- [ ] **Step 5: 커밋**

```bash
git add app/ui/detached_window.py tests/ui/test_detached_window.py
git commit -m "feat: DetachedWindow — 탭 분리 창 추가"
```

---

## Task 4: MainWindow — UI 재구성 (setup_ui 교체)

**Files:**
- Modify: `app/ui/main_window.py` (setup_ui, _setup_menu 부분)
- Create: `tests/ui/test_main_window_tabs.py`

이 Task에서는 `main_window.py`의 `_setup_ui` 메서드에서 단일 `PdfViewer`/`PdfDocument`를 `PdfTabWidget`으로 교체하고, 탭 전환 시 사이드바를 재연결하는 `_on_active_tab_changed`를 추가한다.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/ui/test_main_window_tabs.py
"""MainWindow 멀티탭 통합 테스트."""
from __future__ import annotations
import pytest
from PyQt6.QtWidgets import QMessageBox
from app.ui.main_window import MainWindow
from app.ui.pdf_tab_widget import PdfTabWidget

@pytest.fixture
def win(qapp):
    w = MainWindow()
    yield w
    w._tab_widget.close_all()
    w.close()

class TestMainWindowHasTabWidget:
    def test_has_tab_widget(self, win):
        assert hasattr(win, "_tab_widget")
        assert isinstance(win._tab_widget, PdfTabWidget)

    def test_no_single_doc_attr(self, win):
        assert not hasattr(win, "_doc")

    def test_no_single_viewer_attr(self, win):
        assert not hasattr(win, "_viewer")

class TestMainWindowOpenInTab:
    def test_open_file_creates_tab(self, win, pdf_3pages, monkeypatch):
        from PyQt6.QtWidgets import QFileDialog
        monkeypatch.setattr(
            QFileDialog, "getOpenFileName",
            lambda *a, **kw: (pdf_3pages, "")
        )
        win._open_file()
        assert win._tab_widget.count() == 1

    def test_open_two_files_creates_two_tabs(self, win, pdf_1page, pdf_3pages, monkeypatch):
        from PyQt6.QtWidgets import QFileDialog
        paths = [pdf_1page, pdf_3pages]
        call_count = [0]
        def fake_open(*a, **kw):
            p = paths[call_count[0] % len(paths)]
            call_count[0] += 1
            return (p, "")
        monkeypatch.setattr(QFileDialog, "getOpenFileName", fake_open)
        win._open_file()
        win._open_file()
        assert win._tab_widget.count() == 2

    def test_title_updates_on_open(self, win, pdf_3pages, monkeypatch):
        from PyQt6.QtWidgets import QFileDialog
        import os
        monkeypatch.setattr(
            QFileDialog, "getOpenFileName",
            lambda *a, **kw: (pdf_3pages, "")
        )
        win._open_file()
        assert os.path.basename(pdf_3pages) in win.windowTitle()

class TestMainWindowTabSwitch:
    def test_title_updates_on_tab_switch(self, win, pdf_1page, pdf_3pages, monkeypatch):
        import os
        from PyQt6.QtWidgets import QFileDialog
        paths = [pdf_1page, pdf_3pages]
        idx = [0]
        def fake_open(*a, **kw):
            p = paths[idx[0] % 2]; idx[0] += 1; return (p, "")
        monkeypatch.setattr(QFileDialog, "getOpenFileName", fake_open)
        win._open_file()
        win._open_file()
        win._tab_widget.setCurrentIndex(0)
        assert os.path.basename(pdf_1page) in win.windowTitle()

class TestMainWindowCloseEvent:
    def test_close_event_closes_all_tabs(self, win, pdf_3pages, monkeypatch):
        from PyQt6.QtWidgets import QFileDialog
        monkeypatch.setattr(
            QFileDialog, "getOpenFileName",
            lambda *a, **kw: (pdf_3pages, "")
        )
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.Discard
        )
        win._open_file()
        win.close()
        assert win._tab_widget.count() == 0
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/ui/test_main_window_tabs.py -v 2>&1 | head -30
```

예상 출력: `AttributeError: 'MainWindow' object has no attribute '_tab_widget'`

- [ ] **Step 3: `main_window.py` — `__init__` 정리 및 `_setup_ui` 교체**

`app/ui/main_window.py` 상단의 import를 수정한다:

```python
# 기존 import 블록에서 PdfDocument, PdfViewer 제거하고 아래 추가
from app.ui.pdf_tab_widget import PdfTabWidget
from app.ui.pdf_tab_page import PdfTabPage
```

`__init__` 메서드를 다음으로 교체한다:

```python
def __init__(self) -> None:
    super().__init__()
    self._is_fullscreen = False
    self._recent_menu = None
    self._search_bar = None
    self._bookmark_panel = None
    self._prev_tab: PdfTabPage | None = None
    self._setup_ui()
    self._connect_signals()
    self.setWindowTitle(f"{self.APP_TITLE} v{__version__}")
    self.resize(1200, 800)
    self.setAcceptDrops(True)
```

`_setup_ui` 메서드를 다음으로 교체한다:

```python
def _setup_ui(self) -> None:
    from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

    self._toolbar = MainToolBar(self)
    self.addToolBar(self._toolbar)

    self._splitter = QSplitter(Qt.Orientation.Horizontal)

    # 좌측: 썸네일 + 북마크 탭
    self._side_tabs = QTabWidget()
    self._page_panel = PagePanel()
    self._side_tabs.addTab(self._page_panel, "썸네일")

    try:
        from app.ui.bookmark_panel import BookmarkPanel
        self._bookmark_panel = BookmarkPanel()
        self._side_tabs.addTab(self._bookmark_panel, "북마크")
    except ImportError:
        pass

    self._splitter.addWidget(self._side_tabs)

    # 우측: 검색바 + PdfTabWidget
    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(0)

    try:
        from app.ui.search_bar import SearchBar
        self._search_bar = SearchBar()
        self._search_bar.hide()
        right_layout.addWidget(self._search_bar)
    except ImportError:
        pass

    self._tab_widget = PdfTabWidget()
    right_layout.addWidget(self._tab_widget)

    self._splitter.addWidget(right_widget)
    self._splitter.setStretchFactor(0, 0)
    self._splitter.setStretchFactor(1, 1)
    self.setCentralWidget(self._splitter)

    self._status_bar = QStatusBar(self)
    self.setStatusBar(self._status_bar)
    self._lbl_page = QLabel("페이지: -")
    self._lbl_zoom = QLabel("줌: -")
    self._lbl_tool = QLabel("도구: 선택")
    self._lbl_file = QLabel("")
    self._status_bar.addWidget(self._lbl_page)
    self._status_bar.addWidget(QLabel("  |  "))
    self._status_bar.addWidget(self._lbl_zoom)
    self._status_bar.addWidget(QLabel("  |  "))
    self._status_bar.addWidget(self._lbl_tool)
    self._status_bar.addPermanentWidget(self._lbl_file)

    self._setup_menu()
```

`_on_active_tab_changed` 메서드를 추가한다:

```python
def _on_active_tab_changed(self, tab: PdfTabPage | None) -> None:
    """탭 전환 시 사이드바·툴바·타이틀을 새 탭에 맞게 갱신한다."""
    # 이전 탭 시그널 해제
    if self._prev_tab is not None:
        try:
            self._prev_tab.viewer.zoom_changed.disconnect(self._on_zoom_changed)
            self._prev_tab.viewer.page_changed.disconnect(self._on_page_changed)
            self._prev_tab.viewer.annotation_requested.disconnect(
                self._on_annotation_requested
            )
        except (TypeError, RuntimeError):
            pass
    self._prev_tab = tab

    if tab is None:
        self._page_panel.clear() if hasattr(self._page_panel, "clear") else None
        self.setWindowTitle(f"{self.APP_TITLE} v{__version__}")
        self._lbl_file.setText("")
        self._lbl_page.setText("페이지: -")
        self._lbl_zoom.setText("줌: -")
        self._toolbar.set_document_loaded(False)
        self._update_undo_actions(tab)
        return

    # 새 탭 시그널 연결
    tab.viewer.zoom_changed.connect(self._on_zoom_changed)
    tab.viewer.page_changed.connect(self._on_page_changed)
    tab.viewer.annotation_requested.connect(self._on_annotation_requested)

    # 사이드바 갱신
    if tab.doc.is_open:
        self._page_panel.load_document(tab.doc)
        if self._bookmark_panel:
            self._bookmark_panel.load_bookmarks(tab.path)
        self._update_title(tab.path)
        self._lbl_file.setText(os.path.basename(tab.path))
        self._toolbar.set_document_loaded(True)
    else:
        self.setWindowTitle(f"{self.APP_TITLE} v{__version__}")
        self._lbl_file.setText("")
        self._toolbar.set_document_loaded(False)

    # 검색바 상태 복원
    if self._search_bar:
        if tab.search_query:
            self._search_bar.show()
        else:
            self._search_bar.hide()

    self._update_page_status(tab.viewer.current_page)
    self._toolbar.update_zoom_display(tab.viewer.zoom)
    self._toolbar.set_tool_checked(AnnotationTool.SELECT)
    self._update_undo_actions(tab)
```

`_active_tab` 헬퍼 프로퍼티를 추가한다:

```python
def _active_tab(self) -> PdfTabPage | None:
    return self._tab_widget.active_tab()
```

- [ ] **Step 4: `_connect_signals` 업데이트**

기존 `_connect_signals`를 다음으로 교체한다:

```python
def _connect_signals(self) -> None:
    # 파일
    self._toolbar.open_requested.connect(self._open_file)
    self._toolbar.save_requested.connect(self._save_file)

    # 줌 (active_tab 경유)
    self._toolbar.zoom_in_requested.connect(self._zoom_in)
    self._toolbar.zoom_out_requested.connect(self._zoom_out)
    self._toolbar.zoom_fit_requested.connect(self._zoom_fit)
    self._toolbar.zoom_value_changed.connect(self._set_zoom)

    # 페이지 편집
    self._toolbar.delete_page_requested.connect(self._delete_selected_pages)
    self._toolbar.extract_page_requested.connect(self._extract_selected_pages)
    self._toolbar.insert_page_requested.connect(self._insert_pages_at_current)
    self._page_panel.page_selected.connect(self._on_thumbnail_selected)
    self._page_panel.page_moved.connect(self._on_page_moved)
    self._page_panel.delete_requested.connect(self._delete_pages)
    self._page_panel.extract_requested.connect(self._extract_pages)
    self._page_panel.insert_requested.connect(self._insert_pages)

    # 어노테이션
    self._toolbar.tool_changed.connect(self._on_tool_changed)
    self._toolbar.color_changed.connect(self._on_color_changed)
    self._toolbar.width_changed.connect(self._on_width_changed)
    self._toolbar.text_font_changed.connect(self._on_text_font_changed)
    self._toolbar.text_size_changed.connect(self._on_text_size_changed)
    self._toolbar.text_bold_changed.connect(self._on_text_bold_changed)
    self._toolbar.text_italic_changed.connect(self._on_text_italic_changed)

    # 검색바
    if self._search_bar:
        self._search_bar.search_requested.connect(self._on_search_requested)
        self._search_bar.next_requested.connect(self._on_search_next)
        self._search_bar.prev_requested.connect(self._on_search_prev)

    # 북마크 패널
    if self._bookmark_panel:
        self._bookmark_panel.page_requested.connect(self._on_bookmark_page_requested)

    # 변환
    self._toolbar.convert_requested.connect(self._open_convert_dialog)

    # 탭 전환
    self._tab_widget.active_tab_changed.connect(self._on_active_tab_changed)
```

줌 델리게이트 메서드를 추가한다:

```python
def _zoom_in(self) -> None:
    tab = self._active_tab()
    if tab:
        tab.viewer.zoom_in()

def _zoom_out(self) -> None:
    tab = self._active_tab()
    if tab:
        tab.viewer.zoom_out()

def _zoom_fit(self) -> None:
    tab = self._active_tab()
    if tab:
        tab.viewer.zoom_fit()

def _set_zoom(self, zoom: float) -> None:
    tab = self._active_tab()
    if tab:
        tab.viewer.set_zoom(zoom)

def _on_bookmark_page_requested(self, page: int) -> None:
    tab = self._active_tab()
    if tab:
        tab.viewer.goto_page(page)
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
python -m pytest tests/ui/test_main_window_tabs.py -v
```

예상 출력: 모든 테스트 PASSED

- [ ] **Step 6: 커밋**

```bash
git add app/ui/main_window.py tests/ui/test_main_window_tabs.py
git commit -m "feat: MainWindow — PdfTabWidget 통합, setup_ui/connect_signals 재구성"
```

---

## Task 5: MainWindow — 액션 핸들러 전체 업데이트

**Files:**
- Modify: `app/ui/main_window.py` (파일 작업, 페이지 편집, 어노테이션, Undo/Redo, 모든 도구 메서드)

모든 `self._doc`, `self._viewer`, `self._cmd_mgr` 참조를 `self._active_tab()` 경유로 교체한다.

- [ ] **Step 1: `_open_file` 교체**

```python
def _open_file(self) -> None:
    path, _ = QFileDialog.getOpenFileName(
        self, "PDF 파일 열기", "", "PDF 파일 (*.pdf);;모든 파일 (*)"
    )
    if not path:
        return
    try:
        self._tab_widget.open_pdf(path)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"파일을 열 수 없습니다:\n{e}")
        return
    self._add_recent_file(path)
```

- [ ] **Step 2: `_save_file`, `_save_as` 교체**

```python
def _save_file(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    try:
        tab.doc.save()
        self._status_bar.showMessage("저장 완료", 2000)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")

def _save_as(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    path, _ = QFileDialog.getSaveFileName(
        self, "다른 이름으로 저장", "", "PDF 파일 (*.pdf)"
    )
    if not path:
        return
    if not path.lower().endswith(".pdf"):
        path += ".pdf"
    try:
        tab.doc.save(path)
        self._update_title(path)
        self._lbl_file.setText(os.path.basename(path))
        self._status_bar.showMessage("저장 완료", 2000)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")
```

- [ ] **Step 3: 페이지 편집 메서드 교체**

```python
def _on_page_moved(self, from_idx: int, to_idx: int) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    cmd = MovePageCommand(tab.doc.raw, from_idx, to_idx)
    tab.cmd_mgr.execute(cmd)
    self._refresh_after_edit()
    tab.viewer.goto_page(min(to_idx, tab.doc.page_count - 1))
    self._status_bar.showMessage(f"페이지 {from_idx + 1} → {to_idx + 1} 이동", 2000)
    self._update_undo_actions(tab)

def _delete_selected_pages(self) -> None:
    self._delete_pages(self._page_panel.selected_indices())

def _delete_pages(self, indices: list[int]) -> None:
    tab = self._active_tab()
    if not indices or tab is None or not tab.doc.is_open:
        return
    if tab.doc.page_count <= len(indices):
        QMessageBox.warning(self, "삭제 불가", "모든 페이지를 삭제할 수 없습니다.")
        return
    page_nums = ", ".join(str(i + 1) for i in sorted(indices))
    reply = QMessageBox.question(
        self, "페이지 삭제", f"페이지 {page_nums}을(를) 삭제하시겠습니까?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return
    cmd = DeletePagesCommand(tab.doc.raw, indices)
    tab.cmd_mgr.execute(cmd)
    self._refresh_after_edit()
    self._status_bar.showMessage(f"{len(indices)}개 페이지 삭제됨", 2000)
    self._update_undo_actions(tab)

def _extract_selected_pages(self) -> None:
    self._extract_pages(self._page_panel.selected_indices())

def _extract_pages(self, indices: list[int]) -> None:
    tab = self._active_tab()
    if not indices or tab is None or not tab.doc.is_open:
        return
    path, _ = QFileDialog.getSaveFileName(
        self, "페이지 추출 — 저장 위치 선택", "", "PDF 파일 (*.pdf)"
    )
    if not path:
        return
    if not path.lower().endswith(".pdf"):
        path += ".pdf"
    try:
        page_editor.extract_pages(tab.doc.raw, indices, path)
        self._status_bar.showMessage(
            f"{len(indices)}개 페이지 추출 → {os.path.basename(path)}", 3000
        )
    except Exception as e:
        QMessageBox.critical(self, "오류", f"추출 실패:\n{e}")

def _insert_pages_at_current(self) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    self._insert_pages(tab.viewer.current_page + 1)

def _insert_pages(self, insert_before: int) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    dlg = InsertDialog(self)
    if dlg.exec() != InsertDialog.DialogCode.Accepted:
        return
    source_path = dlg.source_path()
    source_indices = dlg.selected_indices()
    if not source_path or not source_indices:
        return
    try:
        cmd = InsertPagesCommand(tab.doc.raw, source_path, source_indices, insert_before)
        tab.cmd_mgr.execute(cmd)
        self._refresh_after_edit()
        self._status_bar.showMessage(f"{len(source_indices)}개 페이지 삽입 완료", 3000)
        self._update_undo_actions(tab)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"삽입 실패:\n{e}")

def _refresh_after_edit(self) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    current = tab.viewer.current_page
    self._page_panel.reload_all()
    target = min(current, tab.doc.page_count - 1)
    tab.viewer.goto_page(max(0, target))
    self._update_page_status(tab.viewer.current_page)
```

- [ ] **Step 4: 어노테이션·Undo/Redo 메서드 교체**

```python
def _on_tool_changed(self, tool: AnnotationTool) -> None:
    tab = self._active_tab()
    if tab:
        tab.viewer.set_tool(tool)
    self._toolbar.set_text_tool_active(tool == AnnotationTool.TEXT)
    tool_names = {
        AnnotationTool.SELECT:  "선택",
        AnnotationTool.TEXT:    "텍스트",
        AnnotationTool.RECT:    "사각형",
        AnnotationTool.ELLIPSE: "타원",
        AnnotationTool.LINE:    "선",
    }
    self._lbl_tool.setText(f"도구: {tool_names.get(tool, '')}")

def _on_color_changed(self, rgb: tuple) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    style = tab.viewer.annotation_style
    style.color = rgb
    tab.viewer.set_annotation_style(style)

def _on_width_changed(self, width: float) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    style = tab.viewer.annotation_style
    style.line_width = width
    tab.viewer.set_annotation_style(style)

def _on_text_font_changed(self, family: str) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    style = tab.viewer.annotation_style
    style.font_family = family
    tab.viewer.set_annotation_style(style)

def _on_text_size_changed(self, size: float) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    style = tab.viewer.annotation_style
    style.font_size = size
    tab.viewer.set_annotation_style(style)

def _on_text_bold_changed(self, bold: bool) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    style = tab.viewer.annotation_style
    style.bold = bold
    tab.viewer.set_annotation_style(style)

def _on_text_italic_changed(self, italic: bool) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    style = tab.viewer.annotation_style
    style.italic = italic
    tab.viewer.set_annotation_style(style)

def _on_annotation_requested(self, annotate_fn, description: str) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    cmd = AddAnnotationCommand(
        tab.doc.raw, tab.viewer.current_page, annotate_fn, description
    )
    tab.cmd_mgr.execute(cmd)
    tab.viewer.refresh_page()
    self._page_panel.reload_page(tab.viewer.current_page)
    self._status_bar.showMessage(f"{description} — Ctrl+Z로 취소 가능", 3000)
    tab.viewer.annotation_added.emit()
    self._update_undo_actions(tab)

def _undo(self) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    desc = tab.cmd_mgr.undo()
    if desc is None:
        return
    self._full_undo_redo_refresh()
    self._status_bar.showMessage(f"실행 취소: {desc}", 2000)
    self._update_undo_actions(tab)

def _redo(self) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    desc = tab.cmd_mgr.redo()
    if desc is None:
        return
    self._full_undo_redo_refresh()
    self._status_bar.showMessage(f"다시 실행: {desc}", 2000)
    self._update_undo_actions(tab)

def _full_undo_redo_refresh(self) -> None:
    self._refresh_after_edit()
    tab = self._active_tab()
    if tab:
        tab.viewer.refresh_page()

def _update_undo_actions(self, tab: PdfTabPage | None = None) -> None:
    if tab is None:
        tab = self._active_tab()
    can_undo = tab.cmd_mgr.can_undo if tab else False
    can_redo = tab.cmd_mgr.can_redo if tab else False
    self._act_undo.setEnabled(can_undo)
    self._act_redo.setEnabled(can_redo)
    u_desc = tab.cmd_mgr.undo_description if tab else None
    r_desc = tab.cmd_mgr.redo_description if tab else None
    self._act_undo.setText(f"실행 취소: {u_desc}(&Z)" if u_desc else "실행 취소(&Z)")
    self._act_redo.setText(f"다시 실행: {r_desc}(&Y)" if r_desc else "다시 실행(&Y)")
```

- [ ] **Step 5: 나머지 도구 메서드 교체 (rotate, merge, split, stamp, OCR, 최적화, 비교, 워터마크, 보안)**

```python
def _rotate_cw(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    page_editor.rotate_page(tab.doc.raw, tab.viewer.current_page, 90)
    self._refresh_after_edit()
    self._status_bar.showMessage("시계방향 90° 회전", 2000)

def _rotate_ccw(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    page_editor.rotate_page(tab.doc.raw, tab.viewer.current_page, -90)
    self._refresh_after_edit()
    self._status_bar.showMessage("반시계방향 90° 회전", 2000)

def _open_merge_dialog(self) -> None:
    paths, _ = QFileDialog.getOpenFileNames(
        self, "병합할 PDF 파일 선택", "", "PDF 파일 (*.pdf)"
    )
    if not paths or len(paths) < 2:
        return
    out_path, _ = QFileDialog.getSaveFileName(
        self, "병합 결과 저장", "", "PDF 파일 (*.pdf)"
    )
    if not out_path:
        return
    if not out_path.lower().endswith(".pdf"):
        out_path += ".pdf"
    try:
        from app.core.merger import merge_pdfs
        merge_pdfs(paths, out_path)
        self._status_bar.showMessage(f"병합 완료: {os.path.basename(out_path)}", 3000)
        reply = QMessageBox.question(
            self, "병합 완료", "병합된 PDF를 열겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._open_in_new_tab(out_path)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"병합 실패:\n{e}")

def _open_in_new_tab(self, path: str) -> None:
    try:
        self._tab_widget.open_pdf(path)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"파일을 열 수 없습니다:\n{e}")

def _open_split_dialog(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    from app.ui.dialogs.split_dialog import SplitDialog
    dlg = SplitDialog(self, page_count=tab.doc.page_count)
    if dlg.exec() != SplitDialog.DialogCode.Accepted:
        return
    out_dir = QFileDialog.getExistingDirectory(self, "분할 결과 저장 폴더")
    if not out_dir:
        return
    try:
        from app.core.merger import split_pdf
        kwargs = {}
        if dlg.split_mode() == "bookmark":
            kwargs["by_bookmarks"] = True
        else:
            kwargs["pages_per_split"] = dlg.pages_per_split()
        files = split_pdf(tab.doc.path, out_dir, **kwargs)
        self._status_bar.showMessage(f"분할 완료: {len(files)}개 파일", 3000)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"분할 실패:\n{e}")

def _open_stamp_dialog(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    from app.ui.dialogs.stamp_dialog import StampDialog
    import fitz
    dlg = StampDialog(self)
    if dlg.exec() != StampDialog.DialogCode.Accepted:
        return
    page = tab.doc.raw[tab.viewer.current_page]
    if dlg.is_text_stamp():
        from app.core.stamp import add_text_stamp
        center = fitz.Point(page.rect.width / 2, page.rect.height / 2)
        add_text_stamp(page, center, dlg.stamp_text(),
                       fontsize=dlg.fontsize(), rotate=dlg.rotation(),
                       opacity=dlg.opacity())
    elif dlg.image_path():
        from app.core.stamp import add_image_stamp
        add_image_stamp(page, fitz.Rect(100, 100, 300, 300), dlg.image_path())
    tab.viewer.refresh_page()
    self._page_panel.reload_page(tab.viewer.current_page)
    self._status_bar.showMessage("스탬프 추가됨", 2000)

def _open_ocr_dialog(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    from app.ui.dialogs.ocr_dialog import OcrDialog
    dlg = OcrDialog(self, page_count=tab.doc.page_count)
    if dlg.exec() != OcrDialog.DialogCode.Accepted:
        return
    try:
        from app.core.ocr_engine import add_ocr_layer
        out_path, _ = QFileDialog.getSaveFileName(self, "OCR 결과 저장", "", "PDF (*.pdf)")
        if out_path:
            add_ocr_layer(tab.doc.path, out_path, lang=dlg.language(), dpi=dlg.dpi())
            self._status_bar.showMessage("OCR 완료", 3000)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"OCR 실패:\n{e}")

def _open_optimize_dialog(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    from app.ui.dialogs.optimize_dialog import OptimizeDialog
    file_size = os.path.getsize(tab.doc.path) if tab.doc.path else 0
    dlg = OptimizeDialog(self, current_size=file_size)
    if dlg.exec() != OptimizeDialog.DialogCode.Accepted:
        return
    out_path, _ = QFileDialog.getSaveFileName(self, "최적화 결과 저장", "", "PDF (*.pdf)")
    if not out_path:
        return
    try:
        from app.core.optimizer import optimize_pdf
        optimize_pdf(tab.doc.path, out_path, preset=dlg.preset())
        new_size = os.path.getsize(out_path)
        self._status_bar.showMessage(f"최적화 완료: {new_size / 1024:.0f} KB", 3000)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"최적화 실패:\n{e}")

def _open_compare_dialog(self) -> None:
    from app.ui.dialogs.compare_dialog import CompareDialog
    tab = self._active_tab()
    current = tab.doc.path if tab and tab.doc.is_open else ""
    CompareDialog(self, current_path=current).exec()

def _open_watermark_dialog(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    from app.ui.dialogs.watermark_dialog import WatermarkDialog
    dlg = WatermarkDialog(self)
    if dlg.exec() != WatermarkDialog.DialogCode.Accepted:
        return
    out_path, _ = QFileDialog.getSaveFileName(self, "결과 저장", "", "PDF (*.pdf)")
    if not out_path:
        return
    try:
        if dlg.current_tab() == 0:
            from app.core.watermark import add_text_watermark
            add_text_watermark(tab.doc.path, out_path, dlg.watermark_text(),
                               opacity=dlg.opacity(), rotate=dlg.rotation(),
                               tile=dlg.is_tile())
        else:
            from app.core.watermark import add_header_footer
            add_header_footer(tab.doc.path, out_path, **dlg.header_footer_settings())
        self._status_bar.showMessage("적용 완료", 3000)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"실패:\n{e}")

def _open_security_dialog(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open:
        return
    from app.ui.dialogs.security_dialog import SecurityDialog
    dlg = SecurityDialog(self)
    if dlg.exec() != SecurityDialog.DialogCode.Accepted:
        return
    out_path, _ = QFileDialog.getSaveFileName(self, "암호화 저장", "", "PDF (*.pdf)")
    if not out_path:
        return
    try:
        from app.core.security import encrypt_pdf
        encrypt_pdf(tab.doc.path, out_path,
                    user_password=dlg.user_password(),
                    owner_password=dlg.owner_password(),
                    algorithm=dlg.algorithm(),
                    permissions=dlg.permissions())
        self._status_bar.showMessage("암호 설정 완료", 3000)
    except Exception as e:
        QMessageBox.critical(self, "오류", f"암호 설정 실패:\n{e}")

def _open_convert_dialog(self) -> None:
    from app.ui.dialogs.convert_dialog import ConvertDialog
    dlg = ConvertDialog(self)
    dlg.conversion_done.connect(self._open_converted_pdfs)
    dlg.exec()

def _open_converted_pdfs(self, output_paths: list) -> None:
    for path in output_paths:
        try:
            self._tab_widget.open_pdf(path)
        except Exception as exc:
            QMessageBox.critical(self, "오류", f"변환된 파일을 열 수 없습니다:\n{exc}")
```

- [ ] **Step 6: 이벤트 핸들러 교체**

```python
def _on_zoom_changed(self, zoom: float) -> None:
    self._lbl_zoom.setText(f"줌: {round(zoom * 100)}%")
    self._toolbar.update_zoom_display(zoom)

def _on_page_changed(self, page_idx: int) -> None:
    self._update_page_status(page_idx)
    self._page_panel.set_current_page(page_idx)

def _on_thumbnail_selected(self, page_idx: int) -> None:
    tab = self._active_tab()
    if tab:
        tab.viewer.goto_page(page_idx)

def _update_page_status(self, page_idx: int) -> None:
    tab = self._active_tab()
    total = tab.doc.page_count if tab and tab.doc.is_open else 0
    self._lbl_page.setText(f"페이지: {page_idx + 1} / {total}" if total else "페이지: -")

def _sync_annot_style(self) -> None:
    tab = self._active_tab()
    if tab is None:
        return
    style = AnnotationStyle(
        color=self._toolbar.current_annot_color,
        line_width=self._toolbar.current_annot_width,
        font_size=self._toolbar.current_font_size,
        font_family=self._toolbar.current_font_family,
        bold=self._toolbar.current_bold,
        italic=self._toolbar.current_italic,
    )
    tab.viewer.set_annotation_style(style)
```

- [ ] **Step 7: 검색 메서드 교체**

```python
def _toggle_search_bar(self) -> None:
    if self._search_bar is None:
        return
    if self._search_bar.isVisible():
        self._search_bar.close_bar()
        tab = self._active_tab()
        if tab:
            tab.search_results = []
            tab.search_idx = -1
            tab.search_query = ""
    else:
        self._search_bar.show()
        self._search_bar.focus_input()

def _on_search_requested(self, text: str) -> None:
    tab = self._active_tab()
    if tab is None or not tab.doc.is_open or not text:
        return
    try:
        from app.core.search_engine import SearchEngine
        engine = SearchEngine(tab.doc.path)
        tab.search_results = engine.search(
            text,
            case_sensitive=self._search_bar.is_case_sensitive(),
            whole_word=self._search_bar.is_whole_word(),
            regex=self._search_bar.is_regex(),
        )
        tab.search_query = text
        tab.search_idx = 0 if tab.search_results else -1
        self._search_bar.set_result_count(
            len(tab.search_results), max(0, tab.search_idx)
        )
        if tab.search_results:
            tab.viewer.goto_page(tab.search_results[0].page_idx)
        self._status_bar.showMessage(f"검색: {len(tab.search_results)}개 매칭", 2000)
    except Exception as e:
        self._status_bar.showMessage(f"검색 오류: {e}", 3000)

def _on_search_next(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.search_results:
        return
    tab.search_idx = (tab.search_idx + 1) % len(tab.search_results)
    self._search_bar.set_result_count(len(tab.search_results), tab.search_idx)
    tab.viewer.goto_page(tab.search_results[tab.search_idx].page_idx)

def _on_search_prev(self) -> None:
    tab = self._active_tab()
    if tab is None or not tab.search_results:
        return
    tab.search_idx = (tab.search_idx - 1) % len(tab.search_results)
    self._search_bar.set_result_count(len(tab.search_results), tab.search_idx)
    tab.viewer.goto_page(tab.search_results[tab.search_idx].page_idx)
```

- [ ] **Step 8: 드래그앤드롭 교체**

```python
def dragEnterEvent(self, event) -> None:
    if event.mimeData().hasUrls():
        urls = event.mimeData().urls()
        if any(u.toLocalFile().lower().endswith(".pdf") for u in urls):
            event.acceptProposedAction()

def dropEvent(self, event) -> None:
    urls = event.mimeData().urls()
    for url in urls:
        path = url.toLocalFile()
        if path.lower().endswith(".pdf"):
            self._open_in_new_tab(path)
            self._add_recent_file(path)

def handle_drop_file(self, path: str) -> None:
    self._open_in_new_tab(path)
    self._add_recent_file(path)
```

- [ ] **Step 9: `closeEvent`, 전체화면, 최근 파일 교체**

```python
def closeEvent(self, event) -> None:
    self._tab_widget.close_all()
    event.accept()

def toggle_fullscreen(self) -> None:
    if self._is_fullscreen:
        self.showNormal()
        self._toolbar.show()
        self._side_tabs.show()
        self._status_bar.show()
        self.menuBar().show()
        self._is_fullscreen = False
    else:
        self._toolbar.hide()
        self._side_tabs.hide()
        self._status_bar.hide()
        self.menuBar().hide()
        self.showFullScreen()
        self._is_fullscreen = True

def _add_recent_file(self, path: str) -> None:
    try:
        from app.services.settings import AppSettings
        settings = AppSettings()
        settings.add_recent_file(path)
        self._update_recent_menu()
    except Exception:
        pass

def _update_recent_menu(self) -> None:
    if self._recent_menu is None:
        return
    self._recent_menu.clear()
    try:
        from app.services.settings import AppSettings
        settings = AppSettings()
        recent = settings.get_recent_files()
        for path in recent[:10]:
            act = self._recent_menu.addAction(os.path.basename(path))
            act.setData(path)
            act.triggered.connect(lambda checked, p=path: self._open_in_new_tab(p))
        if not recent:
            self._recent_menu.addAction("(없음)").setEnabled(False)
    except Exception:
        self._recent_menu.addAction("(없음)").setEnabled(False)
```

- [ ] **Step 10: 전체 테스트 통과 확인**

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -30
```

예상 출력: 기존 테스트 대부분 PASSED (일부 `_doc`/`_viewer` 참조 테스트는 실패 — Task 6에서 정리)

- [ ] **Step 11: 커밋**

```bash
git add app/ui/main_window.py
git commit -m "feat: MainWindow 액션 핸들러 전체를 active_tab() 경유로 교체"
```

---

## Task 6: MainWindow — 탭 단축키 추가 및 기존 테스트 정리

**Files:**
- Modify: `app/ui/main_window.py` (메뉴에 탭 단축키 추가)
- Modify: `tests/ui/test_main_window.py` 등 (`_doc`/`_viewer` 직접 참조 제거)

- [ ] **Step 1: `_setup_menu`에 탭 관련 단축키 추가**

`_setup_menu` 내 파일 메뉴 부분에 다음을 추가한다:

```python
# 파일 메뉴 — 탭 닫기 / 재열기 추가
file_menu.addSeparator()
act_close_tab = file_menu.addAction("탭 닫기(&W)")
act_close_tab.setShortcut(QKeySequence("Ctrl+W"))
act_close_tab.triggered.connect(
    lambda: self._tab_widget.close_tab(self._tab_widget.currentIndex())
    if self._tab_widget.currentIndex() >= 0 else None
)
act_reopen = file_menu.addAction("마지막 탭 다시 열기(&T)")
act_reopen.setShortcut(QKeySequence("Ctrl+Shift+T"))
act_reopen.triggered.connect(self._tab_widget.reopen_last_closed)
```

보기 메뉴에 다음을 추가한다:

```python
# 보기 메뉴 — 탭 이동
view_menu.addSeparator()
act_next_tab = QAction("다음 탭", self)
act_next_tab.setShortcut(QKeySequence("Ctrl+Tab"))
act_next_tab.triggered.connect(self._next_tab)
view_menu.addAction(act_next_tab)

act_prev_tab = QAction("이전 탭", self)
act_prev_tab.setShortcut(QKeySequence("Ctrl+Shift+Tab"))
act_prev_tab.triggered.connect(self._prev_tab)
view_menu.addAction(act_prev_tab)

# Ctrl+1 ~ Ctrl+9
for i in range(1, 10):
    act = QAction(f"탭 {i}(&{i})", self)
    act.setShortcut(QKeySequence(f"Ctrl+{i}"))
    act.triggered.connect(lambda checked, n=i: self._goto_tab(n - 1))
    view_menu.addAction(act)
```

탭 이동 헬퍼 메서드를 추가한다:

```python
def _next_tab(self) -> None:
    n = self._tab_widget.count()
    if n < 2:
        return
    self._tab_widget.setCurrentIndex(
        (self._tab_widget.currentIndex() + 1) % n
    )

def _prev_tab(self) -> None:
    n = self._tab_widget.count()
    if n < 2:
        return
    self._tab_widget.setCurrentIndex(
        (self._tab_widget.currentIndex() - 1) % n
    )

def _goto_tab(self, index: int) -> None:
    if 0 <= index < self._tab_widget.count():
        self._tab_widget.setCurrentIndex(index)
```

편집 메뉴에 다음을 추가한다:

```python
edit_menu.addSeparator()
act_dup = QAction("탭 복제(&D)", self)
act_dup.setShortcut(QKeySequence("Ctrl+Shift+D"))
act_dup.triggered.connect(
    lambda: self._tab_widget.duplicate_tab(self._tab_widget.currentIndex())
)
edit_menu.addAction(act_dup)

act_detach = QAction("새 창으로 분리(&N)", self)
act_detach.setShortcut(QKeySequence("Ctrl+Shift+N"))
act_detach.triggered.connect(
    lambda: self._tab_widget.detach_tab(self._tab_widget.currentIndex())
)
edit_menu.addAction(act_detach)
```

- [ ] **Step 2: 기존 테스트에서 `_doc`/`_viewer` 직접 참조 수정**

`tests/ui/test_main_window.py`, `tests/ui/test_main_window_menu.py` 등에서
`main_window._doc`을 `main_window._tab_widget.active_tab().doc`으로,
`main_window._viewer`를 `main_window._tab_widget.active_tab().viewer`로 교체한다.

```bash
grep -rn "_doc\._\|_viewer\." tests/ui/ | grep -v test_pdf_tab
```

위 명령으로 수정이 필요한 줄을 모두 찾아 교체한다.

`tests/helpers.py`의 `load_pdf_directly` 함수도 확인하여 필요시 업데이트한다:

```bash
grep -n "load_pdf_directly\|_doc\|_viewer" tests/helpers.py
```

- [ ] **Step 3: 전체 테스트 통과 확인**

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -40
```

예상 출력: 모든 테스트 PASSED

- [ ] **Step 4: 커밋**

```bash
git add app/ui/main_window.py tests/
git commit -m "feat: 탭 단축키 추가 및 기존 테스트 _doc/_viewer 참조 수정"
```

---

## Task 7: CHANGE.md / README.md 업데이트 및 최종 확인

**Files:**
- Modify: `CHANGE.md`
- Modify: `README.md`

- [ ] **Step 1: CHANGE.md 업데이트**

`CHANGE.md` 최상단에 다음 섹션을 추가한다:

```markdown
## [미정] — 멀티 PDF 탭 기능

### 추가
- 멀티 탭 방식으로 여러 PDF 동시 열기 (`PdfTabPage`, `PdfTabWidget`)
- 탭 닫기(Ctrl+W), 복제(Ctrl+Shift+D), 분리(Ctrl+Shift+N)
- 최근 닫은 탭 재열기(Ctrl+Shift+T)
- 탭 전환(Ctrl+Tab / Ctrl+1~9)
- 탭 우클릭 컨텍스트 메뉴
- 탭 분리 창(`DetachedWindow`) — 탭으로 되돌리기 지원
- 드래그앤드롭으로 여러 PDF 각각 새 탭으로 열기
```

- [ ] **Step 2: 전체 테스트 최종 확인**

```bash
python -m pytest tests/ -v 2>&1 | tail -20
```

예상 출력: 전체 PASSED

- [ ] **Step 3: 최종 커밋**

```bash
git add CHANGE.md README.md
git commit -m "[Tabs] 멀티 PDF 탭 기능 완성 — CHANGE.md/README.md 업데이트"
```
