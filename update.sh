#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Terra Balance — One-Command Update Script
#  Run this after downloading a new TerraBalance.html from Claude
#
#  Usage:  ./update.sh path/to/TerraBalance.html
#  Or:     ./update.sh   (looks in ~/Downloads automatically)
# ─────────────────────────────────────────────────────────────

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
DOWNLOADS=~/Downloads

# Find the source file
if [ -n "$1" ]; then
  SRC="$1"
elif ls "$DOWNLOADS"/terra_balance_globe.html 2>/dev/null | head -1 | grep -q html; then
  SRC="$DOWNLOADS/terra_balance_globe.html"
elif ls "$DOWNLOADS"/TerraBalance*.html 2>/dev/null | head -1 | grep -q html; then
  SRC=$(ls -t "$DOWNLOADS"/TerraBalance*.html | head -1)
else
  echo "❌  Could not find TerraBalance HTML in Downloads."
  echo "    Usage: ./update.sh /path/to/TerraBalance.html"
  exit 1
fi

echo "🌍  Terra Balance — Publishing update"
echo "    Source: $SRC"
echo "    Repo:   $REPO_DIR"
echo ""

# Copy into repo as index.html
cp "$SRC" "$REPO_DIR/index.html"
echo "✓  Copied to index.html"

# Git commit and push
cd "$REPO_DIR"
git add index.html
git commit -m "Update Terra Balance $(date '+%Y-%m-%d %H:%M')"
git push

echo ""
echo "✅  Done! Your live site will update in ~30 seconds."
echo "    https://honnikorn.github.io/terra-balance/"
