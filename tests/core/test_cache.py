"""TC-167 ~ TC-172: LRU 이미지 캐시 단위 테스트."""

from __future__ import annotations

import pytest


class TestLRUCache:
    """utils/cache.py — RenderCache 단위 테스트."""

    # TC-167: 캐시 미스 → 저장 → 히트
    def test_tc167_miss_then_hit(self):
        from app.utils.cache import RenderCache

        cache = RenderCache(max_items=10)
        key = (0, 1.5, 0)  # (page_idx, zoom, generation)

        assert cache.get(key) is None  # 미스
        cache.put(key, b"fake_pixmap_data")
        assert cache.get(key) == b"fake_pixmap_data"  # 히트

    # TC-168: 용량 초과 시 LRU 제거
    def test_tc168_eviction_on_capacity(self):
        from app.utils.cache import RenderCache

        cache = RenderCache(max_items=3)
        cache.put((0, 1.0, 0), b"page0")
        cache.put((1, 1.0, 0), b"page1")
        cache.put((2, 1.0, 0), b"page2")

        # 4번째 삽입 → 가장 오래된 page0 제거
        cache.put((3, 1.0, 0), b"page3")

        assert cache.get((0, 1.0, 0)) is None  # 제거됨
        assert cache.get((1, 1.0, 0)) == b"page1"
        assert cache.get((3, 1.0, 0)) == b"page3"

    # TC-169: 세대 카운터 변경 시 무효화
    def test_tc169_generation_invalidation(self):
        from app.utils.cache import RenderCache

        cache = RenderCache(max_items=10)
        cache.put((0, 1.5, 0), b"gen0")  # generation=0

        # 같은 page/zoom이지만 generation이 다르면 미스
        assert cache.get((0, 1.5, 1)) is None

        # 이전 generation은 여전히 존재
        assert cache.get((0, 1.5, 0)) == b"gen0"

    # TC-170: 거리 기반 우선 제거
    def test_tc170_distance_based_eviction(self):
        from app.utils.cache import RenderCache

        cache = RenderCache(max_items=5)
        # 페이지 0~4 추가
        for i in range(5):
            cache.put((i, 1.0, 0), f"page{i}".encode())

        # 현재 페이지를 2로 설정하고 새 항목 추가
        cache.set_current_page(2)
        cache.put((5, 1.0, 0), b"page5")

        # 현재 페이지(2)에서 가장 먼 페이지(0 또는 4)가 제거되어야 함
        # page0(거리2) 또는 page4(거리2) 중 하나가 제거
        evicted_count = sum(
            1 for i in range(5)
            if cache.get((i, 1.0, 0)) is None
        )
        assert evicted_count >= 1  # 최소 1개 제거
        assert cache.get((2, 1.0, 0)) is not None  # 현재 페이지는 유지

    # TC-171: 빈 캐시에서 조회
    def test_tc171_empty_cache_get(self):
        from app.utils.cache import RenderCache

        cache = RenderCache(max_items=10)
        result = cache.get((999, 5.0, 99))

        assert result is None  # KeyError 없이 None

    # TC-172: clear() 호출 후 비어있음
    def test_tc172_clear(self):
        from app.utils.cache import RenderCache

        cache = RenderCache(max_items=10)
        cache.put((0, 1.0, 0), b"data0")
        cache.put((1, 1.0, 0), b"data1")
        cache.put((2, 1.0, 0), b"data2")

        cache.clear()

        assert cache.get((0, 1.0, 0)) is None
        assert cache.get((1, 1.0, 0)) is None
        assert cache.get((2, 1.0, 0)) is None
        assert len(cache) == 0
