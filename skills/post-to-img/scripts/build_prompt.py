#!/usr/bin/env python3
"""Build gen-img prompts from structured post content.json."""

from __future__ import annotations

import argparse
import json
import re
from math import gcd
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


def ratio_label(size: str) -> str:
    """1152x1536 → '3:4'（1024x1536 → '2:3'，注意 2:3 不是 3:4）。"""
    try:
        w, h = (int(x) for x in size.lower().split("x"))
        g = gcd(w, h)
        return f"{w // g}:{h // g}"
    except Exception:
        return ""


def canvas_lock(size: str, portrait: bool) -> str:
    """画布锁定句：实测服务端不认精确像素，但 prompt 写死比例句后能出对比例（2924762 实测）。"""
    ratio = ratio_label(size)
    if not ratio:
        return ""
    w, h = size.lower().split("x")
    orient = "竖版" if portrait else "横版"
    pool = ["2:3", "手机长图"] if portrait else ["3:2", "16:9", "超宽横幅"]
    wrongs = "，".join("不是" + (" " if x[:1].isascii() else "") + x for x in [p for p in pool if p != ratio][:2])
    tail = "禁止上下超长留白" if portrait else "禁止超宽构图"
    return (
        f"画布必须是一张{orient}海报，像素 {w}×{h}，宽高比严格 {ratio}"
        f"（宽:高={ratio}，{wrongs}）。单页，内容全部收进这一张里，禁止拉成长截图、{tail}。"
    )


def bullets_block(items: list[Any], limit: int = 5) -> str:
    lines = []
    for it in (items or [])[:limit]:
        s = clip(str(it), 28)
        if s:
            lines.append(f"  · {s}")
    return "\n".join(lines)


def build_zh(
    data: dict[str, Any],
    preset: str,
    textless: bool,
    orientation: str = "horizontal",
    aspect: str = "",
    size: str = "",
) -> str:
    p = PRESETS[preset]
    portrait = orientation == "vertical"
    title = clip(data.get("title") or "复盘第一天", 14)
    subtitle = clip(data.get("subtitle") or "接受现实，复盘自己，拥抱变化，行动起来", 36)
    hook = clip(data.get("hook") or "生活不会突然变好，但你可以选择让自己变得更强", 32)
    style = p["style_zh"].replace("横版", "竖版", 1) if portrait else p["style_zh"]
    aspect_label = aspect or ("3:4" if portrait else "")
    frame = f"竖版{(' ' + aspect_label) if aspect_label else ''}" if portrait else (
        f"横版{(' ' + aspect_label) if aspect_label else ''}"
    )
    col_left = "【上区】" if portrait else "【左栏】"
    col_mid = "【中区】" if portrait else "【中栏】"
    col_right = "【下区】" if portrait else "【右栏】"
    stack_rule = (
        "禁止左右三栏并排，下面各区改为自上而下、拉通画幅宽度的圆角卡片。"
        if portrait else
        "主体为三栏圆角卡片拼贴布局。"
    )

    lock = canvas_lock(size, portrait)

    parts: list[str] = [style, ""]
    if lock:
        parts.append(lock)
    parts.append(
        f"画幅{frame}信息图。{stack_rule}"
        f"顶部中央巨大粉色手写卡通标题「{title}」，周围爱心星星闪光；"
        f"下方棕色副标题「{subtitle}」。"
    )
    parts.append(f"{'标题下方左侧' if portrait else '左上角'}：{MASCOT_ZH['teacher-rabbit']}，旁边对话框写着「{hook}」。")

    moods = data.get("mood_checklist") or ["接受现实", "复盘反思", "规划未来", "行动起来"]
    moods_s = "、".join(clip(m, 8) for m in moods[:4])
    parts.append(
        f"右上角：{MASCOT_ZH['heart']}，旁边「今日心情备忘录」勾选清单：{moods_s}。"
    )
    parts.append("分区顺序固定，不要打乱：")

    sections = data.get("sections") or []
    # Map first 3 to left column emotions if present
    left = sections[:3]
    if left:
        parts.append(col_left)
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

    parts.append(col_mid)
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

    parts.append(col_right)
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
        "避免：写实摄影、3D渲染、赛博霓虹、暗黑丧系、纯黑大字墙、无分区密文、真人脸、写实婴幼儿脸、伤害或虐待画面、网站名、论坛水印、低清模糊、水印。"
    )
    if textless:
        parts.append("重要：正文用色块与线条示意排版，不要渲染大段可读汉字细节。")

    return "\n".join(parts)


def build_en(
    data: dict[str, Any],
    preset: str,
    textless: bool,
    orientation: str = "horizontal",
    aspect: str = "",
    size: str = "",
) -> str:
    p = PRESETS[preset]
    portrait = orientation == "vertical"
    title = clip(data.get("title") or "Day One After Layoff", 40)
    subtitle = clip(data.get("subtitle") or "Accept, review, embrace AI, take action", 80)
    style = p["style_en"]
    if portrait:
        style = style.replace("Horizontal 16:9", "Vertical 3:4").replace("Horizontal", "Vertical")
    ratio = ratio_label(size)
    canvas_line = (
        f"Canvas must be exactly {size.lower()} pixels, aspect ratio strictly {ratio} "
        f"(not 2:3, not a long screenshot). Single page."
        if ratio else ""
    )
    layout = (
        "Vertical 3:4 stacked layout, NOT three side-by-side columns. "
        "Top title, then emotion cards, then table and toolbox, then action plan, then bottom banner."
        if portrait else
        "Three-column rounded pastel sticky-note layout: LEFT emotion cards with crying/sad/dizzy hamsters; "
        "CENTER productivity table + AI toolbox + laptop hamster; RIGHT action plan + coins hamster + reading hamster."
    )
    lines = [style]
    if canvas_line:
        lines.append(canvas_line)
    lines += [
        f'Frame {aspect or ("3:4" if portrait else "landscape")}. '
        f'Top center large pink hand-lettered Chinese title "{title}" with hearts and stars; subtitle "{subtitle}".',
        "Cute white rabbit teacher with glasses and pink bow holding a pointer; hamster holding a heart with checklist.",
        layout,
        "Bottom tip note, full-width warm banner message, praying hamster CTA.",
    ]
    if not textless:
        secs = data.get("sections") or []
        for sec in secs[:6]:
            h = clip(sec.get("heading") or "", 20)
            if h:
                lines.append(f'Section "{h}" with short Chinese bullets.')
    lines.append(
        "Avoid photorealism, 3D, neon cyberpunk, dark gothic, dense unsectioned text walls, "
        "realistic humans, realistic baby faces, harm, website names, forum watermarks, blur, watermark."
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
    ap.add_argument(
        "--size",
        default="",
        help="Override size e.g. 1536x1152（横版 4:3）/ 1152x1536（竖版 3:4；1024x1536 是 2:3 不要用）",
    )
    ap.add_argument(
        "--orientation",
        choices=["horizontal", "vertical"],
        default="horizontal",
        help="horizontal=横版三栏；vertical=竖版上下堆叠",
    )
    ap.add_argument("--aspect", default="", help="写入 prompt 的比例，如 4:3 / 3:4")
    ap.add_argument(
        "--prompt-name",
        default="",
        help="中文 prompt 文件名。指定后不覆盖 prompt.txt（便于同目录出双比例）",
    )
    args = ap.parse_args()

    content_path = Path(args.content).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(content_path.read_text(encoding="utf-8"))
    if args.size:
        size = args.size
    elif args.orientation == "vertical":
        size = "1152x1536"
    else:
        size = PRESETS[args.preset]["default_size"]

    prompt_zh = build_zh(data, args.preset, args.textless, args.orientation, args.aspect, size)
    prompt_en = build_en(data, args.preset, args.textless, args.orientation, args.aspect, size)

    if args.prompt_name:
        zh_name = args.prompt_name if args.prompt_name.endswith(".txt") else args.prompt_name + ".txt"
        stem = zh_name[:-4]
        en_name = f"{stem}_en.txt"
        meta_name = f"{stem}.meta.json"
    elif args.orientation == "vertical":
        zh_name, en_name, meta_name = "prompt-vertical.txt", "prompt-vertical_en.txt", "prompt-vertical.meta.json"
    else:
        zh_name, en_name, meta_name = "prompt.txt", "prompt_en.txt", "prompt.meta.json"

    (out_dir / zh_name).write_text(prompt_zh, encoding="utf-8")
    (out_dir / en_name).write_text(prompt_en, encoding="utf-8")

    meta = {
        "preset": args.preset,
        "orientation": args.orientation,
        "aspect": args.aspect,
        "size": size,
        "quality": "high",
        "format": "png",
        "textless": bool(args.textless),
        "title": data.get("title"),
        "source_url": data.get("source_url"),
        "prompt_file": zh_name,
        "prompt_en_file": en_name,
    }
    (out_dir / meta_name).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Wrote {out_dir / zh_name}")
    print(f"Wrote {out_dir / en_name}")
    print(f"Wrote {out_dir / meta_name}")
    print(f"size={size} preset={args.preset} orientation={args.orientation} textless={args.textless}")


if __name__ == "__main__":
    main()
