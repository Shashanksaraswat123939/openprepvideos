#!/usr/bin/env bash
cd "$(dirname "$0")"; echo "scripts: $(ls scripts/*.json 2>/dev/null | wc -l) / 87   videos done: $(ls out/*.mp4 2>/dev/null | wc -l) / 87"; tail -n 3 logs/worker*.log 2>/dev/null; ls scripts/*.errors.txt 2>/dev/null
