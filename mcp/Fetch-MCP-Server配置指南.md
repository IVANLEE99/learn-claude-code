# Fetch MCP Server 配置指南

## 简介

Fetch MCP Server 是 Anthropic 官方提供的网页抓取 MCP 服务器，让 Claude Code 可以直接获取网页内容——支持 HTML、Markdown、JSON 等格式，是轻量级的网页数据获取工具。

## 前置条件

- Node.js (v18+) 和 npx

## 与 Puppeteer 的区别

| 特性 | Fetch | Puppeteer |
|------|-------|-----------|
| 用途 | 网页内容抓取 | 浏览器自动化 |
| 速度 | 快（直接 HTTP 请求） | 慢（启动 Chrome） |
| JavaScript 渲染 | 不支持 | 支持 |
| 交互操作 | 不支持 | 支持（点击、填表等） |
| 截图 | 不支持 | 支持 |
| 资源占用 | 低 | 高 |

**选择建议**：
- 只需要读取网页内容 → 用 **Fetch**
- 需要交互操作、截图、JS 渲染 → 用 **Puppeteer**

## 功能

| 工具 | 说明 |
|------|------|
| `fetch` | 获取指定 URL 的内容 |

支持的格式：
- HTML → 自动转换为 Markdown
- JSON → 直接返回
- 纯文本 → 直接返回

## 配置方式

### 方式一：全局配置（推荐）

编辑 `~/.claude/settings.json`，在 `mcpServers` 中添加：

```json
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-fetch"
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
    "fetch": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-fetch"
      ]
    }
  }
}
```

## 使用示例

配置完成后，重启 Claude Code，即可在对话中使用：

```
获取 https://docs.anthropic.com/en/docs/claude-code 的内容
```

```
帮我抓取 https://api.github.com/repos/anthropics/claude-code 的 JSON 数据
```

```
获取 https://news.ycombinator.com 首页的标题列表
```

## 注意事项

- Fetch 只能获取静态内容，无法处理需要 JavaScript 渲染的页面
- 对于需要登录或复杂交互的网站，请使用 Puppeteer
- 部分网站可能拒绝非浏览器请求（User-Agent 检测）

## 相关资源

- [Fetch MCP Server 源码](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)
- [MCP 协议](https://modelcontextprotocol.io)
