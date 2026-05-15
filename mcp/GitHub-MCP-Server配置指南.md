# GitHub MCP Server 配置指南

## 简介

MCP (Model Context Protocol) 是 Anthropic 推出的开放协议，允许 Claude Code 与外部工具和数据源连接。通过配置 GitHub MCP Server，你可以在 Claude Code 中直接操作 GitHub——搜索仓库、管理 Issue、查看 PR 等。

## 前置条件

- Node.js (v18+) 和 npx
- GitHub Personal Access Token (PAT)

## 生成 GitHub Token

1. 打开 https://github.com/settings/tokens
2. 点击 **Generate new token** → **Generate new token (classic)**
3. **Note**: `claude-code-mcp`
4. **Expiration**: 建议 90 天
5. **勾选权限**:
   - `repo` — 完整仓库访问（代码、PR、Issue）
   - `read:org` — 读取组织信息
   - `read:user` — 读取用户信息
6. 点击 **Generate token** 并复制（只显示一次）

## 配置方式

### 方式一：全局配置（推荐）

编辑 `~/.claude/settings.json`，添加 `mcpServers` 字段：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_你的token"
      }
    }
  }
}
```

> 全局配置对所有项目生效。

### 方式二：项目级配置

在项目根目录创建 `.claude/mcp.json`：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_你的token"
      }
    }
  }
}
```

> 项目级配置只对当前项目生效。注意将 `.claude/` 加入 `.gitignore`，避免 token 泄露。

## 使用的 MCP Server

| 包名 | 说明 |
|------|------|
| `@modelcontextprotocol/server-github` | 官方 GitHub MCP Server，提供仓库、Issue、PR、搜索等 API 能力 |

## 可用功能示例

配置完成后，重启 Claude Code，即可在对话中使用：

- `搜索我最近的 GitHub 仓库`
- `列出我的 GitHub 信息`
- `查看仓库 xxx 的最近 Issue`
- `创建一个新的 Issue`
- `查看 PR #123 的详情`

## 安全提醒

- **不要** 将包含 token 的配置文件提交到 Git
- 定期轮换 Token（设置合理的过期时间）
- Token 权限遵循最小权限原则，按需勾选
