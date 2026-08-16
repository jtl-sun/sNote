@echo off
setlocal
title sNote Easy Installer
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_windows.ps1"
if errorlevel 1 (
    echo.
    echo sNote installation failed. Please copy this screen and report it.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0scripts\close_calling_terminal.ps1"
exit /b 0
