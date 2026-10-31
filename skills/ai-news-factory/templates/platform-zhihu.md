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

### 1.5 标题规则

- 上限 **100 字**（编辑器 placeholder 明示「最多 100 个字」）
- 不要带 `【YYYY-MM-DD】` 前缀（那是公众号/视频平台的排版习惯，知乎不需要）
- 不用「4条重磅AI新闻一次看完」这类营销后缀
- 示例：`Claude 账号进入 KYC 与封号双收紧，Opus 一个额度做完了 Astra 半天的活`

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
☐  7. 正文已披露 AI 使用目的与相关部分（文末 AI 辅助创作说明段）
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
| 图片上传 input | `input[type=file][accept*="image/webp"]` |
| 封面 | `input[type=file][accept=".jpeg, .jpg, .png"]`（class `UploadPicture-input`） |
| 创作声明 | `div.css-be2u3` 中 `label` 文本 == `创作声明` → 其 `button[role=combobox]` |
| 创作声明选项 | `.Select-option`，目标文本 `包含 AI 辅助创作 作者对内容负责` |
| 专栏收录 | `.ColumnSetting-ColumnSelector` 内 `input[type=radio]` 的 **`checked` 属性**；真实专栏名 `「今日羊报 AI」`（中间是半角空格 U+20，末位是大写 I） |
| 保存状态 | 底部 `刚刚 · 草稿` / `N 分钟前 · 草稿`（**自动保存，无「保存草稿」按钮**） |
| 危险按钮 | `发布`（`Button--pri`）、`预览`（安全但无用） |

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

知乎支持内嵌视频。视频卡片**插在当前光标所在块**，所以光标移到文档最开头即可让它排在正文前面：

```python
# 1) 光标移到第一个块的开头
page.evaluate("""() => {
  const el = document.querySelector('div.public-DraftEditor-content');
  el.focus();
  const first = el.querySelector('[data-block="true"]') || el;
  const r = document.createRange(); r.setStart(first, 0); r.collapse(true);
  const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
}""")
# 2) 点工具栏「视频」（会弹出「导入视频」弹窗）
page.evaluate("""() => {
  for (const e of document.querySelectorAll('button[aria-label="视频"]')) {
    if (e.offsetParent) { e.click(); return true; }
  }
  return false;
}""")
# 3) 直接对弹窗里的 input 传文件——它点开弹窗前就已经在 DOM 里
page.locator('input.VideoUploadButton-fileInput').first.set_input_files(VIDEO)
```

- 上传约 10–15 s 后出现视频卡片，用 `dataset.videoPlayable === 'true'` 判可播放
- 落位结果：block 0 是自动生成的空文本块，block 1 才是 VIDEO —— **视频确实在正文之前**
- 视频卡片是**单个原子块**，整体删除/移动都按块走（坑 338）

### 3.8 添加封面

```python
# 点「添加封面」展开上传区，再对 accept 为图片的 input 传文件
page.evaluate("""() => {
  for (const e of document.querySelectorAll('*')) {
    if ((e.innerText||'').trim() === '添加封面' && e.offsetParent && e.children.length === 0) { e.click(); return; }
  }
}""")
page.locator('input[type=file][accept=".jpeg, .jpg, .png"]').first.set_input_files(COVER)
```

封面用 `news-pipeline/<DATE>/images/horizontal-4-3.png`（知乎文章封面为横图位，4:3 可接受）。

### 3.9 设创作声明（必做）

```python
# 1) 打开创作声明下拉
page.evaluate("""() => {
  const norm = s => (s||'').replace(/[\\s\\u200b]/g,'');
  for (const box of document.querySelectorAll('div.css-be2u3')) {
    const lab = box.querySelector('label');
    if (!lab || norm(lab.textContent) !== '创作声明') continue;
    const combo = box.querySelector('button[role=combobox]');
    if (combo) { combo.click(); return; }
  }
}""")
# 2) 选目标项
page.evaluate("""() => {
  const norm = s => (s||'').replace(/[\\s\\u200b]/g,'');
  const want = norm('包含 AI 辅助创作 作者对内容负责');
  for (const e of document.querySelectorAll('.Select-option')) {
    if (norm(e.innerText) === want && e.offsetParent) { e.click(); return; }
  }
}""")
# 3) 回读（必须去掉零宽字符再比）
cur = page.evaluate("""() => {
  const norm = s => (s||'').replace(/[\\s\\u200b]/g,'');
  for (const box of document.querySelectorAll('div.css-be2u3')) {
    const lab = box.querySelector('label');
    if (!lab || norm(lab.textContent) !== '创作声明') continue;
    const c = box.querySelector('button[role=combobox]');
    return c ? norm(c.innerText) : null;
  }
  return null;
}""")
assert cur == '包含AI辅助创作作者对内容负责', f'创作声明未生效: {cur!r}'
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

### 3.12 上传验收判据

| 项 | 判据 |
|---|---|
| appmsg 级 ID | 编辑页 URL 变为 `zhuanlan.zhihu.com/p/<id>/edit`（说明已落库为草稿） |
| 标题 | `textarea` value 与 TITLE 完全一致 |
| 正文 | `div.public-DraftEditor-content` innerText 长度 > 800 |
| 视频 | `.Editable-video` 数 == 1 且 `data-video-playable == 'true'`；块序在第一个正文块之前。**判块序要看前 3 块的 kind 序列**（如 `0:TXT(空) 1:VIDEO 2:正文`），**不要**看日志里的 `first block: TXT|`——那行用 `startswith(('VIDEO','TXT'))` 取第一个匹配块，正文场景下永远是 TXT，与视频是否插入无关（v3.75.0 坑，1031 实测）|
| 图片 | `IMG` 块数 == 源文图片数，且无 `__IMG__` 残留 |
| 封面 | 封面槽位有图（`img` naturalWidth > 200 或槽位显示已上传态）。**必须并入 `ZHIHU_DRAFT_OK` 的 `ok` 表达式**——旧版漏了它，封面缺失也照印 OK（v3.75.0 坑 354）|
| 创作声明 | combobox 回读归一化后 == `包含AI辅助创作作者对内容负责` |
| 专栏 | **三级判据**（v3.75.0 坑 352 修正）：① 开关是否打开（radio `PublishPanel-columnLabel-1` 的 `checked`）② 打开后 `combo` 是否存在（关态下为 `null`）③ combo 文本归一化后是否 == 目标专栏。**只判第 2 级会漏掉「开关压根没开」这一上游形态**（1031 实测默认就是「不发布到专栏」checked=true）|
| 字面星号 | 全文块文本不含 `**`（坑 341）。**必须并入 `ok`**——`all` 捆绑包不含 footer，旧版永远不会自动跑（v3.75.0 坑 354）|
| 块数守恒 | `len(blocks) == 正文块数 + 2`（+视频卡片 +自动空块）；1031 实测 32 → 34。数量不守恒 = 有块被 `Backspace` 吃掉（坑 342 的指纹）|
| 危险动作 | 全程未点击「发布」 |

**🔴 `ZHIHU_DRAFT_OK` 的真实语义（v3.75.0 坑 354）**：当前脚本的 `ok` 只含 `videos==1 / playable / decl / bodyLen>800 / IMG 数` 五项，**它只证明视频、声明、正文、图数四件事**，不证明封面、专栏、无字面星号。看到 OK 不等于全绿——要么把三项并进 `ok`，要么在 checklist 里另行逐项回读。

---

## 4. 坑（坑 334–355、362–365）

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
| 5 | 创作声明控件 | `div.css-be2u3` → `label`=创作声明 → `button[role=combobox]` → `.Select-option` | ✅ 已测 |
| 6 | 创作声明选项文案 | `包含 AI 辅助创作 作者对内容负责`（回读归一化零宽字符后 = `包含AI辅助创作作者对内容负责`） | ✅ 已测（已实设并回读成功） |
| 7 | 专栏默认值 | **默认是「不发布到专栏」（`PublishPanel-columnLabel-0` checked=true），此时 combo 为 `null`；手动开启后 combo 默认值是上次用过的专栏（1031 实测「虢礫緙嘞」）**（v3.75.0 推翻旧记录，坑 352） | ✅ 已测（v3.75.0 修正） |
| 8 | 封面 input | `input[type=file][accept=".jpeg, .jpg, .png"]`（class `UploadPicture-input`） | ✅ 已测 |
| 9 | 保存机制 | **无保存按钮，自动保存**；底部 `刚刚 · 草稿`；URL 变 `/p/<id>/edit` | ✅ 已测 |
| 10 | 草稿列表入口 | 创作者中心侧栏「草稿箱(N)」 | ✅ 已测 |
| 11 | 额外发现 | 发布设置含「投稿至问题 / 文章话题 / 定时发布 / 送礼物设置 / **内容来源**」；内容来源提示新闻类须标注来源 | ✅ 已测 |
| 12 | 视频工具栏按钮 | `button[aria-label="视频"]`，点击弹出「导入视频」`Modal-content` | ✅ 已测 |
| 13 | 视频上传 input | `input.VideoUploadButton-fileInput`，**弹窗前已在 DOM**，可直接 `set_input_files` | ✅ 已测 |
| 14 | 视频落位 | 插在光标所在块；光标置文档开头 → block 0 自动空文本、block 1 为 VIDEO（即在正文之前） | ✅ 已测 |
| 15 | 视频可播放判据 | `.Editable-video` 的 `dataset.videoPlayable === 'true'`，上传约 10–15 s | ✅ 已测 |
| 16 | 视频持久化 | 刷新页面后视频卡片与前后文本均完好 | ✅ 已测 |
| 17 | 图片上传 input | `input[type=file][accept*="image/webp"]`，上传落在光标块 | ✅ 已测 |
| 18 | 专栏真实选中判据 | **两级**：`.ColumnSetting-ColumnSelector` 内 `input[type=radio]` 的 `checked` **且** combobox 文本归一化 == 目标专栏名（只判 `checked` 会漏掉「开关开了但选错」，v3.75.0 最终版） | ✅ 已测 |
| 19 | 草稿箱 URL | `zhihu.com/creator/manage/creation/draft?type=article\|answer\|zvideo`，子标签「文章草稿」。**必须硬 goto `?type=article`**；点侧栏 tab 会落 `?type=answer` 只列回答草稿（v3.75.0 坑 353） | ✅ 已测（v3.75.0 修正） |
| 20 | 端到端 | 视频 1（playable）+ 图 6 + 封面 1 + 创作声明 + 专栏，`ZHIHU_DRAFT_OK`。**注意该标志只覆盖视频/声明/正文/图数四项**，封面、专栏、字面星号须另行回读（v3.75.0 坑 354） | ✅ 已测（1030 / 1031 两期实跑） |

**尚未实测**：封面裁剪弹窗行为、`zhihu-images/` 目录生成脚本、文章的最终发布流程（本站点不执行发布）。
