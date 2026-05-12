# 安装指南

把"小程序标准团队"装进你的 Claude Code，3 分钟搞定。

## 前置条件

- 已安装 [Claude Code CLI](https://docs.claude.com/en/docs/claude-code/quickstart)
- 在终端执行 `claude --version` 能显示版本号
- （建议）已有微信小程序 AppID，没有可用测试号

---

## 安装

### 方式一：克隆仓库后批量复制（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/claude-standard-mini-program-dev-team.git
cd claude-standard-mini-program-dev-team

# 2. 确保 ~/.claude/agents 目录存在
mkdir -p ~/.claude/agents

# 3. 复制全部 agent
cp agents/*.md ~/.claude/agents/

# 4. 验证
ls ~/.claude/agents/ | grep -E "orchestrator|product-manager|mini-program-developer"
```

看到 3 个文件名就装成功了。

### 方式二：只装部分 agent

```bash
cp agents/orchestrator.md ~/.claude/agents/
cp agents/product-manager.md ~/.claude/agents/
cp agents/mini-program-developer.md ~/.claude/agents/
```

但 **orchestrator 必须配合至少 2-3 个 agent 才有意义**。

---

## 与原版标准团队共存

如果你已经装了原版标准团队（Web 开发），两个团队的 agent 名称不完全相同，可以共存：

| 原版（Web） | 小程序版 | 差异 |
|------------|---------|------|
| frontend-developer | mini-program-developer | 小程序前端专版 |
| devops-automator | mini-program-publisher | 发布专版替代部署专版 |
| product-manager | product-manager | 小程序版增加了微信生态需求 |
| software-architect | software-architect | 小程序版增加了微信登录方案 |
| ui-designer | ui-designer | 小程序版使用 rpx 体系 |
| backend-architect | backend-architect | 小程序版增加微信安全规范 |

**同名文件会覆盖**。如果你两个团队都要用，建议按需切换：

```bash
# 做 Web 项目时
cp claude-standard-dev-team/agents/*.md ~/.claude/agents/

# 做小程序项目时
cp claude-standard-mini-program-dev-team/agents/*.md ~/.claude/agents/
```

---

## 验证安装

打开 Claude Code，新开对话，输入：

```
使用小程序团队帮我做一个简单的打卡签到小程序
```

如果看到 orchestrator 接管并按阶段流程跑，就装成功了。

---

## 卸载

```bash
cd ~/.claude/agents/
rm orchestrator.md product-manager.md software-architect.md ui-designer.md \
   database-optimizer.md backend-architect.md mini-program-developer.md \
   mini-program-publisher.md testing-evidence-collector.md security-engineer.md \
   code-reviewer.md reality-checker.md technical-writer.md
```

---

## 常见问题

### Q: 我必须把全部 13 个 .md 都装吗？

A: 不必。但 orchestrator + 规划层 2 + 实现层至少 1 个，是最小可用集合。

### Q: 这个团队支持 Taro / uni-app 吗？

A: 支持。software-architect 在 TECH_SPEC 中会选择小程序前端框架（原生/Taro/uni-app），后续 agent 会按选择的技术栈实现。

### Q: 支持 TypeScript 吗？

A: 原生小程序支持 JS 和 TypeScript（需开启），Taro/uni-app 原生支持 TypeScript。由 software-architect 在技术选型时决定。

### Q: 跑一次大概多少 token？

A: 与原版类似，主对话几千 token，完整项目约 50-200k token。

### Q: 能做云开发（微信云开发）吗？

A: 当前版本主要针对自定义后端方案。如果你需要云开发版本，可以修改 software-architect 的技术选型部分。
