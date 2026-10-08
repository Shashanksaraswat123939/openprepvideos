#!/usr/bin/env bash
# Starts 3 parallel render workers (4-core Codespace). Safe to re-run: finished videos are skipped.
# The Codespace stops after 30 min with no keyboard/browser activity; set the idle timeout to 240 min in
# GitHub > Settings > Codespaces, and keep this tab open. If it stops, reopen it and run this script again.
cd "$(dirname "$0")"; export PYTHONUTF8=1 OPENPREP_TTS=kokoro; mkdir -p logs out cache
for i in 0 1 2; do nohup python worker.py --shard $i/3 > logs/shard$i.out 2>&1 & done
echo "Started 3 workers. Watch progress with:  bash status.sh"
