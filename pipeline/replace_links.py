#!/usr/bin/env python3
"""
replace_links.py — アフィリエイトリンクのplaceholderを実URLに一括置換

使い方:
  1. pipeline/.env に実URLを記入（下記フォーマット）
  2. python3 pipeline/replace_links.py

.env フォーマット例:
  HELIUM10_LINK=https://partnerstack.helium10.com/?fpr=shoichi
  JUNGLE_SCOUT_LINK=https://junglescout.com/?partner=shoichi
  VIRAL_LAUNCH_LINK=https://viral-launch.com/?ref=shoichi
  DATADIVE_LINK=https://datadive.tools/?ref=shoichi
"""

import os
import re
from pathlib import Path

# ── デフォルトのplaceholder → 環境変数マッピング ──────────────────────────────
PLACEHOLDER_MAP = {
    # 英語サイト
    "https://go.aisellertools.com/helium10":     "HELIUM10_LINK",
    "https://go.aisellertools.com/jungle-scout": "JUNGLE_SCOUT_LINK",
    "https://go.aisellertools.com/viral-launch": "VIRAL_LAUNCH_LINK",
    "https://go.aisellertools.com/datadive":     "DATADIVE_LINK",
    # 日本語サイト
    "https://go.aiseller-jp.com/helium10":       "HELIUM10_LINK",
    "https://go.aiseller-jp.com/jungle-scout":   "JUNGLE_SCOUT_LINK",
    "https://go.aiseller-jp.com/viral-launch":   "VIRAL_LAUNCH_LINK",
    "https://go.aiseller-jp.com/datadive":       "DATADIVE_LINK",
}

def load_env(env_file: Path) -> dict:
    """Load .env file into a dict."""
    env = {}
    if not env_file.exists():
        print(f"WARNING: {env_file} not found. Create it with your affiliate URLs.")
        return env
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def replace_in_file(path: Path, replacements: dict) -> int:
    """Replace placeholder URLs in a single file. Returns number of replacements."""
    content = path.read_text(encoding="utf-8")
    original = content
    count = 0
    for placeholder, real_url in replacements.items():
        if placeholder in content:
            content = content.replace(placeholder, real_url)
            count += content.count(real_url) - original.count(real_url)
            # recount properly
    if content != original:
        path.write_text(content, encoding="utf-8")
    return 0 if content == original else 1

def main():
    script_dir = Path(__file__).parent
    env_file = script_dir / ".env"
    env = load_env(env_file)

    # Build effective replacement map (only for keys that have a real URL)
    replacements = {}
    for placeholder, env_key in PLACEHOLDER_MAP.items():
        real_url = env.get(env_key)
        if real_url and real_url != placeholder:
            replacements[placeholder] = real_url

    if not replacements:
        print("No replacements configured. Add URLs to pipeline/.env")
        print("\nExample .env:")
        print("  HELIUM10_LINK=https://partnerstack.helium10.com/?fpr=YOUR_ID")
        print("  JUNGLE_SCOUT_LINK=https://junglescout.com/?partner=YOUR_ID")
        return

    print(f"Applying {len(replacements)} link replacement(s):")
    for p, r in replacements.items():
        print(f"  {p}")
        print(f"  → {r}")

    # Find all HTML files in both site directories
    base = script_dir.parent
    en_dir = base
    jp_dir = base.parent / "affiliate-jp"

    changed = 0
    for site_dir in [en_dir, jp_dir]:
        for html_file in site_dir.rglob("*.html"):
            if replace_in_file(html_file, replacements):
                print(f"  Updated: {html_file.relative_to(base.parent)}")
                changed += 1

    print(f"\n✓ Done — {changed} file(s) updated")
    print("\nNext: commit and push both repos")
    print("  cd ~/affiliate-en && git add -A && git commit -m 'feat: real affiliate links' && git push")
    print("  cd ~/affiliate-jp && git add -A && git commit -m 'feat: real affiliate links' && git push")

if __name__ == "__main__":
    main()
