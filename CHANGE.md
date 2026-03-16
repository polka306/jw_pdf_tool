# CHANGE.md — 변경 이력

변경 사항은 최신 항목이 최상단에 위치합니다.

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
