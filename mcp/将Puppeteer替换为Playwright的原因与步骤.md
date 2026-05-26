# 将 Puppeteer 替换为 Playwright：原因与步骤

## 为什么要替换？

### 1. 功能与兼容性

| 对比项 | Puppeteer | Playwright |
|--------|-----------|------------|
| 浏览器支持 | 仅 Chrome/Chromium | Chrome、Firefox、WebKit |
| 跨平台 | 主要针对 Chrome | 三引擎全平台覆盖 |
| 移动端模拟 | 基础支持 | 更丰富的设备模拟 |
| 网络拦截 | 有限 | 完整的路由拦截能力 |

### 2. API 设计

- **自动等待**：Playwright 的所有操作都会自动等待元素就绪，减少 flaky 问题
- **多标签页/上下文**：原生支持 Browser Context 隔离，更适合复杂场景
- **内置断言**：Playwright Test 提供丰富的断言库
- **Codegen 工具**：可录制操作自动生成代码，调试更直观

### 3. 社区与维护

- Playwright 由微软维护，更新频率高，社区活跃
- Puppeteer 由 Google 维护，近年来更新节奏放缓
- Playwright 的文档和示例更加完善

### 4. MCP 生态

- `@playwright/mcp` 是官方推荐的 Playwright MCP 包
- Playwright MCP Server 提供了与 Puppeteer 版本对等的功能，且持续更新
- 更好的 TypeScript 支持和类型定义

## 具体替换步骤

### 第一步：确认当前配置

检查你的 MCP 配置文件位置：

```bash
# 全局配置
cat ~/.claude/settings.json

# 项目级配置
cat .claude/mcp.json
```

### 第二步：移除 Puppeteer 配置

在配置文件的 `mcpServers` 中，删除 `puppeteer` 相关配置：

```json
// 删除这部分
"puppeteer": {
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-puppeteer"
  ]
}
```

### 第三步：添加 Playwright 配置

在 `mcpServers` 中添加 `playwright` 配置：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@playwright/mcp"
      ]
    }
  }
}
```

完整的 `~/.claude/settings.json` 示例：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@playwright/mcp"
      ]
    }
  }
}
```

### 第四步：重启 Claude Code

配置修改后需要重启 Claude Code 使配置生效：

```bash
# 退出当前会话后重新启动
claude
```

### 第五步：验证配置

在 Claude Code 中测试基本功能：

```
打开 https://example.com 并截图
```

## 功能对照表

| Puppeteer 工具 | Playwright 对应工具 |
|----------------|---------------------|
| `puppeteer_navigate` | `playwright_navigate` |
| `puppeteer_screenshot` | `playwright_screenshot` |
| `puppeteer_click` | `playwright_click` |
| `puppeteer_fill` | `playwright_fill` |
| `puppeteer_select` | `playwright_select` |
| `puppeteer_hover` | `playwright_hover` |
| `puppeteer_evaluate` | `playwright_evaluate` |

## 注意事项

- Playwright 首次运行会自动下载浏览器，可能需要几分钟
- 如果网络不稳定，可以提前设置镜像源：
  ```bash
  export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
  ```
- 截图保存路径和临时文件处理方式与 Puppeteer 版本一致
- 某些网站的反爬机制在 Playwright 下可能表现不同，按需调整

## 相关资源

- [Playwright MCP Server 源码](https://github.com/microsoft/playwright-mcp)
- [Playwright 官方文档](https://playwright.dev/)
- [MCP 协议](https://modelcontextprotocol.io)
