"""버전 비교 유틸."""

from __future__ import annotations


def compare_versions(current: str, latest: str) -> int:
    """버전 문자열 비교.

    Returns
    -------
    int
        -1: current < latest (업데이트 필요)
         0: 동일
         1: current > latest
    """
    def _parse(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.strip().split("."))

    c = _parse(current)
    l = _parse(latest)

    if c < l:
        return -1
    elif c > l:
        return 1
    return 0
