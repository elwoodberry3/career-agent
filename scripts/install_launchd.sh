#!/usr/bin/env bash
# Install Zoe as a per-user launchd agent.  (Milestone 10)
set -euo pipefail

LABEL="com.elwood.zoelancaster"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$REPO_DIR/launchd/$LABEL.plist.template"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

[[ -x "$REPO_DIR/.venv/bin/python" ]] || { echo "No .venv found. Run: python3 -m venv .venv && pip install -r requirements.txt"; exit 1; }
[[ -f "$REPO_DIR/.env" ]] || { echo "No .env found. Copy .env.example to .env first."; exit 1; }

mkdir -p "$REPO_DIR/logs" "$HOME/Library/LaunchAgents"
sed "s|__REPO_DIR__|$REPO_DIR|g" "$TEMPLATE" > "$TARGET"
plutil -lint "$TARGET"

# Replace any existing copy, then load.
launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$TARGET"

echo "Installed $LABEL"
echo "Status:  launchctl print $DOMAIN/$LABEL | head -30"
echo "Logs:    tail -f $REPO_DIR/logs/zoe.log"
