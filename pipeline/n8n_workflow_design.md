# n8n 自動化ワークフロー設計

## ワークフロー一覧

---

### WF-01: 記事自動生成 & デプロイ（週2回）

**トリガー:** Cron — 月・木 09:00 JST  
**フロー:**
```
Cron
  └─ Execute Command: python3 ~/affiliate-en/pipeline/batch_generate.py --lang en
  └─ Execute Command: python3 ~/affiliate-en/pipeline/batch_generate.py --lang jp
  └─ Execute Command: ~/affiliate-en/pipeline/deploy.sh
  └─ Telegram/通知: "記事生成・デプロイ完了: EN+JP"
```

**注意:** ANTHROPIC_API_KEY を n8n の Credentials（環境変数）に設定する

---

### WF-02: Google Search Console 順位監視（毎日）

**トリガー:** Cron — 毎日 08:30 JST  
**フロー:**
```
Cron
  └─ HTTP Request: GSC API (searchanalytics/query)
      - siteUrl: https://smkrrry-blip.github.io/ai-seller-tools/
      - dimensions: [query, page]
      - rowLimit: 50
  └─ Function: CTR < 2% OR position > 20 の記事を抽出
  └─ IF: 対象記事あり
      └─ Telegram通知: "要改善記事: {title} — CTR:{ctr}% pos:{pos}"
```

---

### WF-03: 競合モニタリング（毎日）

**トリガー:** Cron — 毎日 07:00 JST  
**フロー:**
```
Cron
  └─ HTTP Request: RSS取得
      - https://www.helium10.com/blog/feed/
      - https://www.junglescout.com/blog/feed/
  └─ Function: 前日以降の新着記事を抽出
  └─ IF: 新着あり
      └─ Claude API (claude-haiku): タイトルを見て「対抗記事が必要か」を判定
      └─ IF: 対抗必要
          └─ Telegram通知: "競合新記事: {title} → 対抗記事を検討"
```

---

### WF-04: beehiiv ニュースレター週次配信（週1回）

**トリガー:** Cron — 毎週火曜 10:00 JST  
**フロー:**
```
Cron
  └─ HTTP Request: beehiiv API — 直近7日の公開記事を取得
  └─ Claude API (claude-haiku): 記事を要約・ニュースレター原稿生成
  └─ HTTP Request: beehiiv API — ドラフト作成
  └─ Telegram通知: "ニュースレタードラフト作成完了。beehiivで確認して送信してください"
      (※送信は壮一さんが手動確認後に実行)
```

---

### WF-05: X(Twitter) 自動ポスト（週3回）

**トリガー:** Cron — 月・水・金 12:00 JST  
**フロー:**
```
Cron
  └─ Function: blog/配下の記事をランダムに1本選択
  └─ Claude API (claude-haiku): 記事からツイート文（英語/日本語）を生成
  └─ HTTP Request: Twitter API v2 — ポスト
  └─ Telegram通知: "ツイート投稿完了"
```

**注意:** Twitter API v2 Basic ($100/月) が必要。無料枠では投稿不可。

---

### WF-06: アフィリエイトリンク置換 (.env管理)

**目的:** 仮リンク（go.aisellertools.com/helium10 等）を実際のアフィリエイトURLに一括置換

**手順:**
1. PartnerStack/他ASPで審査通過後、実URLを取得
2. `~/affiliate-en/pipeline/.env` に記載
3. `replace_links.py` を実行（全HTMLを一括置換）

```
# .env 例
HELIUM10_LINK=https://partnerstack.helium10.com/?fpr=shoichi
JUNGLE_SCOUT_LINK=https://junglescout.com/?partner=shoichi
```

---

## セットアップ手順（n8n）

1. n8n起動確認: `docker ps | grep n8n`
2. http://localhost:5678 でワークフロー作成
3. Credentials追加:
   - `ANTHROPIC_API_KEY`（環境変数）
   - beehiiv API Key
   - Twitter Bearer Token（WF-05用）
4. WF-01から順に有効化

---

## 優先度

| WF | 優先度 | 理由 |
|---|---|---|
| WF-01 記事生成 | 必須・最優先 | コンテンツ蓄積がすべての前提 |
| WF-03 競合監視 | 高 | 機会損失防止 |
| WF-02 GSC監視 | 高 | 効果測定（GSC設定後） |
| WF-04 ニュースレター | 中 | 立ち上げ後 |
| WF-05 Twitter | 低 | API費用あり、後回し可 |
