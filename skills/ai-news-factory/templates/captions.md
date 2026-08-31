# 字幕切行规则（v3.25.0）

> 供 Phase 7 使用。算法实现见同目录 `gen_captions.py`。  
> **内容 100% 来自脚本，时间 100% 来自音频。禁止按字数比例切时间轴。**

---

## 物理下限（先于语义）

| 项 | 规则 |
|----|------|
| 目标行长 | 15–20 汉字（空格不计） |
| 软上限 `max_len` | 16：到此长度遇软标点才断 |
| 硬上限 `hard_max` | 20：允许略超 16 以保住专名/动宾/正反并列 |
| 无合法切点 | **整句保留**（可到 24–25），**禁止按字符下标硬切** |
| 最短显示 | 对齐后 `merge_short_dwell(min_sec=1.0)`，<1s 并回上一行 |
| CPS | 中文约 6–7 字/s（由音频时长自然满足，不反推切行） |
| 视觉 | Remotion `Subtitles.tsx` **单行**；不做双行长度平衡 |

## 语义切点

| 标点 | 行为 |
|------|------|
| `。！？；`（`SENT_END`） | **强制断行** |
| `，、：`（`SOFT_PUNCT`） | 仅当当前行 ≥ `max_len` 才断；不到 16 字继续攒 |
| 所有标点一视同仁 | **禁止**（旧 `split_sentences`，会切出 `延期；` 这种 3 字闪行） |

超 `hard_max` 的切法（按序，命中即停）：

1. **标点黄金分割**：在行长 40–60% 找软标点，找不到扩到 30–70%，切在标点后  
2. **弱连接**：在 `WEAK_BEFORE`（所以/就好比/还能/若仍…）前切，且左右都 ≥6 字  
3. **整句保留**：没有合法切点就不断

## 禁切（必须同一行）

| 类型 | 反例（2026-08 月报实测，切开即错） |
|------|----------------------------------|
| 正反并列 | `稳不稳` |
| 偏正 | `硬新闻主轴` |
| 动宾 / 专名+动宾 | `规划步骤`、`编程 Agent`、`终止Cursor官方直连` |
| 专名连发 | `Hy四连发`、`羊报AI月报` |
| 品牌+宾语 | `整月风向`（接在「回顾 AI 圈」后） |
| 数量+名 | `主题近一万`（禁止切成 `有效` / `主题近一万。`） |
| 短尾巴 | `延期；` 不得单独成行 |

后处理：

- `GLUE_TAILS`：这些尾巴若落在行首，并回上一行  
- `BAD_ENDS` + `BAD_STARTS`：`硬新闻`/`主轴`、`稳`/`不稳`、`编程`/`Agent`、`混元`/`Hy`、`回顾`/`AI圈`  
- `jieba.add_word`：当期专名（DeepSeek / Cursor / 峰谷价 / 官方直连…）必须加词，否则 16 字墙会从词中切开

## 时间轴（不要改回估算）

1. `group_caps` **先**切出字幕字符串（可 `--dry-run` 只看切行、不加载 whisper）  
2. faster-whisper `word_timestamps=True` 跑当期 wav  
3. 每条字幕用滑动窗口 `SequenceMatcher` 对齐到词级时间戳  
4. `merge_short_dwell(min_sec=1.0)`  
5. 场景偏移累加 → `captions.json` + `video-project/public/captions.json`

**禁止**：按字符数比例分配 `start/end`（v2.1/v2.2 已废弃）。无 whisper 词时才允许比例兜底。

## 工作流

```
复制 templates/gen_captions.py → 当期 scripts/gen_captions.py
  → 按脚本补 jieba.add_word 专名
  → python3 scripts/gen_captions.py --report-dir <当期目录> --dry-run   # 人工扫禁切反例
  → python3 scripts/gen_captions.py --report-dir <当期目录>             # whisper 对齐
  → 复制到 video-project/public/captions.json
```

Hook 5s 独立成段、前 5s 字号 +20%（`startMs < 5000`）仍有效（v3.21.0）。
