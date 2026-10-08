#!/usr/bin/env bash
# Packs the finished videos into a PRIVATE release of this repo so you can download them from github.com.
cd "$(dirname "$0")"; tag="videos-$(date +%Y%m%d-%H%M)"
gh release create "$tag" out/*.mp4 --title "OpenPrep videos $tag" --notes "Rendered in Codespaces" --latest=false
echo "Open the repo > Releases to download."
