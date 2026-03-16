"""PDF 편집 툴 — 앱 진입점."""

import sys

from PyQt6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("PDF 편집 툴")
    app.setOrganizationName("personal")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
