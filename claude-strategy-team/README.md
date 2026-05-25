# Strategy Team — 战略团队

> 第 6 个团队：把控方向

## 定位

当一人公司创始人获得阶段性成果后，面临方向调整、产品取舍、合作决策、OKR 制定时，战略团队提供结构化的决策支持。

## 团队成员

| Agent | 文件 | 职责 |
|-------|------|------|
| strategy-orchestrator | orchestrator.md | 总指挥，调度全局，整合决策 |
| strategic-planner | strategic-planner.md | 现状诊断，梳理可选方向 |
| cooperation-architect | cooperation-architect.md | 评估外部合作机会 |
| strategic-pmo | strategic-pmo.md | 将战略决策转化为 OKR |
| incubation-officer | incubation-officer.md | 评估新业务，设计最小验证方案 |
| investment-researcher | investment-researcher.md | 行业趋势与竞品情报 |
| financial-modeler | financial-modeler.md | 财务建模，ROI 分析 |

## 触发信号

- "最近效果跟预期不太一样"
- "这个产品还要不要继续做"
- "有个合作找上门，要不要接"
- "下一步该往哪走"
- "这个季度 OKR 怎么排"

## 执行流程

1. **现状诊断** → strategic-planner → STRATEGIC_DIAGNOSIS.md
2. **外部扫描** → investment-researcher + cooperation-architect（并行）
3. **新业务评估** → incubation-officer（如适用）
4. **财务量化** → financial-modeler → FINANCIAL_MODEL.md
5. **战略决策** → orchestrator 整合 → STRATEGIC_DECISION.md
6. **OKR 制定** → strategic-pmo → OKR_CURRENT_QUARTER.md

## 产出文件

```
docs/
  STRATEGIC_DIAGNOSIS.md      ← 现状诊断与方向选项
  MARKET_INTELLIGENCE.md      ← 行业趋势与竞品情报
  COOPERATION_EVALUATION.md   ← 外部合作评估
  NEW_BUSINESS_ASSESSMENT.md  ← 新业务评估
  FINANCIAL_MODEL.md          ← 财务模型
  STRATEGIC_DECISION.md       ← 最终战略决策
  OKR_CURRENT_QUARTER.md      ← 本季度 OKR
```
