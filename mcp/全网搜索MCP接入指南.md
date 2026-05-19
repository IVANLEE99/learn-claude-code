# 全网搜索 MCP 接入指南

## 概述

全网搜索 MCP 通过 MCP over SSE 协议提供全网搜索能力，适合接入支持 MCP 的 Agent、助手或工作流系统。

当前服务仅提供**工具能力**，不提供资源（resources）与提示词（prompts）能力。

> 全网搜索适合做信息补充与外部参考检索，若仅需知乎站内结果，建议优先使用知乎搜索 MCP。

## 接口信息

| 说明 | 值 |
|------|-----|
| SSE URL | `https://developer.zhihu.com/api/mcp/global_search/v1/sse` |
| Message URL | `https://developer.zhihu.com/api/mcp/global_search/v1/message` |
| 传输方式 | MCP over SSE |
| 工具名 | `global_search` |

**流程说明：**

1. 客户端先连接 SSE 端点
2. 服务端通过 `endpoint` 事件返回实际可用的 message 地址（带 sessionId）
3. 后续 `initialize`、`tools/list`、`tools/call` 请求均发送到该 message 地址

## 鉴权

请求头：

```
Authorization: Bearer <your_access_secret>
```

> 建议在 SSE 连接和后续 message 请求中均携带同一份鉴权信息。

## 额度说明

全网搜索每日调用额度为 **10 次**（试用用户），实名认证后可提升至 **1000 次**。

![知乎MCP额度](知乎额度.png)

- API Token 管理：https://developer.zhihu.com/profile
- 知乎数据开发平台文档中心：https://developer.zhihu.com/docs?key=authorization

## 工具定义

### global_search

**入参：**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | String | 是 | 搜索关键词，长度 2-100 个字符 |
| count | Number | 否 | 返回条数，取值范围 1-20，默认 10 |

**返回：**

工具调用结果为 text 类型内容，正文为面向大模型消费的结构化文本（XML 格式）。

返回示例：

```xml
<global_search query="人工智能">
<search_item title="人工智能发展趋势与展望" content_type="Article" url="https://..." author_name="张三" author_avatar="https://..." author_badge_text="" edit_time="2025-03-01 10:00:00 +0000 UTC" authority_level="2" ranking_score="0.9800">
近年来，人工智能（AI）的发展速度令人瞩目 ...
</search_item>
</global_search>
```

> 返回值外层是 MCP text 类型，文本内容为 XML。建议将整段 XML 原样交给模型消费，不建议自行裁剪字段。

## 接入流程

### 1. 建立 SSE 连接

```bash
curl -N 'https://developer.zhihu.com/api/mcp/global_search/v1/sse' \
  -H 'Authorization: Bearer <your_access_secret>' \
  -H 'Accept: text/event-stream'
```

服务端返回 `endpoint` 事件：

```
event: endpoint
data: /api/mcp/global_search/v1/message?sessionId=xxx
```

### 2. 初始化 MCP 会话

将上一步拿到的 message 地址记为 `MESSAGE_URL`。

```bash
curl -X POST "$MESSAGE_URL" \
  -H 'Authorization: Bearer <your_access_secret>' \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "clientInfo": {
        "name": "demo-client",
        "version": "1.0.0"
      },
      "capabilities": {}
    }
  }'
```

> message 端点通常先返回 HTTP 202 Accepted，实际 JSON-RPC 响应通过 SSE 通道异步返回。

### 3. 获取工具列表

```bash
curl -X POST "$MESSAGE_URL" \
  -H 'Authorization: Bearer <your_access_secret>' \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'
```

### 4. 调用搜索工具

```bash
curl -X POST "$MESSAGE_URL" \
  -H 'Authorization: Bearer <your_access_secret>' \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "global_search",
      "arguments": {
        "query": "人工智能",
        "count": 5
      }
    }
  }'
```

SSE 通道返回响应：

```
event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"<global_search query=\"人工智能\">..."}]}}
```

## Claude Code 配置

在 `~/.claude/settings.json` 的 `mcpServers` 中添加：

```json
"global-search": {
  "url": "https://developer.zhihu.com/api/mcp/global_search/v1/sse",
  "headers": {
    "Authorization": "Bearer <your_access_secret>"
  }
}
```

配置完成后重启 Claude Code 即可使用。

## 注意事项

1. 该服务采用标准 MCP 工具调用模式，推荐直接使用现成 MCP Client 接入
2. `tools/call` 的结果通过已建立的 SSE 通道返回，而非直接同步返回在 POST 响应体中
3. `query` 建议尽量具体，以获得更稳定的搜索结果
4. 返回的 XML 建议原样交给大模型消费，不建议自行裁剪字段
5. 全网搜索适合做信息补充与外部参考检索，若仅需知乎站内结果，建议优先使用知乎搜索 MCP

## 搜索示例：Claude Code MCP

通过全网搜索 MCP 搜索「Claude Code MCP」的结果（2026-05-19）：

### 1. Claude Code 实践指南(一):开始第一次对话
- **作者**：P2Tree
- **时间**：2026-05-15
- **链接**：https://zhuanlan.zhihu.com/p/2032855948788749921
- **简介**：Claude Code 实践指南开篇，介绍 Claude 与 Claude Code 的区别，以及与其他 AI 编程工具（Copilot、Cursor、Codex 等）的对比。

### 2. 别等踩坑才装! UI设计必备的5个Claude MCP
- **来源**：优设网
- **时间**：2026-05-19
- **链接**：https://www.uisdc.com/group/670419.html
- **简介**：介绍 Figma MCP、AIDesigner MCP、AccessLint MCP、Playwright MCP、Notion MCP 五个设计与开发必备的 MCP 工具。

### 3. 一个神级 Claude Code 画图插件,开源了!
- **作者**：GitHub Daily
- **时间**：2026-05-11
- **链接**：https://zhuanlan.zhihu.com/p/2037129749403840662
- **简介**：drawio-mcp 项目，让 Claude 直接生成原生 draw.io 图表，支持聊天窗口内交互式渲染，内置一万多个形状搜索。

### 4. 33k Star 的 Claude How To: 一份适合系统学习 Claude Code 的开源指南
- **作者**：yuan（浙江大学 控制科学与工程硕士）
- **时间**：2026-05-18
- **链接**：https://zhuanlan.zhihu.com/p/2039844439842088273
- **简介**：系统学习 Claude Code 的开源指南，涵盖 Skills、Subagents、MCP、Hooks 等核心能力的详解与配置示例。

### 5. 从零搭建 AI 因子挖掘系统: QuantGPT + Claude Code + DeepSeek 实操指南
- **作者**：QuantGPT
- **时间**：2026-05-07
- **链接**：https://zhuanlan.zhihu.com/p/2035301907799986501
- **简介**：利用 Claude Code + DeepSeek 搭建全自动因子挖掘循环，支持设计→回测→评分→诊断→改进的 Agent 研究流程。
