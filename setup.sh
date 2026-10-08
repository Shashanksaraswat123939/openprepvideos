#!/usr/bin/env bash
# One-time setup inside the Codespace (runs automatically after the container is created).
set -e
sudo apt-get update -y
sudo apt-get install -y espeak-ng fonts-dejavu-core ffmpeg
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m playwright install --with-deps chromium
mkdir -p scripts out cache logs
echo "Setup finished. Next: bash run_all.sh"
