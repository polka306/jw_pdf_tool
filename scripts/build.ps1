# PDF Editor - PyInstaller build script
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

Write-Host '============================================================'
Write-Host '  PDF Editor - exe build'
Write-Host '============================================================'
Write-Host ''

Set-Location $root

$pyinstaller = Join-Path $root '.venv\Scripts\pyinstaller.exe'
if (-not (Test-Path $pyinstaller)) {
    $pyinstaller = 'pyinstaller'
}

Write-Host '[1/2] Running PyInstaller...'
& $pyinstaller (Join-Path $root 'pdf_editor.spec') --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Error '[ERROR] Build failed.'
    exit 1
}

Write-Host ''
Write-Host '[2/2] Build complete!'
$exePath = Join-Path $root 'dist' | Join-Path -ChildPath 'PDF편집툴.exe'
Write-Host "Output: $exePath"
