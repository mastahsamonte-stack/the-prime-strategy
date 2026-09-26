#!/usr/bin/env bash
# Make Phil's Claude account skills usable by Claude Code jobs on the Mac.
#
# The Claude desktop app keeps a local copy of the account's skills under
#   ~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/<org>/<account>/skills
# but Claude Code only loads skills from ~/.claude/skills. This copies them across.
#
#   ./scripts/sync-skills.sh            # preview only: what would be added, refreshed, skipped
#   ./scripts/sync-skills.sh --apply    # add new skills and refresh ones this script manages
#   ./scripts/sync-skills.sh --refresh  # refresh managed skills only; never adds new ones
#
# Rules: a skill is written only if the destination folder is missing or carries the
# .prime-synced marker this script leaves. Anything else in ~/.claude/skills is never
# touched. --refresh (what the command center runs before each job) cannot install a
# skill Phil hasn't approved with --apply.
#
# Env overrides: PRIME_SKILLS_SRC (source skills folder), CLAUDE_CONFIG_DIR (default ~/.claude)
set -euo pipefail
mode="${1:-preview}"
case "$mode" in preview|--apply|--refresh) ;; *) echo "usage: $0 [--apply|--refresh]" >&2; exit 2 ;; esac
dest="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
marker=".prime-synced"

src="${PRIME_SKILLS_SRC:-}"
if [[ -z "$src" ]]; then
  # Several account folders can exist; the account library is the one with the most skills.
  best=0
  for d in "$HOME/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin"/*/*/skills; do
    [[ -d "$d" ]] || continue
    n="$(find "$d" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
    if (( n > best )); then best=$n; src="$d"; fi
  done
fi
[[ -n "$src" && -d "$src" ]] || { echo "sync-skills: no account skills folder found; set PRIME_SKILLS_SRC" >&2; exit 1; }

mkdir -p "$dest"
# Replace a managed skill wholesale so files deleted upstream disappear here too.
copy_skill() {
  local from="$1" to="$2" tmp="$2.prime-tmp"
  rm -rf "$tmp" && cp -R "$from" "$tmp" && touch "$tmp/$marker" && rm -rf "$to" && mv "$tmp" "$to" \
    || { echo "sync-skills: failed to copy $(basename "$to")" >&2; return 1; }
}
added=(); refreshed=(); skipped=()
for s in "$src"/*/; do
  name="$(basename "$s")"
  [[ -f "$s/SKILL.md" ]] || continue
  target="$dest/$name"
  if [[ -e "$target" && ! -f "$target/$marker" ]]; then
    skipped+=("$name"); continue
  fi
  if [[ -e "$target" ]]; then
    [[ "$mode" == preview ]] || copy_skill "$s" "$target"
    refreshed+=("$name")
  elif [[ "$mode" != --refresh ]]; then
    [[ "$mode" == preview ]] || copy_skill "$s" "$target"
    added+=("$name")
  fi
done

verb=$([[ "$mode" == preview ]] && echo "would" || echo "did")
[[ "$mode" == --refresh ]] || echo "source: $src"
[[ "$mode" == --refresh ]] || echo "$verb add ${#added[@]}: ${added[*]:-none}"
echo "$verb refresh ${#refreshed[@]} managed skills"
(( ${#skipped[@]} == 0 )) || echo "skipped ${#skipped[@]} (already in $dest, not managed here): ${skipped[*]}"
[[ "$mode" == preview ]] && echo "Nothing changed. Run with --apply to copy." || true
