# Claude Code 模型选择记录

## 记录目的

整理本次会话中与 `/model` 相关的实际输出，便于后续查阅。

## 实际输出

```text
/model
Kept model as Sonnet 4.6 (default)
```

```text
/model GPT-5.4
Unable to validate model: Cannot read properties of undefined (reading 'input_tokens')
```

```text
/model gpt-5.4
Unable to validate model: Cannot read properties of undefined (reading 'input_tokens')
```

```text
/model
Set model to gpt-5.4
```

```text
/effort auto
Effort level set to auto
```

## 一页速查表

### 模型选择速查

| 模型 | 定位 | 优点 | 缺点 | 适用场景 |
| --- | --- | --- | --- | --- |
| Sonnet 4.6 | 日常默认 | 速度和质量均衡，适合大多数开发和文档工作 | 深度推理不如 Opus 强 | 日常改文档、改代码、解释项目 |
| Opus 4.6 | 强推理档 | 推理更强，适合复杂调试、多文件分析、系统设计 | 更慢，成本更高 | 难 bug、复杂重构、架构分析 |
| Haiku 4.5 | 轻量快速档 | 更快、更省，适合简单任务 | 复杂编码和深推理较弱 | 快速问答、摘要、简单改写 |
| gpt-5.4 | 当前会话中的自定义模型 | 当前会话里已可选，可能适合继续试用 | 非 Claude Code 默认官方模型，稳定性取决于兼容网关 | 已配置兼容网关时的自定义使用 |

### 推理强度速查

| 设置项 | 含义 | 特点 | 适用场景 |
| --- | --- | --- | --- |
| `/effort low` | 低推理强度 | 更快，思考更少 | 简单任务、追求速度 |
| `/effort medium` | 中等推理强度 | 速度和质量均衡 | 大多数日常任务 |
| `/effort high` | 高推理强度 | 更深推理，更稳 | 复杂分析、复杂问题排查 |
| `/effort max` | 更高推理强度 | 更强推理，通常只部分模型支持 | 很难的问题 |
| `/effort auto` | 自动推理强度 | 由当前模型自动决定 | 日常默认使用 |

### 本次会话状态速查

| 项目 | 当前记录 |
| --- | --- |
| 初始默认模型 | `Sonnet 4.6` |
| 当前会话模型 | `gpt-5.4` |
| 当前推理强度 | `auto` |
| 模型切换现象 | 先报校验失败，后显示已设置 |
| 当前判断 | 可能受兼容网关、会话状态或模型校验流程影响 |

### 最终推荐配置表

| 使用场景 | 推荐模型 | 推荐推理强度 | 推荐理由 |
| --- | --- | --- | --- |
| 日常写文档、改小内容 | Sonnet 4.6 | `auto` 或 `medium` | 最均衡，适合当前仓库的主流工作 |
| 解释项目、梳理结构 | Sonnet 4.6 | `auto` | 足够稳，也不容易过重 |
| 复杂问题排查 | Opus 4.6 | `high` | 更适合多文件分析和深推理 |
| 棘手 bug / 重构 | Opus 4.6 | `high` 或 `max` | 更适合高难度任务 |
| 快速问答 / 摘要 | Haiku 4.5 | `low` 或 `auto` | 更快更省 |
| 已接好兼容网关后试用 | gpt-5.4 | `auto` | 可以继续观察稳定性和工具兼容性 |

## 当前结论

- 初始默认模型为 `Sonnet 4.6`。
- 在本次会话中，直接切换到 `GPT-5.4` / `gpt-5.4` 时，曾出现模型校验失败。
- 随后再次查看模型时，当前会话显示模型已设置为 `gpt-5.4`。
- 当前推理强度已设置为 `auto`。
- 这说明当前环境里的模型识别结果可能和网关配置、会话状态或模型校验流程有关。

## 当前可参考的模型

在本次讨论里，Claude Code 中提到的官方 Claude 模型主要包括：

- `claude-sonnet-4-6`
- `claude-opus-4-6`
- `claude-sonnet-4-5-20250929`
- `claude-haiku-4-5-20251001`
- 以及文档中提到的 `Opus 4.5`

说明：

- `Sonnet 4.6` 适合作为日常默认模型。
- `Opus 4.6` 更适合复杂推理、复杂重构和棘手问题排查。
- `Haiku 4.5` 更适合轻量、快速、低成本任务。

## 各模型优缺点

### Sonnet 4.6

优点：
- 速度和质量比较均衡
- 适合大多数日常开发和文档工作
- 作为默认模型比较稳

缺点：
- 面对特别复杂的架构问题或深度推理任务，不如 Opus 强

### Opus 4.6

优点：
- 推理能力更强
- 更适合多文件分析、复杂调试和系统设计

缺点：
- 通常更慢
- 成本更高
- 对简单任务可能有些过重

### Haiku 4.5

优点：
- 更快
- 更省
- 适合轻量查询和简单改写

缺点：
- 复杂编码、深推理和大范围修改能力较弱

## 关于 gpt-5.4 的说明

### 是否可以直接使用

就原生能力而言，Claude Code 官方主要支持 Claude 系列模型。

因此：

- `gpt-5.4` 不是 Claude Code 默认内建的官方模型名
- 直接 `/model gpt-5.4` 是否成功，取决于当前环境是否配置了兼容网关或自定义模型映射

### 为什么会先报错，后又显示已设置

可能原因包括：

- 当前环境存在第三方兼容网关
- 模型校验与实际会话状态不完全一致
- 会话中模型元数据刷新存在差异
- 自定义模型通过网关暴露后，被当前会话识别

因此最终应以当前会话的实际 `/model` 输出为准。

## 自定义接入 gpt-5.4 的常见方式

如果要在 Claude Code 中接入类似 `gpt-5.4` 的非 Claude 模型，通常不是原生直连，而是通过兼容网关。

常见配置思路：

```bash
export ANTHROPIC_BASE_URL="https://你的-anthropic-compatible-网关"
export ANTHROPIC_AUTH_TOKEN="你的网关密钥"
export ANTHROPIC_MODEL="gpt-5.4"
```

核心前提：

- 网关必须是 **Anthropic-compatible**
- 不只是普通的 OpenAI-compatible
- 网关需要正确暴露模型 ID，并兼容 Claude Code 所需的模型校验和接口行为

## 设置模型推理强度

Claude Code 中，模型选择和推理强度是两回事：

- `/model`：选择模型档位，例如 `haiku`、`sonnet`、`opus`
- `/effort`：设置当前模型的推理强度

常用命令：

```text
/effort low
/effort medium
/effort high
/effort max
/effort auto
```

含义说明：

- `low`：更快，思考更少
- `medium`：均衡
- `high`：更深推理
- `max`：更强推理，通常只在部分模型上可用
- `auto`：恢复默认策略

可简单理解为：

- 模型决定能力档位
- `effort` 决定当前愿意花多少推理资源

本次会话中的实际输出：

```text
/effort auto
Effort level set to auto
```

使用建议：

- 日常任务：`/effort medium`
- 日常也可直接使用：`/effort auto`
- 复杂分析：`/effort high`
- 很难的问题：`/model opus` + `/effort high`
- 追求速度：`/effort low`

## 使用建议

对于当前这个以中文文档为主、代码较少的仓库，可优先这样选择：

- 日常默认：`Sonnet 4.6`
- 复杂分析或重构：`Opus 4.6`
- 简单快速任务：`Haiku 4.5`

如果当前环境已经稳定支持 `gpt-5.4`，也可以继续保留，但建议实际使用时重点观察：

- 模型切换是否稳定
- `/model` 是否持续可识别
- 工具调用是否正常
- 输出风格是否符合当前工作流

## 备注

如果后续还要补充，可以继续追加：
- 当前网关配置
- `settings.json` 持久化配置示例
- 不同模型在本仓库里的实际体验对比
