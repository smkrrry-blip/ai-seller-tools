# Threads API セットアップ手順

## 必要なもの
- Threadsアカウント（Instagramアカウントと連携済み）
- Meta for Developersアカウント（無料）

## 手順（約10分）

### 1. Meta for Developers にアプリを作成
1. https://developers.facebook.com/apps/ を開く
2. 「アプリを作成」→「その他」→「ビジネス」
3. アプリ名：`affiliate-threads`（何でもOK）

### 2. Threads API を有効化
1. アプリのダッシュボード → 「製品を追加」
2. 「Threads API」を追加
3. 左メニュー「Threads API」→「設定」

### 3. アクセストークン取得
1. 「Threadsアカウントにログイン」で自分のアカウントを連携
2. 「ユーザーアクセストークンを生成」
3. 権限：`threads_basic` + `threads_content_publish` にチェック
4. トークンをコピー

### 4. ユーザーIDを取得
```bash
curl "https://graph.threads.net/v1.0/me?fields=id,username&access_token=YOUR_TOKEN"
```
→ `"id": "123456789"` の数字部分をコピー

### 5. 環境変数に保存
```bash
echo "export THREADS_ACCESS_TOKEN='your_token'" >> ~/.zprofile
echo "export THREADS_USER_ID='your_user_id'" >> ~/.zprofile
source ~/.zprofile
```

### 6. テスト投稿（プレビュー）
```bash
python3 ~/affiliate-en/pipeline/threads_post.py \
  --file ~/affiliate-en/blog/helium10-review-2026.html \
  --preview
```

### 7. 実際に投稿
```bash
python3 ~/affiliate-en/pipeline/threads_post.py \
  --file ~/affiliate-en/blog/helium10-review-2026.html \
  --post
```

### 8. 全記事を一括投稿（英語）
```bash
python3 ~/affiliate-en/pipeline/threads_post.py --all --lang en --post
```

### 9. 全記事を一括投稿（英語+日本語）
```bash
python3 ~/affiliate-en/pipeline/threads_post.py --all --lang both --post
```

## n8n での自動化
セットアップ完了後、n8n に `WF-05_threads_auto.json` をインポートすれば
毎週新記事が自動投稿されます（Claude Code に声をかければ作成します）。

## 注意事項
- Threads APIの投稿制限：1アカウントあたり250投稿/日
- 連続投稿は60秒間隔を推奨（スパム判定回避）
- アクセストークンの有効期限：60日（要更新）
