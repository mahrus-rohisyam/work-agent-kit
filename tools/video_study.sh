#!/usr/bin/env bash
# Break a reference video into small files Claude can read cheaply, instead of watching it.
#   tools/video_study.sh <video> [outdir]
# Default outdir: references/distilled/videos/<video name>/
#
# Output:
#   meta.txt        duration, size, fps, loudness, shot count, average shot length
#   cuts.txt        timestamp of every cut (scene change)
#   hook.png        first 3 s, one frame every 0.5 s (the hook decides a short video)
#   shots.png       one frame per shot, in order (max 24, evenly picked when more)
#   timeline.png    12 frames evenly spread over the whole video
#   silence.txt     quiet parts of the audio (pauses, drops)
#   transcript.srt  speech, if a whisper model is in tools/whisper-models/
#   breakdown.md    notes skeleton; Claude fills it after reading the files above
#
# Needs ffmpeg/ffprobe (ffmpeg 8+ with the whisper filter for transcripts).
# Env: SCENE (cut threshold, default 0.3), WHISPER_MODEL, WHISPER_LANG (default auto).
set -euo pipefail

in="${1:?usage: tools/video_study.sh <video> [outdir]}"
root="$(cd "$(dirname "$0")/.." && pwd)"
name="$(basename "${in%.*}")"
out="${2:-$root/references/distilled/videos/$name}"
scene="${SCENE:-0.3}"

# Windows: winget installs ffmpeg outside Git Bash's PATH until the shell restarts.
if ! command -v ffmpeg >/dev/null 2>&1; then
  for d in "$HOME"/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin; do
    [ -x "$d/ffmpeg.exe" ] && PATH="$d:$PATH"
  done
fi
command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }

mkdir -p "$out"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
ff() { ffmpeg -hide_banner -nostdin -v error -y "$@"; }
probe() { ffprobe -v error "$@" "$in"; }

dur=$(probe -show_entries format=duration -of csv=p=0)
size=$(probe -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0)
fps=$(probe -select_streams v:0 -show_entries stream=avg_frame_rate -of csv=p=0)
has_audio=$(probe -select_streams a -show_entries stream=index -of csv=p=0 | head -1)
tile_h=$(awk -v s="$size" 'BEGIN{split(s,a,"x"); print (a[2]>a[1]) ? 320 : 180}')

# Cuts
ffmpeg -hide_banner -nostdin -i "$in" -an -vf "select='gt(scene,$scene)',showinfo" -f null - 2>&1 \
  | grep -o 'pts_time:[0-9.]*' | cut -d: -f2 > "$tmp/cuts"
{ echo "# cut times in seconds (scene threshold $scene)"; awk '{printf "%.2f\n",$1}' "$tmp/cuts"; } > "$out/cuts.txt"
shots=$(( $(wc -l < "$tmp/cuts") + 1 ))

frame() { ff -ss "$1" -i "$in" -frames:v 1 -vf "scale=-2:$tile_h" "$2"; }
sheet() { # sheet <prefix> <cols> <out.png>
  local n; n=$(ls "$tmp/$1"_*.png | wc -l)
  local cols=$(( n < $2 ? n : $2 )); local rows=$(( (n + cols - 1) / cols ))
  ff -framerate 1 -i "$tmp/$1_%03d.png" -vf "tile=${cols}x${rows}:padding=4:color=white" -frames:v 1 "$3"
}

# Hook: 0, 0.5 ... 2.5 s
i=0; for t in 0 0.5 1 1.5 2 2.5; do
  awk -v t="$t" -v d="$dur" 'BEGIN{exit !(t<d)}' && frame "$t" "$(printf "$tmp/hook_%03d.png" $i)" && i=$((i+1))
done
sheet hook 6 "$out/hook.png"

# Shots: a frame 0.3 s into each shot, max 24
{ echo 0; cat "$tmp/cuts"; } | awk -v n="$shots" -v d="$dur" '
  { t[NR]=$1 } END { step = (n>24) ? n/24 : 1
    for (k=1; k<=n && k<=24; k++) { j=int((k-1)*step)+1; x=t[j]+0.3; if (x>d-0.05) x=t[j]; print x } }' \
  > "$tmp/shot_times"
i=0; while read -r t; do frame "$t" "$(printf "$tmp/shot_%03d.png" $i)"; i=$((i+1)); done < "$tmp/shot_times"
sheet shot 6 "$out/shots.png"
{ echo "# shots.png order: shot -> frame time (s)"; awk '{printf "%d  %.2f\n",NR,$1}' "$tmp/shot_times"; } >> "$out/cuts.txt"

# Timeline: 12 evenly spaced frames
for i in $(seq 0 11); do
  frame "$(awk -v d="$dur" -v i="$i" 'BEGIN{printf "%.2f", d*(i+0.5)/12}')" "$(printf "$tmp/tl_%03d.png" $i)"
done
sheet tl 6 "$out/timeline.png"

# Audio
lufs="no audio"; : > "$out/silence.txt"
if [ -n "$has_audio" ]; then
  lufs=$(ffmpeg -hide_banner -nostdin -i "$in" -vn -af ebur128 -f null - 2>&1 | awk '/Integrated loudness/{f=1} f&&/I:/{print $2" LUFS"; exit}')
  ffmpeg -hide_banner -nostdin -i "$in" -vn -af silencedetect=n=-35dB:d=0.4 -f null - 2>&1 \
    | grep -o 'silence_\(start\|end\): [0-9.]*' > "$out/silence.txt" || true

  model="${WHISPER_MODEL:-}"
  [ -z "$model" ] && model=$(ls "$root"/tools/whisper-models/ggml-*.bin 2>/dev/null | head -1 || true)
  if [ -f "$model" ] && ffmpeg -hide_banner -filters 2>/dev/null | grep -q ' whisper '; then
    # The filter splits its options on ':', so pass paths relative to the work dir (no drive letter).
    cp "$model" "$tmp/model.bin" 2>/dev/null || true
    (cd "$tmp" && ffmpeg -hide_banner -nostdin -v error -y -i "$(cd "$(dirname "$in")" && pwd)/$(basename "$in")" -vn \
       -af "aresample=16000,whisper=model=model.bin:language=${WHISPER_LANG:-auto}:queue=10:destination=transcript.srt:format=srt" \
       -f null -) && mv "$tmp/transcript.srt" "$out/transcript.srt" || echo "transcript failed" >&2
  else
    echo "no whisper model/filter: skipped transcript" >&2
  fi
fi

avg=$(awk -v d="$dur" -v n="$shots" 'BEGIN{printf "%.2f", d/n}')
cat > "$out/meta.txt" <<EOF
file: $in
duration_s: $(printf "%.2f" "$dur")
size: $size
fps: $fps
loudness: $lufs
shots: $shots
avg_shot_s: $avg
EOF

[ -f "$out/breakdown.md" ] || cat > "$out/breakdown.md" <<'EOF'
# Breakdown: <video>

Source: `<raw path>` · Platform/format: <TikTok 9:16, ...> · Studied: dd-mm-yyyy

## Hook (0–3 s)
<what appears first, the first words/text, why it stops the scroll>

## Structure
| Time | Shot / visual | On-screen text | Voice / audio |
|---|---|---|---|

## Pacing & motion
<avg shot length, cut rhythm vs music, transitions, zooms, text animation>

## Visual style
<colors, fonts, captions style, framing, UI footage vs people>

## Audio
<music mood/tempo, voiceover tone, silence drops, loudness>

## CTA
<what, when, how>

## Worth copying / avoid
- Copy: <pattern>, because <reason>
- Avoid: <pattern>, because <reason>
EOF

echo "$out"
cat "$out/meta.txt"
