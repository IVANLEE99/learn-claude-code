# 仓库和标签配置

## 目标仓库（可选）

| 选项 | 仓库 | 获取方式 |
|------|------|----------|
| 1 | IVANLEE99/IVANLEE99.github.io | 固定选项 |
| 2 | 当前项目仓库 | `git remote get-url origin` 解析 |
| 3 | 自定义仓库 | 用户输入 `owner/repo` |

## 标签

标签从 GitHub API 动态获取，不硬编码。用户选择后应用到 Issue。

## Token

按以下顺序尝试读取：
1. `~/.claude/settings.json` 的 `mcpServers.github.env.GITHUB_PERSONAL_ACCESS_TOKEN`
2. `~/.claude/settings.local.json` 的相同路径
3. 环境变量 `GITHUB_PERSONAL_ACCESS_TOKEN`

如果都失败，提示用户手动输入。

## 权限

- Token 类型: classic PAT 或 fine-grained PAT
- 必需权限: `repo` (完整仓库访问，包含 issues 读写)
