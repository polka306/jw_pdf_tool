"""테마 스타일시트."""

from __future__ import annotations

_DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
}
QMenuBar {
    background-color: #2d2d2d;
    color: #d4d4d4;
}
QMenuBar::item:selected {
    background-color: #0e5a8a;
}
QMenu {
    background-color: #2d2d2d;
    color: #d4d4d4;
}
QMenu::item:selected {
    background-color: #0e5a8a;
}
QToolBar {
    background-color: #2d2d2d;
    border: none;
}
QStatusBar {
    background-color: #2d2d2d;
    color: #d4d4d4;
}
QListWidget {
    background-color: #252526;
    color: #d4d4d4;
}
QListWidget::item:selected {
    background-color: #0e5a8a;
}
QTreeWidget {
    background-color: #252526;
    color: #d4d4d4;
}
QTreeWidget::item:selected {
    background-color: #0e5a8a;
}
QPushButton {
    background-color: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #555;
    padding: 4px 12px;
}
QPushButton:hover {
    background-color: #4a4a4a;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #555;
}
"""

_LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #f5f5f5;
    color: #1e1e1e;
}
QMenuBar {
    background-color: #e8e8e8;
    color: #1e1e1e;
}
QMenuBar::item:selected {
    background-color: #cce4f7;
}
QMenu {
    background-color: #ffffff;
    color: #1e1e1e;
}
QMenu::item:selected {
    background-color: #cce4f7;
}
QToolBar {
    background-color: #e8e8e8;
    border: none;
}
QStatusBar {
    background-color: #e8e8e8;
    color: #1e1e1e;
}
QListWidget {
    background-color: #ffffff;
    color: #1e1e1e;
}
QListWidget::item:selected {
    background-color: #cce4f7;
}
QTreeWidget {
    background-color: #ffffff;
    color: #1e1e1e;
}
QPushButton {
    background-color: #e0e0e0;
    color: #1e1e1e;
    border: 1px solid #ccc;
    padding: 4px 12px;
}
QPushButton:hover {
    background-color: #d0d0d0;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #ffffff;
    color: #1e1e1e;
    border: 1px solid #ccc;
}
"""


def get_stylesheet(theme: str = "dark") -> str:
    """테마 이름에 해당하는 스타일시트 반환."""
    if theme == "light":
        return _LIGHT_THEME
    return _DARK_THEME
