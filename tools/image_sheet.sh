#!/usr/bin/env bash
# Put many images or icons on one contact sheet, so Claude reads one picture instead of many.
#   tools/image_sheet.sh <dir> [out.png] [tile px, default 240]
# Writes <out.png> plus <out>.txt listing the files in sheet order (left to right, top to bottom).
# Takes png, jpg, jpeg, webp, gif (first frame). Max 48 per sheet; more make <out>-2.png, -3.png ...
# SVG files are not drawn (they are text, cheaper to read directly); they are listed in <out>.txt.
set -euo pipefail

dir="${1:?usage: tools/image_sheet.sh <dir> [out.png] [tile px]}"
root="$(cd "$(dirname "$0")/.." && pwd)"
out="${2:-$root/references/distilled/sheets/$(basename "$dir").png}"
px="${3:-240}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  for d in "$HOME"/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin; do
    [ -x "$d/ffmpeg.exe" ] && PATH="$d:$PATH"
  done
fi
command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }

mkdir -p "$(dirname "$out")"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
find "$dir" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \
  -o -iname '*.webp' -o -iname '*.gif' \) | sort > "$tmp/list"
find "$dir" -maxdepth 1 -type f -iname '*.svg' | sort > "$tmp/svg"
if [ -s "$tmp/svg" ]; then
  { echo "# SVG (read as text, not on the sheet)"; sed "s|^$root/||" "$tmp/svg"; } > "${out%.png}-svg.txt"
  echo "${out%.png}-svg.txt ($(wc -l < "$tmp/svg") svg files)"
fi
[ -s "$tmp/list" ] || { [ -s "$tmp/svg" ] && exit 0; echo "no images in $dir" >&2; exit 1; }

page=1; n=0
flush() {
  [ "$n" -gt 0 ] || return 0
  local o="$out"; [ "$page" -gt 1 ] && o="${out%.png}-$page.png"
  local cols=$(( n < 8 ? n : 8 )); local rows=$(( (n + cols - 1) / cols ))
  ffmpeg -hide_banner -nostdin -v error -y -framerate 1 -i "$tmp/p${page}_%03d.png" \
    -vf "tile=${cols}x${rows}:padding=6:color=white" -frames:v 1 "$o"
  mv "$tmp/names" "${o%.png}.txt"; echo "$o ($n files)"
  page=$((page+1)); n=0
}
while read -r f; do
  # Checkerboard-free light grey background so white and transparent icons stay visible.
  if ffmpeg -hide_banner -nostdin -v error -y -i "$f" -frames:v 1 -filter_complex \
      "color=c=0xEEEEEE:s=${px}x${px}[bg];[0]scale=${px}:${px}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2:format=auto,format=rgb24" \
      "$(printf "$tmp/p${page}_%03d.png" $n)" 2>/dev/null; then
    echo "$((n+1)). ${f#$root/}" >> "$tmp/names"; n=$((n+1))
  else
    echo "skipped (cannot decode): $f" >&2
  fi
  [ "$n" -eq 48 ] && flush
done < "$tmp/list"
flush
