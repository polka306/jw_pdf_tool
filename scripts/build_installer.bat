@echo off
REM ============================================================
REM  jw_pdf — 설치 마법사 빌드 자동화
REM ============================================================
REM
REM 1. exe 빌드 (PyInstaller)
REM 2. 설치 마법사 빌드 (Inno Setup)
REM
REM 사전 요구사항:
REM   - .venv 가상환경 (uv sync)
REM   - Inno Setup 6 (winget install JRSoftware.InnoSetup)

setlocal
SET ROOT=%~dp0..

echo ============================================================
echo  [1/2] PyInstaller — exe 빌드
echo ============================================================

if exist "%ROOT%\.venv\Scripts\pyinstaller.exe" (
    "%ROOT%\.venv\Scripts\pyinstaller.exe" "%ROOT%\jw_pdf.spec" --clean --noconfirm --distpath "%ROOT%\dist" --workpath "%ROOT%\build"
) else (
    pyinstaller "%ROOT%\jw_pdf.spec" --clean --noconfirm
)

if errorlevel 1 (
    echo [ERROR] PyInstaller 빌드 실패
    exit /b 1
)

echo.
echo ============================================================
echo  [2/2] Inno Setup — 설치 마법사 빌드
echo ============================================================

REM ISCC.exe 위치 탐지
SET ISCC=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" SET ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" SET ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" SET ISCC=C:\Program Files\Inno Setup 6\ISCC.exe

if "%ISCC%"=="" (
    echo [ERROR] Inno Setup 6이 설치되어 있지 않습니다.
    echo         winget install JRSoftware.InnoSetup
    exit /b 1
)

"%ISCC%" "%ROOT%\installer\setup.iss"

if errorlevel 1 (
    echo [ERROR] Inno Setup 빌드 실패
    exit /b 1
)

echo.
echo ============================================================
echo  빌드 완료!
echo ============================================================
echo  - exe:        %ROOT%\dist\jw_pdf-v2.0.0.exe
echo  - 설치 파일:  %ROOT%\dist\jw_pdf-v2.0.0-Setup.exe
echo ============================================================

endlocal
