#!/bin/sh
# crate installer: curl -LsSf https://raw.githubusercontent.com/AUstnnnnnn/crate/main/install.sh | sh
set -e
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv tool install --force --python 3.12 https://github.com/AUstnnnnnn/crate/archive/refs/heads/main.zip
uv tool update-shell >/dev/null 2>&1 || true
if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then brew install ffmpeg
  elif command -v apt-get >/dev/null 2>&1; then sudo apt-get install -y ffmpeg
  else echo "crate needs ffmpeg: install it with your package manager"; fi
fi
echo "done. open a new terminal and run: crate"
