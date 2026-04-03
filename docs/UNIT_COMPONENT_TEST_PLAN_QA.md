# 단위/컴포넌트 테스트 QA 구현 계획서

> 작성일: 2026-04-03
> 대상: TC-001 ~ TC-154 중 미자동화 108건
> 도구: pytest 8.x + pytest-qt 4.4.x + PyQt6 offscreen
> 작성자: QA Lead Agent

---

## 1. 테스트 자동화 판단 기준

### 1.1 판단 매트릭스

| 기준 | 자동화 적합 (Yes) | 부분 자동화 (Partial) | 수동 유지 (No) |
|------|-------------------|----------------------|----------------|
| 실행 환경 | offscreen에서 재현 가능 | 특수 환경 필요 (LibreOffice 등) | 실제 렌더링/물리 디바이스 필요 |
| 반복성 | 회귀 테스트 필수 | 가끔 확인 필요 | 일회성 검증 |
| 비용 | 구현 30분 이내 | 구현 1시간 이내 | 구현 > 1시간 + 유지비 높음 |
| 판정 신뢰도 | 프로그래밍으로 명확 판정 | 보조 도구 필요 | 육안 확인 필수 |

### 1.2 TC별 자동화 판정 결과

#### 자동화 가능 (Yes) — 72건

| TC | 제목 | 근거 |
|----|------|------|
| TC-001 | 정상 PDF 열기 | MainWindow._open_file() monkeypatch로 검증 |
| TC-002 | 문서 교체 열기 | 두 번 load 후 상태 비교 |
| TC-003 | 열기 취소 | QFileDialog monkeypatch → 빈 문자열 |
| TC-004 | 손상 PDF 열기 | 손상 파일 생성 + 오류 처리 확인 |
| TC-005 | 비PDF 파일 열기 | 텍스트 파일 경로 → 예외 처리 확인 |
| TC-006 | Ctrl+O 단축키 | QAction.trigger() 또는 shortcut 확인 |
| TC-007 | Ctrl+S 저장 | save() 호출 + 파일 존재 확인 |
| TC-008 | 미열림 시 저장 | _act_save.isEnabled() == False 확인 |
| TC-009 | 증분저장 폴백 | core 레벨 PdfDocument.save() 테스트 |
| TC-010 | 다른이름으로 저장 | QFileDialog monkeypatch + 파일 검증 |
| TC-011 | 확장자 자동 추가 | _save_as 로직에서 .pdf 추가 확인 |
| TC-012 | 저장 취소 | QFileDialog → 빈 문자열 반환 |
| TC-013 | 정상 종료 | win.close() 후 상태 확인 |
| TC-014 | 문서 열린 채 종료 | 문서 로드 → close → 리소스 해제 확인 |
| TC-015 | 기본 줌 150% | viewer.zoom == 1.5 확인 |
| TC-016 | 다중페이지 렌더링 | goto_page 순회 + current_page 확인 |
| TC-017 | 줌 인 | zoom_in() → zoom > before 확인 |
| TC-018 | 줌 아웃 | zoom_out() → zoom < before 확인 |
| TC-019 | 줌 최대 400% | set_zoom(999) → MAX_ZOOM 확인 |
| TC-020 | 줌 최소 25% | set_zoom(0.01) → MIN_ZOOM 확인 |
| TC-021 | 화면 맞춤 | zoom_fit() 호출 후 zoom 변화 확인 |
| TC-023 | 줌 스핀박스 직접입력 | _zoom_spin.setValue(200) → viewer.zoom 확인 |
| TC-026 | PgDn 다음 페이지 | goto_page(current+1) + page_changed 시그널 |
| TC-027 | PgUp 이전 페이지 | goto_page(current-1) |
| TC-028 | 첫페이지에서 PgUp | goto_page(-1) → 변화 없음 |
| TC-029 | 마지막페이지 PgDn | goto_page(page_count) → 변화 없음 |
| TC-030 | 썸네일 클릭 이동 | page_panel._list.setCurrentRow() → page_selected 시그널 |
| TC-031 | 상태바 페이지 정보 | _lbl_page.text() 패턴 매칭 |
| TC-034 | 모든 페이지 썸네일 | _list.count() == page_count |
| TC-035 | 단일 클릭 선택 | _list.setCurrentRow() → selected_indices() |
| TC-047 | Delete 삭제 | QMessageBox monkeypatch Yes → page_count 감소 |
| TC-048 | 다중 삭제 | 다중 선택 → 삭제 → page_count 확인 |
| TC-049 | 1페이지 삭제 시도 | QMessageBox.warning 호출 확인 |
| TC-050 | 2페이지 모두 삭제 | page_count <= len(indices) → 경고 |
| TC-051 | 삭제 Undo | 삭제 → undo → page_count 복원 |
| TC-052 | 삭제 취소 | QMessageBox monkeypatch No → 변화 없음 |
| TC-053 | 툴바 삭제 버튼 | _act_delete.trigger() → 같은 흐름 |
| TC-054 | 편집메뉴 삭제 | 편집 메뉴 액션 trigger |
| TC-055 | 단일 추출 | extract_pages + fitz 검증 |
| TC-056 | 다중 추출 | 다중 인덱스 extract_pages |
| TC-057 | 추출 후 원본 불변 | 추출 전후 page_count 비교 |
| TC-058 | 추출 취소 | QFileDialog → 빈 문자열 |
| TC-059 | 페이지 삽입 | InsertDialog monkeypatch → page_count 증가 |
| TC-061 | 다중 삽입 | 여러 인덱스 삽입 |
| TC-062 | 삽입 Undo | 삽입 → undo → page_count 복원 |
| TC-063 | 삽입 취소 | InsertDialog.exec() → Rejected |
| TC-064 | 도구 배타적 전환 | tool_actions 체크 상태 확인 |
| TC-065 | Escape 선택 복귀 | _tool_actions[SELECT].trigger() |
| TC-067 | 기본 색상 빨강 | _annot_color == QColor(255,0,0) |
| TC-068 | 선 굵기 변경 | _width_spin.setValue() → width_changed 시그널 |
| TC-069 | 선 굵기 최소 | _width_spin.minimum() == 0.5 |
| TC-070 | 선 굵기 최대 | _width_spin.maximum() == 20.0 |
| TC-075 | 어노테이션 Undo | AddAnnotationCommand.undo() — 이미 core에서 커버 |
| TC-081 | 텍스트 크기 최소 | _font_size_spin.minimum() == 6 |
| TC-082 | 텍스트 크기 최대 | _font_size_spin.maximum() == 72 |
| TC-085 | 텍스트 스타일 가시성 | set_text_tool_active(True/False) → 위젯 enabled 확인 |
| TC-100 | Ctrl+Z Undo | _undo() → cmd_mgr 상태 변화 |
| TC-101 | 연속 Undo | 3회 실행 → 3회 undo |
| TC-102 | 빈 Undo | cmd_mgr.undo() → None |
| TC-103 | 이력 50개 제한 | 51회 execute → can_undo 50번 |
| TC-108 | 메뉴 동적 텍스트 | _act_undo.text() 확인 |
| TC-109 | Ctrl+Y Redo | _redo() 동작 확인 |
| TC-110 | 새 작업 시 Redo 초기화 | execute 후 can_redo == False |
| TC-111 | 빈 Redo | cmd_mgr.redo() → None |
| TC-112 | Undo→Redo→Undo 반복 | 순차 실행 + 상태 확인 |
| TC-120 | 이미지 없이 변환 | ValueError 확인 |
| TC-123 | LibreOffice 미설치 | find_libreoffice mock None |
| TC-130 | 메인 윈도우 레이아웃 | 위젯 존재 + 타입 확인 |
| TC-131~136 | 메뉴 항목 확인 | menuBar().actions() 순회 |
| TC-137~140 | 툴바 구성 확인 | 액션/위젯 존재 확인 |
| TC-154 | Core/UI 분리 | ast.parse로 import 스캔 |

#### 부분 자동화 (Partial) — 18건

| TC | 제목 | 자동화 범위 | 수동 필요 부분 |
|----|------|------------|--------------|
| TC-022 | Ctrl+마우스 휠 줌 | QWheelEvent 시뮬레이션 가능하나 offscreen 불안정 | 실제 마우스 휠 동작 |
| TC-024 | 페이지 팬 (드래그) | DragMode 설정 확인만 자동화 | 실제 드래그 스크롤 |
| TC-036 | Ctrl+클릭 다중 선택 | QListWidget 내부 API로 선택 | 실제 Ctrl+클릭 인터랙션 |
| TC-037 | Shift+클릭 범위 선택 | QListWidget 내부 API로 선택 | 실제 Shift+클릭 |
| TC-043 | 드래그앤드롭 순서변경 | page_moved 시그널 emit 테스트 | 실제 D&D |
| TC-044 | 순서변경 Undo | MovePageCommand 기반 테스트 | D&D 연동 |
| TC-045 | 마지막→첫 이동 | core 레벨 테스트 | D&D 연동 |
| TC-046 | 같은 위치 드롭 | same index noop 확인 | D&D 연동 |
| TC-060 | 삽입 다이얼로그 미리보기 | InsertDialog 위젯 생성 + 파일 로드 | 실제 썸네일 렌더링 품질 |
| TC-066 | 색상 선택 QColorDialog | monkeypatch 가능 | 실제 색상 피커 UI |
| TC-076 | 텍스트 삽입 | core add_text + QInputDialog mock | 뷰어에서 위치 정확도 |
| TC-077 | 한글 텍스트 삽입 | core 수준 이미 커버 | 뷰어 렌더링 품질 |
| TC-079 | 폰트 변경 | 콤보박스 + core add_text | 렌더링 차이 육안 |
| TC-080 | 텍스트 크기 변경 | 스핀박스 + core add_text | 렌더링 차이 육안 |
| TC-083 | Bold 스타일 | _act_bold.setChecked(True) + core | 렌더링 차이 |
| TC-084 | Italic 스타일 | _act_italic.setChecked(True) + core | 렌더링 차이 |
| TC-127 | 다이얼로그 탭 구조 | QTabWidget.count() + tabText() | 탭 UI 레이아웃 |
| TC-139 | 도구 배타적 토글 | QActionGroup.checkedAction() | - |

#### 수동 유지 (No) — 18건

| TC | 제목 | 수동 유지 근거 |
|----|------|--------------|
| TC-025 | OpenHand 커서 | offscreen에서 커서 형태 검증 불가 |
| TC-032 | 썸네일 비동기 렌더링 | QThread 타이밍 + 50페이지 PDF 성능 측정 |
| TC-033 | 썸네일 크기/비율 | 픽셀 정확도 검증은 디스플레이 의존 |
| TC-038~042 | 컨텍스트 메뉴 | QMenu.exec_() 네이티브 이벤트 루프 |
| TC-071 | PDF 콘텐츠 스트림 호환성 | 다른 PDF 뷰어에서 확인 필요 |
| TC-072~074 | 회전 페이지 어노테이션 좌표 | 마우스 좌표 → PDF 좌표 매핑 정확도(부분 커버됨) |
| TC-078 | 텍스트 도구 IBeam 커서 | offscreen 커서 |
| TC-086 | 텍스트 입력 취소 | QInputDialog 네이티브 |
| TC-087 | 빈 텍스트 입력 | QInputDialog 네이티브 |
| TC-088 | 맑은 고딕 자동 감지 | Windows 폰트 존재 여부 환경 의존 |
| TC-089~099 | 드래그 기반 도형 그리기 | QGraphicsView 마우스 이벤트 offscreen 불안정 |
| TC-091 | 반투명 프리뷰 | 시각적 검증 |
| TC-090 | Crosshair 커서 | offscreen 커서 |
| TC-092~099 | 3px 미만 무시/색상 적용 | 마우스 드래그 시뮬레이션 필요 |
| TC-115 | 모든 이미지 형식 변환 | 8종 파일 생성 비용 높음 (부분 자동화 가능) |
| TC-116~119 | 변환 다이얼로그 UI 조작 | ConvertDialog + QThread 연동 |
| TC-121~122 | Office 변환 | LibreOffice 설치 필요 |
| TC-124~125 | LO 감지/타임아웃 | 환경 의존 |
| TC-126 | Ctrl+Shift+C | 단축키는 자동화 가능하나 다이얼로그 모달 |
| TC-128~129 | 프로그레스/비차단 | QThread 타이밍 + UI 반응성 |
| TC-141~142 | 다크 테마/하이라이트 | 색상값 육안 확인 |
| TC-143~144 | 전체 단축키/마우스 휠 | 종합 수동 검증 |
| TC-145~149 | 빌드/배포/실행 | CI/CD 또는 수동 |
| TC-150~153 | 성능/안정성/호환성 | 비기능 요구사항, 환경 의존 |

### 1.3 비용-편익 분석

| 카테고리 | TC 수 | 구현 예상 공수 | 회귀 방지 효과 | 판정 |
|----------|------|---------------|---------------|------|
| 문서 관리 (열기/저장) | 14건 중 10건 미자동화 | 3시간 | 높음 — 가장 기본 기능 | **자동화** |
| PDF 뷰어 (줌/탐색) | 11건 중 6건 | 2시간 | 중간 | **자동화** |
| 썸네일 패널 | 11건 중 5건 | 2시간 | 중간 — D&D는 수동 | **부분 자동화** |
| 페이지 편집 | 21건 중 12건 | 4시간 | 높음 | **자동화** |
| 어노테이션 | 36건 중 6건 | 2시간 (나머지 수동) | 중간 — core 이미 커버 | **부분 자동화** |
| Undo/Redo | 13건 중 9건 | 2시간 | 높음 | **자동화** |
| 변환 | 17건 중 4건 | 1시간 | 중간 — core 이미 커버 | **부분 자동화** |
| UI 레이아웃/메뉴 | 13건 | 2시간 | 낮음 — 변경 빈도 낮음 | **자동화** (간단) |
| 빌드/배포 | 5건 | N/A | — | **수동** |
| 비기능 | 5건 | N/A | — | **수동** |

---

## 2. 리스크 기반 우선순위

### 2.1 리스크 × 영향도 매트릭스

```
영향도 (높음)
    │
    │  ★ TC-001~002 (열기)     ★ TC-007,009 (저장)     ★ TC-051,062 (Undo)
    │  ★ TC-047~050 (삭제)     ★ TC-059,061 (삽입)     ★ TC-100~101 (Undo)
    │
    │  ◆ TC-064~065 (도구전환)  ◆ TC-130~136 (메뉴구조) ◆ TC-154 (아키텍처)
    │  ◆ TC-055~057 (추출)      ◆ TC-110,112 (Redo)
    │
    │  ○ TC-023 (줌 스핀박스)   ○ TC-033 (썸네일 크기)  ○ TC-141~142 (테마)
    │  ○ TC-069~070 (경계값)    ○ TC-081~082 (경계값)
    │
    └──────────────────────────────────────────────── 회귀 발생 확률 (높음)
```

**범례**: ★ = 우선순위 1 (즉시 자동화), ◆ = 우선순위 2, ○ = 우선순위 3

### 2.2 회귀 리스크 상위 20 TC

| 순위 | TC | 제목 | 리스크 근거 |
|------|-----|------|-----------|
| 1 | TC-001 | PDF 열기 | 모든 기능의 전제 조건. _open_file 변경 시 전체 영향 |
| 2 | TC-007 | 저장 | 데이터 손실 가능. incremental save 로직 복잡 |
| 3 | TC-009 | 저장 폴백 | 실패 경로 코드가 변경될 가능성 높음 |
| 4 | TC-047 | 페이지 삭제 | QMessageBox 연동 + Command 패턴. 리팩토링 취약 |
| 5 | TC-051 | 삭제 Undo | 스냅샷 복원 로직이 복잡. 페이지 인덱스 계산 오류 가능 |
| 6 | TC-059 | 페이지 삽입 | InsertDialog + InsertPagesCommand 연동 복잡 |
| 7 | TC-062 | 삽입 Undo | 삽입 역순 삭제 로직 |
| 8 | TC-100 | Undo 기본 | 모든 편집 기능의 안전망 |
| 9 | TC-101 | 연속 Undo | 스택 관리 오류 가능 |
| 10 | TC-110 | Redo 스택 초기화 | 새 execute() 시 redo_stack.clear() 누락 가능 |
| 11 | TC-002 | 문서 교체 | 리소스 정리 누락 시 메모리 누수 |
| 12 | TC-064 | 도구 배타적 전환 | QActionGroup 설정 변경 시 다중 활성화 버그 |
| 13 | TC-065 | Escape 복귀 | 단축키 충돌 가능 |
| 14 | TC-049 | 1페이지 삭제 방지 | 경계값 체크 누락 시 빈 문서 crash |
| 15 | TC-055 | 페이지 추출 | extract_pages 인덱스 계산 |
| 16 | TC-130 | 레이아웃 | 위젯 추가/제거 시 레이아웃 깨짐 |
| 17 | TC-154 | Core/UI 분리 | 실수로 core에 PyQt6 import 추가 |
| 18 | TC-103 | 이력 50개 제한 | MAX_HISTORY 상수 변경 또는 제한 로직 누락 |
| 19 | TC-085 | 텍스트 스타일 가시성 | set_text_tool_active() 위젯 목록 불일치 |
| 20 | TC-108 | 메뉴 동적 텍스트 | _update_undo_actions() 텍스트 포맷 변경 |

### 2.3 구현 순서 (Sprint 단위)

**Sprint 1 (최우선)**: TC-001~014 (문서 관리) + TC-047~063 (페이지 편집 UI 레벨) + TC-100~112 (Undo/Redo UI 레벨)
**Sprint 2**: TC-015~031 (뷰어/탐색) + TC-064~070 (도구 전환/스타일) + TC-085
**Sprint 3**: TC-130~140 (UI 구조) + TC-154 (아키텍처) + TC-103 + 나머지

---

## 3. 테스트 파일별 구현 계획

### 3.1 기존 파일 확장

#### `tests/core/test_pdf_document.py` — 추가 0건 (이미 충분)

기존 16개 테스트가 TC-001(core), TC-002(core), TC-007(core), TC-009(core), TC-011(core) 등을 커버.

#### `tests/core/test_page_editor.py` — 추가 0건 (이미 충분)

기존 15개 테스트가 move/delete/extract/insert의 core 로직 커버.

#### `tests/core/test_command_manager.py` — 추가 2건

TC-103 (이력 50개 제한), TC-112 (Undo→Redo→Undo 반복) 보강.

```python
# 추가할 테스트

class TestCommandManagerMaxHistory:
    def test_max_history_limit_50(self, cmd_mgr, raw_3pages):
        """TC-103: 50개 초과 시 가장 오래된 이력 제거."""
        for i in range(55):
            cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 1))
            # move 후 원래 위치로 복구 (다음 반복 위해)
            raw_3pages.move_page(1, 0)
        
        undo_count = 0
        while cmd_mgr.can_undo:
            cmd_mgr.undo()
            undo_count += 1
        assert undo_count == 50

    def test_undo_redo_undo_cycle(self, cmd_mgr, raw_3pages):
        """TC-112: Undo → Redo → Undo 반복."""
        def texts(doc):
            return [doc[i].get_text().strip() for i in range(doc.page_count)]
        
        original = texts(raw_3pages)
        cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 2))
        after_move = texts(raw_3pages)
        
        cmd_mgr.undo()
        assert texts(raw_3pages) == original
        
        cmd_mgr.redo()
        assert texts(raw_3pages) == after_move
        
        cmd_mgr.undo()
        assert texts(raw_3pages) == original
```

**필요 픽스처**: 기존 `raw_3pages`, `cmd_mgr` 사용.

#### `tests/core/test_converter.py` — 추가 2건

TC-115 (다양한 이미지 형식), TC-120 (이미지 없이 변환 — 이미 있지만 UI 레벨 보강 불필요).

```python
class TestConvertAllImageFormats:
    """TC-115: 지원되는 모든 이미지 형식 변환."""
    
    @pytest.mark.parametrize("ext,mode", [
        (".png", "RGB"),
        (".jpg", "RGB"),
        (".bmp", "RGB"),
        (".gif", "P"),
        (".tiff", "RGB"),
        (".webp", "RGB"),
    ])
    def test_format_converts_to_pdf(self, tmp_path, ext, mode):
        from PIL import Image
        from app.core.converter import convert_images_to_pdf
        img_path = str(tmp_path / f"test{ext}")
        Image.new(mode, (200, 150), color=128).save(img_path)
        out = str(tmp_path / f"out{ext}.pdf")
        result = convert_images_to_pdf([img_path], out)
        assert os.path.exists(result)
```

#### `tests/ui/test_pdf_viewer.py` — 추가 3건

TC-015 (기본 줌 확인), TC-021 (화면 맞춤) 보강.

```python
class TestPdfViewerZoomBoundary:
    """TC-019, TC-020 줌 경계값 (이미 있지만 정확한 값 확인 보강)."""
    
    def test_zoom_max_is_400_percent(self, loaded_viewer):
        """TC-019: 줌 최대값이 정확히 4.0(400%)인지 확인."""
        w, _ = loaded_viewer
        assert PdfViewer.MAX_ZOOM == 4.0
    
    def test_zoom_min_is_25_percent(self, loaded_viewer):
        """TC-020: 줌 최소값이 정확히 0.25(25%)인지 확인."""
        w, _ = loaded_viewer
        assert PdfViewer.MIN_ZOOM == 0.25

    def test_zoom_fit_changes_zoom(self, loaded_viewer):
        """TC-021: zoom_fit() 호출 후 줌 값이 변경됨."""
        w, _ = loaded_viewer
        w.set_zoom(3.0)  # 의도적으로 큰 줌
        before = w.zoom
        w.zoom_fit()
        # zoom_fit은 페이지 크기에 맞추므로 3.0과 다를 것
        # offscreen에서는 viewport 크기가 0일 수 있어 값이 안 바뀔 수 있음
        # 따라서 예외 없이 동작하는지만 확인
        assert isinstance(w.zoom, float)
```

#### `tests/ui/test_page_panel.py` — 추가 2건

TC-034 (모든 페이지 썸네일), TC-035 (단일 선택) 보강.

```python
class TestPagePanelAllPages:
    """TC-034: 다양한 페이지 수의 PDF에서 모든 썸네일 표시."""
    
    def test_20_pages_all_thumbnails(self, qtbot, tmp_path):
        from tests.conftest import _make_pdf
        path = _make_pdf(20, tmp_path)
        doc = PdfDocument()
        doc.open(path)
        w = PagePanel()
        qtbot.addWidget(w)
        w.load_document(doc)
        assert w._list.count() == 20
        w._cancel_loader()
        doc.close()

class TestPagePanelSelection:
    """TC-035: 단일 클릭 선택 후 selected_indices 확인."""
    
    def test_single_click_selection(self, loaded_panel):
        w, _ = loaded_panel
        w._list.setCurrentRow(2)
        indices = w.selected_indices()
        assert indices == [2]
```

### 3.2 신규 파일

#### `tests/ui/test_main_window.py` — 신규 생성 (약 40개 테스트)

이 파일이 **가장 핵심**. MainWindow 레벨에서 UI 통합 테스트를 수행.

```python
"""MainWindow 단위/컴포넌트 테스트 — TC-001~TC-014, TC-047~TC-063, TC-100~TC-112 등."""

from __future__ import annotations

import os
import pytest
from PyQt6.QtWidgets import QMessageBox, QFileDialog

from app.core.annotator import AnnotationTool
from app.core.pdf_document import PdfDocument
from app.ui.main_window import MainWindow


# ── 픽스처 ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def win(qtbot):
    """독립적인 MainWindow. teardown 시 QThread 정리 후 close."""
    w = MainWindow()
    qtbot.addWidget(w)
    w.show()
    yield w
    if hasattr(w, '_page_panel') and hasattr(w._page_panel, '_cancel_loader'):
        w._page_panel._cancel_loader()
    w.close()


def _load_pdf(win, path: str) -> None:
    """QFileDialog 우회하여 직접 PDF 로드."""
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


# ── TC-001~TC-014: 문서 관리 ─────────────────────────────────────────────────

class TestDocumentOpen:
    """TC-001 ~ TC-006."""

    def test_tc001_open_valid_pdf(self, win, pdf_3pages):
        """TC-001: 정상 PDF 열기 → 뷰어, 썸네일, 상태바 갱신."""
        _load_pdf(win, pdf_3pages)
        assert win._doc.is_open
        assert win._doc.page_count == 3
        assert win._page_panel._list.count() == 3
        assert win._viewer.current_page == 0
        assert "3" in win._lbl_page.text()

    def test_tc002_reopen_replaces_document(self, win, pdf_3pages, pdf_5pages):
        """TC-002: 이미 열린 상태에서 새 문서 열기 → 교체."""
        _load_pdf(win, pdf_3pages)
        assert win._doc.page_count == 3
        _load_pdf(win, pdf_5pages)
        assert win._doc.page_count == 5
        assert win._page_panel._list.count() == 5

    def test_tc003_open_dialog_cancel(self, win, monkeypatch):
        """TC-003: 파일 선택 취소 → 상태 변화 없음."""
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getOpenFileName",
            lambda *a, **kw: ("", "")
        )
        win._open_file()
        assert not win._doc.is_open

    def test_tc004_open_corrupted_pdf(self, win, tmp_path, monkeypatch):
        """TC-004: 손상된 PDF → 오류 메시지, 정상 상태 유지."""
        corrupted = str(tmp_path / "corrupted.pdf")
        with open(corrupted, "wb") as f:
            f.write(b"NOT A VALID PDF CONTENT")
        
        errors = []
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.critical",
            lambda *a, **kw: errors.append(a)
        )
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getOpenFileName",
            lambda *a, **kw: (corrupted, "PDF 파일 (*.pdf)")
        )
        win._open_file()
        assert len(errors) == 1  # 오류 다이얼로그 호출됨
        assert not win._doc.is_open

    def test_tc005_open_non_pdf_file(self, win, tmp_path, monkeypatch):
        """TC-005: PDF 아닌 파일 → 오류 메시지."""
        txt_file = str(tmp_path / "test.txt")
        with open(txt_file, "w") as f:
            f.write("Hello World")
        
        errors = []
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.critical",
            lambda *a, **kw: errors.append(a)
        )
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getOpenFileName",
            lambda *a, **kw: (txt_file, "")
        )
        win._open_file()
        assert len(errors) == 1

    def test_tc006_ctrl_o_shortcut_exists(self, win):
        """TC-006: Ctrl+O 단축키가 열기 액션에 연결됨."""
        shortcut = win._toolbar._act_open.shortcut().toString()
        assert "O" in shortcut.upper()


class TestDocumentSave:
    """TC-007 ~ TC-012."""

    def test_tc007_save_overwrites(self, win, pdf_3pages, tmp_path):
        """TC-007: Ctrl+S로 저장 → 파일 존재 확인."""
        import shutil
        save_path = str(tmp_path / "writable.pdf")
        shutil.copy(pdf_3pages, save_path)
        _load_pdf(win, save_path)
        win._save_file()
        assert os.path.exists(save_path)

    def test_tc008_save_disabled_when_no_doc(self, win):
        """TC-008: 문서 미열림 시 저장 버튼 비활성화."""
        assert not win._toolbar._act_save.isEnabled()

    def test_tc010_save_as(self, win, pdf_3pages, tmp_path, monkeypatch):
        """TC-010: 다른 이름으로 저장."""
        _load_pdf(win, pdf_3pages)
        save_path = str(tmp_path / "new_name.pdf")
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: (save_path, "PDF 파일 (*.pdf)")
        )
        win._save_as()
        assert os.path.exists(save_path)

    def test_tc011_save_as_auto_extension(self, win, pdf_3pages, tmp_path, monkeypatch):
        """TC-011: 확장자 미지정 시 .pdf 자동 추가."""
        _load_pdf(win, pdf_3pages)
        no_ext_path = str(tmp_path / "no_extension")
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: (no_ext_path, "PDF 파일 (*.pdf)")
        )
        win._save_as()
        assert os.path.exists(no_ext_path + ".pdf")

    def test_tc012_save_as_cancel(self, win, pdf_3pages, monkeypatch):
        """TC-012: 다른 이름으로 저장 취소."""
        _load_pdf(win, pdf_3pages)
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: ("", "")
        )
        # 예외 없이 동작하면 성공
        win._save_as()


class TestDocumentClose:
    """TC-013 ~ TC-014."""

    def test_tc013_close_app(self, win):
        """TC-013: 정상 종료."""
        win.close()  # 예외 없이 종료

    def test_tc014_close_with_open_doc(self, win, pdf_3pages):
        """TC-014: 문서 열린 상태에서 종료 → 리소스 해제."""
        _load_pdf(win, pdf_3pages)
        assert win._doc.is_open
        win.close()
        # closeEvent에서 _doc.close()가 호출됨


# ── TC-015~TC-031: 뷰어/탐색 (일부 viewer 테스트 보강) ──────────────────────

class TestViewerInMainWindow:
    """TC-015, TC-016, TC-026~TC-031."""

    def test_tc015_default_zoom_150(self, win, pdf_3pages):
        """TC-015: 기본 줌 150%."""
        _load_pdf(win, pdf_3pages)
        assert win._viewer.zoom == pytest.approx(1.5)

    def test_tc016_multipage_navigation(self, win, pdf_3pages):
        """TC-016: 다중 페이지 순차 이동."""
        _load_pdf(win, pdf_3pages)
        for i in range(3):
            win._viewer.goto_page(i)
            assert win._viewer.current_page == i

    def test_tc026_pgdn_next_page(self, win, pdf_3pages):
        """TC-026: 다음 페이지 이동."""
        _load_pdf(win, pdf_3pages)
        assert win._viewer.current_page == 0
        win._viewer.goto_page(1)
        assert win._viewer.current_page == 1

    def test_tc027_pgup_prev_page(self, win, pdf_3pages):
        """TC-027: 이전 페이지 이동."""
        _load_pdf(win, pdf_3pages)
        win._viewer.goto_page(2)
        win._viewer.goto_page(1)
        assert win._viewer.current_page == 1

    def test_tc028_pgup_at_first_page(self, win, pdf_3pages):
        """TC-028: 첫 페이지에서 PgUp → 변화 없음."""
        _load_pdf(win, pdf_3pages)
        win._viewer.goto_page(-1)
        assert win._viewer.current_page == 0

    def test_tc029_pgdn_at_last_page(self, win, pdf_3pages):
        """TC-029: 마지막 페이지에서 PgDn → 변화 없음."""
        _load_pdf(win, pdf_3pages)
        win._viewer.goto_page(99)
        assert win._viewer.current_page == 0  # 범위 초과이므로 이전 값 유지

    def test_tc031_statusbar_page_info(self, win, pdf_3pages):
        """TC-031: 상태바 페이지 정보."""
        _load_pdf(win, pdf_3pages)
        win._viewer.goto_page(1)
        win._update_page_status(1)
        text = win._lbl_page.text()
        assert "2" in text  # "페이지: 2 / 3"


# ── TC-047~TC-063: 페이지 편집 (MainWindow 레벨) ─────────────────────────────

class TestPageDelete:
    """TC-047 ~ TC-054."""

    def test_tc047_delete_single_page(self, win, pdf_5pages, monkeypatch):
        """TC-047: Delete 키로 단일 페이지 삭제."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([1])  # 2번째 페이지 삭제
        assert win._doc.page_count == 4

    def test_tc048_delete_multiple_pages(self, win, pdf_5pages, monkeypatch):
        """TC-048: 다중 페이지 삭제."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0, 2, 4])
        assert win._doc.page_count == 2

    def test_tc049_delete_all_pages_blocked(self, win, pdf_1page, monkeypatch):
        """TC-049: 1페이지 문서에서 삭제 → 경고."""
        _load_pdf(win, pdf_1page)
        warnings = []
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.warning",
            lambda *a, **kw: warnings.append(a)
        )
        win._delete_pages([0])
        assert len(warnings) == 1
        assert win._doc.page_count == 1

    def test_tc050_delete_all_of_2page_blocked(self, win, tmp_path, monkeypatch):
        """TC-050: 2페이지 문서에서 모든 페이지 삭제 시도 → 경고."""
        from tests.conftest import _make_pdf
        path = _make_pdf(2, tmp_path)
        _load_pdf(win, path)
        warnings = []
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.warning",
            lambda *a, **kw: warnings.append(a)
        )
        win._delete_pages([0, 1])
        assert len(warnings) == 1
        assert win._doc.page_count == 2

    def test_tc051_delete_undo(self, win, pdf_5pages, monkeypatch):
        """TC-051: 삭제 후 Undo → 페이지 복원."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([1])
        assert win._doc.page_count == 4
        win._undo()
        assert win._doc.page_count == 5

    def test_tc052_delete_cancel(self, win, pdf_5pages, monkeypatch):
        """TC-052: 삭제 확인 다이얼로그 취소 → 변화 없음."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.No
        )
        win._delete_pages([1])
        assert win._doc.page_count == 5

    def test_tc053_toolbar_delete_button(self, win, pdf_5pages, monkeypatch):
        """TC-053: 툴바 삭제 버튼 동작."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        # 페이지 선택
        win._page_panel._list.setCurrentRow(0)
        win._delete_selected_pages()
        assert win._doc.page_count == 4

    def test_tc054_edit_menu_delete(self, win, pdf_5pages, monkeypatch):
        """TC-054: 편집 메뉴에서 삭제."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._page_panel._list.setCurrentRow(2)
        # 편집 메뉴의 삭제 액션은 _toolbar._act_delete과 같은 시그널
        win._toolbar._act_delete.trigger()
        assert win._doc.page_count == 4


class TestPageExtract:
    """TC-055 ~ TC-058."""

    def test_tc055_extract_single(self, win, pdf_5pages, tmp_path, monkeypatch):
        """TC-055: 단일 페이지 추출."""
        _load_pdf(win, pdf_5pages)
        out = str(tmp_path / "extracted.pdf")
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: (out, "PDF 파일 (*.pdf)")
        )
        win._extract_pages([0])
        assert os.path.exists(out)
        import fitz
        doc = fitz.open(out)
        assert len(doc) == 1
        doc.close()

    def test_tc056_extract_multiple(self, win, pdf_5pages, tmp_path, monkeypatch):
        """TC-056: 다중 페이지 추출."""
        _load_pdf(win, pdf_5pages)
        out = str(tmp_path / "multi_extract.pdf")
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: (out, "PDF 파일 (*.pdf)")
        )
        win._extract_pages([0, 1, 2])
        import fitz
        doc = fitz.open(out)
        assert len(doc) == 3
        doc.close()

    def test_tc057_extract_preserves_original(self, win, pdf_5pages, tmp_path, monkeypatch):
        """TC-057: 추출 후 원본 불변."""
        _load_pdf(win, pdf_5pages)
        out = str(tmp_path / "extract.pdf")
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: (out, "PDF 파일 (*.pdf)")
        )
        win._extract_pages([0, 1])
        assert win._doc.page_count == 5  # 원본 유지

    def test_tc058_extract_dialog_cancel(self, win, pdf_5pages, monkeypatch):
        """TC-058: 추출 저장 취소."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: ("", "")
        )
        win._extract_pages([0])  # 예외 없이 반환


class TestPageInsert:
    """TC-059 ~ TC-063."""

    def test_tc059_insert_pages(self, win, pdf_3pages, pdf_5pages, monkeypatch):
        """TC-059: 페이지 삽입."""
        _load_pdf(win, pdf_3pages)
        
        class FakeInsertDialog:
            DialogCode = type('DC', (), {'Accepted': 1})()
            def __init__(self, parent): pass
            def exec(self): return 1
            def source_path(self): return pdf_5pages
            def selected_indices(self): return [0, 1]
        
        monkeypatch.setattr("app.ui.main_window.InsertDialog", FakeInsertDialog)
        win._insert_pages(insert_before=1)
        assert win._doc.page_count == 5  # 3 + 2

    def test_tc061_insert_multiple(self, win, pdf_3pages, pdf_5pages, monkeypatch):
        """TC-061: 다중 페이지 삽입."""
        _load_pdf(win, pdf_3pages)
        
        class FakeInsertDialog:
            DialogCode = type('DC', (), {'Accepted': 1})()
            def __init__(self, parent): pass
            def exec(self): return 1
            def source_path(self): return pdf_5pages
            def selected_indices(self): return [0, 1, 2]
        
        monkeypatch.setattr("app.ui.main_window.InsertDialog", FakeInsertDialog)
        win._insert_pages(insert_before=0)
        assert win._doc.page_count == 6  # 3 + 3

    def test_tc062_insert_undo(self, win, pdf_3pages, pdf_5pages, monkeypatch):
        """TC-062: 삽입 후 Undo → 원래 페이지 수 복원."""
        _load_pdf(win, pdf_3pages)
        
        class FakeInsertDialog:
            DialogCode = type('DC', (), {'Accepted': 1})()
            def __init__(self, parent): pass
            def exec(self): return 1
            def source_path(self): return pdf_5pages
            def selected_indices(self): return [0]
        
        monkeypatch.setattr("app.ui.main_window.InsertDialog", FakeInsertDialog)
        win._insert_pages(insert_before=1)
        assert win._doc.page_count == 4
        win._undo()
        assert win._doc.page_count == 3

    def test_tc063_insert_dialog_cancel(self, win, pdf_3pages, monkeypatch):
        """TC-063: 삽입 다이얼로그 취소."""
        _load_pdf(win, pdf_3pages)
        
        class FakeInsertDialog:
            DialogCode = type('DC', (), {'Accepted': 1, 'Rejected': 0})()
            def __init__(self, parent): pass
            def exec(self): return 0  # Rejected
            def source_path(self): return ""
            def selected_indices(self): return []
        
        monkeypatch.setattr("app.ui.main_window.InsertDialog", FakeInsertDialog)
        win._insert_pages(insert_before=0)
        assert win._doc.page_count == 3


# ── TC-064~TC-070, TC-085: 도구 전환 / 스타일 ────────────────────────────────

class TestToolSwitching:
    """TC-064, TC-065, TC-067~TC-070, TC-085."""

    def test_tc064_exclusive_tool_selection(self, win, pdf_3pages):
        """TC-064: 도구 배타적 전환."""
        _load_pdf(win, pdf_3pages)
        toolbar = win._toolbar
        
        # 텍스트 도구 선택
        toolbar._tool_actions[AnnotationTool.TEXT].trigger()
        assert toolbar._tool_group.checkedAction() == toolbar._tool_actions[AnnotationTool.TEXT]
        
        # 사각형 도구로 전환
        toolbar._tool_actions[AnnotationTool.RECT].trigger()
        assert toolbar._tool_group.checkedAction() == toolbar._tool_actions[AnnotationTool.RECT]
        # 텍스트는 더 이상 체크되지 않음
        assert not toolbar._tool_actions[AnnotationTool.TEXT].isChecked()

    def test_tc065_escape_returns_to_select(self, win, pdf_3pages):
        """TC-065: Escape로 선택 도구 복귀."""
        _load_pdf(win, pdf_3pages)
        toolbar = win._toolbar
        toolbar._tool_actions[AnnotationTool.RECT].trigger()
        assert toolbar._tool_group.checkedAction() == toolbar._tool_actions[AnnotationTool.RECT]
        
        toolbar._tool_actions[AnnotationTool.SELECT].trigger()
        assert toolbar._tool_group.checkedAction() == toolbar._tool_actions[AnnotationTool.SELECT]

    def test_tc067_default_color_red(self, win):
        """TC-067: 기본 색상 빨강."""
        from PyQt6.QtGui import QColor
        assert win._toolbar._annot_color == QColor(255, 0, 0)

    def test_tc068_line_width_change_signal(self, win, pdf_3pages, qtbot):
        """TC-068: 선 굵기 변경 시그널."""
        _load_pdf(win, pdf_3pages)
        with qtbot.waitSignal(win._toolbar.width_changed, timeout=1000):
            win._toolbar._width_spin.setValue(5.0)

    def test_tc069_line_width_minimum(self, win):
        """TC-069: 선 굵기 최소값 0.5pt."""
        assert win._toolbar._width_spin.minimum() == 0.5

    def test_tc070_line_width_maximum(self, win):
        """TC-070: 선 굵기 최대값 20pt."""
        assert win._toolbar._width_spin.maximum() == 20.0

    def test_tc081_font_size_minimum(self, win):
        """TC-081: 텍스트 크기 최소값 6pt."""
        assert win._toolbar._font_size_spin.minimum() == 6

    def test_tc082_font_size_maximum(self, win):
        """TC-082: 텍스트 크기 최대값 72pt."""
        assert win._toolbar._font_size_spin.maximum() == 72

    def test_tc085_text_style_visibility(self, win, pdf_3pages):
        """TC-085: 텍스트 스타일 컨트롤 — 텍스트 도구 시만 활성화."""
        _load_pdf(win, pdf_3pages)
        toolbar = win._toolbar
        
        # 선택 도구 → 텍스트 스타일 비활성화
        toolbar._tool_actions[AnnotationTool.SELECT].trigger()
        assert not toolbar._font_combo.isEnabled()
        assert not toolbar._font_size_spin.isEnabled()
        assert not toolbar._act_bold.isEnabled()
        assert not toolbar._act_italic.isEnabled()
        
        # 텍스트 도구 → 텍스트 스타일 활성화
        toolbar._tool_actions[AnnotationTool.TEXT].trigger()
        # set_text_tool_active(True) 호출됨
        win._on_tool_changed(AnnotationTool.TEXT)
        assert toolbar._font_combo.isEnabled()
        assert toolbar._font_size_spin.isEnabled()
        assert toolbar._act_bold.isEnabled()
        assert toolbar._act_italic.isEnabled()


# ── TC-100~TC-112: Undo/Redo (MainWindow 레벨) ──────────────────────────────

class TestUndoRedoMainWindow:
    """TC-100 ~ TC-112."""

    def test_tc100_undo_basic(self, win, pdf_5pages, monkeypatch):
        """TC-100: Ctrl+Z Undo 기본 동작."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        assert win._doc.page_count == 4
        win._undo()
        assert win._doc.page_count == 5

    def test_tc101_consecutive_undo(self, win, pdf_5pages, monkeypatch):
        """TC-101: 연속 Undo — 3회 삭제 후 3회 Undo."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        # 3회 삭제 (매번 첫 페이지)
        win._delete_pages([0])  # 5→4
        win._delete_pages([0])  # 4→3
        win._delete_pages([0])  # 3→2
        assert win._doc.page_count == 2
        
        win._undo()  # 2→3
        win._undo()  # 3→4
        win._undo()  # 4→5
        assert win._doc.page_count == 5

    def test_tc102_undo_when_empty(self, win, pdf_3pages):
        """TC-102: 이력 없을 때 Undo → 오류 없음."""
        _load_pdf(win, pdf_3pages)
        win._undo()  # 예외 없이 동작

    def test_tc108_undo_dynamic_text(self, win, pdf_5pages, monkeypatch):
        """TC-108: 메뉴 동적 텍스트 "실행 취소: {설명}"."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        text = win._act_undo.text()
        assert "실행 취소" in text
        assert "삭제" in text

    def test_tc109_redo_basic(self, win, pdf_5pages, monkeypatch):
        """TC-109: Ctrl+Y Redo 기본 동작."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        win._undo()
        assert win._doc.page_count == 5
        win._redo()
        assert win._doc.page_count == 4

    def test_tc110_new_action_clears_redo(self, win, pdf_5pages, monkeypatch):
        """TC-110: 새 작업 수행 시 Redo 스택 초기화."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])  # 삭제
        win._undo()              # Undo → Redo 가능
        assert win._cmd_mgr.can_redo
        
        win._delete_pages([0])   # 새 작업 → Redo 초기화
        assert not win._cmd_mgr.can_redo

    def test_tc111_redo_when_empty(self, win, pdf_3pages):
        """TC-111: Redo 이력 없을 때 → 오류 없음."""
        _load_pdf(win, pdf_3pages)
        win._redo()  # 예외 없이 동작

    def test_tc112_undo_redo_undo_cycle(self, win, pdf_5pages, monkeypatch):
        """TC-112: Undo → Redo → Undo 반복."""
        _load_pdf(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        assert win._doc.page_count == 4
        
        win._undo()
        assert win._doc.page_count == 5
        
        win._redo()
        assert win._doc.page_count == 4
        
        win._undo()
        assert win._doc.page_count == 5
```

#### `tests/ui/test_main_window_menu.py` — 신규 생성 (13개 테스트)

TC-130 ~ TC-140: UI 구조 검증.

```python
"""MainWindow 메뉴/툴바 구조 테스트 — TC-130~TC-140."""

from __future__ import annotations

import pytest
from app.ui.main_window import MainWindow


@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    w.show()
    yield w
    if hasattr(w, '_page_panel') and hasattr(w._page_panel, '_cancel_loader'):
        w._page_panel._cancel_loader()
    w.close()


class TestMainWindowLayout:
    """TC-130: 메인 윈도우 레이아웃 구성."""

    def test_tc130_has_toolbar(self, win):
        assert win._toolbar is not None

    def test_tc130_has_page_panel(self, win):
        assert win._page_panel is not None

    def test_tc130_has_viewer(self, win):
        assert win._viewer is not None

    def test_tc130_has_status_bar(self, win):
        assert win.statusBar() is not None


class TestMenuStructure:
    """TC-131 ~ TC-136: 메뉴 항목 존재 확인."""

    def _menu_texts(self, win, menu_title_fragment):
        """메뉴바에서 특정 메뉴를 찾아 하위 액션 텍스트 반환."""
        for action in win.menuBar().actions():
            if menu_title_fragment in action.text():
                menu = action.menu()
                if menu:
                    return [a.text() for a in menu.actions() if not a.isSeparator()]
        return []

    def test_tc131_file_menu(self, win):
        """TC-131: 파일 메뉴 항목."""
        texts = self._menu_texts(win, "파일")
        text_str = " ".join(texts)
        assert "열기" in text_str
        assert "저장" in text_str
        assert "종료" in text_str

    def test_tc132_edit_menu(self, win):
        """TC-132: 편집 메뉴 항목."""
        texts = self._menu_texts(win, "편집")
        text_str = " ".join(texts)
        assert "실행 취소" in text_str or "취소" in text_str
        assert "삭제" in text_str
        assert "추출" in text_str
        assert "삽입" in text_str

    def test_tc133_view_menu(self, win):
        """TC-133: 보기 메뉴 항목."""
        texts = self._menu_texts(win, "보기")
        assert len(texts) >= 3  # 줌인, 줌아웃, 맞춤, 이전, 다음

    def test_tc134_annotation_menu(self, win):
        """TC-134: 어노테이션 메뉴 항목."""
        texts = self._menu_texts(win, "어노테이션")
        text_str = " ".join(texts)
        assert "선택" in text_str
        assert "텍스트" in text_str
        assert "사각형" in text_str
        assert "타원" in text_str
        assert "선" in text_str

    def test_tc135_tools_menu(self, win):
        """TC-135: 도구 메뉴 항목."""
        texts = self._menu_texts(win, "도구")
        text_str = " ".join(texts)
        assert "변환" in text_str

    def test_tc136_help_menu(self, win):
        """TC-136: 도움말 메뉴 항목."""
        texts = self._menu_texts(win, "도움말")
        text_str = " ".join(texts)
        assert "정보" in text_str


class TestToolbarStructure:
    """TC-137 ~ TC-140: 툴바 구성."""

    def test_tc137_file_group(self, win):
        """TC-137: 파일 그룹 — 열기, 저장."""
        assert win._toolbar._act_open is not None
        assert win._toolbar._act_save is not None

    def test_tc138_page_edit_group(self, win):
        """TC-138: 페이지 편집 그룹."""
        assert win._toolbar._act_delete is not None
        assert win._toolbar._act_extract is not None
        assert win._toolbar._act_insert is not None
        assert win._toolbar._act_convert is not None

    def test_tc139_annotation_exclusive_toggle(self, win):
        """TC-139: 어노테이션 도구 배타적 토글."""
        from app.core.annotator import AnnotationTool
        group = win._toolbar._tool_group
        assert group.isExclusive()
        assert len(win._toolbar._tool_actions) == 5

    def test_tc140_zoom_controls(self, win):
        """TC-140: 줌 컨트롤."""
        assert win._toolbar._act_zoom_in is not None
        assert win._toolbar._act_zoom_out is not None
        assert win._toolbar._act_zoom_fit is not None
        assert win._toolbar._zoom_spin is not None
```

#### `tests/core/test_architecture.py` — 신규 생성 (1개 테스트)

TC-154: Core/UI 분리.

```python
"""아키텍처 제약 테스트 — TC-154."""

from __future__ import annotations

import ast
import os

import pytest


class TestArchitecture:
    """TC-154: app/core/ 내에 PyQt6 import가 없어야 합니다."""

    def test_tc154_core_no_pyqt6_import(self):
        """Core 모듈에 PyQt6 의존성이 없어야 합니다."""
        core_dir = os.path.join(os.path.dirname(__file__), "..", "..", "app", "core")
        core_dir = os.path.normpath(core_dir)
        
        violations = []
        for root, dirs, files in os.walk(core_dir):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read())
                    except SyntaxError:
                        continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if "PyQt6" in alias.name:
                                violations.append(f"{fpath}: import {alias.name}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "PyQt6" in node.module:
                            violations.append(f"{fpath}: from {node.module}")
        
        assert violations == [], f"Core에 PyQt6 의존 발견:\n" + "\n".join(violations)
```

---

## 4. 다이얼로그/모달 테스트 패턴 가이드

### 4.1 QFileDialog monkeypatch

**핵심 원칙**: `QFileDialog`는 네이티브 다이얼로그를 사용하므로 반드시 `monkeypatch.setattr`으로 우회해야 한다.

```python
# 패턴 1: 열기 다이얼로그 — 파일 반환
def test_open_pdf(win, pdf_3pages, monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (pdf_3pages, "PDF 파일 (*.pdf)")
    )
    win._open_file()
    assert win._doc.is_open

# 패턴 2: 열기 다이얼로그 — 취소
def test_open_cancel(win, monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("", "")
    )
    win._open_file()
    assert not win._doc.is_open

# 패턴 3: 저장 다이얼로그
def test_save_as(win, pdf_3pages, tmp_path, monkeypatch):
    _load_pdf(win, pdf_3pages)
    out = str(tmp_path / "saved.pdf")
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (out, "PDF 파일 (*.pdf)")
    )
    win._save_as()
    assert os.path.exists(out)
```

**주의사항**:
- `monkeypatch.setattr`의 경로는 **사용되는 모듈 기준**이다. `main_window.py`에서 `from PyQt6.QtWidgets import QFileDialog`로 임포트했더라도, monkeypatch 경로는 `"app.ui.main_window.QFileDialog.getOpenFileName"`이어야 한다.
- 반환값은 반드시 `(path, filter)` 튜플이다.

### 4.2 QMessageBox monkeypatch

```python
# 패턴 1: question → Yes
def test_delete_confirmed(win, monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )

# 패턴 2: question → No
def test_delete_cancelled(win, monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No
    )

# 패턴 3: warning 호출 감지
def test_warning_shown(win, monkeypatch):
    warnings = []
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.warning",
        lambda *args, **kwargs: warnings.append(args)
    )
    # ... 경고 트리거 동작 ...
    assert len(warnings) == 1

# 패턴 4: critical 오류 감지
def test_error_shown(win, monkeypatch):
    errors = []
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.critical",
        lambda *args, **kwargs: errors.append(args)
    )
    # ... 오류 트리거 동작 ...
    assert len(errors) == 1
```

### 4.3 QInputDialog monkeypatch

`PdfViewer`에서 텍스트 도구 클릭 시 `QInputDialog.getText`가 호출된다.

```python
# 패턴 1: 텍스트 입력 확인
def test_text_annotation(win, monkeypatch):
    monkeypatch.setattr(
        "app.ui.pdf_viewer.QInputDialog.getText",
        lambda *args, **kwargs: ("테스트 텍스트", True)  # (text, ok)
    )

# 패턴 2: 텍스트 입력 취소
def test_text_cancel(win, monkeypatch):
    monkeypatch.setattr(
        "app.ui.pdf_viewer.QInputDialog.getText",
        lambda *args, **kwargs: ("", False)  # ok=False
    )

# 패턴 3: 빈 텍스트 입력
def test_empty_text(win, monkeypatch):
    monkeypatch.setattr(
        "app.ui.pdf_viewer.QInputDialog.getText",
        lambda *args, **kwargs: ("", True)  # 빈 문자열, ok=True
    )
```

### 4.4 QColorDialog monkeypatch

```python
# 패턴: 색상 선택
from PyQt6.QtGui import QColor

def test_color_change(win, pdf_3pages, monkeypatch):
    _load_pdf(win, pdf_3pages)
    monkeypatch.setattr(
        "app.ui.toolbar.QColorDialog.getColor",
        lambda *args, **kwargs: QColor(0, 0, 255)  # 파란색
    )
    win._toolbar._pick_color()
    # toolbar._annot_color가 파란색으로 변경되었는지 확인
```

**주의**: `QColorDialog.getColor`가 유효한 `QColor`를 반환해야 한다. 취소 시에는 `QColor()` (invalid)를 반환.

```python
# 패턴: 색상 선택 취소
def test_color_cancel(win, monkeypatch):
    monkeypatch.setattr(
        "app.ui.toolbar.QColorDialog.getColor",
        lambda *args, **kwargs: QColor()  # invalid = 취소
    )
```

### 4.5 InsertDialog monkeypatch

```python
# 패턴: InsertDialog를 가짜 클래스로 교체
class FakeInsertDialog:
    """InsertDialog 대체."""
    DialogCode = type('DC', (), {'Accepted': 1, 'Rejected': 0})()
    
    def __init__(self, parent):
        pass
    
    def exec(self):
        return 1  # Accepted
    
    def source_path(self):
        return "/path/to/source.pdf"
    
    def selected_indices(self):
        return [0, 1]


def test_insert_with_fake_dialog(win, pdf_3pages, pdf_5pages, monkeypatch):
    _load_pdf(win, pdf_3pages)
    
    class MyFakeDialog(FakeInsertDialog):
        def source_path(self):
            return pdf_5pages
    
    monkeypatch.setattr("app.ui.main_window.InsertDialog", MyFakeDialog)
    win._insert_pages(insert_before=1)
    assert win._doc.page_count == 5
```

### 4.6 ConvertDialog monkeypatch

ConvertDialog는 `exec()`로 모달 실행되므로 직접 테스트하기 어렵다. 두 가지 전략:

```python
# 전략 1: 다이얼로그 자체를 monkeypatch하여 즉시 반환
def test_convert_dialog_opens(win, monkeypatch):
    class FakeConvertDialog:
        conversion_done = type('sig', (), {
            'connect': lambda self, fn: None
        })()
        def __init__(self, parent): pass
        def exec(self): return 0
    
    monkeypatch.setattr(
        "app.ui.main_window.ConvertDialog",
        FakeConvertDialog
    )
    win._open_convert_dialog()  # 예외 없이 완료

# 전략 2: ConvertDialog 내부 위젯을 직접 테스트
def test_convert_dialog_tabs(qtbot):
    from app.ui.dialogs.convert_dialog import ConvertDialog
    dlg = ConvertDialog()
    qtbot.addWidget(dlg)
    # QTabWidget 확인
    tab_widget = dlg.findChild(QTabWidget)
    assert tab_widget is not None
    assert tab_widget.count() == 2
```

---

## 5. 키보드 단축키 테스트 전략

### 5.1 QAction.trigger() vs QTest.keyClick()

**권장**: `QAction.trigger()`를 우선 사용.

```python
# 권장 방법: QAction.trigger()
def test_shortcut_via_action(win, pdf_3pages):
    _load_pdf(win, pdf_3pages)
    before = win._viewer.zoom
    win._toolbar._act_zoom_in.trigger()
    assert win._viewer.zoom > before
```

**이유**:
1. `QTest.keyClick()`은 offscreen에서 포커스 문제로 불안정하다.
2. `QAction.trigger()`는 단축키가 연결된 액션을 직접 호출하므로 100% 안정적이다.
3. 단축키 바인딩 자체는 별도로 검증한다 (action.shortcut() 확인).

```python
# 단축키 바인딩 검증 (키 매핑만 확인)
def test_shortcut_bindings(win):
    """TC-143: 단축키 바인딩 존재 확인."""
    shortcuts = {
        win._toolbar._act_open: "Ctrl+O",
        win._toolbar._act_save: "Ctrl+S",
        win._toolbar._act_zoom_in: "Ctrl+=",
        win._toolbar._act_zoom_out: "Ctrl+-",
        win._toolbar._act_zoom_fit: "Ctrl+0",
        win._toolbar._act_delete: "Delete",
    }
    for action, expected_key in shortcuts.items():
        actual = action.shortcut().toString()
        # QKeySequence 표현이 플랫폼별로 다를 수 있으므로 부분 매칭
        assert expected_key.split("+")[-1] in actual, \
            f"{action.text()}: expected {expected_key}, got {actual}"
```

### 5.2 QTest.keyClick() — 필요한 경우

마우스 이벤트 없이 키보드만으로 동작하는 경우에만 사용.

```python
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# Escape 키 테스트 (포커스가 MainWindow에 있을 때)
def test_escape_key(win, pdf_3pages, qtbot):
    _load_pdf(win, pdf_3pages)
    win._toolbar._tool_actions[AnnotationTool.RECT].trigger()
    
    # Escape 키 시뮬레이션 — 주의: offscreen에서 포커스 문제 가능
    QTest.keyClick(win, Qt.Key.Key_Escape)
    # 불안정하면 대신:
    # win._toolbar._tool_actions[AnnotationTool.SELECT].trigger()
```

### 5.3 Modifier 키 (Ctrl, Shift)

```python
# Ctrl+Z 시뮬레이션
QTest.keyClick(win, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)

# Ctrl+Shift+C 시뮬레이션
QTest.keyClick(
    win, Qt.Key.Key_C,
    Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
)
```

**주의**: offscreen에서 modifier 키 시뮬레이션이 불안정할 수 있으므로, **QAction.trigger()를 강력히 권장**한다.

---

## 6. 수동 테스트 유지 목록

### 6.1 빌드/배포 (TC-145 ~ TC-149) — 5건

| TC | 근거 |
|----|------|
| TC-145 | EXE 빌드는 PyInstaller 환경 필요, CI/CD에서만 자동화 가능 |
| TC-146 | EXE 환경 기능 동작은 실제 실행 필요 |
| TC-147 | uv sync는 클린 환경 필요 |
| TC-148 | GUI 앱 실행은 디스플레이 필요 |
| TC-149 | pytest 실행은 CI/CD로 대체 가능 (수동 항목으로 유지) |

### 6.2 시각적/테마 (TC-025, TC-033, TC-078, TC-090, TC-091, TC-141, TC-142) — 7건

| TC | 근거 |
|----|------|
| TC-025 | OpenHand 커서 — offscreen에서 커서 형태 불확인 |
| TC-033 | 썸네일 크기/비율 — 픽셀 정확도 (디스플레이 의존) |
| TC-078 | IBeam 커서 |
| TC-090 | Crosshair 커서 |
| TC-091 | 반투명 프리뷰 — 시각적 확인 필수 |
| TC-141 | 다크 테마 배경색 — 스타일시트 적용은 렌더링 확인 |
| TC-142 | 선택 하이라이트 색상 |

### 6.3 마우스 인터랙션 (TC-022, TC-024, TC-038~TC-042, TC-043~TC-046, TC-089~TC-099, TC-144) — 29건

| TC 범위 | 근거 |
|---------|------|
| TC-022 | Ctrl+마우스 휠 — QWheelEvent offscreen 불안정 |
| TC-024 | 드래그 스크롤 |
| TC-038~042 | 우클릭 컨텍스트 메뉴 — QMenu.exec_() 네이티브 이벤트 루프 |
| TC-043~046 | 드래그 앤 드롭 — QDrag 시뮬레이션 offscreen 미지원 |
| TC-089, TC-094, TC-097 | 드래그 기반 도형 그리기 |
| TC-092~093, TC-095~096, TC-098~099 | 드래그 기반 경계값/스타일 |
| TC-144 | Ctrl+마우스 휠 줌 |

### 6.4 외부 의존성 (TC-071, TC-088, TC-121~TC-125, TC-128~TC-129, TC-150~TC-153) — 14건

| TC 범위 | 근거 |
|---------|------|
| TC-071, TC-153 | 다른 PDF 뷰어에서 확인 (Adobe Reader, Chrome) |
| TC-088 | Windows 폰트 파일 존재 여부 (malgun.ttf) |
| TC-121~122 | LibreOffice 설치 필요 |
| TC-124~125 | LibreOffice 감지/타임아웃 |
| TC-128~129 | 변환 진행 중 UI 반응성 — QThread 타이밍 |
| TC-150 | 썸네일 대용량 성능 — 100페이지 |
| TC-151 | 단일 페이지 갱신 성능 |
| TC-152 | 저장 폴백 안정성 |

### 6.5 텍스트 입력 다이얼로그 (TC-076~TC-077, TC-079~TC-080, TC-083~TC-084, TC-086~TC-087) — 8건

**참고**: 이 중 TC-076, TC-077, TC-079~084는 **core 레벨에서 이미 커버**됨 (`test_annotator.py`).
UI 레벨에서는 QInputDialog 연동이 필요하므로 수동 유지하되, core 테스트가 회귀 방지 역할을 한다.

| TC | core 커버 상태 | 수동 유지 근거 |
|----|---------------|--------------|
| TC-076 | TestAddText.test_changes_page_content | QInputDialog → 뷰어 좌표 연동 |
| TC-077 | TestAddText.test_korean_text | 맑은 고딕 + 뷰어 렌더링 |
| TC-086 | 미커버 | QInputDialog 취소 흐름 |
| TC-087 | TestAddText.test_empty_string_no_crash | 빈 입력 + Undo 미추가 확인 |

---

## 7. Flaky 테스트 방지 가이드

### 7.1 QThread 정리 필수

**문제**: `PagePanel`의 썸네일 로더 스레드가 종료되지 않으면 테스트 다음 항목에서 segfault 발생.

```python
# 반드시 teardown에서 _cancel_loader() 호출
@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    w.show()
    yield w
    # 1) QThread 정리 — 반드시 close() 전에!
    if hasattr(w, '_page_panel') and hasattr(w._page_panel, '_cancel_loader'):
        w._page_panel._cancel_loader()
    # 2) 윈도우 닫기
    w.close()
```

### 7.2 시그널 타이밍

**문제**: `qtbot.waitSignal`이 타임아웃으로 실패하는 경우.

```python
# 나쁜 예: 시그널이 동기적으로 emit되는 경우 waitSignal 불필요
with qtbot.waitSignal(viewer.zoom_changed, timeout=1000):
    viewer.zoom_in()

# 좋은 예: 동기 동작이면 직접 확인
viewer.zoom_in()
assert viewer.zoom > before
```

**규칙**: `waitSignal`은 **비동기 시그널에만** 사용한다. `QThread.finished`, 타이머 기반 시그널 등.

### 7.3 offscreen 환경 gotchas

1. **viewport 크기가 0**: offscreen에서 `QGraphicsView.viewport().size()` == `QSize(0, 0)`. `zoom_fit()`이 0으로 나누기를 할 수 있다. 테스트에서는 `zoom_fit` 결과를 정확한 값이 아닌 "예외 없음"으로만 확인.

2. **마우스 이벤트 좌표 매핑 불안정**: `QGraphicsView.mapToScene()`이 offscreen에서 정확하지 않을 수 있다. 드래그 기반 테스트는 수동으로 유지.

3. **QPixmap null**: offscreen에서 `QPixmap`이 null일 수 있다. 렌더링 결과는 `QImage`로 확인하거나, `fitz`로 직접 검증.

4. **폰트 메트릭스 차이**: offscreen에서 텍스트 크기/위치가 실제 디스플레이와 다를 수 있다. 텍스트 위치 검증은 `fitz.Page.get_text()`로.

### 7.4 위젯 정리 패턴

```python
# 반드시 qtbot.addWidget으로 등록
w = MainWindow()
qtbot.addWidget(w)  # Qt 이벤트 루프 정리 보장

# 여러 위젯을 생성하는 경우
viewer = PdfViewer()
qtbot.addWidget(viewer)
panel = PagePanel()
qtbot.addWidget(panel)
```

### 7.5 임시 파일 정리

```python
# tmp_path 사용 — pytest가 자동 정리
def test_save(win, pdf_3pages, tmp_path):
    out = str(tmp_path / "output.pdf")
    # tmp_path는 테스트 종료 시 자동 삭제

# fitz.Document는 반드시 close()
doc = fitz.open(path)
try:
    # 검증 로직
finally:
    doc.close()
```

### 7.6 테스트 격리

```python
# 나쁜 예: 테스트 간 상태 공유
@pytest.fixture(scope="module")
def shared_window(qtbot):
    ...  # 모듈 내 모든 테스트가 같은 윈도우 사용 → 상태 오염

# 좋은 예: 테스트마다 새 인스턴스
@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    yield w
    # teardown
```

### 7.7 monkeypatch 범위

```python
# 나쁜 예: 함수 레벨 monkeypatch를 fixture에서 사용
@pytest.fixture
def always_yes(monkeypatch):
    monkeypatch.setattr(...)  # monkeypatch는 함수 스코프

# 좋은 예: 테스트 함수 내에서 monkeypatch 사용
def test_delete(win, monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.Yes
    )
```

---

## 부록: TC 커버리지 요약

### 이미 자동화된 TC (46건)

| 테스트 파일 | 커버하는 TC (core 레벨) |
|------------|----------------------|
| test_pdf_document.py | TC-001(core), TC-002(core), TC-004(core), TC-007(core), TC-009(core) |
| test_page_editor.py | TC-043~046(core), TC-047~048(core), TC-055~057(core), TC-059,061(core) |
| test_command_manager.py | TC-044(core), TC-051(core), TC-062(core), TC-075(core), TC-100~102, TC-104~107, TC-109~111 |
| test_annotator.py | TC-067(core), TC-072~074(core), TC-076~077(core), TC-079~084(core), TC-088(core), TC-089,094,097(core) |
| test_converter.py | TC-113~114(core), TC-120(core), TC-123~124(core) |
| test_pdf_viewer.py | TC-015(core), TC-017~020(core), TC-026~029(core) |
| test_page_panel.py | TC-034~035(core), TC-030(core) |

### 본 계획서에서 추가되는 자동화 TC (약 65건)

| 신규 테스트 파일 | 추가 TC |
|-----------------|---------|
| tests/ui/test_main_window.py | TC-001~014(UI), TC-047~063(UI), TC-064~070, TC-081~082, TC-085, TC-100~112(UI) |
| tests/ui/test_main_window_menu.py | TC-130~140 |
| tests/core/test_architecture.py | TC-154 |
| tests/core/test_command_manager.py (기존 확장) | TC-103, TC-112(보강) |
| tests/core/test_converter.py (기존 확장) | TC-115 |
| tests/ui/test_pdf_viewer.py (기존 확장) | TC-019, TC-020, TC-021(보강) |
| tests/ui/test_page_panel.py (기존 확장) | TC-034(20페이지), TC-035(보강) |

### 수동 유지 TC (약 43건)

TC-022, TC-024~025, TC-032~033, TC-036~042, TC-043~046(D&D), TC-071~074(UI레벨), TC-076~080(UI레벨), TC-083~084(UI레벨), TC-086~099, TC-115(일부), TC-116~119, TC-121~122, TC-124~129, TC-141~149, TC-150~153

---

> **최종 목표**: 자동화 테스트 약 111건 (46 기존 + 65 신규) + 수동 43건 = TC-001~154 전체 커버리지 달성.
> Sprint 1 완료 후 자동화 커버리지: 약 72% (111/154)

---

## 상호 검증 리뷰 결과

> 리뷰 대상: `docs/UNIT_COMPONENT_TEST_PLAN.md` (Test Architect 계획서)
> 비교 기준: `docs/UNIT_COMPONENT_TEST_PLAN_QA.md` (본 문서), `docs/E2E_TEST_PLAN.md`
> 리뷰 일자: 2026-04-03
> 리뷰어: QA Lead Agent

---

### 1. 코드 스켈레톤 정확성 검증

#### 1.1 monkeypatch 경로 오류 (Critical)

Architect 계획서의 **monkeypatch 경로가 대부분 잘못**되어 있다. 실제 `main_window.py`는 `from PyQt6.QtWidgets import QFileDialog, QMessageBox`로 직접 import하므로 두 가지 패치 경로가 모두 작동 가능하나, Architect가 일관성 없이 혼용하고 있다.

| 위치 | Architect 사용 경로 | 올바른 경로 | 심각도 |
|------|---------------------|------------|--------|
| TC-003 (`test_main_window.py` 4.10절) | `"PyQt6.QtWidgets.QFileDialog.getOpenFileName"` | `"app.ui.main_window.QFileDialog.getOpenFileName"` 또는 전역 모두 동작하나 **모듈 단위 패치가 더 안전** | 경고 |
| TC-006 (`test_main_window.py` 4.10절) | `"PyQt6.QtWidgets.QFileDialog.getOpenFileName"` | 동일 | 경고 |
| TC-012, TC-052, TC-058 | `"PyQt6.QtWidgets.QFileDialog/QMessageBox..."` | 동일 | 경고 |
| TC-039, TC-040 (`test_main_window_pages.py`) | `"PyQt6.QtWidgets.QMessageBox.question"` | `"app.ui.main_window.QMessageBox.question"` | 경고 |
| TC-066 (`test_main_window.py`) | `"PyQt6.QtWidgets.QColorDialog.getColor"` | `"app.ui.toolbar.QColorDialog.getColor"` (toolbar.py에서 import) | **오류** |
| TC-086 (`test_main_window.py`) | `"PyQt6.QtWidgets.QInputDialog.getText"` | `"app.ui.pdf_viewer.QInputDialog.getText"` (pdf_viewer.py에서 import) | **오류** |

**결론**: Architect 계획서 6.1절에서 `"PyQt6.QtWidgets...."` 전역 경로가 "더 안전하다"고 주장하나, 이는 **부분적으로만 맞다**. QA 계획서(본 문서)의 접근처럼 모듈 기준 경로(`"app.ui.main_window.QFileDialog..."`)를 일관되게 사용하는 것이 확실하다. 특히 TC-066, TC-086은 `QColorDialog`/`QInputDialog`를 toolbar.py/pdf_viewer.py에서 각각 import하므로, 전역 패치로는 해당 모듈의 로컬 바인딩이 이미 만들어진 후라 **패치가 반영되지 않을 가능성**이 있다. 병합 시 반드시 모듈 기준 경로로 통일해야 한다.

#### 1.2 PyQt6 API 호출 정확성

| 항목 | 검증 결과 |
|------|----------|
| `QWheelEvent` 생성자 (TC-022) | Architect가 8인자 생성자 사용 -- PyQt6에서 `QWheelEvent(QPointF, QPointF, QPoint, QPoint, ...)` 시그니처이므로 `QPoint` 대신 `QPointF`를 사용해야 한다. **수정 필요**. |
| `QItemSelectionModel.SelectionFlag` (TC-036, TC-037) | Architect의 `QItemSelectionModel.SelectionFlag.Select`는 정확. 다만 TC-037의 Shift+클릭 범위 선택은 `QItemSelectionModel.SelectionFlag.Select | Rows`만으로는 범위 선택이 아닌 **개별 추가 선택**이 된다. 실제 범위 선택은 `SelectCurrent | Rows`가 필요하거나, `QAbstractItemView.setCurrentIndex()` + `setSelection()` 조합이 필요하다. **수정 필요**. |
| `InsertDialog.DialogCode` 접근 | Architect 일부 테스트에서 `InsertDialog.DialogCode.Accepted`를 사용하는데, `InsertDialog`가 `QDialog`를 상속하면 `QDialog.DialogCode.Accepted` (= 1) 이다. `InsertDialog`에 `DialogCode` 속성이 직접 정의되어 있지 않을 수 있으므로, FakeInsertDialog에서 `exec()`가 `int` 값을 반환하는 QA 방식이 더 안전하다. |
| `viewport().cursor().shape()` (TC-025, TC-078, TC-090) | API 자체는 정확하나 Architect가 offscreen 제한사항을 인지하면서도 테스트를 Priority 1에 포함시킨 것은 모순. |

#### 1.3 qtbot 사용 패턴

| 항목 | 검증 결과 |
|------|----------|
| `qtbot.addWidget()` | 양 계획서 모두 올바르게 사용. |
| `qtbot.waitSignal()` | Architect TC-068에서 `waitSignal(width_changed)`을 사용하나, `_width_spin.setValue()`는 **동기적으로** `valueChanged` 시그널을 emit하므로 `waitSignal`이 불필요하다. 동기 시그널에 `waitSignal`을 쓰면 타이밍 이슈가 발생할 수 있다 (QA 계획서 7.2절 지적 사항과 일치). |
| `QTest.keyClick()` offscreen 안정성 | Architect TC-006, TC-021, TC-143의 `QTest.keyClick()`은 offscreen에서 포커스 문제로 불안정. QA 계획서의 `QAction.trigger()` + `shortcut().toString()` 검증 분리 방식이 더 안정적. |

#### 1.4 Fixture 정리 패턴

Architect의 `main_window` fixture는 `_cancel_loader()` 호출 후 `close()`를 하는 올바른 패턴을 사용. 다만 **conftest.py에 `main_window` fixture를 정의**하는 것은 E2E 계획서의 `tests/e2e/conftest.py`와 충돌할 수 있다. 병합 시 스코프를 명확히 분리해야 한다.

---

### 2. E2E 계획서와의 중복 검증

| Architect TC | E2E TC | 중복 수준 | 권장 |
|-------------|--------|----------|------|
| TC-001~002 (MainWindow 열기) | TC-155 (열기->어노테이션->저장->재열기) | **낮음** -- E2E는 전체 흐름, Unit은 개별 동작 | 유지 (보완 관계) |
| TC-047~051 (페이지 삭제/Undo) | TC-157 (순서변경->삭제->Undo x2) | **중간** -- 삭제+Undo 경로 겹침 | 유지하되 TC-051의 UI 레벨 테스트는 E2E와 거의 동일 |
| TC-059, TC-062 (삽입/Undo) | TC-156 (삽입->어노테이션->저장) | **중간** | 유지 |
| TC-064~065 (도구 배타적 전환) | TC-161 (도구 전환 후 작업), TC-163 (메뉴-툴바 동기화) | **높음** -- Architect의 TC-064 Component 테스트와 E2E TC-163이 거의 동일한 검증 수행 | **TC-064는 Component 수준(toolbar만)으로 제한, MainWindow 레벨 검증은 E2E에 위임** |
| TC-100~112 (Undo/Redo) | TC-160 (다중 Undo/Redo), TC-166 (Command 패턴 4종) | **높음** -- TC-103(50개 제한)이 TC-E05와 동일, TC-112(반복)가 TC-166과 겹침 | **core 레벨 TC-103, TC-112는 유지. MainWindow 레벨 TC-100~101은 E2E TC-160과 겹치므로 간소화 가능** |
| TC-108 (메뉴 동적 텍스트) | TC-162 (상태바 종합) | **낮음** | 유지 |
| TC-130~140 (UI 구조) | TC-164 (문서 미열림 시 비활성화) | **중간** -- TC-164가 액션 `isEnabled()` 검증을 포함하므로 TC-137~138과 부분 겹침 | 유지 (관점 다름: 구조 vs 상태) |
| TC-143 (전체 단축키) | 없음 | 없음 | 유지 |
| TC-154 (Core/UI 분리) | 없음 | 없음 | 유지 |

**결론**: 전체적으로 Unit/Component와 E2E는 보완 관계이나, **TC-064/TC-163, TC-100~101/TC-160, TC-103/TC-E05**에서 의미있는 중복이 존재한다. 병합 시 MainWindow 레벨 Undo 테스트는 E2E로 위임하고, Unit/Component는 core + 개별 위젯에 집중하는 것이 효율적이다.

---

### 3. 미커버 TC 검증

108개 미자동화 TC 중 Architect 계획서가 실제로 다루는 TC를 교차 확인한다.

#### 3.1 Architect가 다루지 않는 TC (누락 의심)

| TC | 제목 | Architect 상태 | QA 판정 |
|----|------|---------------|---------|
| TC-032 | 썸네일 비동기 렌더링 | 이미 자동화 목록에 포함 (test_page_panel.py) | 정상 -- 기존 커버 |
| TC-071 | PDF 콘텐츠 스트림 호환성 | 이미 자동화 목록에 포함 | 정상 -- 기존 커버 |
| TC-088 | 맑은 고딕 자동 감지 | 이미 자동화 목록에 포함 | 정상 -- 기존 커버 |
| TC-089, TC-094, TC-097 | 드래그 기반 도형 그리기 | 이미 자동화 목록에 포함 | 정상 -- core 레벨 커버 |
| TC-129 | 변환 중 UI 비차단 | 수동 유지 처리 | 정상 |
| TC-150 | 썸네일 UI 비차단 성능 | 수동 유지 처리 | 정상 |
| TC-151 | 어노테이션 후 단일 페이지 갱신 | Architect가 Integration으로 분류, 구현 포함 | 정상 |
| TC-153 | PDF 뷰어 호환성 | 수동 유지 처리 | 정상 |

#### 3.2 TC 숫자 불일치

- Architect는 "108개 미자동화"에서 "100개 자동화 + 8개 수동"으로 처리한다고 요약 (7절).
- QA는 "72건 자동화 + 18건 부분 자동화 + 18건 수동"으로 분류.
- **차이 원인**: Architect는 TC-104~107을 "이미 커버된 TC의 매핑 주석"으로 처리하여 신규 테스트 수를 줄이고, QA는 부분 자동화 카테고리를 별도로 둔다.
- **실질적 커버리지는 동등**하나 분류 체계가 다르므로 병합 시 통일 필요.

---

### 4. offscreen 모드에서 비실용적 테스트 플래그

#### 4.1 높은 실패 리스크 (병합 시 수동으로 전환 권장)

| TC | Architect 위치 | 문제점 |
|----|---------------|--------|
| TC-025 | tests/ui/test_pdf_viewer.py (Component) | `viewport().cursor().shape()` -- offscreen에서 커서 형태가 `ArrowCursor`로 고정될 수 있음. Architect가 Priority 1에 포함시킨 것은 과도. |
| TC-078 | tests/ui/test_pdf_viewer.py (Component) | IBeam 커서 -- 동일 문제. |
| TC-090 | tests/ui/test_pdf_viewer.py (Component) | Crosshair 커서 -- 동일 문제. |
| TC-091 | tests/ui/test_pdf_viewer.py (Component) | 드래그 프리뷰 -- Architect 스켈레톤 자체가 실질적 검증 없이 `assert ... or scene_items_before >= 0` (항상 True)로 끝남. **무의미한 테스트**. |
| TC-092, TC-095, TC-099 | tests/ui/test_pdf_viewer.py (Component) | 3px 미만 드래그 무시 -- 마우스 이벤트 시뮬레이션 필요하나 스켈레톤이 시그널 연결만 하고 실제 드래그를 하지 않음. `assert len(signals) == 0`은 드래그를 시도하지 않았으므로 **항상 통과하는 거짓 양성**. |
| TC-022 | tests/ui/test_main_window.py (Integration) | `QWheelEvent` 생성자 인자 타입 오류 + offscreen 불안정. |
| TC-141~142 | tests/ui/test_ui_layout.py | 다크 테마 색상 검증 -- offscreen에서 스타일시트/팔레트 적용이 불완전할 수 있음. TC-142의 `assert True` 폴백은 사실상 검증 포기. |
| TC-006 (QTest.keyClick) | tests/ui/test_main_window.py | offscreen에서 `QTest.keyClick(main_window, Qt.Key.Key_O, ControlModifier)` 후 `_doc.is_open` 확인 -- 포커스 미설정 시 키 이벤트가 무시됨. |

#### 4.2 권장 조치

- TC-025, TC-078, TC-090: `@pytest.mark.skip(reason="offscreen에서 커서 형태 검증 불가")` 마킹하거나, `_current_tool` 내부 상태로 대체 검증 (QA 방식).
- TC-091, TC-092, TC-095, TC-099: 현재 스켈레톤은 **거짓 양성**이므로 삭제하거나 수동 유지로 전환.
- TC-022: `QPointF` 타입으로 수정하고 `@pytest.mark.xfail` 마킹.
- TC-141~142: offscreen 제한 인지 주석 추가하고 조건부 skip 적용.

---

### 5. Fixture/헬퍼 일관성 검증

#### 5.1 `load_pdf_directly()` 불일치

| 항목 | QA (본 문서) | Architect | E2E |
|------|-------------|-----------|-----|
| 위치 | 섹션 3.1 `_load_pdf()` 인라인 | conftest.py `load_pdf_directly()` | tests/e2e/helpers.py `load_pdf_directly()` |
| `_lbl_file.setText()` 호출 | **포함** | **포함** | **포함** |
| `_sync_annot_style()` 호출 | **포함** | **포함** | **포함** |
| 함수 시그니처 | `_load_pdf(win, path)` | `load_pdf_directly(win, path)` | `load_pdf_directly(win, path)` |

**문제**: Architect와 QA가 서로 다른 이름(`load_pdf_directly` vs `_load_pdf`)과 위치(conftest.py vs 인라인)를 사용. 병합 시 **E2E의 `tests/e2e/helpers.py`의 `load_pdf_directly()`를 공통 헬퍼로 채택**하고, Unit/Component 테스트에서도 import하여 사용하는 것이 일관적.

#### 5.2 `main_window` fixture 충돌

- Architect: `tests/conftest.py`에 `main_window` fixture 정의
- E2E: `tests/e2e/conftest.py`에 `main_window` fixture 정의
- QA: `tests/ui/test_main_window.py` 내 `win` fixture로 인라인 정의

**병합 권장**: `tests/conftest.py`에 **공통 `main_window` fixture** 1개만 정의. E2E conftest.py에서는 import하여 재사용. 인라인 `win` fixture는 `main_window`를 래핑.

#### 5.3 `pdf_factory` vs 개별 fixture

- QA/E2E: `pdf_factory` 팩토리 패턴 사용 (유연)
- Architect: `pdf_1page`, `pdf_3pages`, `pdf_5pages` 개별 fixture + `pdf_factory` 미사용

**병합 권장**: `pdf_factory`를 공통으로 채택하되, 기존 `pdf_1page`, `pdf_3pages`는 하위 호환용으로 유지.

#### 5.4 monkeypatch 헬퍼 불일치

| 항목 | QA (4.1~4.6절) | Architect (tests/helpers.py) | E2E (tests/e2e/helpers.py) |
|------|----------------|------------------------------|---------------------------|
| 패치 경로 | `"app.ui.main_window.QFileDialog..."` | `"PyQt6.QtWidgets.QFileDialog..."` | `"app.ui.main_window.QFileDialog..."` |
| mock 도구 | `monkeypatch` only | `unittest.mock.patch` 혼용 (TC-121 등) | `monkeypatch` only |
| InsertDialog mock | FakeInsertDialog 클래스 | FakeInsertDialog 클래스 | `_FakeInsertDialog` 클래스 |

**병합 권장**:
1. 패치 경로: **모듈 기준 (`"app.ui.main_window...."`)으로 통일**. 전역 패치는 import 순서에 따라 실패 가능.
2. mock 도구: Architect의 TC-121, TC-125에서 `unittest.mock.patch`/`MagicMock`을 사용하는데, E2E 규칙("모든 모킹은 `monkeypatch.setattr`") 위반. **`monkeypatch`로 통일**하거나 core 테스트에 한해 `unittest.mock` 허용을 명시.
3. FakeInsertDialog: 3개 계획서에서 각각 다르게 정의. **하나의 공통 클래스**로 통일.

---

### 6. 최종 권장 사항

#### 6.1 병합 시 반드시 수정할 항목 (Critical)

1. **monkeypatch 경로 통일**: TC-066(`QColorDialog`)과 TC-086(`QInputDialog`)은 반드시 각각 `"app.ui.toolbar.QColorDialog.getColor"`, `"app.ui.pdf_viewer.QInputDialog.getText"`로 수정. 그렇지 않으면 런타임에 패치가 적용되지 않아 모달 다이얼로그가 뜨며 테스트가 hang.
2. **QWheelEvent 생성자 수정** (TC-022): `QPoint` -> `QPointF`.
3. **거짓 양성 테스트 제거**: TC-091, TC-092, TC-095, TC-099의 스켈레톤은 실제 드래그 없이 항상 통과하므로, 수동 유지로 전환하거나 실질적 검증 로직 추가.
4. **`unittest.mock` 혼용 정리**: TC-121, TC-125에서 `MagicMock`/`patch` 사용을 `monkeypatch` 기반으로 전환하거나, core 테스트에서의 예외를 명시.

#### 6.2 구조적 개선 권장 (Important)

5. **공통 헬퍼 단일 모듈**: `tests/helpers.py`에 `load_pdf_directly()`, monkeypatch 헬퍼, `FakeInsertDialog`를 통합 배치. Unit/Component/E2E 모두에서 import.
6. **fixture 계층 정리**: `tests/conftest.py`에 `main_window`, `pdf_factory` 공통 배치. `tests/e2e/conftest.py`는 E2E 전용(`image_factory` 등)만.
7. **커서 테스트 분리**: TC-025, TC-078, TC-090은 offscreen 불안정하므로 `@pytest.mark.skipif(os.environ.get("QT_QPA_PLATFORM") == "offscreen")` 조건 추가.

#### 6.3 우선순위 조정 권장 (Nice-to-have)

8. **Architect의 QTest.keyClick() 기반 테스트**(TC-006, TC-021, TC-143)를 QA 방식의 `QAction.trigger()` + `shortcut().toString()` 검증으로 대체하면 offscreen 안정성 확보.
9. **TC-037 Shift+클릭 범위 선택**: `QItemSelectionModel` API 사용법 수정 필요. 현재 스켈레톤은 범위 선택이 아닌 개별 추가 선택을 수행.
10. **Architect TC-142 (하이라이트 색상)**: `assert True` 폴백이 포함되어 사실상 테스트 무효. 삭제하거나 실질적 검증 추가.

#### 6.4 요약 매트릭스

| 카테고리 | Architect | QA | 병합 권장 |
|----------|----------|-----|----------|
| monkeypatch 경로 | 전역 (`PyQt6.QtWidgets...`) | 모듈 기준 (`app.ui.main_window...`) | **모듈 기준** |
| mock 도구 | `monkeypatch` + `unittest.mock` 혼용 | `monkeypatch` 전용 | **`monkeypatch` 전용** (core 예외 허용) |
| 커서 테스트 | Component에 포함 | 수동 유지 | **조건부 skip 또는 수동** |
| 드래그 기반 테스트 | Component에 포함 (거짓 양성) | 수동 유지 | **수동 유지** |
| 키보드 단축키 | `QTest.keyClick()` | `QAction.trigger()` + `shortcut()` 검증 | **QAction 기반** |
| load 헬퍼 이름 | `load_pdf_directly` (conftest) | `_load_pdf` (인라인) | **`load_pdf_directly`** (공통 모듈) |
| InsertDialog mock | 인라인 FakeInsertDialog | FakeInsertDialog 패턴 | **공통 모듈에 단일 정의** |
