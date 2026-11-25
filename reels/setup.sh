#!/usr/bin/env bash
# One-time setup on macOS / Linux. Needs Python 3.10+ and ffmpeg (macOS: brew install ffmpeg python).
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "Install ffmpeg first (macOS: brew install ffmpeg)"; exit 1; }
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
echo "Ready. Put files in reels/inbox/media and reels/inbox/music, then run: npm run reels"
