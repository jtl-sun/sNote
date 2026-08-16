@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
start "" pythonw -m snote %*
exit /b 0
