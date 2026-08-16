@echo off
setlocal
title sNote Uninstaller
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\uninstall_windows.ps1"
if errorlevel 1 (
    echo.
    echo sNote removal failed. Please copy this screen and report it.
    pause
    exit /b 1
)

timeout /t 2 /nobreak >nul
exit /b 0
