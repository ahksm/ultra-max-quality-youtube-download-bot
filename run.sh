#!/usr/bin/env bash
# One-click launcher for macOS / Linux.
# Creates a local virtual environment, installs dependencies, and runs the
# downloader. Any arguments you pass are forwarded to the script, e.g.
#     ./run.sh https://youtu.be/dQw4w9WgXcQ
set -e

cd "$(dirname "$0")"

# Pick a Python 3 interpreter.
PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python

# Create the venv on first run.
if [ ! -d ".venv" ]; then
  echo "Setting up (first run only)..."
  "$PY" -m venv .venv
fi

# Activate it.
# shellcheck disable=SC1091
source .venv/bin/activate

# Install / update dependencies quietly.
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Run the downloader, passing along any arguments.
python youtube_download.py "$@"
