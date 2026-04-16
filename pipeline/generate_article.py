#!/usr/bin/env python3
"""
AI Seller Tools — Article Generation Pipeline
Usage:
  python generate_article.py --lang en --slug my-article --title "My Article Title"
  python generate_article.py --lang jp --slug my-article --title "記事タイトル"

Requires: ANTHROPIC_API_KEY in environment
"""

import argparse
import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

SITE_EN = {
    "name": "AI Seller Tools",
    "base_url": "https://smkrrry-blip.github.io/ai-seller-tools",
    "css_path": "/ai-seller-tools/assets/style.css",
    "nav": """<nav class="site-nav">
  <div class="nav-inner">
    <a href="/ai-seller-tools/" class="nav-logo">AI Seller Tools</a>
    <ul class="nav-links">
      <li><a href="/ai-seller-tools/">Home</a></li>
      <li><a href="/ai-seller-tools/blog/">Blog</a></li>
      <li><a href="/ai-seller-tools/about.html">About</a></li>
      <li><a href="/ai-seller-tools/disclosure.html">Disclosure</a></li>
    </ul>
  </div>
</nav>""",
    "footer": """<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-links">
      <a href="/ai-seller-tools/">Home</a>
      <a href="/ai-seller-tools/blog/">Blog</a>
      <a href="/ai-seller-tools/about.html">About</a>
      <a href="/ai-seller-tools/disclosure.html">Affiliate Disclosure</a>
    </div>
    <p>© 2026 AI Seller Tools · This site contains affiliate links. <a href="/ai-seller-tools/disclosure.html">See full disclosure.</a></p>
  </div>
</footer>""",
    "author_bio": """<div class="author-bio">
  <img src="https://amazing-japan.jp/wp-content/uploads/2022/09/IMG_4969.jpg" alt="Shoichi" width="64" height="64">
  <div class="author-bio-text">
    <h4>Shoichi</h4>
    <p>Amazon FBA seller based in Japan · 5+ years experience on JP, US, and EU marketplaces · I only review tools I personally pay for and use.</p>
  </div>
</div>""",
    "disclosure_banner": """<div class="disclosure-banner">This article contains affiliate links. If you purchase through my links, I earn a commission at no extra cost to you. <a href="/ai-seller-tools/disclosure.html">Full disclosure.</a></div>""",
    "output_dir": Path(__file__).parent.parent / "blog",
    "lang": "en",
    "affiliate_links": {
        "helium10": "https://go.aisellertools.com/helium10",
        "jungle_scout": "https://go.aisellertools.com/jungle-scout",
        "viral_launch": "https://go.aisellertools.com/viral-launch",
        "datadive": "https://go.aisellertools.com/datadive",
    }
}

SITE_JP = {
    "name": "AIセラーツールガイド",
    "base_url": "https://smkrrry-blip.github.io/ai-seller-jp",
    "css_path": "/ai-seller-jp/assets/style.css",
    "nav": """<nav class="site-nav">
  <div class="nav-inner">
    <a href="/ai-seller-jp/" class="nav-logo">AIセラーツールガイド</a>
    <ul class="nav-links">
      <li><a href="/ai-seller-jp/">ホーム</a></li>
      <li><a href="/ai-seller-jp/blog/">ブログ</a></li>
      <li><a href="/ai-seller-jp/about.html">サイトについて</a></li>
      <li><a href="/ai-seller-jp/disclosure.html">広告掲載</a></li>
    </ul>
  </div>
</nav>""",
    "footer": """<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-links">
      <a href="/ai-seller-jp/">ホーム</a>
      <a href="/ai-seller-jp/blog/">ブログ</a>
      <a href="/ai-seller-jp/about.html">サイトについて</a>
      <a href="/ai-seller-jp/disclosure.html">広告掲載について</a>
    </div>
    <p>© 2026 AIセラーツールガイド · 本サイトはアフィリエイト広告を利用しています。</p>
  </div>
</footer>""",
    "author_bio": """<div class="author-bio">
  <img src="https://amazing-japan.jp/wp-content/uploads/2022/09/IMG_4969.jpg" alt="壮一" width="64" height="64">
  <div class="author-bio-text">
    <h4>壮一</h4>
    <p>Amazon FBAセラー歴5年以上（JP・US・EU）。このサイトに掲載しているのは、自費で購入・使用したツールのみです。</p>
  </div>
</div>""",
    "disclosure_banner": """<div class="disclosure-banner">⚠️ 本記事にはアフィリエイトリンクが含まれます。リンク経由で購入された場合、読者の方に追加費用なく報酬が発生します。<a href="/ai-seller-jp/disclosure.html">詳細</a></div>""",
    "output_dir": Path(__file__).parent.parent.parent / "affiliate-jp" / "blog",
    "lang": "ja",
    "affiliate_links": {
        "helium10": "https://go.aiseller-jp.com/helium10",
        "jungle_scout": "https://go.aiseller-jp.com/jungle-scout",
        "viral_launch": "https://go.aiseller-jp.com/viral-launch",
        "datadive": "https://go.aiseller-jp.com/datadive",
    }
}

# ── Prompt builder ─────────────────────────────────────────────────────────────

SYSTEM_EN = """You are a content writer who is also an Amazon FBA seller with 5+ years of hands-on experience.
You write detailed, honest, experience-based articles for other Amazon sellers.

Rules:
- Always include personal experience and specific numbers (e.g., "cut my research time from 2 hours to 20 minutes")
- Always mention at least one genuine weakness or downside of any tool you review
- Use the author persona: Shoichi, Amazon FBA seller based in Japan
- Write in clear, direct English
- Output ONLY the <article> body HTML content (no full page wrapper — that is added by the pipeline)
- Use semantic HTML: h2, h3, p, ul, ol, table, blockquote
- Use CSS classes from the stylesheet: compare-table, cta-box, btn-primary, pro-con, pros, cons, rating, stars, faq, faq-item
- Affiliate links use placeholders like {helium10}, {jungle_scout} etc."""

SYSTEM_JP = """あなたはAmazon FBAセラー歴5年以上のコンテンツライターです。
実体験に基づいた、正直で詳細な記事を他のAmazonセラー向けに書きます。

ルール：
- 必ず個人的な体験と具体的な数字を含める（例：「リサーチ時間が2時間→20分に」）
- レビュー記事では必ず正直な欠点・デメリットを記述する
- 著者ペルソナ：壮一（Amazon FBAセラー、日本在住）
- 自然な日本語で書く
- <article>本文のHTMLのみ出力（ページ全体のラッパーはパイプラインが追加する）
- セマンティックHTML使用：h2, h3, p, ul, ol, table, blockquote
- CSSクラス使用：compare-table, cta-box, btn-primary, pro-con, pros, cons, rating, stars, faq, faq-item
- アフィリエイトリンクはプレースホルダー {helium10}, {jungle_scout} 等を使用"""


def build_prompt(title: str, article_type: str, keywords: list[str], lang: str) -> str:
    kw_str = ", ".join(keywords) if keywords else title
    if lang == "en":
        return f"""Write a complete, high-quality article for the following:

Title: {title}
Type: {article_type}
Target keywords: {kw_str}
Last updated: April 2026

Requirements:
- Minimum 1,200 words
- Include a comparison table if reviewing multiple tools
- Include a pros/cons section using the pro-con CSS classes
- Include 3-5 FAQ items at the end using the faq/faq-item CSS classes
- Include at least one CTA box with affiliate link placeholder
- Add JSON-LD schema appropriate for the article type (Article, Review, HowTo, or FAQPage)
- The JSON-LD goes in a <script type="application/ld+json"> block at the TOP of your output

Output format: JSON-LD script block first, then the article HTML body."""
    else:
        return f"""以下の記事を完全に書いてください：

タイトル：{title}
種類：{article_type}
ターゲットキーワード：{kw_str}
最終更新：2026年4月

要件：
- 最低1,200字以上
- 複数ツールをレビューする場合は比較表を含める
- pro-con CSSクラスを使った長所・短所セクション
- faq/faq-itemクラスを使った3〜5問のFAQ
- アフィリエイトリンクのプレースホルダーを含むCTAボックス
- 記事種別に合ったJSON-LDスキーマ（Article, Review, HowTo, FAQPage）
- JSON-LDは<script type="application/ld+json">ブロックとして出力の先頭に置く

出力形式：最初にJSON-LDスクリプトブロック、その後に記事本文HTML"""


# ── HTML wrapper ───────────────────────────────────────────────────────────────

def wrap_html(site: dict, slug: str, title: str, description: str, body: str) -> str:
    canonical = f"{site['base_url']}/blog/{slug}.html"
    lang = site["lang"]
    updated = "April 2026" if lang == "en" else "2026年4月"
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — {site['name']}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <link rel="stylesheet" href="{site['css_path']}">
</head>
<body>
{site['nav']}
<div class="container">
  <div class="article-wrap">
    <div class="article-header">
      <h1>{title}</h1>
      <div class="article-meta">
        <span>By Shoichi</span>
        <span>Last updated: {updated}</span>
      </div>
    </div>
    {site['disclosure_banner']}
    <div class="article-body">
{body}
    </div>
    {site['author_bio']}
  </div>
</div>
{site['footer']}
</body>
</html>"""


# ── Replace affiliate placeholders ────────────────────────────────────────────

def replace_affiliate_links(html: str, links: dict) -> str:
    for key, url in links.items():
        html = html.replace(f"{{{key}}}", url)
    return html


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate an affiliate article")
    parser.add_argument("--lang", choices=["en", "jp"], required=True)
    parser.add_argument("--slug", required=True, help="Output filename without .html")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--type", dest="article_type", default="review",
                        choices=["review", "comparison", "howto", "roundup", "listicle"])
    parser.add_argument("--keywords", default="", help="Comma-separated keywords")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt only, don't call API")
    args = parser.parse_args()

    site = SITE_EN if args.lang == "en" else SITE_JP
    system = SYSTEM_EN if args.lang == "en" else SYSTEM_JP
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    prompt = build_prompt(args.title, args.article_type, keywords, args.lang)

    if args.dry_run:
        print("=== SYSTEM ===")
        print(system)
        print("\n=== PROMPT ===")
        print(prompt)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    print(f"Generating: {args.title} ({args.lang}) ...")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )

    body = message.content[0].text
    body = replace_affiliate_links(body, site["affiliate_links"])

    description = args.description or args.title
    full_html = wrap_html(site, args.slug, args.title, description, body)

    out_path = site["output_dir"] / f"{args.slug}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(full_html, encoding="utf-8")
    print(f"✓ Written: {out_path}")
    print(f"  Tokens used: {message.usage.input_tokens} in / {message.usage.output_tokens} out")


if __name__ == "__main__":
    main()
