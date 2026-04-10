# jw_pdf 구현 계획서

## 1. 기술 스택 선정

### 핵심 결론: **Python + PyQt6**

| 항목 | 선택 | 이유 |
|------|------|------|
| GUI 프레임워크 | **PyQt6** | 고품질 위젯, PDF 뷰어 구현 용이, Windows 네이티브 느낌 |
| PDF 렌더링/어노테이션 | **PyMuPDF (fitz)** | 빠른 렌더링, 어노테이션 API 완비, 페이지 조작 강력 |
| PDF 페이지 편집 | **pikepdf** | 페이지 추출/병합/순서변경에 특화 |
| 문서 변환 | **LibreOffice CLI** + **Pillow** | docx/xlsx/pptx → PDF, 이미지 → PDF |
| 패키지 관리 | **uv** | 빠른 의존성 관리 |

> **Electron/Tauri를 쓰지 않는 이유:** PDF 라이브러리 생태계가 Python에 집중되어 있고, PyQt6이 데스크탑 앱 품질로는 충분함.

---

## 2. 프로젝트 구조

```
02_jw_pdf/
├── main.py                  # 앱 진입점
├── pyproject.toml           # 의존성 (uv)
├── PLAN.md                  # 이 파일 - 구현 계획서
├── CLAUDE.md                # Claude 협업 규칙
├── CHANGE.md                # 변경 이력
├── README.md                # 사용법 및 프로젝트 설명
│
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── pdf_document.py  # PDF 로드/저장 래퍼
│   │   ├── page_editor.py   # 페이지 추출/삽입/순서변경
│   │   ├── annotator.py     # 어노테이션 (텍스트/도형/선)
│   │   └── converter.py     # 다른 형식 → PDF 변환
│   │
│   ├── ui/
│   │   ├── main_window.py   # 메인 윈도우
│   │   ├── pdf_viewer.py    # PDF 미리보기 위젯
│   │   ├── page_panel.py    # 왼쪽 썸네일 패널
│   │   ├── toolbar.py       # 툴바
│   │   └── dialogs/
│   │       ├── insert_dialog.py
│   │       └── convert_dialog.py
│   │
│   └── utils/
│       └── temp_manager.py  # 임시 파일 관리
│
└── assets/
    └── icons/
```

---

## 3. UI 레이아웃 설계

```
┌─────────────────────────────────────────────────────────────┐
│  파일  편집  보기  도구                          [메뉴바]     │
├──────────────┬──────────────────────────────────────────────┤
│  [툴바]      │  📄 열기  💾 저장  ✂️ 추출  ➕ 삽입          │
│              │  ✏️ 텍스트  □ 사각형  ○ 원  ─ 선  🔄 변환   │
├──────────────┼──────────────────────────────────────────────┤
│              │                                              │
│  썸네일      │              PDF 미리보기                    │
│  패널        │              (현재 페이지 렌더링)            │
│              │                                              │
│  [페이지1]   │   ← 드래그로 어노테이션 그리기               │
│  [페이지2]   │                                              │
│  [페이지3]   │                                              │
│  ...         │                                              │
│              │                                              │
│  드래그로    │                                              │
│  순서변경    │                                              │
├──────────────┴──────────────────────────────────────────────┤
│  페이지 1 / 12   |   줌: 100%   |   도구: 선택             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 기능별 구현 방법

### 4-1. PDF 미리보기

```python
# PyMuPDF로 페이지를 QPixmap으로 변환
import fitz  # PyMuPDF

doc = fitz.open("sample.pdf")
page = doc[0]
mat = fitz.Matrix(2.0, 2.0)  # 2x 줌
pix = page.get_pixmap(matrix=mat)
# pix.tobytes() → QImage → QPixmap으로 Qt에 표시
```

### 4-2. 페이지 편집

```python
# pikepdf로 페이지 조작
import pikepdf

# 추출
with pikepdf.open("input.pdf") as pdf:
    new_pdf = pikepdf.Pdf.new()
    new_pdf.pages.extend([pdf.pages[0], pdf.pages[2]])  # 1, 3페이지 추출
    new_pdf.save("extracted.pdf")

# 삽입 (다른 PDF의 페이지를 특정 위치에 삽입)
pdf.pages.insert(2, other_pdf.pages[0])

# 순서 변경 (드래그앤드롭 후)
page = pdf.pages[old_idx]
del pdf.pages[old_idx]
pdf.pages.insert(new_idx, page)
```

### 4-3. 어노테이션

```python
# PyMuPDF로 어노테이션 추가
page = doc[0]

# 텍스트 추가
page.insert_text((100, 200), "주석 텍스트", fontsize=12, color=(1,0,0))

# 사각형
page.draw_rect(fitz.Rect(50, 50, 200, 150), color=(0,0,1), width=2)

# 자유선 (마우스 드래그 경로)
page.draw_polyline([(x1,y1), (x2,y2), ...], color=(0,1,0))

# 표준 어노테이션 (하이라이트, 메모 등)
annot = page.add_highlight_annot(fitz.Rect(...))
```

### 4-4. 문서 변환 → PDF

```python
# Word/Excel/PPT → PDF: LibreOffice CLI
import subprocess
subprocess.run([
    "soffice", "--headless", "--convert-to", "pdf",
    "--outdir", output_dir, input_file
])

# 이미지 → PDF: Pillow
from PIL import Image
img = Image.open("photo.jpg").convert("RGB")
img.save("output.pdf")
```

---

## 5. 의존성 목록

```toml
# pyproject.toml
[project]
name = "pdf-editor"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "PyQt6>=6.6.0",
    "PyMuPDF>=1.24.0",    # fitz
    "pikepdf>=8.0.0",
    "Pillow>=10.0.0",
    "reportlab>=4.0.0",   # PDF 생성
]
```

> LibreOffice는 별도 설치 필요 (변환 기능 사용 시)

---

## 6. 구현 순서 (단계별)

| Phase | 내용 | 산출물 |
|-------|------|--------|
| **Phase 1** | 프로젝트 초기화, PDF 열기+렌더링, 기본 MainWindow | 실행 가능한 뷰어 |
| **Phase 2** | 썸네일 패널, 드래그앤드롭 순서변경, 페이지 추출/삽입/삭제 | 페이지 편집 완성 |
| **Phase 3** | 마우스 이벤트 어노테이션 (텍스트/사각형/원/선) | 어노테이션 완성 |
| **Phase 4** | 이미지→PDF, LibreOffice 연동 변환, 진행 다이얼로그 | 변환 기능 완성 |
| **Phase 4.5** | 텍스트 어노테이션 스타일 확장 (폰트 선택, 글자 크기 조절, 볼드/이탤릭) | 텍스트 어노테이션 고도화 |
| **Phase 5** ✅ | Undo/Redo, 단축키, PyInstaller exe 패키징 → **v1.0.0** | 최종 배포 |

각 Phase 완료 시 git 커밋.

---

## 7. 주요 기술적 고려사항

- **어노테이션 렌더링**: PyMuPDF로 어노테이션을 PDF에 직접 쓰는 방식 → 저장 시 호환성 보장
- **썸네일 드래그앤드롭**: `QListWidget` + `setDragDropMode(InternalMove)` 활용
- **줌/스크롤**: `QGraphicsView` + `QGraphicsScene`으로 PDF 페이지 표시 → 줌/패닝 자연스럽게 처리
- **대용량 PDF**: 현재 보이는 페이지만 렌더링하는 지연 로딩 적용
- **변환 의존성**: LibreOffice가 없으면 해당 기능만 비활성화 처리
