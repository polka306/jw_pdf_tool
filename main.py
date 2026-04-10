"""PDF 편집 툴 — 앱 진입점."""

import sys

from PyQt6.QtWidgets import QApplication

from app.__version__ import __version__
from app.core.cli import parse_cli_args
from app.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("jw_pdf")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("personal")

    # 단일 인스턴스 확인
    try:
        from app.services.single_instance import SingleInstanceManager
        instance_mgr = SingleInstanceManager()
        if not instance_mgr.try_lock():
            # 이미 실행 중 → 파일 경로 전달 후 종료
            args = parse_cli_args(sys.argv)
            if args.file_path:
                instance_mgr.send_message(args.file_path)
            sys.exit(0)
    except Exception:
        pass  # 단일 인스턴스 실패 시 무시

    # 테마 적용
    try:
        from app.services.settings import AppSettings
        from app.services.theme import get_stylesheet
        settings = AppSettings()
        theme = settings.get("theme", "dark")
        app.setStyleSheet(get_stylesheet(theme))
    except Exception:
        pass

    window = MainWindow()
    window.show()

    # 명령줄 인자로 파일 열기
    args = parse_cli_args(sys.argv)
    if args.file_path:
        window.handle_drop_file(args.file_path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
