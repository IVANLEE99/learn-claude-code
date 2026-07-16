# Claude Code Skill 详解：gen-img

## 一、Skill 是什么

Skill（技能）是 Claude Code 的扩展机制，允许用户定义可复用的专业能力。它比 Command（命令）更强大：

| 特性 | Command | Skill |
|------|---------|-------|
| 调用方式 | 用户手动 `/command` | Claude 自动触发 + 用户手动 |
| 文件结构 | 单个 `.md` 文件 | 目录，含 `SKILL.md` + 脚本/参考资料 |
| 典型用途 | 动作型："帮我做 X" | 知识型 + 执行型："知道 X 并执行 X" |
| 可捆绑资源 | 不能 | 可以（脚本、模板、API 配置等） |

**一句话理解**：Command 是快捷操作按钮，Skill 是会自动识别场景并执行标准流程的领域专家。

---

## 二、gen-img Skill 说明

### 功能

基于 OpenAI 兼容 Images API 的图片生成工具，支持：
- 文本生成图片（text-to-image）
- 自定义尺寸、质量、格式
- **模型从 `GEN_IMG_MODEL` 读取**（如 `gpt-image-2` / `grok-imagine-image` / `grok-imagine-image-lite`）
- 自动保存到本地目录
- 支持批量生成（1-10 张）

### 触发条件

当用户提到以下关键词时，自动触发：
- 生成图片 / generate image / create image
- 画图 / 画一张 / draw
- 生图 / 出图 / create a picture
- 任何请求生成视觉内容的语句

### 技术架构

```
用户: "画一只戴墨镜的猫"
        ↓
Claude 检测到关键词 "画" → 激活 gen-img skill
        ↓
读取 SKILL.md → 解析用户意图（prompt、size、quality 等）
        ↓
从 ~/.claude/settings.json 读取 API 配置
        ↓
执行 gen-img.sh 脚本 → 读取 GEN_IMG_API_URL / KEY / MODEL → 调用 Images API
        ↓
API 返回 base64 图片数据
        ↓
脚本解码并保存为 PNG 文件
        ↓
Claude 使用 Read 工具展示生成的图片
```

---

## 三、创建详细过程

### 第 1 步：分析参考项目

项目来源：[CookSleep/gpt_image_playground](https://github.com/CookSleep/gpt_image_playground)

这是一个基于 React + TypeScript 的 Web UI 工具，核心特性：
- 支持 OpenAI 兼容接口（Images API + Responses API）
- 支持 fal.ai 和自定义 HTTP 服务商
- 内置可视化遮罩编辑器
- 纯本地 IndexedDB 存储

**关键代码分析：**

| 文件 | 作用 |
|------|------|
| `src/lib/openaiCompatibleImageApi.ts` | API 调用核心逻辑 |
| `src/lib/apiProfiles.ts` | API 配置管理 |
| `src/types.ts` | 类型定义（TaskParams、ApiResponse 等） |

**API 调用流程：**

```typescript
// 1. 构建请求体
const body = {
  model: profile.model,        // 从 GEN_IMG_MODEL 读取，如 "gpt-image-2" / "grok-imagine-image"
  prompt: prompt,               // 用户输入
  size: params.size,            // "1024x1024"
  quality: params.quality,      // "auto"
  output_format: params.output_format,  // "png"
  moderation: params.moderation,
  n: params.n,
  response_format: 'b64_json',
}

// 2. 发送请求
const response = await fetch(`${baseUrl}/v1/images/generations`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(body),
})

// 3. 解析响应
const payload = await response.json()
const b64 = payload.data[0].b64_json
```

### 第 2 步：创建 Skill 目录结构

```bash
mkdir -p ~/.claude/skills/gen-img/scripts
```

最终结构：
```
~/.claude/skills/gen-img/
├── SKILL.md                    # 入口文件（触发条件 + 执行步骤）
└── scripts/
    └── gen-img.sh              # 图片生成脚本
```

### 第 3 步：编写 SKILL.md

这是 Skill 的核心文件，包含：

1. **Frontmatter** — name、description、version
2. **触发条件** — 关键词列表，匹配用户输入
3. **环境变量** — API 配置读取方式
4. **执行步骤** — 4 步标准流程
5. **API 参考** — 请求/响应格式说明
6. **错误处理** — 常见问题排查

**关键设计决策：**

| 决策 | 选择 | 原因 |
|------|------|------|
| 响应格式 | `b64_json` | 直接在本地解码保存，无需处理 URL 过期 |
| 默认尺寸 | `1024x1024` | 平衡质量和生成速度 |
| 默认质量 | `auto` | 让 API 自动选择最优质量 |
| 保存目录 | `~/Documents/learn-claude-code/generated-images/` | 统一管理生成的图片 |

### 第 4 步：编写生成脚本

`gen-img.sh` 负责实际的 API 调用：

```bash
#!/bin/bash
# 核心逻辑：
# 1. 解析参数（prompt、size、quality、n、format）
# 2. 从 settings.json 读取 API 配置
# 3. 调用 curl 请求 API
# 4. 用 Python 解析 JSON 并保存 base64 图片
```

**脚本特点：**
- 自动从 `~/.claude/settings.json` 读取 API 配置
- 支持命令行参数和默认值
- 生成带时间戳的文件名，避免冲突
- 支持批量生成（多张图片）
- 错误处理和友好的输出信息

### 第 5 步：配置环境变量

在 `~/.claude/settings.json` 的 `env` 中添加：

```json
{
  "env": {
    "GEN_IMG_API_URL": "https://your-api-endpoint.com",
    "GEN_IMG_API_KEY": "sk-your-api-key-here",
    "GEN_IMG_MODEL": "gpt-image-2"
  }
}
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `GEN_IMG_API_URL` | 是 | API base URL（不要尾斜杠） |
| `GEN_IMG_API_KEY` | 是 | API Key |
| `GEN_IMG_MODEL` | 否 | 模型名，默认 `gpt-image-2`。可选：`grok-imagine-image`、`grok-imagine-image-lite` 等 |

脚本与 SKILL.md **不再硬编码 model**，统一从 `GEN_IMG_MODEL` 读取。
---

## 四、对话中的相关讨论

### Q: 为什么用 GPT-Image-2 而不是 DALL-E 3？

**A**: GPT-Image-2 是 OpenAI 最新的图像生成模型（2025 年发布），相比 DALL-E 3 有显著提升：
- **文字渲染**：GPT-Image-2 在图片中生成文字的能力远超 DALL-E 3
- **指令遵循**：更精确地理解复杂提示词
- **质量**：支持 4K 分辨率，细节更丰富
- **API 兼容**：使用相同的 `/v1/images/generations` 端点，迁移成本为零

### Q: 为什么用 b64_json 而不是 url 格式？

**A**: 
- `b64_json`：图片数据直接在响应中返回，解码后保存到本地，**无网络依赖**
- `url`：返回一个临时 URL，需要二次下载，**URL 可能过期**

对于 Claude Code 这种本地工具，`b64_json` 更可靠。

### Q: 如何支持参考图编辑（image editing）？

**A**: 当前 Skill 只支持 text-to-image。如需支持参考图编辑，需要：
1. 使用 `/v1/images/edits` 端点
2. 请求格式改为 `multipart/form-data`
3. 上传原图 + 遮罩图

这是后续可以扩展的功能。

### Q: API Key 安全吗？

**A**: 
- API Key 存储在 `~/.claude/settings.json`，**不写入代码**
- Skill 脚本运行时从配置文件读取，**不硬编码**
- `settings.json` 应加入 `.gitignore`，**不提交到仓库**

### Q: 如何切换到其他图片生成服务 / 模型？

**A**: 修改 `settings.json` 中的环境变量即可：

```json
{
  "env": {
    "GEN_IMG_API_URL": "https://elysiver.h-e.top",
    "GEN_IMG_API_KEY": "sk-your-key",
    "GEN_IMG_MODEL": "grok-imagine-image"
  }
}
```

常用组合示例：
| URL | MODEL | 备注 |
|-----|-------|------|
| `https://elysiver.h-e.top` | `grok-imagine-image` | 约 $0.5/request |
| `https://ai.xmiaom.com` | `grok-imagine-image-lite` | 约 $1/request |
| `https://new.iqach.top` | `grok-imagine-image` | 已验证可用 |
| OpenAI 兼容端点 | `gpt-image-2` | 官方 / 中转 |

切换后无需改代码；`gen-img.sh` 会自动读取 `GEN_IMG_MODEL`。
---

## 五、文件内容

Skill 已备份至本项目 `skills/gen-img/` 目录，完整文件请查看：

| 文件 | 说明 | 链接 |
|------|------|------|
| SKILL.md | 入口文件（触发条件 + 执行步骤） | [查看](gen-img/SKILL.md) |
| gen-img.sh | 图片生成脚本 | [查看](gen-img/scripts/gen-img.sh) |

---

## 六、使用方式

### 自动触发（推荐）

直接用自然语言描述你想生成的图片：

```
用户: "画一只在月球上弹钢琴的宇航员"
Claude: [自动激活 gen-img skill → 生成图片 → 展示结果]

用户: "生成一张赛博朋克风格的城市夜景，1536x1024"
Claude: [自动激活 → 使用指定尺寸 → 生成并保存]

用户: "draw a cute robot reading a book under a tree"
Claude: [自动激活 → 生成英文提示词图片]
```

### 手动调用脚本

```bash
# 基础用法
bash ~/.claude/skills/gen-img/scripts/gen-img.sh "一只戴墨镜的猫"

# 完整参数
bash ~/.claude/skills/gen-img/scripts/gen-img.sh \
  "赛博朋克城市夜景" \
  ~/output.png \
  1536x1024 \
  high \
  1 \
  png
```

### 参数说明

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| prompt | $1 | (必填) | 图片描述 |
| output | $2 | 自动生成 | 输出文件路径 |
| size | $3 | `1024x1024` | 尺寸：`1024x1024`、`1536x1024`、`1024x1536`、`auto` |
| quality | $4 | `auto` | 质量：`auto`、`low`、`medium`、`high` |
| n | $5 | `1` | 生成数量：1-10 |
| format | $6 | `png` | 格式：`png`、`jpeg`、`webp` |

---

## 七、测试结果

### 测试 1：基础生成（英文提示词）

```bash
bash ~/.claude/skills/gen-img/scripts/gen-img.sh \
  "a cute cat wearing sunglasses" \
  generated-images/test_cat.png 1024x1024 auto 1 png
```

![戴墨镜的猫](../generated-images/test_cat.png)

**结果：**
- 文件大小：2.5MB
- 分辨率：1254 x 1254（API 实际返回，略大于请求的 1024x1024）
- 格式：PNG
- 生成时间：< 10 秒
- 评价：猫咪细节丰富，墨镜反射效果逼真，背景海滩氛围到位

### 测试 2：复杂场景（高质量 + 自定义尺寸）

```bash
bash ~/.claude/skills/gen-img/scripts/gen-img.sh \
  "an astronaut playing a grand piano on the moon, Earth visible in the background, stars and lunar landscape, cinematic lighting, highly detailed" \
  generated-images/astronaut_piano_moon.png 1024x1024 high 1 png
```

![月球弹钢琴的宇航员](../generated-images/astronaut_piano_moon.png)

**结果：**
- 文件大小：约 3MB
- 分辨率：1254 x 1254
- 格式：PNG
- 生成时间：< 15 秒
- 评价：NASA 宇航服细节精准，Steinway & Sons 钢琴品牌标识清晰，地球与星空背景层次分明

### 测试 3：中文提示词

```bash
bash ~/.claude/skills/gen-img/scripts/gen-img.sh \
  "一只戴着墨镜的猫在海滩上" \
  generated-images/test_cn.png
```

**结果：** 成功生成，API 自动将中文提示词改写为英文后生成

### 测试总结

| 测试项 | 提示词语言 | 尺寸 | 质量 | 结果 |
|--------|-----------|------|------|------|
| 基础生成 | 英文 | 1024x1024 | auto | 成功 |
| 复杂场景 | 英文 | 1024x1024 | high | 成功 |
| 中文提示词 | 中文 | 1024x1024 | auto | 成功 |

**核心发现：**
- GPT-Image-2 对中英文提示词均有良好支持
- 实际输出分辨率（1254x1254）略大于请求值，属于 API 行为
- `high` 质量模式生成时间略长，但细节更丰富
- API 会自动改写提示词以提升生成质量

---

## 八、扩展方向

### 短期优化

1. **支持参考图编辑** — 使用 `/v1/images/edits` 端点
2. **支持 Responses API** — 使用 `/v1/responses` 端点，获得更好的提示词保护
3. **批量生成优化** — 并发请求提升速度

### 长期规划

1. **MCP Server 集成** — 将图片生成封装为 MCP 工具
2. **历史记录管理** — 本地存储生成历史，支持搜索和复用
3. **多服务商支持** — 自动切换 fal.ai、Replicate 等备用服务

---

## 九、相关资源

- Claude Code 官方文档: https://docs.anthropic.com/en/docs/claude-code
- OpenAI Image API: https://platform.openai.com/docs/guides/image-generation
- GPT Image Playground: https://github.com/CookSleep/gpt_image_playground
- MCP 协议: https://modelcontextprotocol.io
