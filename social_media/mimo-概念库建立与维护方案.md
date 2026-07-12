# 概念库建立与维护方案

> 从每天的新闻脚本中自动生长出来，不是一次性建好就完事。

---

## 一、种子概念（从 44 期脚本反向提取）

从已有脚本中标记所有技术术语，按出现频次排序，频次高的进 Tier 1。

| 概念 | 脚本中出现次数 | 当前处理方式 | 建议优先级 |
|------|:---:|------|:---:|
| Agent | 8 | 只说"AI Agent"，没解释是什么 | ★★★ |
| 蒸馏 | 6 | 只说"被指控蒸馏"，没解释原理 | ★★★ |
| Token | 5+ | 从未解释 | ★★★ |
| 上下文窗口 | 4 | 只说数字，没解释为什么重要 | ★★★ |
| MoE | 3 | 一笔带过"MoE 架构" | ★★★ |
| Chain-of-Thought | 3 | 只说"思考强度"，没解释机制 | ★★ |
| Fine-tune | 3 | 只说"微调排行榜" | ★★ |
| Alignment | 2 | 只说"安全过滤器" | ★★ |
| 量化 | 2 | 从未解释 | ★★ |
| Diffusion | 1 | 从未解释 | ★ |
| KV Cache | 1 | 从未解释 | ★ |
| RLHF | 0 | 从未提及 | ★ |
| RAG | 0 | 从未提及 | ★ |
| Embedding | 0 | 从未提及 | ★ |
| Scaling Law | 0 | 从未提及 | ★ |
| Attention | 0 | 从未提及 | ★ |

**全部来自你自己的脚本，只是从未展开讲过。**

---

## 二、概念主库（concepts.json）

建议放在 `news-pipeline/concept-bank/concepts.json`。

```json
{
  "concepts": [
    {
      "id": "moe",
      "name": "MoE（混合专家）",
      "tier": 1,
      "one_liner": "大模型的分诊制度，省钱不降质",
      "analogy": "医院分诊台：100 个医生全看一遍 → 先分诊只派 2 个相关专家，效果差不多，成本砍 98%",
      "news_keywords": ["MoE", "混合专家", "激活参数", "总参数", "MoE 架构"],
      "related_events": ["微软 MAI", "DeepSeek V4", "MiniMax M3"],
      "search_volume": "high",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "token",
      "name": "Token",
      "tier": 1,
      "one_liner": "AI 的最小计费单位，相当于手机流量的 KB",
      "analogy": "你打电话按分钟计费，AI 按 token 计费。一个汉字约 1-2 个 token，一个英文单词约 1 个 token",
      "news_keywords": ["token", "百万 token", "token 消耗", "token 价格", "按量计费"],
      "related_events": ["任何定价/降价新闻", "Sonnet 5 token 消耗增加"],
      "search_volume": "high",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "context_window",
      "name": "上下文窗口",
      "tier": 1,
      "one_liner": "AI 的工作台大小，越大一次能处理的信息越多",
      "analogy": "桌子越大能摊开的文件越多。128K 上下文 ≈ 一次能读一本小说，8K ≈ 只能读几页",
      "news_keywords": ["上下文", "context", "128K", "200K", "百万上下文", "512K"],
      "related_events": ["GLM-5.2 百万上下文", "GPT-5.6 窗口扩大到 353K", "华为盘古 512K"],
      "search_volume": "high",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "distillation",
      "name": "蒸馏",
      "tier": 1,
      "one_liner": "大模型教小模型，像学霸抄作业",
      "analogy": "学霸（大模型）做一遍题，学渣（小模型）照着抄答案。抄得像但没学到真本事——所以 Opus 4.8 被问是谁，它说自己是 Qwen",
      "news_keywords": ["蒸馏", "distill", "训练数据", "身份错乱"],
      "related_events": ["Opus 4.8 蒸馏争议", "阿里被 Anthropic 指控蒸馏", "GLM 被质疑蒸馏 Claude"],
      "search_volume": "high",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "agent",
      "name": "Agent（智能体）",
      "tier": 1,
      "one_liner": "AI 不只聊天，还能自己规划步骤干活",
      "analogy": "请了个助理：你说"帮我订机票"，它自己查航班、比价格、下单，不用你一步步指挥",
      "news_keywords": ["Agent", "智能体", "AI Agent", "自主执行", "工具调用"],
      "related_events": ["Claude Code", "Codex", "微信 A2A", "豆包千问下架智能体"],
      "search_volume": "high",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "rlhf",
      "name": "RLHF（人类反馈强化学习）",
      "tier": 1,
      "one_liner": "训练 AI 的方法——做对给奖励，做错扣分",
      "analogy": "训狗：坐下给骨头（奖励），咬人不给（惩罚）。训多了狗就知道什么该做什么不该做",
      "news_keywords": ["RLHF", "人类反馈", "安全训练", "对齐"],
      "related_events": ["Claude 安全过滤器太敏感", "Fable 5 被吐槽'敏感肌'"],
      "search_volume": "medium",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "finetune",
      "name": "Fine-tune（微调）",
      "tier": 1,
      "one_liner": "通才上了个专业培训班，变成专科医生",
      "analogy": "医学院毕业生（基础模型）什么都会一点，去骨科进修一年（微调）后变成了骨科专家",
      "news_keywords": ["微调", "fine-tune", "fine tuning", "微调排行榜"],
      "related_events": ["GLM 开源后下游微调", "模型微调排行榜登顶争议"],
      "search_volume": "medium",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "rag",
      "name": "RAG（检索增强生成）",
      "tier": 2,
      "one_liner": "给 AI 配了个随身图书馆，不会的现查",
      "analogy": "开卷考试 vs 闭卷考试。RAG 让 AI 可以翻书（检索知识库）再回答，比死记硬背更准",
      "news_keywords": ["RAG", "检索增强", "知识库", "向量数据库"],
      "related_events": ["企业 AI 应用", "微信小微", "Notion 集成 AI"],
      "search_volume": "medium",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "quantization",
      "name": "模型量化",
      "tier": 2,
      "one_liner": "高清图压缩成缩略图，看着差不多但文件小 10 倍",
      "analogy": "4K 电视和 720P 电视，坐三米外看着差不多，但 720P 便宜得多。量化就是把 4K 模型压成 720P",
      "news_keywords": ["量化", "Q4", "Q8", "4bit", "8bit", "GGUF"],
      "related_events": ["本地模型横评", "Gemma 4 笔记本能跑"],
      "search_volume": "medium",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "diffusion",
      "name": "Diffusion（扩散模型）",
      "tier": 2,
      "one_liner": "先撒满噪点，再一步步还原照片",
      "analogy": "把一张照片打印出来，撒一把沙子（加噪），然后一颗颗把沙子吹掉还原原图。AI 就是学怎么吹沙子",
      "news_keywords": ["Diffusion", "扩散", "生图", "图像生成"],
      "related_events": ["谷歌 Diffusion Gemma", "Grok Imagine 1.5", "Ideogram 4 开源"],
      "search_volume": "medium",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "attention",
      "name": "Attention（注意力机制）",
      "tier": 2,
      "one_liner": "AI 读文章时自动聚焦重点词",
      "analogy": "你读一句话时眼睛会自动忽略"的地得"，聚焦在关键词上。Attention 就是 AI 的"眼睛聚焦"机制",
      "news_keywords": ["Attention", "注意力", "Transformer", "Self-Attention"],
      "related_events": ["模型性能对比", "降智讨论"],
      "search_volume": "medium",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "embedding",
      "name": "Embedding（向量嵌入）",
      "tier": 2,
      "one_liner": "AI 把文字变成数字坐标，才能做计算",
      "analogy": "地图上每个城市有经纬度坐标。Embedding 就是给每个词一个"语义坐标"，意思相近的词坐标也近",
      "news_keywords": ["Embedding", "向量", "嵌入", "语义搜索"],
      "related_events": ["RAG 应用", "语义搜索"],
      "search_volume": "low",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "cot",
      "name": "Chain-of-Thought（思维链）",
      "tier": 2,
      "one_liner": "让 AI 写出解题步骤，比直接写答案更准",
      "analogy": "老师说"把解题过程写出来"，学生就会一步步算，不会跳步骤出错。思考强度 high/xhigh 就是让 AI 写更多步骤",
      "news_keywords": ["思考强度", "Chain-of-Thought", "CoT", "xhigh", "reasoning"],
      "related_events": ["Codex 思考强度设置", "Fable 5 推理能力"],
      "search_volume": "medium",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "scaling_law",
      "name": "Scaling Law（缩放定律）",
      "tier": 3,
      "one_liner": "参数越多、数据越多、算力越大，模型就越强（但有上限）",
      "analogy": "10 个人干 1 天的活 ≈ 1 个人干 10 天。但 100 个人干 1 天不一定等于 1 个人干 100 天——人多了协调成本也高",
      "news_keywords": ["参数", "万亿参数", "算力", "训练成本", "烧钱"],
      "related_events": ["融资新闻", "大厂算力军备竞赛"],
      "search_volume": "low",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "alignment",
      "name": "Alignment（对齐）",
      "tier": 3,
      "one_liner": "让 AI 的行为符合人类价值观",
      "analogy": "给 AI 装了个道德指南针。但有时候指南针太敏感——问个化学溶剂都被拒",
      "news_keywords": ["Alignment", "对齐", "安全", "安全过滤器", "拒绝回答"],
      "related_events": ["Fable 5 太敏感", "Claude 安全策略"],
      "search_volume": "low",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "constitutional_ai",
      "name": "Constitutional AI（宪法 AI）",
      "tier": 3,
      "one_liner": "Anthropic 的独门武器——给 AI 一部"宪法"让它自我约束",
      "analogy": "不靠警察（人工审核）管 AI，而是给 AI 一本法律让它自己学着不犯法",
      "news_keywords": ["Constitutional AI", "宪法 AI", "Anthropic 安全"],
      "related_events": ["Anthropic 呼吁暂停 AI 开发", "安全研究"],
      "search_volume": "low",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "mixture_of_agents",
      "name": "Mixture of Agents（多模型协作）",
      "tier": 3,
      "one_liner": "多个 AI 模型分工合作，像一个团队",
      "analogy": "写论文：一个人查资料、一个人写初稿、一个人审稿。每个模型做自己擅长的部分",
      "news_keywords": ["多模型", "模型协作", "编排", "Orchestrator"],
      "related_events": ["多模型横评", "编程工具对比"],
      "search_volume": "low",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "synthetic_data",
      "name": "Synthetic Data（合成数据）",
      "tier": 3,
      "one_liner": "AI 用自己生成的数据训练自己",
      "analogy": "老师出卷子给学生做，结果学生自己出题自己做——看起来分数很高，但真考试可能翻车",
      "news_keywords": ["合成数据", "synthetic", "自我训练", "训练数据"],
      "related_events": ["蒸馏争议", "训练数据来源讨论"],
      "search_volume": "low",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "kv_cache",
      "name": "KV Cache（键值缓存）",
      "tier": 3,
      "one_liner": "AI 的书签——翻过的地方做个标记，下次不用从头翻",
      "analogy": "你读一本 500 页的书，每天读 50 页并做书签。没有 KV Cache 就得每天从第 1 页重新翻",
      "news_keywords": ["KV Cache", "缓存", "长对话变慢", "压缩"],
      "related_events": ["Codex 自动压缩耗时", "上下文管理"],
      "search_volume": "low",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "speculative_decoding",
      "name": "Speculative Decoding（推测解码）",
      "tier": 3,
      "one_liner": "先让实习生快速写草稿，老师傅再检查修正",
      "analogy": "实习生（小模型）快速写 5 个字，老师傅（大模型）一看"前 3 个对了，后 2 个改一下"。比老师傅一个字一个字写快得多",
      "news_keywords": ["极速", "tokens/s", "推理速度", "Cerebras"],
      "related_events": ["MiMo UltraSpeed 1000 tokens/s", "Cerebras 极速版"],
      "search_volume": "low",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "tokenizer",
      "name": "Tokenizer（分词器）",
      "tier": 3,
      "one_liner": "不同模型切词方式不同，所以同一个问题消耗的 token 数不一样",
      "analogy": "英文按空格切词，中文按字切词。就像不同国家切蛋糕的方式不同，但蛋糕总量一样",
      "news_keywords": ["tokenizer", "分词", "token 消耗差异"],
      "related_events": ["Sonnet 5 换 tokenizer 导致消耗增加 1-1.35 倍"],
      "search_volume": "low",
      "last_used": null,
      "use_count": 0
    }
  ]
}
```

---

## 三、维护机制（嵌入现有 Pipeline）

### 现有流程中新增环节

```
抓取 → 合并 → 分析 → 写脚本 → 【概念提取】→ 分镜
                                    ↑
                             从当天脚本中提取技术术语
                             匹配概念库
                             标记"可用"或"新增"
```

### 每次生成脚本后，在脚本末尾追加

```markdown
---
## 当天概念提取

**已提及的技术术语：**
- MoE 架构（场景2，微软 MAI）
- 万亿参数（场景2）

**匹配概念库：**
- MoE → Tier 1，上次使用 6/3，间隔 >14天 ✅ 可用

**建议深潜主题：** MoE（用微软 MAI 做引入）
```

---

## 四、使用记录（used-log.json）

```json
{
  "log": [
    {
      "date": "2026-06-17",
      "concept_id": "moe",
      "news_trigger": "微软 MAI 用 MoE 架构",
      "script_path": "2026-06-17/scripts/video-script-2026-06-17.md"
    }
  ]
}
```

---

## 五、自动化维护规则

| 规则 | 触发条件 | 动作 |
|------|------|------|
| **自动提取** | 每次生成新脚本后 | 扫描脚本中的技术术语，匹配概念库 |
| **自动提醒** | 某个 Tier 1 概念 > 14 天未使用 | 提示"该讲这个概念了" |
| **自动降级** | 某个概念连续 3 期没人搜/没人讨论 | 从 Tier 1 降到 Tier 2 |
| **自动升级** | 某个概念突然在新闻中高频出现 | 从 Tier 2 升到 Tier 1，优先使用 |
| **自动新增** | 脚本中出现概念库没有的技术术语 | 提示"新概念，是否加入概念库？" |

---

## 六、概念的生命周期

```
发现 → 评估 → 写模板 → 使用 → 追踪 → 淘汰/保留
```

| 阶段 | 做什么 |
|------|------|
| **发现** | 从新闻、社区讨论、脚本中提取技术术语 |
| **评估** | 这个概念观众会搜吗？和新闻关联度高吗？ |
| **写模板** | 60 秒脚本 = 过渡句 + 类比 + 新闻关联 + 一句话记住 |
| **使用** | 在日报/周报中播放 |
| **追踪** | 记录使用日期、观众反馈（评论区是否讨论） |
| **淘汰** | 使用 3 次后观众无反应 → 降级或移除 |
| **保留** | 观众评论区主动提问或讨论 → 标记为"高价值" |

---

## 七、概念使用防重复表

每次使用后标记日期，同一个概念至少间隔 14 天再用：

| 概念 | Tier | 首次使用 | 上次使用 | 使用次数 | 状态 |
|------|:---:|------|------|:---:|------|
| MoE | 1 | - | - | 0 | 待使用 |
| Token | 1 | - | - | 0 | 待使用 |
| 上下文窗口 | 1 | - | - | 0 | 待使用 |
| 蒸馏 | 1 | - | - | 0 | 待使用 |
| Agent | 1 | - | - | 0 | 待使用 |
| RLHF | 1 | - | - | 0 | 待使用 |
| Fine-tune | 1 | - | - | 0 | 待使用 |
| RAG | 2 | - | - | 0 | 待使用 |
| 模型量化 | 2 | - | - | 0 | 待使用 |
| Diffusion | 2 | - | - | 0 | 待使用 |
| Attention | 2 | - | - | 0 | 待使用 |
| Embedding | 2 | - | - | 0 | 待使用 |
| Chain-of-Thought | 2 | - | - | 0 | 待使用 |
| Scaling Law | 3 | - | - | 0 | 待使用 |
| Alignment | 3 | - | - | 0 | 待使用 |
| Constitutional AI | 3 | - | - | 0 | 待使用 |
| Mixture of Agents | 3 | - | - | 0 | 待使用 |
| Synthetic Data | 3 | - | - | 0 | 待使用 |
| KV Cache | 3 | - | - | 0 | 待使用 |
| Speculative Decoding | 3 | - | - | 0 | 待使用 |
| Tokenizer | 3 | - | - | 0 | 待使用 |

---

## 八、每日选概念优先级

```
优先级 1：当天新闻里提到了 → 直接用
  例：6/17 报了"微软 MAI 用 MoE 架构" → 当天深潜讲 MoE

优先级 2：当天新闻没有明显概念 → 从概念库 Tier 1 里挑 >14 天未用的
  例：6/28 全是封号和低价渠道 → 从库中选"Token 是什么"

优先级 3：热点事件关联概念 → 讲"为什么这件事重要"
  例：Fable 5 被禁 → 讲"什么是出口管制？AI 模型为什么会被禁？"
```

---

## 九、落地步骤

**今天就做（30 分钟）：**
1. 创建 `news-pipeline/concept-bank/` 目录
2. 把上面的 concepts.json 写入
3. 从种子表中挑出现最多但从未解释的 5 个概念（Token、蒸馏、Agent、上下文窗口、MoE）
4. 为这 5 个概念各写一个 60 秒脚本模板

**每周做（15 分钟）：**
1. 回顾本周脚本，提取新出现的技术术语
2. 更新概念库的 `last_used` 和 `use_count`
3. 检查是否有 Tier 1 概念超过 14 天未使用

**每月做（30 分钟）：**
1. 根据评论区反馈调整概念的 Tier 等级
2. 淘汰观众不感兴趣的冷门概念
3. 从新的 AI 产品发布中补充新概念
