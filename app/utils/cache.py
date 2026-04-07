"""LRU 이미지 캐시 — 렌더링 결과를 (page, zoom, generation) 키로 캐싱."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any


class RenderCache:
    """줌 레벨×페이지×세대 키 기반 LRU 캐시.

    Parameters
    ----------
    max_items : int
        최대 캐시 항목 수 (기본 20).
    """

    def __init__(self, max_items: int = 20) -> None:
        self._max = max_items
        self._data: OrderedDict[tuple, Any] = OrderedDict()
        self._current_page: int = -1  # 미설정 시 모든 페이지 동일 거리 → LRU 폴백

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def get(self, key: tuple) -> Any | None:
        """캐시 조회. 히트 시 LRU 순서 갱신, 미스 시 None."""
        if key in self._data:
            self._data.move_to_end(key)
            return self._data[key]
        return None

    def put(self, key: tuple, value: Any) -> None:
        """캐시에 저장. 용량 초과 시 거리 기반 LRU 제거."""
        if key in self._data:
            self._data.move_to_end(key)
            self._data[key] = value
            return

        # 용량 초과 시 먼저 제거 후 삽입 (새 항목 보호)
        if len(self._data) >= self._max:
            self._evict()

        self._data[key] = value

    def clear(self) -> None:
        """전체 캐시 초기화."""
        self._data.clear()

    def set_current_page(self, page: int) -> None:
        """현재 페이지 설정 — 거리 기반 제거 시 사용."""
        self._current_page = page

    def __len__(self) -> int:
        return len(self._data)

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------

    def _evict(self) -> None:
        """항목 제거 정책.

        current_page가 설정되어 있으면 → 거리 기반 (먼 것 우선, 같으면 LRU).
        current_page가 미설정(-1)이면 → 순수 LRU (가장 오래된 것).
        """
        if not self._data:
            return

        if self._current_page < 0:
            # 순수 LRU: OrderedDict의 첫 항목(가장 오래된)
            self._data.popitem(last=False)
            return

        worst_key = None
        worst_dist = -1

        for k in self._data:
            page_idx = k[0] if isinstance(k[0], int) else 0
            dist = abs(page_idx - self._current_page)
            if dist > worst_dist:
                worst_dist = dist
                worst_key = k

        if worst_key is not None:
            del self._data[worst_key]
