# 知乎热榜 MCP 接入指南

## 概述

知乎热榜 MCP 通过 MCP over SSE 协议提供知乎热榜能力，适合接入支持 MCP 的 Agent、助手或工作流系统。

当前服务仅提供**工具能力**，不提供资源（resources）与提示词（prompts）能力。

## 接口信息

| 说明 | 值 |
|------|-----|
| SSE URL | `https://developer.zhihu.com/api/mcp/hot_list/v1/sse` |
| Message URL | `https://developer.zhihu.com/api/mcp/hot_list/v1/message` |
| 传输方式 | MCP over SSE |
| 工具名 | `hot_list` |

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

热榜每日调用额度为 **2 次**（试用用户），实名认证后可提升至 **1000 次**。

![知乎MCP额度](知乎额度.png)

- API Token 管理：https://developer.zhihu.com/profile
- 知乎数据开发平台文档中心：https://developer.zhihu.com/docs?key=authorization

## 工具定义

### hot_list

**入参：**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | Number | 否 | 返回条数，取值范围 1-30，默认 30 |

**返回：**

工具调用结果为 text 类型内容，正文为面向大模型消费的结构化文本（XML 格式）。

返回示例：

```xml
<hot_list limit="30" total="3">
  <item rank="1">
    <title>如何看待当前 AI Agent 的发展趋势？</title>
    <url>https://www.zhihu.com/question/123456789</url>
    <thumbnail_url>https://pic1.zhimg.com/v2-xxx.jpg</thumbnail_url>
    <summary>这是该问题的内容摘要</summary>
  </item>
</hot_list>
```

> `thumbnail_url` 和 `summary` 始终返回，无数据时为空。建议将整段 XML 原样交给模型消费，不建议自行裁剪字段。

## 接入流程

### 1. 建立 SSE 连接

```bash
curl -N 'https://developer.zhihu.com/api/mcp/hot_list/v1/sse' \
  -H 'Authorization: Bearer <your_access_secret>' \
  -H 'Accept: text/event-stream'
```

### 2. 初始化 MCP 会话

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
      "clientInfo": {"name": "demo-client", "version": "1.0.0"},
      "capabilities": {}
    }
  }'
```

### 3. 调用热榜工具

```bash
curl -X POST "$MESSAGE_URL" \
  -H 'Authorization: Bearer <your_access_secret>' \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "hot_list",
      "arguments": {"limit": 10}
    }
  }'
```

## Claude Code 配置

在 `~/.claude/settings.json` 的 `mcpServers` 中添加：

```json
"hot-list": {
  "url": "https://developer.zhihu.com/api/mcp/hot_list/v1/sse",
  "headers": {
    "Authorization": "Bearer <your_access_secret>"
  }
}
```

配置完成后重启 Claude Code 即可使用。

## 注意事项

1. 该服务采用标准 MCP 工具调用模式，推荐直接使用现成 MCP Client 接入
2. `tools/call` 的结果通过已建立的 SSE 通道返回，而非直接同步返回在 POST 响应体中
3. 热榜结果偏实时性，列表顺序和内容会随时间变化

## 热榜数据（2026-05-19）

| 排名 | 标题 | 链接 |
|------|------|------|
| 1 | 洁丽雅晒报案回执，辟谣「私生子」「姐妹关系」等谣言，能平息此次风波吗？ | [链接](https://www.zhihu.com/question/2039822539430388810) |
| 2 | 普京即将启程访华，俄罗斯远东地区要真正融入「大远东」经济圈，最紧迫的突破口在哪里？ | [链接](https://www.zhihu.com/question/2039719852647113704) |
| 3 | 吃自助餐真的能吃回本吗? | [链接](https://www.zhihu.com/question/629054270) |
| 4 | 如何看待 2026 年 5 月 18 日《给阿嬷的情书》排片占比大幅提升至 45% 左右？ | [链接](https://www.zhihu.com/question/2039304488998152020) |
| 5 | 如何评价上海交大通报给予樊同学严重警告处分？ | [链接](https://www.zhihu.com/question/2039769972348605747) |
| 6 | 家长哭诉女儿遭校园欺凌，沈奕斐称是家长陷入「受害者思维」导致孩子认知扭曲，你认同吗？ | [链接](https://www.zhihu.com/question/2039711643739713761) |
| 7 | 当你吃着白馍夹着满满的肉时，是否会好奇为啥叫「肉夹馍」而不叫「馍夹肉」？ | [链接](https://www.zhihu.com/question/2027025332805407760) |
| 8 | 没考上大专，18岁在深圳做流水线工人，真的很迷茫，有没有过来人的真心建议？ | [链接](https://www.zhihu.com/question/2029672850043286403) |
| 9 | 新加坡总理要求民众「做好抗通胀准备」，2026年全球通胀趋势一旦确立，普通人能如何抗通胀呢？ | [链接](https://www.zhihu.com/question/2039464484771779756) |
| 10 | 如何看待多家银行关停独立信用卡 App？这会带来哪些影响？ | [链接](https://www.zhihu.com/question/2039616106520950320) |
