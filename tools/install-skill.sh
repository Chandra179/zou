#!/usr/bin/env bash
# Install the business-rules Claude skill for the current user by symlinking it
# from this repo, so edits here apply everywhere. Usage: tools/install-skill.sh
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dest="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$dest"
ln -sfn "$repo/.claude/skills/business-rules" "$dest/business-rules"
echo "Installed: $dest/business-rules -> $repo/.claude/skills/business-rules"
