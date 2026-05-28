# Chrome DevTools MCP Server 配置指南

## 简介

Chrome DevTools MCP Server（`chrome-devtools-mcp`）是 Google Chrome 团队官方维护的 MCP 服务器，让 Claude Code、Cursor、Copilot 等 AI 编程助手直接操控和检查实时 Chrome 浏览器。它基于 Chrome DevTools Protocol，提供**性能分析**、**网络调试**、**截图**、**自动化操作**等完整 DevTools 能力。npm 包由 [ChromeDevTools](https://github.com/ChromeDevTools) 组织维护。

**与 Playwright MCP 的区别**：Playwright MCP 侧重页面自动化（导航、点击、填表），而 Chrome DevTools MCP 额外提供**性能 Trace 录制与分析**、**Lighthouse 审计**、**网络请求检查**、**内存快照分析**、**控制台日志查看**等深度调试能力，更适合前端性能优化和 Bug 排查场景。

## 前置条件

- Node.js LTS 版本
- Google Chrome 最新稳定版
- npm / npx

## 功能列表

### 完整模式（43 个工具）

| 分类 | 工具 | 说明 |
|------|------|------|
| **输入自动化** | `click` | 点击页面元素 |
| | `dblClick` | 双击页面元素（`click` 的 `dblClick=true`） |
| | `drag` | 拖拽元素到另一个元素 |
| | `fill` | 填写输入框、文本域或选择下拉框 |
| | `fill_form` | 一次性填写多个表单元素（推荐替代多次 `fill`） |
| | `handle_dialog` | 处理浏览器弹窗（alert/confirm/prompt） |
| | `hover` | 悬停在元素上 |
| | `press_key` | 按键或组合键（支持 Ctrl+A、Ctrl+Shift+R 等） |
| | `type_text` | 模拟键盘输入文本 |
| | `upload_file` | 上传文件到 file input 元素 |
| | `click_at` | 按坐标点击（需 `--experimentalVision=true`） |
| **导航自动化** | `navigate_page` | 导航到 URL、前进、后退或刷新 |
| | `new_page` | 打开新标签页加载 URL |
| | `close_page` | 关闭指定标签页 |
| | `list_pages` | 列出所有打开的标签页 |
| | `select_page` | 切换当前活动标签页 |
| | `wait_for` | 等待页面上出现指定文本 |
| **设备模拟** | `emulate` | 模拟深色/浅色模式、地理位置、网络条件、UA、视口等 |
| | `resize_page` | 调整页面窗口大小 |
| **性能分析** | `performance_start_trace` | 开始录制性能 Trace（Core Web Vitals 等） |
| | `performance_stop_trace` | 停止性能 Trace 录制 |
| | `performance_analyze_insight` | 获取性能洞察的详细分析 |
| **网络调试** | `list_network_requests` | 列出当前页面所有网络请求 |
| | `get_network_request` | 获取单个网络请求的详细信息 |
| **调试工具** | `take_snapshot` | 基于 a11y 树获取页面文本快照（含元素 uid） |
| | `take_screenshot` | 截取页面或元素截图 |
| | `evaluate_script` | 在页面中执行 JavaScript |
| | `list_console_messages` | 列出所有控制台日志 |
| | `get_console_message` | 获取单条控制台日志详情 |
| | `lighthouse_audit` | 运行 Lighthouse 审计（无障碍、SEO、最佳实践） |
| | `screencast_start` | 开始录制页面视频（需 `--experimentalScreencast=true`） |
| | `screencast_stop` | 停止录制 |
| **内存分析** | `take_heapsnapshot` | 捕获堆快照（需 `--experimentalMemory=true`） |
| | `get_heapsnapshot_details` | 获取堆快照详细统计 |
| | `get_heapsnapshot_class_nodes` | 按类名获取实例列表 |
| | `get_heapsnapshot_retainers` | 获取节点的保留链 |
| | `get_heapsnapshot_summary` | 获取堆快照摘要 |
| **扩展管理** | `install_extension` | 安装 Chrome 扩展（需 `--categoryExtensions`） |
| | `list_extensions` | 列出已安装扩展 |
| | `reload_extension` | 重载扩展 |
| | `trigger_extension_action` | 触发扩展默认操作 |
| | `uninstall_extension` | 卸载扩展 |
| **第三方工具** | `list_3p_developer_tools` | 列出页面暴露的第三方开发者工具 |
| | `execute_3p_developer_tool` | 执行第三方开发者工具 |
| **WebMCP** | `list_webmcp_tools` | 列出页面暴露的 WebMCP 工具 |
| | `execute_webmcp_tool` | 执行 WebMCP 工具 |

### 精简模式（3 个工具）

| 工具 | 说明 |
|------|------|
| `navigate` | 导航到指定 URL |
| `evaluate` | 执行 JavaScript |
| `screenshot` | 截图 |

## 配置方式

### Claude Code（CLI 方式，推荐）

```bash
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

### Claude Code（插件方式，MCP + Skills）

```bash
/plugin marketplace add ChromeDevTools/chrome-devtools-mcp
/plugin install chrome-devtools-mcp@chrome-devtools-plugins
```

重启 Claude Code 后生效，可用 `/skills` 检查。

### VS Code / Copilot

通过命令面板（`Cmd+Shift+P`）搜索 `Chat: Install Plugin From Source`，输入 `ChromeDevTools/chrome-devtools-mcp`。

或手动添加 MCP 配置：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

### Cursor

在 Cursor Settings → MCP → New MCP Server 中添加：

```json
{
  "command": "npx -y chrome-devtools-mcp@latest"
}
```

### 全局配置（适用于所有 MCP 客户端）

编辑 `~/.claude/settings.json`：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

### 精简模式配置

只需基本浏览器操作时使用精简模式，工具更少、启动更快：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--slim", "--headless"]
    }
  }
}
```

### 连接已有浏览器实例

如果 Chrome 已启动并开启了远程调试端口：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browser-url=http://127.0.0.1:9222"]
    }
  }
}
```

## 常用启动参数

| 参数 | 说明 |
|------|------|
| `--headless` | 无头模式运行浏览器 |
| `--slim` | 精简模式，仅加载 3 个基础工具 |
| `--browser-url=<url>` | 连接已有 Chrome 实例的调试端口 |
| `--no-usage-statistics` | 禁用使用统计收集 |
| `--no-performance-crux` | 禁用 CrUX 真实用户数据 |
| `--log-file=<path>` | 将日志输出到文件 |
| `--experimentalVision=true` | 启用视觉功能（坐标点击等） |
| `--experimentalScreencast=true` | 启用录屏功能 |
| `--experimentalMemory=true` | 启用内存分析功能 |
| `--categoryExtensions` | 启用扩展管理工具 |
| `--categoryExperimentalThirdParty` | 启用第三方开发者工具 |
| `--categoryExperimentalWebmcp` | 启用 WebMCP 工具 |

## 使用示例

配置完成后，重启 Claude Code，即可在对话中使用：

**性能分析**：
```
检查 https://developers.chrome.com 的性能
```

**页面截图与快照**：
```
打开 https://example.com 并截图
```

**表单自动化**：
```
打开登录页面，填写用户名和密码，点击登录按钮
```

**网络调试**：
```
打开某个页面，查看所有网络请求，找出加载失败的资源
```

**JavaScript 执行**：
```
在当前页面执行 JS 获取 document.title
```

**Lighthouse 审计**：
```
对当前页面运行 Lighthouse 审计（移动端模式）
```

**内存分析**：
```
捕获当前页面的堆快照并分析内存分布
```

## CLI 使用

`chrome-devtools-mcp` 也提供了实验性 CLI 接口，可直接在终端操控浏览器：

```bash
# 全局安装
npm i chrome-devtools-mcp@latest -g

# 检查状态
chrome-devtools status

# 导航到 URL
chrome-devtools navigate_page "https://google.com"

# 截图并保存
chrome-devtools take_screenshot --filePath screenshot.png

# 停止后台守护进程
chrome-devtools stop
```

CLI 默认以无头模式运行，后台守护进程会保持浏览器状态。

## 注意事项

- 首次启动会自动下载 Chrome for Testing，可能需要几分钟
- MCP 服务器**不会在连接时自动启动浏览器**，仅在调用需要浏览器的工具时才启动
- 浏览器内容会暴露给 MCP 客户端，**不要在包含敏感信息的页面上使用**
- 官方仅支持 Google Chrome 和 Chrome for Testing，其他 Chromium 浏览器不保证兼容
- 性能工具可能向 Google CrUX API 发送 Trace URL 以获取真实用户数据（可用 `--no-performance-crux` 禁用）
- 默认会收集使用统计（可用 `--no-usage-statistics` 禁用）

## 常见问题排查

| 问题 | 解决方案 |
|------|----------|
| `Error [ERR_MODULE_NOT_FOUND]` | 清除 npx 缓存：`rm -rf ~/.npm/_npx && npm cache clean --force` |
| `Target closed` 错误 | 关闭所有 Chrome 实例后重试，确保 Chrome 版本为最新稳定版 |
| macOS Web Bluetooth 崩溃 | 系统设置 → 隐私与安全 → 蓝牙，授予 MCP 客户端蓝牙权限 |
| Windows `Connection closed` | 将 `command` 改为 `cmd`，`args` 改为 `["/c", "npx", "-y", "chrome-devtools-mcp@latest"]` |
| WSL 无法启动 Chrome | 在 WSL 内安装 Chrome：`wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && sudo dpkg -i google-chrome-stable_current_amd64.deb` |
| 插件安装失败 | 配置 SSH 替代 HTTPS：`git config --global url."git@github.com:".insteadOf "https://github.com/"` |
| 调试模式 | `DEBUG=* npx chrome-devtools-mcp@latest --log-file=/path/to/log.log` |

## 设计原则

- **Agent 无关**：基于 MCP 标准，不锁定特定 LLM，注重互操作性
- **Token 优化**：返回语义化摘要而非大量 JSON（如 "LCP was 3.2s"）
- **小而确定的工具块**：提供可组合的基础工具（Click、Screenshot），而非魔法按钮
- **自愈错误**：返回可操作的错误信息，包含上下文和修复建议
- **渐进式复杂度**：默认简单，高级参数可选

## 相关资源

- [GitHub 仓库](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [工具参考文档](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/tool-reference.md)
- [CLI 文档](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/cli.md)
- [故障排查指南](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/troubleshooting.md)
- [设计原则](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/design-principles.md)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [MCP 协议](https://modelcontextprotocol.io)
