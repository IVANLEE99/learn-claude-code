# Publish Markdown to GitHub Issue

将 Markdown 内容发布为 GitHub Issue

## 触发条件

当用户提到以下关键词时，自动触发此 Skill：
- 发布 issue / publish issue
- 提交 issue / submit issue
- 将 markdown 发布到 github
- 新建 issue / create issue
- 写完文档要发布

## 执行步骤

### 第 1 步：选择目标仓库

向用户展示以下选项：

```
请选择目标仓库：
1. IVANLEE99/IVANLEE99.github.io（个人站点）
2. 当前目录对应的 GitHub 仓库（通过 git remote 获取）
3. 自定义仓库（格式：owner/repo）
```

- 选项 1：固定为 `IVANLEE99/IVANLEE99.github.io`
- 选项 2：执行 `git remote get-url origin` 获取仓库地址，解析出 `owner/repo`
- 选项 3：让用户输入 `owner/repo` 格式的仓库名

### 第 2 步：读取 GitHub Token

从 `~/.claude/settings.json` 中读取 `mcpServers.github.env.GITHUB_PERSONAL_ACCESS_TOKEN` 作为认证 token。

```bash
cat ~/.claude/settings.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['mcpServers']['github']['env']['GITHUB_PERSONAL_ACCESS_TOKEN'])
"
```

如果读取失败，提示用户手动输入 token。

### 第 3 步：获取并选择标签

使用 token 调用 GitHub API 获取目标仓库的所有 labels：

```bash
curl -s -H "Authorization: token <TOKEN>" \
  "https://api.github.com/repos/<OWNER>/<REPO>/labels"
```

将 **所有标签** 展示为独立选项，支持多选：

```
选择标签（可多选，输入 Other 添加自定义标签）：

 [x] Claude Code ⭐（推荐）
 [ ] mcp
 [ ] bug
 [ ] enhancement
 [ ] documentation
 [ ] docker
 [ ] git
 [ ] github
 [ ] k8s
 [ ] Kubernetes
 [ ] mac
 [ ] node
 [ ] npm
 [ ] about
 [ ] AI
 [ ] Ai Prompt(Ai 提示词)
 [ ] CC Switch
 [ ] Charles
 [ ] codex
 [ ] duplicate
 [ ] Fetch
 [ ] Gemini CLI
 [ ] good first issue
 [ ] help wanted
 [ ] html2pdf.js
 [ ] invalid
 [ ] Navicat Premium
 [ ] open
 [ ] OpenClaw
 [ ] OpenCode
 [+ ] 自定义标签（输入 Other 添加新标签）

已选中：Claude Code
```

交互规则：
- **每个标签是一个独立选项**，全部列出
- 标记 ⭐ 的为推荐标签（默认预选）
- **多选**：可同时选择多个标签
- **自定义标签**：选择"自定义标签"选项后输入新标签名，会自动创建
- **回车**：确认当前选择并继续

### 第 4 步：读取 Markdown 内容

读取用户提供的 Markdown 文件或内容：
1. 提取第一个 `#` 标题作为 Issue 标题
2. 剩余内容作为 Issue body

### 第 5 步：创建 Issue

使用 GitHub API 创建 Issue（详见 [create-issue-api.md](references/create-issue-api.md)）

### 第 6 步：输出结果

返回 Issue 编号和链接：
```
Issue 已创建：
- #41 GitHub MCP Server 配置指南
- https://github.com/IVANLEE99/IVANLEE99.github.io/issues/41
- Labels: Claude Code, mcp
```

## 参考

- [GitHub API - Create Issue](references/create-issue-api.md)
- [仓库和标签配置](references/publish-config.md)
