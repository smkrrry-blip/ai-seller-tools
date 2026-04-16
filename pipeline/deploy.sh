#!/bin/bash
# deploy.sh — Generate pending articles and push both sites to GitHub Pages
# Usage: ./deploy.sh [--force]

set -e
FORCE=${1:-""}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EN_DIR="$HOME/affiliate-en"
JP_DIR="$HOME/affiliate-jp"

echo "=== Generating English articles ==="
python3 "$SCRIPT_DIR/batch_generate.py" --lang en $FORCE

echo ""
echo "=== Generating Japanese articles ==="
python3 "$SCRIPT_DIR/batch_generate.py" --lang jp $FORCE

echo ""
echo "=== Pushing English site ==="
cd "$EN_DIR"
git add -A
git diff --cached --quiet || git commit -m "chore: auto-deploy $(date '+%Y-%m-%d %H:%M')"
git push origin main

echo ""
echo "=== Pushing Japanese site ==="
cd "$JP_DIR"
git add -A
git diff --cached --quiet || git commit -m "chore: auto-deploy $(date '+%Y-%m-%d %H:%M')"
git push origin main

echo ""
echo "✓ Both sites deployed."
echo "  EN: https://smkrrry-blip.github.io/ai-seller-tools/"
echo "  JP: https://smkrrry-blip.github.io/ai-seller-jp/"
