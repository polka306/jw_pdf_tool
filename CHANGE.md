# CHANGE.md — 변경 이력

변경 사항은 최신 항목이 최상단에 위치합니다.

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
