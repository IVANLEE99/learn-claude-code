# Claude Code Skills 配置文档

## 概述

Skills（技能）是 Claude Code 的扩展机制，允许定义可复用的专业能力。Claude 会根据用户输入自动触发相关 Skill，也可以通过 `/skill-name` 手动调用。

---

## 当前可用 Skills

### 1. publish-issue — GitHub Issue 发布

| 属性 | 说明 |
|------|------|
| **功能** | 将本地 Markdown 文件发布为 GitHub Issue |
| **触发关键词** | 发布 issue、publish issue、提交 issue、新建 issue |
| **执行流程** | 选择仓库 → 读取 token → 获取标签 → 读取内容 → 调用 API → 返回链接 |

```bash
# 手动调用
/publish-issue ./mcp/GitHub-MCP-Server配置指南.md

# 自动触发
# 说 "帮我把这个文档发布到 GitHub" 即可
```

---

### 2. weread — 微信读书助手

| 属性 | 说明 |
|------|------|
| **功能** | 搜索书籍、管理书架、查看笔记划线、浏览书评、阅读统计、发现推荐好书 |
| **触发关键词** | 微信读书、书架、笔记、划线、书评、阅读统计 |
| **详细文档** | [Claude-Code-Skill详解-weread.md](Claude-Code-Skill详解-weread.md) |

```bash
# 手动调用
/weread

# 自动触发
# 说 "帮我看看微信读书里的笔记" 即可
```

---

### 3. update-config — 配置管理

| 属性 | 说明 |
|------|------|
| **功能** | 通过 settings.json 配置 Claude Code，包括 hooks、权限、环境变量 |
| **触发关键词** | 配置、settings、hooks、permissions、环境变量 |
| **适用场景** | 自动化行为（hooks）、权限管理、环境变量设置 |

```bash
# 手动调用
/update-config

# 自动触发
# 说 "从现在开始每次运行 X 时执行 Y" 即可
```

---

### 4. keybindings-help — 快捷键配置

| 属性 | 说明 |
|------|------|
| **功能** | 自定义键盘快捷键、重新绑定按键、修改 ~/.claude/keybindings.json |
| **触发关键词** | 快捷键、键盘、keybindings、重新绑定 |

```bash
# 手动调用
/keybindings-help

# 自动触发
# 说 "帮我重新绑定 ctrl+s" 即可
```

---

### 5. simplify — 代码简化

| 属性 | 说明 |
|------|------|
| **功能** | 审查已修改的代码，检查复用性、质量和效率，并修复问题 |
| **触发关键词** | simplify、简化、重构、优化代码 |

```bash
# 手动调用
/simplify

# 自动触发
# 说 "帮我简化这些代码" 即可
```

---

### 6. fewer-permission-prompts — 减少权限提示

| 属性 | 说明 |
|------|------|
| **功能** | 扫描对话记录，将常见的只读 Bash 和 MCP 调用添加到允许列表 |
| **触发关键词** | 权限提示太多、减少权限弹窗、添加权限 |
| **作用** | 将允许列表写入 .claude/settings.json，减少后续操作的确认提示 |

```bash
# 手动调用
/fewer-permission-prompts

# 自动触发
# 说 "权限提示太多了，帮我减少一些" 即可
```

---

### 7. loop — 循环执行

| 属性 | 说明 |
|------|------|
| **功能** | 按固定间隔重复运行 prompt 或 slash command |
| **触发关键词** | 每隔 X 分钟、循环、轮询、定时检查 |
| **支持间隔** | 分钟级（如 5m）、小时级（如 1h） |

```bash
# 手动调用
/loop 5m /foo        # 每 5 分钟执行 /foo
/loop 1h /check      # 每 1 小时执行 /check

# 自动触发
# 说 "每隔 5 分钟检查一次部署状态" 即可
```

---

### 8. claude-api — Claude API 开发

| 属性 | 说明 |
|------|------|
| **功能** | 构建、调试和优化 Claude API / Anthropic SDK 应用 |
| **触发关键词** | Anthropic SDK、Claude API、prompt caching、thinking、tool use |
| **支持功能** | 缓存、thinking、tool use、batch、files、citations、memory |

```bash
# 手动调用
/claude-api

# 自动触发
# 当代码导入 anthropic 或 @anthropic-ai/sdk 时自动触发
```

---

### 9. init — 初始化文档

| 属性 | 说明 |
|------|------|
| **功能** | 为代码库创建 CLAUDE.md 文档 |
| **触发关键词** | 初始化、创建 CLAUDE.md、项目文档 |

```bash
# 手动调用
/init

# 自动触发
# 说 "帮我为这个项目创建文档" 即可
```

---

### 10. review — 代码审查

| 属性 | 说明 |
|------|------|
| **功能** | 审查 Pull Request 的代码变更 |
| **触发关键词** | review、审查 PR、代码审查 |

```bash
# 手动调用
/review

# 自动触发
# 说 "帮我审查这个 PR" 即可
```

---

### 11. security-review — 安全审查

| 属性 | 说明 |
|------|------|
| **功能** | 对当前分支的待合并变更进行安全审查 |
| **触发关键词** | security review、安全审查、漏洞检查 |

```bash
# 手动调用
/security-review

# 自动触发
# 说 "帮我做安全审查" 即可
```

---

## Skills 对比总览

| Skill | 类型 | 手动调用 | 自动触发 | 适用场景 |
|-------|------|----------|----------|----------|
| publish-issue | 工作流 | `/publish-issue` | 发布相关关键词 | 文档发布 |
| weread | 集成 | `/weread` | 微信读书相关 | 阅读管理 |
| update-config | 配置 | `/update-config` | 配置相关关键词 | 环境配置 |
| keybindings-help | 配置 | `/keybindings-help` | 快捷键相关 | 键盘定制 |
| simplify | 代码 | `/simplify` | 简化相关 | 代码优化 |
| fewer-permission-prompts | 配置 | `/fewer-permission-prompts` | 权限相关 | 减少弹窗 |
| loop | 工作流 | `/loop` | 定时相关 | 定时任务 |
| claude-api | 开发 | `/claude-api` | SDK 导入 | API 开发 |
| init | 文档 | `/init` | 初始化相关 | 项目文档 |
| review | 代码 | `/review` | 审查相关 | PR 审查 |
| security-review | 代码 | `/security-review` | 安全相关 | 安全检查 |

---

## 配置文件位置

- **用户级配置**: `~/.claude/skills/`
- **项目级配置**: `.claude/skills/`
- **设置文件**: `~/.claude/settings.json`

---

## 使用建议

1. **新手入门**：先使用 `init` 创建项目文档，然后通过 `/help` 了解可用命令
2. **日常开发**：使用 `simplify` 优化代码，`review` 审查 PR
3. **配置管理**：使用 `update-config` 和 `fewer-permission-prompts` 优化工作流
4. **安全检查**：合并前使用 `security-review` 进行安全审查
5. **定时任务**：使用 `loop` 实现定时检查和轮询

---

## 相关资源

- Claude Code 官方文档: https://docs.anthropic.com/en/docs/claude-code
- GitHub API 文档: https://docs.github.com/en/rest
- MCP 协议: https://modelcontextprotocol.io
