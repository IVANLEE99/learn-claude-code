#!/usr/bin/env python3
"""Generate captions JSON from script text, timed to audio durations."""
import json
import os
import re

OUTPUT_DIR = os.path.expanduser("~/Documents/learn-claude-code/ai-tools-video/public")

# Audio durations in seconds (from previous generation)
AUDIO_DURATIONS = {
    "scene1_opening": 27.2,
    "scene2_claude_code": 61.3,
    "scene3_cursor": 56.8,
    "scene4_copilot": 56.1,
    "scene5_v0": 51.1,
    "scene6_bolt": 49.5,
    "scene7_summary": 66.8,
}

# Scene start times (cumulative, accounting for transitions)
SCENE_OFFSETS = {
    "scene1_opening": 0,
    "scene2_claude_code": 27.2 - 0.5,  # minus transition overlap
    "scene3_cursor": 27.2 - 0.5 + 61.3 - 0.5,
    "scene4_copilot": 27.2 - 0.5 + 61.3 - 0.5 + 56.8 - 0.5,
    "scene5_v0": 27.2 - 0.5 + 61.3 - 0.5 + 56.8 - 0.5 + 56.1 - 0.5,
    "scene6_bolt": 27.2 - 0.5 + 61.3 - 0.5 + 56.8 - 0.5 + 56.1 - 0.5 + 51.1 - 0.5,
    "scene7_summary": 27.2 - 0.5 + 61.3 - 0.5 + 56.8 - 0.5 + 56.1 - 0.5 + 51.1 - 0.5 + 49.5 - 0.5,
}

SCENES = [
    {
        "id": "scene1_opening",
        "text": "大家好，今天分享五个我亲测有效的AI效率工具。最近总有人问我，你一个人怎么搞定这么多事？答案很简单，用对工具。这五个工具，每一个都是我日常高频使用的，不是广告，纯粹觉得好用才推荐。接下来我会逐一演示，告诉大家每个工具适合什么场景，效率能提升多少。"
    },
    {
        "id": "scene2_claude_code",
        "text": "第一个是Claude Code，一个AI编程助手。它最大的特点是能理解你代码的意图，不只是简单的语法补全。主要功能有四个。第一，代码生成，你描述需求，它直接生成完整代码。第二，代码解释，看不懂的代码，让它解释给你听。第三，Bug调试，报错信息直接贴进去，帮你分析原因。第四，重构优化，代码写完让它优化，通常能提升百分之二十质量。适合什么场景呢？写重复性代码时，直接描述需求生成。接手老项目时，让它解释复杂逻辑。调试Bug时，快速定位问题原因。我用了三个月，最明显的感受是写代码的时间减少了百分之四十。以前要查文档，搜Stack Overflow的问题，现在直接问它就行。"
    },
    {
        "id": "scene3_cursor",
        "text": "第二个是Cursor，一个把AI深度集成到编辑器里的VS Code替代品。它的核心功能。第一，智能补全，不是简单的语法补全，而是理解上下文的智能建议。第二，代码重构，选中代码，描述你想怎么改，它帮你重构。第三，多文件编辑，一次对话，同时修改多个相关文件。第四，内联编辑，选中代码，直接用自然语言描述修改需求。适合什么场景呢？重构代码时，让它帮忙批量修改。写新功能时，利用智能补全加速。代码review时，让它帮忙检查问题。我从VS Code切换到Cursor后，编码速度提升了百分之三十。特别是重构代码的时候，效率提升非常明显。"
    },
    {
        "id": "scene4_copilot",
        "text": "第三个是GitHub Copilot，这是我用得最多的工具，已经离不开了。它的核心功能。第一，实时补全，写代码时自动给出建议，按Tab接受。第二，函数生成，写好函数名和注释，自动生成实现。第三，测试生成，写好函数，让它帮忙生成单元测试。第四，文档生成，代码写完，自动生成注释和文档。适合什么场景呢？写重复模式的代码时，自动补全超快。写单元测试时，让它帮忙生成测试用例。写文档时，自动生成规范的注释。这是我每天都在用的工具，每天至少节省两小时。特别是写CRUD代码和单元测试的时候，效率提升巨大。"
    },
    {
        "id": "scene5_v0",
        "text": "第四个是v0.dev，前端开发者的福音。它的核心功能。第一，组件生成，描述UI需求，直接生成React或Vue组件。第二，样式生成，自动添加Tailwind CSS样式。第三，响应式设计，生成的组件自带响应式适配。第四，实时预览，生成后可以直接预览效果。适合什么场景呢？快速搭建页面原型时，几分钟搞定。写UI组件时，生成基础代码再微调。学习前端时，看看AI怎么写组件。以前写一个复杂的表单组件要半天，现在十分钟搞定。特别适合快速验证想法和搭建原型。"
    },
    {
        "id": "scene6_bolt",
        "text": "第五个是bolt.new，AI全栈开发工具。它的核心功能。第一，全栈生成，前端、后端、数据库，一键生成。第二，实时预览，生成后直接在线预览。第三，迭代修改，对话式修改，逐步完善。第四，一键部署，生成后直接部署上线。适合什么场景呢？快速搭建MVP时，几分钟搞定原型。做个人项目时，省去搭建环境的时间。学习全栈开发时，看看完整项目结构。我用它做了两个小项目，从想法到上线只用了一小时。虽然不适合复杂项目，但做MVP和原型简直神器。"
    },
    {
        "id": "scene7_summary",
        "text": "好，我们来总结一下这五个工具。Claude Code，适合代码生成、调试、重构，效率提升百分之四十。Cursor，适合日常编码、重构，效率提升百分之三十。GitHub Copilot，适合代码补全、测试生成，效率提升百分之五十。v0.dev，适合UI组件、页面原型，效率提升百分之七十。bolt.new，适合MVP、原型、小项目，效率提升百分之八十。我的建议是，先从GitHub Copilot开始，这是基础。然后试试Cursor，替换VS Code。根据需要选择其他工具。最后送大家一句话，工具不会让你变成高手，但能让你有更多时间思考真正重要的事。如果觉得有用，别忘了三连支持一下！有问题欢迎在评论区交流。我们下期再见！"
    },
]

def split_into_sentences(text):
    """Split text into sentences by Chinese punctuation."""
    # Split by sentence-ending punctuation
    parts = re.split(r'([。！？，；])', text)
    sentences = []
    i = 0
    while i < len(parts):
        sentence = parts[i]
        # Attach punctuation to the sentence
        if i + 1 < len(parts) and parts[i + 1] in '。！？，；':
            sentence += parts[i + 1]
            i += 2
        else:
            i += 1
        if sentence.strip():
            sentences.append(sentence)
    return sentences

def generate_captions():
    all_captions = []
    caption_id = 0

    for scene in SCENES:
        scene_id = scene["id"]
        duration = AUDIO_DURATIONS[scene_id]
        offset = SCENE_OFFSETS[scene_id]
        sentences = split_into_sentences(scene["text"])

        # Distribute time proportionally by character count
        total_chars = sum(len(s) for s in sentences)
        current_time = 0.0

        for sentence in sentences:
            char_ratio = len(sentence) / total_chars
            sentence_duration = duration * char_ratio
            start_ms = (offset + current_time) * 1000
            end_ms = (offset + current_time + sentence_duration) * 1000

            all_captions.append({
                "text": sentence,
                "startMs": round(start_ms),
                "endMs": round(end_ms),
                "timestampMs": round(start_ms),
                "confidence": 1.0,
            })

            current_time += sentence_duration
            caption_id += 1

    # Save captions
    output_path = os.path.join(OUTPUT_DIR, "captions.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_captions, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(all_captions)} captions")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    generate_captions()
