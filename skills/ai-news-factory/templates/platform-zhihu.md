# 知乎平台模块（文章派生 + 合规审核 + 草稿上传）

> 本文件是 `SKILL.md` 的**平台子模块**，由 SKILL.md 的 Phase 10.6 / Phase 14 引用。
> 版本：v3.75.0（2026-10-31 日报三期实跑：专栏「第 0 级」失败 + 草稿箱 `?type=article` + 登录判据假阴性 + `ZHIHU_DRAFT_OK` 覆盖不全，坑 352–355、362–364）
> 上一版：v3.74.0（2026-10-30 二次实跑：post-to-video 帖文成片，raw CDP + 坑 344–347）
> 合规依据（同目录）：
> - `知乎关于 AI 辅助创作内容的治理细则.md`
> - `知乎社区规范.md`

---

## 0. 定位与铁律

| 项 | 规则 |
|---|---|
| 内容来源 | **从当期公众号文章派生**（`wechat-article-<DATE>.md`），不另写一套 |
| 落盘 | `news-pipeline/<DATE>/zhihu-article-<DATE>.md` |
| 上传 | **只存草稿**。`发布` 按钮**永不进入脚本逻辑** |
| 创作声明 | **必须**设为「包含 AI 辅助创作 作者对内容负责」 |
| 专栏 | 发布到专栏「今日羊报 AI」 |
| 审核 | 生成后必须过 §2 审核清单并落盘 `review-checklist.md`，未过不得上传 |

---

## 1. 从公众号文章派生知乎文章

### 1.1 输入 / 输出

- 输入：`news-pipeline/<DATE>/wechat-article-<DATE>.md`（Phase 10.3 产物）
- 输出：`news-pipeline/<DATE>/zhihu-article-<DATE>.md`
- 配图复用：`news-pipeline/<DATE>/wechat-images/scene<i>.jpg`（已为 JPEG，知乎原生支持）

### 1.2 必须做的改造

公众号与知乎不是同一文体，**禁止直接复制粘贴**：

| 维度 | 公众号原文 | 知乎要改成 |
|---|---|---|
| 开头 | `> 今日羊报 AI · YYYY-MM-DD` 引语块 | 改为信息型导语（1–2 句，说清本篇讲了哪几件事） |
| 小标题 | `## 1. {事件}` 编号式 | 保留 `##` 层级，但标题写成**信息句**（可去掉序号） |
| 正文 | 偏口语、短段落 | 补一句「为什么重要」，段落可稍长；**不要**加主观评价 |
| 结尾 CTA | 「点个赞、转发」「关注今日羊报AI，每天9点」「评论区聊聊」 | **整段删除**（知乎反感导流；也违反社区规范「恶意营销导流」） |
| 图片来源 | `![](images/sceneN.png)` | 改用 `![](wechat-images/sceneN.jpg)` |
| AI 声明 | 公众号无 | **正文末尾必须有**（见 1.4） |

### 1.3 结构模板

```markdown
{标题：≤100 字，信息型，不用「4条重磅」式营销后缀}


{导语：1–2 句，说清本篇覆盖哪几件事}

## {事件一的信息句标题}

{2–3 段：发生了什么 → 为什么值得注意}

![](wechat-images/scene2.jpg)

## {事件二的信息句标题}

{...}

![](wechat-images/scene3.jpg)

...

## 最后

{把几条串成一句判断，不要喊口号}

---

**AI 辅助创作说明**：本文由作者主导选题、核实与撰写，使用 AI 辅助整理公开信息与润色文字；所有事实性内容均经作者人工核对，作者对最终内容负责。
```

### 1.4 AI 声明是硬要求（两个层面都要做）

知乎治理细则要求「主动添加『包含 AI 辅助创作』创作声明」+「对 AI 使用情况进行适当的披露」。因此**两层都做**：

1. **平台控件**：上传时把「创作声明」设为 `包含 AI 辅助创作 作者对内容负责`（见 §3.6）
2. **正文披露**：文末写一段 AI 辅助创作说明（说明用途 + 作者负责）

只做第 1 层、不写正文说明，在细则口径下仍属披露不足。

> **🔴 v3.78.0 硬要求（2026-11-02 1102 期复盘）：文末披露段必须逐字使用下面的固定句，禁止改写。**
>
> ```
> **AI 辅助创作说明**：本文由作者主导选题、核实与撰写，使用 AI 辅助整理公开信息与润色文字；所有事实性内容均经作者人工核对，作者对最终内容负责。
> ```
>
> **禁止**把这一段写成「本文由「今日羊报 AI」基于 linux.do 社区 X 月 X 日 A 至 B（N 小时窗口）的公开讨论整理生成：双源合并去重后落入窗口 265 帖，全量抓取正文（18 批，valid 265，err 0）……」这类**带来源平台名 + 抓取统计**的版本。两条理由：
> 1. **披露的是「AI 参与程度」，不是「数据来源说明」**——写抓取批次数、valid/err 计数，答的不是细则问的那个问题；信源清单属于日报的「数据来源说明」小节，不属于知乎正文。
> 2. **正文出现第三方平台名等于给外部导流**，与知乎《社区规范》§四（禁止诱导至第三方平台）的口径相冲；平台名一旦进正文，人工复核每次都要重判一遍。
>
> 派生脚本里请把这段当**常量**（和标题、尾部 CTA 一样），不要跟着日报统计字段拼串。

> **🔴 v3.79.0 补强（W43 周报复发）：这条规则必须写进「派生器模板」，否则下一期原样复活。**
> 坑 388 在 1102 日报脚本里已经落地成硬断言，但 **W43 周报的知乎稿从更早的模板派生**，于是同一句错话又出现了：
> > 本文由「羊报AI周刊」基于 **linux.do 社区** 2026-10-26 至 2026-11-01 的公开讨论整理生成：周内去重 2453 帖，过滤后收录 2365 帖……
>
> **状态：该期稿件已按固定句改正。**
> **铁律：`AI_DISCLOSURE` 常量与禁词断言属于「随 skill 演进」的部分，派生时从 `templates/` 拷，不要从上一期脚本拷。** 派生后立刻跑：
> ```bash
> grep -c 'linux\.do\|linuxdo\|linux do' <新稿>.md   # 必须 0
> grep -c '本文由作者主导选题'            <新稿>.md   # 必须 1
> ```
> **适用范围不止知乎**：公众号图文、视频口播、字幕、B站/抖音/视频号简介、封面大字，全部禁止出现来源平台名（skill 主文档 v3.17.0 已有此规则，本期再次踩到说明它只写在「注意事项」里、没写进派生器自检）。**派生后对全部产出物跑一遍禁词 grep，不要只查知乎稿。**

> **🔴 v3.96.0 补强（2026-11-14 1114 期复发，坑 467）：只断言「固定句存在」不够，必须「整句全等 + 全文禁平台名」两道。**
> 1114 期把披露段写成「固定句 + 一句来源说明」，而脚本判据是 `assert AI_DISCLOSURE in _md`——
> 自拟句恰好以固定句为**前缀**，`in` 恒真，带来源平台名的版本一路进草稿，人工复核才发现。
> **固定句是「整句」，不是「开头」**：
> ```python
> import re
> norm = lambda s: re.sub(r'\s+', '', s)
> assert norm(text).count(norm(FIXED_WHOLE)) == 1, '披露段必须是固定句且只出现一次'
> assert not re.search(r'linux\.do|linuxdo|linux do', text, re.I), '正文出现来源平台名'
> ```
> `FIXED_WHOLE` 从本节固定句**逐字拷贝**（含标点与全/半角），禁止从上期脚本或上期稿件拷。
> 另：`templates/check-derived-content.py` 只扫 `script` / `voiceover` / `prompts` / `sections` 四层，
> **不扫 `zhihu-article-*.md` / `wechat-article-*.md`**；`articles` 阶段的 `ai_disclosure: true` 是 worker **自报**。
> **「checker PASS」不等于「文章合规」**——要么把两份 article 加进 `layers`，要么在 `Validator.validate('articles')`
> 里硬断言「固定句恰 1 次 + 全文 0 处来源平台名」。

### 1.5 标题规则

- 上限 **100 字**（编辑器 placeholder 明示「最多 100 个字」）
- 不要带 `【YYYY-MM-DD】` 前缀（那是公众号/视频平台的排版习惯，知乎不需要）
- 不用「4条重磅AI新闻一次看完」这类营销后缀
- 示例：`Claude 账号进入 KYC 与封号双收紧，Opus 一个额度做完了 Astra 半天的活`
- **🔴 稿件首行的 `#` 必须剥掉，而且要在两个地方剥**（坑 375，2026-11-01 实测）
  - 知乎稿件首行按惯例写成 `# 标题`。上传脚本的 `load_title()` 若原样返回，标题框里就成了 `# Claude…`（多出 `# ` 两字符）。
  - `build_html()` 也用同一首行算 `title_md`，**只改一处会立刻炸 `assert TITLE == title_md`**，而报错位置在 `main()`，看起来像稿件有问题。
  - 两处都写：`if first.startswith('#'): first = first.lstrip('#').strip()`，并加断言 `assert first, f'{md_path} 首行只有 # 号'`。

### 1.6 派生后必做的两条断言（都是「静默成功」陷阱）

**① 图片标记数**（坑 376）：从公众号稿派生知乎稿时只搬文字、漏掉 `![](...)`，脚本 `imgs=0`，`step_images` 输出 `0 IMG blocks, placeholders left=0` —— **断言全过、零报错，稿子里就是没图**。
- 断言 `md.count('![') == 预期图数`（预期 = 正文 `## ` 小节数，排除「编辑判断」「AI 辅助创作说明」这类无图小节）。
- 补图正解：在**每个 `## ` 小节之后**插 `![场景{i}](wechat-images/scene{i}.jpg)`，插完重跑 `body` 步（会重贴带占位符的正文），再跑 `images` 步逐个替换占位块。

**② 视频块是否真落块**（坑 377）：见 §3.7 末尾的上传可靠性说明。

### 1.7 派生源铁律：从 `templates/` 拷，不要从上一期脚本拷（坑 395）

**W43 周报实例**：`坑 388` 的 `AI_DISCLOSURE` 硬断言两天前就在 1102 日报脚本里了，但周报的知乎稿**从更早的模板派生**，于是同一句错话原样复活；同期的 `cdp_w43.py` 也还是旧箭头判定，本期又炸出 `async async`（而 `templates/cdp_helper.py` 早在 v3.67.0 就改成了括号深度扫描）。

**为什么会这样**：上一期脚本是「那天正确的快照」，不是「今天正确的源」。拷它可以跑通，但它把**已经修好的坑一起拷回了解放前**。

**派生第一件事（写进派生器脚本头部注释）**：

```bash
cp templates/cdp_helper.py        scripts/cdp_<id>.py        # ✅
cp ../<上期>/scripts/cdp_*.py     scripts/cdp_<id>.py        # ❌ 会把旧 bug 带回来
```

`AI_DISCLOSURE`、禁词表、`assert_identity`、`assert_editor`、`_is_arrow_at_top` 都属于**随 skill 演进**的部分，一律从 `templates/` 取。

**派生后立刻跑的四条自检**（缺一条就别往下走）：

```bash
D=<新期目录>
# 1. AI 声明：固定句在、平台名不在
grep -c '本文由作者主导选题' "$D/zhihu-article-"*.md           # 必须 1
grep -c 'linux\.do\|linuxdo\|linux do' "$D/zhihu-article-"*.md  # 必须 0
# 2. helper 没落后于模板
diff <(sed -n '/_is_arrow_at_top/,/return False/p' "$D/scripts/cdp_"*.py) \
     <(sed -n '/_is_arrow_at_top/,/return False/p' templates/cdp_helper.py) && echo HELPER_OK
# 3. 图片标记数 == 预期
grep -c '!\[' "$D/zhihu-article-"*.md
# 4. 全产出物禁词（不只知乎稿）
grep -rn 'linux\.do\|linuxdo\|linux do' "$D"/*.md "$D"/publish.json
```

**判据形态归位**：`坑 355`（未回写 = 未修复）说的是「临时探针里的修复不算修复」；坑 395 是它的**第二种形态**——修复只写进了当期实例，没写进派生源。共同点是「下次还会犯」，区别是前者在内存里、后者在文件系统里，**更隐蔽**——因为在当期脚本里能搜到那句断言，看着像已经修好了。

---

## 2. 合规审核清单（上传前必须逐项勾选并落盘）

写到 `news-pipeline/<DATE>/review-checklist.md` 的「知乎」小节，未勾完不得上传。

### 2.0 总清单（十一条，全部 PASS 才准进 §3）

```
☐  1. 稿子由公众号文章派生，事实与当期视频/公众号完全一致，未新增未经核实的信息
☐  2. 有「编辑判断」段（≥120 字，作者视角的判断而非复述）——AI 治理细则的前提
☐  3. 公众号 CTA 已整段删除（点赞/转发/关注/评论区），无导流
☐  4. 标题 ≤100 字、无品牌后缀、无营销后缀、无标题党禁词
☐  5. 已逐条人工核对事实；无文不对题、无图文不相关、无事实错误、无虚假谣言
☐  6. 主要智力劳动由作者完成；非整篇机器生成、非拼凑；单期只发 1 篇不刷量
☐  7. 正文已披露 AI 使用目的与相关部分 —— **必须是 §1.4 的固定句**，且全文 grep 不到来源平台名（`linux.do` / `linuxdo`）（坑388）
☐  8. 上传时平台「创作声明」设为「包含 AI 辅助创作 作者对内容负责」并回读通过
☐  9. 无违法违规 / 不友善 / 低俗 / 侵权 / 抄袭内容；引用已注明来源
☐ 10. 配图与所在小节对应（`zhihu-images/scene<i>.jpg`），非无关配图
☐ 11. 新闻类内容已标注信息来源（「添加来源」或正文来源表述）
```

以下 2.1 / 2.2 / 2.3 是上述十一条的**依据与展开**，判分歧义时以内文为准。

### 2.1 AI 辅助创作专项（依据 `知乎关于 AI 辅助创作内容的治理细则.md`）

```
☐ 已添加平台「创作声明」= 包含 AI 辅助创作 作者对内容负责
☐ 正文已披露 AI 使用目的（如：整理公开信息 / 文字润色）与相关部分
☐ 主要智力劳动由作者完成，AI 仅为辅助（非整篇生成、非拼凑）
☐ 已逐条人工核对事实；无文不对题、无图文不相关、无事实错误、无虚假信息
☐ 未批量发布生成/拼凑内容（单期只发 1 篇，不刷量）
```

**细则列明的重点治理行为（命中即不可发）**：
- 滥用 AI 创作，大量发布生成、拼凑内容
- 利用 AI 生成并发布低质内容：文不对题、图文不相关、事实错误、虚假谣言

**后果**：账号提示/处罚；内容标识、减少分发、折叠、建议修改、删除；批量违规时展示干预。

### 2.2 社区规范专项（依据 `知乎社区规范.md`）

```
☐ 无违法违规内容（危害国家安全、暴恐、谣言、人口贩卖、公民信息、洗钱、非法网络资源等）
☐ 无不友善/攻击性表达
☐ 无低质、低俗、标题党（标题与内容一致）
☐ 无抄袭、无未授权转载（引用注明来源）
☐ 无侵权（名誉/肖像/隐私/著作权）
☐ 无虚假认证或冒充
☐ 无恶意营销导流（已删除公众号式「关注/转发/点赞」CTA，未放外链引流）
☐ 不涉及未成年人伤害
☐ 新闻类内容已标注信息来源（见 §3.10「内容来源」）
```

### 2.3 与视频口径的对齐

- 视频脚本里已过关的敏感词过滤、A/B 档选题规则同样适用于知乎文章：**融资/IPO/外泄/监管对抗类不进知乎标题**（与公众号口径一致）
- 文章内容与当期视频/公众号**事实必须一致**，不得出现视频里删掉、文章里又写回来的表述

---

## 3. 上传流程（只存草稿）

### 3.1 入口与登录态

- 入口：`https://www.zhihu.com/creator/manage/creation/article`
- 登录判据（**v3.75.0 修正**）：侧栏有 **「草稿箱(N)」/「创作主页」** 且 **无扫码/密码登录** → 已登录。**不要**把「页面出现『立即创作』按钮」当判据——1031 实测该按钮可以整个不存在（`hasCreate: False`）而同页侧栏「草稿箱」正常，账号也确实登录着；按旧判据会在第一步就把自己拦下（坑 353 同族的假阴性）。出现扫码/密码登录即未登录 → 停下报错，不重试
- 登录后该页可见：内容管理 / 数据中心 / 创作成长 / 个人中心 等侧栏

### 3.2 打开编辑器

点「立即创作」→ **会新开一个标签页** `https://zhuanlan.zhihu.com/write`。
**注意**：点击后当前页不变，必须从 `ctx.pages` 里重新找 `zhuanlan.zhihu.com` 的页；不要以为点击失败。

**🔴 按钮不存在时的等价回退（v3.75.0 坑，1031 实测）**：

```python
page = ctx.new_page()
page.goto('https://zhuanlan.zhihu.com/write', wait_until='domcontentloaded')
# 实测：标题 textarea 与正文 Draft.js 都在，可直接开工；wantsLogin=False
```

按钮缺席只是 UI 变体，**不是未登录、不是功能不可用**。旧脚本 `get_editor_page(ctx)` 只从 `ctx.pages` 里找现成标签页、自己不点也不 goto，按钮一缺席就 `AssertionError: 找不到知乎编辑器标签页`——这个回退必须写进脚本，不能只在探针里用（坑 355：未回写 = 未修复）。

### 3.3 编辑器结构（2026-10-30 实测）

| 元素 | 选择器 / 判据 |
|---|---|
| 标题 | `textarea[placeholder="请输入标题（最多 100 个字）"]` |
| 正文 | `div.public-DraftEditor-content`（Draft.js contenteditable） |
| 正文块 | `div.public-DraftEditor-content [data-block="true"]` |
| 视频卡片 | 块内 `.Editable-video`；可播放判据 `dataset.videoPlayable === 'true'` |
| 图片块 | 块内 `img`（src 含 `pic-private.zhihu.com`） |
| 视频上传 input | `input.VideoUploadButton-fileInput`（**打开弹窗前就已存在于 DOM**） |
| 视频工具栏按钮 | `button[aria-label="视频"]` |
| 图片上传 input | **`input[accept*="image/webp"]`**（正文配图专用，常驻 DOM）。**🔴 v3.79.0 坑 392：编辑器里常驻 3 个 `input[type=file]`，按用途分开**——① 导入文档 `.pdf,.md,.txt,…` ② **正文配图 `image/webp,image/jpg,…`** ③ 封面 `.jpeg, .jpg, .png`（class `UploadPicture-input`）。**禁止按索引取**（`inputs[1]` 会拿错），**也别用 `input[type=file]` 全取**——点工具栏「图片」会**动态挂第 4 个 `image/*` input**，等待结束时它通常已被替换成空壳，往里塞文件返回 `files=1` 但什么都不发生 |
| 封面 | `input[type=file][accept=".jpeg, .jpg, .png"]`（class `UploadPicture-input`） |
| 创作声明 | `div.css-be2u3` 中 `label` 文本 == `创作声明` → 其 `button[role=combobox]` |
| 创作声明选项 | `.Select-option`，目标文本 `包含 AI 辅助创作 作者对内容负责` |
| 专栏收录 | `.ColumnSetting-ColumnSelector` 内 `input[type=radio]` 的 **`checked` 属性**；真实专栏名 `「今日羊报 AI」`（中间是半角空格 U+20，末位是大写 I） |
| **话题 chips** | **`.css-1d3pntc`**（v3.82.0 / 2026-11-05 实测）：chip 的 `textContent` 即话题名；「添加话题」入口是 `button` 文案精确为该四字（class `css-1gtqxw0`），点开出现 `input[placeholder="搜索话题..."]`，候选项为 BUTTON，**选完即生效无确认按钮** |
| 保存状态 | 底部 `刚刚 · 草稿` / `N 分钟前 · 草稿`（**自动保存，无「保存草稿」按钮**） |
| 危险按钮 | `发布`（`Button--pri`）、`预览`（安全但无用） |

> **🔴 v3.79.0 坑 390：`/p/<id>` 阅读页也有 `div.public-DraftEditor-content`，别把它当编辑器。**
> 已发布的知乎文章阅读页实测：`hasTitleInput: false` / `editorCount: 1` / `dataBlocks: [1]` / `editorTexts: [" "]` / `bodyLen: 0` / `title: ""`。也就是说「有编辑器容器」「标题空」「正文空」**三条全部成立**——旧 `assert_editor` 因此把一篇已经发出去的文章认成「刚建好的空草稿」，后续步骤全在原稿上跑。
> **URL 判据必须要求 `/edit` 结尾**：
> ```python
> assert st['url'].startswith('https://zhuanlan.zhihu.com/write') \
>     or re.search(r'zhuanlan\.zhihu\.com/p/\d+/edit', st['url']), \
>     f'FATAL: 不是可编辑页面 {st["url"][:90]}'
> ```
> 知乎评论框也用同一套 Draft.js，这是站点固有形态，不是异常。**任何「页面长得像编辑器」的判据都要反问：阅读态会不会也命中。**

> **🔴 v3.79.0 坑 391：`input.files.length === 1` 不能证明图片进了正文。**
> W43 实测：3 张图每张都回读 `files.length === 1`，占位符也确实从 10 减到 7，但正文 `draft_token` 图数**恒为 0**——`blob:` 预览能渲染，**永远不换成 `pic-private.zhihu.com` 真链**。且失败**不稳定**：进页面后的第一张能成，之后每张都被静默丢弃（首张 CORS 正常，后续被拦）。
> **唯一有效判据**：块内 `img.src` 含 `draft_token=<文章id>`。`files.length` 只证明「文件进了 input」，不证明「进了正文」。
> **处置**：连续 2 张 `imgTok` 不增立刻停手切 `locator.set_input_files`（走坑 392 的稳定 input），**不要重试第 3 次**——重试只会把一个空块顶到别处，制造坑 393 的错位。

> **🔴 v3.79.0 坑 393：逐张替换占位符会让后续图片整体错位，占位符数量不是进度指示器。**
> W43 实测块映射：`scene3` 落在应在 `scene2` 的位置、`scene4`/`scene5` 各错一格、`scene2` 被挤到文末成第 11 张——而「占位符归零 / IMG 块数 = 10」全部是绿的。
> **根因**：占位符被吃掉 ≠ 图落到了那个位置。Draft.js 里图片落在**当前光标处**，光标位置取决于上次操作后的选区。先连续失败 3 次再成功时，前 3 个空块会被后来的图顶上去。
> **必做校验**：把正文每张图下载算 MD5 ↔ 本地 `zhihu-images/scene*.jpg` 建反查表，逐块比对位次。**位次错就全部删除重插**，不要「只补缺的那张」。

> **🔴 v3.82.0 先决条件：编辑器必须按「已知文章 id」直开，不能只找现成标签。**
> 1105 实测踩到：`get_editor_page` 只按域名匹配时，会先捡到 `www.zhihu.com/`（首页，`bodyLen=1`），
> 修成「要求 `/edit` 或 `/write`」后，又因为本期 `/edit` 标签已被关掉而新开了一个**空 `/write` 新稿**
> —— 在那个空页上回读，`chips=[]`、`hasAdd=False`，脚本因此报「三个话题全缺」，
> 而真稿上三个 chip 都在。**判据没错，对象错了**（坑 366/371 同族）。
> **正解**：`publish.json` 的 `platform.zhihu.article_id` 存本期文章 id（首次上传后回填），
> `get_editor_page` 在找不到合格标签时**按 id 直开** `zhuanlan.zhihu.com/p/<id>/edit`；
> 匹配现成标签时也要跑一道 `_editor_ok()`（标题含本期标题前 8 字，或正文 >200 字），
> **只匹配域名一定会抓到首页**。

### 3.3b 选话题（v3.82.0 新增；放在专栏之后、存草稿之前）

目标话题来源：`publish.json` 的 `platform.zhihu.topics`（2–4 个，对应正文主线）。

```python
TOPIC_CHIP_SEL = '.css-1d3pntc'
got = lambda: page.evaluate(
    "() => [...document.querySelectorAll('%s')].map(e => (e.textContent||'').trim())" % TOPIC_CHIP_SEL)

have = got()                                   # 平台会按正文自动带 1-2 个
for want in TOPICS:
    if want in have:                           # 已有就不重复加
        continue
    # ① 打开「添加话题」搜索框（button 文案精确匹配，必须滚进视口再取 rect）
    btn = page.evaluate("""() => {
      const bs=[...document.querySelectorAll('button')]
        .filter(b => (b.innerText||'').trim()==='添加话题' && b.offsetParent);
      if(!bs.length) return null;
      bs[0].scrollIntoView({block:'center'});
      const r=bs[0].getBoundingClientRect();
      return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)};
    }""")
    page.wait_for_timeout(600)
    page.mouse.click(btn['x'], btn['y'])
    page.wait_for_timeout(1800)
    # ② 搜索
    inp = page.locator('input[placeholder="搜索话题..."]').first
    inp.wait_for(state='visible', timeout=8000)
    inp.click(); inp.fill('')
    page.keyboard.type(want, delay=55)
    page.wait_for_timeout(2800)
    # ③ 候选：必须「y 在视口内」+「文本完全等于」——搜索会命中正文段落（y 为负）
    cand = page.evaluate("""(want) => {
      const vh = window.innerHeight, out = [];
      for (const el of document.querySelectorAll('button,div,span,a,li')) {
        if (el.children.length > 1) continue;
        if ((el.textContent||'').trim() !== want) continue;
        const r = el.getBoundingClientRect();
        if (r.top < 0 || r.bottom > vh || r.width < 10) continue;
        out.push({x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
      }
      return out.length ? out[out.length-1] : null;
    }""", want)
    # ④ 落点自证（坑 317 同族）
    ok = page.evaluate("""([x,y,want]) => {
      let el = document.elementFromPoint(x,y), hops = 0;
      while (el && hops < 4) { if ((el.textContent||'').trim() === want) return true; el = el.parentElement; hops++; }
      return false;
    }""", [cand['x'], cand['y'], want])
    if not ok:
        continue
    page.mouse.click(cand['x'], cand['y'])
    page.wait_for_timeout(2200)
    have = got()

missing = [t for t in TOPICS if t not in got()]
print('ZHIHU_TOPICS:', {'chips': got(), 'missing': missing})
```

**判据与纪律**：
- 回读只认 `.css-1d3pntc` 的 `textContent`（不要 grep 页面文本——正文里到处是同一个词）。
- **`missing` 非空不阻断存草稿**（与坑 351 的标签同族），但必须打印并写进 `review-checklist.md`。
- 搜索结果**会命中正文段落**（`y` 为负、不在视口内）。只按文本匹配会点到正文或点空，所以候选必须做视口过滤。这是本期实测踩到的坑。
- 平台已自动带上的话题**不要重复添加**，否则可能出现同名 chip 重复。

### 3.4 填标题

```python
page.locator('textarea[placeholder*="请输入标题"]').fill(TITLE)
```

### 3.5 填正文

Draft.js 对 `innerHTML` 直接赋值不生效。**实测最稳的是合成 `ClipboardEvent`**（比真剪贴板更可靠，无需 `grant_permissions`，也不会被系统剪贴板污染）：

```python
page.evaluate(
    """(html) => {
      const el = document.querySelector('div.public-DraftEditor-content');
      el.focus();
      const dt = new DataTransfer();
      dt.setData('text/html', html);
      dt.setData('text/plain', html.replace(/<[^>]+>/g, '\\n'));
      el.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
    }""",
    BODY_HTML,
)
```

粘贴后回读 `innerText.length`，与源文长度同量级才算成功（判据 > 800）。

**图片先用占位块**：把每个 `![](...)` 转成 `<p>__IMG__</p>`，粘贴完再逐张替换（见 3.6）。
**行内粗体要逐行处理**（坑 341）：`**说明**：后接正文` 这种「行首加粗、行内还有字」的行，只判整行 `startswith('**') and endswith('**')` 会漏掉，页面上留下字面星号。

### 3.6 插图（占位块替换）

知乎的图片上传 input 是常驻 DOM 的 `input[type=file][accept*="image/webp"]`，**上传落在当前光标所在的块位置**。所以流程是「精确定位占位 → 删掉 → 传图」：

```python
# 1) 只选中占位文本节点（绝不能用 Shift+Home，见坑 339）
page.evaluate("""() => {
  const body = document.querySelector('div.public-DraftEditor-content');
  const walk = (n) => {
    if (n.nodeType === 3 && n.textContent.includes('__IMG__')) return n;
    if (n.nodeType !== 1) return null;
    for (const c of n.childNodes) { const h = walk(c); if (h) return h; }
    return null;
  };
  const tn = walk(body);
  if (!tn) return 'not-found';
  body.focus();
  const rg = document.createRange();
  rg.selectNodeContents(tn);
  const s = window.getSelection(); s.removeAllRanges(); s.addRange(rg);
  return 'selected';
}""")
page.keyboard.press('Backspace')
page.wait_for_timeout(900)
# 2) 传图，等 naturalWidth > 100
page.locator('input[type=file][accept*="image/webp"]').first.set_input_files(path)
```

**验收必须断言总数**：`IMG|` 块数 == 源文图片数，且残留 `__IMG__` 占位 == 0。
只判「本轮拿到一张图」会假绿——1030 首轮就是这样带着 1/6 张图跑完六轮还报成功的。

### 3.7 插视频（放在正文之前，需求硬要求）

> **🔴 v3.76.0 大改（坑 367）**：本节旧结论「把光标移到文档开头，视频就插在光标块」**是错的**。
> 知乎媒体块**一律追加到文档末尾**，光标位置不决定落点。四轮搬动尝试全部失败（光标置顶 / Cut-Paste / HTML5 拖拽）。
> **唯一可靠做法：先插视频、再粘正文。** 下文的代码保留「光标置顶」只是为了置编辑器于可编辑态，不要指望它改变落点。

```python
# 1) 编辑器获得焦点（落点不受它影响，见上方警示）
page.evaluate("""() => {
  const el = document.querySelector('div.public-DraftEditor-content');
  el.focus();
}""")
# 2) 点工具栏「视频」（会弹出「导入视频」弹窗）
page.evaluate("""() => {
  for (const e of document.querySelectorAll('button[aria-label="视频"]')) {
    if (e.offsetParent) { e.click(); return true; }
  }
  return false;
}""")
page.wait_for_timeout(2000)
# 3) 用 Playwright 传文件 —— 【必须】Playwright，不能用 raw CDP 的 DOM.setFileInputFiles
inp = page.locator('input.VideoUploadButton-fileInput')
assert inp.count() >= 1, '视频 file input 未挂载'
inp.first.set_input_files(VIDEO)
```

- 上传约 **40 s** 后出现视频卡片（25 MB / 196 s 文件），用 `dataset.videoPlayable === 'true'` 判可播放
- **延迟生效陷阱**：每轮 `set_input_files` 都会成功，但在等待窗口里反复重试会**累积**成多个视频块（本期曾堆到 5 个）。上传后不要立刻重试；稳定后去重到 1 个：

```python
# 去重：删掉多余的视频块（保留第 1 个）
while state['vids'] > 1:
    page.evaluate("""() => {
      const root = document.querySelector('div.public-DraftEditor-content');
      root.focus();
      const vs = [...root.querySelectorAll('.Editable-video')];
      const blk = vs[vs.length - 1].closest('[data-block="true"]');
      const rg = document.createRange(); rg.selectNode(blk);
      const s = window.getSelection(); s.removeAllRanges(); s.addRange(rg);
    }""")
    page.keyboard.press('Backspace')
    page.wait_for_timeout(1500)
    state = read_state(page)          # 每次回读块数/视频数/图片数
```

- 视频卡片是**单个原子块**，整体删除/移动都按块走（坑 338）

**🔴 v3.77.0 上传可靠性（坑 377，2026-11-01 实测）**：**大视频不可靠，且失败形态是「看起来成功」**。

- 33.9 MB / 297 s 成片：`set_input_files` 返回成功，等待窗口里 `Editable-video` **短暂出现过 2 个**，随后全部消失，最终 `videos=0`。两轮独立上传（第一轮等了约 13 分钟）结果相同。同期 25 MB / 196 s 的月报视频是能落块的。
- **判定必须「刷新后数块」，不能数等待窗口里的瞬时值**。瞬时出现又消失，是最容易被骗过去的形态。

```python
# 上传后：先等「上传中/处理中/xx%」字样全部消失，再 reload 回读
page.wait_for_timeout(upload_wait_ms)          # 大文件给足 ~10min
page.reload(wait_until='domcontentloaded'); page.wait_for_timeout(4000)
vids = page.locator('.Editable-video').count()  # ← 只认这个数
```

- 若 reload 后仍为 0：**不要无限重试**。上传耗时 10 分钟量级，重试只会烧时间。当日决策是**无视频存草稿并如实标注**（用户批准的兜底）。验收行写「视频：未落块（33.9MB 两轮均失败），已无视频存草稿」，**不许写成「已插视频」**。
- 重排顺序提示：因为视频一律追加到文档末尾（见上方 v3.76.0 警示），**插视频必须发生在粘正文之前**；若正文已粘好才发现视频要重试，只能把正文整段删掉重粘，成本很高 —— 所以**先传视频、确认 reload 后块数=1，再粘正文**。

### 3.8 添加封面

> **v3.76.0 实测**：`input.UploadPicture-input` 同样是 `display:none`，raw CDP 的 `DOM.setFileInputFiles` 无效，
> 必须用 Playwright `set_input_files`。判据不能用「页面文本里有『上传封面』」——该字样常驻模板，**恒真**；
> 真判据 = 发布设置面板里 `添加文章封面` 占位消失。

```python
# 点「添加封面」展开上传区，再对 accept 为图片的 input 传文件
page.evaluate("""() => {
  for (const e of document.querySelectorAll('*')) {
    if (/^(添加封面|设置封面)$/.test((e.innerText||'').trim()) && e.offsetParent && e.children.length === 0) { e.click(); return; }
  }
}""")
page.wait_for_timeout(2500)
inp = page.locator('input.UploadPicture-input')
assert inp.count() >= 1, '封面 input 未挂载'
inp.first.set_input_files(COVER)
page.wait_for_timeout(3000)
# 判据：面板里「添加文章封面」占位消失
panel = page.evaluate("""() => { const p = document.querySelector('.css-13mrzb0'); return p ? p.innerText : ''; }""")
assert '添加文章封面' not in panel, f'封面未生效: {panel[:80]}'
```

封面用 `news-pipeline/<DATE>/images/horizontal-4-3.png`（知乎文章封面为横图位，4:3 可接受）。

### 3.9 设创作声明（必做）

> **🔴 v3.76.0 两处修正（坑 370）**
> ① **`div.css-be2u3` 不能当定位锚点**：本期页面上它有 **6 个**，第一个是「投稿至问题」。
> ② **页面上有多个 `[role=combobox]`**（投稿至问题 / 创作声明 / 文章话题…），按「第一个」取会拿到
> 「投稿至问题」→ 选项列表为空 → 误报「找不到声明选项」。必须**沿 combobox 向上 ≤4 层**找
> innerText 以 `创作声明` 开头的那一行。
> ③ **该字段不随草稿持久化**：编辑器内选中后回读正确，整页刷新后稳定回落为「无声明」（两个标签各复现，共 3 次）。
> 与坑 318 视频号「视频标注」同族——只在发布时随请求提交。验收**不得**标 PASS。

```python
# 1) 定位「创作声明」那一行的 combobox（不是第一个 combobox！）
pos = page.evaluate("""() => {
  for (const c of [...document.querySelectorAll('button.Select-button')].filter(e => e.offsetParent)) {
    let p = c;
    for (let i = 0; i < 4 && p; i++, p = p.parentElement) {
      const t = (p.innerText || '').replace(/\\s+/g, ' ').trim();
      if (t.startsWith('创作声明') && t.length < 80) {
        c.scrollIntoView({block: 'center'});
        const r = c.getBoundingClientRect();
        return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
                cur: (c.innerText || '').trim()};
      }
    }
  }
  return null;
}""")
assert pos, '创作声明 combobox 未找到'
# 坐标点击（坑 340）；DOM .click() 对部分控件静默无效
page.mouse.click(pos['x'], pos['y'])
page.wait_for_timeout(3000)

# 2) 选目标项（选项渲染 ≥3 s）
opt = page.evaluate("""() => {
  for (const e of document.querySelectorAll('*')) {
    if (e.children.length || !e.offsetParent) continue;
    if ((e.innerText||'').replace(/\\s+/g,' ').trim() !== '包含 AI 辅助创作 作者对内容负责') continue;
    const r = e.getBoundingClientRect();
    return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
  }
  return null;
}""")
assert opt, '声明选项未渲染'
page.mouse.click(opt['x'], opt['y'])
page.wait_for_timeout(2500)

# 3) 回读（当前会话内应为目标值；刷新后会回落，见上方 ③）
cur = page.evaluate("""() => {
  const b = [...document.querySelectorAll('button.Select-button')].filter(e => e.offsetParent)
    .find(e => { let p = e; for (let i = 0; i < 4 && p; i++, p = p.parentElement) {
      const t = (p.innerText||'').replace(/\\s+/g,' ').trim();
      if (t.startsWith('创作声明')) return true; } return false; });
  return b ? b.innerText.trim() : null;
}""")
assert '包含' in (cur or '') and 'AI 辅助创作' in (cur or ''), f'创作声明未生效: {cur!r}'
print('声明已在编辑器中选中；注意：草稿不保存该项，发布前需再设一次')
```

### 3.10 专栏收录

**🔴 v3.75.0 坑 352：专栏有两个失败层级，判据必须覆盖「开关压根没开」。** 1031 实测默认状态是 **`不发布到专栏` checked=true**，此时 combobox **不存在**（`combo: null`），旧断言直接抛 `未选中「发布到专栏」: '不发布到专栏'`。坑 346 讲的「开关已勾、专栏选错」是**第 2 级**；今天的形态是**第 0 级**。

正确的三步 + 三分支判据：

```python
# 第 0 级：先确认开关是开的（坑 340：Vue radio 的 .click() 静默无效，必须坐标点）
box = page.evaluate("""() => {
  const lab = document.querySelector('label[for="PublishPanel-columnLabel-1"]');
  if (!lab) return null;
  const r = lab.getBoundingClientRect();
  return {x: r.x + r.width/2, y: r.y + r.height/2, checked:
          !!document.querySelector('#PublishPanel-columnLabel-1')?.checked};
}""")
if box and not box['checked']:
    page.mouse.click(box['x'], box['y'])      # 1031 实测 label rect {'x':393,'y':444.07,'w':94,'h':38}
    page.wait_for_timeout(1200)

# 第 1/2 级：radio + combo 双证（combo 在关态为 None，必须先拦）
sel = page.evaluate("""() => {
  const box = document.querySelector('.ColumnSetting-ColumnSelector');
  if (!box) return {found: false};
  const on = Array.from(box.querySelectorAll('input[type=radio]')).find(r => r.checked);
  const lab = on && on.closest('label[for]') ? on.closest('label[for]').innerText.replace(/\s+/g,'') : '';
  const combo = box.querySelector('button[role=combobox]');
  return {found: true, checkedLabel: lab, combo: combo ? combo.innerText.replace(/[\s​]/g,'') : null};
}""")
if not sel['found']:              raise AssertionError('找不到专栏设置区，发布设置可能未展开')
if sel['checkedLabel'] != '发布到专栏': raise AssertionError(f'第0级失败：开关未开（{sel["checkedLabel"]!r}）')
if not sel.get('combo'):          raise AssertionError('第1级失败：开关已开但 combo 不存在')
if want not in sel['combo']:      raise AssertionError(f'第2级失败：专栏选错（{sel["combo"]!r}）')
```

**选专栏的真路径（1031 唯一成功路径）**：点开 combobox → 在 `.Select-option` 里按 `innerText.replace(/\s/g,'')` **命中带书名号的目标名** → 取 rect 中心 `page.mouse.click`。该账号专栏总数只有 **2 个**（`「虢礫緙嘞」` 与 `「今日羊报AI」`），「默认就是目标专栏」不是可依赖假设。

**⚠️ 旧写法的两个错**：① 上面 `assert '今日羊报AI' in sel['combo']` 在 combo 为 `None` 时会抛 `TypeError: argument of type 'NoneType' is not iterable`，必须先 `if not sel.get('combo')` 拦；② 坑 334 说「创作声明要先展开发布设置才可见」——**1031 实测不成立**：在已落库的 `/p/<id>/edit` 页上，`[decl]` 在 `[column]` 之前成功执行、全程没点过「发布设置」。所以步骤顺序 decl 可以在 column 之前；`step_decl` 找不到控件时应「尝试展开面板」兜底，而不是静默走过去让后面的断言报「未生效: None」（那会把「没找到」误报成「没生效」）。

**专栏名要按码点核，别靠肉眼**：`今日羊报 AI` 中间有**半角空格 U+20**，末位是**大写 I（U+49）**。这两个字符极容易被写错成「无空格」或小写 `l`（U+6C），肉眼几乎分辨不出。实测码点：

```
「  U+300C
今  U+4ECA   日 U+65E5   羊 U+7F8A   报 U+62A5
    U+20   ← 半角空格
A   U+41     I  U+49   ← 大写 I，不是小写 l
」 U+300D
```

因此比较时**两边都去空白**（`re.sub(r'\s','',...)`）最稳，既能吃掉上游文案的空格差异，也不会把大写 I 误判成小写 l。

若默认不是目标专栏，再点专栏名打开下拉选目标专栏并回读。

**内容来源**：面板底部有「根据自媒体投稿规范，发布新闻类的内容需要明确标注信息来源」提示。新闻类内容建议点「添加来源」补一条（可选，但建议做）。

### 3.11 保存草稿 = 等自动保存 + 验收

**知乎文章页没有「保存草稿」按钮**，是自动保存：

1. 填完标题/正文后等 ≥3s，页面底部应出现 `刚刚 · 草稿`
2. **不要点「发布」**（`Button--pri`，危险按钮，scripts 里禁止出现对其的点击）
3. 到草稿箱核验：**必须硬 goto `https://www.zhihu.com/creator/manage/creation/draft?type=article`**（v3.75.0 坑 353）。**不要**「点侧栏『草稿箱』再 grep」——点 tab 后 URL 会变成 `?type=answer`，只列**回答草稿**，文章标题必然查不到，看起来像草稿丢了（1031 实测：点 tab 得 `正文含本期标题: False`；硬 goto 后首条正是本期标题）。记忆钩子：`?type=answer|article|zvideo` 对应 回答/文章/视频 三类草稿，默认 `answer`

> **🔴 v3.76.0 坑 369：不要用「在正文里删点什么」来触发自动保存。**
> 本期为制造一次 input 事件，写了 `selectNodeContents(末块) + execCommand('delete')` ——
> Draft.js 把**视频原子块和结尾段前半句一起删了**（`vids 1→0`，`bodyLen 1846→1706`），
> 且自动保存已把破坏写进草稿。
> **安全做法：只在标题末尾加一个零宽字符 `​` 再删掉**，正文一个字节都不碰：
> ```python
> page.evaluate("""() => {
>   const ta = document.querySelector('textarea[placeholder*="请输入标题"]');
>   const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
>   window.__origTitle = ta.value;
>   ta.focus(); setter.call(ta, ta.value + '​');
>   ta.dispatchEvent(new Event('input', {bubbles: true}));
> }""")
> page.wait_for_timeout(6000)
> page.evaluate("""() => {
>   const ta = document.querySelector('textarea[placeholder*="请输入标题"]');
>   const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
>   setter.call(ta, window.__origTitle);
>   ta.dispatchEvent(new Event('input', {bubbles: true}));
> }""")
> page.wait_for_timeout(8000)
> ```

### 3.12 上传验收判据

**🔴 v3.76.0：门禁第 0 项必须是「我是谁」。** 在跑下面任何一项之前先断言 —— 本期整篇月报写进了日更稿，
而所有 13 项检查在**错误的文章上**全部给出了合理读数：

```python
assert ARTICLE_ID_THIS_ISSUE in page.url                     # /p/<id>/edit 里的 id 必须属于本期
assert page_title_value == publish_json.platform.zhihu.title # 标题必须等于本期标题
assert body_first_line.startswith(BODY_SIGNATURE)            # 正文首句属于本期
```

**🔴 配图计数按来源分类（坑 368）**：正文配图 `src` 带 `draft_token=<文章id>`；
`naturalWidth === 1920` 的是**视频封面缩略图**，按尺寸数会把 8 图数成 9。

```python
body_imgs = page.evaluate("""(id) => [...document.querySelectorAll('div.public-DraftEditor-content img')]
    .filter(i => (i.src || '').includes('draft_token=' + id)).length""", ARTICLE_ID)
```

**🔴 终态必须「刷新后重读」**：`page.reload()` 再跑一遍全部计数。
本期刷新后才暴露三个问题——创作声明回落（坑 370）、视频变成 2 个（延迟累积，坑 367）、配图需按 `draft_token` 重算（坑 368）。

| 项 | 判据 |
|---|---|
| 我是谁（第 0 项）| URL 含本期文章 id **且** 标题 == `publish.json` **且** 正文首句 == 本期签名（坑 371） |
| appmsg 级 ID | 编辑页 URL 变为 `zhuanlan.zhihu.com/p/<id>/edit`（说明已落库为草稿） |
| 标题 | `textarea` value 与 TITLE 完全一致 |
| 正文 | `div.public-DraftEditor-content` innerText 长度 > 800 |
| 视频 | `.Editable-video` 数 == **1**（不是 ≥1，坑 367 会堆出多个）且 `data-video-playable == 'true'`；块序看前 3 块的 kind 序列。**判块序要看前 3 块的 kind 序列**（如 `0:TXT(空) 1:VIDEO 2:正文`），**不要**看日志里的 `first block: TXT|`——那行用 `startswith(('VIDEO','TXT'))` 取第一个匹配块，正文场景下永远是 TXT，与视频是否插入无关（v3.75.0 坑，1031 实测）|
| 图片 | `img[src*=draft_token=<文章id>]` 数 == 源文图片数，且无 `__IMG__` 残留。**不要用 `naturalWidth` 数**（会把视频封面缩略图算进来，坑 368）|
| 封面 | 发布设置面板里 `添加文章封面` 占位**消失**；不要用页面文本含「上传封面」判（恒真）。**必须并入 `ok` 表达式**（v3.75.0 坑 354）|
| 创作声明 | combobox 回读归一化后 == `包含AI辅助创作作者对内容负责`。**🔴 v3.76.0 坑 370：该项刷新后会回落为「无声明」（只在发布时提交），故「刷新后核验」时此项必 FAIL，属预期行为——报告须如实写「未持久化」，不得标 PASS** |
| 专栏 | **三级判据**（v3.75.0 坑 352 修正）：① 开关是否打开（radio `PublishPanel-columnLabel-1` 的 `checked`）② 打开后 `combo` 是否存在（关态下为 `null`）③ combo 文本归一化后是否 == 目标专栏。**只判第 2 级会漏掉「开关压根没开」这一上游形态**（1031 实测默认就是「不发布到专栏」checked=true）|
| 字面星号 | 全文块文本不含 `**`（坑 341）。**必须并入 `ok`**（v3.75.0 坑 354）|
| 块数守恒 | `len(blocks) == 正文块数 + 2`（+视频卡片 +自动空块）；1031 实测 32 → 34。数量不守恒 = 有块被 `Backspace` 吃掉（坑 342/369 的指纹）|
| 危险动作 | 全程未点击「发布」 |
| **刷新后重读** | 上述全部重跑一遍。刷新后仍成立才算「落库」，唯一预期例外是创作声明（坑 370）|

**🔴 `ZHIHU_DRAFT_OK` 的真实语义（v3.75.0 坑 354）**：当前脚本的 `ok` 只含 `videos==1 / playable / decl / bodyLen>800 / IMG 数` 五项，**它只证明视频、声明、正文、图数四件事**，不证明封面、专栏、无字面星号。看到 OK 不等于全绿——要么把三项并进 `ok`，要么在 checklist 里另行逐项回读。

---

## 4. 坑（坑 334–355、362–372、375–377、382）

### 坑 375（v3.77.0）：`# 标题` 前缀两处都要剥
- 见 §1.5。`load_title()` 和 `build_html()` 各有一份首行解析，只改一处炸 `assert TITLE == title_md`，报错点看起来像稿件问题。

### 坑 376（v3.77.0）：派生漏插 `![]()` 是静默失败
- 见 §1.6 ①。`imgs=0` 时所有断言照样全过。

### 坑 377（v3.77.0）：33.9MB 视频两轮都没落块，瞬时出现又消失
- 见 §3.7 末尾。判据只认 `reload` 后 `.Editable-video` 数；失败就如实标「未落块」，不重试到天荒地老。

### 坑 382（v3.77.0）：专栏选择「radio 和下拉是两个真实坐标点击」，且必须精确匹配
- 1101 实测：默认专栏是**上次用过的「羊报AI周刊」**（不是「不发布到专栏」，与 1031 的坑 352 第 0 级形态不同）——**`radio.checked` 只证明开关打开，不证明选的是目标专栏**。
- 下拉**只认真实坐标点击**（`page.mouse.click(cx, cy)`）；`el.click()` / `dispatchEvent` 对这套 Vue 组件静默无效。
- 选项文本带书名号 `「」`，比对必须**剥引号后完全相等**，**不能用 `in` 子串匹配**——`'今日羊报AI' in '羊报AI周刊'` 这类误判会把月报专栏选进日更稿（与坑 366 同源）。
- 步骤顺序：① 坐标点 radio「发布到专栏」→ ② 坐标点 combobox 打开下拉 → ③ 坐标点精确匹配项。三步各自 `wait_for_timeout(≥1200)` 并逐步回读。

### 坑 334：创作声明是 combobox 不是 select；「必须先展开面板」被 1031 推翻
- 控件结构：`div.css-be2u3` → `label`（文本 `创作声明`）→ `button[role=combobox]`
- **该 class `css-be2u3` 被多个字段复用**（投稿至问题 / 创作声明 / 文章话题 / 专栏收录），必须**按 label 文本定位**，不能取第一个
- 选项文本含空格：`包含 AI 辅助创作 作者对内容负责`；回读时元素文本含**零宽空格 `​`**，比较前必须归一化
- **🔴 v3.75.0 修正**：旧文说「页面首次加载时发布设置只露出 添加封面/专栏收录/定时发布；创作声明要等面板完整展开后才在 DOM 里可见（点过『发布到专栏』后可见）」——**1031 实测不成立**。在已落库的 `/p/<id>/edit` 页上，`[decl]` 步在 `[column]` 步**之前**成功执行，全程没有点过「发布设置」。所以：① 步骤顺序上 decl 可以排在 column 之前；② `step_decl` 找不到控件时应「尝试展开面板」兜底，**不要**静默走过去让 `assert cur == ...` 报「未生效: None」——那会把「没找到」误报成「没生效」，误导排查方向。

### 坑 335：知乎文章没有「保存草稿」按钮
- 自动保存，底部显示 `刚刚 · 草稿`
- **验收不能等按钮出现**，要看 `url 变成 /p/<id>/edit` + 底部草稿时间戳 + 草稿箱列表
- 不要为了「触发保存」去点「发布」——那会真的发出去

### 坑 336：点「立即创作」会新开标签页
- 点击后当前页 URL 不变，编辑器在 `zhuanlan.zhihu.com/write`
- 必须重新扫 `ctx.pages` 找新页，别把「当前页没变化」误判为点击失败

### 坑 337：新闻类内容有「内容来源」要求
- 发布设置底部：「根据自媒体投稿规范，发布新闻类的内容需要明确标注信息来源」
- 本站内容为 AI 圈新闻综述，建议「添加来源」；至少在正文中保留来源表述

### 坑 338：视频卡片是原子块，退格会整块删除
- 视频卡片在 Draft.js 里是**一个不可分割的块**（`figure.Editable-styled` 包 `.Editable-video`）
- 光标放在卡片后按一次 `Backspace`，删的是**整个视频**，不是删一个字符
- 想删卡片后面那行文字又保住视频：光标移到该行开头，`Meta+Shift+ArrowDown` 选中整行再退格
- 反过来也成立：删除任何东西之后**都要重新数一遍 `.Editable-video`**，别假设它还在

### 坑 339：Draft.js 里 `Shift+Home` 会选到**整篇开头**
- 想「选中占位块那一行」而按 `Shift+Home`，Draft.js 会从光标反向选到**文档最开头**
- 随后的 `Backspace` 会把占位之前的所有正文一起删掉。1030 首轮：正文 2025 字 → 441 字，34 块 → 7 块，6 张图 → 1 张，**而自动保存已经把破坏写进了草稿**
- 正确做法：用 `Range.selectNodeContents(目标文本节点)` 只选中该节点，再退格
- 教训：破坏发生后必须 reload 页面回读才算知道真实状态——脚本自己内存里的状态是过时的

### 坑 340：Vue 单选框/标签页的 `.click()` 静默无效
- 对 `.Tabs-link`、`input[type=radio]` 之类直接调 `element.click()`，DOM 上看不出报错，但选中态不变
- 有效做法：取 `getBoundingClientRect()` 的中心 → `page.mouse.click(x, y)`（真实鼠标事件）

### 坑 341：整行加粗的判断漏掉「行首加粗 + 行内正文」
- `line.startswith('**') and line.endswith('**')` 只能处理 `**整行都是粗体**`
- `**AI 辅助创作说明**：本文由作者…` 这种行首加粗、后面还有正文的行会被当普通段落原样粘贴，页面上留下字面 `**`
- 正确做法：逐行跑 `re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)`
- 验收时加一条：任何块文本里都不该出现 `**`

### 坑 342：`Backspace` 按的是 Draft.js 的**内部选区**，不是刚设的 DOM 选区
- `paste` 事件读的是 DOM Selection，所以合成 paste 按预期落在目标位置
- **但 `Backspace` 走的是 Draft.js 自己的 SelectionState**，它可能还停在别处
- 1030 实测：想改末段声明，DOM 选区明明设在末段上，退格删掉的却是**文件开头的视频卡片**
- 结论：**任何一步里带 `Backspace` 之后，都必须重新回读全部结构性计数**（视频数、图片数、块数），发现缺了立刻补插；不要相信「我只选了那一块」

### 坑 343：专栏选中态不能靠 grep 页面文本判
- `专栏收录 / 发布到专栏 / 不发布到专栏` 三个字串**本来就常驻 DOM**，grep 恒为 true
- 下拉框里的专栏名也可能是上次残留值
- 真判据：`.ColumnSetting-ColumnSelector` 内 `input[type=radio]` 的 **`checked` 属性**，配合该 radio 所属 `label[for]` 的文本
- 另外：真实专栏名 `「今日羊报 AI」`（含半角空格 U+20、末位大写 I U+49），需求文案写法一致；但比较时仍两边去空白，别靠肉眼分辨

### 坑 344：`cdp_helper.eval()` **不做参数注入**，带参 JS 必须内联
- `Tab.eval(expr)` 只接受**一个字符串表达式**：普通 IIFE，或顶层写 `async () => {...}` 的箭头函数本体（`_is_arrow_at_top` 自动调用）
- 写 `tab.eval("(title) => {...}", title)` 这种 Playwright 风格调用，第二个参数会被**静默丢弃**，JS 侧 `title` 为 `undefined`
- 症状要么是 `Cannot read properties of undefined`，要么更糟——`setter.call(t, undefined)` 把标题写成字面 `"undefined"` 还回读成功
- 正解：`tab.eval(f"(() => {{ const want = {json.dumps(x)}; ... }})()")`，用 `json.dumps` 生成合法 JS 字面量（能正确转义引号/换行/中文）
- 生成的选择器里含 `%` 时不要用 `%` 格式化（`%r` 之外会被当格式符吞掉），统一 `f-string + json.dumps`

### 坑 345：`click_safe` 的危险词闸门会误伤「发布设置」
- 闸门按**子串**匹配 `发表 / 发布 / 立即投稿 / 提交审核 / 发表视频`，而展开设置面板的入口文案正是 `发布设置`
- 一旦被拦就抛异常，整条上传流程卡在设置步骤
- **不要**为此把闸门改宽或传 `allow_danger=True`
- 正解：给「展开型」控件写**局部安全点击**——文案必须**严格等于**目标词、元素不在任何提交按钮的祖先链里、命中 `SUBMIT` 白名单即拒：
  ```js
  const SUBMIT = ['发布','发表','立即投稿','提交审核'];
  const el = [...document.querySelectorAll('*')].find(e =>
    (e.innerText||'').trim() === '发布设置' && e.offsetParent && e.children.length === 0);
  if (SUBMIT.includes((el.innerText||'').trim())) return {err:'danger'};
  for (let n = el, i = 0; i < 5 && n; i++, n = n.parentElement)
    if (n.tagName === 'BUTTON' && SUBMIT.includes((n.innerText||'').trim())) return {err:'danger-ancestor'};
  ```
  再取 `getBoundingClientRect()` 中心走 `Input.dispatchMouseEvent`（坑 340：坐标点击才生效）

### 坑 346：知乎专栏默认值是「上次用过的专栏」，不是目标专栏
- 点「发布到专栏」后回读 `radio.checked` 只能证明**开关**打开了，不能证明**选对了专栏**
- 1030 实测：开关已勾选，专栏名却是随机默认的 `「虢礫緙嘞」`
- 因此判据必须**两级**：`radio.checked === true` **且** `.ColumnSetting-ColumnSelector button` 的文本归一化后 == 目标专栏名
- 改名路径：点该 button 开下拉（选项形如 `「今日羊报AI」`，带书名号，比较时两边都剥 `「」` 与空白）→ 坐标点击目标项 → 回读 button 文本

### 坑 347：视频卡片自己的封面 input 只在弹窗打开时存在
- `.Editable-video` 卡片上叠着「上传视频封面」按钮，但专用 input `input.VideoCoverFileInput-input` **只有点了按钮、弹窗打开后才挂进 DOM**
- 没打开弹窗直接 `set_files('input.VideoCoverFileInput-input')` → `set_files: expression returned no object`
- 且页面上同时存在 4 个 `input[type=file]`（附件 / 正文图片 / 文章封面 `UploadPicture-input` / 视频封面），**按「取最后一个」选 input 会选错**
- 优先级：文章封面已设好时，视频卡片用首帧即可，**不要为了视频封面去点按钮**——点了再选错 input 有污染正文图片的风险

### 坑 352：专栏默认是「不发布到专栏」，开关本身就是关的（v3.75.0 / 2026-10-31 实测）
- 1031 实测 DOM：`[{"id":"PublishPanel-columnLabel-1","checked":false,"label":"发布到专栏"},{"id":"PublishPanel-columnLabel-0","checked":true,"label":"不发布到专栏"}]`，此时 **`combo: null`**
- 这是坑 346 的**上游形态**：346 是「开关已勾、专栏选错」，这里是「开关压根没开」
- 关闭态下 `assert re.sub(r'\s','',WANT) in sel['combo']` 会抛 `TypeError: argument of type 'NoneType' is not iterable` —— 必须先 `if not sel.get('combo')` 拦
- 正确路径见 §3.10 的三步 + 三分支

### 坑 353：草稿箱点 tab 落 `?type=answer`，标题必然查不到（v3.75.0 / 2026-10-31 实测）
- 点「草稿箱」后 URL = `.../draft?type=answer`，只列回答草稿 → `正文含本期标题: False`
- 硬 goto `?type=article` → `草稿箱(24) 回答草稿20 文章草稿3 想法草稿1`，首条即本期标题
- 记忆钩子：`?type=answer|article|zvideo` 对应 回答/文章/视频 三类草稿，默认 `answer`

### 坑 354：`ZHIHU_DRAFT_OK` 只证明四件事，不能当全量验收（v3.75.0 / 2026-10-31 实测）
- `ok` 只含 `videos==1 / playable / decl / bodyLen>800 / IMG 数`；**封面数、专栏两级、字面 `**` 三项全不在内**
- 1031 专栏断言先崩、手工修好才跑 verify —— 若没修，这一行照样印 OK
- 另：`all` 捆绑包**不含 footer**（`if step == 'footer':` 对比相邻的 `if step in ('all','column'):`）→ 坑 341 的 `**` 验收永远不会自动跑

### 坑 355：「未回写 = 未修复」——临时探针里的修复不算修复（v3.75.0 / 2026-10-31 实测）
- 1031 专栏的坐标点击修复**只活在 heredoc 的临时 playwright 代码里**，`zhihu_upload_1031.py` 的 mtime 仍是 `Oct 30 22:08`，脚本内 `grep mouse.click` 只命中旧的三行
- 规则：任何浏览器里手工验证通过的修复，必须当场回写对应 `step_*` 函数，并立刻单跑该 step 自证。没跑过就只能写「人工探针验证过」，不能写「策略已实测」
- 派生器把脚本从上一期复制过去，缺陷会跟着走

### 坑 362：登录判据「页面出现『立即创作』」会假阴性（v3.75.0 / 2026-10-31 实测，知乎专属）
- 1031 实测 `creator page: {'url':'.../creation/article','hasCreate':False,'hasDraft':True,'needsLogin':False,'len':952}` —— 侧栏有草稿箱、无扫码登录，唯独没有「立即创作」
- 按旧判据会在第一步就把自己拦下。真判据 = 侧栏有「草稿箱(N)」/「创作主页」且无扫码/密码登录

### 坑 363：「立即创作」缺席时可直接 goto `/write`（v3.75.0 / 2026-10-31 实测，知乎专属）
- `ctx.new_page()` + `goto('https://zhuanlan.zhihu.com/write')` → `{'title': True, 'editor': True, 'bodyLen': 1, 'wantsLogin': False}`，编辑器直出可用
- 旧脚本 `get_editor_page(ctx)` 只从 `ctx.pages` 里找现成标签页、不点也不 goto → 按钮缺席即 `AssertionError: 找不到知乎编辑器标签页`

### 坑 364：`first block: TXT|` 是构造性无信息行，不能当块序证据（v3.75.0 / 2026-10-31 实测，知乎专属）
- `first = next((b for b in st['blocks'] if b.startswith(('VIDEO','TXT'))), '')` → 正文场景下永远返回第一个 TXT 块，与视频是否插入无关
- 真块序靠打印 `st['blocks'][:3]`：1031 实测 `0:TXT(空) 1:VIDEO 2:正文`

### 坑 365：文章一旦被发布，草稿就从草稿箱消失——验收必须当场做（v3.75.0 / 2026-10-31 实测）
- 1031 上传当场：`文章草稿 2→3`，首条即本期标题，`ZHIHU_DRAFT_OK`
- 同日下午回查：`草稿箱(23) 回答草稿20 文章草稿2`，**本期标题不在草稿箱**；而文章页显示 `发布于 2026-10-31 09:53・广东`、正文 2679 字、视频 1、图 7
- **判定**：草稿被「提升」成正式文章后从草稿箱移除。**这不是草稿丢失，也不是自动化点的发布**（脚本内 `grep 发布` 只命中「发布设置」「发布到专栏」，无提交动作）；**但发布动作由谁触发尚未确认**——公众号（10:59 进「近期发表」、近期草稿退回 10-12）与视频号（10:02 已发表条目）同日出现同族现象，三处都无流水线日志。**在用户明确答复前，只记「上传当时为草稿，其后出现在已发表列表，来源待确认」**
- **规则**：① 草稿验收必须在**上传当场**完成并留存读数，事后回查的「查不到」不能反推「当时没存上」；② 回查发现标题不在草稿箱时，**先去文章页看有没有 `发布于 <时间>`**，再看正文长度/图片数/视频数是否与上传时一致，才能判断是「已发布」还是「真丢失」；③ 汇报时如实写「上传当时为草稿，之后该条目出现在已发表列表（来源待确认）」，不要含糊成「草稿状态正常」，也不要替用户下结论说是谁发的

### 坑 366：跨流水线抢同一个知乎标签，整篇稿子写错（v3.76.0 / 2026-10-31→11-01 实测）

**现象**：整篇月报（标题/正文/8 图/视频/封面/声明/专栏）写进了 1101 日更稿 `2100056075546448877`，而月报本身**从未存在于草稿箱**（草稿箱 `文章草稿3` 只有日更稿 + 两条 10-30 无标题稿）。反向也发生：日更脚本把 1101 标题写进了月报文章 `2100303881762874483`。

**链路**：
1. 月报脚本留下 `/tmp/zhihu-monthly-2026-10-tab.txt` → 标签 `22EE…`（正在编辑月报）；
2. `zhihu_upload_1101.py` 用 `ctx.pages` 里**第一个** `zhuanlan.zhihu.com/*/edit` 认领编辑器 → 选中 `22EE…`；
3. 之后所有「月报」操作全部落进日更稿。

**为什么一直没被发现**：所有单项检查都给出了合理读数 —— 标题框里确实是「某个本期标题」、正文确实是「某期正文」、图片 8 张、视频可播。**判据不会告诉你它在读谁的稿子。**

**规则**：
- 复用文件名带期次：`/tmp/zhihu-<DATE>-tab.txt`；
- **禁止**「取 `ctx.pages` 里第一个匹配项」，必须逐页读标题/正文首句再比对；
- 每个写脚本第一步做三条自证（见 §3.12 第 0 项），任一不符立即 abort；
- 发现串稿先**只读盘点两边**（标题/正文首句/块数/图数/视频数/声明/专栏），确认哪边被改了什么再决定动谁，**不要凭记忆恢复**。

### 坑 367：知乎文件上传必须用 Playwright；且上传「延迟生效」会累积（v3.76.0 / 2026-10-31→11-01 实测）

**第一层：raw CDP 无效。** `DOM.setFileInputFiles` 对 `display:none` 的 `input.VideoUploadButton-fileInput` / `input.UploadPicture-input` 返回 `{}`（看起来成功）但 `input.files.length` 恒为 0。四轮替代路全部失败：ASCII 路径 / 复位面板（先确保 `input` 数量归零再重新挂载）/ 真实 `Input.dispatchMouseEvent` 坐标点击 / 点「导入视频」开 Modal 再用弹窗内 input。**换 Playwright `locator.set_input_files()` 一次成功。**

**第二层：卡片延迟出现，重试会累积。** 每轮 `set_input_files` 都成功，但在等待窗口里反复重试 → 本期一次会话堆出 **5 个**视频块（全部 `playable=true`），刷新后又出现 2 个。

**规则**：① 文件上传优先 Playwright（它与 raw CDP 走不同注入链，同一台机器结论可以相反）；② 喂完立刻回读 `input.files.length`，为 0 即判失败停手，不要用「等卡片出现」掩盖；③ 上传后不要立刻重试；④ 稳定后去重到 1 个（选中末块 → 断言块内无正文 → `Range.selectNode` + `Backspace` → 每次回读三项计数）。

### 坑 368：`img` 计数必须按来源分类（v3.76.0 / 2026-11-01 实测）

正文配图 `src` 带 `draft_token=<文章id>`；`naturalWidth === 1920` 的是**视频封面缩略图**。按 `naturalWidth > 300` 数会把「8 图 + 1 视频封面」数成 9，进而判「多了一张」或与源文不符。正解：`img[src*=draft_token=<文章id>]`。

另：占位符 -1 **不等于**图片 +1 —— 失败的替换会吃掉占位符但不产生卡片，每一步必须同时回读 `img` 数。

### 坑 369：不要用「在正文里删点什么」触发自动保存（v3.76.0 / 2026-11-01 实测）

为了制造一次 input 事件，写了 `selectNodeContents(末块) + execCommand('delete')` —— Draft.js 把**视频原子块和结尾段前半句一起删了**（`vids 1→0`，`bodyLen 1846→1706`），且自动保存已把破坏写进草稿。

**规则**：触发保存只用**标题**（末尾加/删零宽字符 `​`），正文一个字节都不碰。任何「为了凑一个 input 事件」而在正文里做删除的操作都禁止。

### 坑 370：创作声明不随草稿持久化（v3.76.0 / 2026-11-01 实测，与坑 318 同族）

编辑器内选中后回读正确，**整页刷新后稳定回落为「无声明」**（两个标签各复现，共 3 次）；即使之后触发正文级编辑保存也一样。判定为「只在发布时随请求提交」。

**规则**：验收**不得**标 PASS；对外说法是「已在编辑器选中，发布前需再设一次」。与坑 318 视频号「视频标注」同族。

### 坑 371：门禁第 0 项必须是「我是谁」（v3.76.0）

见坑 366。把身份断言写进 `read_state()` 的第一项，而不是写在脚本注释里。三条：URL 含本期文章 id / 标题 == `publish.json` / 正文首句签名。

### 坑 372：公众号标题区 `el.click()` 不送焦点（v3.76.0 / 2026-10-31→11-01 月报实测）

（虽属公众号，但与知乎同批修复，写在此处以免遗漏）
`document.querySelectorAll('.ProseMirror')[0].click()` 后 `document.activeElement` 仍是 `body` → `Input.insertText` 被静默丢弃 → 隐藏 `textarea#title` 恒空 → `AssertionError: title not synced: ''`。必须 `.focus()` 并断言 `document.activeElement === p`，再双回读（`#title` 的 value + ProseMirror 的 textContent）。

---

## 5. 与其他平台的差异速查

| 维度 | 公众号 | 知乎 |
|---|---|---|
| 文体 | 图文推送，可带 CTA | 文章，禁止导流 CTA |
| 保存 | 显式「保存为草稿」按钮 | **自动保存** |
| AI 声明 | 不设（草稿阶段） | **必须设**「包含 AI 辅助创作 作者对内容负责」 |
| 合集/专栏 | 合集「今日羊报 AI」 | 专栏「今日羊报 AI」（同名，含半角空格） |
| 图片 | `wechat-images/scene*.png` | 同目录 `*.jpg` |
| **视频** | 需先上传素材库再插入 | **支持直接内嵌**，插在光标块位置；本期要求放在正文之前 |
| 编辑器 | ProseMirror 系 | **Draft.js**（选区/退格行为差异大，见坑 338–342） |
| 危险按钮 | 发表 | 发布 |

---

## 6. 标题禁词表（命中即改）

重磅 / 独家爆料 / 揭秘 / 炸裂 / 彻底 / 封神 / 翻车 / 末日 / 慌了 / 完蛋 / 震惊 / 不看后悔

> 依据：知乎《社区规范》禁止标题党与营销推广信息；命中即改写为信息型判断句。

---

## 7. 探测记录表（2026-10-30 实测回填，已非 TODO）

首次执行时需探测的项目，本期已全部实测确认：

| # | 探测项 | 实测结果 | 状态 |
|---|---|---|---|
| 1 | 登录判据 | **侧栏有「草稿箱(N)」/「创作主页」且无扫码登录**（~~出现「立即创作」~~ —— 1031 实测该按钮可整个缺席而账号已登录，坑 362） | ✅ 已测（v3.75.0 修正） |
| 2 | 「立即创作」行为 | **新开标签页** → `https://zhuanlan.zhihu.com/write`；**按钮缺席时直接 `ctx.new_page()` + goto `/write` 等价可用** | ✅ 已测（v3.75.0 补回退） |
| 3 | 标题容器 | `textarea[placeholder="请输入标题（最多 100 个字）"]` | ✅ 已测 |
| 4 | 正文容器 | `div.public-DraftEditor-content`（Draft.js；`innerHTML` 直赋无效，须剪贴板 paste） | ✅ 已测 |
| 5 | 创作声明控件 | **按父级文案定位**：沿 `button.Select-button` 向上 ≤4 层找 innerText 以 `创作声明` 开头的那一行。**~~`div.css-be2u3`~~ 不可用**（本期页面 6 个，第一个是「投稿至问题」）；页面上另有多个 `[role=combobox]`，按「第一个」取会拿到「投稿至问题」→ 选项恒空（v3.76.0 坑 370） | ✅ 已测（v3.76.0 修正） |
| 6 | 创作声明选项文案 | `包含 AI 辅助创作 作者对内容负责`（回读归一化零宽字符后 = `包含AI辅助创作作者对内容负责`）。**🔴 该项不随草稿持久化：刷新后回落「无声明」（3 次复现）。只在发布时提交，与坑 318 同族** | ✅ 已测（v3.76.0 坑 370） |
| 7 | 专栏默认值 | **默认是「不发布到专栏」（`PublishPanel-columnLabel-0` checked=true），此时 combo 为 `null`；手动开启后 combo 默认值是上次用过的专栏（1031 实测「虢礫緙嘞」）**（v3.75.0 推翻旧记录，坑 352） | ✅ 已测（v3.75.0 修正） |
| 8 | 封面 input | `input.UploadPicture-input`（`accept=".jpeg, .jpg, .png"`）。**🔴 v3.76.0：raw CDP `DOM.setFileInputFiles` 对它无效（`files.length` 恒 0），必须 Playwright `set_input_files`**；判据 = 面板里 `添加文章封面` 占位消失（「上传封面」字样常驻，恒真） | ✅ 已测（v3.76.0 修正） |
| 9 | 保存机制 | **无保存按钮，自动保存**；底部 `刚刚 · 草稿`；URL 变 `/p/<id>/edit` | ✅ 已测 |
| 10 | 草稿列表入口 | 创作者中心侧栏「草稿箱(N)」 | ✅ 已测 |
| 11 | 额外发现 | 发布设置含「投稿至问题 / 文章话题 / 定时发布 / 送礼物设置 / **内容来源**」；内容来源提示新闻类须标注来源 | ✅ 已测 |
| 12 | 视频工具栏按钮 | `button[aria-label="视频"]`，点击弹出「导入视频」`Modal-content` | ✅ 已测 |
| 13 | 视频上传 input | `input.VideoUploadButton-fileInput`，**`display:none`；raw CDP `DOM.setFileInputFiles` 返回成功但 `input.files.length` 恒 0**（ASCII 路径 / 复位面板 / 真实鼠标点击 / 导入弹窗四条路全试过）→ **必须用 Playwright `set_input_files`**（v3.76.0 坑 367） | ✅ 已测（v3.76.0 修正） |
| 14 | 视频落位 | **~~插在光标所在块~~ 已被推翻**：知乎媒体块**一律追加到文档末尾**，光标不决定落点。唯一把视频放文首的办法 = **先插视频、再粘正文**（实测 block 1 = VIDEO）。事后搬动全部失败：光标置顶无效、Cut/Paste 无效、HTML5 拖拽会直接删掉视频块（v3.76.0 坑 367） | ✅ 已测（v3.76.0 修正） |
| 15 | 视频可播放判据 | `.Editable-video` 的 `dataset.videoPlayable === 'true'`，**25 MB / 196 s 文件约 40 s**（旧记 10–15 s 偏乐观）。**卡片延迟出现，等待期内反复重试会累积成多个视频块（本期堆到 5 个），必须去重到 1 个**（v3.76.0 坑 367） | ✅ 已测（v3.76.0 修正） |
| 16 | 视频持久化 | 刷新页面后视频卡片与前后文本均完好；**但刷新后可能出现 2 个视频块（延迟上传的第二次生效）**，需再核对 `vids == 1` | ✅ 已测（v3.76.0 补） |
| 17 | 图片上传 input | **正文配图专用 = `input[accept*="image/webp"]`**。**🔴 v3.79.0 坑 392：编辑器常驻 3 个 `input[type=file]`（导入文档 / 正文配图 / 封面），点工具栏「图片」还会动态挂第 4 个 `image/*`，禁按索引取**。**占位符 -1 ≠ 图片 +1**（失败的替换会吃掉占位符但不产生卡片）；**`files.length===1` 也不等于进了正文**（坑 391：`blob:` 预览渲染但不换真链）。**配图计数只认 `src` 含 `draft_token=<文章id>` 的 `img`**，`naturalWidth===1920` 的是视频封面缩略图（坑 368）。**位次须按块↔场景哈希校验**（坑 393） | ✅ 已测（v3.79.0 修正） |
| 18 | 专栏真实选中判据 | **两级**：`.ColumnSetting-ColumnSelector` 内 `input[type=radio]` 的 `checked` **且** combobox 文本归一化 == 目标专栏名（只判 `checked` 会漏掉「开关开了但选错」，v3.75.0 最终版） | ✅ 已测 |
| 19 | 草稿箱 URL | `zhihu.com/creator/manage/creation/draft?type=article\|answer\|zvideo`，子标签「文章草稿」。**必须硬 goto `?type=article`**；点侧栏 tab 会落 `?type=answer` 只列回答草稿（v3.75.0 坑 353） | ✅ 已测（v3.75.0 修正） |
| 20 | 端到端 | 视频 1（playable）+ 图 6 + 封面 1 + 创作声明 + 专栏，`ZHIHU_DRAFT_OK`。**注意该标志只覆盖视频/声明/正文/图数四项**，封面、专栏、字面星号须另行回读（v3.75.0 坑 354） | ✅ 已测（1030 / 1031 两期实跑） |

**尚未实测**：封面裁剪弹窗行为、`zhihu-images/` 目录生成脚本、文章的最终发布流程（本站点不执行发布）。
