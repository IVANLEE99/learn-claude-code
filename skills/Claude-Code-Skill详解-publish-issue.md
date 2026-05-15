# Claude Code Skill 详解：publish-issue

## 一、Skill 是什么

Skill（技能）是 Claude Code 的扩展机制，允许用户定义可复用的专业能力。它比 Command（命令）更强大：

| 特性 | Command | Skill |
|------|---------|-------|
| 调用方式 | 用户手动 `/command` | Claude 自动触发 + 用户手动 |
| 文件结构 | 单个 `.md` 文件 | 目录，含 `SKILL.md` + 参考资料 |
| 典型用途 | 动作型："帮我做 X" | 知识型："知道 X 的最佳实践" |
| 可捆绑资源 | 不能 | 可以（模板、脚本、示例等） |

**一句话理解**：Command 是快捷操作按钮，Skill 是会自动识别场景并执行标准流程的领域专家。

---

## 二、publish-issue Skill 说明

### 功能

将本地 Markdown 文件发布为 GitHub Issue，支持：
- 选择目标仓库（固定站点 / 当前 git 仓库 / 自定义）
- 动态获取并选择标签
- Token 从配置文件动态读取，不硬编码

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
Step 2: 从 ~/.claude/settings.json 读取 token
        ↓
Step 3: 调 GitHub API 获取所有标签 → 用户选择
        ↓
Step 4: 读取 Markdown → 提取标题和内容
        ↓
Step 5: 调 GitHub API 创建 Issue
        ↓
Step 6: 返回 Issue 编号和链接
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
| Token 硬编码 | 从 `~/.claude/settings.json` 动态读取 |

---

## 四、对话中的相关讨论

### Q: ~/.claude/commands 和 ~/.claude/skills 有啥区别？

**A**: 不是升级，是两个不同的东西：

- **Command** = 快捷操作按钮，用户手动按一下就执行
- **Skill** = 领域专家，Claude 自动判断什么时候该用它

Command 像手机里的快捷指令（手动触发），Skill 像随身顾问（遇到相关场景主动提醒）。

### Q: 为什么 publish-issue 适合用 Skill 而不是 Command？

**A**: 因为发布 Issue 是一个**多步骤的标准流程**（选仓库 → 读 token → 选标签 → 读内容 → 调 API），每次都要重复同样的步骤。用 Skill 可以：

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

---

## 五、文件内容

Skill 已备份至本项目 `skills/publish-issue/` 目录，完整文件请查看：

| 文件 | 说明 | 链接 |
|------|------|------|
| SKILL.md | 入口文件（触发条件 + 执行步骤） | [查看](publish-issue/SKILL.md) |
| create-issue-api.md | GitHub API 调用参考 | [查看](publish-issue/references/create-issue-api.md) |
| publish-config.md | 仓库和标签配置 | [查看](publish-issue/references/publish-config.md) |

---

## 六、使用方式

```bash
# 手动调用
/publish-issue ./mcp/GitHub-MCP-Server配置指南.md

# 自动触发
# 说 "帮我把这个文档发布到 GitHub" 即可
```

---

## 七、相关资源

- Claude Code 官方文档: https://docs.anthropic.com/en/docs/claude-code
- GitHub API 文档: https://docs.github.com/en/rest
- MCP 协议: https://modelcontextprotocol.io
