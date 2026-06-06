@echo off
REM One-click launcher for Windows.
REM Creates a local virtual environment, installs dependencies, and runs the
REM downloader. Double-click this file, or run it from a terminal with a URL:
REM     run.bat https://youtu.be/dQw4w9WgXcQ

cd /d "%~dp0"

REM Create the venv on first run.
if not exist ".venv" (
    echo Setting up ^(first run only^)...
    python -m venv .venv
)

REM Activate it.
call .venv\Scripts\activate.bat

REM Install / update dependencies quietly.
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

REM Run the downloader, passing along any arguments.
python youtube_download.py %*

echo.
pause
