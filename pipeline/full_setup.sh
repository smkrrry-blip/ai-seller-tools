#!/bin/bash
# full_setup.sh — APIキー設定 + 記事生成 + launchd自動化 を一括実行
set -e

echo ""
echo "=== AI Affiliate セットアップ ==="
echo ""

# ── 1. ANTHROPIC_API_KEY ──────────────────────────────────────────────────────
echo "【1/3】 Anthropic API キーを入力してください（入力は非表示）："
read -s ANTHROPIC_API_KEY
echo ""
echo "✓ 入力完了"

# 空チェック
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "✗ キーが空です。再実行してください。"
  exit 1
fi

# ~/.zprofile に保存
grep -q "ANTHROPIC_API_KEY" ~/.zprofile 2>/dev/null && \
  sed -i '' '/ANTHROPIC_API_KEY/d' ~/.zprofile
echo "export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'" >> ~/.zprofile
export ANTHROPIC_API_KEY
echo "  → ~/.zprofile に保存しました"

# anthropic パッケージ確認・インストール
if ! python3 -c "import anthropic" 2>/dev/null; then
  echo "  anthropic パッケージをインストール中..."
  pip3 install anthropic -q
fi

# ── 2. 記事生成（今すぐ） ──────────────────────────────────────────────────────
echo ""
echo "【2/3】 記事を生成します（英語5本 + 日本語5本）"
echo "  ※ 1本あたり約30秒。合計15〜20分かかります"
echo ""

echo "  英語記事を生成中..."
python3 "$HOME/affiliate-en/pipeline/batch_generate.py" --lang en

echo "  日本語記事を生成中..."
python3 "$HOME/affiliate-en/pipeline/batch_generate.py" --lang jp

echo "  英語サイトをデプロイ中..."
cd "$HOME/affiliate-en"
git add -A
git diff --cached --quiet || git commit -m "feat: initial 5 articles (EN) $(date '+%Y-%m-%d')"
git push origin main

echo "  日本語サイトをデプロイ中..."
cd "$HOME/affiliate-jp"
git add -A
git diff --cached --quiet || git commit -m "feat: initial 5 articles (JP) $(date '+%Y-%m-%d')"
git push origin main

echo "  ✓ 記事生成・デプロイ完了"

# ── 3. launchd で自動化（月・木 09:00 JST） ──────────────────────────────────
echo ""
echo "【3/3】 自動実行スケジュール（月・木 09:00）を設定中..."

PLIST_PATH="$HOME/Library/LaunchAgents/com.affiliate.deploy.plist"

cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.affiliate.deploy</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$HOME/affiliate-en/pipeline/auto_deploy.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Weekday</key><integer>1</integer>
      <key>Hour</key><integer>9</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
      <key>Weekday</key><integer>4</integer>
      <key>Hour</key><integer>9</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>ANTHROPIC_API_KEY</key>
    <string>$ANTHROPIC_API_KEY</string>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>$HOME/affiliate-en/pipeline/deploy.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/affiliate-en/pipeline/deploy_error.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
PLIST

# 登録
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
echo "  ✓ 自動実行スケジュール設定完了（月・木 09:00 JST）"

# ── 完了通知 ──────────────────────────────────────────────────────────────────
osascript -e 'display notification "セットアップ完了！記事10本が公開されました" with title "AI Affiliate" sound name "Glass"'

echo ""
echo "✅ 全て完了！"
echo ""
echo "   英語サイト: https://smkrrry-blip.github.io/ai-seller-tools/"
echo "   日本語サイト: https://smkrrry-blip.github.io/ai-seller-jp/"
echo "   自動更新: 毎週月・木 09:00 に新記事を自動生成・公開"
echo ""
