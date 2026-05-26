#!/usr/bin/env python3
"""
linux.do 帖子正文抓取（Playwright 版）

使用 Playwright 浏览器加载 cookies 抓取需要登录的帖子正文。
支持从 data/cookies.json 加载已保存的登录态。

用法:
  # 抓取单个帖子
  python3 fetch_content.py 2162720

  # 批量抓取高赞帖子（从 daily 数据中）
  python3 fetch_content.py --batch --min-likes 10

  # 指定 cookies 文件
  python3 fetch_content.py 2162720 --cookies /path/to/cookies.json

前置条件:
  pip install playwright
  playwright install chromium
"""

import json, sys, argparse, time
from datetime import datetime, timezone
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ 需要安装 playwright: pip install playwright && playwright install chromium")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
POSTS_DIR = DATA_DIR / "posts"
COOKIES_FILE = DATA_DIR / "cookies.json"
now = datetime.now(timezone.utc)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def load_cookies(filepath=None):
    """加载 cookies 文件"""
    filepath = Path(filepath or COOKIES_FILE)
    if not filepath.exists():
        log(f"❌ Cookies 文件不存在: {filepath}")
        log("   请先通过 Playwright MCP 登录 linux.do 并保存 cookies")
        return None
    cookies = json.loads(filepath.read_text())
    log(f"✅ 加载 {len(cookies)} 个 cookies")
    return cookies


def fetch_post_content(page, post_id, timeout=15000):
    """抓取单个帖子的首帖正文"""
    url = f"https://linux.do/t/{post_id}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        # 等待内容加载
        page.wait_for_selector(".cooked", timeout=8000)

        # 检测 Cloudflare 挑战
        if "Just a moment" in page.title():
            log(f"    ⚠️ Cloudflare 挑战页")
            return ""

        # 提取正文
        content = page.evaluate("""() => {
            const cooked = document.querySelector('.cooked');
            return cooked ? cooked.innerText : '';
        }""")

        if content:
            # 清理文本
            content = content.strip()
            if len(content) > 500:
                content = content[:500]
            return content
    except Exception as e:
        log(f"    ⚠️ 抓取失败: {e}")
    return ""


def update_post_content(post_id, content):
    """更新帖子 JSON 文件的 content 字段"""
    filepath = POSTS_DIR / f"{post_id}.json"
    if not filepath.exists():
        log(f"    ⚠️ 帖子文件不存在: {filepath}")
        return False

    d = json.loads(filepath.read_text())
    d["content"] = content
    d["content_fetched_at"] = now.isoformat()
    filepath.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    return True


def batch_fetch(min_likes=10, max_posts=20):
    """批量抓取高赞帖子正文"""
    today = now.strftime("%Y-%m-%d")
    daily_file = DATA_DIR / "daily" / f"{today}.json"

    if not daily_file.exists():
        log(f"❌ 今日数据文件不存在: {daily_file}")
        return

    daily = json.loads(daily_file.read_text())
    posts = daily.get("posts", [])

    # 筛选需要抓取的帖子
    candidates = [
        p for p in posts
        if p.get("like_count", 0) >= min_likes
        and not p.get("content")
    ]
    candidates.sort(key=lambda x: x["like_count"], reverse=True)
    candidates = candidates[:max_posts]

    log(f"📋 待抓取: {len(candidates)} 篇 (≥{min_likes} 赞, 无正文)")
    return candidates


def main():
    parser = argparse.ArgumentParser(description="linux.do 帖子正文抓取 (Playwright)")
    parser.add_argument("post_id", nargs="?", type=int, help="帖子 ID")
    parser.add_argument("--batch", action="store_true", help="批量抓取高赞帖子")
    parser.add_argument("--min-likes", type=int, default=10, help="最低点赞数")
    parser.add_argument("--max-posts", type=int, default=20, help="最大抓取数")
    parser.add_argument("--cookies", help="Cookies 文件路径")
    args = parser.parse_args()

    if not args.post_id and not args.batch:
        parser.print_help()
        sys.exit(1)

    # 加载 cookies
    cookies = load_cookies(args.cookies)
    if not cookies:
        sys.exit(1)

    # 转换 cookies 格式（Playwright 需要的格式）
    pw_cookies = []
    for c in cookies:
        pw_cookie = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
        }
        if c.get("httpOnly"):
            pw_cookie["httpOnly"] = True
        if c.get("secure"):
            pw_cookie["secure"] = True
        if c.get("sameSite"):
            pw_cookie["sameSite"] = c["sameSite"]
        if c.get("expires") and c["expires"] > 0:
            pw_cookie["expires"] = c["expires"]
        pw_cookies.append(pw_cookie)

    # 启动 Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(pw_cookies)
        page = context.new_page()

        if args.batch:
            candidates = batch_fetch(args.min_likes, args.max_posts)
            if not candidates:
                log("✅ 没有需要抓取的帖子")
                return

            success = 0
            for i, post in enumerate(candidates, 1):
                log(f"[{i}/{len(candidates)}] {post['title'][:40]}... (👍{post['like_count']})")
                content = fetch_post_content(page, post["id"])
                if content:
                    update_post_content(post["id"], content)
                    log(f"    ✅ {len(content)} 字")
                    success += 1
                else:
                    log(f"    ❌ 无内容")
                time.sleep(1)  # 避免请求过快

            log(f"\n📊 完成: {success}/{len(candidates)} 篇成功")
        else:
            log(f"📖 抓取帖子 #{args.post_id}")
            content = fetch_post_content(page, args.post_id)
            if content:
                update_post_content(args.post_id, content)
                log(f"✅ 抓取成功: {len(content)} 字")
                log(f"📝 内容预览: {content[:100]}...")
            else:
                log(f"❌ 抓取失败")

        browser.close()


if __name__ == "__main__":
    main()
