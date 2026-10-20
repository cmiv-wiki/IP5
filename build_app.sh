#!/usr/bin/env bash
# Build the standalone app with PyInstaller.
#   macOS:   dist/IP5 Recorder.app
#   Windows: dist/IP5 Recorder/IP5 Recorder.exe  (run from Git Bash, or: pyinstaller --noconfirm ip5.spec)
set -euo pipefail
cd "$(dirname "$0")"
pyinstaller --noconfirm --clean ip5.spec
