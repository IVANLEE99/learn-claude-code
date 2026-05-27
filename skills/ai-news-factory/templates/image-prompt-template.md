# 图片 Prompt 模板

## 视频品牌

- **频道名称**: 「今日羊报 AI」
- **副标题**: 「AI News」

所有图片中如需显示台标、频道名、编辑室标识、屏幕文字等，统一使用「今日羊报 AI」。副标题使用「AI News」。

## 核心方法：把新闻翻译成视觉画面

新闻通常是抽象逻辑，图像模型需要具体视觉元素。必须充当"美术指导"，把文字逻辑翻译成视觉画面。

## 第一步：拆解新闻为可画元素

拿到新闻后，用四个问题拆解：

| 问题 | 说明 | 示例 |
|------|------|------|
| 谁/什么 | 主体：人物、物体、场景 | 游客、AI模型、公司Logo |
| 在哪里 | 环境/地点 | 故宫、发布会、交易所 |
| 在做什么 | 动作/事件核心 | 拍照、发布、交易 |
| 整体氛围 | 情绪 | 惊喜、紧张、兴奋 |

## 第二步：选择视觉表现策略

| 新闻类型 | 策略 | 说明 |
|----------|------|------|
| 科技/产品 | 社论插画风 | 用具象物体代表抽象概念 |
| 财经/数据 | 隐喻风 + 数据具象化 | 图表、金币等视觉元素 |
| 社会/突发 | 纪实写实风 | 直接描绘新闻现场 |

## 第三步：Prompt 万能公式

```
[主体与环境] + [关键动作或事件] + [细节烘托] + [构图/镜头] + [风格/画质] — [不要什么]
```

## 填空即用模板

```
Create a realistic editorial news image about:

{新闻内容}

The image should show:
- clear main subject
- real-world environment
- strong relation to the news event
- cinematic but realistic lighting
- professional news photography style
- modern AI technology atmosphere

Avoid:
- abstract AI concepts
- floating holograms
- random sci-fi elements
- text in image
- logos
- low-detail compositions

[新闻核心地点] with [主要人物/物体], [他们在做的关键动作]. [标志性环境细节], [时间/天气/光线]. [情绪与氛围描述]. [新闻摄影/编辑插图风格], photorealistic, highly detailed, shot on [镜头焦段] — no text, no watermark.

16:9 aspect ratio
今日羊报 AI
AI News 
分两行显示在右上角,充当背景
```


## 避坑指南

1. **先说明任务**: Prompt 第一句告诉它要做什么（如 An editorial illustration...）
2. **用英文写**: 图像模型底层标签大多是英文，专业词汇质感更好
3. **避免抽象比喻**: 不要写"经济腾飞像雄鹰"，要画"城市高楼间阳光穿透、数据图表上升"
4. **不要让 AI 做算术或排版**: 不要试图画"500亿"字样，画"两只穿西装的手在金色背景下握手"
5. **用否定提示**: 加 —no text, no letters, no signature, no watermark 保证画面干净
6. **关键词前置**: 越靠前权重越高，重要元素放开头

## 质量检查清单

- [ ] 主体清晰，一眼能看懂
- [ ] 新闻核心信息点已视觉化
- [ ] 「今日羊报 AI」品牌可见（如需要）
- [ ] 16:9 比例，适合横屏视频
- [ ] 写实风格，非过度幻想
- [ ] 无文字/水印污染画面
- [ ] 情绪与脚本匹配
