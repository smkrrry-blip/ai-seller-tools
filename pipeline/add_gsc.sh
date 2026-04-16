#!/bin/bash
# add_gsc.sh — Google Search Console 確認コードを両サイトに追加してデプロイ
#
# 使い方:
#   bash ~/affiliate-en/pipeline/add_gsc.sh <ENコード> <JPコード>
#
# 例:
#   bash ~/affiliate-en/pipeline/add_gsc.sh abc123xyz def456uvw

EN_CODE="$1"
JP_CODE="$2"

if [ -z "$EN_CODE" ] || [ -z "$JP_CODE" ]; then
  echo "使い方: bash add_gsc.sh <英語サイトのコード> <日本語サイトのコード>"
  echo ""
  echo "コードの取得方法:"
  echo "  1. https://search.google.com/search-console/ を開く"
  echo "  2. 「プロパティを追加」→ URLを入力"
  echo "  3. 「HTMLタグ」を選択 → content=\"XXXXXXX\" の XXXXXXX 部分をコピー"
  exit 1
fi

# 英語サイト
sed -i '' "s|<!-- <meta name=\"google-site-verification\" content=\"GSC_VERIFICATION_CODE_EN\"> -->|<meta name=\"google-site-verification\" content=\"$EN_CODE\">|g" \
  ~/affiliate-en/index.html
echo "✓ 英語サイト: GSCコード設定済み"

# 日本語サイト
sed -i '' "s|<!-- <meta name=\"google-site-verification\" content=\"GSC_VERIFICATION_CODE_JP\"> -->|<meta name=\"google-site-verification\" content=\"$JP_CODE\">|g" \
  ~/affiliate-jp/index.html
echo "✓ 日本語サイト: GSCコード設定済み"

# デプロイ
cd ~/affiliate-en && git add index.html && git commit -m "feat: add GSC verification" && git push origin main
cd ~/affiliate-jp && git add index.html && git commit -m "feat: add GSC verification" && git push origin main

echo ""
echo "✅ デプロイ完了！"
echo "   数分後に GSC で「確認」ボタンを押してください。"
echo ""
echo "   サイトマップも送信してください："
echo "   EN: https://smkrrry-blip.github.io/ai-seller-tools/sitemap.xml"
echo "   JP: https://smkrrry-blip.github.io/ai-seller-jp/sitemap.xml"
