#!/usr/bin/env bash
# Review strip: 5 frames side by side (0.8 s, 25 %, 50 %, 75 %, last second) at phone size.
#   tools/frames.sh <video.mp4> [out.png]
set -euo pipefail
in="$1"; out="${2:-${in%.*}-frames.png}"
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
i=0
for t in 0.8 $(awk -v d="$d" 'BEGIN{print d*.25, d*.5, d*.75, d-1}'); do
  ffmpeg -v error -y -ss "$t" -i "$in" -frames:v 1 -vf "scale=-2:640" "$tmp/$i.png"; i=$((i+1))
done
ffmpeg -v error -y -i "$tmp/0.png" -i "$tmp/1.png" -i "$tmp/2.png" -i "$tmp/3.png" -i "$tmp/4.png" -filter_complex hstack=5 "$out"
echo "$out"
