# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 빌드 명세.

빌드:
    uv run pyinstaller pdf_editor.spec --clean

결과물: dist/PDF편집툴-v{version}.exe  (단일 실행 파일, 콘솔 창 없음)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(SPEC)))
from app.__version__ import __version__

_exe_name = f"PDF편집툴-v{__version__}"

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'fitz',
        'pymupdf',
        'PIL._imaging',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', '_tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=_exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # GUI 앱 — 콘솔 창 숨김
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,           # TODO: assets/icons/app.ico 추가 후 여기 경로 지정
)
