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

## 2d. 平台脚本必备步骤（v3.84.0 新增，1106 实测）

平台上传脚本目前只能从上一期派生（见第 0 段例外），所以每个「必备步骤」都要在派生后 grep 断言，不能等跑起来才发现缺。

**① 公众号 `mp_*_run.py` 必须同时有 `title` 步与 `author` 步（用户 1106 明确要求）。** 1106 只派生了 `title`，草稿作者栏为空。作者选择器是 `input[placeholder="请输入作者"]`，值 = 当期作者（按模式映射：日报「今日羊报AI」/ 周报「羊报AI周刊」/ 月报「羊报AI月报」，**≤8 字**），必须用原生 setter + `input` 事件；`verify` 回读并输出 `author_ok`，缺作者不许打印 `MP_VERIFY_OK`：

```python
inp = ed.locator('input[placeholder="请输入作者"]').first
inp.wait_for(timeout=10000)
inp.click()
inp.evaluate('''(el) => {
  const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  set.call(el, AUTHOR);   // AUTHOR = 当期作者（日报/周报/月报各自的名字）
  el.dispatchEvent(new Event('input', { bubbles: true }));
}''')
# verify 回读
author = ed.evaluate('''() => { const el = document.querySelector('input[placeholder="请输入作者"]'); return el ? el.value : null; }''')
author_ok = (author == AUTHOR)
```

派生后两连 grep（任一为空 = 派生器漏了，别进上传）：

```bash
S=news-pipeline/<DATE>/scripts/mp_*_run.py
grep -q '请输入作者' "$S" || echo AUTHOR_STEP_MISSING
grep -q 'author_ok'   "$S" || echo AUTHOR_VERIFY_MISSING
```

**② `mp` 的正文长度下限必须由本期文案预算推导（0.9 倍），禁止上期硬编码。** 1106 的 `assert ln > 1800` 是 1105 的口径，本期正文回读 **1702** → 正确内容被判 `MP_VERIFY_FAILED`。`body` / `save` / `verify` 三处共用同一个 `floor`：

```python
expect = sum(len(h) + sum(len(x) for x in ps) for h, ps in SECTIONS) + sum(len(x) for x in TAIL)
floor = int(expect * 0.9)          # 本期纯文本预算的 90%
assert ln > floor, f'body paste failed bodyLen={ln} floor={floor}'
```

派生后断言「长度比较式里没有 1800」（`wait_for_timeout(1800)` 与注释里的历史说明不算，只拦比较）：

```bash
grep -nE '(>|=)\s*1800' news-pipeline/<DATE>/scripts/mp_*_run.py && echo HARDCODED_1800 || echo FLOOR_OK
```

**③ `channels_upload` 的草稿验收日期用 `rf'11月0?{day}日'`（`day` 取自当期日号），禁止 `includes('11月6日')` 这类写死日号。** 视频号草稿列表页的日期是**零填充**（`11月06日`），`includes('11月6日')` 在本期会漏判成「草稿不存在」。正则同时兼容两种写法：

```python
DATE_RE = re.compile(rf'11月0?{day}日')      # day 取自当期（如 6）；列表页零填充，标题回读不零填充
...
v = page.evaluate('''(pat) => {
  const re = new RegExp(pat);
  const w = document.querySelector('wujie-app');
  const t = (w && w.shadowRoot && w.shadowRoot.body ? w.shadowRoot.body.innerText : document.body.innerText) || '';
  return { hasTitle: re.test(t), sample: t.replace(/\\s+/g, ' ').slice(0, 400) };
}''', DATE_RE.pattern)
assert v['hasTitle'], f"draft not found: {v['sample'][:200]!r}"
```

**④ 写盘安全：状态 JSON 与 Markdown 清单不得复用同一变量名。** 1106 期 01:24 一次状态写入把 `.pipeline-state-2026-11-06.json` 写进了 `review-checklist.md` 路径（同一变量 `p` 先后指向两个文件），清单被 JSON 覆盖；渲染已在 01:17 完成所以门禁未受影响，但清单只能按实跑结果重建。派生器与临时 Python 片段统一用两个变量名，写完立即 `head -1` 回读：

```python
state_path     = '.pipeline-state-<DATE>.json'
checklist_path = 'news-pipeline/<DATE>/review-checklist.md'   # 不复用变量
json.dump(state, open(state_path, 'w'), ensure_ascii=False, indent=2)
open(checklist_path, 'w').write(md)
```

```bash
head -1 .pipeline-state-<DATE>.json                 # 必须以 '{' 开头
head -1 news-pipeline/<DATE>/review-checklist.md    # 必须以 '# ' 开头
```

---

## 2e. **断言表 × 本期成品文案 双向交叉 grep（v3.85.0 新增，1107 一期连踩三次）**

2d 管的是「平台脚本必备步骤**有没有**」，本节管的是「平台脚本的**判据指向哪一期**」。
1107 期的三次 `MP_VERIFY_FAILED` / `AssertionError` 全部出自这里，且**内容层完全正确**：

| # | 文件 | 症状 | 性质 |
|---|---|---|---|
| 1 | `mp_<issue>_run.py` | `stale_<prev>` 里含 `英伟达`，但它是本期**股价主线** | 上期禁词表误伤 |
| 2 | `channels_upload_<issue>*.py` | issue-word 整块还是上期的（断言 `ERNIE` **必须在场**） | 断言表未重写 |
| 3 | `gen_publish_<issue>.py` | `douyin/channels.description` 缺 `Qwen 4` | 内容该补，不是断言该放 |

**派生完立刻跑这条（一条命令覆盖 A/B/C 三段）**：

```bash
python3 templates/assertion_crosscheck.py --date <DATE> \
  --prev-words <上期词1> <上期词2> <上期词3> \
  --issue-words <本期词1> <本期词2>
```

它做六件事：A 本期词是否真在成品文案里；B 上期词是否漏进成品文案；C 上期词是否留在
**正向断言**里；D `publish.video` 是否等于实际文件名 + `zhihu.article_id` 是否被清空；
E 内容层哨兵是否清干净；F `review-checklist` 是否指向本期。

### ⚠️ 交叉检查工具本身也会犯坑 326（v3.85.0 现场教训）

首版 `assertion_crosscheck.py` 在 **1107 已完成的正确产物上**报了 **13 处假 FAIL**。
原因不是产物有问题，是判据写错了。**三种形态**，每个写判据的人都会遇到：

| 形态 | 错误判据 | 正确判据 |
|---|---|---|
| **① 把工作笔记当成品文案** | 整篇读 `script-<date>.md`，命中了「3 天去重」段落里合法列出的近三天事件（`FlashProve` / `ERNIE` / `白宫住宅代理`） | 只取 `## 正文` 之后的章节，并剥离「去重/历史/上期」说明行 |
| **② 不区分「要求在场」和「要求缺席」** | 见到 `for w in [...]: assert w not in DESC`（**禁词断言**）和 `'stale_<prev>': (...)`（**残留检测**）也报「上期词还在断言表里」 | 按语义判：只有 `assert w in ...`（正向断言）才可能是坑 326；含 `not in` / `stale_` / `prior_` 的一律跳过 |
| **③ 把 JSON 判据键当内容载荷** | 整份 `json.load` 后 `json.dumps` 塞进 blob，于是 `wechat-sections-<issue>.json` 的 `must_not_have` 里那 8 个上期词全被判「漏进成品文案」 | JSON 按**键名语义**取载荷：`sections`/`tail`/`scenes`/`text`/`title`/`description` 收，`must_have`/`must_not_have`/`forbidden`/`stale*`/`prior*`/`checks`/`issue_words`/`COLLOQ` 一律丢 |

**结论（本期最该记住的一条）**：判据的语义是「**要求在场**」还是「**要求缺席**」，
比「这个词来自哪一期」更重要。禁词表里出现上期词是**功能**，不是残留。
同理，**同一个 JSON 文件里「发出去的内容」和「用来判它的表」必须分开读**。

**纪律**：任何新写的门禁/检查器，**必须做双向控制**——
① 在已通过的正确产物上跑，**必须 PASS**；② 喂一个已知错误的输入，**必须 FAIL 且非零退出**。
只测单向等于没测。如果它在正确产物上报 FAIL，先怀疑判据，再怀疑产物：
这是「判据自欺」的反向形态，不是假绿而是**假红**，同样会把你逼去改本来对的东西。

> 1107 现场：假红修了**两轮**才干净——第一轮修了 ①②，第二轮才发现 ③（`must_not_have`）。
> 而且第一轮验证时我用 `| tail` 接管道，`$?` 拿到的是 `tail` 的退出码，**假 PASS 过一次**。
> 验证退出码必须 `> log 2>&1` 后单独读 `$?`，**不要接管道**。


**判据纪律**：

- **B 命中 = 补描述，不是放宽断言**（坑 380）。改的是 `gen_publish` 的 `description`，不是删 `assert`。
- **A 命中 = 该词是本期合法内容**，从禁词表移出，同时把「本期真正缺席」的上期词补进去（否则禁词表就形同虚设）。
- **C 命中要先判断**：是本期合法引用（如 1103 的 `招股书`）就移出禁词表；是真残留就改文案。**不要为了让它过而放宽断言**（坑 326 第三次命中的教训）。

**⚠️ 连带必查：重跑 `gen_publish` 会清空 `platform.zhihu.article_id`。** 该字段由上传脚本回填、生成器里恒为 `''`。

```bash
python3 - <<'EOF'
import json
pp = 'news-pipeline/<DATE>/publish.json'
pub = json.load(open(pp, encoding='utf-8'))
aid = pub['platform']['zhihu'].get('article_id')
if not aid:
    print('WARN: zhihu.article_id empty — 若本期已上传过知乎，必须回填旧 id 后再进上传')
else:
    print('zhihu.article_id =', aid)
EOF
```

---

## 2f. **视频号封面必须回读图元尺寸（v3.85.0 新增，坑 419）**

`channels_upload_<issue>.py cover` 打印 `CH_COVER: ok` **不代表封面落上了**。1107 实测：脚本报 `dialog_closed= False`，
回读编辑页 `.vertical-img-size` 仍是 `720×405`（视频默认帧缩略），正确值应为 **`810×1080`**（`1152×1536` × 0.703）。

**根因**：该弹窗变体的确认控件不是 `<button>`，脚本按 `button` + `/确认|完成|保存/` 正则匹配到的是**页面级「保存草稿」**，
于是在错误元素上点了坐标 / 直接跳过。

**判据（回读图元，不问按钮）**：

```python
st = page.evaluate('''() => {
  const sr = document.querySelector('wujie-app').shadowRoot;
  const pick = cls => { const e = sr.querySelector('.'+cls); if (!e) return null;
    const i = e.tagName === 'IMG' ? e : e.querySelector('img');
    return i ? {nw: i.naturalWidth, nh: i.naturalHeight} : null; };
  return {v: pick('vertical-img-size'), h: pick('horizon-img-size')};
}''')
assert st['v'] and abs(st['v']['nw'] / st['v']['nh'] - 1152 / 1536) < 0.02, \
    f"vertical cover NOT applied: {st['v']}（720×405 = 视频默认帧，说明 cover 步静默失效）"
```

**补做路径**（不依赖原 cover 步）：草稿箱首条 → 悬停 `.post-draft-item` → 点 `.opr .opr-item` → 进入 `post/create`
→ 点 `.vertical-img-wrap` 中心 → `page.locator('wujie-app input[type=file][accept*="image"]').first`
喂 `images/vertical-3-4.png` → **真实坐标**点确认 → 回读 `(810, 1080)`。

⚠️ **该弹窗底部可能是 `直接编辑 / 使用素材 / 保存草稿 / 手机预览 / 发表`（没有「确认」）。此时不要为了关弹窗去点底部按钮**——
`保存草稿` 与 `发表` 相邻，误触「发表」是不可逆的。横封面保持视频默认帧是可接受状态（视频号展示以竖封面为主），
**如实记录**即可，不要谎报「双封面已上」。

---

## 2g. **`review-checklist.md` 必须整份重写，且排在 audit 之前（v3.85.0 新增，坑 420）**

`_derive_video_<issue>.py` 只给清单加 `<!-- __REWRITE_FOR_<issue>__ -->` 哨兵、**不替换正文**
→ §一~§十三 全是上期文案（1107 渲染完才发现 §十三 还写着上期 appmsgid、§六 写着上期锚点）。

它是**渲染门禁的一部分**，不能是上期快照。流水线顺序固定为：

```
派生脚本 → 删内容层哨兵 → 重写 review-checklist（按本期实跑前状态）→ audit → 渲染 → 用实跑结果回填 checklist
```

自检：

```bash
C=news-pipeline/<DATE>/review-checklist.md
grep -n "<上期期号>\|<上期appmsgid>\|<上期锚点概念>" "$C" && echo CHECKLIST_STALE || echo CHECKLIST_OK
grep -rn "__REWRITE_FOR_<issue>__" news-pipeline/<DATE>/ | wc -l   # 渲染前应为 0
```

---

## 2h. **launch wrapper 必须防「多实例并存」（v3.85.0 新增，坑 422）**

`_launch_<issue>.sh` 的 pidfile **只在启动瞬间检查一次**。1106 上午反复试跑留下 **4 个** wrapper，
它们各自写 pidfile、各自 `while` 睡到同一个 22:35 —— 到点**同时醒来抢跑**。

派生器在等待循环里加「归属校验」：

```bash
while [ "$(date '+%s')" -lt "$TARGET_EPOCH" ]; do
  [ "$(cat "$PIDFILE" 2>/dev/null)" = "$$" ] || { echo "superseded by $(cat "$PIDFILE")"; exit 0; }
  sleep 30
done
```

开工前自检（真仓库）：`pgrep -fl "_launch_<issue>" | wc -l` 应为 **1**（或 0，若尚未启动）。

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

# ① 视频文件名必须等于 publish.json 的 video 字段（坑 401）+ ffprobe 流完整性深度校验（坑 411）
python3 - <<'EOF'
import json, os, shutil, subprocess
D = 'news-pipeline/<DATE>'
pub = json.load(open(f'{D}/publish.json'))
src = f"{D}/video/video-{pub['date']}.mp4"      # remotion 输出的简名
dst = f"{D}/video/{pub['video']}"               # 平台展示名
if os.path.exists(src) and not os.path.exists(dst):
    shutil.move(src, dst); print('renamed ->', dst)
assert os.path.exists(dst), f'video missing: {dst}'
assert os.path.getsize(dst) > 1024 * 1024, f'video too small: {dst}'

# ffprobe 深度校验 moov atom 与时长（坑 411：防生成的视频打不开）
cmd = [
    'ffprobe', '-v', 'error',
    '-show_entries', 'format=duration,size',
    '-show_entries', 'stream=codec_type,width,height,duration',
    '-of', 'json', dst
]
r = subprocess.run(cmd, capture_output=True, text=True)
assert r.returncode == 0, f'ffprobe failed (moov atom missing/corrupt): {r.stderr.strip()}'
meta = json.loads(r.stdout)
dur = float(meta.get('format', {}).get('duration', 0))
assert dur >= 30.0, f'video duration too short: {dur}s'
streams = meta.get('streams', [])
assert any(s.get('codec_type') == 'video' and s.get('width') == 1920 and s.get('height') == 1080 for s in streams), 'video stream invalid'
assert any(s.get('codec_type') == 'audio' for s in streams), 'audio stream invalid'
print('video verified OK', os.path.getsize(dst), 'bytes', f'duration={dur:.2f}s')
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

# ④ CDP 分层探活（坑 404 / 262 / ★423）
#    ★ 1108 教训：先分层，再决定动作。三种 CDP 故障根因不同，别混为一谈。
#      ECONNREFUSED 9222          → daemon 进程不存在 → 起 browser_daemon.py（别读登录态、别等自愈）
#      curl 通 + ws 后超时        → attach 层故障     → revive_frozen_tabs.py → 重试，绝不重启浏览器
#      curl 通 + 整体挂起         → 冻结 target       → 切 raw CDP（cdp_helper.py）
curl -s --max-time 8 http://127.0.0.1:9222/json/version   # 有 JSON = daemon 活着
# 不通就起（视频链不需要 CDP，可以先跑完 PDF/封面/audit/生图/TTS/字幕/渲染）：
#   nohup python3 skills/ai-news-factory/templates/browser_daemon.py > data/logs/<issue>-daemon.log 2>&1 &
#   sleep 8; tail -1 data/logs/<issue>-daemon.log    # 期望 DAEMON_READY port=9222

# ⑤ ★ ws 挂起 → revive（v3.81.0 新增；顺序固定，别跳过）
#    connect_over_cdp 在 ws connected 后超时 → 跑 revive_frozen_tabs.py → 重试
python3 skills/ai-news-factory/templates/revive_frozen_tabs.py
# 期望末行 PLAYWRIGHT_OK；出现 DEAD: 是正常的，说明找到并解冻了冻结页

# ⑥ ★ step 词表统一性自检（v3.86.0 新增，坑 425）
#    传 all 给不认 all 的脚本 = 静默空转 exit 0（最坏的一类失败）。
#    派生后先确认每个平台脚本的 VALID 集合，或全部支持 all，或全部不支持 + runner 显式逐步调用。
for f in mp_<issue>_run.py zhihu_upload_<issue>.py bili_upload_<issue>.py \
         douyin_e2e_<issue>.py channels_upload_<issue>.py; do
  echo "== $f"; grep -n "sys.argv\[1\]\|STEP =\|step =" "$f" | head -2
  grep -q "'all'\|\"all\"" "$f" && echo "   supports all" || echo "   ⚠️ NO 'all' — runner 必须逐步调用"
done
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

## 附：本期（1108）实际踩点与耗时

| # | 坑 | 何时暴露 | 若不提前查会怎样 |
|---|---|---|---|
| 423 | `ECONNREFUSED 9222` | 上传链第一行 | 五个平台一次全灭；易误判为「登录失效」或「等自愈」→ 空转 |
| 424 | 知乎图片失败块计入 IMG | zhihu images 步 | **假绿**：7 图全灭也打印 PASS，草稿缺图发出 |
| 425 | channels 脚本不认 `all` | channels 步 | **静默空转 exit 0**，日志像跑过了，实际一平台全漏 |
| 426 | `dialogOpen` 祖先链假阳性 | channels cover 步 | 误信坑 419「弹窗没关=封面没落上」，去重传封面（有误触发表风险） |

| 阶段 | 实际 | 备注 |
|---|---|---|
| 抓取 | 307 入库 / 22 批 / err=0（队列 323） | 22:35 → 23:01 |
| 报告 / press / PDF | 10.6 KB / 5.8 KB / 272,643 B | 9 required / 4 forbidden；禁词 × 当日报表交叉 grep 过 |
| 视频链 | 207.48 s 音频 → 207.66 s 成片 / 24.6 MB | audit 38/38；锚点 `multimodal` 0.7111；**一次过** |
| 上传链 | 五平台草稿 | 卡在坑 423（daemon 没起），起完即通；坑 424/425/426 全在判据层 |

**本期最大教训**：视频链零返工，上传链的每一步返工**都不是内容错**，而是「判据在骗人」或「调度没对齐」。
枚举判据时先问一句：**这个判据在失败时会给出什么读数？** 若答案也是「pass」，它就不是判据。

---

## 附：本期（1105）实际踩点与耗时

| 阶段 | 实际 | 备注 |
|---|---|---|
| 抓取 | 458 抓 / 447 入库 / 31 批 / err=0 | 22:35:19 → 23:12:17（37 分钟） |
| 报告 / press / PDF | 31.2 KB / 11.8 KB / 471,350 B | 30 required / 31 forbidden；坑326 实测把「未确认传闻」从 forbidden 移除（本期是合法可信度标签） |
| 视频 | 237.61 s / 25.4 MB / 1920×1080 / 7128 帧 | 锚点 0.7319（`stealth_model`，第 7 景）；audit 38 门禁 0 failed |
| 字幕 | 108 行 | mp4 复核中位 +0.235 s、8 个场景块 Δ≤1 ms；1 个离群是 ASR 把中文数字写成别字导致锚定偏移，非真错位 |
| 上传 | 5 平台 | 公众号 100001886 / 知乎 2101475383770198107 / B站草稿 / 抖音假阴性 / 视频号草稿(9) |

**本期踩到并已回写模板的 11 条**（详见 SKILL.md v3.82.0 段）：
1. 上传 daemon 未在跑 → `/json/list` 返回非 JSON，`json.load` 直接崩。**开工第一件事是 `curl /json/version` 探活**，别误判成登录失效。
2. `wechat-sections-*.json` 缺 `must_have` / `must_not_have` 键 → `KeyError`。派生断言层要**逐键**对当日产物核对，不能只看语法。
3. issue word 写成「65 美元」而正文是「六十五美元」→ 断言炸。**数字口径以正文实际写法为准**（中文正文里数字常写中文）。
4. `stale_1104` 把 `KYC` 当禁词，但本期「没弹 KYC」是合法内容 → 禁词表要按「本期是否合法引用」逐词判断（坑 326 第三次命中）。
5. **坑403 复发**：mp home 标签不存在 → `PUT /json/new?<home+token>` 开一个即恢复。
6. **坑405/349 第三次复发**：抖音 `DY_E2E_FAILED` 仍是跳转后取空的假阴性，`readback` 阶段数据完好 → `done_with_caveat`，**不重传**。
7. **坑325 复发**：视频号 ready 判据在 `pct=25` 就放行 → 改为只认 `video` 元素数 + 时长 >200 s。
8. 视频号短标题 Vue setter 一次性赋值吞尾字 → 清空后用 `keyboard.type(delay=40)` 真实键入。
9. **坑410（公众号 ProseMirror 节点事务与存草稿）**：严禁按 Escape 取消事务（导致 16 图未替换）；每张图必做单调严格递减断言（`after == before - 1`）；同标签禁 `goto` 避免 abort 异步存草稿；合集四步真控件点击（`.allow_click_opr.js_article_tags_label`）。
10. **坑411（视频完整性探活门禁）**：拒绝纯文件大小假绿，必须用 `ffprobe` 验证 `moov` atom 存在且 duration > 0，杜绝「生成的视频打不开」。
11. **坑412（跨平台生僻字符合集/专栏联动）**：多端合集（如「虢礫緙嘞」）在 `publish.json` 独立声明，DOM 匹配严禁裸写 RegExp，未建合集走软门禁留痕不阻断存草稿。

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
