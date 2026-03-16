# CHANGE.md — 변경 이력

변경 사항은 최신 항목이 최상단에 위치합니다.

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
