#!/usr/bin/env bash
# Light scheduled jobs for the marketing agent (run from cron on Linux).
#   tools/scheduled.sh radar     weekly: product changes -> content ideas (only if a repo changed)
#   tools/scheduled.sh refresh   monthly: channel / tactic / tool research -> playbook
#
# Light by design:
# - shell does the cheap checks (git, pnpm) first; Claude starts only when there is something new
# - Claude gets no Bash: only read/write tools (plus web for refresh), so nothing gets installed or rendered
# - nice/ionice idle priority, one job at a time, skipped when RAM is low or a render is running
# - hard timeout, logs kept to the last 10 per job
set -euo pipefail
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
job="${1:?usage: scheduled.sh radar|refresh}"
LOG_DIR="$ROOT/logs"; mkdir -p "$LOG_DIR"
log="$LOG_DIR/$job-$(date +%F).log"
exec 9>"$LOG_DIR/.lock"
flock -n 9 || { echo "$(date -Is) another job is running; skip" >>"$log"; exit 0; }
exec >>"$log" 2>&1
echo "== $(date -Is) $job"

avail_mb=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
if [ "$avail_mb" -lt 1200 ]; then echo "only ${avail_mb} MB free; skip"; exit 0; fi
if pgrep -f "remotion (render|still)" >/dev/null; then echo "render running; skip"; exit 0; fi

run_claude() { # $1 prompt, $2 allowed tools, $3 minutes, rest: extra claude args
  cd "$ROOT"
  local prompt="$1" tools="$2" mins="$3"; shift 3
  timeout "${mins}m" nice -n 19 ionice -c3 claude -p "$prompt" "$@" \
    --model sonnet --effort low --max-turns 30 \
    --permission-mode acceptEdits --allowedTools "$tools" \
    --disallowedTools "Bash,Agent,NotebookEdit" </dev/null
}

case "$job" in
radar)
  ctx=""; dirs=()
  for b in "$ROOT"/brands/*/; do
    slug=$(basename "$b"); [ "$slug" = _template ] && continue
    repo=$(sed -n 's/^product_repo: *//p' "$b/brand.md" | head -1)
    [ -d "$repo/.git" ] || continue
    last=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('last_commit') or '')" "$b/radar.json")
    head=$(git -C "$repo" rev-parse HEAD)
    if [ -n "$last" ] && [ "$last" = "$head" ]; then echo "$slug: no new commits"; continue; fi
    range=$([ -n "$last" ] && echo "$last..$head" || echo "--since=30.days $head")
    changes=$(git -C "$repo" log --oneline --no-merges $range -- docs CHANGELOG.md README.md | head -40)
    if [ -z "$changes" ]; then
      echo "$slug: commits but no doc changes; advance marker"
      python3 -c "import json,sys,datetime;p=sys.argv[1];d=json.load(open(p));d['last_commit']=sys.argv[2];d['last_checked']=str(datetime.date.today());json.dump(d,open(p,'w'),indent=2)" "$b/radar.json" "$head"
      continue
    fi
    media=$(git -C "$repo" diff --name-status ${last:-$(git -C "$repo" rev-list -1 --before=30.days HEAD)} "$head" -- docs/media '*.mp4' | head -20 || true)
    dirs+=(--add-dir "$repo")
    ctx+=$'\n\n'"### Brand: $slug (repo $repo, HEAD $head)"$'\nDoc commits:\n'"$changes"$'\nMedia changes:\n'"$media"
  done
  if [ -z "$ctx" ]; then echo "nothing new; Claude not started"; exit 0; fi
  run_claude "Follow .claude/skills/content-radar/SKILL.md for the brands below. The git data is already collected here, so do not run git; read the product repo's docs files directly when you need detail. Write ideas to each brand's ideas.md and set radar.json last_commit to the HEAD given and last_checked to today. Do not edit brand.md; put proposed message changes at the top of ideas.md under 'Proposed brand.md changes'.$ctx" \
    "Read,Glob,Grep,Edit(brands/**)" 15 "${dirs[@]}"
  ;;
refresh)
  outdated=$(cd "$ROOT/video" && timeout 120 nice -n 19 pnpm outdated 2>&1 | head -30 || true)
  run_claude "Follow .claude/skills/refresh/SKILL.md (all areas). pnpm outdated for video/ is below, so do not run it. Keep it short: at most 12 web searches. Edit only files in playbook/. Anything that would change rules, code or brand files goes under 'Proposed changes' in playbook/CHANGELOG.md.

pnpm outdated:
$outdated" \
    "Read,Glob,Grep,Edit(playbook/**),WebSearch,WebFetch" 25
  ;;
*) echo "unknown job $job"; exit 1 ;;
esac
echo "== done $(date -Is)"
ls -1t "$LOG_DIR"/"$job"-*.log | tail -n +11 | xargs -r rm -f
