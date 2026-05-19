# 知乎搜索 MCP 接入指南

## 概述

知乎搜索 MCP 通过 MCP over SSE 协议提供知乎站内搜索能力，适合接入支持 MCP 的 Agent、助手或工作流系统。

当前服务仅提供**工具能力**，不提供资源（resources）与提示词（prompts）能力。

## 接口信息

| 说明 | 值 |
|------|-----|
| SSE URL | `https://developer.zhihu.com/api/mcp/zhihu_search/v1/sse` |
| Message URL | `https://developer.zhihu.com/api/mcp/zhihu_search/v1/message` |
| 传输方式 | MCP over SSE |
| 工具名 | `zhihu_search` |

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

知乎搜索每日调用额度为 **10 次**（试用用户），实名认证后可提升至 **1000 次**。

![知乎MCP额度](知乎额度.png)

- API Token 管理：https://developer.zhihu.com/profile
- 知乎数据开发平台文档中心：https://developer.zhihu.com/docs?key=authorization

## 工具定义

### zhihu_search

**入参：**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | String | 是 | 搜索关键词，长度 2-100 个字符 |
| count | Number | 否 | 返回条数，取值范围 1-10，默认 10 |

**返回：**

工具调用结果为 text 类型内容，正文为面向大模型消费的结构化文本（XML 格式）。

返回示例：

```xml
<zhihu_search query="RAG">
<search_item title="RAG 评测方法综述" content_type="Article" url="https://..." author_name="张三" author_avatar="https://..." author_badge_text="" edit_time="2025-03-01 10:00:00 +0000 UTC" authority_level="2" ranking_score="0.9800">
本文介绍了主流 RAG 评测框架，包括 RAGAS、TruLens ...
</search_item>
</zhihu_search>
```

> 返回值外层是 MCP text 类型，文本内容为 XML。建议将整段 XML 原样交给模型消费，不建议自行裁剪字段。

## 接入流程

### 1. 建立 SSE 连接

```bash
curl -N 'https://developer.zhihu.com/api/mcp/zhihu_search/v1/sse' \
  -H 'Authorization: Bearer <your_access_secret>' \
  -H 'Accept: text/event-stream'
```

服务端返回 `endpoint` 事件：

```
event: endpoint
data: /api/mcp/zhihu_search/v1/message?sessionId=xxx
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
      "name": "zhihu_search",
      "arguments": {
        "query": "RAG",
        "count": 5
      }
    }
  }'
```

SSE 通道返回响应：

```
event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"<zhihu_search query=\"RAG\">..."}]}}
```

## Claude Code 配置

在 `~/.claude/settings.json` 的 `mcpServers` 中添加：

```json
"zhihu-search": {
  "url": "https://developer.zhihu.com/api/mcp/zhihu_search/v1/sse",
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

## 搜索示例：Claude Code MCP

通过知乎搜索 MCP 搜索「Claude Code MCP」的结果（2026-05-19）：

### 1. 一个神级 Claude Code 画图插件,开源了!
- **作者**：GitHub Daily
- **时间**：2026-05-11
- **链接**：https://zhuanlan.zhihu.com/p/2037129749403840662
- **简介**：drawio-mcp 项目，让 Claude 直接生成原生 draw.io 图表，支持在聊天窗口中交互式渲染，内置一万多个形状搜索能力。

### 2. 从零搭建 AI 因子挖掘系统:QuantGPT + Claude Code + DeepSeek 实操指南
- **作者**：QuantGPT
- **时间**：2026-05-07
- **链接**：https://zhuanlan.zhihu.com/p/2035301907799986501
- **简介**：利用 Claude Code + DeepSeek 搭建全自动因子挖掘循环，支持设计→回测→评分→诊断→改进的 Agent 研究流程。

### 3. 读完 Claude Code 源码才发现:Skills、MCP、Rules 的区别,远没有你想的那么大
- **作者**：百度Geek说
- **时间**：2026-04-17
- **链接**：https://zhuanlan.zhihu.com/p/2028415894259286896
- **简介**：从源码层面拆解 Rules、MCP、Skills 的底层实现，揭示三者本质区别在于信息在 API 请求中的位置不同。

### 4. Claude Code + Seedance MCP: 命令行AI舞蹈视频生成的潜力
- **作者**：崔庆才丨静觅
- **时间**：2026-03-24
- **链接**：https://zhuanlan.zhihu.com/p/2019822088903488871
- **简介**：结合 Claude Code 和字节跳动 Seedance MCP，从命令行直接生成舞蹈视频的实践。

### 5. 最适合新手的 Claude Code、MCP、Skills 全套教程
- **作者**：熊猫Jay
- **时间**：2026-02-11
- **链接**：https://zhuanlan.zhihu.com/p/2004938127299613030
- **简介**：从 Cursor 迁移到 Claude Code 的完整经历，包含新手上手、踩坑总结和 CC Switch 模型切换工具介绍。
