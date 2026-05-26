#!/usr/bin/env python3
"""
linux.do AI日报抓取脚本

数据源:
  A: https://linux.do/tag/444.json  (#人工智能 标签)
  B: https://linux.do/c/news/34.json (前沿快讯 分类)

用法:
  python3 skills/linuxdo-daily/scripts/scrape.py           # 抓取并生成日报
  python3 skills/linuxdo-daily/scripts/scrape.py --pages 5 # 每源抓5页
  python3 skills/linuxdo-daily/scripts/scrape.py --detail  # 抓取高赞帖正文
"""

import json, os, subprocess, sys, re
from datetime import datetime, timedelta, timezone
from pathlib import Path

# === 配置 ===
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # learn-claude-code/
DATA_DIR = PROJECT_ROOT / "data"
DAILY_DIR = DATA_DIR / "daily"
POSTS_DIR = DATA_DIR / "posts"
REPORTS_DIR = DATA_DIR / "reports"

SOURCES = {
    "ai_tag": "https://linux.do/tag/444.json",
    "news_category": "https://linux.do/c/news/34.json",
}

now = datetime.now(timezone.utc)
today = now.strftime("%Y-%m-%d")
scrape_window_start = (now - timedelta(hours=15)).strftime("%Y-%m-%dT%H:%M UTC")
scrape_window_end = now.strftime("%Y-%m-%dT%H:%M UTC")


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def fetch_json(url, timeout=15):
    """用 curl 抓取 JSON（跳过 SSL 验证）"""
    result = subprocess.run(
        ["curl", "-s", "-k", url,
         "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"],
        capture_output=True, text=True, timeout=timeout
    )
    return json.loads(result.stdout)


def fetch_html(url, timeout=20):
    """用 curl 抓取 HTML"""
    result = subprocess.run(
        ["curl", "-s", "-k", url,
         "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout


def fetch_all_pages(base_url, max_pages=3):
    """抓取多页数据"""
    all_topics = []
    for page in range(max_pages):
        url = f"{base_url}?page={page}"
        try:
            data = fetch_json(url)
            topics = data.get("topic_list", {}).get("topics", [])
            if not topics:
                break
            all_topics.extend(topics)
            log(f"  Page {page}: {len(topics)} topics")
        except Exception as e:
            log(f"  Page {page} failed: {e}")
            break
    return all_topics


def normalize_topic(t, source):
    """规范化帖子数据（完整版）"""
    posters = []
    for p in t.get("posters", []):
        posters.append({
            "user_id": p.get("user_id"),
            "description": p.get("description", "")
        })

    return {
        "id": t["id"],
        "title": t.get("fancy_title") or t.get("title", ""),
        "slug": t.get("slug", ""),
        "created_at": t.get("created_at", ""),
        "last_posted_at": t.get("last_posted_at", ""),
        "views": t.get("views", 0),
        "like_count": t.get("like_count", 0),
        "posts_count": t.get("posts_count", 0),
        "reply_count": t.get("reply_count", 0),
        "op_like_count": t.get("op_like_count", 0),
        "tags": [tag["name"] if isinstance(tag, dict) else tag for tag in t.get("tags", [])],
        "category_id": t.get("category_id"),
        "image_url": t.get("image_url"),
        "featured_link": t.get("featured_link"),
        "sources": [source],
        "content": "",
        "content_fetched_at": None,
        "posters": posters,
    }


def is_ai_post(post):
    """判断是否为 AI 相关帖子"""
    return "人工智能" in post["tags"]


def merge_posts(source_a, source_b_all):
    """合并两个源的数据，去重"""
    merged = {}
    for post in source_a:
        merged[post["id"]] = post
    for post in source_b_all:
        if post["id"] in merged:
            existing = merged[post["id"]]
            if "news_category" not in existing["sources"]:
                existing["sources"].append("news_category")
            existing["views"] = max(existing["views"], post["views"])
            existing["like_count"] = max(existing["like_count"], post["like_count"])
            existing["posts_count"] = max(existing["posts_count"], post["posts_count"])
        else:
            merged[post["id"]] = post
    return list(merged.values())


def count_history_hits(posts):
    """统计历史命中数（data/posts/ 中已存在的帖子）"""
    hits = 0
    for post in posts:
        filepath = POSTS_DIR / f"{post['id']}.json"
        if filepath.exists():
            hits += 1
    return hits


def save_post_history(posts):
    """保存帖子历史数据"""
    for post in posts:
        filepath = POSTS_DIR / f"{post['id']}.json"
        existing = None

        if filepath.exists():
            try:
                existing = json.loads(filepath.read_text())
            except:
                pass

        if existing:
            if "scrape_history" not in existing:
                existing["scrape_history"] = []
            existing["scrape_history"].append({
                "scraped_at": now.isoformat(),
                "views": post["views"],
                "like_count": post["like_count"],
                "posts_count": post["posts_count"]
            })
            existing["views"] = post["views"]
            existing["like_count"] = post["like_count"]
            existing["posts_count"] = post["posts_count"]
            existing["last_posted_at"] = post.get("last_posted_at", "")
            if post["content"] and not existing.get("content"):
                existing["content"] = post["content"]
                existing["content_fetched_at"] = post["content_fetched_at"]
            filepath.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
        else:
            post["scrape_history"] = [{
                "scraped_at": now.isoformat(),
                "views": post["views"],
                "like_count": post["like_count"],
                "posts_count": post["posts_count"]
            }]
            filepath.write_text(json.dumps(post, ensure_ascii=False, indent=2))


def fetch_post_content(post_id):
    """抓取帖子首帖正文（从 HTML 页面提取）"""
    try:
        url = f"https://linux.do/t/{post_id}"
        html = fetch_html(url, timeout=20)
        # 检测 Cloudflare 挑战页
        if "Just a moment" in html or "cf-mitigated" in html:
            return ""
        # 提取 .cooked 内的正文（第一篇帖子）
        match = re.search(r'<div class="cooked"[^>]*>(.*?)</div>\s*</article>', html, re.DOTALL)
        if not match:
            match = re.search(r'<div itemprop="text"[^>]*>(.*?)</div>', html, re.DOTALL)
        if match:
            raw = match.group(1)
            text = re.sub(r'<[^>]+>', '', raw).strip()
            text = re.sub(r'\s+', ' ', text)
            return text[:500]
    except Exception as e:
        log(f"    ⚠️ 正文抓取失败: {e}")
    return ""


def classify(post):
    """帖子分类"""
    tags, title = post["tags"], post["title"].lower()
    if "OpenAI" in tags or "ChatGPT" in tags or "openai" in title:
        return "OpenAI"
    if "Claude" in tags or "claude" in title or "anthropic" in title:
        return "Claude"
    if "DeepSeek" in tags or "deepseek" in title:
        return "DeepSeek"
    if "Gemini" in tags or "gemini" in title:
        return "Gemini"
    if "grok" in title or "xai" in title:
        return "Grok/xAI"
    if "Cursor" in tags or "Codex" in tags or "cursor" in title or "codex" in title:
        return "编程工具"
    if "开源" in " ".join(tags) or "开源" in title:
        return "开源项目"
    if any(k in title for k in ["发布", "上线", "更新", "突破", "训练", "模型", "降价", "完成"]):
        return "行业动态"
    return "其他"


def build_topic_groups(posts):
    """构建话题聚类"""
    groups = {}
    for post in posts:
        group = classify(post)
        if group not in groups:
            groups[group] = []
        groups[group].append(post)

    topic_groups = []
    for name, gposts in groups.items():
        if not gposts:
            continue
        gposts.sort(key=lambda x: x["like_count"], reverse=True)
        # 生成摘要：取 top 3 帖子标题
        top_titles = [p["title"][:40] for p in gposts[:3]]
        summary = "、".join(top_titles)
        topic_groups.append({
            "name": name,
            "count": len(gposts),
            "post_ids": [p["id"] for p in gposts],
            "top_post_id": gposts[0]["id"],
            "summary": summary
        })

    topic_groups.sort(key=lambda x: x["count"], reverse=True)
    return topic_groups


def save_daily_data(posts, stats, topic_groups):
    """保存每日数据（完整版）"""
    daily_file = DAILY_DIR / f"{today}.json"
    data = {
        "date": today,
        "scrape_window": f"{scrape_window_start} ~ {scrape_window_end}",
        "scraped_at": now.isoformat(),
        "sources": SOURCES,
        "stats": stats,
        "topic_groups": topic_groups,
        "posts": [{
            "id": p["id"],
            "title": p["title"],
            "tags": p["tags"],
            "views": p["views"],
            "like_count": p["like_count"],
            "posts_count": p["posts_count"],
            "reply_count": p["reply_count"],
            "op_like_count": p["op_like_count"],
            "image_url": p["image_url"],
            "featured_link": p["featured_link"],
            "sources": p["sources"],
            "content": p["content"],
            "content_fetched_at": p["content_fetched_at"],
            "posters": p["posters"],
        } for p in posts]
    }
    daily_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    log(f"💾 每日数据: {daily_file}")
    return daily_file


def generate_report(posts, stats, topic_groups):
    """生成 Markdown 日报（完整版）"""
    lines = []
    lines.append(f"# ⼈⼯智能技术⽇报")
    lines.append(f"")
    lines.append(f"**{today}** | 发布于 {now.strftime('%Y-%m-%d %H:%M UTC')} | 新帖 {stats['ai_posts']} 篇 | #⼈⼯智能 标签")
    lines.append(f"")

    # 数据概览
    lines.append(f"## 📊 数据概览")
    lines.append(f"")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 抓取窗口 | {scrape_window_start} ~ {scrape_window_end} |")
    lines.append(f"| 原始可见帖子 | {stats['raw_visible']} |")
    lines.append(f"| 原始新帖 | {stats['raw_new']} |")
    lines.append(f"| 历史命中（旧帖更新） | {stats['history_hit']} |")
    lines.append(f"| Source A (#人工智能) | {stats['raw_source_a']} |")
    lines.append(f"| Source B (前沿快讯) | {stats['raw_source_b']} |")
    lines.append(f"| Source B AI过滤 | {stats['ai_filtered_source_b']} |")
    lines.append(f"| 合并去重后 | {stats['merged_total']} |")
    lines.append(f"| AI 帖子 | {stats['ai_posts']} |")
    lines.append(f"| 话题组数量 | {stats['topic_groups']} |")
    lines.append(f"")

    # 今日主线趋势
    if topic_groups:
        lines.append(f"## 🔥 今日主线趋势")
        lines.append(f"")
        for g in topic_groups[:5]:
            lines.append(f"- **{g['name']}** ({g['count']}篇): {g['summary']}")
        lines.append(f"")

    # Top 10
    top = sorted(posts, key=lambda x: x["like_count"], reverse=True)[:10]
    lines.append(f"## 🏆 今日热门 Top 10")
    lines.append(f"")
    for i, p in enumerate(top, 1):
        lines.append(f"{i}. **{p['title'][:70]}**")
        lines.append(f"   - 👍 {p['like_count']} | 👁 {p['views']} | 💬 {p['posts_count']}")
        lines.append(f"   - 标签: {', '.join(p['tags'][:4])}")
        lines.append(f"")

    # 分类详情
    groups_dict = {}
    for post in posts:
        g = classify(post)
        if g not in groups_dict:
            groups_dict[g] = []
        groups_dict[g].append(post)

    lines.append(f"## 📂 分类详情")
    lines.append(f"")
    for name in ["OpenAI", "Claude", "DeepSeek", "Gemini", "Grok/xAI", "编程工具", "开源项目", "行业动态", "其他"]:
        gposts = groups_dict.get(name, [])
        if not gposts:
            continue
        gposts.sort(key=lambda x: x["like_count"], reverse=True)
        lines.append(f"### {name} ({len(gposts)})")
        lines.append(f"")
        for p in gposts[:8]:
            lines.append(f"- **{p['title'][:65]}**")
            lines.append(f"  - 👍 {p['like_count']} | 👁 {p['views']} | 💬 {p['posts_count']}")
        lines.append(f"")

    report = "\n".join(lines)
    report_file = REPORTS_DIR / f"{today}.md"
    report_file.write_text(report)
    log(f"📄 日报: {report_file}")
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="linux.do AI日报抓取")
    parser.add_argument("--pages", type=int, default=3, help="每源抓取页数")
    parser.add_argument("--detail", action="store_true", help="抓取高赞帖正文")
    args = parser.parse_args()

    # 确保目录存在
    for d in [DAILY_DIR, POSTS_DIR, REPORTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    log(f"🚀 linux.do AI日报抓取 - {today}")
    log(f"📅 抓取窗口: {scrape_window_start} ~ {scrape_window_end}")

    # === Source A ===
    log("\n=== Source A: #人工智能 标签 ===")
    source_a_raw = fetch_all_pages(SOURCES["ai_tag"], args.pages)
    source_a = [normalize_topic(t, "ai_tag") for t in source_a_raw]
    log(f"  Total: {len(source_a)}")

    # === Source B ===
    log("\n=== Source B: 前沿快讯 ===")
    source_b_raw = fetch_all_pages(SOURCES["news_category"], args.pages)
    source_b_all = [normalize_topic(t, "news_category") for t in source_b_raw]
    source_b_ai = [t for t in source_b_all if is_ai_post(t)]
    log(f"  Total: {len(source_b_all)}, AI filtered: {len(source_b_ai)}")

    # === 合并 ===
    log("\n=== 合并去重 ===")
    all_merged = merge_posts(source_a, source_b_all)
    ai_posts = [p for p in all_merged if is_ai_post(p)]
    log(f"  All merged: {len(all_merged)}")
    log(f"  AI posts: {len(ai_posts)}")

    # === 历史命中 ===
    history_hit = count_history_hits(ai_posts)
    log(f"  History hit: {history_hit}")

    # === 抓取正文 ===
    if args.detail:
        log("\n=== 抓取高赞帖正文 ===")
        high_value = sorted(
            [p for p in ai_posts if p["like_count"] >= 10],
            key=lambda x: x["like_count"], reverse=True
        )[:10]
        for post in high_value:
            log(f"  📖 {post['title'][:40]}... (👍{post['like_count']})")
            content = fetch_post_content(post["id"])
            if content:
                post["content"] = content
                post["content_fetched_at"] = now.isoformat()
                log(f"    ✅ {len(content)} 字")
    else:
        log("\n=== 跳过正文抓取（加 --detail 启用） ===")

    # === 话题聚类 ===
    log("\n=== 话题聚类 ===")
    topic_groups = build_topic_groups(ai_posts)
    for g in topic_groups:
        log(f"  {g['name']}: {g['count']} 篇")
    log(f"  Total groups: {len(topic_groups)}")

    # === 保存 ===
    save_post_history(ai_posts)

    stats = {
        "scrape_window": f"{scrape_window_start} ~ {scrape_window_end}",
        "scraped_at": now.isoformat(),
        "raw_visible": len(all_merged),
        "raw_new": len(source_a) + len(source_b_all),
        "history_hit": history_hit,
        "raw_source_a": len(source_a),
        "raw_source_b": len(source_b_all),
        "ai_filtered_source_b": len(source_b_ai),
        "merged_total": len(all_merged),
        "ai_posts": len(ai_posts),
        "topic_groups": len(topic_groups),
    }
    save_daily_data(ai_posts, stats, topic_groups)

    # === 生成日报 ===
    report = generate_report(ai_posts, stats, topic_groups)

    # === 概览 ===
    log(f"\n📊 数据概览")
    log(f"┌─────────────────────────┬──────────┐")
    log(f"│ 指标                     │ 数值     │")
    log(f"├─────────────────────────┼──────────┤")
    log(f"│ 抓取窗口                 │ {today}   │")
    log(f"│ 原始可见帖子             │ {len(all_merged):>8} │")
    log(f"│ 历史命中（旧帖更新）      │ {history_hit:>8} │")
    log(f"│ Source A (#人工智能)      │ {len(source_a):>8} │")
    log(f"│ Source B (前沿快讯)       │ {len(source_b_all):>8} │")
    log(f"│ Source B AI过滤          │ {len(source_b_ai):>8} │")
    log(f"│ 合并去重后               │ {len(all_merged):>8} │")
    log(f"│ AI 帖子                 │ {len(ai_posts):>8} │")
    log(f"│ 话题组数量               │ {len(topic_groups):>8} │")
    log(f"└─────────────────────────┴──────────┘")

    # 今日主线
    if topic_groups:
        log(f"\n🔥 今日主线趋势")
        for g in topic_groups[:5]:
            log(f"  • {g['name']} ({g['count']}篇): {g['summary']}")

    top = sorted(ai_posts, key=lambda x: x["like_count"], reverse=True)[:5]
    log(f"\n🏆 Top 5")
    for i, p in enumerate(top, 1):
        log(f"  {i}. {p['title'][:55]}... 👍{p['like_count']}")

    log(f"\n✅ 完成！")


if __name__ == "__main__":
    main()
