#!/usr/bin/env bash
# Put the curated roster on standby for Vader (the Hermes Agent orchestrator).
#
#   ./scripts/standby.sh            # both targets below
#   ./scripts/standby.sh claude     # only ~/.claude/agents  (global Claude Code subagents)
#   ./scripts/standby.sh hermes     # only ~/.hermes/plugins/agency-agents-router (+ enable in config.yaml)
#   ./scripts/standby.sh status     # report what is installed, change nothing
#
# Why both: when Vader launches a Claude Code job through the Claude subscription,
# Claude Code only loads subagents from ~/.claude/agents (global) or the job's own
# .claude/agents. Jobs rarely start inside this repo, so the global copy is what
# keeps the roster available. The Hermes plugin lets Vader itself search, load,
# and delegate to the same 71 specialists without preloading them as skills.
#
# Env overrides: CLAUDE_CONFIG_DIR (default ~/.claude), HERMES_HOME (default ~/.hermes)
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
claude_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agents"
hermes_home="${HERMES_HOME:-$HOME/.hermes}"
plugin_src="$here/integrations/hermes/agency-agents-router"
plugin_dest="$hermes_home/plugins/agency-agents-router"
config="$hermes_home/config.yaml"
mode="${1:-all}"

roster_count() { ls "$here"/.claude/agents/*.md 2>/dev/null | wc -l | tr -d ' '; }

install_claude() {
  mkdir -p "$claude_dir"
  local n=0
  for f in "$here"/.claude/agents/*.md; do cp "$f" "$claude_dir/$(basename "$f")"; n=$((n+1)); done
  echo "claude-code: $n agents -> $claude_dir"
}

enable_plugin_in_config() {
  mkdir -p "$hermes_home"
  [[ -f "$config" ]] && cp "$config" "$config.bak.prime-strategy.$$"
  python3 - "$config" agency-agents-router <<'PY'
from pathlib import Path
import sys
path, plugin = Path(sys.argv[1]), sys.argv[2]
lines = (path.read_text() if path.exists() else "").splitlines()

# Already enabled? Walk the plugins: block looking for "- <plugin>" under enabled:.
in_plugins = in_enabled = False
for line in lines:
    if line.startswith("plugins:"):
        in_plugins, in_enabled = True, False; continue
    if in_plugins and line and not line.startswith((" ", "\t")):
        in_plugins = in_enabled = False
    s = line.strip()
    if in_plugins and s == "enabled:":
        in_enabled = True; continue
    if in_plugins and s.startswith("enabled:") and "[]" in s:
        in_enabled = False; continue
    if in_enabled:
        if s.startswith("-") and s[1:].strip().strip("\"'") == plugin:
            print("hermes: plugin already enabled in", path); sys.exit(0)
        if line.startswith("  ") and s.endswith(":"):
            in_enabled = False

if not lines:
    lines = ["plugins:", "  enabled:", f"  - {plugin}"]
elif not any(l.startswith("plugins:") for l in lines):
    if lines[-1].strip(): lines.append("")
    lines += ["plugins:", "  enabled:", f"  - {plugin}"]
else:
    out, in_plugins, inserted, saw_enabled = [], False, False, False
    for line in lines:
        if line.startswith("plugins:"):
            in_plugins = True; out.append(line); continue
        if in_plugins and line and not line.startswith((" ", "\t")):
            if not saw_enabled and not inserted:
                out += ["  enabled:", f"  - {plugin}"]; inserted = True
            in_plugins = False; out.append(line); continue
        if in_plugins and line.strip().startswith("enabled:") and "[]" in line:
            saw_enabled = True; out += ["  enabled:", f"  - {plugin}"]; inserted = True; continue
        if in_plugins and line.strip() == "enabled:":
            saw_enabled = True; out.append(line); out.append(f"  - {plugin}"); inserted = True; continue
        out.append(line)
    if in_plugins and not saw_enabled and not inserted:
        out += ["  enabled:", f"  - {plugin}"]
    lines = out
path.write_text("\n".join(lines) + "\n")
print("hermes: enabled agency-agents-router in", path)
PY
}

install_hermes() {
  [[ -f "$plugin_src/plugin.yaml" && -f "$plugin_src/data/agents.json" ]] || {
    echo "hermes: plugin missing; run ./scripts/build-hermes.sh first" >&2; return 1; }
  [[ "$(basename "$plugin_dest")" == "agency-agents-router" ]] || { echo "refusing to touch $plugin_dest" >&2; return 1; }
  mkdir -p "$(dirname "$plugin_dest")"
  rm -rf "$plugin_dest"
  cp -R "$plugin_src" "$plugin_dest"
  local n; n="$(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$plugin_dest/data/agents.json")"
  echo "hermes: router plugin with $n agents -> $plugin_dest"
  enable_plugin_in_config
  echo "hermes: restart Vader (Hermes gateway/session) so the plugin tools load"
}

status() {
  local want; want="$(roster_count)"
  local have=0; [[ -d "$claude_dir" ]] && have="$(ls "$claude_dir"/*.md 2>/dev/null | wc -l | tr -d ' ')"
  local matched=0
  for f in "$here"/.claude/agents/*.md; do [[ -f "$claude_dir/$(basename "$f")" ]] && matched=$((matched+1)); done
  echo "roster in repo:        $want agents"
  echo "claude-code global:    $matched of $want present in $claude_dir ($have total files there)"
  if [[ -f "$plugin_dest/data/agents.json" ]]; then
    echo "hermes plugin:         installed at $plugin_dest ($(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$plugin_dest/data/agents.json") agents)"
  else
    echo "hermes plugin:         NOT installed ($plugin_dest)"
  fi
  if [[ -f "$config" ]] && grep -qE '^\s*-\s*["'"'"']?agency-agents-router' "$config"; then
    echo "hermes config:         agency-agents-router enabled in $config"
  else
    echo "hermes config:         agency-agents-router NOT enabled in $config"
  fi
}

case "$mode" in
  all)    install_claude; install_hermes ;;
  claude) install_claude ;;
  hermes) install_hermes ;;
  status) status ;;
  *) echo "usage: $0 [all|claude|hermes|status]" >&2; exit 2 ;;
esac
