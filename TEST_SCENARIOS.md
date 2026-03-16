# TEST_SCENARIOS.md — 테스트 시나리오

각 Phase 구현 완료 후 아래 시나리오를 모두 통과해야 커밋합니다.

**테스트 유형:**
- **[AUTO]** — `pytest tests/ -v` 로 자동 실행
- **[MANUAL]** — 앱을 직접 실행하여 수동으로 확인

**상태 표기:**
- ✅ PASS — 통과
- ❌ FAIL — 실패 (이유 기재)
- ⏳ PENDING — 미실행

---

## Phase 0 — 프로젝트 초기화

| ID | 유형 | 시나리오 | 기대 결과 | 상태 |
|----|------|----------|-----------|------|
| P0-01 | [MANUAL] | git 저장소 초기화 확인 (`git log`) | 초기 커밋 존재 | ✅ PASS |
| P0-02 | [MANUAL] | `PLAN.md`, `CLAUDE.md`, `CHANGE.md`, `README.md` 존재 확인 | 4개 파일 모두 존재 | ✅ PASS |
| P0-03 | [MANUAL] | `.gitignore`에 `.claude/`, `.venv/`, `__pycache__/` 포함 확인 | 해당 항목 존재 | ✅ PASS |

---

## Phase 1 — 기반 (PDF 열기 + 렌더링 + MainWindow)

### 자동화 테스트

| ID | 유형 | 테스트 함수 | 시나리오 | 기대 결과 | 상태 |
|----|------|------------|----------|-----------|------|
| P1-A01 | [AUTO] | `test_open_valid_file` | 유효한 PDF 파일 열기 | is_open=True, page_count 정확 | ✅ PASS |
| P1-A02 | [AUTO] | `test_open_invalid_file_raises` | 존재하지 않는 파일 열기 | Exception 발생 | ✅ PASS |
| P1-A03 | [AUTO] | `test_close_clears_state` | 문서 닫기 | is_open=False, page_count=0 | ✅ PASS |
| P1-A04 | [AUTO] | `test_reopen_replaces_previous` | 다른 PDF로 재오픈 | page_count가 새 파일 기준으로 변경 | ✅ PASS |
| P1-A05 | [AUTO] | `test_render_page_returns_bytes` | 페이지 렌더링 | bytes 반환 | ✅ PASS |
| P1-A06 | [AUTO] | `test_render_page_png_header` | 렌더링 결과가 PNG 형식 | `\x89PNG` 헤더로 시작 | ✅ PASS |
| P1-A07 | [AUTO] | `test_render_page_zoom_affects_size` | zoom 값에 따라 이미지 크기 변화 | zoom=2.0 결과가 zoom=0.5보다 큼 | ✅ PASS |
| P1-A08 | [AUTO] | `test_render_thumbnail_returns_bytes` | 썸네일 렌더링 | PNG bytes 반환 | ✅ PASS |
| P1-A09 | [AUTO] | `test_get_page_size_returns_positive` | 페이지 크기 조회 | width > 0, height > 0 | ✅ PASS |
| P1-A10 | [AUTO] | `test_requires_open_raises_when_closed` | 닫힌 상태에서 렌더링 호출 | RuntimeError 발생 | ✅ PASS |
| P1-A11 | [AUTO] | `test_save_overwrites_original` | 저장 후 재오픈 | page_count 동일 | ✅ PASS |
| P1-A12 | [AUTO] | `test_save_without_path_raises_if_no_original` | 경로 없이 저장 | RuntimeError 발생 | ✅ PASS |
| P1-A13 | [AUTO] | `test_initial_state` | PdfViewer 초기 상태 | current_page=0, zoom=1.5 | ✅ PASS |
| P1-A14 | [AUTO] | `test_goto_page_changes_current` | 페이지 이동 | current_page 변경됨 | ✅ PASS |
| P1-A15 | [AUTO] | `test_goto_page_out_of_range_ignored` | 범위 초과 페이지 이동 | 기존 페이지 유지 | ✅ PASS |
| P1-A16 | [AUTO] | `test_page_changed_signal` | 페이지 변경 시그널 | page_changed(idx) emit | ✅ PASS |
| P1-A17 | [AUTO] | `test_zoom_in_increases_zoom` | 줌 인 | zoom 값 증가 | ✅ PASS |
| P1-A18 | [AUTO] | `test_zoom_out_decreases_zoom` | 줌 아웃 | zoom 값 감소 | ✅ PASS |
| P1-A19 | [AUTO] | `test_zoom_clamped_to_min` | 최소 줌 이하 입력 | MIN_ZOOM (0.25)로 고정 | ✅ PASS |
| P1-A20 | [AUTO] | `test_zoom_clamped_to_max` | 최대 줌 초과 입력 | MAX_ZOOM (4.0)으로 고정 | ✅ PASS |
| P1-A21 | [AUTO] | `test_zoom_changed_signal` | 줌 변경 시그널 | zoom_changed emit | ✅ PASS |

### 수동 테스트

| ID | 유형 | 시나리오 | 확인 방법 | 상태 |
|----|------|----------|-----------|------|
| P1-M01 | [MANUAL] | 앱 실행 | `python main.py` → 창 표시 | ✅ PASS |
| P1-M02 | [MANUAL] | PDF 파일 열기 | 툴바 "열기" 클릭 → 파일 선택 → 첫 페이지 표시 | ✅ PASS |
| P1-M03 | [MANUAL] | 썸네일 패널 표시 | 왼쪽에 페이지 썸네일 목록 표시 | ✅ PASS |
| P1-M04 | [MANUAL] | 썸네일 클릭으로 페이지 이동 | 썸네일 클릭 → 뷰어 해당 페이지로 이동 | ✅ PASS |
| P1-M05 | [MANUAL] | Ctrl+스크롤 줌 인/아웃 | 뷰어에서 Ctrl+휠 → 줌 변경, 툴바 스핀박스 동기화 | ✅ PASS |
| P1-M06 | [MANUAL] | 툴바 줌 스핀박스 | 값 직접 입력 → 뷰어 줌 변경 | ✅ PASS |
| P1-M07 | [MANUAL] | "맞춤" 버튼 | 클릭 → 뷰 크기에 맞게 줌 조정 | ✅ PASS |
| P1-M08 | [MANUAL] | 저장 | Ctrl+S → 현재 파일 덮어씀 | ✅ PASS |
| P1-M09 | [MANUAL] | 다른 이름으로 저장 | 파일 메뉴 → 새 경로에 저장 | ✅ PASS |
| P1-M10 | [MANUAL] | 상태바 | 현재 페이지 번호, 줌 비율 표시 | ✅ PASS |

---

## Phase 2 — 페이지 편집

### 자동화 테스트

| ID | 유형 | 테스트 함수 | 시나리오 | 기대 결과 | 상태 |
|----|------|------------|----------|-----------|------|
| P2-A01 | [AUTO] | `test_move_forward` | 페이지 앞→뒤 이동 | 이동 후 올바른 위치에 존재 | ✅ PASS |
| P2-A02 | [AUTO] | `test_move_backward` | 페이지 뒤→앞 이동 | 이동 후 올바른 위치에 존재 | ✅ PASS |
| P2-A03 | [AUTO] | `test_move_same_position_no_change` | 같은 위치로 이동 | 변경 없음 | ✅ PASS |
| P2-A04 | [AUTO] | `test_page_count_unchanged_after_move` | 이동 후 페이지 수 | page_count 변하지 않음 | ✅ PASS |
| P2-A05 | [AUTO] | `test_delete_single_page` | 단일 페이지 삭제 | page_count -1 | ✅ PASS |
| P2-A06 | [AUTO] | `test_delete_multiple_pages` | 복수 페이지 삭제 | page_count -N | ✅ PASS |
| P2-A07 | [AUTO] | `test_delete_empty_list_no_change` | 빈 목록 삭제 | 변경 없음 | ✅ PASS |
| P2-A08 | [AUTO] | `test_delete_preserves_other_pages` | 삭제 후 나머지 페이지 순서 유지 | 인접 페이지 내용 올바름 | ✅ PASS |
| P2-A09 | [AUTO] | `test_extract_creates_file` | 페이지 추출 | 새 PDF 파일 생성됨 | ✅ PASS |
| P2-A10 | [AUTO] | `test_extract_correct_page_count` | 추출된 PDF 페이지 수 | 선택한 개수와 일치 | ✅ PASS |
| P2-A11 | [AUTO] | `test_extract_single_page` | 단일 페이지 추출 | 내용 동일 | ✅ PASS |
| P2-A12 | [AUTO] | `test_extract_deduplicates_indices` | 중복 인덱스로 추출 | 중복 제거 후 추출 | ✅ PASS |
| P2-A13 | [AUTO] | `test_insert_at_beginning` | 맨 앞에 삽입 | page_count 증가, 위치 정확 | ✅ PASS |
| P2-A14 | [AUTO] | `test_insert_at_end` | 맨 끝에 삽입 | page_count 증가 | ✅ PASS |
| P2-A15 | [AUTO] | `test_insert_in_middle` | 중간에 삽입 | page_count 증가 | ✅ PASS |
| P2-A16 | [AUTO] | `test_inserted_content_is_correct` | 삽입된 페이지 내용 | 원본 내용과 동일 | ✅ PASS |
| P2-A17 | [AUTO] | `test_load_shows_correct_item_count` | PagePanel 로드 후 아이템 수 | doc.page_count와 일치 | ✅ PASS |
| P2-A18 | [AUTO] | `test_first_item_selected_after_load` | 로드 후 첫 아이템 선택 | currentRow() == 0 | ✅ PASS |
| P2-A19 | [AUTO] | `test_clear_removes_items` | clear() 후 | list.count() == 0 | ✅ PASS |
| P2-A20 | [AUTO] | `test_set_current_page_no_signal` | set_current_page() | 시그널 발생 없이 선택 변경 | ✅ PASS |
| P2-A21 | [AUTO] | `test_selected_indices_single` | 단일 선택 | [row] 반환 | ✅ PASS |
| P2-A22 | [AUTO] | `test_page_selected_signal_on_click` | 썸네일 클릭 시그널 | page_selected(idx) emit | ✅ PASS |
| P2-A23 | [AUTO] | `test_reload_preserves_selection` | reload_all() 후 선택 유지 | 이전 페이지 유지 | ✅ PASS |
| P2-A24 | [AUTO] | `test_reload_after_page_count_change` | 페이지 수 변경 후 reload | list.count() 갱신됨 | ✅ PASS |

### 수동 테스트

| ID | 유형 | 시나리오 | 확인 방법 | 상태 |
|----|------|----------|-----------|------|
| P2-M01 | [MANUAL] | 썸네일 드래그앤드롭 순서 변경 | 썸네일 드래그 → 다른 위치에 드롭 → 뷰어 이동 | ✅ PASS |
| P2-M02 | [MANUAL] | 다중 선택 (Ctrl 클릭) | Ctrl+클릭으로 여러 페이지 선택 | ✅ PASS |
| P2-M03 | [MANUAL] | 다중 선택 (Shift 클릭) | Shift+클릭으로 범위 선택 | ✅ PASS |
| P2-M04 | [MANUAL] | 우클릭 컨텍스트 메뉴 | 썸네일 우클릭 → 메뉴 표시 | ✅ PASS |
| P2-M05 | [MANUAL] | 페이지 삭제 (Delete키) | 페이지 선택 → Delete → 확인 다이얼로그 → 삭제 | ✅ PASS |
| P2-M06 | [MANUAL] | 페이지 삭제 취소 | 삭제 확인 다이얼로그에서 아니오 선택 → 취소됨 | ✅ PASS |
| P2-M07 | [MANUAL] | 모든 페이지 삭제 시도 | 전체 선택 후 삭제 → 경고 메시지 표시 | ✅ PASS |
| P2-M08 | [MANUAL] | 페이지 추출 | 선택 후 우클릭 → 추출 → 저장 경로 선택 → 새 PDF 생성 | ✅ PASS |
| P2-M09 | [MANUAL] | 페이지 삽입 다이얼로그 | 삽입 버튼 → 다이얼로그 표시 → PDF 선택 → 썸네일 표시 | ✅ PASS |
| P2-M10 | [MANUAL] | 페이지 삽입 실행 | 삽입 다이얼로그에서 페이지 선택 후 삽입 → 문서에 반영 | ✅ PASS |
| P2-M11 | [MANUAL] | 편집 후 썸네일 갱신 | 삭제/삽입 후 썸네일 패널 즉시 갱신 | ✅ PASS |
| P2-M12 | [MANUAL] | 편집 후 저장 | 편집 후 Ctrl+S → 파일에 변경사항 저장 | ✅ PASS |

---

## 통합 실행 결과 (최신)

| 날짜 | pytest 결과 | 수동 테스트 | 비고 |
|------|------------|------------|------|
| 2026-03-16 | 47/47 PASS (4.75s) | Phase 0~2 전체 PASS | Phase 2 완료 시점 |

---

## 테스트 규칙

1. **자동화 테스트**: 각 Phase 구현 후 `python -m pytest tests/ -v` 실행하여 전체 통과 확인
2. **수동 테스트**: 새 Phase의 수동 시나리오를 직접 실행하고 결과 기록
3. **실패 시**: 커밋 전에 반드시 수정하여 통과 상태로 만듦
4. **시나리오 업데이트**: 새 Phase 구현 후 해당 Phase의 시나리오를 이 파일에 추가

---

## 향후 추가 예정 시나리오

- **Phase 3** — 어노테이션 (텍스트/사각형/원/선 그리기)
- **Phase 4** — 문서 변환 (이미지/Word/PPT → PDF)
- **Phase 5** — Undo/Redo, 단축키, 패키징
