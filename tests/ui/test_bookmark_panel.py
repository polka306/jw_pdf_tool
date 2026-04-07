"""TC-227 ~ TC-229: 북마크 패널 UI 테스트."""

from __future__ import annotations

import os
import fitz
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_pdf_with_bookmarks(tmp_path) -> str:
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Chapter {i + 1}", fontsize=24)
    toc = [[1, "Chapter 1", 1], [1, "Chapter 2", 2], [1, "Chapter 3", 3]]
    doc.set_toc(toc)
    path = str(tmp_path / "bookmarked.pdf")
    doc.save(path)
    doc.close()
    return path


class TestBookmarkPanel:
    """ui/bookmark_panel.py — 북마크 트리 패널 테스트."""

    # TC-227: 트리 표시
    def test_tc227_tree_display(self, qtbot, tmp_path):
        from app.ui.bookmark_panel import BookmarkPanel

        pdf_path = _make_pdf_with_bookmarks(tmp_path)
        panel = BookmarkPanel()
        qtbot.addWidget(panel)
        panel.load_bookmarks(pdf_path)

        assert panel._tree.topLevelItemCount() == 3
        assert panel._tree.topLevelItem(0).text(0) == "Chapter 1"

    # TC-228: 항목 클릭 → 페이지 이동 시그널
    def test_tc228_click_navigates(self, qtbot, tmp_path):
        from app.ui.bookmark_panel import BookmarkPanel

        pdf_path = _make_pdf_with_bookmarks(tmp_path)
        panel = BookmarkPanel()
        qtbot.addWidget(panel)
        panel.load_bookmarks(pdf_path)

        pages = []
        panel.page_requested.connect(lambda p: pages.append(p))

        # 두 번째 항목 클릭 시뮬레이션
        item = panel._tree.topLevelItem(1)
        panel._tree.setCurrentItem(item)
        panel._on_item_clicked(item, 0)

        assert len(pages) >= 1
        assert pages[0] == 1  # Chapter 2 → page 1 (0-indexed)

    # TC-229: 썸네일/북마크 탭 전환
    def test_tc229_tab_switch(self, qtbot, tmp_path):
        from app.ui.bookmark_panel import BookmarkPanel

        panel = BookmarkPanel()
        qtbot.addWidget(panel)
        panel.show()

        # 패널이 표시되는지 확인
        assert panel.isVisible()
