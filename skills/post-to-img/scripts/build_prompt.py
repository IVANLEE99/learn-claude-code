#!/usr/bin/env python3
"""Build gen-img prompts from structured post content.json."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PRESETS = {
    "kawaii-journal": {
        "style_zh": (
            "横版日系手账风信息图海报，暖奶油米白纸张背景，草莓粉蜜桃橙薄荷绿低饱和配色。"
            "细手绘描边，平涂淡彩与腮红，圆角贴纸拼贴分区，Q版仓鼠与白兔吉祥物点缀。"
            "高信息密度但透气，深灰棕字，温柔治愈励志，不丧不暗黑。"
            "无写实摄影、无3D、无霓虹赛博、无真人脸，印刷级清晰数字插画。"
        ),
        "style_en": (
            "Horizontal 16:9 kawaii hand-drawn bullet-journal infographic on warm cream paper, "
            "strawberry pink coral peach mint pastels, thin outlines, flat color soft blush, "
            "rounded sticky-note cards, chibi hamsters and optional white rabbit teacher, "
            "gentle motivational workplace vibe, no photorealism no 3D no cyberpunk."
        ),
        "default_size": "1536x1024",
    },
    "clean-tech": {
        "style_zh": (
            "横版极简科技信息图，浅灰蓝背景，白卡片细灰描边，靛蓝标题，无吉祥物无贴纸，"
            "干净扁平 UI 插画，专业冷静，非手账非可爱风。"
        ),
        "style_en": (
            "Horizontal clean tech infographic, light gray-blue background, white cards thin gray borders, "
            "indigo titles, no mascots no stickers, flat UI illustration, professional calm."
        ),
        "default_size": "1536x1024",
    },
    "warm-note": {
        "style_zh": (
            "暖色便签拼贴海报，米黄底，粉色与淡黄便签微倾角，手写感标题，"
            "一只Q版仓鼠点缀，少表格多短句，治愈手账风，留白充足。"
        ),
        "style_en": (
            "Warm sticky-note collage poster, cream background, pink and yellow slightly tilted notes, "
            "hand-lettered title, one chibi hamster, short lines few tables, healing journal vibe."
        ),
        "default_size": "1536x1024",
    },
}

MASCOT_ZH = {
    "teacher-rabbit": "戴圆框眼镜粉领结持教鞭的白兔老师",
    "heart": "捧粉色爱心的圆润仓鼠",
    "crying": "捂脸哭泣的仓鼠",
    "sad": "失落表情的仓鼠",
    "dizzy": "晕眩表情的仓鼠",
    "focus-laptop": "戴耳机看笔记本电脑的专注仓鼠",
    "coins": "捧金币袋的仓鼠",
    "reading": "捧书阅读的仓鼠",
    "pray": "合掌加油的仓鼠",
    "sweat": "流汗的仓鼠",
}


def clip(text: str, n: int) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


def bullets_block(items: list[Any], limit: int = 5) -> str:
    lines = []
    for it in (items or [])[:limit]:
        s = clip(str(it), 28)
        if s:
            lines.append(f"  · {s}")
    return "\n".join(lines)


def build_zh(data: dict[str, Any], preset: str, textless: bool) -> str:
    p = PRESETS[preset]
    title = clip(data.get("title") or "复盘第一天", 14)
    subtitle = clip(data.get("subtitle") or "接受现实，复盘自己，拥抱变化，行动起来", 36)
    hook = clip(data.get("hook") or "生活不会突然变好，但你可以选择让自己变得更强", 32)

    parts: list[str] = [
        p["style_zh"],
        "",
        f"画幅横版信息图。顶部中央巨大粉色手写卡通标题「{title}」，周围爱心星星闪光；"
        f"下方棕色副标题「{subtitle}」。",
        f"左上角：{MASCOT_ZH['teacher-rabbit']}，旁边对话框写着「{hook}」。",
    ]

    moods = data.get("mood_checklist") or ["接受现实", "复盘反思", "规划未来", "行动起来"]
    moods_s = "、".join(clip(m, 8) for m in moods[:4])
    parts.append(
        f"右上角：{MASCOT_ZH['heart']}，旁边「今日心情备忘录」勾选清单：{moods_s}。"
    )
    parts.append("主体为三栏圆角卡片拼贴布局：")

    sections = data.get("sections") or []
    # Map first 3 to left column emotions if present
    left = sections[:3]
    if left:
        parts.append("【左栏】")
        for i, sec in enumerate(left, 1):
            h = clip(sec.get("heading") or f"区块{i}", 12)
            mood = sec.get("mascot_mood") or ("crying" if i == 1 else "sad" if i == 2 else "dizzy")
            mascot = MASCOT_ZH.get(mood, MASCOT_ZH["sad"])
            if textless:
                parts.append(f"{i}. 卡片标题区「{h}」，旁有{mascot}；正文为短列表色块占位。")
            else:
                parts.append(f"{i}.「{h}」：")
                parts.append(bullets_block(sec.get("bullets") or [], 4))
                parts.append(f"  旁有{mascot}。")

    # Middle: table + toolbox + trials
    table = data.get("table") or {}
    toolbox = data.get("toolbox") or []
    trials = data.get("trials") or []
    mid_sections = [s for s in sections[3:] if s.get("id") in (4, 5)] or sections[3:5]

    parts.append("【中栏】")
    if table.get("title") or table.get("rows"):
        th = clip(table.get("title") or "成长变化", 16)
        headers = table.get("headers") or ["阶段", "时间", "能力", "行动", "效果"]
        parts.append(f"大卡片「{th}」：粉表头表格列 { ' / '.join(headers[:5]) }。")
        if not textless:
            for row in (table.get("rows") or [])[:4]:
                if isinstance(row, dict):
                    cells = [clip(str(v), 12) for v in row.values()]
                else:
                    cells = [clip(str(c), 12) for c in row]
                parts.append("  行：" + " | ".join(cells[:5]))
        parts.append(f"旁有{MASCOT_ZH['focus-laptop']}。")
    for sec in mid_sections:
        h = clip(sec.get("heading") or "中栏", 14)
        if textless:
            parts.append(f"卡片「{h}」短列表占位。")
        else:
            parts.append(f"「{h}」：")
            parts.append(bullets_block(sec.get("bullets") or [], 4))

    if toolbox:
        if textless:
            parts.append("「我的工具箱」粉色便签色块。")
        else:
            tools = "、".join(clip(t, 16) for t in toolbox[:8])
            parts.append(f"「我的工具箱」便签：{tools}。")
    if trials:
        if textless:
            parts.append("「小尝试」一排打勾小卡片占位。")
        else:
            t = "；".join(clip(x, 18) for x in trials[:5])
            parts.append(f"「小尝试」打勾项：{t}。")

    # Right column
    plan = data.get("plan") or []
    money = data.get("money_ideas") or []
    letter = clip(data.get("letter_to_future") or "迷茫期很正常，方向比努力更重要。", 40)
    right_secs = sections[5:8]

    parts.append("【右栏】")
    if plan or any((s.get("heading") or "").find("计划") >= 0 for s in right_secs):
        parts.append(f"「接下来怎么做」金色星星列表，旁有微笑仓鼠。")
        if not textless:
            parts.append(bullets_block(plan or (right_secs[0].get("bullets") if right_secs else []), 4))
    if money:
        parts.append(f"「赚钱/变现思路」旁有{MASCOT_ZH['coins']}。")
        if not textless:
            parts.append(bullets_block(money, 4))
    parts.append(f"「给未来的自己」黄便签，旁有{MASCOT_ZH['reading']}。")
    if not textless:
        parts.append(f"  文案：「{letter}」")

    tip = clip(data.get("tip") or "焦虑解决不了问题，行动才有答案！", 28)
    closing = clip(
        data.get("closing")
        or "不管今天多难，明天都是新的开始。愿我们都能在不确定中，活出确定的自己！加油！",
        48,
    )
    cta = clip(data.get("cta") or "交流欢迎！一起加油鸭！", 24)

    parts.append("【底栏】")
    parts.append(f"左：今日小贴士「{tip}」+ {MASCOT_ZH['sweat']}。")
    parts.append(f"中：全宽寄语横幅「{closing}」配爱心。")
    parts.append(f"右：「{cta}」+ {MASCOT_ZH['pray']}。")

    parts.append("")
    parts.append(
        "避免：写实摄影、3D渲染、赛博霓虹、暗黑丧系、纯黑大字墙、无分区密文、真人脸、低清模糊、水印。"
    )
    if textless:
        parts.append("重要：正文用色块与线条示意排版，不要渲染大段可读汉字细节。")

    return "\n".join(parts)


def build_en(data: dict[str, Any], preset: str, textless: bool) -> str:
    p = PRESETS[preset]
    title = clip(data.get("title") or "Day One After Layoff", 40)
    subtitle = clip(data.get("subtitle") or "Accept, review, embrace AI, take action", 80)
    lines = [
        p["style_en"],
        f'Top center large pink hand-lettered Chinese title "{title}" with hearts and stars; subtitle "{subtitle}".',
        "Top-left cute white rabbit teacher with glasses and pink bow holding a pointer; top-right hamster holding a heart with checklist.",
        "Three-column rounded pastel sticky-note layout: LEFT emotion cards with crying/sad/dizzy hamsters; "
        "CENTER productivity table + AI toolbox + laptop hamster; RIGHT action plan + coins hamster + reading hamster.",
        "Bottom tip note, full-width warm banner message, praying hamster CTA.",
    ]
    if not textless:
        # light content hints
        secs = data.get("sections") or []
        for sec in secs[:6]:
            h = clip(sec.get("heading") or "", 20)
            if h:
                lines.append(f'Section "{h}" with short Chinese bullets.')
    lines.append(
        "Avoid photorealism, 3D, neon cyberpunk, dark gothic, dense unsectioned text walls, realistic humans, blur, watermark."
    )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build post-to-img prompts")
    ap.add_argument("--content", required=True, help="Path to content.json")
    ap.add_argument(
        "--preset",
        default="kawaii-journal",
        choices=sorted(PRESETS.keys()),
    )
    ap.add_argument("--out-dir", required=True, help="Output directory")
    ap.add_argument("--textless", action="store_true", help="Layout-only prompt")
    ap.add_argument("--size", default="", help="Override size e.g. 1536x1024")
    args = ap.parse_args()

    content_path = Path(args.content).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(content_path.read_text(encoding="utf-8"))
    size = args.size or PRESETS[args.preset]["default_size"]

    prompt_zh = build_zh(data, args.preset, args.textless)
    prompt_en = build_en(data, args.preset, args.textless)

    (out_dir / "prompt.txt").write_text(prompt_zh, encoding="utf-8")
    (out_dir / "prompt_en.txt").write_text(prompt_en, encoding="utf-8")

    meta = {
        "preset": args.preset,
        "size": size,
        "quality": "high",
        "format": "png",
        "textless": bool(args.textless),
        "title": data.get("title"),
        "source_url": data.get("source_url"),
        "prompt_file": "prompt.txt",
        "prompt_en_file": "prompt_en.txt",
    }
    (out_dir / "prompt.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Wrote {out_dir / 'prompt.txt'}")
    print(f"Wrote {out_dir / 'prompt_en.txt'}")
    print(f"Wrote {out_dir / 'prompt.meta.json'}")
    print(f"size={size} preset={args.preset} textless={args.textless}")


if __name__ == "__main__":
    main()
