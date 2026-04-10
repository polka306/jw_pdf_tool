"""Windows 파일 확장자 연결 — .pdf 기본 뷰어 등록."""

from __future__ import annotations

import sys

PROG_ID = "jw_pdf.pdf"
APP_NAME = "jw_pdf"


def register_pdf_association(
    *,
    exe_path: str,
    dry_run: bool = False,
) -> dict:
    """PDF 파일 연결 등록. dry_run=True이면 레지스트리 변경 없이 결과만 반환."""
    command = f'"{exe_path}" "%1"'
    icon = f"{exe_path},0"

    result = {
        "progid": PROG_ID,
        "command": command,
        "icon": icon,
        "app_name": APP_NAME,
    }

    if dry_run or sys.platform != "win32":
        return result

    import winreg

    # ProgID 등록
    key_path = rf"Software\Classes\{PROG_ID}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, APP_NAME)

    # shell\open\command
    cmd_path = rf"Software\Classes\{PROG_ID}\shell\open\command"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_path) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

    # DefaultIcon
    icon_path = rf"Software\Classes\{PROG_ID}\DefaultIcon"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, icon_path) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, icon)

    # .pdf OpenWithProgids
    owp_path = r"Software\Classes\.pdf\OpenWithProgids"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, owp_path) as key:
        winreg.SetValueEx(key, PROG_ID, 0, winreg.REG_NONE, b"")

    return result


def unregister_pdf_association(*, dry_run: bool = False) -> dict:
    """PDF 파일 연결 해제."""
    if dry_run or sys.platform != "win32":
        return {"status": "ok"}

    import winreg

    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                         rf"Software\Classes\{PROG_ID}\shell\open\command")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                         rf"Software\Classes\{PROG_ID}\DefaultIcon")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                         rf"Software\Classes\{PROG_ID}\shell\open")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                         rf"Software\Classes\{PROG_ID}\shell")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                         rf"Software\Classes\{PROG_ID}")
    except OSError:
        pass

    return {"status": "ok"}
