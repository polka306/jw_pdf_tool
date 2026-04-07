"""PDF 문서 로드/저장/렌더링 래퍼."""

from __future__ import annotations

import fitz  # PyMuPDF


class PdfDocument:
    """PyMuPDF fitz.Document를 감싸는 래퍼 클래스."""

    def __init__(self) -> None:
        self._doc: fitz.Document | None = None
        self._path: str | None = None
        self._generations: dict[int, int] = {}  # 페이지별 세대 카운터

    # ------------------------------------------------------------------
    # 열기 / 닫기
    # ------------------------------------------------------------------

    def open(self, path: str) -> None:
        """PDF 파일을 엽니다."""
        if self._doc:
            self._doc.close()
        self._doc = fitz.open(path)
        self._path = path
        self._generations = {i: 0 for i in range(len(self._doc))}

    def close(self) -> None:
        """열린 문서를 닫습니다."""
        if self._doc:
            self._doc.close()
            self._doc = None
            self._path = None

    # ------------------------------------------------------------------
    # 프로퍼티
    # ------------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self._doc is not None

    @property
    def page_count(self) -> int:
        return len(self._doc) if self._doc else 0

    @property
    def path(self) -> str | None:
        return self._path

    @property
    def raw(self) -> fitz.Document | None:
        """내부 fitz.Document 객체 직접 접근 (고급 작업용)."""
        return self._doc

    # ------------------------------------------------------------------
    # 렌더링
    # ------------------------------------------------------------------

    def render_page(self, page_idx: int, zoom: float = 1.5) -> bytes:
        """지정 페이지를 PNG bytes로 렌더링합니다."""
        self._require_open()
        page = self._doc[page_idx]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")

    def render_page_thumbnail(self, page_idx: int, thumb_width: int = 140) -> bytes:
        """썸네일 크기의 PNG bytes를 반환합니다."""
        self._require_open()
        page = self._doc[page_idx]
        zoom = thumb_width / page.rect.width
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")

    def get_page_size(self, page_idx: int) -> tuple[float, float]:
        """페이지의 (width, height) — 포인트 단위."""
        self._require_open()
        page = self._doc[page_idx]
        return page.rect.width, page.rect.height

    # ------------------------------------------------------------------
    # 저장
    # ------------------------------------------------------------------

    def save(self, path: str | None = None) -> None:
        """저장합니다. path 미지정 시 원본 파일을 덮어씁니다.

        같은 파일 덮어쓰기: incremental save (변경분만 기록, 빠름).
        다른 경로(Save As): garbage=4 + deflate 전체 저장 (느리지만 최적화됨).
        """
        self._require_open()
        save_path = path or self._path
        if save_path is None:
            raise ValueError("저장 경로가 지정되지 않았습니다.")
        if path is None:
            # 같은 파일 덮어쓰기 → incremental (빠름)
            try:
                self._doc.save(
                    save_path,
                    incremental=True,
                    encryption=fitz.PDF_ENCRYPT_KEEP,
                )
                return
            except Exception:
                pass  # incremental 불가 시 전체 저장으로 폴백
        self._doc.save(save_path, garbage=4, deflate=True)
        if path:
            self._path = path

    def save_as_temp(self, temp_path: str) -> None:
        """임시 경로에 저장합니다 (내부 경로 변경 없음)."""
        self._require_open()
        self._doc.save(temp_path, garbage=4, deflate=True)

    # ------------------------------------------------------------------
    # 세대 카운터
    # ------------------------------------------------------------------

    def get_generation(self, page_idx: int) -> int:
        """페이지의 현재 세대 카운터 값."""
        return self._generations.get(page_idx, 0)

    def increment_generation(self, page_idx: int) -> None:
        """페이지 세대 카운터를 1 증가."""
        self._generations[page_idx] = self._generations.get(page_idx, 0) + 1

    def reindex_generations_after_delete(self, deleted_indices: list[int]) -> None:
        """페이지 삭제 후 세대 카운터 인덱스를 재매핑."""
        deleted_set = set(deleted_indices)
        old_gens = self._generations.copy()
        self._generations.clear()

        new_idx = 0
        for old_idx in sorted(old_gens.keys()):
            if old_idx not in deleted_set:
                self._generations[new_idx] = old_gens[old_idx]
                new_idx += 1

    # ------------------------------------------------------------------
    # 내부 유틸
    # ------------------------------------------------------------------

    def _require_open(self) -> None:
        if not self._doc:
            raise RuntimeError("열린 PDF 문서가 없습니다.")
