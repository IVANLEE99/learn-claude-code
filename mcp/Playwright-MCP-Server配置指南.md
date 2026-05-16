# Playwright MCP Server 配置指南

## 简介

Playwright MCP Server 是 Anthropic 官方提供的浏览器自动化 MCP 服务器，基于 Playwright（支持 Chromium、Firefox、WebKit），让 Claude Code 可以直接操控浏览器——导航网页、截图、点击、填表、执行 JavaScript 等。

## 前置条件

- Node.js (v18+) 和 npx
- 网络连接（首次运行时自动下载 Playwright 浏览器）

## 功能列表

| 工具 | 说明 |
|------|------|
| `playwright_navigate` | 导航到指定 URL |
| `playwright_screenshot` | 页面截图 |
| `playwright_click` | 点击页面元素（CSS 选择器） |
| `playwright_fill` | 填写输入框 |
| `playwright_select` | 选择下拉框选项 |
| `playwright_hover` | 悬停在元素上 |
| `playwright_evaluate` | 在浏览器中执行 JavaScript |

## 配置方式

### 方式一：全局配置（推荐）

编辑 `~/.claude/settings.json`，在 `mcpServers` 中添加：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic-ai/mcp-server-playwright"
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
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic-ai/mcp-server-playwright"
      ]
    }
  }
}
```

## 使用示例

配置完成后，重启 Claude Code，即可在对话中使用：

```
打开 https://github.com 并截图
```

```
帮我打开百度，搜索 "Claude Code"，然后截图
```

```
访问 https://httpbin.org/forms/post，填写表单并提交
```

```
打开网页 https://example.com，执行 JS 获取页面标题
```

## 注意事项

- 首次运行会自动下载 Chromium 浏览器，可能需要几分钟
- 如需使用其他浏览器（Firefox/WebKit），需手动安装：
  ```bash
  npx playwright install firefox
  npx playwright install webkit
  ```
- 截图保存在临时目录，Claude 会自动读取并展示
- 执行 JavaScript 时注意安全，避免访问不可信的页面
- 某些网站可能有反爬机制，导致自动化操作失败

## 安全提醒

- 不要在包含敏感信息的页面上执行自动化操作
- 避免在需要登录的页面上保存凭证
- 执行 JavaScript 前确认页面内容安全

## 相关资源

- [Playwright MCP Server 源码](https://github.com/anthropics/mcp-server-playwright)
- [Playwright 官方文档](https://playwright.dev/)
- [MCP 协议](https://modelcontextprotocol.io)
