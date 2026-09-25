#!/usr/bin/env bash
# Keep the Prime Command Center board running on the Mac Mini, including after reboots.
#
#   ./command-center/install-mac.sh            # install and start (launchd agent)
#   ./command-center/install-mac.sh uninstall  # stop and remove
#
# The board listens on 127.0.0.1 only. To open it from your phone, use Tailscale:
#   tailscale serve --bg 8787     (then open https://<mac-mini-name>.<tailnet>.ts.net/?t=TOKEN)
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
label="com.prime.command-center"
plist="$HOME/Library/LaunchAgents/$label.plist"
port="${PRIME_CC_PORT:-8787}"
logdir="${PRIME_CC_HOME:-$HOME/Cowork/olympus/command-center}/logs"

if [[ "${1:-}" == "uninstall" ]]; then
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  rm -f "$plist"
  echo "removed $label"
  exit 0
fi

command -v claude >/dev/null || { echo "claude not found on PATH. Install Claude Code first." >&2; exit 1; }
py="$(command -v python3)"
mkdir -p "$logdir" "$(dirname "$plist")"

# launchd starts with a bare PATH, so hand it the PATH that can find claude and python3.
cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key>
  <array><string>$py</string><string>$here/cc.py</string><string>serve</string><string>--port</string><string>$port</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>$PATH</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$logdir/board.out.log</string>
  <key>StandardErrorPath</key><string>$logdir/board.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$plist"
sleep 1
echo "board running: http://127.0.0.1:$port/?t=$("$py" "$here/cc.py" token)"
echo "phone access:  tailscale serve --bg $port   (see command-center/README.md)"
