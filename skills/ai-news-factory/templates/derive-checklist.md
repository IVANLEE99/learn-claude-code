# 派生自检清单（每期开工第一件事，机械可跑）

> 来源：坑 241（内容层必须重写）+ 坑 395（helper 从 templates/ 拷）+ 坑 396-407（v3.80.0，断言层必须一起重写）
> + **坑 408-409（v3.81.0，哨兵会自伤 + 锚点扩写会叠写）**。
> 配套文件：`templates/watchdog.md`（定时任务与看门狗的三层架构 + 沙箱验判定分支）。
> 核心判据：**派生不是「把日期替换掉」，是「让本期所有判据指向本期内容」。**
> 内容层漏改 → 成片讲上期事件（**会被口径检查抓到**）。
> 断言层漏改 → 本期正确内容被判 FAIL（**不会被告警抓到，只会逼你去修本来对的东西**）。
> **防呆机制本身也要测** → 哨兵插错位、扩写写重了，都会以「保护」的名义制造故障（坑 408/409）。

按顺序跑完下面 7 段，任一段失败就不许进下一阶段。

---

## 0. 派生源选择：只从 `templates/` 拷，不从上一期脚本拷

```bash
SKILL=~/.claude/skills/ai-news-factory
# helper / 断言常量 / 模板 —— 这些「随 skill 演进」，不随期次变
cp "$SKILL/templates/cdp_helper.py"        news-pipeline/<DATE>/scripts/
cp "$SKILL/templates/issue_guard.py"       news-pipeline/<DATE>/scripts/
cp "$SKILL/templates/gen_captions.py"      news-pipeline/<DATE>/scripts/
cp "$SKILL/templates/revive_frozen_tabs.py" news-pipeline/<DATE>/scripts/
```

**禁止**：`cp ../<上期>/scripts/*.py`。上一期脚本是「那天正确的快照」，不是「今天正确的源」（坑 395）。

**例外**：平台上传脚本（`bili_upload` / `douyin_e2e` / `channels_upload` / `zhihu_upload` / `mp_*_run`）目前没有独立模板，只能从上一期派生——但**必须**走完下面第 2 段的断言层重写。

---

## 1. 日期四形态替换 + leftover 归零

```python
OLD = ('2026-11-03', '1103', '2026, 11, 3,', '__wx1103')
NEW = ('2026-11-04', '1104', '2026, 11, 4,', '__wx1104')
# 降序替换！升序会让 03→04 生成的新 04 被后一条规则再推一天
```

**launch wrapper 特判**：触发串是「上一期 DATE 22:35」，不会被当期替换命中：

```python
LAUNCH_OLD = '2026-11-03 22:35'
LAUNCH_NEW = '2026-11-04 22:35'
```

自检：

```bash
# 四形态 leftover 必须为 0（launch wrapper 的触发串先抹掉再查）
grep -rn "2026-11-03\|1103\|__wx1103" data/_*_1104.* && echo LEFTOVER_FAIL || echo LEFTOVER_OK
# 触发 epoch 必须与 date -j 一致
date -j -f '%Y-%m-%d %H:%M:%S' '2026-11-04 22:35:00' '+%s'
```

---

## 2. **断言层重写清单（本期最重要，v3.80.0 新增）**

逐个文件把这些「判据表」里的上期词换掉。**语法检查不会发现它们，只有跑起来才会炸。**

| 文件 | 变量 | 上期词长什么样 | 本期该怎么写 |
|---|---|---|---|
| `audit_<id>.py` | `issue_words` | 上期事件名（如 `Instant` / `默契挑战` / `Argon`） | 本期**口播原文里真实出现**的实词 |
| `audit_<id>.py` | `prior_tokens` | 上上期事件名 | 上期事件名（用于「无残留」断言） |
| `audit_<id>.py` | `COLLOQ` | 上期口语化句子 | 本期口播里的原句（≥3 条） |
| `audit_<id>.py` | 封面大字断言 | 上期 `'无限没了' in cover` | 本期封面词 |
| `audit_<id>.py` | `CRED` 枚举 | 一般不变 | 如需新增档位，必须同时更新枚举 |
| `_md2typ_<id>.py` | `checks` | 上期报告实词 | 本期报告实词（**逐条 grep 报告验证存在**） |
| `_md2typ_<id>.py` | `forbidden` | 上期事件词 | 上期事件词 **− 本期合法引用的那些** |
| `_setup_remotion_<id>.py` | 首行断言 | 上期口播首句关键词 | 本期口播首句关键词 |
| `_setup_remotion_<id>.py` | `ANCHOR` 注释 | 上期锚点名 | 本期锚点名 |
| `gen_publish_<id>.py` | `TITLE_MAIN` / `DESC` / `STALE` / `MUST` | 上期事件 | 本期事件 |
| `gen_publish_<id>.py` | `ALLOWED_SAME` | — | **只放真正常驻字段**，见第 4 段 |
| `gen_covers_local_<id>.py` | `LINE1_*` / `LINE2_*` / `FORBIDDEN` | 上期封面大字 | 本期封面大字 + 上期大字进 FORBIDDEN |
| `bili_upload_<id>.py` | issue words 的 `for w in [...]` | 上期事件 | 本期事件 |
| `douyin_e2e_<id>.py` | issue words 的 `for _w in [...]` | 上期事件 | 本期事件 |
| `channels_upload_<id>.py` | issue words | 上期事件 | 本期事件 |
| `zhihu_upload_<id>.py` | `N_IMGS` / 标题来源 | 上期硬编码 | 按稿件实算 / 读稿件首行 |

**机械自检（派生完立刻跑）**：

```bash
# ① 上期事件词出现在「断言表」里 = 还没重写
#    先列出上期报告的高频实词，再 grep 本期脚本
grep -rn "默契挑战\|计算摄影\|workbuddy\|codebuddy\|信任最小化\|池化合账" \
     news-pipeline/<DATE>/scripts/*.py | grep -v "STALE\|forbidden\|prior_tokens\|prior_hits"
#  ↑ 命中且落在 checks/issue_words/COLLOQ 里 = FAIL

# ② 本期 checks 必须在报告里真实存在
python3 - <<'EOF'
import re
src = open('news-pipeline/<DATE>/scripts/_md2typ_<id>.py', encoding='utf-8').read()
rep = open('data/reports/<DATE>.md', encoding='utf-8').read()
m = re.search(r'^checks = \[(.*?)^\]', src, re.S | re.M)
checks = eval('[' + m.group(1) + ']', {'DATE': '<DATE>'})
miss = [c for c in checks if c not in rep]
print('checks missing in report:', miss or 'NONE')
EOF
```

---

## 2b. **哨兵插入位置（v3.81.0 新增，坑 408）**

派生器给内容层文件插 `__REWRITE_FOR_<id>__` 哨兵时，**插入位置错一位就会吃掉文件头**。

```python
# ✅ 正确：插在 shebang 之后、docstring 之前
lines = body.split('\n')
idx = 1 if lines[0].startswith('#!') else 0
new = '\n'.join(lines[:idx] + [SENTINEL_BLOCK.rstrip()] + lines[idx:])

# ❌ 错误：PY_BLOCK + body —— 哨兵在 shebang 之前，删哨兵时连带删掉 import
```

**更稳的做法：用独立 `.SENTINEL` 文件，不碰 py 正文。**

**每删完一个哨兵，立刻两连验证（缺一不可）**：

```bash
F=news-pipeline/<DATE>/scripts/audit_<id>.py
python3 -c "import ast;ast.parse(open('$F',encoding='utf-8').read());print('syntax OK')"
python3 "$F" 2>&1 | head -5     # 至少跑到业务断言前不报 NameError
```

本期实测：`_add_concepts_1104.py` 因哨兵插在 shebang 前，删哨兵时把 `import json, os` 一起删了 →
`NameError: name 'os' is not defined`。**14 个文件里只有它崩，其余是侥幸（import 恰好在 docstring 之后）。**

---

## 2c. **锚点扩写：整段重写 + 三重断言（v3.81.0 新增，坑 409）**

锚点占比超线需要扩写锚点场景时：

```python
BASE     = "……（不含任何扩展段的原始口播）……"
EXTRA    = "还有一层常被忽略：……"      # 新增内容
ANCHOR15 = "……"                        # 库里 script_15s，逐字照抄

new = BASE + EXTRA                      # ✅ 拼一次
assert ANCHOR15 in new,       'script_15s 未逐字保留（坑 399）'
assert new.count(EXTRA) == 1, '扩展段重复（坑 409）'
```

**❌ 禁止**：对同一字符串连续两次 `str.replace`（先加 before 再加 after）。
第二次的锚点是第一次的产物，极易把扩写段叠两遍——本期 scene7 因此从 78 s 变 **104 s**，白跑一次 TTS。

**目标时长公式**（坑 327/398）：`s7_target = pre*(1-r)/r - s8`，`r` 取 0.75~0.76 留边距。
中文 TTS（atempo=1.4）约 **4.4 字/秒**，据此换算要加多少字。

**改完只重跑该场景 TTS**，然后复核 `ratio ∈ [0.70, 0.80]` 且 **不落在 0.79+**。

---

## 3. 禁词表 × 当日报告 交叉 grep（坑 326，每期必查）

**上期禁词表照抄 = 误伤本期合法引用。** 本期真实案例：`workbuddy` / `codebuddy` / `反代封号` / `二三十倍` 在 1102 是禁词，但 1103 的报告**合法引用**它们（新政策禁的正是这类玩法）。

```python
# _md2typ 里必须有这段，且必须在 typst compile 之前跑
conflicts = [f for f in forbidden if f in md]
assert not conflicts, f'禁词在 {DATE} 报告中合法出现，必须从 forbidden 移除: {conflicts}'
```

**判据**：交叉检查报告 `NONE` 才继续；有冲突就**逐个判断**——是本期合法引用（移出禁词表）还是真残留（改报告）。**不要为了让它过而放宽断言。**

---

## 4. `ALLOWED_SAME` 白名单：只放真正常驻字段

`gen_publish` 的「字段与上期雷同」断言是有用的。命中时先问「这个字段本期真的该变吗」，**不要第一反应就往白名单里加**。

| 字段 | 可以常驻？ | 理由 |
|---|---|---|
| `draft_only` | ✅ | 常设约束 |
| `cover.horizontal` / `cover.vertical` | ✅ | 文件名固定 |
| `platform.bilibili.partition` | ✅ | 分区固定 |
| `platform.wechat.images` | ✅ | 目录固定 |
| `anchor.play_order` | ✅ | 恒为 `[1..N]` |
| `anchor.scene` | ⚠️ | 只有当两期锚点都在同一景时才相同；**必须写明理由** |
| **`tags` / `platform.bilibili.tags`** | ❌ | **必须覆盖本期主线厂商**（本期实测：主线是 Claude/Grok，tags 却是 ChatGPT/OpenAI/Gemini → 断言抓对了） |
| `anchor.concept_id` | ❌ | 换锚点必须换 |

**自检**：

```python
# tags 必须至少覆盖本期主线的两个主语
main_subjects = ['Claude', 'Grok']   # 本期人工确认
for s in main_subjects:
    assert s in TAGS, f'tags 未覆盖本期主线 {s}'
```

---

## 4b. **新增字段 vs 逐字段 diff 门（v3.82.0 新增）**

`gen_publish` 里有 `extra_keys` 断言：`publish.json` 出现上期没有的字段就中止。这是**好东西**（挡住「派生脚本凭空造字段」），但**新增字段是正当需求时不要删断言**。

1105 实测：补 `platform.zhihu.*` 时 `AssertionError: extra fields vs prev: ['platform.zhihu.title', ...]`。

**正解**：

```python
ALLOWED_NEW_PREFIXES = ('platform.zhihu.',)          # 显式声明本期有意新增
unexpected = [k for k in extra_keys if not k.startswith(ALLOWED_NEW_PREFIXES)]
assert not unexpected, f'unexpected extra fields vs prev: {unexpected}'
if extra_keys:
    print(f'new fields (allowed): {extra_keys}')     # 留痕，便于下一期知道这是什么时候加的
```

**同时**：`same` / `changed` 的比较要加 `k in pf` 保护，否则新增键会在 `str(pf[k])` 处 `KeyError`：

```python
same    = [k for k in cf if k in pf and str(cf[k]) == str(pf[k])]
changed = [k for k in cf if (k not in pf) or str(cf[k]) != str(pf[k])]
```

**纪律**：删断言 = 把整道门的价值一起删掉；加白名单 + 打印留痕 = 保留价值并且下一期可追溯。

---

## 4c. **平台字段完整性清单（v3.82.0，每期逐项核对）**

这三项在过去几期反复漏，1105 由用户点名：

| 项 | 位置 | 判据 | 漏了会怎样 |
|---|---|---|---|
| **公众号标题** | `mp_*_run.py` 的 `title` 步 | `#title.value == publish.json.title` 逐字相等 | 后台草稿显示「无标题」，`title_ok` 恒假 |
| **视频号 hashtag 行** | `platform.channels.description` 末尾 | 与 `platform.douyin.description` 同样以 `#今日羊报AI #AI日报 …` 结尾 | 两个平台描述形态不一致（用户直接点名要统一） |
| **知乎 topics** | `platform.zhihu.topics`（**整段都不能缺**） | 2–4 个，且 `zhihu_upload.py topics` 步回读 chips 后 `missing == []` | 话题只能靠平台按正文自动带 1–2 个，等于没管 |

自检片段：

```python
pub = json.load(open(f'{D}/publish.json'))
ch, dy = pub['platform']['channels'], pub['platform']['douyin']

# ② 视频号必须像抖音一样带 hashtag 行
ch_tags = [t for t in ch['description'].split('\n') if t.strip().startswith('#')]
dy_tags = [t for t in dy['description'].split('\n') if t.strip().startswith('#')]
assert ch_tags, 'channels description 缺 hashtag 行（v3.82.0）'
assert ch_tags == dy_tags, f'channels/douyin hashtag 不一致: {ch_tags} vs {dy_tags}'

# ③ 知乎 topics 必须在场
zh = pub['platform'].get('zhihu') or {}
assert zh.get('topics'), 'platform.zhihu.topics 缺失（v3.82.0）'
assert 2 <= len(zh['topics']) <= 4, f'话题数应 2-4: {zh["topics"]}'
```

---

## 5. 锚点三重校验（坑 397/398/399）

```python
# ① eligible（缺一不可）
c = [x for x in bank['concepts'] if x['name'] == ANCHOR_NAME][0]
assert c['status'] == 'ready'
assert len(c.get('script_15s') or '') > 50
assert c['script_meta']['authored_by'] == 'ai-concept-narrator'
assert c['script_meta']['reviewed'] is True
assert (today - parse(c['last_used'])).days >= 14

# ② 台词逐字（从库读，禁止手打）
s7 = c['script_15s'] + extras
assert c['script_15s'] in full_voiceover

# ③ 占比按 wav 头实测，且不压线
#    目标 0.75±0.02；0.79+ 视为不合格（TTS 波动会越界）
scene7_target = pre * (1 - 0.76) / 0.76 - scene8
```

**回调只重跑 scene7 的 TTS**（坑 327），不动其他场景。

---

## 6. 上传前置检查（坑 401/403/404/408 → v3.81.0 补「标签页盘点」）

```bash
D=news-pipeline/<DATE>

# ① 视频文件名必须等于 publish.json 的 video 字段（坑 401，每期必犯）
python3 - <<'EOF'
import json, os, shutil
D = 'news-pipeline/<DATE>'
pub = json.load(open(f'{D}/publish.json'))
src = f"{D}/video/video-{pub['date']}.mp4"      # remotion 输出的简名
dst = f"{D}/video/{pub['video']}"               # 平台展示名
if os.path.exists(src) and not os.path.exists(dst):
    shutil.move(src, dst); print('renamed ->', dst)
assert os.path.exists(dst), f'video missing: {dst}'
print('video OK', os.path.getsize(dst), 'bytes')
EOF

# ② ★ 标签页盘点（v3.81.0 新增，坑 403 新形态）
curl -s http://127.0.0.1:9222/json/list | python3 -c "
import json,sys
for t in json.load(sys.stdin):
    if t.get('type')=='page': print(t.get('url','')[:110])
"
# 缺哪个平台就开一个（mp 要带 token，从 probe_login 取）：
#   PUT http://127.0.0.1:9222/json/new?<urlencoded url>

# ③ 平台登录态用结构性判据，不用文本短语
#    公众号  = cgi-bin/home 且有 token=
#    视频号  = URL 不含 login.html
#    知乎    = /write 或 /p/<id>/edit 结尾
#    B站     = member.bilibili.com + 页面含「投稿」

# ④ CDP 分层探活（坑 404 / 262）
curl -s --max-time 8 http://127.0.0.1:9222/json/version   # 有 JSON = daemon 活着

# ⑤ ★ ws 挂起 → revive（v3.81.0 新增；顺序固定，别跳过）
#    connect_over_cdp 在 ws connected 后超时 → 跑 revive_frozen_tabs.py → 重试
python3 skills/ai-news-factory/templates/revive_frozen_tabs.py
# 期望末行 PLAYWRIGHT_OK；出现 DEAD: 是正常的，说明找到并解冻了冻结页
```

---

## 7. 收工三件事

```bash
# ① 回写 state.stages + heartbeat
# ② 终态标记（看门狗据此退出，不依赖 state.json）
touch data/logs/<issue>-DONE
# ③ 概念库回填（本期锚点用了就必须记，坑 355「未回写=未修复」）
#    usage-log.json 追加一条 + concepts.json 的 use_count/last_used 更新
```

---

## 附：本期（1105）实际踩点与耗时

| 阶段 | 实际 | 备注 |
|---|---|---|
| 抓取 | 458 抓 / 447 入库 / 31 批 / err=0 | 22:35:19 → 23:12:17（37 分钟） |
| 报告 / press / PDF | 31.2 KB / 11.8 KB / 471,350 B | 30 required / 31 forbidden；坑326 实测把「未确认传闻」从 forbidden 移除（本期是合法可信度标签） |
| 视频 | 237.61 s / 25.4 MB / 1920×1080 / 7128 帧 | 锚点 0.7319（`stealth_model`，第 7 景）；audit 38 门禁 0 failed |
| 字幕 | 108 行 | mp4 复核中位 +0.235 s、8 个场景块 Δ≤1 ms；1 个离群是 ASR 把中文数字写成别字导致锚定偏移，非真错位 |
| 上传 | 5 平台 | 公众号 100001886 / 知乎 2101475383770198107 / B站草稿 / 抖音假阴性 / 视频号草稿(9) |

**本期踩到并已回写模板的 8 条**（详见 SKILL.md v3.82.0 段）：
1. 上传 daemon 未在跑 → `/json/list` 返回非 JSON，`json.load` 直接崩。**开工第一件事是 `curl /json/version` 探活**，别误判成登录失效。
2. `wechat-sections-*.json` 缺 `must_have` / `must_not_have` 键 → `KeyError`。派生断言层要**逐键**对当日产物核对，不能只看语法。
3. issue word 写成「65 美元」而正文是「六十五美元」→ 断言炸。**数字口径以正文实际写法为准**（中文正文里数字常写中文）。
4. `stale_1104` 把 `KYC` 当禁词，但本期「没弹 KYC」是合法内容 → 禁词表要按「本期是否合法引用」逐词判断（坑 326 第三次命中）。
5. **坑403 复发**：mp home 标签不存在 → `PUT /json/new?<home+token>` 开一个即恢复。
6. **坑405/349 第三次复发**：抖音 `DY_E2E_FAILED` 仍是跳转后取空的假阴性，`readback` 阶段数据完好 → `done_with_caveat`，**不重传**。
7. **坑325 复发**：视频号 ready 判据在 `pct=25` 就放行 → 改为只认 `video` 元素数 + 时长 >200 s。
8. 视频号短标题 Vue setter 一次性赋值吞尾字 → 清空后用 `keyboard.type(delay=40)` 真实键入。

**耗时对比**：本期抓取 37 分钟（1104 是 32 分钟），视频链因断言层返工多花了约 40 分钟——**返工全部发生在断言层，不在内容层**，与坑 241 的模式一致。

---

## 附：本期（1104）实际踩点与耗时

| # | 坑 | 何时暴露 | 若不提前查会怎样 |
|---|---|---|---|
| 408 | 哨兵插在 shebang 前 | 跑 `_add_concepts` | **删哨兵时连 import 一起删 → NameError** |
| 409 | 锚点扩写两次 replace | 复核 ratio | **扩写段叠两遍，scene7 从 78s 变 104s，白跑一次 TTS** |
| 401 | 视频文件名 | zhihu 首行 | 四个平台全部启动失败（本期复发） |
| 403 | 标签页不存在 | mp 首行 | `mp home tab not found`，须 CDP 开标签（本期新形态） |
| 262 | ws 挂起 | zhihu 连接 | 连挂 2 次各 30s；跑一次 revive 即好（本期复发） |
| 380 | issue word 缺失 | douyin/channels 首行 | 补描述，**不是**删断言（本期复发） |
| 326 | 禁词误伤 | md2typ 编译 | `Pierlink`/`招股书` 本期合法，须移出禁词表 |
| — | 可信度枚举 | audit §4 | 写「官方/媒体多源」→ 不在五档内 |
| — | 选材表降序 | audit §10 | 按重要性排而非总分排 → 断言炸 |
| — | edge-tts 通路 | TTS | 直连可用、代理超时（**与 1103 相反**） |

---

## 附：上一期（1103）实际踩点与耗时

| # | 坑 | 何时暴露 | 若不提前查会怎样 |
|---|---|---|---|
| 396 | fetch 缺代理 | 抓取启动即失败 | 整期抓不到列表 |
| 397 | 锚点为 candidate | audit §6 | **整段 script + voiceover 重写** |
| 398 | 占比压线 0.7994 | gen_publish | 重跑 2 次 TTS，浪费约 5 分钟 |
| 399 | 台词未逐字 | audit §6 | 再重跑 1 次 TTS |
| 400 | `-I` 丢 faster_whisper | ASR 验收 | 验收做不成，只能用源 wav 假绿 |
| 401 | 视频文件名 | bili 上传首行 | 四个平台全部启动失败 |
| 402 | tags 脱节 | gen_publish 雷同断言 | 带着错误标签发出去 |
| 403 | 登录判据太松 | 平台探测 | **误报「已登录」，白等一轮** |
| 404 | CDP 间歇挂起 | 上传阶段 | 若误判为永久故障会去重启浏览器 |
| 405 | 抖音假阴性 | 上传验收 | 误报失败、重复上传 |
| 406 | wrapper 空转 | 抓取阶段 | 看门狗永久 RUNNING，整夜无人知晓 |
| 407 | 看门狗噪声 | 全程 | 51 KB 日志淹没状态切换 |
