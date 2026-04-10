# E2E 테스트 구현 계획서 (최종 통합본)

> 작성일: 2026-04-03
> 최종 병합: 2026-04-03 (Test Architect + QA Lead 상호 검증 + QA 리뷰 10건 반영)
> 대상: jw_pdf v1.0.0
> 기반: TEST_SCENARIOS_FULL.md (TC-155~TC-166), USER_SCENARIOS.md (US-102~US-107)
> 도구: pytest 8.x + pytest-qt 4.4.x + PyQt6 offscreen

---

## 1. 전략 개요

### 1.1 테스트 수준: Hybrid (API-level 주도 + UI 검증 보조)

MainWindow 내부 API 호출을 주 경로로 사용하되, 위젯 상태 검증으로 UI 통합을 확인한다.

**이유**:
1. **offscreen 환경 제약**: `QT_QPA_PLATFORM=offscreen`에서 `QGraphicsView` 위의 마우스 이벤트 좌표 매핑이 불안정하다.
2. **모달 다이얼로그 제어**: `QFileDialog`, `QMessageBox` 등 네이티브 다이얼로그는 `monkeypatch`로 우회해야 한다.
3. **검증 정확도**: PDF 내용 검증은 `fitz`로 직접 확인하는 것이 UI 렌더링 비교보다 정확하다.

| 계층 | 방법 | 예시 |
|------|------|------|
| 문서 로딩 | `load_pdf_directly()` 헬퍼 | QFileDialog 우회 |
| 어노테이션 | `win._on_annotation_requested()` (E2E 표준) | 시그널 흐름 + 부수효과(refresh, undo 상태 갱신) 포함 |
| 어노테이션 (TC-166만) | `AddAnnotationCommand` 직접 생성 | Command 유형별 개별 검증 시에만 허용 |
| 상태 검증 | 위젯 속성 읽기 + fitz PDF 파싱 | `win._lbl_page.text()`, `fitz.open(path)` |
| Undo/Redo | `win._undo()` / `win._redo()` (E2E 표준) | UI 새로고침 부수효과 포함 |
| Undo/Redo (TC-166만) | `win._cmd_mgr.undo()` / `win._cmd_mgr.redo()` | core 계층 개별 검증 시에만 허용 |

### 1.2 범위

| 범위 | 포함 | 비고 |
|------|------|------|
| MainWindow 생성 + PDF 로드 | O | 모든 E2E 테스트의 기반 |
| 어노테이션 추가/저장/재열기 | O | TC-155, TC-158 |
| 페이지 편집(삽입/삭제/이동/추출) + Undo/Redo | O | TC-156, TC-157, TC-159, TC-166 |
| 다중 어노테이션 Undo/Redo 연속 | O | TC-160 |
| 메뉴 도구 전환 + 어노테이션 | O | TC-161, TC-163 |
| 상태바 종합 확인 | O | TC-162 |
| 문서 미열림 시 비활성화 | O | TC-164 |
| 도움말 > 정보 다이얼로그 | O | TC-165 |
| 이미지->PDF 변환 통합 | O | TC-158 (core 레벨) |
| QFileDialog 실제 파일 탐색기 | X | monkeypatch로 우회 |
| LibreOffice CLI 실제 호출 | X | mock 처리 |

### 1.3 기존 단위 테스트(155개)와의 관계

기존 테스트는 `app/core/` 계층과 개별 위젯을 독립적으로 검증한다. E2E 테스트는 **MainWindow를 진입점으로** 실제 시그널 흐름(toolbar -> main_window -> viewer/panel -> core)을 따라가므로, 단위 테스트와 상호 보완 관계에 있다.

### 1.4 테스트 격리 전략

```
원칙: 각 테스트는 자신만의 MainWindow와 임시 PDF를 생성/파괴한다.
```

- **tmp_path**: pytest 내장 픽스처. 테스트 종료 시 자동 정리.
- **MainWindow 생명주기**: `qtbot.addWidget(win)` 등록 + `yield` 후 `win.close()`.
- **PdfDocument 정리**: `closeEvent`에서 `_doc.close()` 호출되므로 MainWindow 닫으면 자동 정리.
- **CommandManager 격리**: 각 테스트에서 새 MainWindow 생성하므로 Undo 스택이 공유되지 않음.
- **QThread 정리**: teardown에서 `_cancel_loader()` 호출하여 썸네일 로더 스레드 행(hang) 방지.

---

## 2. 테스트 인프라 설계

### 2.1 추가 의존성

현재 `pyproject.toml`에 `pytest-qt>=4.4.0`이 이미 포함되어 있으므로 추가 패키지 불필요. `monkeypatch`, `tmp_path`, `qtbot`은 모두 기존 의존성으로 충분하다.

### 2.2 파일 구조

```
tests/
├── conftest.py              # 기존 공통 픽스처 (pdf_1page, pdf_3pages 등)
├── e2e/
│   ├── __init__.py
│   ├── conftest.py          # E2E 전용 픽스처 (main_window, pdf_factory 등)
│   ├── helpers.py           # load_pdf_directly, monkeypatch 헬퍼 함수
│   ├── test_tc155_save_reopen.py
│   ├── test_tc156_insert_annotate.py
│   ├── test_tc157_move_delete_undo.py
│   ├── test_tc158_convert_annotate.py
│   ├── test_tc159_extract_verify.py
│   ├── test_tc160_multi_undo_redo.py
│   ├── test_tc161_tool_switch.py
│   ├── test_tc162_status_bar.py
│   ├── test_tc163_menu_toolbar_sync.py
│   ├── test_tc164_disabled_without_doc.py
│   ├── test_tc165_about_dialog.py
│   ├── test_tc166_command_pattern.py
│   └── test_edge_cases.py   # TC-E01~E07 추가 시나리오
├── core/
│   └── ...
└── ui/
    └── ...
```

> **설계 결정**: TC 번호 기반 파일명 채택. 테스트 추적성이 높고, 특정 TC만 실행하기 편리하다.

### 2.3 E2E 전용 conftest.py

```python
# tests/e2e/conftest.py

import os
import fitz
import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def main_window(qtbot):
    """독립적인 MainWindow 인스턴스. 테스트 후 자동 정리.

    teardown 순서: _cancel_loader() -> close()
    _cancel_loader()를 먼저 호출하여 QThread가 fitz.Document를
    사용 중인 상태에서 close()가 호출되어 segfault가 발생하는 것을 방지한다.
    """
    from app.ui.main_window import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    yield win
    # 1) QThread 정리 — 썸네일 로더 스레드 hang/segfault 방지
    if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
        win._page_panel._cancel_loader()
    # 2) 윈도우 닫기 — closeEvent에서 _doc.close() 호출됨
    win.close()


@pytest.fixture
def pdf_factory(tmp_path):
    """다양한 조건의 테스트 PDF를 생성하는 팩토리 픽스처.

    매개변수:
        num_pages: 페이지 수
        rotations: {page_idx: degrees} 회전 설정
        with_annotations: 기본 어노테이션 포함 여부
        page_texts: 각 페이지에 삽입할 텍스트 리스트
    """
    def _create(
        num_pages: int = 3,
        *,
        rotations: dict[int, int] | None = None,
        with_annotations: bool = False,
        page_texts: list[str] | None = None,
    ) -> str:
        doc = fitz.open()
        for i in range(num_pages):
            page = doc.new_page(width=595, height=842)
            text = (page_texts[i] if page_texts and i < len(page_texts)
                    else f"Page {i + 1}")
            page.insert_text((72, 100), text, fontsize=24)

            if rotations and i in rotations:
                page.set_rotation(rotations[i])

            if with_annotations:
                page.draw_rect(fitz.Rect(50, 200, 200, 300), color=(1, 0, 0), width=2)

        path = str(tmp_path / f"test_{num_pages}p.pdf")
        doc.save(path)
        doc.close()
        return path

    return _create


@pytest.fixture
def image_factory(tmp_path):
    """테스트용 이미지 파일을 생성하는 팩토리."""
    from PIL import Image

    def _create(name: str = "test.png", size=(200, 150), color=(100, 149, 237)) -> str:
        path = str(tmp_path / name)
        Image.new("RGB", size, color=color).save(path)
        return path

    return _create
```

> **설계 결정**: 팩토리 패턴 채택 (QA Lead 방식). 개별 픽스처(`pdf_1page`, `png_images_3`)보다 유연하며, 테스트 내에서 다양한 조건의 PDF/이미지를 즉석 생성할 수 있다.

### 2.4 load_pdf_directly 헬퍼

```python
# tests/e2e/helpers.py

import os
from app.core.annotator import AnnotationTool


def load_pdf_directly(win, path: str) -> None:
    """QFileDialog 없이 MainWindow에 PDF를 직접 로드한다.

    MainWindow._open_file()의 핵심 로직을 재현하되,
    QFileDialog 호출과 에러 다이얼로그를 생략한다.
    """
    win._doc.open(path)
    win._cmd_mgr.clear()
    win._page_panel.load_document(win._doc)
    win._viewer.set_document(win._doc)
    win._toolbar.set_document_loaded(True)
    win._toolbar.set_tool_checked(AnnotationTool.SELECT)
    win._update_page_status(0)
    win._toolbar.update_zoom_display(win._viewer.zoom)
    win._lbl_file.setText(os.path.basename(path))
    win._update_undo_actions()
    win._sync_annot_style()
```

> **설계 결정**: QFileDialog monkeypatch 대신 직접 로딩 헬퍼 사용 (QA Lead 방식). 테스트가 UI 구현 세부사항에 덜 의존하고, `_lbl_file` 설정 등 누락 가능한 부분을 명시적으로 제어한다.

### 2.5 monkeypatch 헬퍼 함수

> **규칙**: 모든 모킹은 `monkeypatch.setattr`을 사용한다. `unittest.mock.patch`/`MagicMock`은 사용하지 않는다 (pytest 네이티브 일관성).

```python
# tests/e2e/helpers.py에 추가

from PyQt6.QtWidgets import QMessageBox


def mock_open_dialog(monkeypatch, return_path: str):
    """QFileDialog.getOpenFileName을 고정 경로로 모킹."""
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getOpenFileName",
        lambda *a, **kw: (return_path, "PDF 파일 (*.pdf)")
    )


def mock_save_dialog(monkeypatch, return_path: str):
    """QFileDialog.getSaveFileName을 고정 경로로 모킹."""
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getSaveFileName",
        lambda *a, **kw: (return_path, "PDF 파일 (*.pdf)")
    )


def mock_confirm_yes(monkeypatch):
    """QMessageBox.question을 항상 Yes로 모킹."""
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.Yes
    )


def mock_confirm_no(monkeypatch):
    """QMessageBox.question을 항상 No로 모킹."""
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.No
    )


class _FakeInsertDialog:
    """InsertDialog 대체용. MagicMock 대신 명시적 클래스 사용."""

    def __init__(self, source_path: str, indices: list[int]):
        self._source_path = source_path
        self._indices = indices

    def exec(self):
        return 1  # QDialog.DialogCode.Accepted

    def source_path(self):
        return self._source_path

    def selected_indices(self):
        return self._indices


def mock_insert_dialog(monkeypatch, source_path: str, indices: list[int]):
    """InsertDialog를 모킹하여 특정 소스/인덱스를 반환."""
    fake = _FakeInsertDialog(source_path, indices)
    monkeypatch.setattr(
        "app.ui.main_window.InsertDialog",
        lambda parent: fake
    )


def mock_text_input(monkeypatch, text: str = "테스트 텍스트"):
    """QInputDialog.getText를 고정 텍스트로 모킹."""
    monkeypatch.setattr(
        "app.ui.pdf_viewer.QInputDialog.getText",
        lambda *a, **kw: (text, True)
    )
```

### 2.6 테스트 데이터 전략

| 데이터 | 생성 방법 | 픽스처 |
|--------|----------|--------|
| N페이지 PDF | `pdf_factory(num_pages=N)` | `pdf_factory` |
| 텍스트 포함 PDF | `pdf_factory(page_texts=["A", "B"])` | `pdf_factory` |
| 회전 페이지 PDF | `pdf_factory(rotations={0: 90})` | `pdf_factory` |
| 기존 어노테이션 PDF | `pdf_factory(with_annotations=True)` | `pdf_factory` |
| PNG 이미지 | `image_factory("name.png")` | `image_factory` |
| 저장/추출 결과 | `str(tmp_path / "output.pdf")` | 테스트 내 인라인 |

> **절대 하드코딩 경로 사용 금지** (프로젝트 규칙 준수).

---

## 3. E2E 테스트 케이스 상세 설계

### 3.1 TC-155: 열기 -> 어노테이션 -> 저장 -> 재열기

**접근**: API-level. `_on_annotation_requested()` 경유로 어노테이션 추가 -> 저장 -> fitz로 재열기하여 내용 검증.

**함정/리스크**:
- 저장 시 incremental save vs full save 경로 차이. 같은 경로에 쓰면 파일 잠금 주의.
- 어노테이션은 content stream에 직접 기록되므로 `page.get_drawings()`로 검증 가능.
- **동일 경로 저장 후 재열기**: `_doc.close()` -> `_doc.open()` 순서 중요. 파일 핸들 해제 전 열기 시도하면 실패.
- **거짓 양성 방지**: `pdf_factory(with_annotations=True)`로 생성한 PDF는 이미 drawings를 포함하므로, 어노테이션 검증 시 반드시 추가 전/후의 **상대적 비교**를 사용해야 한다. `len(drawings) > 0`은 거짓 양성을 유발한다.

```python
# tests/e2e/test_tc155_save_reopen.py

import fitz
from app.core.annotator import AnnotationStyle, add_text, add_rect, add_ellipse
from tests.e2e.helpers import load_pdf_directly


class TestTC155:
    """TC-155: PDF 열기 -> 어노테이션 추가 -> 저장 -> 재열기 확인."""

    def test_annotations_persist_after_save_and_reopen(
        self, main_window, pdf_factory, tmp_path
    ):
        win = main_window
        original_path = pdf_factory(num_pages=2)
        save_path = str(tmp_path / "annotated.pdf")

        # 1) 문서 로드
        load_pdf_directly(win, original_path)
        assert win._doc.is_open
        assert win._doc.page_count == 2

        # 2) 어노테이션 추가 전 drawings/text 기록 (상대적 비교용)
        page_idx = 0
        before_drawings = len(win._doc.raw[page_idx].get_drawings())
        before_text = win._doc.raw[page_idx].get_text()

        # 3) 텍스트 어노테이션 추가 (_on_annotation_requested 경유)
        style = AnnotationStyle(color=(1.0, 0.0, 0.0))

        def annotate_text():
            add_text(win._doc.raw[page_idx], 100, 200, "E2E Test", style)

        win._on_annotation_requested(annotate_text, "텍스트 추가")

        # 4) 사각형 어노테이션 추가
        def annotate_rect():
            add_rect(win._doc.raw[page_idx], 50, 300, 200, 400, style)

        win._on_annotation_requested(annotate_rect, "사각형 추가")

        # 5) 다른 이름으로 저장
        win._doc.save(save_path)

        # 6) 재열기하여 어노테이션 존재 확인 (fitz 직접 사용)
        verify_doc = fitz.open(save_path)
        try:
            page = verify_doc[0]

            # 상대적 비교: 추가 전보다 drawings가 증가했는지 확인 (거짓 양성 방지)
            after_drawings = len(page.get_drawings())
            assert after_drawings > before_drawings, \
                f"사각형 어노테이션 미반영: before={before_drawings}, after={after_drawings}"

            # 텍스트 어노테이션은 고유 문자열로 검증 (거짓 양성 없음)
            assert "E2E Test" in page.get_text(), "텍스트 어노테이션이 저장되지 않았음"
            assert "E2E Test" not in before_text, "테스트 전제 실패: 이미 텍스트가 존재"
        finally:
            verify_doc.close()

    def test_rect_and_ellipse_persist(self, main_window, pdf_factory, tmp_path):
        """사각형 + 타원 어노테이션이 저장/재열기 후에도 유지되는지 확인."""
        win = main_window
        path = pdf_factory(num_pages=1)
        save_path = str(tmp_path / "shapes.pdf")

        load_pdf_directly(win, path)

        style = AnnotationStyle()
        page_idx = 0
        before_drawings = len(win._doc.raw[page_idx].get_drawings())

        def add_rect_fn():
            add_rect(win._doc.raw[page_idx], 50, 50, 200, 150, style)

        def add_ellipse_fn():
            add_ellipse(win._doc.raw[page_idx], 250, 50, 450, 200, style)

        win._on_annotation_requested(add_rect_fn, "사각형")
        win._on_annotation_requested(add_ellipse_fn, "타원")

        win._doc.save(save_path)

        doc2 = fitz.open(save_path)
        try:
            after_drawings = len(doc2[page_idx].get_drawings())
            assert after_drawings >= before_drawings + 2, \
                f"사각형+타원 미반영: before={before_drawings}, after={after_drawings}"
        finally:
            doc2.close()
```

> **접근 선택 이유**: `_on_annotation_requested()` 경유를 E2E 표준으로 채택. 실제 시그널 흐름(viewer -> main_window -> command_manager -> refresh)을 따르므로 부수효과(refresh_page, _update_undo_actions 등)까지 검증된다. drawings 검증은 상대적 비교(`after > before`)로 거짓 양성을 방지한다.

---

### 3.2 TC-156: 삽입 -> 삽입 페이지에 어노테이션 -> 저장

**접근**: `InsertPagesCommand` 직접 실행. InsertDialog는 우회.

**함정/리스크**:
- 페이지 삽입 후 인덱스 변화에 주의. 0번 앞에 2페이지 삽입 시 기존 0번은 2번으로 이동.
- 삽입된 페이지에 어노테이션 추가 시 `win._doc.raw[삽입된_인덱스]`가 정확해야 함.

```python
# tests/e2e/test_tc156_insert_annotate.py

import fitz
from app.core.annotator import AnnotationStyle, add_rect
from app.core.command_manager import InsertPagesCommand
from tests.e2e.helpers import load_pdf_directly


class TestTC156:
    """TC-156: 페이지 삽입 -> 삽입된 페이지에 어노테이션 -> 저장."""

    def test_annotation_on_inserted_page_persists(
        self, main_window, pdf_factory, tmp_path
    ):
        win = main_window
        main_pdf = pdf_factory(num_pages=2, page_texts=["Main1", "Main2"])
        source_pdf = pdf_factory(num_pages=3, page_texts=["Src1", "Src2", "Src3"])
        save_path = str(tmp_path / "inserted_annotated.pdf")

        load_pdf_directly(win, main_pdf)

        # 1) 페이지 삽입 (source의 0번 페이지를 main의 1번 앞에)
        cmd = InsertPagesCommand(win._doc.raw, source_pdf, [0], insert_before=1)
        win._cmd_mgr.execute(cmd)
        assert win._doc.raw.page_count == 3  # 2 + 1

        # 2) 삽입된 페이지(idx=1)에 어노테이션 추가
        style = AnnotationStyle(color=(0.0, 0.0, 1.0))
        inserted_idx = 1
        before_drawings = len(win._doc.raw[inserted_idx].get_drawings())

        def annotate():
            add_rect(win._doc.raw[inserted_idx], 50, 50, 200, 150, style)

        win._on_annotation_requested(annotate, "사각형")

        # 3) 저장 및 검증
        win._doc.save(save_path)

        verify_doc = fitz.open(save_path)
        try:
            assert verify_doc.page_count == 3
            inserted_page = verify_doc[1]
            assert len(inserted_page.get_drawings()) > before_drawings, \
                "삽입된 페이지에 어노테이션이 반영되지 않았음"
            assert "Src1" in inserted_page.get_text()
        finally:
            verify_doc.close()
```

> **접근 선택 이유**: `page_texts` 파라미터로 삽입된 페이지 내용까지 검증. `_on_annotation_requested()` 경유로 E2E 시그널 흐름을 따르며, drawings는 상대적 비교로 거짓 양성 방지.

---

### 3.3 TC-157: 순서변경 -> 삭제 -> Undo x 2

**접근**: `CommandManager`를 직접 사용. 각 단계에서 페이지 텍스트 비교로 상태 검증.

**함정/리스크**:
- `MovePageCommand`의 `to` 인덱스는 fitz의 `move_page(from, to)` 의미를 따름.
- Undo 후 페이지 텍스트가 원본과 정확히 일치하는지 검증. 단순 page_count로는 부족.
- **DeletePagesCommand의 Undo**가 페이지 내용을 스냅샷에서 복원하므로 텍스트 검증이 핵심.

```python
# tests/e2e/test_tc157_move_delete_undo.py

from app.core.command_manager import MovePageCommand, DeletePagesCommand
from tests.e2e.helpers import load_pdf_directly


class TestTC157:
    """TC-157: 페이지 순서변경 -> 삭제 -> Undo x2 -> 원래 상태 복원."""

    def test_double_undo_restores_original(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=5,
                          page_texts=["P1", "P2", "P3", "P4", "P5"])
        load_pdf_directly(win, path)

        def get_texts():
            return [win._doc.raw[i].get_text().strip()
                    for i in range(win._doc.raw.page_count)]

        original_texts = get_texts()

        # 1) 1페이지(idx=0)를 3번째(to=2)로 이동
        cmd_move = MovePageCommand(win._doc.raw, 0, 2)
        win._cmd_mgr.execute(cmd_move)
        win._refresh_after_edit()
        assert get_texts() != original_texts  # 순서 변경됨

        # 2) 현재 2번째 페이지(idx=1) 삭제
        cmd_del = DeletePagesCommand(win._doc.raw, [1])
        win._cmd_mgr.execute(cmd_del)
        win._refresh_after_edit()
        assert win._doc.raw.page_count == 4

        # 3) Undo (삭제 취소) — win._undo()로 UI 새로고침 포함
        win._undo()
        assert win._doc.raw.page_count == 5

        # 4) Undo (이동 취소)
        win._undo()
        assert get_texts() == original_texts  # 원본 복원 확인
```

---

### 3.4 TC-158: 이미지 -> PDF 변환 -> 열기 -> 어노테이션 -> 저장

**접근**: `converter.convert_images_to_pdf()` 직접 호출 -> 결과 PDF 로드 -> 어노테이션 추가 -> 저장 검증. ConvertDialog는 우회.

**함정/리스크**:
- 이미지 변환 결과 PDF는 각 이미지가 1페이지. 페이지 크기가 이미지 크기와 다를 수 있음.
- 변환된 PDF에 어노테이션 좌표가 유효한지 확인 필요.

```python
# tests/e2e/test_tc158_convert_annotate.py

import os
import fitz
from app.core.converter import convert_images_to_pdf
from app.core.annotator import AnnotationStyle, add_text, add_rect
from tests.e2e.helpers import load_pdf_directly


class TestTC158:
    """TC-158: 이미지 -> PDF 변환 -> 열기 -> 어노테이션 -> 저장."""

    def test_converted_pdf_accepts_annotations(
        self, main_window, image_factory, tmp_path
    ):
        win = main_window
        img1 = image_factory("img1.png", color=(200, 100, 50))
        img2 = image_factory("img2.png", color=(50, 200, 100))
        img3 = image_factory("img3.png", color=(100, 50, 200))
        converted_path = str(tmp_path / "converted.pdf")
        save_path = str(tmp_path / "annotated_converted.pdf")

        # 1) 이미지 -> PDF 변환
        convert_images_to_pdf([img1, img2, img3], converted_path)
        assert os.path.exists(converted_path)

        # 2) 변환된 PDF 열기
        load_pdf_directly(win, converted_path)
        assert win._doc.page_count == 3

        # 3) 어노테이션 추가 (_on_annotation_requested 경유)
        style = AnnotationStyle()

        def annotate():
            add_text(win._doc.raw[0], 50, 50, "Converted!", style)

        win._on_annotation_requested(annotate, "텍스트")

        # 4) 저장 및 검증
        win._doc.save(save_path)

        verify_doc = fitz.open(save_path)
        try:
            assert verify_doc.page_count == 3
            assert "Converted!" in verify_doc[0].get_text()
        finally:
            verify_doc.close()
```

---

### 3.5 TC-159: 페이지 추출 -> 추출 PDF 열기 -> 내용 확인

**접근**: `page_editor.extract_pages()` 직접 호출 -> 추출된 PDF를 fitz로 열어 내용 비교.

**함정/리스크**:
- 추출 시 인덱스가 0-based인지 확인.
- 추출된 PDF의 페이지 순서가 입력 인덱스 순서를 따르는지 검증.
- 원본 PDF가 변경되지 않았는지도 확인.

```python
# tests/e2e/test_tc159_extract_verify.py

import fitz
from app.core import page_editor
from tests.e2e.helpers import load_pdf_directly


class TestTC159:
    """TC-159: 페이지 추출 -> 추출된 PDF 열기 -> 내용 확인."""

    def test_extracted_pdf_contains_correct_pages(
        self, main_window, pdf_factory, tmp_path
    ):
        win = main_window
        path = pdf_factory(num_pages=5,
                          page_texts=["Alpha", "Beta", "Gamma", "Delta", "Epsilon"])
        extract_path = str(tmp_path / "extracted.pdf")

        load_pdf_directly(win, path)

        # 1) 2~4페이지(idx 1,2,3) 추출
        page_editor.extract_pages(win._doc.raw, [1, 2, 3], extract_path)

        # 2) 추출된 PDF 검증
        extracted = fitz.open(extract_path)
        try:
            assert extracted.page_count == 3
            assert "Beta" in extracted[0].get_text()
            assert "Gamma" in extracted[1].get_text()
            assert "Delta" in extracted[2].get_text()
        finally:
            extracted.close()

        # 3) 원본은 변경되지 않았는지 확인
        assert win._doc.raw.page_count == 5

    def test_extract_single_page_content(self, main_window, pdf_factory, tmp_path):
        """단일 페이지 추출 후 내용 일치 확인."""
        win = main_window
        path = pdf_factory(num_pages=5, page_texts=["A", "B", "C", "D", "E"])
        extract_path = str(tmp_path / "single.pdf")

        load_pdf_directly(win, path)
        original_text = win._doc.raw[2].get_text().strip()

        page_editor.extract_pages(win._doc.raw, [2], extract_path)

        result = fitz.open(extract_path)
        try:
            assert result.page_count == 1
            assert result[0].get_text().strip() == original_text
        finally:
            result.close()
```

---

### 3.6 TC-160: 다중 어노테이션 -> 연속 Undo -> 연속 Redo

**접근**: 6개 어노테이션을 `_on_annotation_requested()` 경유로 추가 -> `win._undo()` 6회 -> `win._redo()` 6회. 각 단계에서 drawings 수 검증.

**함정/리스크**:
- `AddAnnotationCommand.undo()`는 페이지 스냅샷을 복원하므로 이전 어노테이션도 함께 사라짐.
- **핵심**: 6회 Undo 후 drawings가 초기값으로 복원되는지, 6회 Redo 후 원래 수인지 확인.
- 스냅샷 기반 Undo이므로 메모리 사용량이 큼 (테스트에서는 문제 없으나 실제로는 50개 제한).

```python
# tests/e2e/test_tc160_multi_undo_redo.py

from app.core.annotator import AnnotationStyle, add_rect, add_text, add_line
from tests.e2e.helpers import load_pdf_directly


class TestTC160:
    """TC-160: 다중 어노테이션 -> 연속 Undo -> 연속 Redo."""

    def test_six_annotations_full_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=1)
        load_pdf_directly(win, path)

        style = AnnotationStyle(color=(1, 0, 0))
        page_idx = 0

        initial_drawings = len(win._doc.raw[page_idx].get_drawings())

        # 사각형 3개 + 텍스트 2개 + 선 1개 = 6개 어노테이션
        annotations = [
            ("사각형1", lambda: add_rect(win._doc.raw[page_idx], 10, 10, 100, 100, style)),
            ("사각형2", lambda: add_rect(win._doc.raw[page_idx], 110, 10, 200, 100, style)),
            ("사각형3", lambda: add_rect(win._doc.raw[page_idx], 210, 10, 300, 100, style)),
            ("텍스트1", lambda: add_text(win._doc.raw[page_idx], 50, 200, "Text1", style)),
            ("텍스트2", lambda: add_text(win._doc.raw[page_idx], 50, 300, "Text2", style)),
            ("선1",     lambda: add_line(win._doc.raw[page_idx], 10, 400, 500, 400, style)),
        ]

        for desc, fn in annotations:
            win._on_annotation_requested(fn, desc)

        after_all = len(win._doc.raw[page_idx].get_drawings())
        assert after_all > initial_drawings

        # Undo 6회 -> 원래 상태 (win._undo()로 UI 새로고침 포함)
        for _ in range(6):
            assert win._cmd_mgr.can_undo
            win._undo()

        assert len(win._doc.raw[page_idx].get_drawings()) == initial_drawings
        assert not win._cmd_mgr.can_undo

        # Redo 6회 -> 다시 6개 어노테이션 상태
        for _ in range(6):
            assert win._cmd_mgr.can_redo
            win._redo()

        assert len(win._doc.raw[page_idx].get_drawings()) == after_all
        assert not win._cmd_mgr.can_redo
```

---

### 3.7 TC-161: 어노테이션 메뉴 도구 전환 후 작업 수행

**접근**: Hybrid. 툴바 QAction `trigger()`로 도구 전환 (UI 레벨) + 어노테이션 API 호출 + 상태 검증.

**함정/리스크**:
- `QActionGroup`의 배타적 체크 상태가 offscreen에서 정상 동작하는지 확인 필요.
- 도구 전환 후 커서 변경은 offscreen에서 검증 불가 -- 내부 상태(`_current_tool`)로 대체 검증.

```python
# tests/e2e/test_tc161_tool_switch.py

from app.core.annotator import AnnotationTool, AnnotationStyle, add_rect, add_ellipse
from tests.e2e.helpers import load_pdf_directly


class TestTC161:
    """TC-161: 어노테이션 메뉴에서 도구 전환 후 작업 수행."""

    def test_menu_tool_switch_enables_drawing(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=1)
        load_pdf_directly(win, path)

        style = AnnotationStyle()
        page_idx = 0

        # 1) 사각형 도구로 전환 (QAction trigger = 실제 메뉴 클릭 시뮬레이션)
        win._toolbar._tool_actions[AnnotationTool.RECT].trigger()
        assert win._viewer._current_tool == AnnotationTool.RECT

        # 2) 사각형 그리기
        def add_rect_fn():
            add_rect(win._doc.raw[page_idx], 50, 50, 200, 150, style)

        win._on_annotation_requested(add_rect_fn, "사각형")
        drawings_after_rect = len(win._doc.raw[page_idx].get_drawings())
        assert drawings_after_rect > 0

        # 3) 타원 도구 전환
        win._toolbar._tool_actions[AnnotationTool.ELLIPSE].trigger()
        assert win._viewer._current_tool == AnnotationTool.ELLIPSE

        # 4) 타원 그리기
        def add_ellipse_fn():
            add_ellipse(win._doc.raw[page_idx], 250, 50, 450, 200, style)

        win._on_annotation_requested(add_ellipse_fn, "타원")
        drawings_after_ellipse = len(win._doc.raw[page_idx].get_drawings())
        assert drawings_after_ellipse > drawings_after_rect

        # 5) 선택 도구 복귀
        win._toolbar._tool_actions[AnnotationTool.SELECT].trigger()
        assert win._viewer._current_tool == AnnotationTool.SELECT
```

> **접근 선택 이유**: QAction `trigger()` + 실제 어노테이션 추가 (Test Architect 방식)를 채택. QA Lead의 `_on_tool_changed()` 직접 호출보다 UI 시그널 경로를 더 넓게 커버한다.

---

### 3.8 TC-162: 상태바 종합 확인

**접근**: 각 상태 변경 후 `_lbl_page`, `_lbl_zoom`, `_lbl_tool`, `_lbl_file` 텍스트 검증.

**함정/리스크**:
- `zoom_changed` 시그널이 비동기적으로 처리될 수 있음 -- `qtbot.waitSignal` 사용 고려.
- 상태바 텍스트에 한국어 포함. 부분 문자열 매칭 사용.

```python
# tests/e2e/test_tc162_status_bar.py

from app.core.annotator import AnnotationTool
from tests.e2e.helpers import load_pdf_directly


class TestTC162:
    """TC-162: 상태바 정보 종합 확인."""

    def test_statusbar_shows_page_info(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=5))
        assert "1 / 5" in win._lbl_page.text()

    def test_statusbar_updates_on_page_change(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=5))
        win._viewer.goto_page(3)
        assert "4 / 5" in win._lbl_page.text()

    def test_statusbar_shows_zoom(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))
        win._viewer.zoom_in()
        zoom_pct = round(win._viewer.zoom * 100)
        assert str(zoom_pct) in win._lbl_zoom.text()

    def test_statusbar_shows_tool_name(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))

        assert "선택" in win._lbl_tool.text()

        win._on_tool_changed(AnnotationTool.RECT)
        assert "사각형" in win._lbl_tool.text()

        win._on_tool_changed(AnnotationTool.TEXT)
        assert "텍스트" in win._lbl_tool.text()

    def test_statusbar_shows_filename(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))
        assert win._lbl_file.text() != ""
```

---

### 3.9 TC-163: 어노테이션 메뉴 도구 전환 + 툴바 동기화

**접근**: QAction `trigger()`로 도구 전환 -> `isChecked()` 상태 검증.

**함정/리스크**:
- 메뉴 -> 툴바 동기화는 `QActionGroup` 기반. 같은 QAction 객체를 공유하므로 자동 동기화.
- `isChecked()` 검증 시 `QActionGroup`의 exclusive 설정 확인.

```python
# tests/e2e/test_tc163_menu_toolbar_sync.py

from app.core.annotator import AnnotationTool
from tests.e2e.helpers import load_pdf_directly


class TestTC163:
    """TC-163: 어노테이션 메뉴 도구 전환 시 툴바 동기화."""

    def test_menu_action_syncs_toolbar(self, main_window, pdf_factory):
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))

        # 메뉴의 타원 액션을 직접 trigger
        ellipse_action = win._toolbar._tool_actions[AnnotationTool.ELLIPSE]
        ellipse_action.trigger()

        assert ellipse_action.isChecked()

        # 선택 액션으로 전환
        select_action = win._toolbar._tool_actions[AnnotationTool.SELECT]
        select_action.trigger()
        assert select_action.isChecked()
        assert not ellipse_action.isChecked()

    def test_all_tool_actions_are_exclusive(self, main_window, pdf_factory):
        """모든 도구 액션이 배타적 그룹에 속하는지 확인."""
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))

        for tool, action in win._toolbar._tool_actions.items():
            action.trigger()
            for other_tool, other_action in win._toolbar._tool_actions.items():
                if other_tool == tool:
                    assert other_action.isChecked()
                else:
                    assert not other_action.isChecked(), \
                        f"{tool} 활성 시 {other_tool}이 여전히 checked"
```

---

### 3.10 TC-164: 문서 미열림 시 편집 기능 비활성화

**접근**: MainWindow 생성 직후 (문서 로드 없이) 각 액션/버튼의 `isEnabled()` 확인. 가장 단순한 E2E 테스트.

```python
# tests/e2e/test_tc164_disabled_without_doc.py

from app.core.annotator import AnnotationTool


class TestTC164:
    """TC-164: 문서 미열림 상태에서 편집 기능 비활성화."""

    def test_actions_disabled_without_document(self, main_window):
        win = main_window

        # 저장 비활성
        assert not win._toolbar._act_save.isEnabled()

        # 페이지 편집 비활성
        assert not win._toolbar._act_delete.isEnabled()
        assert not win._toolbar._act_extract.isEnabled()
        assert not win._toolbar._act_insert.isEnabled()

        # Undo/Redo 비활성
        assert not win._act_undo.isEnabled()
        assert not win._act_redo.isEnabled()

    def test_annotation_tools_disabled_without_document(self, main_window):
        """어노테이션 도구 버튼이 비활성화 상태여야 합니다."""
        win = main_window
        for tool, action in win._toolbar._tool_actions.items():
            if tool != AnnotationTool.SELECT:
                assert not action.isEnabled(), \
                    f"문서 미열림 시 {tool} 도구가 활성화되어 있습니다"

    def test_open_button_is_enabled(self, main_window):
        """열기 버튼만 활성화 상태여야 합니다."""
        win = main_window
        assert win._toolbar._act_open.isEnabled()
```

---

### 3.11 TC-165: 도움말 > 정보 다이얼로그

**접근**: `QMessageBox.about`을 monkeypatch하여 호출 여부와 인자 검증.

**함정/리스크**:
- `QMessageBox.about`은 모달이므로 monkeypatch 없이 호출하면 블로킹.

```python
# tests/e2e/test_tc165_about_dialog.py


class TestTC165:
    """TC-165: 도움말 > 정보 다이얼로그."""

    def test_about_dialog_shows_app_info(self, main_window, monkeypatch):
        win = main_window
        called_with = {}

        def fake_about(parent, title, text):
            called_with["title"] = title
            called_with["text"] = text

        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.about",
            fake_about
        )

        win._show_about()

        assert "jw_pdf" in called_with["title"]
        assert "v" in called_with["text"]  # 버전 정보 포함
        assert "PyQt6" in called_with["text"]
```

> **접근 선택 이유**: `monkeypatch` 방식 채택 (QA Lead). `unittest.mock.patch` 대비 pytest 네이티브하고, 호출 인자를 명시적으로 캡처할 수 있어 가독성이 높다.

---

### 3.12 TC-166: Command 패턴 4종 Undo/Redo 순차 검증

**접근**: 4종 커맨드(Move, Delete, Insert, Annotation)를 개별 테스트 + 순차 통합 테스트로 분리. TC-166은 Command 유형별 개별 검증이 목적이므로 `AddAnnotationCommand` 직접 생성 + `_cmd_mgr.undo()`/`redo()` 직접 호출을 허용하는 유일한 TC이다. 순차 통합 테스트에서는 `win._undo()`를 사용한다.

**함정/리스크**:
- 가장 복잡한 테스트. 각 커맨드의 Undo/Redo를 독립적으로 검증한 후 순차 통합 검증.
- `InsertPagesCommand`에 source PDF 경로가 필요하므로 별도 PDF 생성.
- 순차 실행 시 이전 작업 결과가 다음에 영향을 줌.

```python
# tests/e2e/test_tc166_command_pattern.py

import fitz
from app.core.annotator import AnnotationStyle, add_rect
from app.core.command_manager import (
    AddAnnotationCommand,
    DeletePagesCommand,
    InsertPagesCommand,
    MovePageCommand,
)
from tests.e2e.helpers import load_pdf_directly


class TestTC166:
    """TC-166: Command 패턴 4종 Undo/Redo 순차 검증."""

    def _get_page_texts(self, doc):
        return [doc[i].get_text().strip() for i in range(doc.page_count)]

    def test_move_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=5, page_texts=["A", "B", "C", "D", "E"])
        load_pdf_directly(win, path)

        original = self._get_page_texts(win._doc.raw)

        cmd = MovePageCommand(win._doc.raw, 0, 3)
        win._cmd_mgr.execute(cmd)
        moved = self._get_page_texts(win._doc.raw)
        assert moved != original

        win._cmd_mgr.undo()
        assert self._get_page_texts(win._doc.raw) == original

        win._cmd_mgr.redo()
        assert self._get_page_texts(win._doc.raw) == moved

    def test_delete_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=5, page_texts=["A", "B", "C", "D", "E"])
        load_pdf_directly(win, path)

        cmd = DeletePagesCommand(win._doc.raw, [1])
        win._cmd_mgr.execute(cmd)
        assert win._doc.raw.page_count == 4

        win._cmd_mgr.undo()
        assert win._doc.raw.page_count == 5
        assert "B" in win._doc.raw[1].get_text()

        win._cmd_mgr.redo()
        assert win._doc.raw.page_count == 4

    def test_insert_undo_redo(self, main_window, pdf_factory):
        win = main_window
        main_path = pdf_factory(num_pages=3, page_texts=["M1", "M2", "M3"])
        source_path = pdf_factory(num_pages=2, page_texts=["S1", "S2"])
        load_pdf_directly(win, main_path)

        cmd = InsertPagesCommand(win._doc.raw, source_path, [0], insert_before=1)
        win._cmd_mgr.execute(cmd)
        assert win._doc.raw.page_count == 4

        win._cmd_mgr.undo()
        assert win._doc.raw.page_count == 3

        win._cmd_mgr.redo()
        assert win._doc.raw.page_count == 4
        assert "S1" in win._doc.raw[1].get_text()

    def test_annotation_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=1)
        load_pdf_directly(win, path)

        style = AnnotationStyle()
        initial_drawings = len(win._doc.raw[0].get_drawings())

        def annotate():
            add_rect(win._doc.raw[0], 10, 10, 100, 100, style)

        cmd = AddAnnotationCommand(win._doc.raw, 0, annotate, "사각형")
        win._cmd_mgr.execute(cmd)
        after_add = len(win._doc.raw[0].get_drawings())
        assert after_add > initial_drawings

        win._cmd_mgr.undo()
        assert len(win._doc.raw[0].get_drawings()) == initial_drawings

        win._cmd_mgr.redo()
        assert len(win._doc.raw[0].get_drawings()) == after_add

    def test_all_four_sequential_undo(self, main_window, pdf_factory):
        """4종 작업을 순차 실행 후 4회 Undo로 원상 복원."""
        win = main_window
        main_path = pdf_factory(num_pages=5, page_texts=["A", "B", "C", "D", "E"])
        source_path = pdf_factory(num_pages=2, page_texts=["S1", "S2"])
        load_pdf_directly(win, main_path)

        original_count = win._doc.raw.page_count
        original_texts = self._get_page_texts(win._doc.raw)
        original_drawings = len(win._doc.raw[0].get_drawings())

        # 1) 이동
        win._cmd_mgr.execute(MovePageCommand(win._doc.raw, 0, 2))
        win._refresh_after_edit()

        # 2) 삭제
        win._cmd_mgr.execute(DeletePagesCommand(win._doc.raw, [0]))
        win._refresh_after_edit()

        # 3) 삽입
        win._cmd_mgr.execute(
            InsertPagesCommand(win._doc.raw, source_path, [0], insert_before=0)
        )
        win._refresh_after_edit()

        # 4) 어노테이션
        style = AnnotationStyle()

        def add_fn():
            add_rect(win._doc.raw[0], 10, 10, 100, 100, style)

        cmd = AddAnnotationCommand(win._doc.raw, 0, add_fn, "사각형")
        win._cmd_mgr.execute(cmd)

        # 4회 Undo -> 원본 복원
        for _ in range(4):
            win._undo()

        assert win._doc.raw.page_count == original_count
        assert self._get_page_texts(win._doc.raw) == original_texts
```

---

## 4. 추가 E2E 시나리오 (엣지 케이스)

TC-155~TC-166 외에 자동화해야 할 통합 시나리오:

| ID | 시나리오 | 이유 |
|----|---------|------|
| TC-E01 | 대용량 PDF(50+ 페이지) 열기 + 썸네일 로딩 완료 대기 | 성능 회귀 감지 |
| TC-E02 | 회전(90/180/270) 페이지에 어노테이션 -> 저장 -> 좌표 검증 | 좌표 변환 통합 |
| TC-E03 | 페이지 삭제 후 마지막 페이지 접근 시 out-of-range 방지 | 경계 조건 |
| TC-E04 | 한글 텍스트 어노테이션 -> 저장 -> 재열기 -> 텍스트 확인 | 폰트 임베딩 통합 |
| TC-E05 | Undo 50회(최대) 초과 시 가장 오래된 커맨드 폐기 | Undo 스택 한계 |
| TC-E06 | 동일 경로 덮어쓰기 저장(incremental) -> 재열기 유효성 | 증분 저장 통합 |
| TC-E07 | 닫기(closeEvent) 시 리소스 정리 확인 | 메모리 누수 방지 |

```python
# tests/e2e/test_edge_cases.py

from app.core.annotator import AnnotationStyle, add_rect
from app.core.command_manager import AddAnnotationCommand, DeletePagesCommand
from tests.e2e.helpers import load_pdf_directly


class TestEdgeCases:
    """추가 E2E 시나리오."""

    def test_delete_until_one_page_left(self, main_window, pdf_factory):
        """TC-E03: 1페이지만 남을 때까지 삭제 시 에러 없이 동작."""
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=5))

        while win._doc.raw.page_count > 1:
            cmd = DeletePagesCommand(win._doc.raw, [0])
            win._cmd_mgr.execute(cmd)
            win._refresh_after_edit()
        assert win._doc.raw.page_count == 1

    def test_undo_stack_limit(self, main_window, pdf_factory):
        """TC-E05: 50개 초과 커맨드 시 가장 오래된 것이 폐기."""
        win = main_window
        load_pdf_directly(win, pdf_factory(num_pages=1))

        style = AnnotationStyle()
        for i in range(55):
            def add_fn(idx=i):
                add_rect(win._doc.raw[0], 10 + idx, 10, 50 + idx, 50, style)

            cmd = AddAnnotationCommand(win._doc.raw, 0, add_fn, f"사각형 {i}")
            win._cmd_mgr.execute(cmd)

        # 50회만 undo 가능 (최대 이력)
        undo_count = 0
        while win._cmd_mgr.can_undo:
            win._cmd_mgr.undo()
            undo_count += 1
        assert undo_count <= 50
```

---

## 5. 모달 다이얼로그 테스트 전략

### 5.1 대상 다이얼로그

| 다이얼로그 | 사용처 | 모킹 패치 경로 |
|-----------|--------|--------------|
| `QFileDialog.getOpenFileName` | PDF 열기 | `app.ui.main_window.QFileDialog.getOpenFileName` |
| `QFileDialog.getSaveFileName` | 저장/추출 | `app.ui.main_window.QFileDialog.getSaveFileName` |
| `QMessageBox.question` | 삭제 확인 | `app.ui.main_window.QMessageBox.question` |
| `QMessageBox.critical` | 오류 표시 | `app.ui.main_window.QMessageBox.critical` |
| `QMessageBox.about` | 정보 | `app.ui.main_window.QMessageBox.about` |
| `QInputDialog.getText` | 텍스트 입력 | `app.ui.pdf_viewer.QInputDialog.getText` |
| `InsertDialog.exec` | 삽입 설정 | `app.ui.main_window.InsertDialog` |

### 5.2 monkeypatch 패턴

> **규칙**: `unittest.mock.patch`/`MagicMock`은 사용하지 않는다. 모든 모킹은 pytest 네이티브 `monkeypatch.setattr`로 통일한다.

모든 다이얼로그 모킹 헬퍼는 `tests/e2e/helpers.py`에 정의 (2.5절 참조). 사용 예시:

```python
# QFileDialog 모킹 후 파일 열기 전체 경로 테스트
def test_open_file_via_menu(self, main_window, pdf_factory, monkeypatch):
    from tests.e2e.helpers import mock_open_dialog
    path = pdf_factory(num_pages=3)
    mock_open_dialog(monkeypatch, path)
    win = main_window
    win._open_file()
    assert win._doc.is_open
    assert win._doc.page_count == 3


# QMessageBox.question Yes 모킹 후 삭제
def test_delete_with_confirmation(self, main_window, pdf_factory, monkeypatch):
    from tests.e2e.helpers import load_pdf_directly, mock_confirm_yes
    win = main_window
    load_pdf_directly(win, pdf_factory(num_pages=5))
    mock_confirm_yes(monkeypatch)
    win._delete_pages([0])
    assert win._doc.page_count == 4
```

---

## 6. 비동기 테스트 전략

### 6.1 썸네일 백그라운드 로딩 대기

`PagePanel.load_document()`는 QThread에서 비동기로 썸네일을 렌더링한다.

```python
# 방법 1: 시그널 기반 대기 (썸네일 로딩 완료 시그널이 있는 경우)
with qtbot.waitSignal(win._page_panel.thumbnails_loaded, timeout=5000):
    load_pdf_directly(win, path)

# 방법 2 (추천): 아이템 수만 확인 (플레이스홀더 즉시 생성)
load_pdf_directly(win, path)
assert win._page_panel._list.count() == expected_page_count
```

> **추천**: 방법 2 사용. E2E 테스트의 관심사는 PDF 내용이지 썸네일 이미지가 아니다. teardown에서 `_cancel_loader()`를 호출하여 QThread 행 방지 (conftest에서 처리).

### 6.2 qtbot.waitSignal 활용 가이드

```python
# 기본 사용
with qtbot.waitSignal(widget.some_signal, timeout=3000) as blocker:
    widget.do_something()
assert blocker.args == [expected_value]

# 시그널이 발생하지 않아야 하는 경우
with qtbot.assertNotEmitted(widget.some_signal):
    widget.do_something_that_should_not_emit()
```

### 6.3 processEvents 주의사항

```python
from PyQt6.QtWidgets import QApplication
QApplication.processEvents()  # 시그널 딜리버리 보장
```

> **주의**: `processEvents()`를 남용하면 테스트가 비결정적이 된다. Direct connection인 경우 불필요.

---

## 7. 리스크 및 Flaky Test 방지

### 7.1 offscreen 환경 제약

| 제약 | 영향 | 대응 |
|------|------|------|
| 마우스 드래그 불안정 | QGraphicsView 좌표 매핑 불일치 | API-level 접근 |
| 렌더링 비교 불가 | 픽셀 단위 비교 불가능 | fitz PDF 내용 검증 |
| 네이티브 다이얼로그 실행 불가 | QFileDialog 등 블로킹 | monkeypatch 모킹 |
| 커서 변경 미반영 | setCursor() 확인만 가능 | 내부 상태 변수 검증 |
| DnD 불가 | 썸네일 패널 순서 변경 | `page_moved` 시그널 직접 emit |

### 7.2 Flaky Test 방지 방안

| 원인 | 방지 방안 |
|------|----------|
| 타이밍 의존 | `waitSignal` 사용, `sleep` 절대 금지 |
| QThread 경합 | 테스트 종료 시 `_cancel_loader()` 호출 |
| 전역 상태 오염 | 각 테스트에서 새 MainWindow 생성 |
| 파일 잠금 | `tmp_path` 사용, 명시적 `doc.close()` |
| 시그널 누락 | `timeout` 파라미터 명시 (기본 5000ms) |
| processEvents 타이밍 | Direct connection 사용, Queued 최소화 |

### 7.3 CI 환경 고려사항

```yaml
# GitHub Actions 예시
env:
  QT_QPA_PLATFORM: offscreen
  DISPLAY: ""
```

- **Windows CI**: offscreen 플러그인이 기본 포함. 추가 설정 불필요.
- **메모리**: AddAnnotationCommand 스냅샷이 페이지당 수십 KB. CI에서 문제 없음.
- **실행 시간**: 전체 E2E 12건이 30초 이내 완료되어야 함.

---

## 8. 구현 우선순위 및 로드맵

### Phase 1 (필수, 우선순위 상) -- 인프라 + 핵심 기능

| 순서 | TC | 파일 | 테스트 수 |
|------|------|------|---------|
| 1 | 인프라 | `e2e/conftest.py`, `e2e/helpers.py` | 0 (픽스처) |
| 2 | TC-164 | `test_tc164_disabled_without_doc.py` | 3 |
| 3 | TC-157 | `test_tc157_move_delete_undo.py` | 1 |
| 4 | TC-166 | `test_tc166_command_pattern.py` | 5 |
| 5 | TC-160 | `test_tc160_multi_undo_redo.py` | 1 |

> **이유**: TC-164는 가장 단순하여 인프라 검증에 적합. Command Undo/Redo는 핵심 기능.

### Phase 2 (필수, 우선순위 상) -- 저장/영속성

| 순서 | TC | 파일 | 테스트 수 |
|------|------|------|---------|
| 6 | TC-155 | `test_tc155_save_reopen.py` | 2 |
| 7 | TC-156 | `test_tc156_insert_annotate.py` | 1 |
| 8 | TC-159 | `test_tc159_extract_verify.py` | 2 |

### Phase 3 (보통, 우선순위 중) -- UI 상태/변환

| 순서 | TC | 파일 | 테스트 수 |
|------|------|------|---------|
| 9 | TC-161 | `test_tc161_tool_switch.py` | 1 |
| 10 | TC-163 | `test_tc163_menu_toolbar_sync.py` | 2 |
| 11 | TC-162 | `test_tc162_status_bar.py` | 5 |
| 12 | TC-165 | `test_tc165_about_dialog.py` | 1 |
| 13 | TC-158 | `test_tc158_convert_annotate.py` | 1 |

### Phase 4 (추가 시나리오)

| 순서 | TC | 테스트 수 |
|------|------|---------|
| 14 | TC-E01~E07 | 5~7 |

### 예상 총 테스트 수

| 분류 | 수 |
|------|-----|
| TC-155~TC-166 기반 | 25 |
| 추가 시나리오 (TC-E01~E07) | 7 |
| **합계** | **~32** |

---

## 9. 실행 명령

```bash
# E2E 테스트만 실행
uv run pytest tests/e2e/ -v --tb=short

# 전체 테스트 (기존 단위 + E2E)
uv run pytest tests/ -v

# 특정 TC만 실행
uv run pytest tests/e2e/test_tc155_save_reopen.py -v

# 실패 시 첫 실패에서 중단
uv run pytest tests/e2e/ -v -x

# 특정 테스트 함수 실행
uv run pytest tests/e2e/test_tc157_move_delete_undo.py -v -k "test_double_undo"
```

---

## 부록 A: 전체 테스트 매핑

| TC | US | 테스트 파일 | 테스트 함수 |
|----|-----|-----------|-----------|
| TC-155 | US-102 | `test_tc155_save_reopen.py` | `test_annotations_persist_after_save_and_reopen`, `test_rect_and_ellipse_persist` |
| TC-156 | US-103 | `test_tc156_insert_annotate.py` | `test_annotation_on_inserted_page_persists` |
| TC-157 | US-104 | `test_tc157_move_delete_undo.py` | `test_double_undo_restores_original` |
| TC-158 | US-105 | `test_tc158_convert_annotate.py` | `test_converted_pdf_accepts_annotations` |
| TC-159 | US-106 | `test_tc159_extract_verify.py` | `test_extracted_pdf_contains_correct_pages`, `test_extract_single_page_content` |
| TC-160 | US-107 | `test_tc160_multi_undo_redo.py` | `test_six_annotations_full_undo_redo` |
| TC-161 | US-058 | `test_tc161_tool_switch.py` | `test_menu_tool_switch_enables_drawing` |
| TC-162 | US-079 | `test_tc162_status_bar.py` | `test_statusbar_shows_page_info` 외 4개 |
| TC-163 | US-058 | `test_tc163_menu_toolbar_sync.py` | `test_menu_action_syncs_toolbar`, `test_all_tool_actions_are_exclusive` |
| TC-164 | US-080 | `test_tc164_disabled_without_doc.py` | `test_actions_disabled_without_document` 외 2개 |
| TC-165 | US-082 | `test_tc165_about_dialog.py` | `test_about_dialog_shows_app_info` |
| TC-166 | US-090 | `test_tc166_command_pattern.py` | `test_move_undo_redo` 외 4개 |

---

## 부록 B: 상호 검증 결과

### B.1 비교 대상

- **Test Architect 계획서** (원본 `E2E_TEST_PLAN.md`)
- **QA Lead 계획서** (`E2E_TEST_PLAN_QA.md`)
- **QA Lead 리뷰 결과** (`E2E_TEST_PLAN_QA.md` 하단 "상호 검증 리뷰 결과" 섹션)

### B.2 QA Lead 리뷰에서 발견된 문제 10건 및 해결

QA Lead가 Test Architect 계획서를 검토하여 발견한 문제점과 이 최종 통합본에서의 해결 내용:

| # | 심각도 | 발견 내용 | 해결 방법 | 반영 위치 |
|---|--------|----------|----------|----------|
| 1 | **CRITICAL** | `loaded_main_window` 픽스처에 `set_tool_checked(AnnotationTool.SELECT)`, `_lbl_file.setText()` 호출 누락. 실제 `_open_file()` 동작과 불일치 | `load_pdf_directly()` 헬퍼에 실제 `_open_file()`의 모든 단계를 정확히 재현 (`set_tool_checked`, `_lbl_file.setText`, `_update_undo_actions`, `_sync_annot_style` 포함) | 2.4절 `load_pdf_directly` |
| 2 | **CRITICAL** | TC-155의 `len(drawings) > 0` 검증은 `pdf_factory`의 기존 `draw_rect` 때문에 어노테이션 없이도 통과하는 거짓 양성(false positive) 발생 | 모든 drawings 검증을 상대적 비교(`after > before`)로 변경. 텍스트 어노테이션은 고유 문자열 검증 + 사전 부재 확인 | 3.1절 TC-155, 3.2절 TC-156 |
| 3 | **HIGH** | 어노테이션 추가 경로가 TC별로 불일치: `_on_annotation_requested()` vs `AddAnnotationCommand` 직접 생성 혼재. 부수효과(refresh, undo 상태 갱신) 누락 가능 | E2E 표준을 `_on_annotation_requested()`로 통일. TC-166만 Command 유형별 개별 검증 목적으로 `AddAnnotationCommand` 직접 사용 허용 | 1.1절 전략 표, 3.1/3.2/3.4/3.6절 |
| 4 | **HIGH** | QThread `_cancel_loader()` teardown 누락. QThread가 실행 중일 때 `fitz.Document`가 닫히면 segfault 발생 가능 | `main_window` 픽스처 teardown에 `_cancel_loader()` -> `win.close()` 순서 명시. 주석으로 호출 순서의 이유 설명 | 2.3절 conftest.py |
| 5 | **MEDIUM** | `unittest.mock.patch`와 `monkeypatch` 혼용. TC-165에서 `from unittest.mock import patch` 사용 | 모든 모킹을 `monkeypatch.setattr`로 통일. `unittest.mock.patch`/`MagicMock` 사용 금지 규칙 추가 | 2.5절 규칙, 3.11절 TC-165, 5.2절 |
| 6 | **MEDIUM** | Undo/Redo 호출이 `_cmd_mgr.undo()`와 `win._undo()` 혼용. `_cmd_mgr.undo()`는 UI 새로고침 부수효과가 없어 실제 앱 동작과 괴리 | E2E 표준을 `win._undo()`/`win._redo()`로 통일. TC-166 개별 테스트만 `_cmd_mgr.undo()`/`redo()` 허용 | 1.1절 전략 표, 3.3/3.6절 |
| 7 | **MEDIUM** | fitz.Document 검증 시 테스트 실패하면 `close()`가 호출되지 않아 Windows 파일 잠금 발생 가능 | 모든 fitz 검증 코드를 `try/finally` 패턴으로 감싸서 안전한 close 보장 | 3.1/3.2/3.4/3.5절 |
| 8 | **MEDIUM** | InsertDialog 모킹에 `MagicMock` 사용. pytest 스타일과 불일치 | `_FakeInsertDialog` 명시적 클래스로 대체. `MagicMock` 의존성 제거 | 2.5절 헬퍼 |
| 9 | **LOW** | TC-157에서 `cmd_mgr.execute()` 후 `_refresh_after_edit()` 미호출이나 Undo 시 `_undo()`로 호출하는 비대칭 패턴 | execute 후 `_refresh_after_edit()` 명시적 호출 추가. Undo는 `win._undo()`로 통일 | 3.3절 TC-157 |
| 10 | **LOW** | `_make_pdf()` 기존 팩토리의 초기 drawings 수 문제. E2E용 `pdf_factory`는 `with_annotations=False`가 기본이나 검증 패턴이 절대값 비교 | `pdf_factory`의 기본 동작(`with_annotations=False`)은 drawings 미포함으로 유지. 검증은 상대적 비교로 통일하여 양쪽 모두 안전 | 2.3절 pdf_factory, 전체 TC |

### B.3 QA Lead 계획에서 병합한 강점

| 항목 | 병합 내용 | 이유 |
|------|----------|------|
| Hybrid 전략 명시 (1.1) | "API-level 주도 + UI 검증 보조" 전략과 근거를 도입 | offscreen 제약을 체계적으로 설명 |
| `pdf_factory` 팩토리 패턴 | rotations, with_annotations, page_texts 파라미터 지원 | 개별 픽스처(`pdf_1page` 등)보다 유연 |
| `image_factory` 팩토리 패턴 | 정적 픽스처 대신 팩토리 채택 | 테스트 내 이미지 조건 다양화 가능 |
| `load_pdf_directly` 헬퍼 (전체 `_open_file` 재현) | `_lbl_file.setText`, `_sync_annot_style` 등 누락 없는 완전한 재현 | Architect 버전의 불완전성 해소 |
| monkeypatch 전용 규칙 | `unittest.mock` 사용 금지, `monkeypatch.setattr` 통일 | pytest 네이티브 일관성 |
| 비동기 테스트 전략 (6절) | waitSignal, processEvents, QThread 정리 가이드 | Flaky test 방지에 필수 |
| per-TC "함정/리스크" | 각 TC에 함정/리스크 섹션 추가 | 구현 시 주의사항을 코드와 함께 제공 |
| CI 환경 고려사항 | GitHub Actions 설정, 메모리, 실행시간 가이드 | 실무 적용에 필요 |
| TC-156: `page_texts` 활용 | 삽입된 페이지의 텍스트 내용까지 검증 | 단순 page_count 비교보다 정확 |
| TC-159: 원본 미변경 검증 | 추출 후 원본 PDF가 그대로인지 확인 | 부작용 감지 |
| TC-165: monkeypatch 방식 | `unittest.mock.patch` 대신 pytest 네이티브 | 일관성 있는 테스트 스타일 |
| TC-166: 4종 독립 + 순차 통합 | 개별 검증 후 순차 통합 테스트 추가 | 독립/통합 양면 커버 |
| `e2e/conftest.py` 분리 | 루트 conftest 대신 E2E 전용 conftest | 기존 단위 테스트에 영향 없음 |
| Flaky test 방지 표 (7.2) | 원인별 방지 방안 정리 | 실무 체크리스트 역할 |

### B.4 Test Architect 계획에서 유지한 강점

| 항목 | 유지 내용 | 이유 |
|------|----------|------|
| 추가 시나리오 TC-E01~E07 | 엣지 케이스 7건 포함 | QA Lead 계획에 없던 경계 조건/성능 시나리오 |
| 구현 우선순위 로드맵 (Phase 1~4) | 단계별 구현 순서 유지 | 점진적 구현 가이드 |
| 세분화된 테스트 분리 | TC-162를 5개 테스트로 분리, TC-164를 3개로 분리 | 실패 시 원인 추적 용이 |
| `test_all_tool_actions_are_exclusive` | TC-163에 배타적 그룹 전수 검증 포함 | 모든 도구 조합 커버 |
| 전체 테스트 매핑 표 | TC -> US -> 파일 -> 함수 매핑 | 추적성 확보 |
| TC-161 실제 어노테이션 추가 | 도구 전환 후 실제 drawings 생성 검증 | QA Lead의 상태 변경만 확인하는 것보다 실질적 |

### B.5 식별된 모순 및 해결

| 모순 | Test Architect | QA Lead | 해결 |
|------|---------------|---------|------|
| 픽스처 위치 | 루트 `conftest.py`에 추가 | `e2e/conftest.py` 분리 | **QA Lead 채택** -- 기존 단위 테스트 격리 |
| 문서 로딩 방식 | `loaded_main_window` 픽스처 (불완전) | `main_window` + `load_pdf_directly` (완전) | **QA Lead 채택** -- 실제 `_open_file()` 전체 재현 |
| 어노테이션 경로 | `_on_annotation_requested()` / `AddAnnotationCommand` 혼재 | `AddAnnotationCommand` 직접 | **`_on_annotation_requested()` 표준화** (TC-166만 예외) |
| Undo/Redo 호출 | `_cmd_mgr.undo()` / `win._undo()` 혼재 | `_cmd_mgr.undo()` 직접 | **`win._undo()`/`_redo()` 표준화** (TC-166만 예외) |
| TC-161 도구 전환 | `_tool_actions[].trigger()` + 실제 그리기 | `_on_tool_changed()` 상태만 확인 | **TA 채택** -- UI 시그널 경로 + 실제 동작 검증 |
| 파일명 규칙 | 기능 설명 기반 (`test_annotation_save.py`) | TC 번호 기반 (`test_tc155_save_reopen.py`) | **QA Lead 채택** -- 추적성 우선 |
| TC-165 모킹 | `unittest.mock.patch` | `monkeypatch` | **QA Lead 채택** -- pytest 네이티브 일관성 |
| drawings 검증 | 절대값 (`> 0`) | 절대값 (`> 0`) | **양쪽 모두 수정** -- 상대적 비교 (`after > before`) |
| fitz 리소스 정리 | `doc.close()` 직접 호출 | 동일 | **양쪽 모두 수정** -- `try/finally` 패턴 적용 |
| QThread teardown | `_cancel_loader()` 포함 (불완전) | `_cancel_loader()` 언급만 | **양쪽 통합** -- 픽스처에 명시적 호출 + 주석 |

### B.6 양쪽 모두 누락된 블라인드 스팟

| 항목 | 설명 | 대응 |
|------|------|------|
| 다중 문서 열기/전환 | 문서 A 열기 -> 문서 B 열기 시 A가 정상 닫히는지 | TC-E08로 추가 고려 |
| 빈 PDF(0페이지) 처리 | 0페이지 PDF 열기 시 에러 처리 | TC-E09로 추가 고려 |
| 손상된 PDF 열기 | 잘못된 파일/깨진 PDF 열기 시 에러 다이얼로그 | TC-E10으로 추가 고려 |
| 매우 큰 어노테이션 좌표 | 페이지 범위 밖 좌표에 어노테이션 추가 시 동작 | TC-E11로 추가 고려 |
| 저장 실패 시나리오 | 읽기 전용 경로에 저장 시도 시 에러 처리 | TC-E12로 추가 고려 |
| 동시 Undo/Redo 비활성 | can_undo=False 시 `_undo()` 호출이 안전한지 | TC-166 내에서 assert로 이미 부분 커버 |

> 이 블라인드 스팟들은 Phase 4 이후에 검토한다. 현재 TC-155~TC-166 범위에서는 위 항목들이 범위 밖이지만, 프로덕션 품질을 위해 향후 추가를 권장한다.
