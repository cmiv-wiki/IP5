#!/usr/bin/env bash
# Build the standalone app with PyInstaller.
#   macOS:   dist/IP5 Recorder.app
#   Linux:   dist/IP5 Recorder/IP5 Recorder
#   Windows: dist/IP5 Recorder/IP5 Recorder.exe  (run from Git Bash, or: uv run pyinstaller --noconfirm --clean ip5.spec)
set -euo pipefail
cd "$(dirname "$0")"
if command -v uv >/dev/null; then
    uv run pyinstaller --noconfirm --clean ip5.spec
else
    pyinstaller --noconfirm --clean ip5.spec
fi
