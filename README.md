# PDF 편집 툴

개인용 PDF 편집 데스크탑 애플리케이션. Python + PyQt6 기반.

---

## 주요 기능

| 기능 | 상태 |
|------|------|
| PDF 미리보기 (줌/스크롤) | ✅ 완료 |
| 페이지 썸네일 패널 | ✅ 완료 |
| 페이지 편집 (추출/삽입/삭제/순서변경) | ✅ 완료 |
| 어노테이션 (텍스트/사각형/타원/선) | ✅ 완료 |
| 문서 변환 (이미지/Word/PPT → PDF) | ✅ 완료 |
| Undo/Redo (페이지 편집 + 어노테이션) | ✅ 완료 |
| exe 패키징 (PyInstaller) | ✅ 완료 |

---

## 요구사항

- Python 3.11 이상
- [uv](https://github.com/astral-sh/uv) 패키지 매니저
- (선택) LibreOffice — Word/PPT/Excel → PDF 변환 기능 사용 시 필요

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
02_PDF편집툴/
├── main.py                  # 앱 진입점
├── pyproject.toml           # 의존성
├── PLAN.md                  # 구현 계획서
├── CLAUDE.md                # Claude 협업 규칙
├── CHANGE.md                # 변경 이력
├── README.md                # 이 파일
│
├── app/
│   ├── core/
│   │   ├── pdf_document.py  # PDF 로드/저장/렌더링 래퍼 ✅
│   │   ├── page_editor.py   # 페이지 추출/삽입/순서변경 (Phase 2)
│   │   ├── annotator.py     # 어노테이션 (Phase 3)
│   │   └── converter.py     # 문서 변환 (Phase 4)
│   │
│   ├── ui/
│   │   ├── main_window.py   # 메인 윈도우 ✅
│   │   ├── pdf_viewer.py    # PDF 미리보기 위젯 ✅
│   │   ├── page_panel.py    # 썸네일 패널 ✅
│   │   ├── toolbar.py       # 툴바 ✅
│   │   └── dialogs/         # 각종 다이얼로그 (Phase 2~)
│   │
│   └── utils/
│       └── temp_manager.py  # 임시 파일 관리 (Phase 2)
│
└── assets/
    └── icons/
```

---

## 테스트 실행

```bash
uv run python -m pytest tests/ -v
```

총 **262개** 자동화 테스트 (Core 136 + UI 95 + E2E 31):

| 카테고리 | 파일 | 테스트 수 |
|----------|------|-----------|
| Core | `tests/core/test_pdf_document.py` | 16 |
| Core | `tests/core/test_page_editor.py` | 14 |
| Core | `tests/core/test_command_manager.py` | 31 |
| Core | `tests/core/test_annotator.py` | 60 |
| Core | `tests/core/test_converter.py` | 31 |
| Core | `tests/core/test_architecture.py` | 1 |
| UI | `tests/ui/test_pdf_viewer.py` | 22 |
| UI | `tests/ui/test_page_panel.py` | 15 |
| UI | `tests/ui/test_toolbar.py` | 10 |
| UI | `tests/ui/test_main_window.py` | 20 |
| UI | `tests/ui/test_main_window_menu.py` | 10 |
| UI | `tests/ui/test_convert_dialog.py` | 3 |
| E2E | `tests/e2e/test_tc155~tc166` | 31 |

---

## exe 빌드

```bash
scripts\build.bat
# 또는
uv run pyinstaller pdf_editor.spec --clean
```

결과물: `dist/PDF편집툴.exe`

---

## 개발 문서

- 구현 계획 상세: [PLAN.md](PLAN.md)
- 기능 정의서: [docs/FEATURE_SPEC.md](docs/FEATURE_SPEC.md)
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
