"""TC-165: 도움말 > 정보 다이얼로그."""

from __future__ import annotations


class TestTC165:
    """TC-165: 도움말 > 정보 다이얼로그."""

    def test_about_dialog_shows_app_info(self, main_window, monkeypatch):
        win = main_window
        called_with = {}

        def fake_about(parent, title, text):
            called_with["title"] = title
            called_with["text"] = text

        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.about",
            fake_about,
        )

        win._show_about()

        assert "title" in called_with, "_show_about()이 QMessageBox.about을 호출하지 않았음"
        assert "PDF 편집 툴" in called_with["title"]
        assert "v" in called_with["text"]  # 버전 정보 포함
        assert "PyQt6" in called_with["text"]
