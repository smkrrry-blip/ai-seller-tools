#!/usr/bin/env python3
"""
threads_post.py — ブログ記事をThreads投稿用テキストに変換して投稿

使い方:
  # 記事からThreads投稿文を生成（投稿せずプレビュー）
  python3 threads_post.py --file blog/helium10-review-2026.html --preview

  # 実際に投稿
  python3 threads_post.py --file blog/helium10-review-2026.html --post

  # 全記事を順番に処理（投稿済みをスキップ）
  python3 threads_post.py --all --post

環境変数（~/.zprofileに追加）:
  THREADS_ACCESS_TOKEN=your_token
  THREADS_USER_ID=your_user_id
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

THREADS_API = "https://graph.threads.net/v1.0"
POSTED_LOG = Path(__file__).parent / "threads_posted.json"

# 英語・日本語サイトのブログディレクトリ
BLOG_DIRS = {
    "en": Path.home() / "affiliate-en" / "blog",
    "jp": Path.home() / "affiliate-jp" / "blog",
}

SITE_URLS = {
    "en": "https://smkrrry-blip.github.io/ai-seller-tools/blog",
    "jp": "https://smkrrry-blip.github.io/ai-seller-jp/blog",
}

# ── HTML → テキスト抽出 ───────────────────────────────────────────────────────

def extract_article_text(html_path: Path) -> dict:
    """HTMLファイルからタイトル・本文テキストを抽出"""
    content = html_path.read_text(encoding="utf-8")

    # タイトル
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else html_path.stem

    # メタディスクリプション
    desc_match = re.search(r'<meta name="description" content="([^"]+)"', content)
    description = desc_match.group(1) if desc_match else ""

    # 本文テキスト（article-body内）
    body_match = re.search(r'<div class="article-body">(.*?)</div>\s*<div class="author-bio"', content, re.DOTALL)
    if body_match:
        body_html = body_match.group(1)
        body_text = re.sub(r'<[^>]+>', ' ', body_html)
        body_text = re.sub(r'\s+', ' ', body_text).strip()[:2000]
    else:
        body_text = description

    # 言語判定
    lang = "jp" if re.search(r'<html lang="ja"', content) else "en"

    # 記事URL
    slug = html_path.stem
    article_url = f"{SITE_URLS[lang]}/{slug}.html"

    return {
        "title": title,
        "description": description,
        "body": body_text,
        "lang": lang,
        "url": article_url,
        "slug": slug,
    }


# ── Claude でThreads投稿文生成 ────────────────────────────────────────────────

def generate_threads_post(article: dict) -> str:
    """記事情報からThreads投稿文（500字以内）を生成"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)

    if article["lang"] == "en":
        prompt = f"""Write a compelling Threads post (max 500 characters) for this blog article.

Article title: {article['title']}
Article URL: {article['url']}
Description: {article['description']}

Requirements:
- Hook in the first line (make people want to read more)
- 2-3 key insights or numbers from the article
- End with the article URL
- Use relevant emojis sparingly
- No hashtags (Threads doesn't boost them like Instagram)
- Tone: experienced Amazon seller sharing genuine advice
- Max 500 characters total

Output ONLY the post text, nothing else."""
    else:
        prompt = f"""以下のブログ記事について、Threadsに投稿するテキストを書いてください（500文字以内）。

記事タイトル：{article['title']}
記事URL：{article['url']}
概要：{article['description']}

要件：
- 1行目でフック（続きを読みたくなる一文）
- 記事の重要な数字・発見を2〜3点
- 最後に記事URLを記載
- 絵文字を適度に使用（使いすぎない）
- ハッシュタグなし
- トーン：Amazonセラーの実体験を共有するリアルな声
- 合計500文字以内

投稿テキストのみを出力してください。"""

    message = client.messages.create(
        model="claude-haiku-4-5",  # 安価なモデルで生成
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()


# ── Threads API 投稿 ──────────────────────────────────────────────────────────

def post_to_threads(text: str, user_id: str, access_token: str) -> dict:
    """Threads APIに投稿（2ステップ：コンテナ作成 → 公開）"""

    # Step 1: メディアコンテナ作成
    container_resp = requests.post(
        f"{THREADS_API}/{user_id}/threads",
        params={
            "media_type": "TEXT",
            "text": text,
            "access_token": access_token,
        }
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]
    print(f"  コンテナ作成: {container_id}")

    # Step 2: 公開（APIの仕様上30秒待機が推奨）
    time.sleep(30)
    publish_resp = requests.post(
        f"{THREADS_API}/{user_id}/threads_publish",
        params={
            "creation_id": container_id,
            "access_token": access_token,
        }
    )
    publish_resp.raise_for_status()
    return publish_resp.json()


# ── 投稿済みログ管理 ──────────────────────────────────────────────────────────

def load_posted_log() -> dict:
    if POSTED_LOG.exists():
        return json.loads(POSTED_LOG.read_text())
    return {}

def save_posted_log(log: dict):
    POSTED_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False))

def is_posted(slug: str) -> bool:
    return slug in load_posted_log()

def mark_posted(slug: str, post_id: str):
    log = load_posted_log()
    log[slug] = {"post_id": post_id, "posted_at": datetime.now().isoformat()}
    save_posted_log(log)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Threads投稿ツール")
    parser.add_argument("--file", help="特定のHTMLファイルを処理")
    parser.add_argument("--all", action="store_true", help="全記事を処理")
    parser.add_argument("--lang", choices=["en", "jp", "both"], default="both")
    parser.add_argument("--preview", action="store_true", help="投稿せずプレビューのみ")
    parser.add_argument("--post", action="store_true", help="実際に投稿する")
    args = parser.parse_args()

    if not args.preview and not args.post:
        print("--preview または --post を指定してください")
        sys.exit(1)

    # 対象ファイルを収集
    files = []
    if args.file:
        files = [Path(args.file)]
    elif args.all:
        langs = ["en", "jp"] if args.lang == "both" else [args.lang]
        for lang in langs:
            files.extend(sorted(BLOG_DIRS[lang].glob("*.html")))
        files = [f for f in files if f.name != "index.html"]

    if not files:
        print("対象ファイルがありません")
        sys.exit(1)

    # Threads認証情報
    access_token = os.environ.get("THREADS_ACCESS_TOKEN", "")
    user_id = os.environ.get("THREADS_USER_ID", "")

    if args.post and (not access_token or not user_id):
        print("ERROR: THREADS_ACCESS_TOKEN と THREADS_USER_ID を設定してください")
        print("取得方法: ~/affiliate-en/pipeline/setup_threads.md を参照")
        sys.exit(1)

    for html_file in files:
        slug = html_file.stem
        if args.post and is_posted(slug):
            print(f"SKIP (投稿済み): {slug}")
            continue

        print(f"\n処理中: {html_file.name}")
        article = extract_article_text(html_file)
        post_text = generate_threads_post(article)

        print(f"\n{'='*50}")
        print(post_text)
        print(f"{'='*50}")
        print(f"文字数: {len(post_text)}")

        if args.post:
            result = post_to_threads(post_text, user_id, access_token)
            post_id = result.get("id", "unknown")
            mark_posted(slug, post_id)
            print(f"✓ 投稿完了 (ID: {post_id})")
            if len(files) > 1:
                print("  次の投稿まで60秒待機...")
                time.sleep(60)

    print("\n✓ 全処理完了")


if __name__ == "__main__":
    main()
