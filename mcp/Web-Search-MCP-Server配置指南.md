# Web Search MCP Server 配置指南

## 简介

Web Search MCP Server 是基于 `open-websearch` 的网页搜索 MCP 服务器，让 Claude Code 可以直接搜索互联网——支持 DuckDuckGo、Bing、Exa、Brave 等多个搜索引擎。

## 前置条件

- Node.js (v18+) 和 npx

## 支持的搜索引擎

| 引擎 | 特点 | 是否需要 API Key |
|------|------|------------------|
| DuckDuckGo | 默认引擎，隐私友好 | 不需要 |
| Bing | 微软搜索引擎 | 不需要 |
| Exa | AI 优化搜索 | 需要 |
| Brave | 隐私保护搜索 | 需要 |

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
        "ALLOWED_SEARCH_ENGINES": "duckduckgo,bing"
      }
    }
  }
}
```

## 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MODE` | 运行模式 | `stdio` |
| `DEFAULT_SEARCH_ENGINE` | 默认搜索引擎 | `duckduckgo` |
| `ALLOWED_SEARCH_ENGINES` | 允许使用的引擎（逗号分隔） | 全部 |

## 使用示例

配置完成后，重启 Claude Code，即可在对话中使用：

```
搜索 "Claude Code" 最新教程
```

```
用 Bing 搜索 React 18 新特性
```

```
搜索 MCP 协议相关文档
```

```
帮我搜索一下 Node.js 22 的新功能
```

## 与 Claude Code 内置 WebSearch 的区别

| 特性 | Web Search MCP | Claude Code 内置 |
|------|----------------|------------------|
| 搜索引擎 | 多个可选 | 固定 |
| 隐私控制 | 支持 DuckDuckGo | 无 |
| API Key | 大多不需要 | 不需要 |
| 自定义程度 | 高 | 低 |

## 注意事项

- DuckDuckGo 和 Bing 不需要 API Key，开箱即用
- Exa 和 Brave 需要配置 API Key（在 env 中添加 `EXA_API_KEY` 或 `BRAVE_API_KEY`）
- 部分地区可能需要代理访问某些搜索引擎
- 重启 Claude Code 后配置生效

## 相关资源

- [open-websearch 仓库](https://github.com/nicepkg/open-websearch)
- [MCP 协议](https://modelcontextprotocol.io)
