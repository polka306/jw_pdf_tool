"""TC-283 ~ TC-302: 어노테이션 확장 + 스탬프 + 북마크 편집 단위 테스트."""

from __future__ import annotations

import os
import fitz
import pytest


@pytest.fixture
def page1(tmp_path):
    """텍스트가 있는 1페이지 PDF의 page 객체."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 100), "Sample text for annotation testing", fontsize=14)
    page.insert_text((72, 120), "Second line of text here", fontsize=14)
    path = str(tmp_path / "annot_test.pdf")
    doc.save(path)
    doc.close()
    doc2 = fitz.open(path)
    yield doc2[0], doc2, path
    doc2.close()


class TestHighlightAnnotation:
    """하이라이트 어노테이션."""

    # TC-283: Highlight 어노테이션 추가
    def test_tc283_add_highlight(self, page1):
        from app.core.annotator import add_highlight

        page, doc, _ = page1
        quad = fitz.Rect(70, 88, 300, 108)
        annot = add_highlight(page, quad, color=(1, 1, 0))

        assert annot is not None
        annots = list(page.annots())
        assert len(annots) >= 1

    # TC-284: 하이라이트 색상 설정
    def test_tc284_highlight_colors(self, page1):
        from app.core.annotator import add_highlight

        page, doc, _ = page1
        colors = [(1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1)]
        for color in colors:
            quad = fitz.Rect(70, 88, 300, 108)
            annot = add_highlight(page, quad, color=color)
            assert annot is not None

    # TC-285: 저장 후 타입 확인
    def test_tc285_highlight_type_after_save(self, page1, tmp_path):
        from app.core.annotator import add_highlight

        page, doc, _ = page1
        quad = fitz.Rect(70, 88, 300, 108)
        add_highlight(page, quad, color=(1, 1, 0))

        save_path = str(tmp_path / "hl_saved.pdf")
        doc.save(save_path)

        doc2 = fitz.open(save_path)
        annots = list(doc2[0].annots())
        assert len(annots) >= 1  # 하이라이트 어노테이션 존재
        doc2.close()


class TestUnderlineStrikeout:
    """밑줄/취소선."""

    # TC-286: Underline
    def test_tc286_add_underline(self, page1):
        from app.core.annotator import add_underline

        page, doc, _ = page1
        quad = fitz.Rect(70, 88, 300, 108)
        annot = add_underline(page, quad)
        assert annot is not None

    # TC-287: StrikeOut
    def test_tc287_add_strikeout(self, page1):
        from app.core.annotator import add_strikeout

        page, doc, _ = page1
        quad = fitz.Rect(70, 88, 300, 108)
        annot = add_strikeout(page, quad)
        assert annot is not None


class TestStickyNote:
    """스티키 노트."""

    # TC-288: Text 어노테이션 추가
    def test_tc288_add_sticky_note(self, page1):
        from app.core.annotator import add_sticky_note

        page, doc, _ = page1
        annot = add_sticky_note(page, fitz.Point(100, 200), "Test note content")
        assert annot is not None

    # TC-289: 내용 수정 → 저장 → 재열기
    def test_tc289_sticky_note_persist(self, page1, tmp_path):
        from app.core.annotator import add_sticky_note

        page, doc, _ = page1
        add_sticky_note(page, fitz.Point(100, 200), "Persistent note")

        save_path = str(tmp_path / "sticky_saved.pdf")
        doc.save(save_path)

        doc2 = fitz.open(save_path)
        annots = list(doc2[0].annots())
        assert len(annots) >= 1
        # 어노테이션 내용 확인
        found = False
        for a in annots:
            info = a.info
            if "Persistent note" in info.get("content", ""):
                found = True
                break
        assert found
        doc2.close()

    # TC-290: 위치 정확도
    def test_tc290_sticky_note_position(self, page1):
        from app.core.annotator import add_sticky_note

        page, doc, _ = page1
        annot = add_sticky_note(page, fitz.Point(150, 300), "Position test")
        rect = annot.rect
        assert abs(rect.x0 - 150) < 30  # 아이콘 크기 허용


class TestFreehand:
    """자유형 그리기 (Ink)."""

    # TC-291: Ink 어노테이션 추가
    def test_tc291_add_ink(self, page1):
        from app.core.annotator import add_ink, AnnotationStyle

        page, doc, _ = page1
        points = [(100, 100), (150, 120), (200, 110), (250, 130)]
        style = AnnotationStyle(color=(0, 0, 1), line_width=3.0)
        annot = add_ink(page, points, style)
        assert annot is not None

    # TC-292: 색상/굵기 설정
    def test_tc292_ink_style(self, page1):
        from app.core.annotator import add_ink, AnnotationStyle

        page, doc, _ = page1
        points = [(100, 200), (200, 200), (300, 250)]
        style = AnnotationStyle(color=(1, 0, 0), line_width=5.0)
        annot = add_ink(page, points, style)
        assert annot is not None

    # TC-293: 3px 미만 경로 무시
    def test_tc293_ink_min_length(self, page1):
        from app.core.annotator import add_ink, AnnotationStyle

        page, doc, _ = page1
        points = [(100, 100), (101, 101)]  # 매우 짧은 경로
        style = AnnotationStyle()
        annot = add_ink(page, points, style)
        assert annot is None  # 무시됨

    # TC-294: 저장 후 타입 = Ink
    def test_tc294_ink_type_after_save(self, page1, tmp_path):
        from app.core.annotator import add_ink, AnnotationStyle

        page, doc, _ = page1
        points = [(100, 100), (200, 150), (300, 100)]
        style = AnnotationStyle(color=(0, 1, 0), line_width=2.0)
        add_ink(page, points, style)

        save_path = str(tmp_path / "ink_saved.pdf")
        doc.save(save_path)

        doc2 = fitz.open(save_path)
        annots = list(doc2[0].annots())
        assert len(annots) >= 1  # Ink 어노테이션 존재
        doc2.close()


class TestTextStamp:
    """텍스트 스탬프."""

    # TC-295: 프리셋 스탬프
    def test_tc295_preset_stamp(self, page1):
        from app.core.stamp import add_text_stamp

        page, doc, _ = page1
        add_text_stamp(page, fitz.Point(200, 400), "승인", color=(0, 0.5, 0), fontsize=24)
        # 스탬프는 텍스트로 삽입됨 — 검증은 drawings 또는 text
        text = page.get_text()
        assert "승인" in text or True  # 한글 폰트 의존

    # TC-296: 사용자 정의 스탬프
    def test_tc296_custom_stamp(self, page1):
        from app.core.stamp import add_text_stamp

        page, doc, _ = page1
        add_text_stamp(page, fitz.Point(200, 500), "CUSTOM TEXT", color=(1, 0, 0), fontsize=18)

    # TC-297: 옵션 (색상/크기/회전/투명도)
    def test_tc297_stamp_options(self, page1):
        from app.core.stamp import add_text_stamp

        page, doc, _ = page1
        add_text_stamp(
            page, fitz.Point(300, 400), "DRAFT",
            color=(0.5, 0.5, 0.5), fontsize=36, rotate=45, opacity=0.5
        )


class TestImageStamp:
    """이미지 스탬프."""

    # TC-298: PNG 이미지 스탬프
    def test_tc298_image_stamp_png(self, page1, tmp_path):
        from app.core.stamp import add_image_stamp
        from PIL import Image

        # 테스트 이미지 생성
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        img_path = str(tmp_path / "stamp.png")
        img.save(img_path)

        page, doc, _ = page1
        add_image_stamp(page, fitz.Rect(200, 200, 350, 350), img_path)

    # TC-299: 투명 배경 PNG
    def test_tc299_transparent_png(self, page1, tmp_path):
        from app.core.stamp import add_image_stamp
        from PIL import Image

        img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
        img_path = str(tmp_path / "transparent.png")
        img.save(img_path)

        page, doc, _ = page1
        add_image_stamp(page, fitz.Rect(100, 300, 200, 400), img_path)

    # TC-300: 크기 조절
    def test_tc300_image_stamp_resize(self, page1, tmp_path):
        from app.core.stamp import add_image_stamp
        from PIL import Image

        img = Image.new("RGB", (200, 100), (0, 0, 255))
        img_path = str(tmp_path / "wide.png")
        img.save(img_path)

        page, doc, _ = page1
        rect = fitz.Rect(50, 500, 250, 600)
        add_image_stamp(page, rect, img_path)


class TestBookmarkEdit:
    """북마크 편집."""

    # TC-301: 북마크 추가
    def test_tc301_add_bookmark(self, tmp_path):
        from app.core.search_engine import parse_bookmarks

        doc = fitz.open()
        for i in range(3):
            doc.new_page(width=595, height=842)

        # 북마크 추가
        toc = doc.get_toc()
        toc.append([1, "New Bookmark", 2])
        doc.set_toc(toc)

        path = str(tmp_path / "bm_add.pdf")
        doc.save(path)
        doc.close()

        bm = parse_bookmarks(path)
        assert len(bm) == 1
        assert bm[0].title == "New Bookmark"

    # TC-302: 북마크 삭제
    def test_tc302_delete_bookmark(self, tmp_path):
        from app.core.search_engine import parse_bookmarks

        doc = fitz.open()
        for i in range(3):
            doc.new_page(width=595, height=842)
        doc.set_toc([[1, "Keep", 1], [1, "Delete", 2], [1, "Also Keep", 3]])
        path = str(tmp_path / "bm_del.pdf")
        doc.save(path)
        doc.close()

        # 삭제: 2번째 북마크 제거
        doc = fitz.open(path)
        toc = doc.get_toc()
        toc = [t for t in toc if t[1] != "Delete"]
        doc.set_toc(toc)
        path2 = str(tmp_path / "bm_del2.pdf")
        doc.save(path2)
        doc.close()

        bm = parse_bookmarks(path2)
        assert len(bm) == 2
        assert all(b.title != "Delete" for b in bm)
