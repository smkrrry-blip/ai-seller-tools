#!/bin/bash
# auto_deploy.sh — launchd から呼ばれる自動デプロイスクリプト
set -e

# ─── APIキーを外部ファイルから読み込み（plist平文漏洩対策 2026-05-01）─────
if [[ -f "$HOME/.config/anthropic/env" ]]; then
  source "$HOME/.config/anthropic/env"
else
  echo "[FATAL] $HOME/.config/anthropic/env が見つかりません。APIキーが読み込めません。" >&2
  exit 1
fi
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "[FATAL] ANTHROPIC_API_KEY が未設定です。" >&2
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M')] 自動デプロイ開始"

# 英語記事生成
python3 "$HOME/affiliate-en/pipeline/batch_generate.py" --lang en

# 日本語記事生成
python3 "$HOME/affiliate-en/pipeline/batch_generate.py" --lang jp

# 英語サイト push
cd "$HOME/affiliate-en"
git add -A
git diff --cached --quiet || git commit -m "chore: auto-deploy $(date '+%Y-%m-%d')"
git push origin main

# 日本語サイト push
cd "$HOME/affiliate-jp"
git add -A
git diff --cached --quiet || git commit -m "chore: auto-deploy $(date '+%Y-%m-%d')"
git push origin main

echo "[$(date '+%Y-%m-%d %H:%M')] 完了"

osascript -e 'display notification "記事自動更新完了" with title "AI Affiliate" sound name "Glass"'
