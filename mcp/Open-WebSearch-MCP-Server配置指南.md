# Open-WebSearch MCP Server 配置指南

## 简介

Open-WebSearch 是一个多引擎 Web 搜索 MCP 服务器，无需 API Key，支持 Bing、DuckDuckGo、Exa、Brave、百度、CSDN、掘金、Startpage 等搜索引擎，同时支持抓取 CSDN、掘金、GitHub README 和通用网页内容。

## 前置条件

- Node.js (v18+) 和 npx
- 网络连接

## 功能列表

| 工具 | 说明 |
|------|------|
| `search` | 多引擎网页搜索，返回标题、URL、描述 |
| `fetchCsdnArticle` | 抓取 CSDN 博客文章完整内容 |
| `fetchJuejinArticle` | 抓取掘金文章完整内容 |
| `fetchGithubReadme` | 获取 GitHub 仓库 README 内容 |
| `fetchWebContent` | 抓取通用 HTTP(S) 页面 / Markdown 内容 |

支持的搜索引擎：`bing`、`duckduckgo`、`exa`、`brave`、`baidu`、`csdn`、`juejin`、`startpage`

## 配置方式

### 方式一：全局配置（推荐）

编辑 `~/.claude/settings.json`，在 `mcpServers` 中添加：

```json
{
  "mcpServers": {
    "web-search": {
      "command": "npx",
      "args": [
        "-y",
        "open-websearch@latest"
      ],
      "env": {
        "MODE": "stdio",
        "DEFAULT_SEARCH_ENGINE": "duckduckgo",
        "ALLOWED_SEARCH_ENGINES": "duckduckgo,bing,exa,brave"
      }
    }
  }
}
```

### 方式二：项目级配置

在项目根目录创建 `.claude/mcp.json`：

```json
{
  "mcpServers": {
    "web-search": {
      "command": "npx",
      "args": [
        "-y",
        "open-websearch@latest"
      ],
      "env": {
        "MODE": "stdio",
        "DEFAULT_SEARCH_ENGINE": "duckduckgo",
        "ALLOWED_SEARCH_ENGINES": "duckduckgo,bing,exa,brave"
      }
    }
  }
}
```

## 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MODE` | `both` | 服务器模式：`stdio`（MCP 推荐）、`http`、`both` |
| `DEFAULT_SEARCH_ENGINE` | `bing` | 默认搜索引擎 |
| `ALLOWED_SEARCH_ENGINES` | 空（全部可用） | 限制可用的搜索引擎，逗号分隔 |
| `USE_PROXY` | `false` | 是否启用 HTTP 代理 |
| `PROXY_URL` | `http://127.0.0.1:7890` | 代理服务器地址 |
| `SEARCH_MODE` | `auto` | 搜索策略：`request`、`auto`、`playwright` |

## 代理配置（可选）

如果某些搜索引擎在你的网络环境下不可用，可以配置代理：

```json
{
  "mcpServers": {
    "web-search": {
      "command": "npx",
      "args": [
        "-y",
        "open-websearch@latest"
      ],
      "env": {
        "MODE": "stdio",
        "DEFAULT_SEARCH_ENGINE": "duckduckgo",
        "USE_PROXY": "true",
        "PROXY_URL": "http://127.0.0.1:7890"
      }
    }
  }
}
```

## 使用示例

配置完成后，重启 Claude Code，即可在对话中使用：

```
搜索 "Claude Code MCP 最佳实践"
```

```
帮我搜索一下 Playwright 和 Puppeteer 的区别
```

```
抓取这篇文章的完整内容 https://blog.csdn.net/xxx/article/details/xxx
```

```
获取这个 GitHub 仓库的 README https://github.com/anthropics/claude-code
```

## 注意事项

- 首次运行会自动下载依赖，可能需要几分钟
- 搜索结果依赖各引擎的 HTML 结构，引擎更新时可能暂时失效
- 短时间大量搜索可能触发频率限制
- 该工具仅供个人使用，请遵守各搜索引擎的服务条款

## 相关资源

- [Open-WebSearch 源码](https://github.com/Aas-ee/open-webSearch)
- [MCP 协议](https://modelcontextprotocol.io)
