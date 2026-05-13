"""앱 버전 정보.

버전 체계:
  v0.x.y  — Phase x 완료 상태 (개발 중)
  v1.0.0  — Phase 5 완료 = 첫 안정 릴리즈

Phase 이력:
  v0.1.0  Phase 1: PDF 열기/렌더링/기본 윈도우
  v0.2.0  Phase 2: 페이지 편집 (순서변경/삭제/추출/삽입)
  v0.3.0  Phase 3: 어노테이션 (텍스트/사각형/타원/선)
  v0.4.0  Phase 4: 문서 변환 (이미지/Office → PDF)
  v0.4.1  중간 버그픽스 + 성능 개선 + 테스트 보강
  v1.0.0  Phase 5: Undo/Redo, 단축키, exe 패키징 ✅
  v2.0.0  전체 재설계: 비동기 렌더, 검색, 북마크, 병합/분할, 암호화, OCR, 워터마크 등
  v2.1.0  멀티 PDF 탭 기능 (PdfTabWidget, DetachedWindow)
"""

__version__ = "2.1.0"
