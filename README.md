# jw_pdf

개인용 PDF 편집 데스크탑 애플리케이션. Python + PyQt6 기반.

---

## 주요 기능

### 기본 기능 (v1.0.0)
| 기능 | 상태 |
|------|------|
| PDF 미리보기 (줌/스크롤) | ✅ 완료 |
| 페이지 썸네일 패널 | ✅ 완료 |
| 페이지 편집 (추출/삽입/삭제/순서변경) | ✅ 완료 |
| 어노테이션 (텍스트/사각형/타원/선) | ✅ 완료 |
| 문서 변환 (이미지/Word/PPT/Markdown → PDF) | ✅ 완료 |
| Undo/Redo (페이지 편집 + 어노테이션) | ✅ 완료 |
| exe 패키징 (PyInstaller) | ✅ 완료 |

### 확장 기능 (v2.0.0)
| 기능 | 상태 |
|------|------|
| 비동기 렌더링 엔진 (LRU 캐시, 프리페치) | ✅ 완료 |
| 텍스트 검색 (Ctrl+F, 정규식, 대소문자) | ✅ 완료 |
| 북마크 패널 (트리 표시, 클릭 이동) | ✅ 완료 |
| PDF 병합/분할 (북마크 기준, N페이지) | ✅ 완료 |
| 페이지 회전 (Ctrl+R) / 크롭 | ✅ 완료 |
| PDF → 이미지/텍스트 내보내기 | ✅ 완료 |
| 하이라이트/밑줄/취소선 어노테이션 | ✅ 완료 |
| 스티키 노트 / 자유형 그리기 (Ink) | ✅ 완료 |
| 텍스트/이미지 스탬프 | ✅ 완료 |
| PDF 암호화 (AES-256) / 복호화 | ✅ 완료 |
| 양식 필드 읽기/쓰기/생성/내보내기 | ✅ 완료 |
| OCR 텍스트 인식 (Tesseract/Windows) | ✅ 완료 |
| 워터마크 / 머리글·바닥글 / 베이츠 번호 | ✅ 완료 |
| PDF 최적화 (파일 크기 감소) | ✅ 완료 |
| PDF 비교 (텍스트 diff) | ✅ 완료 |
| 리댁션 (민감정보 영구 삭제) | ✅ 완료 |
| 파일 확장자 연결 (.pdf 기본 뷰어) | ✅ 완료 |
| 단일 인스턴스 (Named Mutex) | ✅ 완료 |
| 시스템 트레이 상주 | ✅ 완료 |
| 다크/라이트 테마 | ✅ 완료 |
| 드래그앤드롭 파일 열기 | ✅ 완료 |
| 명령줄 인자 (파일 경로) | ✅ 완료 |
| 전체 화면 모드 (F11) | ✅ 완료 |
| 최근 파일 목록 | ✅ 완료 |
| 가상 PDF 프린터 서비스 | ✅ 완료 |

---

## 요구사항

- Python 3.11 이상
- [uv](https://github.com/astral-sh/uv) 패키지 매니저
- (선택) LibreOffice — Word/PPT/Excel → PDF 변환 기능 사용 시 필요
- (선택) [Pandoc](https://pandoc.org) — Markdown → PDF 고품질 변환 시 필요 (미설치 시 Python 기본 변환 사용)

---

## 설치 및 실행

```bash
# 방법 1: uv 사용
uv sync
uv run python main.py

# 방법 2: pip 직접 설치 (uv 네트워크 문제 발생 시)
pip install PyQt6 PyMuPDF pikepdf Pillow reportlab
python main.py
```

---

## 프로젝트 구조

```
02_jw_pdf/
├── main.py                      # 앱 진입점 (CLI, 단일 인스턴스, 테마)
├── pyproject.toml               # 의존성
│
├── app/
│   ├── core/                    # 순수 비즈니스 로직 (UI 의존 없음)
│   │   ├── pdf_document.py      # PDF 로드/저장/렌더링 + 세대 카운터
│   │   ├── page_editor.py       # 페이지 편집 + 회전/크롭
│   │   ├── annotator.py         # 어노테이션 + 하이라이트/Ink/스티키노트
│   │   ├── converter.py         # 문서 변환 + PDF→이미지/텍스트
│   │   ├── command_manager.py   # Undo/Redo (Command 패턴)
│   │   ├── search_engine.py     # 텍스트 검색 + 북마크 파서
│   │   ├── merger.py            # PDF 병합/분할
│   │   ├── stamp.py             # 텍스트/이미지 스탬프
│   │   ├── security.py          # 암호화/복호화/리댁션
│   │   ├── form_handler.py      # 양식 필드 읽기/쓰기/생성
│   │   ├── ocr_engine.py        # OCR (Tesseract/Windows)
│   │   ├── watermark.py         # 워터마크/머리글/바닥글/베이츠
│   │   ├── optimizer.py         # PDF 최적화
│   │   ├── comparator.py        # PDF 비교
│   │   └── cli.py               # 명령줄 인자 파서
│   │
│   ├── ui/                      # PyQt6 UI 컴포넌트
│   │   ├── main_window.py       # 메인 윈도우 + 메뉴/단축키/D&D
│   │   ├── pdf_viewer.py        # PDF 뷰어 + 보기 모드/텍스트 선택
│   │   ├── render_engine.py     # 비동기 렌더링 엔진
│   │   ├── page_panel.py        # 썸네일 패널
│   │   ├── bookmark_panel.py    # 북마크 트리 패널
│   │   ├── search_bar.py        # 검색바
│   │   ├── toolbar.py           # 메인 툴바
│   │   └── dialogs/             # 각종 다이얼로그
│   │
│   ├── services/                # 시스템 통합 (Windows 특화)
│   │   ├── settings.py          # QSettings 설정 관리
│   │   ├── file_association.py  # 파일 확장자 연결
│   │   ├── single_instance.py   # 단일 인스턴스
│   │   ├── tray_service.py      # 시스템 트레이
│   │   ├── theme.py             # 다크/라이트 테마
│   │   ├── updater.py           # 버전 비교
│   │   └── print_service.py     # 가상 PDF 프린터
│   │
│   └── utils/                   # 공통 유틸리티
│       ├── cache.py             # LRU 렌더 캐시
│       ├── platform.py          # 플랫폼 추상화
│       └── async_worker.py      # 비동기 워커
│
├── tests/                       # pytest (506+ 테스트)
│   ├── core/                    # Core 단위 테스트
│   ├── ui/                      # UI 컴포넌트 테스트
│   ├── services/                # 서비스 테스트
│   ├── e2e/                     # E2E 통합 테스트
│   ├── bench/                   # 성능 벤치마크
│   └── utils/                   # 유틸 테스트
│
├── docs/                        # 설계 문서
└── assets/
    └── icons/
```

---

## 테스트 실행

```bash
uv run python -m pytest tests/ -v
```

총 **506개** 자동화 테스트 (Core + UI + Services + E2E + Bench):

| 카테고리 | 테스트 수 | 비고 |
|----------|-----------|------|
| Core 단위 (v1.0.0) | 153 | 문서/편집/커맨드/어노테이션/변환/아키텍처 |
| Core 단위 (v2.0.0) | 95 | 캐시/세대/검색/북마크/회전/병합/크롭/내보내기/암호화/양식/OCR/워터마크/최적화/비교/리댁션/스탬프 |
| UI 컴포넌트 (v1.0.0) | 80 | 뷰어/패널/툴바/윈도우/다이얼로그 |
| UI 컴포넌트 (v2.0.0) | 75 | 렌더엔진/성능/가상화/검색바/북마크/모드/전체화면 (66 skip 포함) |
| Services | 32 | 설정/파일연결/단일인스턴스/트레이/테마/프린터 |
| E2E (v1.0.0) | 31 | TC-155~166 |
| E2E (v2.0.0) | 35 | TC-197~454 |
| 벤치마크 | 5 | 렌더/캐시/줌/열기/어노테이션 속도 |

---

## exe 빌드

```bash
scripts\build.bat
# 또는
uv run pyinstaller pdf_editor.spec --clean
```

결과물: `dist/jw_pdf.exe`

---

## 키보드 단축키

| 단축키 | 기능 |
|--------|------|
| Ctrl+O | PDF 열기 |
| Ctrl+S | 저장 |
| Ctrl+Z / Ctrl+Y | 실행 취소 / 다시 실행 |
| Ctrl+F | 텍스트 검색 |
| Ctrl+R / Ctrl+Shift+R | 페이지 회전 (시계/반시계) |
| Ctrl+Shift+M | PDF 병합 |
| Ctrl+Shift+C | 변환 다이얼로그 |
| F11 | 전체 화면 |
| PgUp / PgDn | 이전/다음 페이지 |
| Delete | 선택 페이지 삭제 |
| Ctrl+=/- / Ctrl+0 | 줌 인/아웃 / 화면 맞춤 |
| Escape | 선택 도구 전환 |

---

## 개발 문서

- 구현 계획 상세: [PLAN.md](PLAN.md)
- **v2.0.0 기능 정의서**: [docs/FEATURE_SPEC_v2.md](docs/FEATURE_SPEC_v2.md)
- **v2.0.0 구축 계획서**: [docs/BUILD_PLAN_v2.md](docs/BUILD_PLAN_v2.md)
- 기능 정의서 (v1.0.0): [docs/FEATURE_SPEC.md](docs/FEATURE_SPEC.md)
- 유저 시나리오: [docs/USER_SCENARIOS.md](docs/USER_SCENARIOS.md)
- 테스트 시나리오 (상세): [docs/TEST_SCENARIOS_FULL.md](docs/TEST_SCENARIOS_FULL.md)
- E2E 테스트 계획: [docs/E2E_TEST_PLAN.md](docs/E2E_TEST_PLAN.md)
- 단위/컴포넌트 테스트 계획: [docs/UNIT_COMPONENT_TEST_PLAN.md](docs/UNIT_COMPONENT_TEST_PLAN.md)
- 테스트 시나리오 (Phase별): [TEST_SCENARIOS.md](TEST_SCENARIOS.md)
- 변경 이력: [CHANGE.md](CHANGE.md)
- 협업 규칙: [CLAUDE.md](CLAUDE.md)

---

## 기술 스택

- **GUI**: PyQt6
- **PDF 처리**: PyMuPDF (fitz), pikepdf
- **이미지 처리**: Pillow
- **문서 변환**: LibreOffice CLI
- **OCR**: Tesseract / Windows OCR
- **디지털 서명**: pyHanko (예정)
- **시스템 통합**: pywin32, winreg
