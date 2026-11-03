# 派生自检清单（每期开工第一件事，机械可跑）

> 来源：坑 241（内容层必须重写）+ 坑 395（helper 从 templates/ 拷）+ **坑 396-407（v3.80.0，断言层必须一起重写）**。
> 配套文件：`templates/watchdog.md`（定时任务与看门狗的三层架构 + 沙箱验判定分支）。
> 核心判据：**派生不是「把日期替换掉」，是「让本期所有判据指向本期内容」。**
> 内容层漏改 → 成片讲上期事件（**会被口径检查抓到**）。
> 断言层漏改 → 本期正确内容被判 FAIL（**不会被告警抓到，只会逼你去修本来对的东西**）。

按顺序跑完下面 6 段，任一段失败就不许进下一阶段。

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

## 6. 上传前置检查（坑 401/403/404）

```bash
D=news-pipeline/<DATE>

# ① 视频文件名必须等于 publish.json 的 video 字段
python3 - <<'EOF'
import json, os
D = 'news-pipeline/<DATE>'
pub = json.load(open(f'{D}/publish.json'))
p = f"{D}/video/{pub['video']}"
assert os.path.exists(p), f'video missing: {p}'
print('video OK', os.path.getsize(p), 'bytes')
EOF

# ② 平台登录态用结构性判据，不用文本短语
#    公众号  = cgi-bin/home 且有 token=
#    视频号  = URL 不含 login.html
#    知乎    = /write 或 /p/<id>/edit 结尾
#    B站     = member.bilibili.com + 页面含「投稿」

# ③ CDP 分层探活（坑 404）
curl -s --max-time 8 http://127.0.0.1:9222/json/version   # 有 JSON = daemon 活着
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

## 附：本期（1103）实际踩点与耗时

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
