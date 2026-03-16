@echo off
chcp 65001 > nul
echo ============================================================
echo  PDF Editor - exe build
echo ============================================================
echo.

cd /d "%~dp0.."

echo [1/2] Running PyInstaller...

if exist ".venv\Scripts\pyinstaller.exe" (
    .venv\Scripts\pyinstaller.exe pdf_editor.spec --clean --noconfirm
) else (
    pyinstaller pdf_editor.spec --clean --noconfirm
)

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check the log above.
    pause
    exit /b 1
)

echo.
echo [2/2] Done!
echo.
echo Output: dist\PDF편집툴.exe
echo.
pause
