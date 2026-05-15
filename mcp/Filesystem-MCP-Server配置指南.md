# Filesystem MCP Server 配置指南

## 简介

Filesystem MCP Server 是 Anthropic 官方提供的文件系统访问 MCP 服务器，让 Claude Code 可以直接操作本地文件系统——读取、写入、搜索、移动文件和目录。

## 前置条件

- Node.js (v18+) 和 npx

## 功能列表

| 工具 | 说明 |
|------|------|
| `read_file` | 读取文件内容 |
| `write_file` | 写入文件内容 |
| `create_directory` | 创建目录 |
| `list_directory` | 列出目录内容 |
| `move_file` | 移动/重命名文件 |
| `search_files` | 搜索文件（支持正则） |
| `get_file_info` | 获取文件信息（大小、时间等） |
| `list_allowed_directories` | 列出允许访问的目录 |

## 配置方式

### 方式一：全局配置（推荐）

编辑 `~/.claude/settings.json`，在 `mcpServers` 中添加：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/你的用户名"
      ]
    }
  }
}
```

**重要**：最后一个参数是允许访问的目录路径，可以指定多个：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/你的用户名/Documents",
        "/Users/你的用户名/Projects"
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
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/directory"
      ]
    }
  }
}
```

## 安全机制

Filesystem MCP Server 有严格的安全限制：

- **只允许访问指定的目录**（通过 args 参数配置）
- 无法访问配置目录之外的文件
- 无法执行系统命令
- 无法修改系统文件

### 配置建议

| 场景 | 建议目录 |
|------|----------|
| 个人使用 | `/Users/你的用户名` |
| 项目开发 | `/Users/你的用户名/Projects` |
| 文档管理 | `/Users/你的用户名/Documents` |
| 限定项目 | `/path/to/specific/project` |

## 使用示例

配置完成后，重启 Claude Code，即可在对话中使用：

```
读取 ~/Documents/notes.md 的内容
```

```
在 ~/Projects 下搜索所有 .vue 文件
```

```
创建 ~/Desktop/test.txt 文件，写入 "Hello World"
```

```
列出 ~/Documents 目录下的所有文件
```

```
将 ~/Desktop/old.txt 移动到 ~/Documents/new.txt
```

## 与 Claude Code 内置工具的区别

| 特性 | Filesystem MCP | Claude Code 内置 |
|------|----------------|------------------|
| 跨项目访问 | 支持（配置目录） | 仅当前项目 |
| 搜索文件 | 正则支持 | glob 模式 |
| 文件信息 | 详细（大小、时间） | 基本 |
| 安全限制 | 目录白名单 | 工作目录 |

## 注意事项

- 配置的目录路径必须是绝对路径
- 多个目录用多个 args 参数指定
- 重启 Claude Code 后配置生效
- 访问配置外的目录会被拒绝

## 相关资源

- [Filesystem MCP Server 源码](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- [MCP 协议](https://modelcontextprotocol.io)
