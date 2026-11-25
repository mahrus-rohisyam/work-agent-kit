#!/usr/bin/env bash
# Lint and render every spec in a brief folder.
#   tools/render.sh <brand> <campaign> [spec-name...]
# Spec file names choose the composition: vertical*.json, landscape*.json,
# square*.json, showcase-vertical*.json, showcase-landscape*.json, tour*.json (video) and post*.json, og*.json, cover*.json (stills).
# Output: brands/<brand>/out/<campaign>/<spec-name>.{mp4,png}, plus a poster .jpg per video.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
brand="$1"; campaign="$2"; shift 2
dir="$ROOT/brands/$brand/briefs/$campaign"
out="$ROOT/brands/$brand/out/$campaign"
mkdir -p "$out"
specs=()
if [ $# -gt 0 ]; then for n in "$@"; do specs+=("$dir/$n.json"); done
else for f in "$dir"/*.json; do specs+=("$f"); done; fi

PY="${PYTHON:-}"; if [ -z "$PY" ]; then if python3 -c "" 2>/dev/null; then PY=python3; else PY="uv run --no-project python"; fi; fi
$PY "$ROOT/tools/slop_check.py" --brand "$brand" "${specs[@]}"

cd "$ROOT/video"
node scripts/sync-brands.mjs
for f in "${specs[@]}"; do
  name="$(basename "$f" .json)"
  comp="${name%%[-_.]*}"
  case "$name" in showcase-vertical*|showcase-landscape*) comp="${name%%_*}"; comp="${comp%%.*}";; esac
  case "$comp" in
    showcase-vertical|showcase-landscape|\
    tour|vertical|landscape|square)
      npx remotion render src/index.tsx "$comp" "$out/$name.mp4" --props="$f" --concurrency="${RENDER_CONCURRENCY:-2}" --log=error
      ffmpeg -v error -y -ss 1.2 -i "$out/$name.mp4" -frames:v 1 -q:v 3 "$out/$name.jpg"
      echo "$out/$name.mp4" ;;
    post|og|cover)
      npx remotion still src/index.tsx "$comp" "$out/$name.png" --props="$f" --log=error
      echo "$out/$name.png" ;;
    *) echo "skip $f: name must start with a composition name (see the top of this file)" >&2 ;;
  esac
done
