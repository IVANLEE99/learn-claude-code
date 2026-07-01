# 月报图片 Prompt 模板（v3.1.0）

本模板用于月报模式（`REPORT_MODE=monthly`）生成视频场景图片的 Prompt。

---

## 基本信息

- **频道名称**: 「羊报AI月报」
- **副标题**: 「AI 月度盘点」
- 所有图片中如需显示台标，统一使用「羊报AI月报」，副标题使用「AI 月度盘点」，分两行显示在右上角，充当背景。
- **日期字段**: `{YYYY-MM}`（如 2026-06），不是 YYYY-MM-DD

---

## 生成规则

### 通用风格
- 所有图片保持统一的风格（暗色调科技感、强烈的蓝红对比灯光、现代新闻演播室）
- 所有图片保持统一的构图（主播在画面中央或偏左，背景为科技感大屏幕）
- **16:9 比例**（1536x1024）用于通用场景

### 场景 Prompt 结构

每个场景的 Prompt 必须包含：
1. **视觉元素**（背景大屏幕显示的内容）
2. **文字元素**（台标、日期、场景标题）
3. **风格描述**（固定后缀）

### Prompt 模板

```
A professional Chinese AI news studio scene {场景编号}. A male news anchor in a dark navy suit sits at a modern curved news desk. Behind him are multiple large display screens showing: {本月该趋势相关的视觉元素，如 OpenAI/Codex logo、智谱 GLM 标识、Anthropic Claude 图标、AI编程工具拼贴}. The studio has dramatic blue and red neon lighting. In the top right corner, display the text "羊报AI月报" on the first line and "AI 月度盘点" on the second line in large white Chinese characters. In the bottom center, display the month "{YYYY-MM}" in large white bold text. Professional broadcast news photography style, photorealistic, highly detailed, cinematic lighting, 16:9 aspect ratio.
```

---

## 各场景视觉元素建议

| 场景 | 内容 | 视觉元素建议 |
|------|------|------------|
| Scene 1 (Hook) | 本月概览 | AI 芯片电路 + 多个 AI 公司 logo 拼贴（OpenAI、智谱、Anthropic、DeepSeek）|
| Scene 2 (趋势一) | 趋势一相关 | 该趋势涉及的公司 logo/产品截图 + 关键数字 |
| Scene 3 (趋势二) | 趋势二相关 | 同上 |
| Scene 4 (趋势三) | 趋势三相关 | 同上 |
| Scene 5 (趋势四) | 趋势四相关 | 同上 |
| Scene 6 (月度总结) | 主题分布 | 多个图表/仪表盘 + "月度总结"文字 |
| Scene 7 (下月展望) | 未来趋势 | 箭头、时间线、问号、"下月展望"文字 |
| Scene 8 (CTA) | 引导关注 | "羊报AI月报" + 订阅按钮 + 二维码（如有） |

---

## 输出文件

生成的图片保存到 `{输出目录}/prompts/image-prompts-YYYY-MM.json`（文件名不含日，仅月）。

JSON 格式：
```json
[
  {
    "scene": 1,
    "content": "Hook 文本",
    "prompt": "完整英文 prompt...",
    "size": "1536x1024"
  }
]
```
