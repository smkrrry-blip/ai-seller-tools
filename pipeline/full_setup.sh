#!/bin/bash
# full_setup.sh — APIキー設定 + n8nワークフロー登録 + 記事生成を一括実行
set -e

echo ""
echo "=== AI Affiliate セットアップ ==="
echo ""

# ── 1. ANTHROPIC_API_KEY ──────────────────────────────────────────────────────
echo "【1/3】 Anthropic API キーを入力してください（入力は非表示）："
read -s ANTHROPIC_API_KEY
echo "✓ 入力完了"

# ~/.zprofile に保存（永続化）
if ! grep -q "ANTHROPIC_API_KEY" ~/.zprofile 2>/dev/null; then
  echo "export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'" >> ~/.zprofile
  echo "  → ~/.zprofile に保存しました"
fi
export ANTHROPIC_API_KEY

# ── 2. n8n ワークフロー登録 ───────────────────────────────────────────────────
echo ""
echo "【2/3】 n8n パスワードを入力してください（入力は非表示）："
read -s N8N_PASS
echo "✓ 入力完了"

echo "  n8n にログイン中..."
LOGIN_RESP=$(curl -s -X POST http://localhost:5678/rest/login \
  -H "Content-Type: application/json" \
  -c /tmp/n8n_cookies.txt \
  -d "{\"emailOrLdapLoginId\":\"smkrrry@gmail.com\",\"password\":\"$N8N_PASS\"}")

if echo "$LOGIN_RESP" | grep -q "Wrong username"; then
  echo "✗ パスワードが違います。スクリプトを再実行してください。"
  exit 1
fi
echo "  ✓ ログイン成功"

# CSRF トークン取得
CSRF_TOKEN=$(echo "$LOGIN_RESP" | grep -o '"csrfToken":"[^"]*"' | cut -d'"' -f4)

# n8n API Key を新規作成
echo "  n8n API Key を作成中..."
API_KEY_RESP=$(curl -s -X POST http://localhost:5678/rest/user/api-key \
  -H "Content-Type: application/json" \
  -H "X-N8N-CSRF-TOKEN: $CSRF_TOKEN" \
  -b /tmp/n8n_cookies.txt \
  -d '{"label":"affiliate-auto"}')
N8N_KEY=$(echo "$API_KEY_RESP" | grep -o '"apiKey":"[^"]*"' | cut -d'"' -f4)

if [ -z "$N8N_KEY" ]; then
  echo "  API Key 作成に失敗しました。レスポンス: $API_KEY_RESP"
  # 既存のキーで試みる
  echo "  既存のワークフローとして登録を試みます..."
fi

# n8n にワークフローをインポート
WF_DIR="$HOME/affiliate-en/pipeline"
for WF_FILE in "$WF_DIR"/n8n_wf0*.json; do
  WF_NAME=$(basename "$WF_FILE")
  echo "  ワークフロー登録: $WF_NAME ..."
  IMPORT_RESP=$(curl -s -X POST http://localhost:5678/rest/workflows \
    -H "Content-Type: application/json" \
    -H "X-N8N-CSRF-TOKEN: $CSRF_TOKEN" \
    -b /tmp/n8n_cookies.txt \
    -d @"$WF_FILE")
  if echo "$IMPORT_RESP" | grep -q '"id"'; then
    WF_ID=$(echo "$IMPORT_RESP" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "  ✓ 登録完了 (ID: $WF_ID)"
    # 有効化
    curl -s -X PATCH "http://localhost:5678/rest/workflows/$WF_ID" \
      -H "Content-Type: application/json" \
      -H "X-N8N-CSRF-TOKEN: $CSRF_TOKEN" \
      -b /tmp/n8n_cookies.txt \
      -d '{"active":true}' > /dev/null
    echo "  ✓ ワークフロー有効化完了"
  else
    echo "  ✗ 登録失敗: $IMPORT_RESP" | head -c 200
  fi
done

# ── 3. 記事生成（今すぐ） ──────────────────────────────────────────────────────
echo ""
echo "【3/3】 記事を今すぐ生成しますか？ [y/N]"
read -r GENERATE_NOW

if [ "$GENERATE_NOW" = "y" ] || [ "$GENERATE_NOW" = "Y" ]; then
  echo "  英語記事を生成中..."
  python3 "$HOME/affiliate-en/pipeline/batch_generate.py" --lang en

  echo "  日本語記事を生成中..."
  python3 "$HOME/affiliate-en/pipeline/batch_generate.py" --lang jp

  echo "  英語サイトをデプロイ中..."
  cd "$HOME/affiliate-en"
  git add -A
  git diff --cached --quiet || git commit -m "feat: initial articles $(date '+%Y-%m-%d')"
  git push origin main

  echo "  日本語サイトをデプロイ中..."
  cd "$HOME/affiliate-jp"
  git add -A
  git diff --cached --quiet || git commit -m "feat: initial articles $(date '+%Y-%m-%d')"
  git push origin main

  osascript -e 'display notification "記事生成・デプロイ完了！" with title "AI Affiliate" sound name "Glass"'
fi

# クリーンアップ
rm -f /tmp/n8n_cookies.txt

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "   英語サイト: https://smkrrry-blip.github.io/ai-seller-tools/"
echo "   日本語サイト: https://smkrrry-blip.github.io/ai-seller-jp/"
echo "   n8n: http://localhost:5678 （WF-01が月・木 09:00に自動実行）"
