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

Wide 16:9 horizontal cinematic composition, full-frame landscape framing. absolutely no text, no letters, no Chinese characters, no watermark.
```

> **🔴 最后一行构图句是强制项（v3.63.0 坑 301）**：rainflow 端点必须传 `size:'auto'`（其余端点传 `1536x1024`；**按 URL 域名判端点，不按 `_000` 后缀判**，坑 304），而 `auto` **只靠 prompt 决定画幅**——缺这句时 gpt-image-2 返回方形 1254×1254，塞进 1920×1080 会裁掉两侧。1025 期补上后 6/6 出 1672×940/941（1.78）。只写 `16:9 aspect ratio` 不够。
>
> **禁止**再追加「今日羊报 AI / AI News 分两行显示在右上角充当背景」——该尾巴会诱发整段伪中文/英文烧进画面（v3.33.0 坑，scene2/scene4 报废重制）。品牌由 Remotion 标题栏叠加。


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
- [ ] 结尾带 `Wide 16:9 horizontal cinematic composition, full-frame landscape framing.`（坑 301，缺则出方图）
- [ ] 出图后 `PIL` 实测 `w/h >= 1.6`，方图判失败重出
- [ ] 写实风格，非过度幻想
- [ ] 无文字/水印污染画面（`absolutely no text, no letters, no Chinese characters, no watermark`）
- [ ] 情绪与脚本匹配

---

## 破格模式 Prompt 变体

破格模式下，在标准 prompt 末尾追加反差视觉描述。

### 追加格式

```
[标准 prompt] + The image conveys a sense of [破格类型]:
- [反差视觉元素1]
- [反差视觉元素2]
- unexpected contrast between [A] and [B]
```

### 各类型示例

**身份破格**：
```
... The image conveys a sense of unexpected role:
- a figure in [身份A] performing [行为B]
- contrast between formal/informal, powerful/vulnerable
- grounded, realistic setting that highlights the mismatch
```

**场景破格**：
```
... The image conveys a sense of environment mismatch:
- [行为A] happening in unexpected [环境B]
- surreal but photorealistic location
- visual tension between subject and surroundings
```

**道具破格**：
```
... The image conveys a sense of creative misuse:
- [日常物品A] being used for [非常规目的B]
- close-up on the repurposed object
- warm, grounded lighting despite the absurdity
```

**角色破格**：
```
... The image conveys a sense of role reversal:
- [角色A] behaving like [角色B]
- reversed hierarchy or expectation
- split composition showing both roles
```
