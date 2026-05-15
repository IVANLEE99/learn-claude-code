# Git MCP Server 配置指南

## 简介

Git MCP Server 是 Anthropic 官方提供的 Git 操作 MCP 服务器，让 Claude Code 可以直接执行 Git 命令——查看状态、提交、分支管理、日志查询等。

## 前置条件

- Node.js (v18+) 和 npx
- Git 已安装

## 功能列表

| 工具 | 说明 |
|------|------|
| `git_status` | 查看仓库状态 |
| `git_diff` | 查看文件差异 |
| `git_log` | 查看提交历史 |
| `git_show` | 查看提交详情 |
| `git_branch` | 分支操作 |
| `git_checkout` | 切换分支/文件 |
| `git_add` | 暂存文件 |
| `git_commit` | 提交更改 |
| `git_push` | 推送到远程 |
| `git_pull` | 拉取远程更新 |
| `git_merge` | 合并分支 |
| `git_stash` | 暂存工作区 |
| `git_tag` | 标签操作 |

## 配置方式

### 方式一：全局配置（推荐）

编辑 `~/.claude/settings.json`，在 `mcpServers` 中添加：

```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-git"
      ]
    }
  }
}
```

### 方式二：项目级配置

在项目根目录创建 `.claude/mcp.json`：

```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-git"
      ]
    }
  }
}
```

## 使用示例

配置完成后，重启 Claude Code，即可在对话中使用：

```
查看当前仓库状态
```

```
查看最近 5 条提交记录
```

```
创建一个新分支 feature/login
```

```
查看 main 和 feature/login 的差异
```

```
提交当前所有更改，提交信息为 "feat: add login"
```

## 与 Claude Code 内置 Git 工具的区别

| 特性 | Git MCP | Claude Code 内置 Bash |
|------|---------|----------------------|
| 操作方式 | 专用工具 | Shell 命令 |
| 错误处理 | 结构化返回 | 需解析输出 |
| 安全性 | 更高（受限操作） | 完全 Shell 权限 |
| 功能范围 | 常用 Git 操作 | 所有 Git 命令 |

### 选择建议

- **简单操作**（状态、日志、提交）→ Git MCP 更方便
- **复杂操作**（rebase、cherry-pick）→ 直接用 Bash 更灵活

## 注意事项

- 需要在 Git 仓库目录下使用
- 推送操作需要配置好远程仓库和认证
- 重启 Claude Code 后配置生效

## 相关资源

- [Git MCP Server 源码](https://github.com/modelcontextprotocol/servers/tree/main/src/git)
- [MCP 协议](https://modelcontextprotocol.io)
- [Git 官方文档](https://git-scm.com/doc)
