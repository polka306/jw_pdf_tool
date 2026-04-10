# E2E 테스트 구현 계획서 — QA Lead

> 작성일: 2026-04-03  
> 대상: jw_pdf v1.0.0  
> 범위: TC-155 ~ TC-166 (통합/E2E 테스트 12건)  
> 도구: pytest 8.x + pytest-qt 4.4.x + PyQt6 offscreen

---

## 1. E2E 테스트 전략

### 1.1 테스트 수준 정의: Hybrid (API-level 주도 + UI 검증 보조)

이 프로젝트는 **순수 UI 자동화(마우스 클릭/키보드 입력 시뮬레이션)가 아닌, MainWindow 내부 API 호출을 주 경로**로 사용한다. 이유는 다음과 같다:

1. **offscreen 환경 제약**: `QT_QPA_PLATFORM=offscreen`에서는 실제 디스플레이가 없으므로 `QGraphicsView` 위의 마우스 이벤트 좌표 매핑이 불안정하다.
2. **모달 다이얼로그 제어**: `QFileDialog`, `QMessageBox`, `QInputDialog`는 네이티브 다이얼로그를 사용하므로 `monkeypatch`로 우회해야 한다.
3. **검증 가능성**: PDF 내용 검증은 `fitz`로 직접 확인하는 것이 UI 렌더링 비교보다 100배 정확하다.

**전략 요약**:

| 계층 | 방법 | 예시 |
|------|------|------|
| 사용자 입력 | MainWindow 내부 메서드 직접 호출 | `win._open_file_from_path(path)` |
| 어노테이션 | `annotation_requested` 시그널 emit 또는 core API 직접 호출 | `annotator.add_rect(...)` |
| 상태 검증 | 위젯 속성 읽기 + fitz로 PDF 직접 파싱 | `win._lbl_page.text()`, `fitz.open(path)` |
| Undo/Redo | `win._undo()` / `win._redo()` 직접 호출 | |

### 1.2 테스트 격리 전략

```
원칙: 각 테스트는 자신만의 MainWindow와 임시 PDF를 생성/파괴한다.
```

- **tmp_path**: pytest 내장 `tmp_path` 픽스처 사용. 테스트 종료 시 자동 정리.
- **MainWindow 생명주기**: `qtbot.addWidget(win)` 등록 + `yield` 후 `win.close()`.
- **PdfDocument 정리**: `closeEvent`에서 `_doc.close()` 호출되므로 MainWindow 닫으면 자동 정리.
- **CommandManager 격리**: 각 테스트에서 새 MainWindow를 생성하므로 Undo 스택이 공유되지 않음.

---

## 2. 테스트 픽스처 설계

### 2.1 MainWindow-level 픽스처

```python
# tests/e2e/conftest.py

import os
import fitz
import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def main_window(qtbot):
    """독립적인 MainWindow 인스턴스. 테스트 후 자동 정리."""
    from app.ui.main_window import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    yield win
    win.close()
```

**핵심 포인트**: `qtbot.addWidget`은 위젯의 생명주기를 관리한다. `show()` 호출은 offscreen에서도 내부 레이아웃을 트리거하여 위젯 상태가 정상적으로 초기화된다.

### 2.2 문서 로딩 헬퍼 (QFileDialog 우회)

MainWindow의 `_open_file()`은 `QFileDialog.getOpenFileName()`을 호출한다. 테스트에서는 이를 우회해야 한다.

```python
def open_pdf_in_window(win, path: str, monkeypatch) -> None:
    """QFileDialog를 monkeypatch하여 지정 경로의 PDF를 MainWindow에 로드한다."""
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (path, "PDF 파일 (*.pdf)")
    )
    win._open_file()
```

**대안 (직접 로딩)**: QFileDialog를 우회하지 않고 MainWindow 내부 로직만 실행하는 헬퍼:

```python
def load_pdf_directly(win, path: str) -> None:
    """QFileDialog 없이 직접 문서를 로드한다. _open_file의 핵심 로직만 실행."""
    from app.core.annotator import AnnotationTool
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

> **추천**: `load_pdf_directly`를 사용한다. QFileDialog 모킹이 필요 없고, 테스트가 UI 구현 세부사항에 덜 의존한다.

### 2.3 PDF 문서 팩토리

```python
@pytest.fixture
def pdf_factory(tmp_path):
    """다양한 조건의 테스트 PDF를 생성하는 팩토리 픽스처."""

    def _create(
        num_pages: int = 3,
        *,
        rotations: dict[int, int] | None = None,   # {page_idx: degrees}
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

        path = str(tmp_path / f"test_{num_pages}p_{'ann' if with_annotations else 'plain'}.pdf")
        doc.save(path)
        doc.close()
        return path

    return _create
```

### 2.4 이미지 팩토리 (TC-158용)

```python
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

### 2.5 임시 파일 관리 전략

- `tmp_path` (pytest 내장): 테스트별 고유 임시 디렉토리. 자동 정리.
- PDF 저장 경로: `str(tmp_path / "output.pdf")`
- 추출/변환 결과: 동일 `tmp_path` 내에 저장하여 테스트 종료 시 일괄 삭제.
- **절대 하드코딩 경로 사용 금지** (프로젝트 규칙 준수).

---

## 3. 핵심 E2E 테스트 케이스

### TC-155: 열기 → 어노테이션 → 저장 → 재열기

**접근**: API-level. 문서 로드 → annotator API로 어노테이션 추가 → 저장 → fitz로 재열기하여 내용 검증.

**함정/리스크**:
- 저장 시 incremental save vs full save 경로 차이. `save()` (덮어쓰기)는 같은 경로에 쓰므로 파일 잠금 주의.
- 어노테이션은 content stream에 직접 기록되므로, 재열기 시 `page.get_drawings()`로 검증 가능.
- **동일 경로 저장 후 재열기**: `_doc.close()` → `_doc.open()` 순서가 중요. 파일 핸들 해제 전 열기 시도하면 실패.

```python
class TestTC155:
    """TC-155: PDF 열기 → 어노테이션 추가 → 저장 → 재열기 확인."""

    def test_annotations_persist_after_save_and_reopen(
        self, main_window, pdf_factory, tmp_path, qtbot
    ):
        win = main_window
        original_path = pdf_factory(num_pages=2)
        save_path = str(tmp_path / "annotated.pdf")

        # 1) 문서 로드
        load_pdf_directly(win, original_path)
        assert win._doc.is_open
        assert win._doc.page_count == 2

        # 2) 텍스트 어노테이션 추가 (Command 경유)
        from app.core.annotator import AnnotationStyle, add_text, add_rect
        style = AnnotationStyle(color=(1.0, 0.0, 0.0))

        page_idx = 0
        def annotate_text():
            add_text(win._doc.raw[page_idx], 100, 200, "E2E Test", style)

        from app.core.command_manager import AddAnnotationCommand
        cmd = AddAnnotationCommand(win._doc.raw, page_idx, annotate_text, "텍스트 추가")
        win._cmd_mgr.execute(cmd)

        # 3) 사각형 어노테이션 추가
        def annotate_rect():
            add_rect(win._doc.raw[page_idx], 50, 300, 200, 400, style)

        cmd2 = AddAnnotationCommand(win._doc.raw, page_idx, annotate_rect, "사각형 추가")
        win._cmd_mgr.execute(cmd2)

        # 4) 다른 이름으로 저장
        win._doc.save(save_path)

        # 5) 재열기하여 어노테이션 존재 확인 (fitz 직접 사용)
        verify_doc = fitz.open(save_path)
        page = verify_doc[0]
        drawings = page.get_drawings()
        text_content = page.get_text()

        assert len(drawings) > 0, "사각형 어노테이션이 저장되지 않았음"
        assert "E2E Test" in text_content, "텍스트 어노테이션이 저장되지 않았음"
        verify_doc.close()
```

### TC-156: 삽입 → 삽입 페이지에 어노테이션 → 저장

**접근**: InsertPagesCommand를 직접 실행. InsertDialog는 모킹.

**함정/리스크**:
- 페이지 삽입 후 인덱스 변화에 주의. 예: 0번 앞에 2페이지 삽입 시, 기존 0번은 2번으로 이동.
- 삽입된 페이지에 어노테이션을 추가할 때, `win._doc.raw[삽입된_인덱스]`가 정확해야 함.

```python
class TestTC156:
    """TC-156: 페이지 삽입 → 삽입된 페이지에 어노테이션 → 저장."""

    def test_annotation_on_inserted_page_persists(
        self, main_window, pdf_factory, tmp_path
    ):
        win = main_window
        main_pdf = pdf_factory(num_pages=2, page_texts=["Main1", "Main2"])
        source_pdf = pdf_factory(num_pages=3, page_texts=["Src1", "Src2", "Src3"])
        save_path = str(tmp_path / "inserted_annotated.pdf")

        load_pdf_directly(win, main_pdf)

        # 1) 페이지 삽입 (source의 0번 페이지를 main의 1번 앞에)
        from app.core.command_manager import InsertPagesCommand
        cmd = InsertPagesCommand(win._doc.raw, source_pdf, [0], insert_before=1)
        win._cmd_mgr.execute(cmd)
        assert win._doc.raw.page_count == 3  # 2 + 1

        # 2) 삽입된 페이지(idx=1)에 어노테이션 추가
        from app.core.annotator import AnnotationStyle, add_rect
        from app.core.command_manager import AddAnnotationCommand
        style = AnnotationStyle(color=(0.0, 0.0, 1.0))

        inserted_idx = 1
        def annotate():
            add_rect(win._doc.raw[inserted_idx], 50, 50, 200, 150, style)

        cmd2 = AddAnnotationCommand(win._doc.raw, inserted_idx, annotate, "사각형")
        win._cmd_mgr.execute(cmd2)

        # 3) 저장 및 검증
        win._doc.save(save_path)

        verify_doc = fitz.open(save_path)
        assert verify_doc.page_count == 3
        inserted_page = verify_doc[1]
        assert len(inserted_page.get_drawings()) > 0
        assert "Src1" in inserted_page.get_text()
        verify_doc.close()
```

### TC-157: 순서변경 → 삭제 → Undo x2

**접근**: CommandManager를 직접 사용. 각 단계에서 페이지 텍스트 비교로 상태 검증.

**함정/리스크**:
- `MovePageCommand`의 `to` 인덱스는 fitz의 `move_page(from, to)` 의미를 따름. `from < to`이면 실제 위치는 `to - 1`.
- Undo 후 페이지 텍스트가 원본과 정확히 일치하는지 검증해야 함. 단순 page_count 비교로는 부족.
- **DeletePagesCommand의 Undo**가 페이지 내용을 스냅샷에서 복원하므로, 텍스트 검증이 핵심.

```python
class TestTC157:
    """TC-157: 페이지 순서변경 → 삭제 → Undo → Undo → 원래 상태 복원."""

    def test_double_undo_restores_original(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=5,
                          page_texts=["P1", "P2", "P3", "P4", "P5"])
        load_pdf_directly(win, path)

        # 원본 상태 캡처
        def get_texts():
            return [win._doc.raw[i].get_text().strip() for i in range(win._doc.raw.page_count)]

        original_texts = get_texts()  # ["P1 ...", "P2 ...", ...]

        # 1) 1페이지(idx=0)를 3번째(to=2)로 이동
        from app.core.command_manager import MovePageCommand
        cmd_move = MovePageCommand(win._doc.raw, 0, 2)
        win._cmd_mgr.execute(cmd_move)
        assert get_texts() != original_texts  # 순서 변경됨

        # 2) 현재 2번째 페이지(idx=1) 삭제
        from app.core.command_manager import DeletePagesCommand
        cmd_del = DeletePagesCommand(win._doc.raw, [1])
        win._cmd_mgr.execute(cmd_del)
        assert win._doc.raw.page_count == 4  # 5 - 1

        # 3) Ctrl+Z (삭제 Undo)
        win._cmd_mgr.undo()
        assert win._doc.raw.page_count == 5

        # 4) Ctrl+Z (이동 Undo)
        win._cmd_mgr.undo()
        assert get_texts() == original_texts  # 원본 복원 확인
```

### TC-158: 이미지 → PDF 변환 → 열기 → 어노테이션 → 저장

**접근**: `converter.convert_images_to_pdf()` 직접 호출 → 결과 PDF 로드 → 어노테이션 추가 → 저장 검증. ConvertDialog는 모킹하지 않고 core API만 테스트.

**함정/리스크**:
- 이미지 변환 결과 PDF는 각 이미지가 1페이지이므로, 페이지 크기가 이미지 크기와 다를 수 있음.
- 변환된 PDF에 어노테이션 좌표가 유효한지 확인 필요.

```python
class TestTC158:
    """TC-158: 이미지 → PDF 변환 → 열기 → 어노테이션 → 저장."""

    def test_converted_pdf_accepts_annotations(
        self, main_window, image_factory, tmp_path
    ):
        win = main_window
        img1 = image_factory("img1.png", color=(200, 100, 50))
        img2 = image_factory("img2.png", color=(50, 200, 100))
        converted_path = str(tmp_path / "converted.pdf")
        save_path = str(tmp_path / "annotated_converted.pdf")

        # 1) 이미지 → PDF 변환
        from app.core.converter import convert_images_to_pdf
        convert_images_to_pdf([img1, img2], converted_path)
        assert os.path.exists(converted_path)

        # 2) 변환된 PDF 열기
        load_pdf_directly(win, converted_path)
        assert win._doc.page_count == 2

        # 3) 어노테이션 추가
        from app.core.annotator import AnnotationStyle, add_text
        from app.core.command_manager import AddAnnotationCommand
        style = AnnotationStyle()

        def annotate():
            add_text(win._doc.raw[0], 50, 50, "Converted!", style)

        cmd = AddAnnotationCommand(win._doc.raw, 0, annotate, "텍스트")
        win._cmd_mgr.execute(cmd)

        # 4) 다른 이름으로 저장 및 검증
        win._doc.save(save_path)

        verify_doc = fitz.open(save_path)
        assert "Converted!" in verify_doc[0].get_text()
        verify_doc.close()
```

### TC-159: 페이지 추출 → 추출 PDF 열기 → 내용 확인

**접근**: `page_editor.extract_pages()` 직접 호출 → 추출된 PDF를 fitz로 열어 내용 비교.

**함정/리스크**:
- 추출 시 인덱스가 0-based인지 확인 (page_editor는 0-based).
- 추출된 PDF의 페이지 순서가 입력 인덱스 순서를 따르는지 검증.
- QFileDialog.getSaveFileName 모킹 필요 (MainWindow 경유 시).

```python
class TestTC159:
    """TC-159: 페이지 추출 → 추출된 PDF 열기 → 내용 확인."""

    def test_extracted_pdf_contains_correct_pages(
        self, main_window, pdf_factory, tmp_path
    ):
        win = main_window
        path = pdf_factory(num_pages=5,
                          page_texts=["Alpha", "Beta", "Gamma", "Delta", "Epsilon"])
        extract_path = str(tmp_path / "extracted.pdf")

        load_pdf_directly(win, path)

        # 1) 2~4페이지(idx 1,2,3) 추출
        from app.core import page_editor
        page_editor.extract_pages(win._doc.raw, [1, 2, 3], extract_path)

        # 2) 추출된 PDF 검증
        extracted = fitz.open(extract_path)
        assert extracted.page_count == 3
        assert "Beta" in extracted[0].get_text()
        assert "Gamma" in extracted[1].get_text()
        assert "Delta" in extracted[2].get_text()

        # 3) 원본은 변경되지 않았는지 확인
        assert win._doc.raw.page_count == 5
        extracted.close()
```

### TC-160: 다중 어노테이션 → 연속 Undo → 연속 Redo

**접근**: 6개 어노테이션을 CommandManager 경유로 추가 → Undo 6회 → Redo 6회. 각 단계에서 drawings 수 검증.

**함정/리스크**:
- `AddAnnotationCommand.undo()`는 페이지 스냅샷을 복원하므로, 이전 어노테이션도 함께 사라짐. 즉 Undo는 마지막 커맨드 실행 직전 상태로 복원.
- **핵심**: 6회 Undo 후 drawings가 0개인지, 6회 Redo 후 다시 원래 수인지 확인.
- 스냅샷 기반 Undo이므로 메모리 사용량이 큼 — 테스트에서는 문제 없으나 실제로는 50개 제한.

```python
class TestTC160:
    """TC-160: 다중 어노테이션 → 연속 Undo → 연속 Redo."""

    def test_six_annotations_full_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=1)
        load_pdf_directly(win, path)

        from app.core.annotator import AnnotationStyle, add_rect, add_text, add_line
        from app.core.command_manager import AddAnnotationCommand

        style = AnnotationStyle(color=(1, 0, 0))
        page_idx = 0

        # 초기 drawings 수 기록
        initial_drawings = len(win._doc.raw[page_idx].get_drawings())
        initial_text = win._doc.raw[page_idx].get_text()

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
            cmd = AddAnnotationCommand(win._doc.raw, page_idx, fn, desc)
            win._cmd_mgr.execute(cmd)

        # 6개 추가 후 drawings 증가 확인
        after_all = len(win._doc.raw[page_idx].get_drawings())
        assert after_all > initial_drawings

        # Undo 6회 → 원래 상태
        for _ in range(6):
            assert win._cmd_mgr.can_undo
            win._cmd_mgr.undo()

        assert len(win._doc.raw[page_idx].get_drawings()) == initial_drawings
        assert not win._cmd_mgr.can_undo

        # Redo 6회 → 다시 6개 어노테이션 상태
        for _ in range(6):
            assert win._cmd_mgr.can_redo
            win._cmd_mgr.redo()

        assert len(win._doc.raw[page_idx].get_drawings()) == after_all
        assert not win._cmd_mgr.can_redo
```

### TC-161: 어노테이션 메뉴 도구 전환 후 작업

**접근**: 툴바의 tool_changed 시그널을 직접 emit하여 도구 전환 → 어노테이션 추가 → 상태 검증.

**함정/리스크**:
- `QActionGroup`의 배타적 체크 상태가 offscreen에서 정상 동작하는지 확인 필요.
- 도구 전환 후 커서 변경은 offscreen에서 검증 불가 — 내부 상태(`_current_tool`)로 대체 검증.

```python
class TestTC161:
    """TC-161: 어노테이션 메뉴에서 도구 전환 후 작업 수행."""

    def test_menu_tool_switch_enables_drawing(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=1)
        load_pdf_directly(win, path)

        from app.core.annotator import AnnotationTool

        # 1) 사각형 도구로 전환
        win._on_tool_changed(AnnotationTool.RECT)
        assert win._viewer._current_tool == AnnotationTool.RECT
        assert "사각형" in win._lbl_tool.text()

        # 2) 타원 도구로 전환
        win._on_tool_changed(AnnotationTool.ELLIPSE)
        assert win._viewer._current_tool == AnnotationTool.ELLIPSE
        assert "타원" in win._lbl_tool.text()

        # 3) 선택 도구로 복귀
        win._on_tool_changed(AnnotationTool.SELECT)
        assert win._viewer._current_tool == AnnotationTool.SELECT
        assert "선택" in win._lbl_tool.text()
```

### TC-162: 상태바 종합 확인

**접근**: 각 상태 변경 후 `_lbl_page`, `_lbl_zoom`, `_lbl_tool`, `_lbl_file` 텍스트 검증.

**함정/리스크**:
- `zoom_changed` 시그널이 비동기적으로 처리될 수 있음 — `qtbot.waitSignal` 사용.
- 상태바 텍스트에 로케일 문자(한국어)가 포함됨. 부분 문자열 매칭 사용.

```python
class TestTC162:
    """TC-162: 상태바 정보 종합 확인."""

    def test_status_bar_reflects_all_state(self, main_window, pdf_factory, qtbot):
        win = main_window
        path = pdf_factory(num_pages=5)
        load_pdf_directly(win, path)

        # 페이지 정보
        assert "1 / 5" in win._lbl_page.text()

        # 줌 정보 (기본 150%)
        assert "150" in win._lbl_zoom.text()

        # 파일명
        assert win._lbl_file.text() != ""

        # 도구 정보
        assert "선택" in win._lbl_tool.text()

        # 페이지 이동 후 상태 변경
        win._viewer.goto_page(3)
        assert "4 / 5" in win._lbl_page.text()

        # 줌 변경 후
        win._viewer.zoom_in()
        zoom_pct = round(win._viewer.zoom * 100)
        assert str(zoom_pct) in win._lbl_zoom.text()

        # 도구 변경 후
        from app.core.annotator import AnnotationTool
        win._on_tool_changed(AnnotationTool.TEXT)
        assert "텍스트" in win._lbl_tool.text()
```

### TC-163: 어노테이션 메뉴 도구 전환 & 툴바 동기화

**접근**: 어노테이션 메뉴의 QAction을 직접 trigger → 툴바 버튼의 checked 상태 검증.

**함정/리스크**:
- 메뉴 → 툴바 동기화는 `QActionGroup` 기반. 같은 QAction 객체를 메뉴와 툴바가 공유하므로 자동 동기화되어야 함.
- `isChecked()` 검증 시 `QActionGroup`의 exclusive 설정 확인.

```python
class TestTC163:
    """TC-163: 어노테이션 메뉴 도구 전환 시 툴바 동기화."""

    def test_menu_action_syncs_toolbar(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=1)
        load_pdf_directly(win, path)

        from app.core.annotator import AnnotationTool

        # 메뉴의 타원 액션을 직접 trigger
        ellipse_action = win._toolbar._tool_actions[AnnotationTool.ELLIPSE]
        ellipse_action.trigger()

        # 툴바에서도 타원이 활성 상태인지 확인
        assert ellipse_action.isChecked()

        # 선택 액션으로 전환
        select_action = win._toolbar._tool_actions[AnnotationTool.SELECT]
        select_action.trigger()
        assert select_action.isChecked()
        assert not ellipse_action.isChecked()
```

### TC-164: 문서 미열림 시 편집 기능 비활성화

**접근**: MainWindow 생성 직후 (문서 로드 없이) 각 액션/버튼의 `isEnabled()` 확인.

**함정/리스크**:
- 없음. 가장 단순한 E2E 테스트. 다만 `_act_open`이 활성인지도 확인해야 함.

```python
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

        # 열기는 활성
        assert win._toolbar._act_open.isEnabled()
```

### TC-165: 도움말 > 정보 다이얼로그

**접근**: `QMessageBox.about`을 monkeypatch하여 호출 여부와 인자 검증.

**함정/리스크**:
- `QMessageBox.about`은 모달 다이얼로그이므로 monkeypatch 없이 호출하면 테스트가 블로킹됨.
- **주의**: `about`은 static method가 아닌 경우가 있으므로, 정확한 패치 경로 확인 필요.

```python
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

### TC-166: Command 패턴 4종 Undo/Redo 순차 검증

**접근**: 4종 커맨드(Move, Delete, Insert, Annotation)를 순차 실행, 각각 Undo → Redo → 상태 검증.

**함정/리스크**:
- 가장 복잡한 테스트. 각 커맨드 실행 후 상태를 캡처하고, Undo/Redo 후 정확히 복원/재적용되는지 검증.
- InsertPagesCommand에 source PDF 경로가 필요하므로 별도 PDF 생성.
- 4종 작업이 독립적으로 테스트되어야 함 (하나의 테스트에서 순차 실행하면 이전 작업 결과가 다음에 영향).

```python
class TestTC166:
    """TC-166: Command 패턴 4종 Undo/Redo 순차 검증."""

    def _get_page_texts(self, doc):
        return [doc[i].get_text().strip() for i in range(doc.page_count)]

    def test_move_undo_redo(self, main_window, pdf_factory):
        win = main_window
        path = pdf_factory(num_pages=5, page_texts=["A", "B", "C", "D", "E"])
        load_pdf_directly(win, path)

        original = self._get_page_texts(win._doc.raw)

        from app.core.command_manager import MovePageCommand
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

        from app.core.command_manager import DeletePagesCommand
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

        from app.core.command_manager import InsertPagesCommand
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

        from app.core.annotator import AnnotationStyle, add_rect
        from app.core.command_manager import AddAnnotationCommand

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
```

---

## 4. 모달 다이얼로그 테스트 전략

### 4.1 문제 정의

이 애플리케이션은 다음 모달 다이얼로그를 사용한다:

| 다이얼로그 | 사용처 | 모킹 전략 |
|-----------|--------|----------|
| `QFileDialog.getOpenFileName` | PDF 열기 | `monkeypatch.setattr` |
| `QFileDialog.getSaveFileName` | 저장/추출 | `monkeypatch.setattr` |
| `QMessageBox.question` | 삭제 확인 | `monkeypatch.setattr` |
| `QMessageBox.critical` | 오류 표시 | `monkeypatch.setattr` |
| `QMessageBox.about` | 정보 | `monkeypatch.setattr` |
| `QInputDialog.getText` | 텍스트 입력 | `monkeypatch.setattr` |
| `InsertDialog.exec` | 삽입 다이얼로그 | `monkeypatch.setattr` + 반환값 조작 |

### 4.2 monkeypatch 패턴

```python
# QFileDialog 모킹 — 파일 열기
def mock_open_dialog(monkeypatch, return_path: str):
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getOpenFileName",
        lambda *a, **kw: (return_path, "PDF 파일 (*.pdf)")
    )

# QMessageBox.question 모킹 — 항상 Yes
def mock_confirm_yes(monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.Yes
    )

# QMessageBox.question 모킹 — 항상 No
def mock_confirm_no(monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.No
    )

# InsertDialog 모킹
def mock_insert_dialog(monkeypatch, source_path: str, indices: list[int]):
    """InsertDialog를 모킹하여 특정 소스/인덱스를 반환."""
    from unittest.mock import MagicMock
    mock_dlg = MagicMock()
    mock_dlg.exec.return_value = 1  # Accepted
    mock_dlg.source_path.return_value = source_path
    mock_dlg.selected_indices.return_value = indices

    monkeypatch.setattr(
        "app.ui.main_window.InsertDialog",
        lambda parent: mock_dlg
    )
```

### 4.3 QInputDialog (텍스트 어노테이션)

PdfViewer에서 텍스트 도구로 클릭 시 `QInputDialog.getText`가 호출된다:

```python
# 텍스트 어노테이션 입력 모킹
monkeypatch.setattr(
    "app.ui.pdf_viewer.QInputDialog.getText",
    lambda *a, **kw: ("테스트 텍스트", True)  # (text, ok)
)
```

---

## 5. 비동기 테스트 전략

### 5.1 썸네일 백그라운드 로딩 대기

`PagePanel.load_document()`는 백그라운드 QThread에서 썸네일을 렌더링한다. 플레이스홀더 아이템은 즉시 생성되지만, 실제 썸네일 이미지는 비동기로 업데이트된다.

```python
# 방법 1: 썸네일 로딩 완료까지 대기 (시그널 기반)
# PagePanel에 썸네일 로딩 완료 시그널이 있는 경우:
with qtbot.waitSignal(win._page_panel.thumbnails_loaded, timeout=5000):
    load_pdf_directly(win, path)

# 방법 2: 아이템 수만 확인 (플레이스홀더 즉시 생성)
load_pdf_directly(win, path)
assert win._page_panel._list.count() == expected_page_count
# 썸네일 이미지 내용은 검증하지 않음 (비동기이므로)

# 방법 3: QThread 명시적 정리 (teardown 행 방지)
# fixture cleanup에서:
win._page_panel._cancel_loader()
```

**추천**: 방법 2를 기본으로 사용. E2E 테스트의 관심사는 PDF 내용이지 썸네일 이미지가 아니다. teardown에서는 `_cancel_loader()`를 호출하여 QThread 소멸 행을 방지한다.

### 5.2 변환 워커 스레드

ConvertDialog의 변환은 QThread에서 실행된다. E2E 테스트에서는 ConvertDialog를 통하지 않고 `converter` 모듈을 직접 호출하므로, 스레드 동기화 문제가 없다.

만약 ConvertDialog를 통해 테스트해야 하는 경우:

```python
# ConvertDialog의 conversion_done 시그널 대기
with qtbot.waitSignal(dlg.conversion_done, timeout=10000) as blocker:
    dlg._start_conversion()

output_paths = blocker.args[0]
assert len(output_paths) > 0
```

### 5.3 qtbot.waitSignal 활용 가이드

```python
# 기본 사용
with qtbot.waitSignal(widget.some_signal, timeout=3000) as blocker:
    widget.do_something()
assert blocker.args == [expected_value]

# 시그널이 발생하지 않아야 하는 경우
with qtbot.assertNotEmitted(widget.some_signal):
    widget.do_something_that_should_not_emit()

# 여러 시그널 중 하나 대기
with qtbot.waitSignals(
    [widget.signal_a, widget.signal_b],
    timeout=3000,
    order="none"  # 순서 무관
):
    widget.do_something()
```

### 5.4 processEvents 호출 패턴

Qt 이벤트 루프가 offscreen에서도 동작하지만, 시그널-슬롯 연결이 Queued인 경우 `processEvents()`가 필요할 수 있다:

```python
from PyQt6.QtWidgets import QApplication

# 명시적 이벤트 처리 (시그널 딜리버리 보장)
QApplication.processEvents()
```

> **주의**: `processEvents()`를 남용하면 테스트가 비결정적이 된다. Direct connection인 경우 불필요.

---

## 6. 리스크 및 제약사항

### 6.1 offscreen 환경 제약

| 제약 | 영향 | 대응 |
|------|------|------|
| 마우스 드래그 시뮬레이션 불안정 | QGraphicsView 위의 마우스 이벤트 좌표가 실제와 다를 수 있음 | API-level 접근으로 우회 |
| 렌더링 결과 비교 불가 | 픽셀 단위 비교 불가능 | fitz로 PDF 내용 직접 검증 |
| 네이티브 다이얼로그 실행 불가 | QFileDialog 등이 블로킹됨 | monkeypatch로 모킹 |
| 커서 변경 미반영 | setCursor() 호출 확인만 가능 | 내부 상태 변수 검증 |
| DnD (드래그 앤 드롭) 불가 | 썸네일 패널의 페이지 순서 변경 | `page_moved` 시그널 직접 emit |

### 6.2 테스트 불안정성 (Flaky Test) 방지

| 원인 | 방지 방안 |
|------|----------|
| 타이밍 의존 | `waitSignal` 사용, `sleep` 절대 금지 |
| QThread 경합 | 테스트 종료 시 `_cancel_loader()` 호출 |
| 전역 상태 오염 | 각 테스트에서 새 MainWindow 생성 |
| 파일 잠금 | `tmp_path` 사용, 명시적 `doc.close()` |
| 시그널 누락 | `timeout` 파라미터 명시 (기본 5000ms) |
| processEvents 타이밍 | Direct connection 사용, Queued 최소화 |

### 6.3 CI 환경 고려사항

```yaml
# CI 환경 변수 설정 (GitHub Actions 예시)
env:
  QT_QPA_PLATFORM: offscreen
  DISPLAY: ""  # Linux에서 Xvfb 대신 offscreen 사용
```

- **Windows CI**: offscreen 플러그인이 기본 포함. 추가 설정 불필요.
- **메모리**: AddAnnotationCommand의 스냅샷이 페이지당 수십 KB. TC-160 같은 테스트에서 6개 스냅샷 생성 — CI에서 문제 없음.
- **실행 시간**: 전체 E2E 12건이 30초 이내 완료되어야 함. PDF 생성/파싱이 주 병목.

### 6.4 테스트 파일 구조 제안

```
tests/
├── conftest.py              # 기존 공통 픽스처
├── e2e/
│   ├── __init__.py
│   ├── conftest.py          # E2E 전용 픽스처 (MainWindow, pdf_factory 등)
│   ├── helpers.py           # load_pdf_directly, mock 헬퍼 함수
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
│   └── test_tc166_command_pattern.py
├── core/
│   └── ...
└── ui/
    └── ...
```

### 6.5 실행 명령

```bash
# E2E 테스트만 실행
uv run pytest tests/e2e/ -v --tb=short

# 전체 테스트 (기존 단위 + E2E)
uv run pytest tests/ -v

# 특정 TC만 실행
uv run pytest tests/e2e/test_tc155_save_reopen.py -v

# 실패 시 첫 실패에서 중단
uv run pytest tests/e2e/ -v -x
```

---

## 부록: load_pdf_directly 전체 코드

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

---

> **참고**: 이 계획서는 기존 단위 테스트(`tests/core/`, `tests/ui/`)와 독립적으로 실행 가능한 E2E 테스트를 정의한다. 단위 테스트가 개별 모듈의 정확성을 보장하고, E2E 테스트는 모듈 간 통합과 사용자 시나리오 전체 흐름을 검증한다.

---

## 상호 검증 리뷰 결과

> 작성일: 2026-04-03
> QA Lead가 Test Architect의 E2E_TEST_PLAN.md를 검토한 결과

---

### 1. Architect 계획서에서 발견된 기술적 문제

#### 1.1 `loaded_main_window` 픽스처의 불일치 (심각)

Architect의 `loaded_main_window` 픽스처(conftest.py 확장 제안, 라인 83~117)에는 실제 `_open_file()` 메서드와 **2가지 차이점**이 있다:

- **`set_tool_checked(AnnotationTool.SELECT)` 호출 누락**: 실제 `_open_file()`은 `self._toolbar.set_tool_checked(AnnotationTool.SELECT)`를 호출하지만, Architect의 픽스처에는 이 줄이 빠져 있다. 이로 인해 도구 전환 테스트(TC-161, TC-163)에서 초기 도구 상태가 실제 앱과 다를 수 있다.
- **`_lbl_file.setText()` 호출 누락**: 실제 `_open_file()`은 `self._lbl_file.setText(os.path.basename(path))`를 호출하지만, Architect의 픽스처에서는 빠져 있다. TC-162 상태바 테스트에서 `_lbl_file` 검증 시 빈 문자열이 반환될 것이다. Architect 본인도 `test_statusbar_shows_filename`에서 `file_text == ""` 케이스를 허용하며 이 문제를 인지한 듯하나, 근본 해결 대신 우회했다.

반면, Architect는 `_update_title(path)`를 호출하지만, 이는 윈도우 타이틀만 변경하므로 상태바 파일명과는 별개이다.

**QA 계획서(본 문서)의 `load_pdf_directly()`는 실제 `_open_file()`의 모든 단계를 정확히 재현**하고 있으므로 이 문제가 없다.

#### 1.2 TC-155 어노테이션 추가 경로의 비일관성 (중간)

Architect의 TC-155에서 어노테이션 추가는 `w._on_annotation_requested(add_rect_fn, "사각형 추가")` 형태로 MainWindow의 슬롯을 직접 호출한다. 이 접근은 E2E 관점에서 더 통합적이다.

그러나 TC-160과 TC-166에서는 `AddAnnotationCommand`를 직접 생성하여 `w._cmd_mgr.execute(cmd)`로 실행한다. **같은 계획서 내에서 두 가지 다른 접근이 혼재**하여, 실제 시그널 흐름(viewer -> main_window -> command_manager)을 일관되게 테스트하지 못한다.

`_on_annotation_requested()`를 사용하면 `refresh_page()`, `reload_page()`, `_update_undo_actions()` 등 부수 효과가 자동으로 실행되지만, `cmd_mgr.execute()`를 직접 호출하면 이 부수 효과가 누락된다. TC-160에서 Undo 후 viewer/panel 새로고침이 누락되어 실제 UI 상태와 테스트 상태가 괴리될 수 있다.

#### 1.3 TC-157 `_refresh_after_edit()` / `_update_undo_actions()` 호출 불일치 (경미)

Architect의 TC-157에서 `cmd_move`, `cmd_delete` 실행 후 `w._refresh_after_edit()`, `w._update_undo_actions()`를 명시적으로 호출하지만, Undo 시에는 `w._undo()`만 호출한다. `_undo()` 내부에서 `_full_undo_redo_refresh()`가 호출되므로 실제로는 문제 없으나, execute와 undo 사이의 패턴이 비대칭적이다.

#### 1.4 TC-162 상태바 줌 검증 (경미)

Architect의 `test_statusbar_shows_zoom`에서 `w._viewer.set_zoom(2.0)` 호출 후 `"200%"` 확인을 한다. 그런데 `set_zoom()`이 `_lbl_zoom` 업데이트를 트리거하는지는 시그널 연결에 따라 다르다. `zoom_changed` 시그널이 Direct Connection인지 확인이 필요하다. Queued Connection이면 `QApplication.processEvents()`가 필요할 수 있다.

#### 1.5 TC-165 `about` mock 패턴 — `unittest.mock.patch` vs `monkeypatch` 혼용 (경미)

Architect의 TC-165에서 `from unittest.mock import patch, MagicMock`과 `with patch(...)` 패턴을 사용한다. 이는 동작하지만, 다른 모든 TC에서는 pytest의 `monkeypatch`를 사용하므로 일관성이 떨어진다. `monkeypatch.setattr` + 수동 호출 기록이 더 pytest-idiomatic하다.

---

### 2. Architect 계획서에서 발견된 좋은 아이디어 (QA 계획서에 반영 권장)

#### 2.1 추가 E2E 시나리오 제안 (TC-E01 ~ TC-E07)

Architect가 제안한 추가 시나리오는 QA 계획서에 없다. 특히 다음은 반영할 가치가 있다:

- **TC-E03: 페이지 삭제 후 마지막 페이지 접근 시 out-of-range 방지** — 실제 사용자가 겪을 수 있는 경계 조건
- **TC-E05: Undo 50회 초과 시 가장 오래된 커맨드 폐기** — Undo 스택 한계 검증
- **TC-E06: 동일 경로 덮어쓰기 저장 → 재열기** — 증분 저장 통합 테스트

#### 2.2 구현 우선순위/로드맵 (Phase 1~4)

Architect가 TC 구현 순서를 "인프라 검증(TC-164) → 핵심 기능(TC-157, TC-166) → 영속성(TC-155, TC-156) → UI(TC-161~165)"로 단계화한 것은 합리적이다. QA 계획서에는 이러한 구현 순서가 명시되어 있지 않다.

#### 2.3 TC-163의 배타적 체크 전수 검증

Architect의 `test_all_tool_actions_are_exclusive`는 모든 도구 조합에 대해 `QActionGroup`의 배타적 선택을 전수 검증한다. QA 계획서의 TC-163은 특정 도구 쌍만 테스트하므로, 이 전수 검증 패턴을 채택하면 더 견고하다.

#### 2.4 TC-159 원본 불변 검증

Architect의 TC-159에서 추출 후 원본 문서의 page_count가 변하지 않았는지(`assert win._doc.raw.page_count == 5`) 검증하는 것은 QA 계획서에 없는 좋은 추가 검증이다.

---

### 3. pytest 코드 스켈레톤 정확성 검증

#### 3.1 pytest-qt 호환성

- **`qtbot.addWidget(w)` + `w.show()`**: 두 계획서 모두 올바르게 사용. pytest-qt 4.4+에서 정상 동작.
- **`qtbot.waitSignal`**: QA 계획서(섹션 5)에서 올바르게 설명. Architect는 사용하지 않음 (불필요한 경우가 대부분이므로 문제 없음).
- **`qtbot.assertNotEmitted`**: QA 계획서에서 언급. pytest-qt 4.0+에서 지원.

#### 3.2 픽스처 구조

**Architect**: 기존 `tests/conftest.py`에 E2E 픽스처를 추가하는 방식. `loaded_main_window`가 `yield` 패턴이나 `_cancel_loader()` 미호출.

**QA**: 별도 `tests/e2e/conftest.py`에 E2E 전용 픽스처를 배치. `load_pdf_directly`를 `helpers.py`로 분리.

**평가**: QA 방식이 더 우수. E2E 픽스처를 별도 conftest에 분리하면 기존 단위 테스트에 영향을 주지 않고, MainWindow import로 인한 불필요한 Qt 초기화를 방지한다.

#### 3.3 코드 정확성 세부 검증

| 항목 | Architect | QA | 실제 코드 기준 판정 |
|------|-----------|-----|-------------------|
| `_on_annotation_requested` 시그니처 | `(annotate_fn, description)` | 동일 | 정확 (두 계획서 모두) |
| `InsertPagesCommand` 생성자 | `(raw, source_path, indices, insert_before)` | 동일 | 정확 |
| `MovePageCommand` 생성자 | `(raw, from_idx, to_idx)` | 동일 | 정확 |
| `DeletePagesCommand` 생성자 | `(raw, [indices])` | 동일 | 정확 |
| `_lbl_page` 텍스트 형식 | `"1 / 5"` 검증 | `"1 / 5"` 검증 | 실제: `f"페이지: {page_idx + 1} / {total}"` — **두 계획서 모두 부분 매칭이므로 정확** |
| `_lbl_tool` 텍스트 형식 | `"선택"`, `"사각형"` 등 | 동일 | 실제: `f"도구: {name}"` — **부분 매칭이므로 정확** |
| `_show_about` 호출 | `QMessageBox.about(self, title, text)` | 동일 | 정확 |

---

### 4. monkeypatch/mock 패턴 정확성

#### 4.1 QFileDialog 모킹

**Architect**:
```python
monkeypatch.setattr(
    "app.ui.main_window.QFileDialog.getOpenFileName",
    lambda *args, **kwargs: (pdf_3pages, "PDF 파일 (*.pdf)")
)
```

**QA**:
```python
monkeypatch.setattr(
    "app.ui.main_window.QFileDialog.getOpenFileName",
    lambda *args, **kwargs: (path, "PDF 파일 (*.pdf)")
)
```

**판정**: 두 패턴 모두 정확. `QFileDialog`가 `app.ui.main_window`에서 import되므로 패치 경로가 올바르다.

#### 4.2 QMessageBox.about 모킹

**Architect**: `unittest.mock.patch("app.ui.main_window.QMessageBox.about")` — 정확하나 pytest 스타일이 아님.

**QA**: `monkeypatch.setattr("app.ui.main_window.QMessageBox.about", fake_about)` — pytest-idiomatic하고 정확.

**판정**: QA 패턴 권장. 두 가지 모두 동작하지만 일관성 측면에서 `monkeypatch`가 낫다.

#### 4.3 InsertDialog 모킹

**QA 계획서**에서 `MagicMock`으로 InsertDialog를 모킹하는 패턴:
```python
mock_dlg = MagicMock()
mock_dlg.exec.return_value = 1  # Accepted
```

**주의점**: PyQt6에서 `QDialog.exec()`의 반환값은 `QDialog.DialogCode.Accepted` (정수 1)이므로 `return_value = 1`은 정확하다. 단, `QDialog.Accepted`가 더 명시적이다.

---

### 5. 경합 조건 및 Flaky Test 리스크

#### 5.1 썸네일 QThread 정리 (두 계획서 모두 부분적으로 다룸)

**Architect**: `loaded_main_window` 픽스처에서 `w._page_panel._cancel_loader()`를 **호출하지 않음**. teardown에서 `w._doc.close()`만 호출. 이는 QThread가 아직 실행 중일 때 `fitz.Document`가 닫히면서 segfault가 발생할 수 있다.

**QA**: 섹션 5.1에서 `_cancel_loader()` 호출을 권장하고 있으나, 실제 픽스처 코드에 반영하지 않았다. `main_window` 픽스처의 teardown에 `win._page_panel._cancel_loader()` 호출이 빠져 있다.

**권장**: 두 계획서 모두 teardown에서 `_cancel_loader()` -> `_doc.close()` -> `win.close()` 순서를 명시해야 한다.

```python
yield win
if hasattr(win, '_page_panel'):
    win._page_panel._cancel_loader()
if win._doc.is_open:
    win._doc.close()
win.close()
```

#### 5.2 `_make_pdf()`의 초기 drawings 수 (두 계획서 모두 영향)

기존 `conftest.py`의 `_make_pdf()`는 **각 페이지에 `draw_rect()`를 호출**하여 시각적 구별용 사각형을 그린다. 따라서 `get_drawings()` 결과에 **이미 1개의 drawing이 포함**되어 있다.

Architect의 TC-160에서 `original_drawings = len(raw[page_idx].get_drawings())`로 초기값을 기록하므로 문제 없다. 그러나 TC-155에서 `assert len(drawings) > 0`은 어노테이션 없이도 참이 될 수 있다 (기존 draw_rect 때문). 이는 **거짓 양성(false positive)** 리스크가 있다.

**QA 계획서의 `pdf_factory`는 `with_annotations=False`가 기본**이므로 이 문제가 없다. 다만 QA 계획서에서도 TC-155 검증 시 "drawings 수가 초기값보다 증가했는지"가 아닌 "drawings > 0"으로 검증하면 동일한 리스크가 있다.

**권장**: 어노테이션 추가 전후의 drawings 수를 비교하는 상대적 검증이 필요하다:
```python
before = len(page.get_drawings())
# ... 어노테이션 추가 ...
after = len(page.get_drawings())
assert after > before
```

#### 5.3 Windows 파일 잠금 (두 계획서 모두 일부 다룸)

Architect가 "fitz.Document가 열려 있는 상태에서 파일 삭제 시 Windows에서 PermissionError 발생 가능"을 언급했다. 이는 정확하다.

TC-155에서 `doc2 = fitz.open(save_path)` 후 `doc2.close()`를 호출하지만, 테스트 실패 시 `close()`가 실행되지 않을 수 있다. `try/finally` 또는 `contextmanager` 패턴을 사용해야 한다.

**QA 계획서도 동일한 패턴**을 사용하고 있으므로 양쪽 모두 수정이 필요하다.

#### 5.4 TC-160 lambda 클로저 변수 캡처 (Architect 특유 문제)

Architect의 TC-160에서:
```python
annotations = [
    ("사각형1", lambda: add_rect(win._doc.raw[page_idx], 10, 10, 100, 100, style)),
    ...
]
```

이 lambda들은 리스트 컴프리헨션이 아닌 리터럴 리스트이므로 클로저 캡처 문제는 없다. 그러나 `page_idx`가 루프 변수가 아닌 고정값이므로 안전하다.

반면 Architect의 같은 TC에서 `for` 루프 내 lambda 생성은 없으므로 이 리스크는 해당되지 않는다.

**Architect의 TC-160 코드에서 TC-160용 `for i in range(3)` 루프 내 `make_rect` lambda** (라인 536-539): `def make_rect(off=offset):` 패턴으로 기본 인자 바인딩을 올바르게 사용하고 있으므로 정확하다.

---

### 6. TC별 최종 판정

| TC | Architect 접근 | QA 접근 | 최종 권장 |
|----|---------------|---------|----------|
| TC-155 | `_on_annotation_requested` 직접 호출. drawings > 0 검증 (거짓 양성 리스크) | `AddAnnotationCommand` 직접 생성. 동일 리스크 있음 | QA 접근 + 상대적 drawings 비교로 수정 |
| TC-156 | `loaded_main_window` 사용. 픽스처 불완전 | `pdf_factory`로 텍스트 포함 PDF 생성. 텍스트 검증 추가 | **QA 접근 채택** — 텍스트 검증이 더 강력 |
| TC-157 | 텍스트 비교로 원본 복원 검증. 견고함 | 동일 접근. `_cmd_mgr.undo()` 직접 호출 | **양쪽 동등** — `win._undo()` 사용 권장 (부수효과 포함) |
| TC-158 | `_on_annotation_requested` + core 직접 호출 혼용 | `AddAnnotationCommand` 경유 | **QA 접근 채택** — CommandManager 경유가 더 E2E적 |
| TC-159 | 텍스트 비교 검증 + 단일 페이지 추가 테스트 | 텍스트 비교 + 원본 불변 검증 | **QA 접근 + Architect의 단일 페이지 테스트 추가** |
| TC-160 | `_on_annotation_requested` 사용. 6회 undo/redo | `AddAnnotationCommand` 직접 사용. 동일 구조 | **양쪽 동등** — 부수효과 포함 위해 `_on_annotation_requested` + `_undo()`/`_redo()` 권장 |
| TC-161 | `_toolbar._tool_actions[...].trigger()` 사용 | `_on_tool_changed()` 직접 호출 | **Architect 접근이 더 E2E적** — 실제 QAction trigger가 시그널 흐름을 통과함 |
| TC-162 | 개별 테스트 메서드로 분리 (4개) | 단일 테스트에 통합 | **Architect 접근 채택** — 개별 실패 시 원인 파악 용이 |
| TC-163 | 배타적 체크 전수 검증 포함 | 특정 도구 쌍만 검증 | **Architect 접근 채택** — 전수 검증이 더 견고 |
| TC-164 | 어노테이션 도구 비활성화 별도 검증 + 열기 버튼 활성 검증 | 동일 항목 검증 | **양쪽 동등** — Architect가 3개 메서드로 분리한 것이 약간 우수 |
| TC-165 | `unittest.mock.patch` 사용 | `monkeypatch.setattr` 사용 | **QA 접근 채택** — pytest-idiomatic |
| TC-166 | `_on_annotation_requested` + `_undo()`/`_redo()` | `AddAnnotationCommand` + `_cmd_mgr.undo()`/`redo()` | **Architect 접근이 더 E2E적** — `_undo()`가 UI 새로고침 포함 |

---

### 7. 최종 병합 권장 사항

1. **픽스처**: QA 계획서의 별도 `tests/e2e/conftest.py` + `helpers.py` 구조를 채택. `load_pdf_directly()`는 QA 버전 사용 (모든 `_open_file()` 단계 재현).

2. **teardown**: 모든 MainWindow 픽스처에 `_cancel_loader()` -> `_doc.close()` -> `win.close()` 순서 적용.

3. **어노테이션 추가 경로**: TC-155/TC-156/TC-160에서는 `_on_annotation_requested()`를 사용하여 실제 시그널 흐름을 타도록 통일. TC-166은 Command 유형별로 개별 테스트이므로 `AddAnnotationCommand` 직접 사용 허용.

4. **Undo/Redo 호출**: `win._undo()` / `win._redo()`를 사용 (UI 새로고침 부수효과 포함). `_cmd_mgr.undo()` 직접 호출은 core 계층 테스트에만 사용.

5. **drawings 검증**: 절대값(`> 0`) 대신 상대값(`after > before`) 비교로 통일. 기존 `_make_pdf()`의 draw_rect로 인한 거짓 양성 방지.

6. **파일 리소스 정리**: fitz.Document 검증 시 `try/finally` 또는 별도 픽스처로 안전한 close 보장.

7. **추가 시나리오**: Architect의 TC-E03(경계 조건), TC-E05(Undo 한계), TC-E06(덮어쓰기 저장)을 Phase 4로 채택.

8. **구현 순서**: Architect의 Phase 1~4 순서를 채택. TC-164(가장 단순) -> TC-157/TC-166(핵심) -> TC-155/TC-156(영속성) -> TC-161~165(UI) 순서.

9. **파일 네이밍**: QA 계획서의 TC별 독립 파일 구조(`test_tc155_save_reopen.py`)를 채택. Architect의 주제별 그룹(`test_annotation_save.py`)보다 TC 추적이 용이.

10. **`_make_pdf` 초기 drawing 문제**: `pdf_factory`에 `draw_rect=False` 옵션을 추가하거나, E2E용 PDF는 drawing 없이 생성하는 별도 팩토리를 사용. 또는 기존 `_make_pdf`의 draw_rect를 제거하되, 기존 단위 테스트에 영향이 없는지 확인 필요.
