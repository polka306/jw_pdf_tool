@echo off
echo ============================================================
echo  PDF 편집 툴 exe 빌드
echo ============================================================
echo.

cd /d "%~dp0.."

echo [1/2] PyInstaller 실행...
uv run pyinstaller pdf_editor.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [오류] 빌드 실패. 위 로그를 확인하세요.
    pause
    exit /b 1
)

echo.
echo [2/2] 완료!
echo.
echo 결과물: dist\PDF편집툴.exe
echo.
pause
