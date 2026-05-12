# CHANGE.md — 변경 이력

변경 사항은 최신 항목이 최상단에 위치합니다.

---

## [미정] — 멀티 PDF 탭 기능

### 추가
- **멀티 탭** — 여러 PDF를 탭으로 동시에 열기 (`PdfTabPage`, `PdfTabWidget`)
- 탭 닫기 `Ctrl+W`, 복제 `Ctrl+Shift+D`, 분리 `Ctrl+Shift+N`
- 최근 닫은 탭 재열기 `Ctrl+Shift+T`
- 탭 전환 `Ctrl+Tab` / `Ctrl+1`~`Ctrl+9`
- 탭 우클릭 컨텍스트 메뉴 (닫기, 다른 탭 모두 닫기, 오른쪽 탭 모두 닫기, 복제, 새 창으로 열기, 파일 경로 복사)
- **분리 창** (`DetachedWindow`) — 탭을 독립 창으로 분리, 탭으로 되돌리기 지원
- 드래그앤드롭으로 여러 PDF를 각각 새 탭으로 열기
- 각 탭이 완전 독립 상태 유지 (페이지, 줌, 검색, 어노테이션 모드)
- 사이드바(썸네일/북마크)가 활성 탭에 자동 연동

### 변경
- `MainWindow`: 단일 `PdfDocument`/`PdfViewer` → `PdfTabWidget` 기반으로 재구성
- 모든 파일 작업·어노테이션·검색이 활성 탭(`active_tab()`)에 위임

### 테스트
- 신규 테스트 파일: `test_pdf_tab_page.py`, `test_pdf_tab_widget.py`, `test_detached_window.py`, `test_main_window_tabs.py`

---

## [v2.0.0] 2026-04-10 — 프로그램명 jw_pdf + 최종 정리

### 변경
- 프로그램명 `PDF 편집 툴` → `jw_pdf` 전체 변경 (코드/빌드/문서/테스트 18개 파일)
- `pdf_editor.spec` → `jw_pdf.spec` 리네임
- `pyproject.toml` name → `jw_pdf`
- `installer/setup.iss` MyAppName/MyAppExeName 갱신
- 모든 문서(README/CLAUDE/CHANGE/PLAN 등 14개) 프로그램명 통일

### 추가
- `scripts/build_installer.bat` — PyInstaller + Inno Setup 2단계 자동화
- `installer/setup.iss` — Inno Setup 설치 마법사 (파일 연결, 시작 메뉴)
- 기본 PDF 뷰어 등록 — SettingsDialog ↔ file_association 실제 동작 연결
- PdfViewer ↔ RenderEngine 실제 통합 (비동기 렌더, 즉시 스케일 3.7ms, debounce)
- 검색바 ↔ SearchEngine 연결 (Ctrl+F → 검색 → 결과 이동)
- 북마크 패널 ↔ 페이지 이동 시그널 연결
- 보충 시나리오 심각 8건 + 보통 11건 (자동 목차, DOCX 내보내기, 양식 가져오기 등)

### 테스트
- **595개** 자동화 테스트 전체 PASS (0 skip, 0 fail)

### 산출물
- `dist/jw_pdf-v2.0.0.exe` (66MB) — 단일 실행 파일
- `dist/jw_pdf-v2.0.0-Setup.exe` (68MB) — 설치 마법사

---

## [v2.0.0] 2026-04-07 — 전체 재설계 (Phase 1~8 + UI 통합)

### 신규 모듈 — app/core/ (10개)
- `search_engine.py` — 텍스트 검색 (대소문자/전체단어/정규식), 북마크 파서, 텍스트 추출
- `cli.py` — 명령줄 인자 파서 (argparse)
- `merger.py` — PDF 병합 (북마크 유지, 페이지 범위), 분할 (N페이지/범위/북마크 기준)
- `stamp.py` — 텍스트 스탬프 (프리셋/회전/투명도), 이미지 스탬프 (PNG/JPG)
- `security.py` — PDF 암호화 (AES-256/128, 권한 비트), 복호화, 리댁션 (민감정보 영구 삭제)
- `form_handler.py` — 양식 필드 읽기/쓰기/생성, JSON 내보내기
- `ocr_engine.py` — Tesseract/Windows OCR 통합, 텍스트 레이어 삽입
- `watermark.py` — 텍스트/이미지 워터마크, 머리글/바닥글 ({page}/{total} 변수), 베이츠 번호
- `optimizer.py` — PDF 최적화 (garbage collection, web/print 프리셋)
- `comparator.py` — PDF 텍스트 비교 (페이지별 diff, 페이지 수 차이 감지)

### 신규 모듈 — app/ui/ (3개)
- `render_engine.py` — QThreadPool 비동기 렌더링 엔진 (프리페치 ±3, 중복 제거, LRU 캐시)
- `search_bar.py` — 검색바 위젯 (입력/다음/이전/옵션 체크박스)
- `bookmark_panel.py` — 북마크 트리 패널 (QTreeWidget, 페이지 이동 시그널)

### 신규 모듈 — app/services/ (7개)
- `settings.py` — QSettings 기반 설정 관리 (최근 파일 10개, 키-값)
- `file_association.py` — .pdf ProgID 등록/해제 (winreg, HKCU, dry_run)
- `single_instance.py` — Named Mutex 기반 단일 인스턴스 관리
- `tray_service.py` — QSystemTrayIcon 래퍼 (메뉴, 토글 시그널)
- `updater.py` — 시맨틱 버전 비교
- `theme.py` — 다크/라이트 테마 스타일시트
- `print_service.py` — 가상 PDF 프린터 서비스, PrintSettings, 파일명 생성

### 신규 모듈 — app/utils/ (3개)
- `cache.py` — LRU 렌더 캐시 (줌×페이지×세대 키, 거리 기반 제거)
- `platform.py` — Windows 한글 폰트 경로 감지
- `async_worker.py` — QThread 기반 범용 비동기 워커

### 확장
- `app/core/pdf_document.py` — 페이지별 세대(generation) 카운터 (get/increment/reindex)
- `app/core/page_editor.py` — `rotate_page()`, `crop_page()`, `reset_cropbox()` 추가
- `app/core/converter.py` — `export_pages_to_images()` PNG/JPG, `export_pdf_to_text()` 추가
- `app/core/annotator.py` — `add_highlight()`, `add_underline()`, `add_strikeout()`, `add_sticky_note()`, `add_ink()` 추가
- `app/ui/main_window.py` — 최근 파일, Ctrl+F 검색, F11 전체화면, Ctrl+R 회전, Ctrl+Shift+M 병합, 사이드바 탭, 드래그앤드롭
- `app/ui/pdf_viewer.py` — 보기 모드 (single/continuous/two_page), 텍스트 선택/복사 API
- `main.py` — CLI 인자, 단일 인스턴스, 테마 로드

### 문서
- `docs/FEATURE_SPEC_v2.md` — v2.0.0 기능 정의서 (26개 섹션)
- `docs/BUILD_PLAN_v2.md` — TDD 기반 구축 계획서 (Phase 1~8, 에이전트 검증 프로토콜)

### 테스트
- **신규 테스트 234개** (TC-167 ~ TC-454 + 벤치마크)
- 전체 자동화 테스트 **506/572** PASS (66 skip — 미구현 다이얼로그 UI)

---

## [기능] 2026-04-03 — Markdown → PDF 변환 기능 추가

### 추가
- `app/core/converter.py`:
  - `SUPPORTED_MARKDOWN_EXTS` — 지원 확장자 (.md, .markdown, .mkd, .mdown)
  - `find_pandoc()` / `is_pandoc_available()` — Pandoc 탐지 (환경변수 → 설치경로 → PATH)
  - `convert_markdown_to_pdf()` — Pandoc 우선, Python 폴백 (markdown + fitz.Story)
  - `_convert_markdown_pandoc()` — Pandoc CLI 기반 고품질 변환 (한글 폰트, 코드 하이라이팅)
  - `_convert_markdown_fitz()` — 순수 Python 변환 (markdown→HTML→fitz.Story→PDF)
  - `_resolve_md_image_paths()` — 상대 이미지 경로 절대경로 변환
  - `_read_and_merge_markdown()` — 다중 MD 파일 병합
- `app/ui/dialogs/convert_dialog.py`:
  - `_MarkdownTab` — Markdown 변환 탭 (파일 추가/제거/순서 변경, Pandoc 상태 표시)
  - ConvertDialog에 3번째 탭 등록
  - `_ConvertWorker.run()` markdown 모드 분기
- `pyproject.toml`: `markdown>=3.5.0` 의존성 추가

### 테스트 추가
- `tests/core/test_converter_markdown.py` — 15개 테스트
  - Pandoc 탐지, 지원 형식, 단일/다중 파일 변환, 한글/테이블/코드블록, Pandoc 경로/폴백 검증
- `tests/ui/test_convert_dialog.py` — 탭 3개 확인 + Markdown 탭 존재 검증 추가

### 비고
- Pandoc 설치 시: 고품질 PDF (xelatex, 한글 맑은 고딕, 코드 하이라이팅)
- Pandoc 미설치 시: Python 폴백 자동 동작 (markdown + fitz.Story, 외부 의존성 불필요)
- 전체 자동화 테스트 277/277 PASS

---

## [테스트] 2026-04-03 — 종합 테스트 체계 구축 (155 → 262 테스트)

### 문서 작성
- `docs/FEATURE_SPEC.md` — 기능 정의서 (11개 섹션, 전체 기능 표 형식 정의)
- `docs/USER_SCENARIOS.md` — 유저 시나리오 107개 (US-001~US-107)
- `docs/TEST_SCENARIOS_FULL.md` — 테스트 시나리오 166개 (TC-001~TC-166, TC↔US 크로스 레퍼런스)
- `docs/E2E_TEST_PLAN.md` — E2E 테스트 구현 계획서 (TC-155~TC-166, 상호 검증 확정본)
- `docs/UNIT_COMPONENT_TEST_PLAN.md` — 단위/컴포넌트 테스트 구현 계획서 (TC-001~TC-154, 상호 검증 확정본)
- `docs/E2E_TEST_PLAN_QA.md` — QA Lead 독립 계획 + 리뷰 결과
- `docs/UNIT_COMPONENT_TEST_PLAN_QA.md` — QA Lead 독립 계획 + 리뷰 결과

### 테스트 인프라
- `tests/helpers.py` (신규) — 공통 monkeypatch 헬퍼 (load_pdf_directly, patch_* 함수, FakeInsertDialog)
- `tests/conftest.py` — 픽스처 추가 (main_window, corrupt_pdf, text_file, pdf_10pages)
- `tests/e2e/conftest.py` (신규) — E2E 전용 픽스처 (pdf_factory, image_factory)

### Core 테스트 추가 (기존 파일 확장)
- `tests/core/test_pdf_document.py` — TC-005, TC-008, TC-152 (3개 추가)
- `tests/core/test_page_editor.py` — TC-049, TC-050 (2개 추가)
- `tests/core/test_command_manager.py` — TC-100~103, TC-109, TC-111~112 (6개 추가)
- `tests/core/test_annotator.py` — TC-069~074, TC-080~082, TC-087, TC-093, TC-096, TC-098 (11개 추가)
- `tests/core/test_converter.py` — TC-114~115, TC-120~122 (5개 추가)
- `tests/core/test_architecture.py` (신규) — TC-154 Core/UI 분리 AST 검증 (1개)

### UI 테스트 추가
- `tests/ui/test_toolbar.py` (신규) — TC-064~065, TC-068~070, TC-081~082, TC-085, TC-139~140 (10개)
- `tests/ui/test_main_window.py` (신규) — 문서관리/페이지편집/Undo-Redo/도구전환 (20개)
- `tests/ui/test_main_window_menu.py` (신규) — 메뉴/레이아웃/단축키 구조 검증 (10개)
- `tests/ui/test_convert_dialog.py` (신규) — 변환 다이얼로그 (3개)
- `tests/ui/test_pdf_viewer.py` — TC-021, TC-028, TC-065 (3개 추가)
- `tests/ui/test_page_panel.py` — TC-030, TC-036 (2개 추가)

### E2E 테스트 (신규 디렉토리)
- `tests/e2e/` — 14개 파일, 31개 테스트
  - TC-155: 열기→어노테이션→저장→재열기 영속성
  - TC-156: 삽입→어노테이션→저장
  - TC-157: 이동→삭제→Undo×2 복원
  - TC-158: 이미지 변환→어노테이션→저장
  - TC-159: 추출→내용 검증
  - TC-160: 6개 어노테이션 Undo×6→Redo×6
  - TC-161~163: 도구 전환/상태바/메뉴-툴바 동기화
  - TC-164: 문서 미열림 시 비활성화
  - TC-165: 정보 대화상자
  - TC-166: 4종 커맨드 순차 Undo/Redo

### 비고
- 전체 자동화 테스트 262/262 PASS (53초)
- 기존 155개 → 262개 (107개 신규 추가, 69% 증가)

---

## [Phase 4.5] 2026-03-16 — 텍스트 어노테이션 스타일 확장

### 추가
- `app/core/annotator.py`:
  - `AnnotationStyle`에 `font_family`, `bold`, `italic` 필드 추가
  - `_FONT_MAP`: Base-14 폰트 (Helvetica/Times/Courier) 변형 매핑
  - `_KOREAN_BOLD_PATH`: 맑은 고딕 볼드 경로
  - `_resolve_font(style)`: 스타일에서 `(fontname, fontfile)` 결정 함수
  - `add_text()`: `_resolve_font()` 적용 — 폰트 패밀리/굵기/기울기 반영
- `app/ui/toolbar.py`:
  - 텍스트 스타일 컨트롤 추가: 폰트 패밀리 콤보, 크기 스핀박스, Bold/Italic 토글
  - 시그널: `text_font_changed`, `text_size_changed`, `text_bold_changed`, `text_italic_changed`
  - `set_text_tool_active()`: TEXT 도구 선택 시에만 컨트롤 활성화
  - `current_font_family`, `current_font_size`, `current_bold`, `current_italic` 속성
- `app/ui/main_window.py`:
  - 텍스트 스타일 시그널 연결 및 핸들러 추가
  - `_sync_annot_style()`: 텍스트 스타일 필드 동기화 포함
  - TEXT 도구 전환 시 텍스트 스타일 컨트롤 자동 활성화/비활성화
- `tests/core/test_annotator.py`:
  - `TestAnnotationStyle`: font_family/bold/italic 기본값 테스트 추가
  - `TestResolveFont`: 폰트 패밀리별 변형 11개 테스트
  - `TestAddTextStyled`: bold/italic/courier/times/korean 렌더링 7개 테스트
- `app/ui/page_panel.py`: `closeEvent` 추가 — 위젯 닫힐 때 백그라운드 로더 정리
- `tests/ui/test_page_panel.py`: `_cancel_loader()` 명시적 호출로 스레드 정리 수정

### 비고
- 자동 테스트 150/150 PASS

---

## [Phase 5] 2026-03-16 — Undo/Redo, 단축키, exe 패키징 → v1.0.0

### 추가
- `app/__version__.py` — 버전 상수 (`__version__`) 중앙 관리
  - 버전 체계: v0.x.0 = Phase x 완료, v1.0.0 = Phase 5 완료 (첫 안정 릴리즈)
- `app/core/command_manager.py` — 커맨드 패턴 Undo/Redo 구현
  - `Command` ABC, `CommandManager` (MAX_HISTORY=50)
  - `MovePageCommand`, `DeletePagesCommand`, `InsertPagesCommand`, `AddAnnotationCommand`
  - `_capture_page()` / `_insert_page()` / `_restore_page()` 내부 헬퍼
- `pdf_editor.spec` — PyInstaller 빌드 명세 (단일 exe, 콘솔 숨김)
- `scripts/build.bat` — Windows 빌드 스크립트
- `tests/core/test_command_manager.py` — CommandManager 단위 테스트 27개

### 수정
- `app/__version__.py`: v1.0.0 설정
- `pyproject.toml`: version = "1.0.0"
- `main.py`: `setApplicationVersion(__version__)` 추가
- `app/ui/main_window.py`:
  - 타이틀바에 버전 표시 (`v{__version__}`)
  - 편집 메뉴에 실행 취소(Ctrl+Z) / 다시 실행(Ctrl+Y) 액션
  - 보기 메뉴에 이전/다음 페이지(PgUp/PgDn) 단축키
  - 도움말 메뉴 + 정보 다이얼로그 (버전 + 기술 스택)
  - 모든 페이지 편집 작업을 커맨드 패턴으로 래핑
  - 파일 열기 시 Undo 스택 초기화
- `app/ui/pdf_viewer.py`:
  - `annotation_requested = pyqtSignal(object, str)` 추가
  - `_finalize_annotation`, `_handle_text_annotation`: 직접 호출 대신 시그널 발생
  - `refresh_page()` 공개 메서드 추가 (Undo 후 재렌더)

### 비고
- 자동 테스트 130/130 PASS
- Undo/Redo 대상: 페이지 이동/삭제/삽입, 어노테이션 추가 (사각형/타원/선/텍스트)

---

## [테스트] 2026-03-16 — 중간 수정 사항 자동화 테스트 추가

### 추가
- `tests/core/test_pdf_document.py` — `TestPdfDocumentSaveIncremental` (3개)
  - 동일 경로 incremental save 후 유효성 확인, page_count 보존, Save As 정상 동작
- `tests/ui/test_pdf_viewer.py` — `TestSceneToPdf` (4개)
  - rotation=0 페이지 원점 매핑, zoom 비율 스케일, MediaBox 범위 내 좌표, /Rotate 90 페이지 derotation_matrix 적용 확인
- `TEST_SCENARIOS.md` — "중간 수정 사항 (버그 픽스 / 성능 개선)" 섹션 추가 (자동 12개 + 수동 6개)

### 비고
- 자동 테스트 103/103 PASS

---

## [Phase 4] 2026-03-16 — 문서 변환 (이미지/Office → PDF)

### 추가
- `app/core/converter.py` — 변환 로직
  - `convert_images_to_pdf()`: PyMuPDF로 이미지(JPG/PNG/BMP/GIF/TIFF/WEBP) → PDF
  - `convert_office_to_pdf()`: LibreOffice CLI로 Office 문서 → PDF
  - `find_libreoffice()`: 환경 변수 → 표준 경로 → glob → PATH 순으로 탐지
  - Windows `CREATE_NO_WINDOW` 플래그로 콘솔 팝업 방지
- `app/ui/dialogs/convert_dialog.py` — 변환 다이얼로그
  - 이미지/Office 탭 구분, 파일 추가/제거/순서 변경
  - `_ConvertWorker(QObject)` + `QThread` 백그라운드 변환
  - LibreOffice 미설치 시 탭 내 상태 표시 및 비활성화
  - 변환 완료 후 "지금 열겠습니까?" 옵션
- `tests/core/test_converter.py` — 20개 단위 테스트 (전체 통과)

### 수정
- `app/ui/toolbar.py` — "변환" 버튼 및 `convert_requested` 시그널 추가 (Ctrl+Shift+C)
- `app/ui/main_window.py` — 도구(&T) 메뉴 추가, `_open_convert_dialog()` / `_open_converted_pdf()` 연결

### 비고
- 자동 테스트 91/91 PASS
- LibreOffice 미설치 환경에서도 이미지→PDF 기능은 정상 동작

---

## [fix] 2026-03-16 — 페이지 삽입 다이얼로그 썸네일 크기 수정

### 수정
- `app/ui/dialogs/insert_dialog.py`:
  - `setIconSize(self._list.iconSize())` → `setIconSize(QSize(THUMB_WIDTH, int(THUMB_WIDTH*1.5)))` 로 수정 (기본값 그대로 세팅하면 16×16으로 고정되는 버그)
  - `setGridSize(self._list.gridSize())` → `setGridSize(QSize(THUMB_WIDTH+16, int(THUMB_WIDTH*1.5)+28))` 로 수정
  - `item.setSizeHint(pixmap.size().__class__(...))` → `QSize(THUMB_WIDTH+8, pixmap.height()+22)` 로 정리

---

## [perf] 2026-03-16 — 파일 로드/저장 딜레이 개선 및 줌 UI 수정

### 수정
- `app/ui/page_panel.py`:
  - `_ThumbnailLoader(QThread)` 추가 — 파일 열기 시 썸네일을 백그라운드에서 순차 생성, placeholder 즉시 표시
  - `load_document()`: 백그라운드 로더 사용, 이전 로더 취소 후 재시작
  - `reload_all()`: `QApplication.processEvents()` 삽입으로 페이지 편집 중 UI 응답 유지
  - `reload_page(idx)` 추가 — 단일 페이지 썸네일만 갱신 (어노테이션 후 전체 재렌더 불필요)
  - `clear()`: 로더 취소 포함
- `app/core/pdf_document.py`:
  - `save()`: 같은 파일 덮어쓰기 시 `incremental=True` 사용 (변경분만 기록, 수 배 빠름). 실패 시 전체 저장으로 자동 폴백. Save As는 기존 `garbage=4 + deflate` 유지.
- `app/ui/main_window.py`:
  - `_on_annotation_added()`: `reload_all()` → `reload_page(current_page)` 로 변경 (30페이지 전체 재렌더 → 1페이지 갱신)
- `app/ui/toolbar.py`:
  - 줌 스핀박스 width 72 → 82px (퍼센트 숫자 잘림 현상 수정)

---

## [fix] 2026-03-16 — 어노테이션 좌표 및 툴바 UI 개선

### 수정
- `app/ui/pdf_viewer.py`:
  - `_scene_to_pdf()`: `page.derotation_matrix` 적용으로 `/Rotate 90` 페이지 좌표 변환 정확도 개선
  - rotation=0인 페이지에서는 항등행렬이므로 동작 그대로 유지
- `app/ui/toolbar.py`:
  - "페이지 삭제/추출/삽입" 버튼 레이블 → "삭제/추출/삽입" 으로 축약 (툴바 잘림 현상 개선, 툴팁은 유지)

### 계획 추가
- `PLAN.md`: Phase 4.5 — 텍스트 어노테이션 스타일 확장 (폰트 선택, 글자 크기 조절, 볼드/이탤릭) 항목 추가

---

## [fix] 2026-03-16 — 가로 페이지 어노테이션 좌표 재수정

### 수정
- `app/ui/pdf_viewer.py`:
  - `_scene_to_pdf()`: `page.transformation_matrix` 역변환 방식 제거 → `scene / zoom` 단순 나눗셈으로 복원
  - 근거: `get_pixmap(Matrix(zoom,zoom))`과 Shape API(`draw_rect`/`insert_text` 등)는 동일한 display space(page.rect 기준, top-left 원점, y 아래 방향)를 사용하므로 rotation 여부와 무관하게 `scene / zoom = draw_coord`가 성립함
  - 이전 `transformation_matrix` 역변환은 PDF user space(bottom-left, y 위 방향)를 반환해 좌표가 더 어긋나던 버그 수정

---

## [fix] 2026-03-16 — 썸네일 크기 및 가로 페이지 어노테이션 좌표 수정

### 수정
- `app/ui/page_panel.py`:
  - `setIconSize()` 누락으로 썸네일이 16×16으로 표시되던 문제 수정 → `QSize(THUMB_WIDTH, THUMB_WIDTH*1.5)` 설정
  - `_make_item()`: `setSizeHint`를 실제 픽스맵 높이 기준으로 설정 (가로/세로 페이지 모두 대응)
- `app/ui/pdf_viewer.py`:
  - `_scene_to_pdf()`: 단순 `/ zoom` → `page.transformation_matrix × zoom_mat` 역변환 적용
  - 가로 방향(rotation=90/270) 페이지에서 어노테이션 좌표가 어긋나던 문제 수정

---

## [fix] 2026-03-16 — 드래그앤드롭 PyQt6 호환성 수정

### 수정
- `app/ui/page_panel.py`: `QDropEvent.pos()` → `event.position().toPoint()` (PyQt6에서 `pos()` 제거됨)

---

## [Phase 3] 2026-03-16 — 어노테이션 (텍스트/사각형/타원/선)

### 추가
- `app/core/annotator.py` — 어노테이션 로직 (add_rect/add_ellipse/add_line/add_text, AnnotationTool 열거형, AnnotationStyle)
- `tests/core/test_annotator.py` — 어노테이션 단위 테스트 24개

### 수정
- `app/ui/pdf_viewer.py` — 어노테이션 도구 마우스 이벤트 (드래그 미리보기, 클릭 확정), `set_tool()`, `set_annotation_style()`
- `app/ui/toolbar.py` — 어노테이션 도구 버튼군 (QActionGroup 배타적 선택), 색상 피커, 굵기 스핀박스
- `app/ui/main_window.py` — 어노테이션 메뉴, 도구 변경/색상/굵기 연결, 상태바 도구 표시

### 비고
- 한글 폰트 자동 감지 (Windows Malgun Gothic)
- 어노테이션은 PDF 콘텐츠 스트림에 직접 기록 (저장 시 모든 뷰어에서 표시)
- 자동 테스트 71/71 PASS

---

## [문서] 2026-03-16 — 테스트 시나리오 문서화 및 Phase 절차 규칙 확립

### 추가
- `TEST_SCENARIOS.md` — Phase 0~2 전체 테스트 시나리오 (자동화 47개 + 수동 25개)

### 수정
- `CLAUDE.md` — Phase 구현 절차 규칙 추가 (코드→시나리오→자동테스트→수동테스트→문서→커밋), 문서 목록에 `TEST_SCENARIOS.md` 추가

---

## [테스트] 2026-03-16 — 자동화 테스트 환경 구축 (pytest + pytest-qt)

### 추가
- `tests/conftest.py` — 픽스처 (테스트용 PDF 프로그래매틱 생성, Qt offscreen 설정)
- `tests/core/test_pdf_document.py` — PdfDocument 단위 테스트 (열기/닫기/렌더링/저장)
- `tests/core/test_page_editor.py` — page_editor 단위 테스트 (move/delete/extract/insert)
- `tests/ui/test_pdf_viewer.py` — PdfViewer 위젯 테스트 (pytest-qt, offscreen 헤드리스)
- `tests/ui/test_page_panel.py` — PagePanel 위젯 테스트

### 수정
- `pyproject.toml` — dev 의존성에 pytest, pytest-qt 추가

### 결과
- 테스트 47개, 전체 통과 (4.75s)
- 실행: `python -m pytest tests/ -v`

---

## [Phase 2] 2026-03-16 — 페이지 편집 (순서변경/삭제/추출/삽입)

### 추가
- `app/core/page_editor.py` — 페이지 편집 로직 (move/delete/extract/insert, PyMuPDF 사용)
- `app/ui/dialogs/insert_dialog.py` — 다른 PDF에서 페이지 선택 삽입 다이얼로그

### 수정
- `app/ui/page_panel.py` — 드래그앤드롭 순서변경, 다중선택(Ctrl/Shift), 우클릭 컨텍스트 메뉴 추가
- `app/ui/toolbar.py` — 페이지 삭제/추출/삽입 버튼 및 단축키(Delete) 추가
- `app/ui/main_window.py` — 페이지 편집 기능 전체 연결, 편집 메뉴 추가, 편집 후 UI 갱신 로직

---

## [Phase 1] 2026-03-16 — 기반 구현 (PDF 열기 + 렌더링 + 기본 MainWindow)

### 추가
- `pyproject.toml` — 의존성 정의 (PyQt6, PyMuPDF, pikepdf, Pillow, reportlab)
- `main.py` — 앱 진입점
- `app/core/pdf_document.py` — PyMuPDF 래퍼 (열기/저장/렌더링/썸네일)
- `app/ui/pdf_viewer.py` — QGraphicsView 기반 PDF 뷰어 (Ctrl+스크롤 줌, 25%~400%)
- `app/ui/page_panel.py` — 좌측 썸네일 패널 (클릭으로 페이지 이동)
- `app/ui/toolbar.py` — 툴바 (열기/저장/줌 컨트롤, 단축키)
- `app/ui/main_window.py` — 메인 윈도우 (스플리터 레이아웃, 메뉴바, 상태바)
- `app/__init__.py`, `app/core/__init__.py`, `app/ui/__init__.py` 등 패키지 파일

### 비고
- uv sync 대신 pip로 직접 설치 가능 (uv의 DNS 이슈 발생 시)

---

## [Phase 0] 2026-03-16 — 프로젝트 초기화

### 추가
- `PLAN.md` — 전체 구현 계획서 작성 (기술 스택, 구조, Phase별 구현 계획)
- `CLAUDE.md` — 협업 규칙 정의 (커밋 규칙, 코드 컨벤션, 문서 관리 정책)
- `CHANGE.md` — 변경 이력 파일 신규 생성
- `README.md` — 프로젝트 소개 및 초기 설정 방법 작성
- `.gitignore` — Python/PyQt 프로젝트용 gitignore 설정
- git 저장소 초기화
