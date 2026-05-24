# Claude Code Skill 详解：publish-issue

## 一、Skill 是什么

Skill（技能）是 Claude Code 的扩展机制，允许用户定义可复用的专业能力。它比 Command（命令）更强大：

| 特性 | Command | Skill |
|------|---------|-------|
| 调用方式 | 用户手动 `/command` | Claude 自动触发 + 用户手动 |
| 文件结构 | 单个 `.md` 文件 | 目录，含 `SKILL.md` + 参考资料 |
| 典型用途 | 动作型："帮我做 X" | 知识型 + 执行型："知道 X 并执行 X" |
| 可捆绑资源 | 不能 | 可以（模板、脚本、示例等） |

**一句话理解**：Command 是快捷操作按钮，Skill 是会自动识别场景并执行标准流程的领域专家。

---

## 二、publish-issue Skill 说明

### 功能

将本地 Markdown 文件发布为 GitHub Issue，支持：
- 选择目标仓库（固定站点 / 当前 git 仓库 / 自定义）
- 动态获取并选择标签
- Token 从配置文件动态读取，不硬编码
- **自动上传附件**（图片、音频、视频等）
- 自动替换本地路径为 GitHub raw URL

### 触发条件

当用户提到以下关键词时，自动触发：
- 发布 issue / publish issue
- 提交 issue / submit issue
- 将 markdown 发布到 github
- 新建 issue / create issue
- 写完文档要发布

### 执行流程

```
用户: "帮我把这个文档发布到 GitHub"
        ↓
Step 1: 选择目标仓库（1/2/3）
        ↓
Step 2: 从配置文件读取 token
        ├── ~/.claude/settings.json
        ├── ~/.claude/settings.local.json
        └── 环境变量 $GITHUB_PERSONAL_ACCESS_TOKEN
        ↓
Step 3: 调 GitHub API 获取所有标签 → 用户选择
        ↓
Step 4: 读取 Markdown → 提取标题和内容
        ↓
Step 5: 扫描并上传附件
        ├── 扫描本地文件引用（图片、音频、视频等）
        ├── 用户确认上传
        ├── 上传到仓库 assets/attachments/ 目录
        └── 替换本地路径为 GitHub raw URL
        ↓
Step 6: 调 GitHub API 创建 Issue
        ↓
Step 7: 返回 Issue 编号、链接和附件统计
```

---

## 三、创建详细过程

### 第 1 步：创建目录结构

```bash
mkdir -p ~/.claude/skills/publish-issue/references
```

最终结构：
```
~/.claude/skills/publish-issue/
├── SKILL.md                          # 入口文件
└── references/
    ├── create-issue-api.md           # API 调用参考
    └── publish-config.md             # 仓库和标签配置
```

### 第 2 步：编写 SKILL.md

这是 Skill 的核心文件，包含：

1. **标题和描述** — Claude 根据描述判断什么时候触发
2. **触发条件** — 关键词列表，匹配用户输入
3. **执行步骤** — 每一步的具体操作指令
4. **参考链接** — 指向 references 目录的详细文档

### 第 3 步：编写参考文档

- `create-issue-api.md` — GitHub API 的技术细节（端点、请求格式、curl 示例）
- `publish-config.md` — 业务配置（目标仓库选项、标签说明、权限要求）

### 第 4 步：迭代优化

根据实际使用中的问题进行优化：

| 问题 | 修复方案 |
|------|----------|
| 目标仓库写死 | 支持 3 种选择：固定 / git remote / 自定义 |
| 标签写死 | 调 API 获取所有标签，用户选择 |
| Token 硬编码 | 从配置文件动态读取，支持多来源降级 |
| 附件无法上传 | 新增附件扫描和自动上传功能 |
| 中文文件名乱码 | URL 编码处理 |

---

## 四、核心功能详解

### 4.1 Token 读取机制

按优先级尝试以下来源：

1. **settings.json**：`~/.claude/settings.json` → `mcpServers.github.env.GITHUB_PERSONAL_ACCESS_TOKEN`
2. **settings.local.json**：`~/.claude/settings.local.json` → 相同路径
3. **环境变量**：`$GITHUB_PERSONAL_ACCESS_TOKEN`

如果都失败，提示用户手动输入。

### 4.2 附件上传功能

**支持的文件类型：**
- 图片：`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`
- 音频：`.mp3`, `.wav`, `.ogg`, `.m4a`
- 视频：`.mp4`, `.webm`
- 文档：`.pdf`

**扫描规则：**
- 匹配 Markdown 图片语法：`![alt](path)`
- 匹配 Markdown 链接语法：`[text](path)`
- 排除 URL（以 `http://` 或 `https://` 开头）
- 排除锚点链接（以 `#` 开头）

**上传流程：**
1. 扫描所有本地文件引用
2. 向用户确认上传列表
3. 对每个文件：
   - 读取文件并 Base64 编码
   - 上传到仓库的 `assets/attachments/` 目录
   - 获取 raw URL
   - 替换 Markdown 中的本地路径

**API 调用：**
```bash
# 1. Base64 编码并创建 JSON
python3 -c "
import base64, json
with open('FILE_PATH', 'rb') as f:
    content = base64.b64encode(f.read()).decode('utf-8')
data = {'message': 'feat: 添加附件', 'content': content}
with open('/tmp/upload_payload.json', 'w') as f:
    json.dump(data, f)
"

# 2. 上传文件
curl -s -X PUT "https://api.github.com/repos/OWNER/REPO/contents/PATH" \
  -H "Authorization: token TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/upload_payload.json
```

### 4.3 标签选择

使用 GitHub API 获取仓库所有标签，支持：
- 多选：可同时选择多个标签
- 自定义：输入新标签名，自动创建
- 推荐：标记 ⭐ 的为推荐标签

---

## 五、对话中的相关讨论

### Q: ~/.claude/commands 和 ~/.claude/skills 有啥区别？

**A**: 不是升级，是两个不同的东西：

- **Command** = 快捷操作按钮，用户手动按一下就执行
- **Skill** = 领域专家，Claude 自动判断什么时候该用它

Command 像手机里的快捷指令（手动触发），Skill 像随身顾问（遇到相关场景主动提醒）。

### Q: 为什么 publish-issue 适合用 Skill 而不是 Command？

**A**: 因为发布 Issue 是一个**多步骤的标准流程**（选仓库 → 读 token → 选标签 → 读内容 → 上传附件 → 调 API），每次都要重复同样的步骤。用 Skill 可以：

1. 自动触发 — 用户说"发布"就激活，不需要记命令名
2. 捆绑参考资料 — API 文档、配置信息随 Skill 一起携带
3. 流程标准化 — 每次执行步骤一致，不会遗漏

### Q: Skill 的触发机制是什么？

**A**: Claude 持续扫描用户输入，当检测到 SKILL.md 中定义的关键词时，自动加载 Skill 的内容作为上下文，然后按照执行步骤操作。

例如用户说"帮我把这个文档发布到 GitHub"：
- 匹配到关键词 "发布" + "GitHub"
- 自动激活 publish-issue skill
- 读取 SKILL.md 获取执行步骤
- 需要 API 细节时读取 references/create-issue-api.md
- 执行完毕后返回结果

### Q: 附件上传有什么限制？

**A**: 
- 文件大小：GitHub 限制单个文件 100 MB
- 中文文件名：自动 URL 编码
- 上传位置：统一存放在 `assets/attachments/` 目录
- 支持格式：图片、音频、视频、文档

---

## 六、文件内容

Skill 已备份至本项目 `skills/publish-issue/` 目录，完整文件请查看：

| 文件 | 说明 | 链接 |
|------|------|------|
| SKILL.md | 入口文件（触发条件 + 执行步骤） | [查看](publish-issue/SKILL.md) |
| create-issue-api.md | GitHub API 调用参考 | [查看](publish-issue/references/create-issue-api.md) |
| publish-config.md | 仓库和标签配置 | [查看](publish-issue/references/publish-config.md) |

---

## 七、使用方式

```bash
# 手动调用
/publish-issue ./mcp/GitHub-MCP-Server配置指南.md

# 自动触发
# 说 "帮我把这个文档发布到 GitHub" 即可
```

### 使用示例

**示例 1：发布简单文档**
```
用户: 帮我把这个文档发布到 GitHub
Claude: [激活 publish-issue skill]
        [读取 Markdown 文件]
        [选择仓库和标签]
        [创建 Issue]
        输出: Issue #61 已创建
```

**示例 2：发布带附件的文档**
```
用户: 发布这个带音频的文档
Claude: [激活 publish-issue skill]
        [扫描本地文件引用]
        [发现: 逍遥游.wav (3.7 MB)]
        [确认上传]
        [上传到 assets/attachments/]
        [替换链接]
        [创建 Issue]
        输出: Issue #62 已创建，1 个附件已上传
```

---

## 八、错误处理

### Token 相关
- **401 Unauthorized**：Token 无效或过期，提示用户重新生成
- **403 Forbidden**：Token 权限不足，需要 `repo` 权限

### 文件上传相关
- **413 Payload Too Large**：文件超过 GitHub 限制（100MB）
- **422 Unprocessable Entity**：文件路径无效或已存在

### Issue 创建相关
- **404 Not Found**：仓库不存在或无权访问
- **422 Validation Failed**：标签不存在或内容格式错误

---

## 九、最佳实践

1. **附件管理**：
   - 建议上传到 `assets/attachments/` 目录
   - 文件名使用有意义的名称
   - 大文件考虑使用 Git LFS

2. **内容优化**：
   - 确保图片链接可访问
   - 音频/视频文件建议添加描述
   - 本地路径使用相对路径

3. **安全考虑**：
   - 不要上传敏感信息（API Key、密码等）
   - 检查文件内容是否包含敏感数据

---

## 十、相关资源

- Claude Code 官方文档: https://docs.anthropic.com/en/docs/claude-code
- GitHub API 文档: https://docs.github.com/en/rest
- GitHub Contents API: https://docs.github.com/rest/repos/contents
- MCP 协议: https://modelcontextprotocol.io
