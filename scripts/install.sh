#!/usr/bin/env bash
# Copy the curated agents into your global Claude Code agents folder.
#   ./scripts/install.sh                      # install every agent
#   ./scripts/install.sh finance sales        # install only these divisions (filename prefix)
#   DRY_RUN=1 ./scripts/install.sh            # show what would be copied
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dest="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agents"
mkdir -p "$dest"
count=0
for f in "$here"/.claude/agents/*.md; do
  base="$(basename "$f")"
  if [[ $# -gt 0 ]]; then
    keep=0
    for d in "$@"; do [[ "$base" == "$d"-* ]] && keep=1; done
    [[ $keep -eq 1 ]] || continue
  fi
  if [[ -n "${DRY_RUN:-}" ]]; then echo "would copy $base"; else cp "$f" "$dest/$base"; fi
  count=$((count+1))
done
echo "$count agent(s) -> $dest"
