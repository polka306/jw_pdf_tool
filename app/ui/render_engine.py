"""비동기 렌더링 엔진 — QThreadPool 기반 PDF 페이지 렌더링."""

from __future__ import annotations

import fitz
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot, QMutex

from app.utils.cache import RenderCache


class _RenderTask(QRunnable):
    """단일 페이지 렌더 태스크."""

    class Signals(QObject):
        finished = pyqtSignal(int, float, bytes)  # page, zoom, png_data

    def __init__(self, pdf_path: str, page_idx: int, zoom: float) -> None:
        super().__init__()
        self.signals = self.Signals()
        self._path = pdf_path
        self._page = page_idx
        self._zoom = zoom
        self._cancelled = False
        self.setAutoDelete(True)

    def cancel(self) -> None:
        self._cancelled = True

    @pyqtSlot()
    def run(self) -> None:
        if self._cancelled:
            return
        try:
            doc = fitz.open(self._path)
            if self._page >= len(doc):
                doc.close()
                return
            page = doc[self._page]
            mat = fitz.Matrix(self._zoom, self._zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            data = pix.tobytes("png")
            doc.close()

            if not self._cancelled:
                self.signals.finished.emit(self._page, self._zoom, data)
        except Exception:
            pass  # 오류 시 무시 (취소됨 등)


class RenderEngine(QObject):
    """비동기 PDF 렌더링 엔진.

    Signals
    -------
    render_complete(page_idx, zoom, png_data)
        렌더링 완료 시 발생.
    """

    render_complete = pyqtSignal(int, float, bytes)

    PREFETCH_RANGE = 3  # 현재 페이지 ±3

    def __init__(self, max_cache: int = 20, max_threads: int = 4) -> None:
        super().__init__()
        self._cache = RenderCache(max_items=max_cache)
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(max_threads)
        self._pdf_path: str | None = None
        self._page_count: int = 0
        self._pending: set[tuple[int, float]] = set()  # 중복 방지
        self._mutex = QMutex()
        self._shutdown = False
        self._generations: dict[int, int] = {}

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def load_document(self, pdf_path: str) -> None:
        """PDF 파일을 로드. 기존 캐시는 초기화."""
        self._cache.clear()
        self._pending.clear()
        self._pdf_path = pdf_path
        doc = fitz.open(pdf_path)
        self._page_count = len(doc)
        self._generations = {i: 0 for i in range(self._page_count)}
        doc.close()
        self._shutdown = False

    def request_render(
        self,
        page_idx: int,
        zoom: float,
        *,
        prefetch: bool = False,
        priority: bool = False,
    ) -> None:
        """페이지 렌더 요청. 캐시 히트 시 즉시 시그널, 미스 시 큐잉."""
        if self._shutdown or self._pdf_path is None:
            return

        gen = self._generations.get(page_idx, 0)
        key = (page_idx, zoom, gen)

        # 캐시 히트 → 즉시 반환
        cached = self._cache.get(key)
        if cached is not None:
            self.render_complete.emit(page_idx, zoom, cached)
            return

        # 중복 요청 방지
        dedup_key = (page_idx, zoom)
        self._mutex.lock()
        if dedup_key in self._pending:
            self._mutex.unlock()
            if prefetch:
                self._schedule_prefetch(page_idx, zoom)
            return
        self._pending.add(dedup_key)
        self._mutex.unlock()

        # 태스크 생성 및 제출
        task = _RenderTask(self._pdf_path, page_idx, zoom)
        task.signals.finished.connect(self._on_task_done)

        if priority:
            # Qt에서는 QThreadPool에 우선순위를 직접 설정할 수 없지만
            # 먼저 제출하면 먼저 처리됨 (FIFO)
            self._pool.start(task, priority=1)
        else:
            self._pool.start(task, priority=0)

        # 프리페치
        if prefetch:
            self._schedule_prefetch(page_idx, zoom)

    def get_cached(self, page_idx: int, zoom: float) -> bytes | None:
        """캐시에서 직접 조회."""
        gen = self._generations.get(page_idx, 0)
        return self._cache.get((page_idx, zoom, gen))

    def shutdown(self) -> None:
        """엔진 종료. 대기 중인 태스크 취소."""
        self._shutdown = True
        self._pool.clear()
        self._pool.waitForDone(1000)
        self._cache.clear()
        self._pending.clear()

    def set_generation(self, page_idx: int, gen: int) -> None:
        """페이지 세대 카운터 갱신."""
        self._generations[page_idx] = gen

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------

    @pyqtSlot(int, float, bytes)
    def _on_task_done(self, page_idx: int, zoom: float, data: bytes) -> None:
        """태스크 완료 콜백."""
        if self._shutdown:
            return

        gen = self._generations.get(page_idx, 0)
        key = (page_idx, zoom, gen)
        self._cache.put(key, data)
        self._cache.set_current_page(page_idx)

        self._mutex.lock()
        self._pending.discard((page_idx, zoom))
        self._mutex.unlock()

        self.render_complete.emit(page_idx, zoom, data)

    def _schedule_prefetch(self, center: int, zoom: float) -> None:
        """현재 페이지 주변 ±PREFETCH_RANGE 프리페치."""
        for offset in range(1, self.PREFETCH_RANGE + 1):
            for idx in (center - offset, center + offset):
                if 0 <= idx < self._page_count:
                    gen = self._generations.get(idx, 0)
                    if self._cache.get((idx, zoom, gen)) is None:
                        dedup = (idx, zoom)
                        self._mutex.lock()
                        if dedup not in self._pending:
                            self._pending.add(dedup)
                            self._mutex.unlock()
                            task = _RenderTask(self._pdf_path, idx, zoom)
                            task.signals.finished.connect(self._on_task_done)
                            self._pool.start(task, priority=0)
                        else:
                            self._mutex.unlock()
