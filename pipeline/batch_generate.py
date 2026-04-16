#!/usr/bin/env python3
"""
Batch article generator — reads articles.json and generates all pending articles.

Usage:
  python batch_generate.py --lang en
  python batch_generate.py --lang jp
  python batch_generate.py --lang en --force   # regenerate even if file exists
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ARTICLES_EN = [
    {
        "slug": "best-ai-tools-amazon-sellers-2026",
        "title": "Best AI Tools for Amazon Sellers in 2026 (Tested by an FBA Seller)",
        "description": "Honest, hands-on comparison of the best AI tools for Amazon FBA sellers in 2026. Written by Shoichi, a Japan-based seller with 5+ years of experience.",
        "type": "roundup",
        "keywords": ["ai tools amazon sellers", "best amazon seller tools 2026", "helium 10 review", "jungle scout"]
    },
    {
        "slug": "helium10-review-2026",
        "title": "Helium 10 Review 2026: Honest Take After 3 Years of Daily Use",
        "description": "Is Helium 10 worth it in 2026? Detailed review after 3 years of daily use by an Amazon FBA seller. Covers pricing, features, and honest downsides.",
        "type": "review",
        "keywords": ["helium 10 review", "helium 10 worth it", "helium 10 2026", "helium 10 pricing"]
    },
    {
        "slug": "jungle-scout-vs-helium10",
        "title": "Jungle Scout vs Helium 10 (2026): I Used Both for 6 Months",
        "description": "Definitive Jungle Scout vs Helium 10 comparison from someone who paid for both simultaneously. Which one wins in 2026?",
        "type": "comparison",
        "keywords": ["jungle scout vs helium 10", "jungle scout vs helium 10 2026", "best amazon research tool"]
    },
    {
        "slug": "ai-keyword-research-amazon",
        "title": "How to Use AI for Amazon Keyword Research: Step-by-Step Guide (2026)",
        "description": "My exact AI workflow for Amazon keyword research that cut my research time from 2 hours to 20 minutes. Combines Helium 10 with ChatGPT.",
        "type": "howto",
        "keywords": ["ai amazon keyword research", "amazon keyword research 2026", "helium 10 chatgpt", "amazon seo"]
    },
    {
        "slug": "ai-product-research-tools",
        "title": "5 Best AI Product Research Tools for Amazon FBA in 2026",
        "description": "Which AI tools are actually worth paying for when researching your next Amazon product? Tested by an FBA seller with 5+ years of experience.",
        "type": "listicle",
        "keywords": ["ai product research amazon", "amazon product research tools 2026", "amazon fba tools"]
    },
]

ARTICLES_JP = [
    {
        "slug": "amazon-ai-tools-2026",
        "title": "2026年版｜Amazonセラー向けAIツール完全比較【実際に使った正直レビュー】",
        "description": "Amazon FBAセラー歴5年以上の壮一が、実際に使ったAIツールを正直に比較。Helium 10・Jungle Scout等の使用感・価格・デメリットを徹底解説。",
        "type": "roundup",
        "keywords": ["Amazon セラー AIツール", "Helium 10 レビュー", "Jungle Scout 比較", "Amazonリサーチツール 2026"]
    },
    {
        "slug": "helium10-review",
        "title": "Helium 10レビュー2026年版｜3年間毎日使って分かった本音評価",
        "description": "Helium 10を3年間毎日使って分かった本音評価。価格・機能・デメリットを正直に解説。2026年も使い続けるべきか判断できます。",
        "type": "review",
        "keywords": ["Helium 10 レビュー", "Helium 10 評判", "Helium 10 料金", "Helium 10 使い方"]
    },
    {
        "slug": "jungle-scout-vs-helium10",
        "title": "Jungle Scout vs Helium 10 徹底比較【2026年版・両方6ヶ月使用】",
        "description": "Jungle ScoutとHelium 10の両方に6ヶ月課金して使い比べた結論。どちらを選べばいいか明確に解説します。",
        "type": "comparison",
        "keywords": ["Jungle Scout Helium 10 比較", "Jungle Scout vs Helium 10", "Amazon リサーチツール 比較"]
    },
    {
        "slug": "ai-keyword-research",
        "title": "AIを使ったAmazonキーワードリサーチ完全ガイド【2026年最新手順】",
        "description": "Helium 10とChatGPTを組み合わせてキーワードリサーチを2時間→20分に短縮した手順を公開。実際に使っている具体的なステップを解説。",
        "type": "howto",
        "keywords": ["Amazon キーワードリサーチ AI", "Helium 10 ChatGPT", "Amazon SEO 2026", "Amazon キーワード 探し方"]
    },
    {
        "slug": "ai-product-research",
        "title": "Amazon FBA商品リサーチに使えるAIツール5選【2026年版】",
        "description": "Amazon FBAの商品リサーチで実際に役立つAIツールを厳選。無駄な課金を避けるための選び方と、各ツールの長所・短所を解説。",
        "type": "listicle",
        "keywords": ["Amazon 商品リサーチ AIツール", "Amazon FBA ツール 2026", "Amazon リサーチ 効率化"]
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["en", "jp"], required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    articles = ARTICLES_EN if args.lang == "en" else ARTICLES_JP
    base = Path(__file__).parent.parent
    blog_dir = base / "blog" if args.lang == "en" else base.parent / "affiliate-jp" / "blog"

    generate_script = Path(__file__).parent / "generate_article.py"

    success, skip, fail = 0, 0, 0
    for art in articles:
        out_file = blog_dir / f"{art['slug']}.html"
        if out_file.exists() and not args.force:
            print(f"SKIP (exists): {art['slug']}")
            skip += 1
            continue

        cmd = [
            sys.executable, str(generate_script),
            "--lang", args.lang,
            "--slug", art["slug"],
            "--title", art["title"],
            "--description", art.get("description", art["title"]),
            "--type", art["type"],
            "--keywords", ",".join(art.get("keywords", [])),
        ]
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode == 0:
            success += 1
        else:
            print(f"FAIL: {art['slug']}")
            fail += 1

    print(f"\nDone — success:{success} skip:{skip} fail:{fail}")


if __name__ == "__main__":
    main()
