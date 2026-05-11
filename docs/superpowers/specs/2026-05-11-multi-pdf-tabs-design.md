# 멀티 PDF 탭 기능 설계

**날짜**: 2026-05-11  
**상태**: 승인됨

---

## 개요

현재 `MainWindow`는 PDF를 하나만 열 수 있다. 이 설계는 탭 방식으로 여러 PDF를 동시에 열고, 각 탭이 완전히 독립된 상태(페이지, 줌, 어노테이션 모드, 검색 등)를 유지하도록 확장한다.

---

## 컴포넌트 구조

### 새 파일

**`app/ui/pdf_tab_page.py`** — 탭 하나의 완전한 뷰어 유닛

- 소유: `PdfDocument`, `PdfViewer`, `RenderEngine` 각 인스턴스
- 상태: 현재 페이지, 줌, 스크롤 위치, 검색 쿼리, 어노테이션 모드
- `cleanup()` 메서드: doc 닫기, 리소스 해제

**`app/ui/pdf_tab_widget.py`** — `QTabWidget` 확장, 탭 생명주기 관리

- `open_pdf(path)`: 새 `PdfTabPage` 생성 후 탭 추가
- `active_tab() -> PdfTabPage | None`: 현재 활성 탭 반환
- `recent_closed_stack`: `(경로, 페이지번호, 줌)` 튜플 스택 (최대 10개)
- 시그널 `active_tab_changed(PdfTabPage)`: 탭 전환/열기/닫기 시 발생

**`app/ui/detached_window.py`** — 탭 분리 시 띄우는 독립 창

- `PdfTabPage`를 받아 독립 `QMainWindow`로 감싼다
- 툴바·메뉴: 열기·저장·어노테이션·줌 서브셋
- 닫을 때 "탭으로 되돌리기 / 그냥 닫기" 다이얼로그 표시

### 수정 파일

**`app/ui/main_window.py`**

- `self._doc`, `self._viewer` 제거
- `self._tab_widget: PdfTabWidget` 추가 (중앙 위젯)
- 모든 액션(열기·저장·어노테이션 등)을 `self._tab_widget.active_tab()`에 위임
- `active_tab_changed` 구독: 사이드바 패널 재연결, 타이틀바 업데이트

---

## 탭 생명주기 & 상태 흐름

### 탭 열기
```
사용자 파일 선택 (Ctrl+O)
  → PdfTabWidget.open_pdf(path)
  → PdfTabPage 생성 (doc + viewer 초기화)
  → addTab() → active_tab_changed 시그널 발생
  → MainWindow: 타이틀바 업데이트, 사이드바 재연결
```

### 탭 닫기
```
X 버튼 / Ctrl+W
  → 미저장 변경 있으면 저장 여부 확인 다이얼로그
  → (경로, 현재페이지, 줌) → recent_closed_stack에 push
  → PdfTabPage.cleanup() → doc.close()
  → 다음 탭 활성화 (없으면 빈 화면)
```

### 탭 복제
```
우클릭 메뉴 → "복제" / Ctrl+Shift+D
  → 현재 탭의 경로로 새 PdfTabPage 생성
  → 같은 페이지·줌으로 초기 상태 설정
```

### 탭 분리 (detach)
```
탭 우클릭 → "새 창으로 열기" / Ctrl+Shift+N / 창 밖으로 드래그
  → PdfTabPage를 탭에서 제거
  → DetachedWindow(PdfTabPage) 생성 후 show()
  → DetachedWindow 닫힐 때 → 탭으로 재삽입 or 완전 닫기 선택
```

### 최근 탭 재열기
```
Ctrl+Shift+T
  → recent_closed_stack.pop()
  → open_pdf(경로) → 해당 페이지·줌으로 복원
```

### 사이드바 연동 (탭 전환 시)
```
active_tab_changed(new_tab)
  → PagePanel.set_document(new_tab.doc)
  → BookmarkPanel.set_document(new_tab.doc)
  → SearchBar: new_tab의 검색 상태 복원
  → 타이틀바: new_tab의 파일명으로 업데이트
```

---

## 단축키

| 동작 | 단축키 |
|------|--------|
| 파일 열기 (새 탭) | `Ctrl+O` |
| 탭 닫기 | `Ctrl+W` |
| 최근 탭 재열기 | `Ctrl+Shift+T` |
| 다음 탭 | `Ctrl+Tab` |
| 이전 탭 | `Ctrl+Shift+Tab` |
| 탭 N번으로 이동 | `Ctrl+1` ~ `Ctrl+9` |
| 탭 복제 | `Ctrl+Shift+D` |
| 새 창으로 분리 | `Ctrl+Shift+N` |

---

## 탭바 우클릭 컨텍스트 메뉴

- 닫기
- 다른 탭 모두 닫기
- 오른쪽 탭 모두 닫기
- 복제
- 새 창으로 열기
- 파일 경로 복사

---

## 탭 제목 표시 규칙

- 파일명만 표시 (예: `report.pdf`)
- 미저장 변경 있으면 앞에 `●` 표시 (예: `● report.pdf`)
- 툴팁: 전체 경로

---

## 구현 범위 밖 (이번 설계에서 제외)

- 분할 화면 (Side-by-side view)
- 탭 간 어노테이션 복사/붙여넣기
- 탭 세션 저장/복원 (앱 재시작 시)
