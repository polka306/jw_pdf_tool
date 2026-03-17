@echo off
echo ============================================================
echo  PDF Editor - exe build
echo ============================================================

SET ROOT=%~dp0..

echo [1/2] Running PyInstaller...

if exist "%ROOT%\.venv\Scripts\pyinstaller.exe" (
    "%ROOT%\.venv\Scripts\pyinstaller.exe" "%ROOT%\pdf_editor.spec" --clean --noconfirm --distpath "%ROOT%\dist" --workpath "%ROOT%\build"
) else (
    pyinstaller "%ROOT%\pdf_editor.spec" --clean --noconfirm
)

if errorlevel 1 (
    echo [ERROR] Build failed.
    exit /b 1
)

echo [2/2] Build complete!
echo Output folder: %ROOT%\dist\

