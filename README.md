# jw_pdf

개인용 PDF 편집 데스크탑 애플리케이션. Python + PyQt6 기반.

---

## 주요 기능

### 기본 기능 (v1.0.0)
| 기능 | 상태 |
|------|------|
| PDF 미리보기 (줌/스크롤) | ✅ |
| 페이지 썸네일 패널 | ✅ |
| 페이지 편집 (추출/삽입/삭제/순서변경) | ✅ |
| 어노테이션 (텍스트/사각형/타원/선) | ✅ |
| 문서 변환 (이미지/Word/PPT/Markdown → PDF) | ✅ |
| Undo/Redo (페이지 편집 + 어노테이션) | ✅ |

### 확장 기능 (v2.0.0)
| 기능 | 상태 |
|------|------|
| 비동기 렌더링 엔진 (LRU 캐시, 프리페치) | ✅ |
| 텍스트 검색 (Ctrl+F, 정규식, 대소문자) | ✅ |
| 북마크 패널 (트리 표시, 클릭 이동) | ✅ |
| PDF 병합/분할 (북마크 기준, N페이지) | ✅ |
| 페이지 회전 (Ctrl+R) / 크롭 | ✅ |
| PDF → 이미지/텍스트/DOCX 내보내기 | ✅ |
| 하이라이트/밑줄/취소선/스티키노트/Ink | ✅ |
| 텍스트/이미지 스탬프 | ✅ |
| PDF 암호화 (AES-256) / 복호화 / 리댁션 | ✅ |
| 양식 필드 읽기/쓰기/생성/가져오기/내보내기 | ✅ |
| OCR 텍스트 인식 (Tesseract/Windows OCR) | ✅ |
| 워터마크 / 머리글·바닥글 / 베이츠 번호 | ✅ |
| PDF 최적화 / PDF 비교 (텍스트 diff) | ✅ |
| 자동 목차 생성 (폰트 크기 기반) | ✅ |
| 파일 확장자 연결 / 단일 인스턴스 / 시스템 트레이 | ✅ |
| 다크/라이트 테마 / 전체 화면 (F11) | ✅ |
| 드래그앤드롭 / 명령줄 인자 / 최근 파일 | ✅ |
| 가상 PDF 프린터 서비스 | ✅ |

---

## 요구사항

- Python 3.11 이상
- [uv](https://github.com/astral-sh/uv) 패키지 매니저
- (선택) LibreOffice — Word/PPT/Excel → PDF 변환
- (선택) [Pandoc](https://pandoc.org) — Markdown → PDF 고품질 변환
- (선택) [Tesseract](https://github.com/tesseract-ocr/tesseract) — 고정밀 OCR

---

## 설치 및 실행

```bash
# 의존성 설치 + 실행
uv sync
uv run python main.py

# 또는 pip 직접 설치
pip install PyQt6 PyMuPDF pikepdf Pillow reportlab markdown
python main.py

# 명령줄로 파일 바로 열기
uv run python main.py "C:\path\to\file.pdf"
```

---

## 프로젝트 구조

```
jw_pdf/
├── main.py                      # 앱 진입점 (CLI, 단일 인스턴스, 테마)
├── pyproject.toml               # 의존성
├── jw_pdf.spec                  # PyInstaller 빌드 명세
│
├── app/
│   ├── core/                    # 순수 비즈니스 로직 (UI 의존 없음)
│   │   ├── pdf_document.py      # PDF 로드/저장/렌더링 + 세대 카운터
│   │   ├── page_editor.py       # 페이지 편집 + 회전/크롭
│   │   ├── annotator.py         # 어노테이션 (도형/텍스트/하이라이트/Ink/스티키)
│   │   ├── converter.py         # 변환 (이미지/Office/Markdown → PDF, PDF → 이미지/텍스트/DOCX)
│   │   ├── command_manager.py   # Undo/Redo (Command 패턴)
│   │   ├── search_engine.py     # 텍스트 검색 + 북마크 파서 + 자동 목차
│   │   ├── merger.py            # PDF 병합/분할
│   │   ├── stamp.py             # 텍스트/이미지 스탬프
│   │   ├── security.py          # 암호화/복호화/리댁션
│   │   ├── form_handler.py      # 양식 필드 (읽기/쓰기/생성/내보내기/가져오기)
│   │   ├── ocr_engine.py        # OCR (Tesseract/Windows OCR)
│   │   ├── watermark.py         # 워터마크/머리글/바닥글/베이츠 번호
│   │   ├── optimizer.py         # PDF 최적화
│   │   ├── comparator.py        # PDF 비교
│   │   └── cli.py               # 명령줄 인자 파서
│   │
│   ├── ui/                      # PyQt6 UI 컴포넌트
│   │   ├── main_window.py       # 메인 윈도우 (메뉴/단축키/D&D/전체화면)
│   │   ├── pdf_viewer.py        # PDF 뷰어 (비동기 렌더/줌 즉시 스케일/보기 모드)
│   │   ├── render_engine.py     # QThreadPool 비동기 렌더링 엔진
│   │   ├── page_panel.py        # 썸네일 패널
│   │   ├── bookmark_panel.py    # 북마크 트리 패널
│   │   ├── search_bar.py        # 검색바
│   │   ├── toolbar.py           # 메인 툴바
│   │   └── dialogs/             # 다이얼로그 (병합/분할/보안/워터마크/OCR/비교/스탬프/양식/인쇄/설정/서명)
│   │
│   ├── services/                # 시스템 통합 (Windows)
│   │   ├── settings.py          # QSettings 설정 관리
│   │   ├── file_association.py  # .pdf 파일 확장자 연결
│   │   ├── single_instance.py   # 단일 인스턴스 (Named Mutex)
│   │   ├── tray_service.py      # 시스템 트레이
│   │   ├── theme.py             # 다크/라이트 테마 스타일시트
│   │   ├── updater.py           # 버전 비교
│   │   └── print_service.py     # 가상 PDF 프린터
│   │
│   └── utils/                   # 공통 유틸리티
│       ├── cache.py             # LRU 렌더 캐시
│       ├── platform.py          # 플랫폼 추상화 (폰트 경로)
│       └── async_worker.py      # QThread 비동기 워커
│
├── tests/                       # pytest (595개 테스트)
├── installer/                   # Inno Setup 설치 마법사
├── scripts/                     # 빌드 스크립트
├── docs/                        # 설계 문서
└── assets/                      # 아이콘 등 리소스
```

---

## 테스트

```bash
uv run python -m pytest tests/ -v
```

**595개** 자동화 테스트 (100% PASS, ~37초):

| 카테고리 | 수 |
|----------|---|
| Core 단위 | 271 |
| UI 컴포넌트 | 168 |
| Services | 32 |
| E2E 통합 | 66 |
| 성능 벤치마크 | 5 |
| 보충 시나리오 | 23 |
| 기타 (conftest/helpers) | 30 |

---

## 빌드

### exe 단일 파일
```bash
scripts\build.bat
# 또는
uv run pyinstaller jw_pdf.spec --clean
```
→ `dist/jw_pdf-v2.0.0.exe` (66MB)

### 설치 마법사 (exe + Inno Setup)
```bash
scripts\build_installer.bat
```
→ `dist/jw_pdf-v2.0.0-Setup.exe` (68MB)

설치 마법사 포함 기능: 바탕화면 아이콘, 시작 메뉴, PDF 파일 연결, 제거 프로그램

---

## 키보드 단축키

| 단축키 | 기능 |
|--------|------|
| Ctrl+O | PDF 열기 |
| Ctrl+S | 저장 |
| Ctrl+Z / Ctrl+Y | 실행 취소 / 다시 실행 |
| Ctrl+F | 텍스트 검색 |
| Ctrl+P | 인쇄 |
| Ctrl+R / Ctrl+Shift+R | 페이지 회전 (시계/반시계) |
| Ctrl+Shift+M | PDF 병합 |
| Ctrl+Shift+C | 변환 다이얼로그 |
| F11 | 전체 화면 |
| PgUp / PgDn | 이전/다음 페이지 |
| Delete | 선택 페이지 삭제 |
| Ctrl+= / Ctrl+- / Ctrl+0 | 줌 인/아웃/맞춤 |
| Escape | 선택 도구 전환 |

---

## 개발 문서

| 문서 | 설명 |
|------|------|
| [PLAN.md](PLAN.md) | v1.0.0 구현 계획서 |
| [docs/FEATURE_SPEC_v2.md](docs/FEATURE_SPEC_v2.md) | v2.0.0 기능 정의서 (26개 섹션) |
| [docs/BUILD_PLAN_v2.md](docs/BUILD_PLAN_v2.md) | v2.0.0 TDD 구축 계획서 (Phase 1~8) |
| [docs/FEATURE_SPEC.md](docs/FEATURE_SPEC.md) | v1.0.0 기능 정의서 |
| [CHANGE.md](CHANGE.md) | 변경 이력 |
| [CLAUDE.md](CLAUDE.md) | Claude 협업 규칙 |
| [TEST_SCENARIOS.md](TEST_SCENARIOS.md) | 테스트 시나리오 (Phase별) |

---

## 기술 스택

| 역할 | 라이브러리 |
|------|-----------|
| GUI | PyQt6 |
| PDF 렌더링/어노테이션 | PyMuPDF (fitz) |
| PDF 페이지 편집 | pikepdf |
| 이미지 처리 | Pillow |
| PDF 생성 | reportlab |
| 문서 변환 | LibreOffice CLI |
| OCR | Tesseract / Windows OCR |
| 시스템 통합 | winreg, ctypes |
| 패키지 관리 | uv |
| exe 빌드 | PyInstaller |
| 설치 마법사 | Inno Setup 6 |
