#!/bin/bash
# setup_n8n_key.sh — n8n の Variables に ANTHROPIC_API_KEY を登録する
#
# 使い方:
#   ANTHROPIC_API_KEY=sk-ant-xxxx bash pipeline/setup_n8n_key.sh
#
# ※ n8n の API Key が必要です。
#   http://localhost:5678 → Settings → API → Create API Key → コピーして下記に設定

N8N_API_KEY="${N8N_API_KEY:-}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
N8N_URL="http://localhost:5678"

if [ -z "$N8N_API_KEY" ]; then
  echo "ERROR: N8N_API_KEY が未設定です"
  echo "http://localhost:5678 → Settings → n8n API → Create an API key"
  echo "取得後: N8N_API_KEY=xxxx ANTHROPIC_API_KEY=sk-ant-xxxx bash pipeline/setup_n8n_key.sh"
  exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: ANTHROPIC_API_KEY が未設定です"
  exit 1
fi

echo "n8n Variable に ANTHROPIC_API_KEY を登録します..."

# 既存のVariableを確認
EXISTING=$(curl -s "$N8N_URL/api/v1/variables" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  | grep -o '"key":"ANTHROPIC_API_KEY"' | head -1)

if [ -n "$EXISTING" ]; then
  echo "既に登録済みです（上書きするには n8n UI から手動更新してください）"
else
  # 新規作成
  RESULT=$(curl -s -X POST "$N8N_URL/api/v1/variables" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"key\": \"ANTHROPIC_API_KEY\", \"value\": \"$ANTHROPIC_API_KEY\"}")
  echo "登録結果: $RESULT"
fi

echo ""
echo "✓ 完了。次のステップ:"
echo "  1. n8n UI で n8n_wf01_article_gen.json をインポート"
echo "  2. ワークフローを有効化"
echo "  3. 手動実行で動作確認"
