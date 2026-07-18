# Claude Code `/help` 命令说明（中文）

> 下面是对 `/help` 常见内容的中文整理，便于快速查阅。

## GitHub Pages

- 文档首页：<https://ivanlee99.github.io/learn-claude-code/>
- 站内阅读器（README）：<https://ivanlee99.github.io/learn-claude-code/viewer.html?doc=readme>
- 模型选择记录：<https://ivanlee99.github.io/learn-claude-code/viewer.html?doc=models>


## 基础命令

- `/help`：查看可用命令列表。
- `/clear`：清除当前会话历史，开始新的上下文。
- `/compact [instructions]`：压缩当前对话为摘要并继续会话，可选参数用于指定压缩重点。
- `/status`：查看当前会话状态（目录、模型、记忆加载等）。
- `/cost`：查看 token 使用量与费用估算。

## 项目与记忆

- `/add-dir <目录路径>`：添加/切换工作目录。
- `/init`：扫描当前项目并生成 `CLAUDE.md`（项目记忆指南）。
- `/memory`：打开并编辑记忆文件（如 `CLAUDE.md`）。

## 配置与模型

- `/config`：查看或修改 Claude Code 配置。
- `/model [model_name]`：查看或切换模型版本。
- `/doctor`：执行环境健康检查，排查依赖/权限/连接问题。

## IDE 集成

- `/ide`：连接到 IDE（如 VS Code / Windsurf / Cursor / JetBrains）。

---

## Git Submodules

本项目包含以下 submodule：

| 子模块 | 仓库地址 |
|--------|---------|
| `ai-concept-bank` | [IVANLEE99/ai-concept-bank](https://github.com/IVANLEE99/ai-concept-bank) |

### Clone 时拉取 submodule

```bash
git clone --recurse-submodules git@github.com:IVANLEE99/learn-claude-code.git
```

### 已有仓库补拉 submodule

```bash
git submodule update --init --recursive
```

### 更新 submodule 到远程最新

```bash
git submodule update --remote
```

---

如果你希望，我还可以把这份 `readme.md` 改成**表格版**或补充为”命令 + 示例 + 适用场景”的速查手册。