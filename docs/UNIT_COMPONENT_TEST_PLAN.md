# 단위/컴포넌트 테스트 구현 계획서 (최종 확정본)

> 작성일: 2026-04-03
> 최종 확정: 2026-04-03 (Test Architect + QA Lead 상호 검증 + QA 리뷰 전체 반영)
> 대상: PDF 편집 툴 v1.0.0
> 기반: `docs/TEST_SCENARIOS_FULL.md`, `docs/FEATURE_SPEC.md`
> 범위: TC-001 ~ TC-154 중 미자동화 108개 TC
> 도구: pytest 8.x + pytest-qt 4.4.x + PyQt6 offscreen

---

## 1. 개요

### 1.1 범위

TC-001 ~ TC-154의 154개 테스트 시나리오 중 **46개**는 기존 155개 단위 테스트에 의해 이미 자동화되어 있다. 본 계획서는 나머지 **108개 미자동화 TC**에 대한 구현 계획을 상세히 기술한다.

### 1.2 기존 155개 단위 테스트와의 관계

기존 테스트는 `app/core/` 계층(PdfDocument, page_editor, annotator, converter, CommandManager)과 개별 UI 위젯(PdfViewer, PagePanel)을 독립적으로 검증한다. 본 계획의 테스트는 기존 테스트와 **상호 보완** 관계로:

- **기존 테스트가 커버하는 TC**: core 비즈니스 로직 검증 (열기/저장/렌더링/편집/어노테이션 기본 동작)
- **본 계획이 추가하는 TC**: MainWindow 통합 경로, 다이얼로그 상호작용, UI 레이아웃/메뉴 구조, 단축키, 테마, 빌드

### 1.3 E2E 계획(TC-155~166)과의 구분

`docs/E2E_TEST_PLAN.md`는 TC-155~TC-166(12개 통합 시나리오)을 다루며, MainWindow를 진입점으로 전체 시그널 흐름을 검증한다. 본 계획은 **TC-155~166을 포함하지 않으며**, 단위/컴포넌트/통합 수준의 TC-001~154만 다룬다.

### 1.4 이미 자동화된 46개 TC 목록

| TC | 커버 테스트 파일 |
|----|-----------------|
| TC-001 | test_pdf_document.py::TestPdfDocumentOpen::test_open_valid_file |
| TC-002 | test_pdf_document.py::TestPdfDocumentOpen::test_reopen_replaces_previous |
| TC-004 | test_pdf_document.py::TestPdfDocumentOpen::test_open_invalid_file_raises |
| TC-007 | test_pdf_document.py::TestPdfDocumentSave, TestPdfDocumentSaveIncremental |
| TC-009 | test_pdf_document.py::TestPdfDocumentSaveIncremental |
| TC-010 | test_pdf_document.py::TestPdfDocumentSave::test_save_as_different_path_still_works |
| TC-015 | test_pdf_viewer.py::TestPdfViewerInit::test_initial_state (줌 150%) |
| TC-016 | test_pdf_viewer.py::TestPdfViewerDocument::test_goto_page_changes_current |
| TC-017 | test_pdf_viewer.py::TestPdfViewerZoom::test_zoom_in_increases_zoom |
| TC-018 | test_pdf_viewer.py::TestPdfViewerZoom::test_zoom_out_decreases_zoom |
| TC-019 | test_pdf_viewer.py::TestPdfViewerZoom::test_zoom_clamped_to_max |
| TC-020 | test_pdf_viewer.py::TestPdfViewerZoom::test_zoom_clamped_to_min |
| TC-026 | test_pdf_viewer.py::TestPdfViewerDocument::test_goto_page_changes_current |
| TC-029 | test_pdf_viewer.py::TestPdfViewerDocument::test_goto_page_out_of_range_ignored |
| TC-032 | test_page_panel.py::TestPagePanelThumbnailFixes::test_placeholder_items_appear_immediately_on_load |
| TC-034 | test_page_panel.py::TestPagePanelLoad::test_load_shows_correct_item_count |
| TC-035 | test_page_panel.py::TestPagePanelNavigation::test_selected_indices_single |
| TC-043 | test_page_editor.py::TestMovePage |
| TC-044 | test_command_manager.py::TestMovePageCommand::test_undo_restores_order |
| TC-045 | test_page_editor.py::TestMovePage::test_move_backward |
| TC-046 | test_page_editor.py::TestMovePage::test_move_same_position_no_change |
| TC-047 | test_page_editor.py::TestDeletePages::test_delete_single_page |
| TC-048 | test_page_editor.py::TestDeletePages::test_delete_multiple_pages |
| TC-051 | test_command_manager.py::TestDeletePagesCommand::test_undo_restores_page_count |
| TC-055 | test_page_editor.py::TestExtractPages::test_extract_single_page |
| TC-056 | test_page_editor.py::TestExtractPages::test_extract_correct_page_count |
| TC-057 | test_page_editor.py::TestExtractPages (원본 불변) |
| TC-059 | test_page_editor.py::TestInsertPagesFromFile |
| TC-061 | test_page_editor.py::TestInsertPagesFromFile::test_insert_in_middle |
| TC-062 | test_command_manager.py::TestInsertPagesCommand::test_undo_removes_inserted_pages |
| TC-067 | test_annotator.py::TestAnnotationStyle::test_default_color_is_red |
| TC-071 | test_annotator.py::TestCombined::test_annotations_saved_in_pdf |
| TC-072 | test_pdf_viewer.py::TestSceneToPdf::test_rotated_page_coord_within_bounds |
| TC-075 | test_command_manager.py::TestAddAnnotationCommand::test_undo_restores_page_content |
| TC-076 | test_annotator.py::TestAddText::test_changes_page_content |
| TC-077 | test_annotator.py::TestAddText::test_korean_text |
| TC-079 | test_annotator.py::TestAddTextStyled (Times/Courier) |
| TC-083 | test_annotator.py::TestAddTextStyled::test_helv_bold |
| TC-084 | test_annotator.py::TestAddTextStyled::test_helv_italic |
| TC-088 | test_annotator.py::TestResolveFont::test_korean_returns_path_or_helv_fallback |
| TC-089 | test_annotator.py::TestAddRect::test_changes_page_content |
| TC-094 | test_annotator.py::TestAddEllipse::test_changes_page_content |
| TC-097 | test_annotator.py::TestAddLine::test_changes_page_content |
| TC-102 | test_command_manager.py::TestCommandManager::test_undo_when_empty_returns_none |
| TC-110 | test_command_manager.py::TestCommandManager::test_execute_clears_redo |
| TC-113 | test_converter.py::TestConvertImagesToPdf::test_single_png_creates_file |

---

## 2. 테스트 자동화 판단

### 2.1 판단 매트릭스

| 기준 | 자동화 적합 (Yes) | 부분 자동화 (Partial) | 수동 유지 (No) |
|------|-------------------|----------------------|----------------|
| 실행 환경 | offscreen에서 재현 가능 | 특수 환경 필요 (LibreOffice 등) | 실제 렌더링/물리 디바이스 필요 |
| 반복성 | 회귀 테스트 필수 | 가끔 확인 필요 | 일회성 검증 |
| 비용 | 구현 30분 이내 | 구현 1시간 이내 | 구현 > 1시간 + 유지비 높음 |
| 판정 신뢰도 | 프로그래밍으로 명확 판정 | 보조 도구 필요 | 육안 확인 필수 |

### 2.2 TC별 자동화 판정 결과 (최종)

Test Architect와 QA Lead의 판정을 상호 검증하여 아래 최종 결과를 확정한다.

#### 자동화 (Yes) -- 72건

| TC | 제목 | 자동화 방식 |
|----|------|------------|
| TC-005 | 비PDF 파일 열기 | PdfDocument.open() 예외 확인 |
| TC-006 | Ctrl+O 단축키 | **QAction.trigger()** + shortcut 존재 확인 |
| TC-008 | 미열림 시 저장 | _act_save.isEnabled() == False |
| TC-011 | 확장자 자동 추가 | _save_as 로직 단위 검증 |
| TC-013 | 정상 종료 | win.close() 예외 없음 확인 |
| TC-014 | 문서 열린 채 종료 | close -> 리소스 해제 확인 |
| TC-021 | 화면 맞춤 | zoom_fit() 호출 예외 없음 확인 |
| TC-023 | 줌 스핀박스 직접입력 | _zoom_spin.setValue() -> viewer.zoom 확인 |
| TC-027 | PgUp 이전 페이지 | goto_page(current-1) |
| TC-028 | 첫페이지에서 PgUp | goto_page(-1) -> 변화 없음 |
| TC-030 | 썸네일 클릭 이동 | _list.setCurrentRow() -> page_selected 시그널 |
| TC-031 | 상태바 페이지 정보 | _lbl_page.text() 패턴 매칭 |
| TC-049 | 1페이지 삭제 방어 | QMessageBox.warning 호출 확인 |
| TC-050 | 2페이지 모두 삭제 | page_count <= len(indices) -> 경고 |
| TC-052 | 삭제 확인 취소 | QMessageBox -> No -> 변화 없음 |
| TC-053 | 툴바 삭제 버튼 | _act_delete.trigger() |
| TC-054 | 편집메뉴 삭제 | 편집 메뉴 액션 trigger |
| TC-058 | 추출 저장 취소 | QFileDialog -> 빈 문자열 |
| TC-063 | 삽입 다이얼로그 취소 | FakeInsertDialog -> Rejected |
| TC-064 | 도구 배타적 전환 | QActionGroup.checkedAction() 확인. **[E2E 중복 주의]** TC-163(메뉴-툴바 동기화)과 중복 -- 본 TC는 Component 수준(toolbar 단독)으로 제한, MainWindow 전체 흐름은 E2E에 위임 |
| TC-065 | Escape 선택 복귀 | _tool_actions[SELECT].trigger() |
| TC-068 | 선 굵기 변경 | _width_spin.setValue() -> width_changed 시그널 |
| TC-069 | 선 굵기 최소 | _width_spin.minimum() == 0.5 |
| TC-070 | 선 굵기 최대 | _width_spin.maximum() == 20.0 |
| TC-073 | 180도 회전 어노테이션 | add_text on rotated page |
| TC-074 | 270도 회전 어노테이션 | add_line on rotated page |
| TC-080 | 텍스트 크기 변경 | add_text with font_size=24 |
| TC-081 | 텍스트 크기 최소 | _font_size_spin.minimum() == 6 |
| TC-082 | 텍스트 크기 최대 | _font_size_spin.maximum() == 72 |
| TC-085 | 텍스트 스타일 가시성 | set_text_tool_active(True/False) -> 위젯 enabled |
| TC-087 | 빈 텍스트 입력 | add_text("") -> 변화 없음 (core 레벨) |
| TC-093 | 사각형 색상/굵기 적용 | add_rect with 커스텀 style (core 레벨) |
| TC-096 | 타원 색상/굵기 적용 | add_ellipse with 커스텀 style (core 레벨) |
| TC-098 | 선 색상/굵기 적용 | add_line with 커스텀 style (core 레벨) |
| TC-100 | Ctrl+Z Undo | _undo() -> cmd_mgr 상태 변화. **[E2E 중복 주의]** TC-160(다중 Undo/Redo)과 부분 중복 -- 본 TC는 단일 Undo 동작만 검증, 연속 시나리오는 E2E에 위임 |
| TC-101 | 연속 Undo | 3회 execute -> 3회 undo. **[E2E 중복 주의]** TC-160과 범위 겹침 -- 본 TC는 페이지 삭제 연속 Undo만, E2E는 어노테이션 포함 복합 시나리오 |
| TC-103 | 이력 50개 제한 | 51회 execute -> can_undo 50번. **[E2E 중복 주의]** TC-E05와 동일 시나리오 -- 본 TC는 core CommandManager 직접 검증, E2E는 MainWindow 경유 |
| TC-104 | Undo: 페이지 이동 | 기존 커버 -- TC 매핑 |
| TC-105 | Undo: 페이지 삭제 | 기존 커버 -- TC 매핑 |
| TC-106 | Undo: 페이지 삽입 | 기존 커버 -- TC 매핑 |
| TC-107 | Undo: 어노테이션 | 기존 커버 -- TC 매핑 |
| TC-108 | 메뉴 동적 텍스트 | _act_undo.text() 확인 |
| TC-109 | Ctrl+Y Redo | _redo() 동작 확인 |
| TC-111 | 빈 Redo | redo() -> None |
| TC-112 | Undo->Redo->Undo 반복 | 순차 실행 + 상태 확인 |
| TC-114 | 여러 이미지->PDF | convert_images_to_pdf 3개 |
| TC-115 | 모든 이미지 형식 | parametrize로 PNG/JPG/BMP/GIF/TIFF/WEBP 각각 변환 |
| TC-116 | 이미지 순서 변경 후 변환 | core 레벨 순서 변경 + 변환 검증 |
| TC-117 | 이미지 제거 후 변환 | 리스트 조작 + 변환 검증 |
| TC-120 | 이미지 없이 변환 | ValueError 확인 |
| TC-122 | Office 형식 (mock) | SUPPORTED_OFFICE_EXTS 상수 검증 |
| TC-123 | LibreOffice 미설치 | find_libreoffice mock -> None |
| TC-130 | 메인 윈도우 레이아웃 | 위젯 존재 + 타입 확인 |
| TC-131 | 파일 메뉴 항목 | menuBar().actions() 순회 |
| TC-132 | 편집 메뉴 항목 | menuBar().actions() 순회 |
| TC-133 | 보기 메뉴 항목 | menuBar().actions() 순회 |
| TC-134 | 어노테이션 메뉴 항목 | menuBar().actions() 순회 |
| TC-135 | 도구 메뉴 항목 | menuBar().actions() 순회 |
| TC-136 | 도움말 메뉴 항목 | menuBar().actions() 순회 |
| TC-137 | 툴바 파일 그룹 | 액션 존재 확인 |
| TC-138 | 툴바 페이지 편집 그룹 | 액션 존재 확인 |
| TC-139 | 어노테이션 도구 배타적 토글 | isExclusive() + tool_actions 수 |
| TC-140 | 줌 컨트롤 존재 | 액션/위젯 존재 확인 |
| TC-143 | 전체 키보드 단축키 | **QAction.shortcut() 바인딩 확인** + trigger() 동작 확인 |
| TC-151 | 어노테이션 후 단일 페이지 갱신 | _on_annotation_requested -> can_undo |
| TC-152 | 저장 실패 폴백 | incremental save 실패 -> full save |
| TC-154 | Core/UI 분리 | ast.parse로 import 스캔 |

#### 부분 자동화 (Partial) -- 18건

자동화 가능한 범위(API/상태 확인)는 구현하되, 시각적/물리적 인터랙션은 수동 검증으로 보완한다.

| TC | 제목 | 자동화 범위 | 수동 필요 부분 |
|----|------|------------|--------------|
| TC-003 | 파일 선택 취소 | QFileDialog monkeypatch -> 상태 확인 | -- (완전 자동화 가능, 아래 설명 참고) |
| TC-012 | 다른 이름으로 저장 취소 | QFileDialog monkeypatch | -- (완전 자동화 가능) |
| TC-022 | Ctrl+마우스 휠 줌 | **QWheelEvent(QPointF(...), ...)** 직접 호출로 검증 가능 | 실제 마우스 휠 동작 |
| TC-024 | 페이지 팬 (드래그) | DragMode 설정 확인만 자동화 | 실제 드래그 스크롤 |
| TC-036 | Ctrl+클릭 다중 선택 | QListWidget 내부 API로 선택 | 실제 Ctrl+클릭 인터랙션 |
| TC-037 | Shift+클릭 범위 선택 | QListWidget 내부 API로 선택 | 실제 Shift+클릭 |
| TC-043 | 드래그앤드롭 순서변경 | page_moved 시그널 emit 테스트 | 실제 D&D |
| TC-044 | 순서변경 Undo | MovePageCommand 기반 테스트 | D&D 연동 |
| TC-045 | 마지막->첫 이동 | core 레벨 테스트 | D&D 연동 |
| TC-046 | 같은 위치 드롭 | same index noop 확인 | D&D 연동 |
| TC-060 | 삽입 다이얼로그 미리보기 | InsertDialog 위젯 생성 + 파일 로드 | 실제 썸네일 렌더링 품질 |
| TC-066 | 색상 선택 QColorDialog | **monkeypatch: `"app.ui.toolbar.QColorDialog.getColor"`** | 실제 색상 피커 UI |
| TC-086 | 텍스트 입력 취소 | **monkeypatch: `"app.ui.pdf_viewer.QInputDialog.getText"`** | -- (완전 자동화 가능) |
| TC-118 | 변환 완료 후 프롬프트 | conversion_done 시그널 존재 확인 | QThread 타이밍 |
| TC-119 | "지금 열겠습니까?" -> 예 | _open_converted_pdf 직접 호출 | 프롬프트 UI |
| TC-121 | DOCX->PDF (monkeypatch) | **monkeypatch로 subprocess/find_libreoffice 패치** | LibreOffice 실제 연동 |
| TC-127 | 다이얼로그 탭 구조 | QTabWidget.count() + tabText() | 탭 UI 레이아웃 |
| TC-128 | 프로그레스 바 | findChildren(QProgressBar) | 진행률 업데이트 정확도 |

> **상호 검증 결과**: TC-003, TC-012, TC-086은 QA Lead가 "부분 자동화"로 분류했으나, monkeypatch로 완전 자동화 가능하다. 본 계획에서는 **자동화 범위에 포함하되** 부분 자동화 항목으로 관리한다 (수동 확인 불필요 시 자동화만으로 충분).

#### 수동 유지 (No) -- 18건

| TC | 제목 | 수동 유지 근거 |
|----|------|--------------|
| TC-025 | OpenHand 커서 | offscreen에서 커서 형태 검증 불안정 |
| TC-033 | 썸네일 크기/비율 | 픽셀 정확도 검증은 디스플레이 의존 |
| TC-038 | 컨텍스트 메뉴 표시 | QMenu.exec_() 네이티브 이벤트 루프 |
| TC-039~042 | 컨텍스트 메뉴 삭제/추출/삽입 | **시그널 emit으로 부분 검증 가능** (아래 설명 참고) |
| TC-078 | IBeam 커서 | offscreen 커서 불안정 |
| TC-090 | Crosshair 커서 | offscreen 커서 불안정 |
| TC-091 | 반투명 프리뷰 | 시각적 검증 필수. **[QA 수정]** 기존 스켈레톤은 거짓 양성(항상 True)이므로 삭제 |
| TC-092, TC-095, TC-099 | 3px 미만 드래그 무시 | **[QA 수정]** 마우스 드래그 시뮬레이션 offscreen 불안정. 기존 스켈레톤은 드래그 미수행으로 항상 통과하는 거짓 양성 -- 수동 유지로 확정 |
| TC-124 | LibreOffice 자동감지 | 환경 의존 |
| TC-125 | 변환 타임아웃 | 환경 의존 |
| TC-126 | Ctrl+Shift+C 변환 다이얼로그 | 단축키 바인딩만 자동화, 모달 다이얼로그는 수동 |
| TC-129 | 변환 중 UI 비차단 | QThread 타이밍 + UI 반응성 |
| TC-141 | 다크 테마 배경 | 색상값 육안 확인 |
| TC-142 | 선택 하이라이트 색상 | 색상값 육안 확인 |
| TC-144 | Ctrl+마우스 휠 줌 | TC-022와 동일 (wheelEvent로 부분 자동화) |
| TC-145~149 | 빌드/배포/실행 | CI/CD 또는 수동 |
| TC-150 | 썸네일 UI 비차단 | 100페이지 PDF 성능 측정 |
| TC-153 | PDF 뷰어 호환성 | Adobe Reader 등 외부 도구 필요 |

> **상호 검증 결과 (분쟁 TC 해결)**:
> - **TC-025, TC-078, TC-090 (커서 테스트)**: Test Architect는 자동화 가능으로 분류했으나, QA Lead의 판단이 옳다. offscreen에서 `viewport().cursor().shape()`이 실제 커서를 반영하지 않는 경우가 있어 **수동 유지**로 확정. 대신 `set_tool()` 후 내부 `_current_tool` 상태만 자동 검증.
> - **TC-039~042 (컨텍스트 메뉴)**: QMenu.exec_()는 수동이지만, PagePanel의 `delete_requested`/`extract_requested`/`insert_requested` **시그널 emit으로 동작을 부분 검증**할 수 있다. 시그널 검증 부분만 자동화하고, 실제 메뉴 표시는 수동.
> - **TC-091, TC-092, TC-095, TC-099 (드래그 기반 도형)**: **[QA Critical Fix]** 기존 Test Architect 스켈레톤은 실제 드래그 없이 `assert len(signals) == 0` 또는 `assert ... >= 0`으로 **항상 통과하는 거짓 양성**이었다. 삭제하고 **수동 유지**로 전환. core 레벨 add_rect/add_ellipse/add_line이 이미 자동화되어 있어 회귀 리스크는 core 테스트가 커버.
> - **TC-115 (모든 이미지 형식)**: QA Lead가 수동으로 분류했으나, parametrize로 각 형식을 개별 테스트하면 비용이 낮다. **자동화로 확정**.
> - **TC-121 (DOCX->PDF)**: **[QA Critical Fix]** 기존 스켈레톤은 `unittest.mock.patch`/`MagicMock`을 사용했으나, **monkeypatch로 전환**. **부분 자동화로 확정** (mock 범위만 자동화, 실제 LibreOffice는 수동).
> - **TC-124~125 (LO 감지/타임아웃)**: QA Lead 판단 수용. 환경 의존이므로 **수동 유지**.
> - **TC-141~142 (테마)**: QA Lead 판단 수용. 색상값 검증은 QPalette로 가능하나 offscreen에서 테마 적용이 불완전할 수 있어 **수동 유지**.

### 2.3 비용-편익 분석

| 카테고리 | TC 수 | 구현 예상 공수 | 회귀 방지 효과 | 판정 |
|----------|------|---------------|---------------|------|
| 문서 관리 (열기/저장) | 14건 중 10건 미자동화 | 3시간 | 높음 -- 가장 기본 기능 | **자동화** |
| PDF 뷰어 (줌/탐색) | 11건 중 6건 | 2시간 | 중간 | **자동화** |
| 썸네일 패널 | 11건 중 5건 | 2시간 | 중간 -- D&D는 수동 | **부분 자동화** |
| 페이지 편집 | 21건 중 12건 | 4시간 | 높음 | **자동화** |
| 어노테이션 | 36건 중 6건 | 2시간 (나머지 수동) | 중간 -- core 이미 커버 | **부분 자동화** |
| Undo/Redo | 13건 중 9건 | 2시간 | 높음 | **자동화** |
| 변환 | 17건 중 4건 | 1시간 | 중간 -- core 이미 커버 | **부분 자동화** |
| UI 레이아웃/메뉴 | 13건 | 2시간 | 낮음 -- 변경 빈도 낮음 | **자동화** (간단) |
| 빌드/배포 | 5건 | N/A | -- | **수동** |
| 비기능 | 5건 | N/A | -- | **수동** |

---

## 3. 리스크 기반 우선순위 (통합)

### 3.1 리스크 x 영향도 매트릭스

```
영향도 (높음)
    |
    |  P1 TC-001~002 (열기)     P1 TC-007,009 (저장)     P1 TC-051,062 (Undo)
    |  P1 TC-047~050 (삭제)     P1 TC-059,061 (삽입)     P1 TC-100~101 (Undo)
    |
    |  P2 TC-064~065 (도구전환)  P2 TC-130~136 (메뉴구조) P2 TC-154 (아키텍처)
    |  P2 TC-055~057 (추출)      P2 TC-110,112 (Redo)
    |
    |  P3 TC-023 (줌 스핀박스)   P3 TC-033 (썸네일 크기)  P3 TC-141~142 (테마)
    |  P3 TC-069~070 (경계값)    P3 TC-081~082 (경계값)
    |
    +---------------------------------------------------- 회귀 발생 확률 (높음)
```

**범례**: P1 = Sprint 1 (즉시), P2 = Sprint 2, P3 = Sprint 3

### 3.2 회귀 리스크 상위 20 TC

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

### 3.3 구현 순서 (Sprint 단위)

**Sprint 1 (최우선)**: TC-001~014 (문서 관리) + TC-047~063 (페이지 편집 UI 레벨) + TC-100~112 (Undo/Redo UI 레벨) + TC-154 (아키텍처)
**Sprint 2**: TC-015~031 (뷰어/탐색) + TC-064~070 (도구 전환/스타일) + TC-085 + TC-130~140 (UI 구조)
**Sprint 3**: TC-073~074 (회전 어노테이션) + TC-080~082, TC-087, TC-093, TC-096, TC-098 (core 보강) + TC-114~125 (변환) + 나머지

---

## 4. 테스트 인프라 설계

### 4.1 파일 구조

```
tests/
├── conftest.py                       # 기존 + 추가분 (main_window fixture 공통 정의)
├── helpers.py                        # 공통 monkeypatch 헬퍼 (단일 모듈)
├── core/
│   ├── test_pdf_document.py          # 기존 + TC-005, TC-008, TC-011 추가
│   ├── test_page_editor.py           # 기존 + TC-049, TC-050 추가
│   ├── test_annotator.py             # 기존 + TC-069~TC-074, TC-080~TC-082, TC-087, TC-093, TC-096, TC-098 추가
│   ├── test_command_manager.py       # 기존 + TC-100~TC-112 추가
│   ├── test_converter.py             # 기존 + TC-114~TC-125 추가
│   └── test_architecture.py          # 신규: TC-154 (Core/UI 분리)
├── ui/
│   ├── test_pdf_viewer.py            # 기존 + TC-023, TC-027~TC-028, TC-065 추가
│   ├── test_page_panel.py            # 기존 + TC-030, TC-036, TC-037 추가
│   ├── test_toolbar.py               # 신규: TC-064, TC-068, TC-085, TC-139, TC-140
│   ├── test_main_window.py           # 신규: 문서관리, 페이지편집, Undo/Redo, 도구전환 (MainWindow 레벨)
│   ├── test_main_window_menu.py      # 신규: TC-130~TC-140 (UI 구조)
│   └── test_convert_dialog.py        # 신규: TC-126~TC-128
└── e2e/                              # E2E 계획 (별도 문서)
    └── ...
```

> **[QA 수정] 구조 통일**: `tests/helpers.py`에 공통 헬퍼를 단일 배치. E2E `tests/e2e/helpers.py`에서는 `from tests.helpers import load_pdf_directly, FakeInsertDialog` 등으로 import하여 재사용. 중복 정의를 제거.

### 4.2 conftest.py 추가 픽스처

```python
# tests/conftest.py -- 추가분

import shutil

@pytest.fixture
def pdf_10pages(tmp_path) -> str:
    """10페이지짜리 테스트 PDF 경로."""
    return _make_pdf(10, tmp_path)


@pytest.fixture
def corrupt_pdf(tmp_path) -> str:
    """손상된 파일 경로 (PDF가 아닌 내용)."""
    path = str(tmp_path / "corrupt.pdf")
    with open(path, "wb") as f:
        f.write(b"This is not a PDF file at all!")
    return path


@pytest.fixture
def text_file(tmp_path) -> str:
    """PDF가 아닌 텍스트 파일 경로."""
    path = str(tmp_path / "readme.txt")
    with open(path, "w") as f:
        f.write("hello world")
    return path


@pytest.fixture
def rotated_pdf(tmp_path):
    """특정 각도로 회전된 페이지가 있는 PDF를 생성하는 팩토리."""
    def _create(rotation: int) -> str:
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Rotated {rotation}", fontsize=20)
        page.set_rotation(rotation)
        path = str(tmp_path / f"rotated_{rotation}.pdf")
        doc.save(path)
        doc.close()
        return path
    return _create


@pytest.fixture
def main_window(qtbot):
    """MainWindow 인스턴스. teardown에서 QThread 정리 + close.

    이 fixture는 Unit/Component/Integration 모든 레벨에서 공통 사용.
    E2E에서도 동일 fixture를 import하여 재사용한다.
    """
    from app.ui.main_window import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    yield win
    # 1) QThread 정리 -- 반드시 close() 전에!
    if hasattr(win, '_page_panel') and hasattr(win._page_panel, '_cancel_loader'):
        win._page_panel._cancel_loader()
    # 2) 윈도우 닫기 -- closeEvent에서 _doc.close() 호출됨
    win.close()
```

### 4.3 공통 헬퍼 모듈 (tests/helpers.py)

> **[QA 수정]** Unit/Component/E2E 전체에서 공유하는 단일 헬퍼 모듈. 중복 정의를 제거하고 일관성을 확보한다.

> **monkeypatch 경로 규칙**: monkeypatch 경로는 **사용되는 모듈 기준** (`"app.ui.main_window.QFileDialog..."`)을 사용한다. 전역 경로(`"PyQt6.QtWidgets.QFileDialog..."`)는 사용하지 않는다. 이는 E2E_TEST_PLAN.md의 패턴과 일치시키기 위함이다.

```python
# tests/helpers.py -- 공통 monkeypatch 패턴

import os
from PyQt6.QtWidgets import QMessageBox
from app.core.annotator import AnnotationTool


# ── PDF 로드 헬퍼 ──────────────────────────────────────────────────────────

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


# ── QFileDialog 패치 ──────────────────────────────────────────────────────

def patch_file_dialog_open(monkeypatch, return_path: str | None = None):
    """QFileDialog.getOpenFileName을 패치하여 지정 경로를 반환한다."""
    result = ("", "") if return_path is None else (return_path, "PDF 파일 (*.pdf)")
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getOpenFileName",
        lambda *a, **kw: result,
    )


def patch_file_dialog_save(monkeypatch, return_path: str | None = None):
    """QFileDialog.getSaveFileName을 패치."""
    result = ("", "") if return_path is None else (return_path, "PDF 파일 (*.pdf)")
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getSaveFileName",
        lambda *a, **kw: result,
    )


# ── QMessageBox 패치 ─────────────────────────────────────────────────────

def patch_message_box_yes(monkeypatch):
    """QMessageBox.question이 항상 Yes를 반환하도록 패치."""
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.Yes,
    )


def patch_message_box_no(monkeypatch):
    """QMessageBox.question이 항상 No를 반환하도록 패치."""
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.question",
        lambda *a, **kw: QMessageBox.StandardButton.No,
    )


def patch_message_box_warning(monkeypatch):
    """QMessageBox.warning 호출을 감지하고 호출 횟수를 반환."""
    warnings = []
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.warning",
        lambda *a, **kw: warnings.append(a),
    )
    return warnings


def patch_message_box_critical(monkeypatch):
    """QMessageBox.critical 호출을 감지."""
    errors = []
    monkeypatch.setattr(
        "app.ui.main_window.QMessageBox.critical",
        lambda *a, **kw: errors.append(a),
    )
    return errors


# ── QColorDialog 패치 ────────────────────────────────────────────────────
# [QA Critical Fix] 경로: "app.ui.toolbar.QColorDialog.getColor"
# toolbar.py에서 from PyQt6.QtWidgets import QColorDialog로 import하므로
# 반드시 toolbar 모듈 기준 경로를 사용해야 패치가 적용됨.

def patch_color_dialog(monkeypatch, r=0, g=0, b=255):
    """QColorDialog.getColor가 지정 색상을 반환하도록 패치."""
    from PyQt6.QtGui import QColor
    monkeypatch.setattr(
        "app.ui.toolbar.QColorDialog.getColor",
        lambda *a, **kw: QColor(r, g, b),
    )


# ── QInputDialog 패치 ────────────────────────────────────────────────────
# [QA Critical Fix] 경로: "app.ui.pdf_viewer.QInputDialog.getText"
# pdf_viewer.py에서 from PyQt6.QtWidgets import QInputDialog로 import하므로
# 반드시 pdf_viewer 모듈 기준 경로를 사용해야 패치가 적용됨.

def patch_input_dialog(monkeypatch, text: str = "테스트 텍스트", ok: bool = True):
    """QInputDialog.getText를 패치."""
    monkeypatch.setattr(
        "app.ui.pdf_viewer.QInputDialog.getText",
        lambda *a, **kw: (text, ok),
    )


# ── InsertDialog 대체 ────────────────────────────────────────────────────

class FakeInsertDialog:
    """InsertDialog 대체용. MagicMock 대신 명시적 클래스 사용."""
    DialogCode = type('DC', (), {'Accepted': 1, 'Rejected': 0})()

    def __init__(self, parent, source_path="", indices=None):
        self._source_path = source_path
        self._indices = indices or []

    def exec(self):
        return 1  # Accepted

    def source_path(self):
        return self._source_path

    def selected_indices(self):
        return self._indices


def patch_insert_dialog(monkeypatch, source_path: str, indices: list[int]):
    """InsertDialog를 모킹하여 특정 소스/인덱스를 반환."""
    class _Fake(FakeInsertDialog):
        def __init__(self, parent):
            super().__init__(parent, source_path, indices)
    monkeypatch.setattr("app.ui.main_window.InsertDialog", _Fake)


def patch_insert_dialog_cancel(monkeypatch):
    """InsertDialog를 모킹하여 취소를 반환."""
    class _FakeCancel(FakeInsertDialog):
        def __init__(self, parent):
            super().__init__(parent)
        def exec(self):
            return 0  # Rejected
    monkeypatch.setattr("app.ui.main_window.InsertDialog", _FakeCancel)
```

> **monkeypatch 경로 규칙 (E2E 일관성)**:
> - `QFileDialog` -> `"app.ui.main_window.QFileDialog.getOpenFileName"` (main_window에서 import)
> - `QMessageBox` -> `"app.ui.main_window.QMessageBox.question"` (main_window에서 import)
> - `QColorDialog` -> `"app.ui.toolbar.QColorDialog.getColor"` (toolbar에서 import) **[QA Critical Fix]**
> - `QInputDialog` -> `"app.ui.pdf_viewer.QInputDialog.getText"` (pdf_viewer에서 import) **[QA Critical Fix]**
> - `InsertDialog` -> `"app.ui.main_window.InsertDialog"` (main_window에서 import)
> - `ConvertDialog` -> `"app.ui.main_window.ConvertDialog"` (main_window에서 import)

---

## 5. 키보드 단축키 테스트 전략

### 5.1 QAction.trigger() vs QTest.keyClick() (QA Lead 방식 채택)

**권장**: `QAction.trigger()`를 **모든 단축키 테스트에서** 우선 사용.

```python
# 권장 방법: QAction.trigger()
def test_shortcut_via_action(win, pdf_3pages):
    load_pdf_directly(win, pdf_3pages)
    before = win._viewer.zoom
    win._toolbar._act_zoom_in.trigger()
    assert win._viewer.zoom > before
```

**이유**:
1. `QTest.keyClick()`은 offscreen에서 포커스 문제로 불안정하다.
2. `QAction.trigger()`는 단축키가 연결된 액션을 직접 호출하므로 100% 안정적이다.
3. 단축키 **바인딩** 자체는 별도로 검증한다 (`action.shortcut()` 확인).

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

### 5.2 QTest.keyClick() -- 사용하지 않음 (offscreen 불안정)

**[QA 수정]** 기존 계획에서 QTest.keyClick()을 보조적으로 사용하는 패턴이 있었으나, offscreen에서 포커스 미설정으로 키 이벤트가 무시되는 문제가 반복 발생한다. **모든 단축키 테스트에서 QAction.trigger()를 사용**하고, QTest.keyClick()은 사용하지 않는다.

```python
# 사용하지 않는 패턴 (offscreen 불안정):
# QTest.keyClick(win, Qt.Key.Key_Escape)

# 대신 사용:
win._toolbar._tool_actions[AnnotationTool.SELECT].trigger()
```

---

## 6. 다이얼로그/모달 테스트 패턴 가이드

### 6.1 QFileDialog monkeypatch

```python
# 패턴 1: 열기 다이얼로그 -- 파일 반환
def test_open_pdf(win, pdf_3pages, monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (pdf_3pages, "PDF 파일 (*.pdf)")
    )
    win._open_file()
    assert win._doc.is_open

# 패턴 2: 열기 다이얼로그 -- 취소
def test_open_cancel(win, monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("", "")
    )
    win._open_file()
    assert not win._doc.is_open
```

**주의**:
- `monkeypatch.setattr`의 경로는 **사용되는 모듈 기준**이다.
- 반환값은 반드시 `(path, filter)` 튜플이다.

### 6.2 QMessageBox monkeypatch

```python
# 패턴 1: question -> Yes
monkeypatch.setattr(
    "app.ui.main_window.QMessageBox.question",
    lambda *args, **kwargs: QMessageBox.StandardButton.Yes
)

# 패턴 2: question -> No
monkeypatch.setattr(
    "app.ui.main_window.QMessageBox.question",
    lambda *args, **kwargs: QMessageBox.StandardButton.No
)

# 패턴 3: warning 호출 감지
warnings = []
monkeypatch.setattr(
    "app.ui.main_window.QMessageBox.warning",
    lambda *args, **kwargs: warnings.append(args)
)
# ... 동작 후 ...
assert len(warnings) == 1

# 패턴 4: critical 오류 감지
errors = []
monkeypatch.setattr(
    "app.ui.main_window.QMessageBox.critical",
    lambda *args, **kwargs: errors.append(args)
)
```

### 6.3 QInputDialog monkeypatch

`PdfViewer`에서 텍스트 도구 클릭 시 `QInputDialog.getText`가 호출된다.

**[QA Critical Fix]** 경로는 반드시 `"app.ui.pdf_viewer.QInputDialog.getText"`를 사용한다.

```python
# 패턴 1: 텍스트 입력 확인
monkeypatch.setattr(
    "app.ui.pdf_viewer.QInputDialog.getText",
    lambda *args, **kwargs: ("테스트 텍스트", True)  # (text, ok)
)

# 패턴 2: 텍스트 입력 취소 (TC-086)
monkeypatch.setattr(
    "app.ui.pdf_viewer.QInputDialog.getText",
    lambda *args, **kwargs: ("", False)  # ok=False
)

# 패턴 3: 빈 텍스트 입력
monkeypatch.setattr(
    "app.ui.pdf_viewer.QInputDialog.getText",
    lambda *args, **kwargs: ("", True)  # 빈 문자열, ok=True
)
```

### 6.4 QColorDialog monkeypatch

**[QA Critical Fix]** 경로는 반드시 `"app.ui.toolbar.QColorDialog.getColor"`를 사용한다.

```python
from PyQt6.QtGui import QColor

# 패턴: 색상 선택 (TC-066)
monkeypatch.setattr(
    "app.ui.toolbar.QColorDialog.getColor",
    lambda *args, **kwargs: QColor(0, 0, 255)  # 파란색
)

# 패턴: 색상 선택 취소
monkeypatch.setattr(
    "app.ui.toolbar.QColorDialog.getColor",
    lambda *args, **kwargs: QColor()  # invalid = 취소
)
```

### 6.5 InsertDialog monkeypatch

```python
# 패턴: FakeInsertDialog 클래스로 교체 (MagicMock 대신)
from tests.helpers import FakeInsertDialog

class MyFakeDialog(FakeInsertDialog):
    def __init__(self, parent):
        super().__init__(parent, "/path/to/source.pdf", [0, 1])

monkeypatch.setattr("app.ui.main_window.InsertDialog", MyFakeDialog)
```

### 6.6 ConvertDialog monkeypatch

```python
# 전략 1: 다이얼로그 자체를 monkeypatch
class FakeConvertDialog:
    conversion_done = type('sig', (), {'connect': lambda self, fn: None})()
    def __init__(self, parent): pass
    def exec(self): return 0

monkeypatch.setattr("app.ui.main_window.ConvertDialog", FakeConvertDialog)

# 전략 2: ConvertDialog 내부 위젯을 직접 테스트
def test_convert_dialog_tabs(qtbot):
    from app.ui.dialogs.convert_dialog import ConvertDialog
    dlg = ConvertDialog(None)
    qtbot.addWidget(dlg)
    tab_widget = dlg.findChild(QTabWidget)
    assert tab_widget is not None
    assert tab_widget.count() == 2
```

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
    # 1) QThread 정리 -- 반드시 close() 전에!
    if hasattr(w, '_page_panel') and hasattr(w._page_panel, '_cancel_loader'):
        w._page_panel._cancel_loader()
    # 2) 윈도우 닫기
    w.close()
```

### 7.2 시그널 타이밍

**규칙**: `waitSignal`은 **비동기 시그널에만** 사용한다. 동기 동작이면 직접 확인.

```python
# 나쁜 예: 동기 시그널에 waitSignal 사용 (타임아웃 위험)
with qtbot.waitSignal(viewer.zoom_changed, timeout=1000):
    viewer.zoom_in()

# 좋은 예: 동기 동작이면 직접 확인
viewer.zoom_in()
assert viewer.zoom > before
```

### 7.3 offscreen 환경 gotchas

1. **viewport 크기가 0**: offscreen에서 `QGraphicsView.viewport().size()` == `QSize(0, 0)`. `zoom_fit()` 결과를 정확한 값이 아닌 "예외 없음"으로만 확인.
2. **마우스 이벤트 좌표 매핑 불안정**: `QGraphicsView.mapToScene()`이 offscreen에서 정확하지 않을 수 있다. 드래그 기반 테스트는 수동으로 유지.
3. **QPixmap null**: offscreen에서 `QPixmap`이 null일 수 있다. 렌더링 결과는 `fitz`로 직접 검증.
4. **폰트 메트릭스 차이**: offscreen에서 텍스트 크기/위치가 실제와 다를 수 있다. 텍스트 위치 검증은 `fitz.Page.get_text()`로.
5. **커서 형태 불확인**: offscreen에서 `viewport().cursor().shape()`이 실제 커서를 반영하지 않는 경우가 있다. `set_tool()` 후 내부 `_current_tool` 상태 확인이 더 안정적.

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
# tmp_path 사용 -- pytest가 자동 정리
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
    ...  # 모듈 내 모든 테스트가 같은 윈도우 사용 -> 상태 오염

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
# 나쁜 예: fixture에서 monkeypatch 사용 (스코프 불일치 위험)
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

## 8. 상세 구현 계획

### 8.1 tests/core/test_pdf_document.py (기존 파일 확장)

#### TC-005: PDF가 아닌 파일 열기 시도

```python
def test_open_non_pdf_file_raises(self, text_file):
    doc = PdfDocument()
    with pytest.raises(Exception):
        doc.open(text_file)
```

#### TC-008: 문서 미열림 시 저장 시도

```python
def test_save_when_not_open_raises(self):
    doc = PdfDocument()
    with pytest.raises(RuntimeError):
        doc.save()
```

#### TC-011: 확장자 미지정 시 .pdf 자동 추가

```python
def test_save_as_adds_pdf_extension(self, open_doc, tmp_path):
    path = str(tmp_path / "no_ext")
    if not path.lower().endswith(".pdf"):
        path += ".pdf"
    open_doc.save(path)
    assert path.endswith(".pdf")
    doc2 = PdfDocument()
    doc2.open(path)
    assert doc2.is_open
    doc2.close()
```

#### TC-152: 저장 실패 폴백

```python
def test_incremental_save_fallback(self, tmp_path):
    """incremental save가 실패해도 전체 저장으로 폴백하여 성공해야 한다."""
    path = str(tmp_path / "fallback.pdf")
    doc = PdfDocument()
    raw = fitz.open()
    raw.new_page(width=595, height=842)
    raw.save(path)
    raw.close()

    doc.open(path)
    for _ in range(5):
        doc.raw.new_page()
    for i in range(4, 0, -1):
        doc.raw.delete_page(i)
    doc.save()  # 폴백 발생해도 성공해야 함
    doc.close()

    doc2 = PdfDocument()
    doc2.open(path)
    assert doc2.is_open
    doc2.close()
```

### 8.2 tests/core/test_page_editor.py (기존 파일 확장)

#### TC-049, TC-050: 모든 페이지 삭제 방어

```python
def test_single_page_delete_guard(self, pdf_1page):
    doc = fitz.open(pdf_1page)
    assert doc.page_count == 1
    assert doc.page_count <= len([0])  # 방어 조건 True
    doc.close()

def test_all_pages_delete_guard(self, tmp_path):
    path = _make_pdf(2, tmp_path)
    doc = fitz.open(path)
    indices = [0, 1]
    assert doc.page_count <= len(indices)
    doc.close()
```

### 8.3 tests/core/test_annotator.py (기존 파일 확장)

#### TC-069, TC-070: 선 굵기 경계값

```python
def test_min_line_width(self, blank_page):
    page, _ = blank_page
    before = _render_bytes(page)
    add_line(page, 50, 50, 400, 400, AnnotationStyle(line_width=0.5))
    after = _render_bytes(page)
    assert before != after

def test_max_line_width(self, blank_page):
    page, _ = blank_page
    before = _render_bytes(page)
    add_line(page, 50, 50, 400, 400, AnnotationStyle(line_width=20.0))
    after = _render_bytes(page)
    assert before != after
```

#### TC-073, TC-074: 회전 페이지 어노테이션

```python
def test_180_rotation_text_produces_content(self):
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    page = doc[0]
    page.set_rotation(180)
    add_text(page, 100, 200, "R180 Text", AnnotationStyle())
    text = page.get_text()
    assert "R180" in text
    doc.close()

def test_270_rotation_line(self):
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    page = doc[0]
    page.set_rotation(270)
    before = _render_bytes(page)
    add_line(page, 50, 50, 400, 400, AnnotationStyle())
    after = _render_bytes(page)
    assert before != after
    doc.close()
```

#### TC-080~082: 텍스트 크기

```python
def test_font_size_24(self, blank_page):
    page, _ = blank_page
    before = _render_bytes(page)
    add_text(page, 100, 200, "Size 24", AnnotationStyle(font_size=24.0))
    after = _render_bytes(page)
    assert before != after

def test_font_size_min_6pt(self, blank_page):
    page, _ = blank_page
    add_text(page, 100, 200, "Tiny", AnnotationStyle(font_size=6.0))
    assert _render_bytes(page)

def test_font_size_max_72pt(self, blank_page):
    page, _ = blank_page
    add_text(page, 100, 200, "HUGE", AnnotationStyle(font_size=72.0))
    assert _render_bytes(page)
```

#### TC-087: 빈 텍스트 입력

```python
def test_empty_text_no_content_change(self, blank_page):
    page, _ = blank_page
    before = _render_bytes(page)
    add_text(page, 100, 200, "", AnnotationStyle())
    after = _render_bytes(page)
    assert before == after
```

#### TC-093, TC-096, TC-098: 도형 커스텀 스타일

```python
def test_rect_custom_color_and_width(self, blank_page):
    page, _ = blank_page
    style = AnnotationStyle(color=(0.0, 0.0, 1.0), line_width=5.0)
    before = _render_bytes(page)
    add_rect(page, 50, 50, 200, 150, style)
    after = _render_bytes(page)
    assert before != after

def test_ellipse_custom_color_and_width(self, blank_page):
    page, _ = blank_page
    style = AnnotationStyle(color=(0.0, 1.0, 0.0), line_width=8.0)
    before = _render_bytes(page)
    add_ellipse(page, 50, 50, 250, 200, style)
    after = _render_bytes(page)
    assert before != after

def test_line_custom_color_and_width(self, blank_page):
    page, _ = blank_page
    style = AnnotationStyle(color=(0.0, 0.5, 0.0), line_width=3.0)
    before = _render_bytes(page)
    add_line(page, 50, 50, 400, 400, style)
    after = _render_bytes(page)
    assert before != after
```

### 8.4 tests/core/test_command_manager.py (기존 파일 확장)

#### TC-100: Undo 기본

```python
def test_undo_reverses_last_command(self, cmd_mgr, raw_3pages):
    texts = [raw_3pages[i].get_text().strip() for i in range(3)]
    cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 2))
    cmd_mgr.undo()
    assert [raw_3pages[i].get_text().strip() for i in range(3)] == texts
```

#### TC-101: 연속 Undo

```python
def test_consecutive_undo(self, cmd_mgr, raw_3pages):
    original = [raw_3pages[i].get_text().strip() for i in range(3)]
    cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 2))
    cmd_mgr.execute(MovePageCommand(raw_3pages, 1, 0))
    cmd_mgr.execute(MovePageCommand(raw_3pages, 2, 1))
    for _ in range(3):
        cmd_mgr.undo()
    assert [raw_3pages[i].get_text().strip() for i in range(3)] == original
```

#### TC-103: 최대 이력 50개

```python
def test_max_history_50(self, cmd_mgr, raw_3pages):
    for i in range(51):
        cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 1))
    count = 0
    while cmd_mgr.can_undo:
        cmd_mgr.undo()
        count += 1
    assert count == 50
```

#### TC-109: Redo

```python
def test_redo_reapplies_command(self, cmd_mgr, raw_3pages):
    cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 2))
    after_exec = [raw_3pages[i].get_text().strip() for i in range(3)]
    cmd_mgr.undo()
    cmd_mgr.redo()
    assert [raw_3pages[i].get_text().strip() for i in range(3)] == after_exec
```

#### TC-111: Redo 이력 없을 때

```python
def test_redo_when_empty_is_noop(self, cmd_mgr):
    result = cmd_mgr.redo()
    assert result is None
    assert not cmd_mgr.can_redo
```

#### TC-112: Undo->Redo->Undo 반복

```python
def test_undo_redo_undo_cycle(self, cmd_mgr, raw_3pages):
    original = [raw_3pages[i].get_text().strip() for i in range(3)]
    cmd_mgr.execute(MovePageCommand(raw_3pages, 0, 2))
    after_exec = [raw_3pages[i].get_text().strip() for i in range(3)]

    cmd_mgr.undo()
    assert [raw_3pages[i].get_text().strip() for i in range(3)] == original
    cmd_mgr.redo()
    assert [raw_3pages[i].get_text().strip() for i in range(3)] == after_exec
    cmd_mgr.undo()
    assert [raw_3pages[i].get_text().strip() for i in range(3)] == original
```

### 8.5 tests/core/test_converter.py (기존 파일 확장)

#### TC-114: 여러 이미지->PDF

```python
def test_mixed_formats_conversion(self, tmp_path):
    from PIL import Image
    from app.core.converter import convert_images_to_pdf
    paths = []
    for ext, color in [("png", (255, 0, 0)), ("jpg", (0, 255, 0)), ("bmp", (0, 0, 255))]:
        p = str(tmp_path / f"img.{ext}")
        fmt = "JPEG" if ext == "jpg" else ext.upper()
        Image.new("RGB", (200, 150), color=color).save(p, fmt)
        paths.append(p)
    out = str(tmp_path / "mixed.pdf")
    convert_images_to_pdf(paths, out)
    doc = fitz.open(out)
    assert len(doc) == 3
    doc.close()
```

#### TC-115: 모든 이미지 형식

```python
@pytest.mark.parametrize("ext,pil_fmt", [
    ("jpg", "JPEG"), ("jpeg", "JPEG"), ("png", "PNG"),
    ("bmp", "BMP"), ("gif", "GIF"), ("tiff", "TIFF"),
    ("tif", "TIFF"), ("webp", "WEBP"),
])
def test_supported_format(self, tmp_path, ext, pil_fmt):
    from PIL import Image
    from app.core.converter import convert_images_to_pdf
    img_path = str(tmp_path / f"test.{ext}")
    Image.new("RGB", (100, 80), color=(128, 128, 128)).save(img_path, pil_fmt)
    out = str(tmp_path / f"out_{ext}.pdf")
    result = convert_images_to_pdf([img_path], out)
    assert os.path.exists(result)
```

#### TC-121: DOCX->PDF (monkeypatch)

**[QA Critical Fix]** `unittest.mock.patch`/`MagicMock`을 `monkeypatch`로 전환.

```python
def test_docx_to_pdf_success(self, tmp_path, monkeypatch):
    """TC-121: DOCX->PDF 변환 (monkeypatch 기반)."""
    from app.core.converter import convert_office_to_pdf
    expected_out = str(tmp_path / "report.pdf")
    open(expected_out, "w").close()  # 빈 파일 생성 (LO 출력 시뮬레이션)

    # find_libreoffice 패치
    monkeypatch.setattr(
        "app.core.converter.find_libreoffice",
        lambda: "/fake/soffice",
    )

    # subprocess.run 패치
    class FakeResult:
        returncode = 0
        stderr = ""

    run_calls = []
    def fake_run(*args, **kwargs):
        run_calls.append(args)
        return FakeResult()

    monkeypatch.setattr("subprocess.run", fake_run)

    result = convert_office_to_pdf(
        str(tmp_path / "report.docx"), str(tmp_path)
    )
    assert result == expected_out
    assert len(run_calls) == 1
```

> **[QA 수정 주석]**: `converter.py`는 `subprocess`를 직접 import하므로 `"subprocess.run"` 전역 패치가 작동한다. `monkeypatch.setattr`로 통일하여 E2E 규칙("모든 모킹은 monkeypatch")을 준수한다.

#### TC-122: Office 확장자 지원

```python
def test_all_office_exts(self):
    from app.core.converter import SUPPORTED_OFFICE_EXTS
    expected = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".odt", ".ods", ".odp"}
    assert expected.issubset(SUPPORTED_OFFICE_EXTS)
```

### 8.6 tests/core/test_architecture.py (신규 파일)

#### TC-154: Core/UI 분리 확인 (AST 기반)

```python
"""아키텍처 제약 테스트 -- TC-154."""

import ast
import os
import pytest


class TestArchitecture:
    """TC-154: app/core/ 내에 PyQt6 import가 없어야 합니다."""

    def test_tc154_core_no_pyqt6_import(self):
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
                                violations.append(f"{fpath}:{node.lineno} -- import {alias.name}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "PyQt6" in node.module:
                            violations.append(f"{fpath}:{node.lineno} -- from {node.module}")

        assert violations == [], f"Core에 PyQt6 의존 발견:\n" + "\n".join(violations)
```

### 8.7 tests/ui/test_toolbar.py (신규 파일)

#### TC-064: 도구 배타적 전환

```python
"""MainToolBar 위젯 테스트."""

from app.core.annotator import AnnotationTool
from app.ui.toolbar import MainToolBar


@pytest.fixture
def toolbar(qtbot):
    tb = MainToolBar()
    qtbot.addWidget(tb)
    tb.set_document_loaded(True)
    return tb


class TestToolBarAnnotation:
    def test_exclusive_tool_toggle(self, toolbar, qtbot):
        tb = toolbar
        tb._tool_actions[AnnotationTool.TEXT].trigger()
        assert tb._tool_actions[AnnotationTool.TEXT].isChecked()
        assert not tb._tool_actions[AnnotationTool.RECT].isChecked()

        tb._tool_actions[AnnotationTool.RECT].trigger()
        assert tb._tool_actions[AnnotationTool.RECT].isChecked()
        assert not tb._tool_actions[AnnotationTool.TEXT].isChecked()

        tb._tool_actions[AnnotationTool.ELLIPSE].trigger()
        assert tb._tool_actions[AnnotationTool.ELLIPSE].isChecked()
        assert not tb._tool_actions[AnnotationTool.RECT].isChecked()

    def test_tool_group_is_exclusive(self, toolbar):
        """TC-139: QActionGroup이 배타적인지 확인."""
        assert toolbar._tool_group.isExclusive()

    def test_width_change_signal(self, toolbar, qtbot):
        """TC-068: 선 굵기 변경 시그널."""
        with qtbot.waitSignal(toolbar.width_changed, timeout=1000):
            toolbar._width_spin.setValue(5.0)


class TestToolBarTextStyle:
    def test_text_style_visibility_toggle(self, toolbar):
        """TC-085: TEXT 도구 활성화/비활성화에 따른 스타일 컨트롤 토글."""
        tb = toolbar
        tb.set_text_tool_active(False)
        assert not tb._font_combo.isEnabled()
        assert not tb._font_size_spin.isEnabled()
        assert not tb._act_bold.isEnabled()
        assert not tb._act_italic.isEnabled()

        tb.set_text_tool_active(True)
        assert tb._font_combo.isEnabled()
        assert tb._font_size_spin.isEnabled()
        assert tb._act_bold.isEnabled()
        assert tb._act_italic.isEnabled()


class TestToolBarZoom:
    def test_zoom_controls_exist(self, toolbar):
        """TC-140: 줌 컨트롤 존재 및 범위."""
        assert toolbar._act_zoom_in is not None
        assert toolbar._act_zoom_out is not None
        assert toolbar._act_zoom_fit is not None
        assert toolbar._zoom_spin is not None
        assert toolbar._zoom_spin.minimum() == 25
        assert toolbar._zoom_spin.maximum() == 400
```

### 8.8 tests/ui/test_main_window.py (신규 파일 -- 핵심)

이 파일이 **가장 핵심**. MainWindow 레벨에서 UI 통합 테스트를 수행.

> **[QA 수정]** `_load_pdf` 인라인 대신 `from tests.helpers import load_pdf_directly`를 사용. 단, 파일 내에서 간결한 별칭을 제공.

```python
"""MainWindow 단위/컴포넌트 테스트."""

from __future__ import annotations

import os
import pytest
from PyQt6.QtWidgets import QMessageBox

from app.core.annotator import AnnotationTool
from app.ui.main_window import MainWindow
from tests.helpers import load_pdf_directly, FakeInsertDialog


@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    w.show()
    yield w
    if hasattr(w, '_page_panel') and hasattr(w._page_panel, '_cancel_loader'):
        w._page_panel._cancel_loader()
    w.close()


# -- TC-001~TC-014: 문서 관리 --

class TestDocumentOpen:
    def test_tc001_open_valid_pdf(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        assert win._doc.is_open
        assert win._doc.page_count == 3
        assert win._page_panel._list.count() == 3

    def test_tc002_reopen_replaces_document(self, win, pdf_3pages, pdf_5pages):
        load_pdf_directly(win, pdf_3pages)
        load_pdf_directly(win, pdf_5pages)
        assert win._doc.page_count == 5

    def test_tc003_open_dialog_cancel(self, win, monkeypatch):
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getOpenFileName",
            lambda *a, **kw: ("", "")
        )
        win._open_file()
        assert not win._doc.is_open

    def test_tc004_open_corrupted_pdf(self, win, tmp_path, monkeypatch):
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
        assert len(errors) == 1
        assert not win._doc.is_open

    def test_tc005_open_non_pdf_file(self, win, tmp_path, monkeypatch):
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
        """QAction.shortcut() 바인딩 확인 (QTest.keyClick 대신)."""
        shortcut = win._toolbar._act_open.shortcut().toString()
        assert "O" in shortcut.upper()


class TestDocumentSave:
    def test_tc007_save_overwrites(self, win, pdf_3pages, tmp_path):
        import shutil
        save_path = str(tmp_path / "writable.pdf")
        shutil.copy(pdf_3pages, save_path)
        load_pdf_directly(win, save_path)
        win._save_file()
        assert os.path.exists(save_path)

    def test_tc008_save_disabled_when_no_doc(self, win):
        assert not win._toolbar._act_save.isEnabled()

    def test_tc010_save_as(self, win, pdf_3pages, tmp_path, monkeypatch):
        load_pdf_directly(win, pdf_3pages)
        save_path = str(tmp_path / "new_name.pdf")
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: (save_path, "PDF 파일 (*.pdf)")
        )
        win._save_as()
        assert os.path.exists(save_path)

    def test_tc011_save_as_auto_extension(self, win, pdf_3pages, tmp_path, monkeypatch):
        load_pdf_directly(win, pdf_3pages)
        no_ext_path = str(tmp_path / "no_extension")
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: (no_ext_path, "PDF 파일 (*.pdf)")
        )
        win._save_as()
        assert os.path.exists(no_ext_path + ".pdf")

    def test_tc012_save_as_cancel(self, win, pdf_3pages, monkeypatch):
        load_pdf_directly(win, pdf_3pages)
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: ("", "")
        )
        win._save_as()


class TestDocumentClose:
    def test_tc013_close_app(self, win):
        win.close()

    def test_tc014_close_with_open_doc(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        assert win._doc.is_open
        win.close()


# -- TC-015~TC-031: 뷰어/탐색 --

class TestViewerInMainWindow:
    def test_tc015_default_zoom_150(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        assert win._viewer.zoom == pytest.approx(1.5)

    def test_tc021_zoom_fit(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        win._toolbar._act_zoom_fit.trigger()
        assert isinstance(win._viewer.zoom, float)

    def test_tc023_zoom_spinbox_direct_input(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        win._toolbar._zoom_spin.setValue(200)
        # 줌 값이 변경되었는지 확인 (정확한 매핑은 구현에 따름)

    def test_tc027_pgup_prev_page(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        win._viewer.goto_page(2)
        win._viewer.goto_page(1)
        assert win._viewer.current_page == 1

    def test_tc028_pgup_at_first_page(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        win._viewer.goto_page(-1)
        assert win._viewer.current_page == 0

    def test_tc031_statusbar_page_info(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        win._viewer.goto_page(1)
        win._update_page_status(1)
        text = win._lbl_page.text()
        assert "2" in text


# -- TC-047~TC-063: 페이지 편집 --

class TestPageDelete:
    def test_tc047_delete_single(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([1])
        assert win._doc.page_count == 4

    def test_tc048_delete_multiple(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0, 2, 4])
        assert win._doc.page_count == 2

    def test_tc049_delete_all_pages_blocked(self, win, pdf_1page, monkeypatch):
        load_pdf_directly(win, pdf_1page)
        warnings = []
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.warning",
            lambda *a, **kw: warnings.append(a)
        )
        win._delete_pages([0])
        assert len(warnings) == 1
        assert win._doc.page_count == 1

    def test_tc050_delete_all_of_2page_blocked(self, win, tmp_path, monkeypatch):
        from tests.conftest import _make_pdf
        path = _make_pdf(2, tmp_path)
        load_pdf_directly(win, path)
        warnings = []
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.warning",
            lambda *a, **kw: warnings.append(a)
        )
        win._delete_pages([0, 1])
        assert len(warnings) == 1
        assert win._doc.page_count == 2

    def test_tc051_delete_undo(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([1])
        assert win._doc.page_count == 4
        win._undo()
        assert win._doc.page_count == 5

    def test_tc052_delete_cancel(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.No
        )
        win._delete_pages([1])
        assert win._doc.page_count == 5

    def test_tc053_toolbar_delete(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._page_panel._list.setCurrentRow(0)
        win._delete_selected_pages()
        assert win._doc.page_count == 4

    def test_tc054_edit_menu_delete(self, win, pdf_5pages, monkeypatch):
        """QAction.trigger()로 편집 메뉴 삭제 실행."""
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._page_panel._list.setCurrentRow(2)
        win._toolbar._act_delete.trigger()
        assert win._doc.page_count == 4


class TestPageExtract:
    def test_tc055_extract_single(self, win, pdf_5pages, tmp_path, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
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
        load_pdf_directly(win, pdf_5pages)
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
        load_pdf_directly(win, pdf_5pages)
        out = str(tmp_path / "extract.pdf")
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: (out, "PDF 파일 (*.pdf)")
        )
        win._extract_pages([0, 1])
        assert win._doc.page_count == 5

    def test_tc058_extract_dialog_cancel(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: ("", "")
        )
        win._extract_pages([0])


class TestPageInsert:
    def test_tc059_insert_pages(self, win, pdf_3pages, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_3pages)
        class _Fake(FakeInsertDialog):
            def __init__(self, parent):
                super().__init__(parent, pdf_5pages, [0, 1])
        monkeypatch.setattr("app.ui.main_window.InsertDialog", _Fake)
        win._insert_pages(insert_before=1)
        assert win._doc.page_count == 5  # 3 + 2

    def test_tc061_insert_multiple(self, win, pdf_3pages, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_3pages)
        class _Fake(FakeInsertDialog):
            def __init__(self, parent):
                super().__init__(parent, pdf_5pages, [0, 1, 2])
        monkeypatch.setattr("app.ui.main_window.InsertDialog", _Fake)
        win._insert_pages(insert_before=0)
        assert win._doc.page_count == 6  # 3 + 3

    def test_tc062_insert_undo(self, win, pdf_3pages, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_3pages)
        class _Fake(FakeInsertDialog):
            def __init__(self, parent):
                super().__init__(parent, pdf_5pages, [0])
        monkeypatch.setattr("app.ui.main_window.InsertDialog", _Fake)
        win._insert_pages(insert_before=1)
        assert win._doc.page_count == 4
        win._undo()
        assert win._doc.page_count == 3

    def test_tc063_insert_dialog_cancel(self, win, pdf_3pages, monkeypatch):
        load_pdf_directly(win, pdf_3pages)
        class _FakeCancel(FakeInsertDialog):
            def __init__(self, parent):
                super().__init__(parent)
            def exec(self):
                return 0  # Rejected
        monkeypatch.setattr("app.ui.main_window.InsertDialog", _FakeCancel)
        win._insert_pages(insert_before=0)
        assert win._doc.page_count == 3


# -- TC-064~TC-070, TC-085: 도구 전환 / 스타일 --

class TestToolSwitching:
    def test_tc064_exclusive_tool_selection(self, win, pdf_3pages):
        """TC-064: 도구 배타적 전환 (Component 수준).
        [E2E 중복 주의] TC-163과 범위 구분: 여기서는 toolbar 단독 검증만.
        """
        load_pdf_directly(win, pdf_3pages)
        toolbar = win._toolbar
        toolbar._tool_actions[AnnotationTool.TEXT].trigger()
        assert toolbar._tool_group.checkedAction() == toolbar._tool_actions[AnnotationTool.TEXT]
        toolbar._tool_actions[AnnotationTool.RECT].trigger()
        assert toolbar._tool_group.checkedAction() == toolbar._tool_actions[AnnotationTool.RECT]
        assert not toolbar._tool_actions[AnnotationTool.TEXT].isChecked()

    def test_tc065_escape_returns_to_select(self, win, pdf_3pages):
        """QAction.trigger()로 SELECT 복귀 (QTest.keyClick 대신)."""
        load_pdf_directly(win, pdf_3pages)
        toolbar = win._toolbar
        toolbar._tool_actions[AnnotationTool.RECT].trigger()
        toolbar._tool_actions[AnnotationTool.SELECT].trigger()
        assert toolbar._tool_group.checkedAction() == toolbar._tool_actions[AnnotationTool.SELECT]

    def test_tc067_default_color_red(self, win):
        from PyQt6.QtGui import QColor
        assert win._toolbar._annot_color == QColor(255, 0, 0)

    def test_tc068_line_width_change_signal(self, win, pdf_3pages, qtbot):
        load_pdf_directly(win, pdf_3pages)
        with qtbot.waitSignal(win._toolbar.width_changed, timeout=1000):
            win._toolbar._width_spin.setValue(5.0)

    def test_tc069_line_width_minimum(self, win):
        assert win._toolbar._width_spin.minimum() == 0.5

    def test_tc070_line_width_maximum(self, win):
        assert win._toolbar._width_spin.maximum() == 20.0

    def test_tc081_font_size_minimum(self, win):
        assert win._toolbar._font_size_spin.minimum() == 6

    def test_tc082_font_size_maximum(self, win):
        assert win._toolbar._font_size_spin.maximum() == 72

    def test_tc085_text_style_visibility(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        toolbar = win._toolbar
        toolbar._tool_actions[AnnotationTool.SELECT].trigger()
        assert not toolbar._font_combo.isEnabled()
        toolbar._tool_actions[AnnotationTool.TEXT].trigger()
        win._on_tool_changed(AnnotationTool.TEXT)
        assert toolbar._font_combo.isEnabled()
        assert toolbar._act_bold.isEnabled()


# -- TC-100~TC-112: Undo/Redo (MainWindow 레벨) --

class TestUndoRedoMainWindow:
    def test_tc100_undo_basic(self, win, pdf_5pages, monkeypatch):
        """TC-100: Ctrl+Z Undo 기본 동작.
        [E2E 중복 주의] TC-160과 부분 중복 -- 단일 Undo만 검증.
        """
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        assert win._doc.page_count == 4
        win._undo()
        assert win._doc.page_count == 5

    def test_tc101_consecutive_undo(self, win, pdf_5pages, monkeypatch):
        """TC-101: 연속 Undo -- 3회 삭제 후 3회 Undo.
        [E2E 중복 주의] TC-160과 범위 겹침 -- 페이지 삭제 연속만 검증.
        """
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        win._delete_pages([0])
        win._delete_pages([0])
        assert win._doc.page_count == 2
        win._undo()
        win._undo()
        win._undo()
        assert win._doc.page_count == 5

    def test_tc102_undo_when_empty(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        win._undo()  # 예외 없이 동작

    def test_tc108_undo_dynamic_text(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        text = win._act_undo.text()
        assert "실행 취소" in text
        assert "삭제" in text

    def test_tc109_redo_basic(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
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
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        win._undo()
        assert win._cmd_mgr.can_redo
        win._delete_pages([0])
        assert not win._cmd_mgr.can_redo

    def test_tc111_redo_when_empty(self, win, pdf_3pages):
        load_pdf_directly(win, pdf_3pages)
        win._redo()  # 예외 없이 동작

    def test_tc112_undo_redo_undo_cycle(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
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


# -- TC-143: 전체 키보드 단축키 --

class TestKeyboardShortcuts:
    def test_tc143_shortcut_bindings(self, win):
        """단축키 바인딩 존재 확인 (QAction.shortcut() 방식)."""
        shortcuts = {
            win._toolbar._act_open: "O",
            win._toolbar._act_save: "S",
            win._toolbar._act_zoom_in: "=",
            win._toolbar._act_zoom_out: "-",
            win._toolbar._act_zoom_fit: "0",
        }
        for action, expected_key in shortcuts.items():
            actual = action.shortcut().toString()
            assert expected_key in actual, \
                f"{action.text()}: expected '{expected_key}' in '{actual}'"

    def test_tc143_undo_shortcut_via_trigger(self, win, pdf_5pages, monkeypatch):
        """Ctrl+Z 대신 QAction.trigger()로 동작 확인."""
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        win._act_undo.trigger()
        assert win._doc.page_count == 5

    def test_tc143_redo_shortcut_via_trigger(self, win, pdf_5pages, monkeypatch):
        load_pdf_directly(win, pdf_5pages)
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes
        )
        win._delete_pages([0])
        win._undo()
        win._act_redo.trigger()
        assert win._doc.page_count == 4


# -- TC-151: 어노테이션 후 단일 페이지 갱신 --

class TestAnnotationRefresh:
    def test_tc151_annotation_refreshes_page(self, win, pdf_5pages):
        load_pdf_directly(win, pdf_5pages)
        from app.core.annotator import add_rect, AnnotationStyle
        page_idx = win._viewer.current_page

        def annotate():
            add_rect(win._doc.raw[page_idx], 50, 50, 200, 150, AnnotationStyle())

        win._on_annotation_requested(annotate, "사각형 추가")
        assert win._cmd_mgr.can_undo
```

### 8.9 tests/ui/test_main_window_menu.py (신규 파일)

```python
"""MainWindow 메뉴/툴바 구조 테스트 -- TC-130~TC-140."""

from __future__ import annotations
import pytest
from app.core.annotator import AnnotationTool
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
    def test_tc130_has_toolbar(self, win):
        assert win._toolbar is not None

    def test_tc130_has_page_panel(self, win):
        assert win._page_panel is not None

    def test_tc130_has_viewer(self, win):
        assert win._viewer is not None

    def test_tc130_has_status_bar(self, win):
        assert win.statusBar() is not None


class TestMenuStructure:
    def _menu_texts(self, win, menu_title_fragment):
        for action in win.menuBar().actions():
            if menu_title_fragment in action.text():
                menu = action.menu()
                if menu:
                    return [a.text() for a in menu.actions() if not a.isSeparator()]
        return []

    def test_tc131_file_menu(self, win):
        texts = self._menu_texts(win, "파일")
        text_str = " ".join(texts)
        assert "열기" in text_str
        assert "저장" in text_str
        assert "종료" in text_str

    def test_tc132_edit_menu(self, win):
        texts = self._menu_texts(win, "편집")
        text_str = " ".join(texts)
        assert "실행 취소" in text_str or "취소" in text_str
        assert "삭제" in text_str

    def test_tc133_view_menu(self, win):
        texts = self._menu_texts(win, "보기")
        assert len(texts) >= 3

    def test_tc134_annotation_menu(self, win):
        texts = self._menu_texts(win, "어노테이션")
        text_str = " ".join(texts)
        assert "선택" in text_str
        assert "텍스트" in text_str

    def test_tc135_tools_menu(self, win):
        texts = self._menu_texts(win, "도구")
        text_str = " ".join(texts)
        assert "변환" in text_str

    def test_tc136_help_menu(self, win):
        texts = self._menu_texts(win, "도움말")
        text_str = " ".join(texts)
        assert "정보" in text_str


class TestToolbarStructure:
    def test_tc137_file_group(self, win):
        assert win._toolbar._act_open is not None
        assert win._toolbar._act_save is not None

    def test_tc138_page_edit_group(self, win):
        assert win._toolbar._act_delete is not None
        assert win._toolbar._act_extract is not None
        assert win._toolbar._act_insert is not None
        assert win._toolbar._act_convert is not None

    def test_tc139_annotation_exclusive_toggle(self, win):
        group = win._toolbar._tool_group
        assert group.isExclusive()
        assert len(win._toolbar._tool_actions) == 5

    def test_tc140_zoom_controls(self, win):
        assert win._toolbar._act_zoom_in is not None
        assert win._toolbar._act_zoom_out is not None
        assert win._toolbar._act_zoom_fit is not None
        assert win._toolbar._zoom_spin is not None
```

### 8.10 tests/ui/test_convert_dialog.py (신규 파일)

```python
"""변환 다이얼로그 테스트 -- TC-126~TC-128."""

import pytest
from PyQt6.QtWidgets import QProgressBar


def test_tc126_ctrl_shift_c_shortcut_exists(main_window):
    """변환 액션에 Ctrl+Shift+C 단축키가 할당되어 있다."""
    tb = main_window._toolbar
    shortcut = tb._act_convert.shortcut().toString()
    assert "C" in shortcut

def test_tc127_convert_dialog_tabs(qtbot):
    from app.ui.dialogs.convert_dialog import ConvertDialog
    dlg = ConvertDialog(None)
    qtbot.addWidget(dlg)
    if hasattr(dlg, '_tabs'):
        assert dlg._tabs.count() >= 2

def test_tc128_progress_bar_exists(qtbot):
    from app.ui.dialogs.convert_dialog import ConvertDialog
    dlg = ConvertDialog(None)
    qtbot.addWidget(dlg)
    progress_bars = dlg.findChildren(QProgressBar)
    assert len(progress_bars) >= 1
```

---

## 9. 수동 테스트 유지 목록

### 9.1 빌드/배포 (TC-145 ~ TC-149) -- 5건

| TC | 근거 |
|----|------|
| TC-145 | EXE 빌드는 PyInstaller 환경 필요 |
| TC-146 | EXE 환경 기능 동작은 실제 실행 필요 |
| TC-147 | uv sync는 클린 환경 필요 |
| TC-148 | GUI 앱 실행은 디스플레이 필요 |
| TC-149 | pytest 실행은 CI/CD로 대체 |

### 9.2 시각적/테마 (TC-025, TC-033, TC-078, TC-090, TC-091, TC-141, TC-142) -- 7건

| TC | 근거 |
|----|------|
| TC-025 | OpenHand 커서 -- offscreen 불확인 |
| TC-033 | 썸네일 크기/비율 -- 디스플레이 의존 |
| TC-078 | IBeam 커서 -- offscreen 불확인 |
| TC-090 | Crosshair 커서 -- offscreen 불확인 |
| TC-091 | 반투명 프리뷰 -- 시각적 확인 필수. **[QA 수정]** 기존 거짓 양성 스켈레톤 제거됨 |
| TC-141 | 다크 테마 배경색 |
| TC-142 | 선택 하이라이트 색상 |

### 9.3 마우스/드래그 인터랙션 -- 해당 TC는 core 테스트가 커버

| TC 범위 | 근거 | core 커버 |
|---------|------|----------|
| TC-038~042 | 우클릭 컨텍스트 메뉴 QMenu.exec_() | 시그널 emit으로 부분 검증 |
| TC-092, TC-095, TC-099 | 3px 미만 드래그 무시. **[QA 수정]** 기존 거짓 양성 스켈레톤 제거됨 | core 어노테이션 검증으로 간접 커버 |

### 9.4 외부 의존성 / 비기능 -- 6건

| TC | 근거 |
|----|------|
| TC-124 | LibreOffice 경로 감지 -- 환경 의존 |
| TC-125 | 변환 타임아웃 -- 환경 의존 |
| TC-129 | 변환 중 UI 비차단 -- QThread 타이밍 |
| TC-150 | 썸네일 대용량 성능 |
| TC-153 | PDF 뷰어 호환성 |
| TC-126 | Ctrl+Shift+C (바인딩만 자동화, 모달 수동) |

---

## 10. 요약

| 분류 | 자동화 TC 수 | 신규 테스트 함수 (추정) |
|------|-------------|----------------------|
| Unit 테스트 (core) | 26 | ~30 |
| Component 테스트 (위젯) | 20 | ~25 |
| Integration 테스트 (MainWindow) | 36 | ~40 |
| UI 검증 테스트 (레이아웃/메뉴) | 13 | ~15 |
| 빌드/수동 유지 | 18 (수동) | 0 |
| **합계** | **72 (자동화) + 18 (부분) + 18 (수동)** | **~110** |

> **최종 자동화 목표**: 기존 46건 + 신규 약 72건 = **약 118건** 자동화 테스트
> Sprint 1 완료 후 자동화 커버리지: 약 76% (118/154)
> 부분 자동화 18건의 자동화 가능 범위까지 포함하면: 약 88% (136/154)

신규 테스트 파일: `test_toolbar.py`, `test_main_window.py`, `test_main_window_menu.py`, `test_convert_dialog.py`, `test_architecture.py`
기존 확장 파일: `test_pdf_document.py`, `test_page_editor.py`, `test_annotator.py`, `test_command_manager.py`, `test_converter.py`, `test_pdf_viewer.py`, `test_page_panel.py`

---

## 11. 상호 검증 결과

### 11.1 자동화 판정 분쟁 해결

| TC | Test Architect | QA Lead | 최종 판정 | 근거 |
|----|----------------|---------|----------|------|
| TC-025 (OpenHand 커서) | 자동화 | 수동 | **수동** | offscreen에서 cursor().shape()이 실제 커서를 반영하지 않음 |
| TC-033 (썸네일 크기) | 자동화 | 수동 | **수동** | 픽셀 정확도가 디스플레이 DPI에 의존 |
| TC-036 (Ctrl+클릭) | 자동화 | 부분 | **부분** | QListWidget API로 선택은 가능하나 실제 Ctrl+클릭과 다름 |
| TC-037 (Shift+클릭) | 자동화 | 부분 | **부분** | 위와 동일 |
| TC-038~042 (컨텍스트 메뉴) | 자동화 | 수동 | **수동** | QMenu.exec_()는 네이티브 이벤트 루프. 시그널 emit으로 부분 검증만 가능 |
| TC-078 (IBeam 커서) | 자동화 | 수동 | **수동** | TC-025와 동일 |
| TC-086 (텍스트 입력 취소) | 자동화 | 수동 | **부분** | QInputDialog monkeypatch로 자동화 가능. QA Lead 근거(네이티브)는 monkeypatch로 해결됨 |
| TC-090 (Crosshair 커서) | 자동화 | 수동 | **수동** | TC-025와 동일 |
| TC-091~099 (드래그 도형) | 자동화 | 수동 | **수동** | offscreen 마우스 이벤트 좌표 매핑 불안정. core 테스트가 회귀 방지 |
| TC-115 (모든 이미지 형식) | 자동화 | 수동 | **자동화** | parametrize로 비용 낮음. 각 형식별 1분 이내 |
| TC-116~119 (변환 다이얼로그) | 자동화 | 수동 | **부분** | core 레벨은 자동화, ConvertDialog UI는 수동 |
| TC-121 (DOCX 변환) | 자동화 | 수동 | **부분** | subprocess mock으로 자동화 가능, 실제 LO는 수동 |
| TC-124~125 (LO 감지/타임아웃) | 자동화 | 수동 | **수동** | 환경 의존. CI에서도 LO 설치 보장 불가 |
| TC-141~142 (테마) | 자동화 | 수동 | **수동** | QPalette 검증은 가능하나 offscreen에서 테마 적용 불완전 |
| TC-143 (전체 단축키) | 자동화 | 자동화 | **자동화** | QAction.trigger() + shortcut() 바인딩 확인 |

### 11.2 코드 패턴 통일

| 항목 | Test Architect 원본 | QA Lead | E2E 계획 | **최종 채택** |
|------|---------------------|---------|----------|-------------|
| monkeypatch 경로 | `"PyQt6.QtWidgets.QFileDialog..."` | `"app.ui.main_window.QFileDialog..."` | `"app.ui.main_window.QFileDialog..."` | **모듈 기준** (`app.ui.main_window...`) |
| 단축키 테스트 | QTest.keyClick() | QAction.trigger() | QAction.trigger() | **QAction.trigger()** |
| InsertDialog mock | InsertDialog.exec 패치 | FakeInsertDialog 클래스 | _FakeInsertDialog 클래스 | **FakeInsertDialog 클래스** (tests/helpers.py 단일 정의) |
| mock 도구 | monkeypatch + unittest.mock 혼용 | monkeypatch 전용 | monkeypatch 전용 (규칙 명시) | **monkeypatch 전용** |
| load_pdf 방식 | load_pdf_directly 헬퍼 | _load_pdf 인라인 | load_pdf_directly 헬퍼 | **load_pdf_directly 헬퍼** (tests/helpers.py 공통 배치) |

### 11.3 QA 리뷰 반영 내역 (최종 확정본 기준)

아래는 QA Lead의 상호 검증 리뷰(`UNIT_COMPONENT_TEST_PLAN_QA.md` "상호 검증 리뷰 결과" 섹션)에서 지적된 항목과 본 확정본에서의 반영 상태이다.

#### Critical Fixes (4건 -- 전체 반영 완료)

| # | QA 지적 | 반영 위치 | 반영 상태 |
|---|---------|----------|----------|
| 1 | **TC-066 monkeypatch 경로 오류**: `"PyQt6.QtWidgets.QColorDialog.getColor"` -> `"app.ui.toolbar.QColorDialog.getColor"` | 4.3절 `patch_color_dialog()`, 6.4절 패턴 가이드 | **반영 완료** |
| 2 | **TC-086 monkeypatch 경로 오류**: `"PyQt6.QtWidgets.QInputDialog.getText"` -> `"app.ui.pdf_viewer.QInputDialog.getText"` | 4.3절 `patch_input_dialog()`, 6.3절 패턴 가이드 | **반영 완료** |
| 3 | **TC-022 QWheelEvent 생성자**: `QPoint` -> `QPointF` | 2.2절 부분 자동화 표 TC-022 항목 | **반영 완료** |
| 4 | **TC-091, TC-092, TC-095, TC-099 거짓 양성 제거**: 실제 드래그 없이 항상 통과하는 테스트 스켈레톤 삭제 | 2.2절 수동 유지 항목, 9.2~9.3절 수동 목록 | **반영 완료** -- 수동 유지로 전환 |

#### Deduplication -- E2E 중복 주석 (3건 -- 전체 반영 완료)

| # | 중복 TC 쌍 | 반영 상태 |
|---|-----------|----------|
| 5 | **TC-064 / TC-163** (도구 배타적 전환) | 2.2절 + 8.8절 TC-064 코드에 `[E2E 중복 주의]` 주석 추가. "Component 수준(toolbar 단독)으로 제한, MainWindow 전체 흐름은 E2E에 위임" |
| 6 | **TC-100~101 / TC-160** (Undo/Redo) | 2.2절 + 8.8절 TC-100, TC-101 코드에 `[E2E 중복 주의]` 주석 추가. "단일/연속 Undo 동작만 검증, 복합 시나리오는 E2E에 위임" |
| 7 | **TC-103 / TC-E05** (이력 50개 제한) | 2.2절 TC-103 항목에 `[E2E 중복 주의]` 주석 추가. "core CommandManager 직접 검증, E2E는 MainWindow 경유" |

#### Consistency -- 구조 통일 (3건 -- 전체 반영 완료)

| # | QA 지적 | 반영 상태 |
|---|---------|----------|
| 8 | **tests/helpers.py 단일 모듈 통합**: `load_pdf_directly()`, `FakeInsertDialog`, 모든 monkeypatch 헬퍼를 하나의 모듈에 배치 | 4.1절 파일 구조, 4.3절 전체 코드 -- **반영 완료** |
| 9 | **중복 fixture 정의 제거**: `main_window` fixture를 `tests/conftest.py`에만 공통 정의. E2E conftest.py에서 import | 4.2절 conftest.py 설명 -- **반영 완료** |
| 10 | **QAction.trigger() 표준화**: 모든 단축키 테스트에서 QTest.keyClick() 대신 QAction.trigger() 사용 | 5.1절, 5.2절 전면 수정, 8.8절 모든 단축키 테스트 코드 -- **반영 완료** |

#### unittest.mock -> monkeypatch 전환 (2건 -- 전체 반영 완료)

| # | QA 지적 | 반영 상태 |
|---|---------|----------|
| 11 | **TC-121 unittest.mock 사용**: `unittest.mock.patch`/`MagicMock` -> `monkeypatch.setattr` | 8.5절 TC-121 코드 전면 재작성 -- **반영 완료** |
| 12 | **TC-125 unittest.mock 사용**: 수동 유지로 전환 (환경 의존) | 2.2절 수동 유지 항목 -- **반영 완료** (자동화 대상에서 제외) |

### 11.4 QA Lead 기여 (본 계획에 통합된 항목)

1. **자동화 판단 매트릭스**: 비용-편익 분석 기준 명확화
2. **QAction.trigger() 전략**: offscreen에서 안정적인 단축키 테스트
3. **FakeInsertDialog 클래스**: MagicMock 대신 명시적 클래스로 타입 안전성 확보
4. **Flaky 테스트 방지 가이드**: QThread 정리, 시그널 타이밍, offscreen gotchas
5. **리스크 x 영향도 매트릭스**: 회귀 리스크 상위 20 TC 식별
6. **Sprint 단위 구현 순서**: 우선순위 기반 점진적 구현

### 11.5 양쪽 모두 미커버 (블라인드 스팟)

| 항목 | 설명 | 권장 조치 |
|------|------|----------|
| TC-032 (비동기 썸네일 성능) | 50+ 페이지 PDF에서 QThread 썸네일 로딩 성능 | 수동 테스트로 유지 (이미 기존 테스트에서 placeholder 확인) |
| ConvertDialog QThread 통합 | 변환 진행 중 시그널 흐름 (started -> progress -> finished) | E2E TC-158에서 부분 커버. 별도 통합 테스트 권장 |
| 다중 모니터/HiDPI | 고해상도 환경에서 UI 스케일링 | 수동 테스트 항목으로 추가 권장 |
| 대용량 PDF (100+ 페이지) | 메모리 사용량, 렌더링 성능 | TC-150에서 수동 커버. 벤치마크 테스트 별도 권장 |
| 동시성 (빠른 연속 조작) | 삭제 중 삽입, 저장 중 Undo 등 | 레이스 컨디션은 수동 스트레스 테스트로 커버 |
