"""Undo/Redo 커맨드 패턴 구현.

Command 추상 기반 클래스와 CommandManager, 그리고
PDF 편집 작업에 대응하는 구체 커맨드 클래스들을 제공합니다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

import fitz  # PyMuPDF

MAX_HISTORY = 50  # 최대 undo 깊이


# ── 추상 기반 ─────────────────────────────────────────────────────────────────

class Command(ABC):
    """편집 작업의 실행/취소 인터페이스."""

    @property
    @abstractmethod
    def description(self) -> str:
        """작업 설명 (상태바/메뉴 표시용)."""

    @abstractmethod
    def execute(self) -> None:
        """작업을 실행합니다."""

    @abstractmethod
    def undo(self) -> None:
        """작업을 취소(역방향 실행)합니다."""


# ── 관리자 ─────────────────────────────────────────────────────────────────────

class CommandManager:
    """Undo/Redo 스택을 관리합니다."""

    def __init__(self) -> None:
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []

    def execute(self, cmd: Command) -> None:
        """커맨드를 실행하고 undo 스택에 추가합니다."""
        cmd.execute()
        self._undo_stack.append(cmd)
        if len(self._undo_stack) > MAX_HISTORY:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> str | None:
        """가장 최근 작업을 취소합니다. 취소된 작업의 설명을 반환 (없으면 None)."""
        if not self._undo_stack:
            return None
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        return cmd.description

    def redo(self) -> str | None:
        """취소한 작업을 다시 실행합니다. 재실행된 작업의 설명을 반환 (없으면 None)."""
        if not self._redo_stack:
            return None
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        return cmd.description

    def clear(self) -> None:
        """스택을 모두 비웁니다 (새 파일 열기 시 호출)."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    @property
    def undo_description(self) -> str | None:
        return self._undo_stack[-1].description if self._undo_stack else None

    @property
    def redo_description(self) -> str | None:
        return self._redo_stack[-1].description if self._redo_stack else None


# ── 구체 커맨드 ────────────────────────────────────────────────────────────────

class MovePageCommand(Command):
    """페이지 순서 이동."""

    def __init__(self, doc: fitz.Document, from_idx: int, to_idx: int) -> None:
        self._doc = doc
        self._from = from_idx
        self._to = to_idx

    @property
    def description(self) -> str:
        return f"페이지 이동: {self._from + 1} → {self._to + 1}"

    def execute(self) -> None:
        if self._from != self._to:
            self._doc.move_page(self._from, self._to)

    def undo(self) -> None:
        if self._from == self._to:
            return
        # fitz.move_page(pno, to) 는 pno를 to 앞에 삽입한다.
        # from < to 이면 실제 결과 위치는 to-1 (제거 후 인덱스 이동).
        # from > to 이면 실제 결과 위치는 to.
        if self._from < self._to:
            self._doc.move_page(self._to - 1, self._from)
        else:
            self._doc.move_page(self._to, self._from + 1)


class DeletePagesCommand(Command):
    """페이지 삭제 — Undo 시 원래 위치에 복원합니다."""

    def __init__(self, doc: fitz.Document, indices: list[int]) -> None:
        self._doc = doc
        self._indices = sorted(set(indices))
        # 삭제 전 각 페이지를 1-page PDF bytes로 저장
        self._snapshots: list[bytes] = [
            _capture_page(doc, idx) for idx in self._indices
        ]

    @property
    def description(self) -> str:
        return f"{len(self._indices)}개 페이지 삭제"

    def execute(self) -> None:
        for idx in reversed(self._indices):
            self._doc.delete_page(idx)

    def undo(self) -> None:
        # 삭제된 페이지들을 원래 위치에 순서대로 삽입 (replace 아님 — 빈 자리에 추가)
        for idx, snap in zip(self._indices, self._snapshots):
            _insert_page(self._doc, idx, snap)


class InsertPagesCommand(Command):
    """외부 PDF 페이지를 현재 문서에 삽입."""

    def __init__(
        self,
        doc: fitz.Document,
        source_path: str,
        source_indices: list[int],
        insert_before: int,
    ) -> None:
        self._doc = doc
        self._source_path = source_path
        self._source_indices = sorted(set(source_indices))
        self._insert_before = insert_before
        self._count = len(self._source_indices)

    @property
    def description(self) -> str:
        return f"{self._count}개 페이지 삽입"

    def execute(self) -> None:
        from app.core.page_editor import insert_pages_from_file
        insert_pages_from_file(
            self._doc, self._source_path, self._source_indices, self._insert_before
        )

    def undo(self) -> None:
        for i in range(self._count - 1, -1, -1):
            self._doc.delete_page(self._insert_before + i)


class AddAnnotationCommand(Command):
    """어노테이션 추가 — Undo 시 해당 페이지를 추가 전 상태로 복원합니다."""

    def __init__(
        self,
        doc: fitz.Document,
        page_idx: int,
        annotate_fn: Callable[[], None],
        description: str = "어노테이션 추가",
    ) -> None:
        self._doc = doc
        self._page_idx = page_idx
        self._annotate_fn = annotate_fn
        self._desc = description
        # 어노테이션 적용 전 페이지 상태 보존
        self._before_snap = _capture_page(doc, page_idx)

    @property
    def description(self) -> str:
        return self._desc

    def execute(self) -> None:
        self._annotate_fn()

    def undo(self) -> None:
        _restore_page(self._doc, self._page_idx, self._before_snap)


# ── 내부 헬퍼 ──────────────────────────────────────────────────────────────────

def _capture_page(doc: fitz.Document, page_idx: int) -> bytes:
    """지정 페이지를 1-page PDF bytes로 캡처합니다."""
    tmp = fitz.open()
    tmp.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
    data = tmp.tobytes()
    tmp.close()
    return data


def _insert_page(doc: fitz.Document, page_idx: int, snap: bytes) -> None:
    """snap(1-page PDF bytes)을 doc의 page_idx 위치에 삽입합니다 (기존 페이지 제거 없음)."""
    tmp = fitz.open("pdf", snap)
    doc.insert_pdf(tmp, from_page=0, to_page=0, start_at=page_idx)
    tmp.close()


def _restore_page(doc: fitz.Document, page_idx: int, snap: bytes) -> None:
    """doc의 page_idx 페이지를 snap으로 교체합니다 (AddAnnotationCommand 복원용)."""
    tmp = fitz.open("pdf", snap)
    doc.delete_page(page_idx)
    doc.insert_pdf(tmp, from_page=0, to_page=0, start_at=page_idx)
    tmp.close()
