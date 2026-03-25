# Claude 相关概念详解

## 一、先用一句话理解全局

你可以先这样记：

- **Claude**：模型本身，是“大脑”
- **Claude API**：程序调用 Claude 的接口
- **Claude Code**：官方提供的命令行 AI 编程代理
- **Agent SDK**：自己构建 agent 应用的开发框架

一句话总结：

> Claude 是模型，API 是调用入口，Claude Code 是现成可用的 agent 产品，Agent SDK 是让你自己搭 agent 系统的工具。

---

## 二、Claude、Claude Code、Claude API、Agent SDK 的关系

### 1. Claude 是什么
Claude 是 Anthropic 的模型系列。

它本身负责：
- 理解自然语言
- 推理
- 生成文本
- 根据上下文做判断
- 在支持工具的场景里决定是否调用工具

但 Claude 本身不是：
- 命令行工具
- IDE 插件
- 终端程序
- 自动化系统

所以 Claude 更像是“核心智能能力”。

### 2. Claude API 是什么
Claude API 是让开发者在自己程序里调用 Claude 的方式。

你可以用它做：
- 聊天应用
- 内容生成
- 结构化输出
- 工具调用
- 多轮对话
- 工作流系统

所以它的本质是：

> 让程序访问 Claude 能力。

如果你想自己开发 AI 应用，通常会接触 Claude API。

### 3. Claude Code 是什么
Claude Code 是一个运行在终端里的官方 agent 产品，专门服务于开发工作流。

它不只是“聊天”，它更像一个能在代码仓库里工作的代理，能帮你：
- 看项目结构
- 搜文件
- 读代码
- 改文件
- 跑命令
- 检查 git 改动
- 按权限调用工具

所以 Claude Code 是：

> Claude 模型 + 工具系统 + 权限控制 + 工程工作流 + CLI 交互界面

### 4. Agent SDK 是什么
Agent SDK 是给开发者用来构建“自己的 agent 系统”的。

如果你想做一个：
- 会用工具的 AI 助手
- 能分步骤执行任务的代理
- 可以连接外部系统的工作流 agent

那你通常会考虑 Agent SDK。

所以它更像是：

> 用来搭建 agent 应用的开发框架。

### 5. 它们之间的关系
可以这么看：

```text
Claude
└── Claude API
    ├── 让程序调用模型
    └── 支持 tool use 等能力

Claude Code
└── 一个官方现成的 agent 产品
    ├── 使用 Claude
    ├── 带工具
    ├── 带权限
    ├── 带配置
    └── 面向开发者终端工作流

Agent SDK
└── 用来自己做 agent 系统
    ├── 使用 Claude 能力
    ├── 管理工具和上下文
    ├── 接入 MCP
    └── 自定义你的代理产品
```

---

## 三、什么是 agent

### 1. agent 不只是“会聊天”
很多人会误以为 agent 就是“更聪明的聊天机器人”。

其实更准确的理解是：

> agent = 模型 + 上下文 + 工具 + 权限 + 执行流程

也就是说，agent 不只是回答一句话，而是会围绕目标做事：

1. 理解任务
2. 决定要不要找信息
3. 决定要不要调用工具
4. 获取结果
5. 继续推进下一步
6. 最后完成任务或请求确认

### 2. Claude Code 里的 agent 怎么理解
在 Claude Code 里，你当前会话中的 Claude 就可以理解为一个 **主 agent**。

它有：
- 当前目录
- 当前会话上下文
- 当前可用工具
- 当前权限
- 项目记忆
- 你的任务目标

所以你让它“帮我修 bug”，它不是只在回答问题，而是在 **agent 模式下工作**。

### 3. agent 和普通对话的区别
#### 普通对话
更偏向：
- 解释概念
- 回答问题
- 输出文本

#### agent 式执行
更偏向：
- 查文件
- 读代码
- 改内容
- 跑命令
- 调工具
- 分多步完成任务

所以它们不是完全分开的，而是连续的：

- 轻一点时像聊天
- 重一点时像执行任务的代理

---

## 四、主 agent 和子 agent

### 1. 主 agent
主 agent 就是当前主会话里的 Claude。

它负责：
- 理解总任务
- 做整体规划
- 跟你交互
- 决定是否分派子任务
- 汇总最终结果

### 2. 子 agent
子 agent 是主 agent 派出去处理某个子问题的代理。

它常见作用：
- 任务拆分
- 上下文隔离
- 专门处理某个方向
- 避免主上下文过度膨胀

例如一个复杂任务：
- 一个子 agent 去搜索代码结构
- 一个子 agent 去研究文档
- 主 agent 最后统一汇总

### 3. 容易误解的点
子 agent 不是“另开一个聊天框”那么简单。

它更像：
- 被委派出去的任务单元
- 有相对独立的上下文
- 完成后把结果交给主 agent

---

## 五、skill 是什么

### 1. skill 的本质
可以把 skill 理解成：

> 一个可复用的能力包或工作流模板

它通常用于解决一类反复出现的问题，比如：
- 审查代码
- 修改配置
- 写 PR 描述
- 调整某种固定格式内容

所以 skill 不是单次回答，而是一个 **复用能力**。

### 2. skill 适合什么场景
它适合：
- 重复性高
- 有固定套路
- 但仍需要模型判断

例如：
- 每次代码审查都按固定维度检查
- 每次改配置都走同样流程
- 每次写提交说明都有统一模板

---

## 六、slash command 和 skill 的关系

### 1. slash command 是什么
slash command 就是 `/xxx` 这种命令。

比如：
- `/help`
- `/commit`
- 某些自定义命令

它的作用是：
- 快速触发某个能力
- 省去重复写长提示词
- 让常见任务有固定入口

### 2. 它和 skill 的关系
最稳妥的理解是：

- **slash command**：入口
- **skill**：能力或流程本身

也就是说：
- skill 是“做什么”
- slash command 是“怎么触发”

很多 skill 会通过 slash command 暴露出来，但两者不完全等价。

### 3. 一个简单例子
如果你有一个“更新配置”的能力：

- `skill` 是“更新配置这套流程”
- `/update-config` 是触发这个流程的入口

---

## 七、MCP 是什么

### 1. MCP 的全称
MCP = **Model Context Protocol**

它是一种标准协议，用来把模型或 agent 连接到外部系统。

你可以把它理解成：

> 给 Claude 接外部能力的标准接口

### 2. MCP 能提供什么
MCP 不只是工具，它通常可以暴露：
- tools
- resources
- prompts

也就是说，它不仅能让 Claude 调工具，还能让 Claude 读取资源、使用标准化提示入口。

### 3. 为什么需要 MCP
没有 MCP 时，每接一个系统都得自己单独写集成，成本高、复用差。

有了 MCP 之后：
- 接入方式统一
- 工具更容易复用
- 模型更容易连接真实业务系统
- 扩展能力更标准化

### 4. MCP 适合连接哪些系统
常见有：
- 数据库
- Jira / 工单系统
- 企业知识库
- 浏览器
- 内部 API
- 文档平台
- 云资源系统

所以 MCP 的意义是：

> 让 Claude 不只会说，还能更标准化地接入真实世界的系统。

---

## 八、tool / tools 是什么

### 1. tool 的本质
tool 就是模型可以请求调用的外部能力。

模型自己不会真的执行工具，它只会：
- 判断是否需要工具
- 选择工具
- 发起调用请求

真正执行工具的是：
- Claude Code 运行环境
- 你的程序
- MCP server
- 其他宿主系统

### 2. 一个例子
比如模型判断：
- 需要读取文件
- 需要跑命令
- 需要搜代码
- 需要查网页

它会发起“调用某工具”的请求，但实际执行不是模型参数本身完成的。

### 3. API 里的 tool use 是什么
在 API 场景里，一般流程是：

1. 你把工具定义给模型
2. 模型决定调用哪个工具
3. 你的程序执行工具
4. 执行结果再传回模型
5. 模型继续推理

所以 tool use 的本质是：

> 模型做决策，宿主负责执行。

---

## 九、MCP tool 和普通 tool 的关系

### 1. MCP tool 是什么
MCP tool 是通过 MCP server 暴露出来的工具。

所以它不是一个完全不同的概念，而是 **tool 的一个来源**。

### 2. 两者关系
可以这样记：

- **tool use**：模型调用工具的机制
- **MCP tool**：工具来自 MCP

所以二者关系是：

> 一个是“怎么调用”，一个是“工具从哪来”。

### 3. 内置工具 vs MCP 工具
#### 内置工具
由 Claude Code 或宿主环境直接提供
例如：
- 读文件
- 搜索代码
- 编辑文件
- 执行命令

#### MCP 工具
通过 MCP 协议接入
例如：
- Jira 查询
- 数据库访问
- 企业内部系统调用

### 4. 本地工具和 MCP 的区别
“本地工具”强调的是运行位置。
“MCP 工具”强调的是接入方式。

所以一个工具可以既是本地的，也是 MCP 的。

---

## 十、hook、settings、memory、plan mode

### 1. hooks 是什么
hooks 是在特定事件前后触发的自动化机制。

适合做：
- 执行前检查
- 执行后提醒
- 自动运行某些固定命令
- 固定流程控制

### 最重要的一点
hooks 是“自动化行为机制”，不是“记忆”。

如果你希望：
- 每次某操作发生时都自动执行某动作

优先考虑 hooks，而不是只靠对话告诉 Claude。

### 2. settings 是什么
settings 是 Claude Code 的配置层。

它控制：
- 权限
- 环境变量
- 默认行为
- hooks 配置
- MCP 配置
- 一些运行规则

所以 settings 更像：

> Claude Code 的系统设置中心

### 3. memory 是什么
memory 是 Claude Code 的长期记忆层。

最典型的项目级载体就是：
- `CLAUDE.md`

它适合记录：
- 项目背景
- 仓库结构
- 团队约定
- 常用命令
- 用户长期偏好

不适合记录：
- 需要严格自动执行的动作
- 临时任务细节
- 敏感密钥

### 一句话记忆
- settings 管规则
- memory 管长期说明

### 4. plan mode 是什么
plan mode 可以理解为：

> 先规划，再执行

适合：
- 先分析方案
- 先确认影响范围
- 先列出会改哪些文件
- 等用户确认后再动手

它不是更强的模型，而是一种 **更保守的工作方式**。

---

## 十一、这些概念之间的关系图

可以用这个文字版关系图来记：

```text
Claude（模型）
├── Claude API（程序调用入口）
│   ├── tool use
│   ├── streaming
│   └── structured output
│
├── Claude Code（官方现成 agent）
│   ├── 主 agent
│   ├── subagents
│   ├── tools
│   │   ├── 内置工具
│   │   └── MCP tools
│   ├── slash commands
│   │   └── skills（常作为复用能力）
│   ├── settings
│   ├── hooks
│   ├── memory
│   └── plan mode
│
└── Agent SDK（自己构建 agent 系统）
    ├── 自定义工具
    ├── 自定义工作流
    ├── MCP 集成
    └── 自定义主/子 agent
```

---

## 十二、最容易混淆的点

### 1. Claude 不等于 Claude Code
- Claude 是模型
- Claude Code 是产品

### 2. Claude Code 不只是聊天工具
它本质上是一个带工具和权限的 agent CLI。

### 3. agent 不等于“自动机器人”
agent 的关键是：
- 有目标
- 有工具
- 有上下文
- 有执行流程

### 4. skill 不完全等于 slash command
- skill 是能力
- slash command 是入口

### 5. memory 不能替代 hooks
- memory 是长期说明
- hooks 是自动执行机制

### 6. settings 和 memory 不是一回事
- settings 是系统规则
- memory 是长期背景

### 7. MCP 不只是“插件”
更准确地说，MCP 是一种协议和接入标准。

### 8. 模型调用工具 ≠ 模型自己执行工具
模型只负责决定调用，执行者是宿主环境或外部系统。

---

## 十三、给中文用户的实用判断法

如果你遇到下面这些需求，可以这样想：

### 想直接让 Claude 在终端里帮你做开发工作
用 **Claude Code**

### 想在自己程序里调用 Claude
用 **Claude API**

### 想自己做一个 agent 应用
看 **Agent SDK**

### 想接入 Jira、数据库、知识库、内部平台
看 **MCP**

### 想把重复任务做成固定入口
看 **skill / slash command**

### 想让某件事自动在某时机发生
看 **hooks**

### 想让 Claude 长期记住项目背景
看 **memory / CLAUDE.md**

### 想先聊方案不要直接改代码
看 **plan mode**

---

## 十四、最短记忆口诀

你可以背这个：

- Claude：模型
- API：调用入口
- Claude Code：现成 agent
- Agent SDK：自己造 agent
- Tool：可调用能力
- MCP：标准化接入外部能力
- Slash command：触发入口
- Skill：复用能力
- Settings：系统规则
- Memory：长期说明
- Hooks：自动触发
- Plan mode：先计划后执行
- Subagent：子任务代理
