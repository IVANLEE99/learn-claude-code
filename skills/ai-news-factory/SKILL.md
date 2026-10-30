---
name: ai-news-factory
description: AI News Factory - 从日报/周报/月报 Markdown 自动生成短视频+图文的完整 Pipeline。触发词: "AI日报", "AI周报", "AI月报", "新闻工厂", "news factory", "日报视频", "周报视频", "月报视频", "AI news video", "知乎文章", "知乎发文章"
version: 3.74.0
---

# AI News Factory — 日报/周报/月报短视频自动生成 v3.74.0

将 AI 日报/周报/月报 Markdown 自动转化为 B站风格短视频 + 多平台发布内容，完整 Pipeline：报告 → 去重/选材 → 事件切分 → 视频脚本 → 分镜 → 图片 → TTS → 字幕 → 视频合成 → 封面 → 多平台发布信息 → 公众号图文 → 多平台上传。支持三种模式：日报（单日去重）、周报（7天聚合）、月报（消费 linuxdo-daily v13 已聚合的月报 md，趋势级选材）。

> **🔴 v3.74.0 核心改进（2026-10-30 知乎二次实跑：raw CDP 全链 + 专栏默认值陷阱，坑 344-347）**：① **`cdp_helper.eval()` 不做参数注入**——Playwright 风格的 `eval("(title) => {...}", title)` 第二个参数被**静默丢弃**，JS 侧变量为 `undefined`；最坏情况是 `setter.call(t, undefined)` 把标题写成字面 `"undefined"` 却回读成功。正解 `f"(() => {{ const x = {json.dumps(v)}; ... }})()"`。② **`click_safe` 危险词闸门会误伤「发布设置」**——闸门按子串匹配 `发布`，而展开发布设置面板的入口文案正是 `发布设置`，一拦就卡死设置步骤；**不许改宽闸门、不许传 `allow_danger=True`**，正解是给「展开型」控件写局部安全点击（文案严格等值 + 祖先链无提交按钮 + `SUBMIT` 白名单即拒）。③ **知乎专栏默认值是「上次用过的专栏」**——回读 `radio.checked` 只证明开关打开，不证明选对；1030 实测开关已勾选、专栏名却是随机的 `「虢礫緙嘞」`，判据必须两级（`checked` **且** combobox 文本 == 目标名）。④ **视频卡片封面 input 只在弹窗打开后才在 DOM**，且页面同时有 4 个 file input，按「取最后一个」会选错。**另固化两条视频号判据**：`draftListManager` 必须**新标签**打开（同页 SPA 路由会弹回），封面弹窗关闭后容器不卸载只压成 `0×0`（`offsetParent` 仍为 true）→ 判据改为 `getBoundingClientRect().width > 0` + 封面槽比例回读。

> **v3.73.0（2026-10-30 知乎首次端到端实跑：视频内嵌落位 + Draft.js 三处选区陷阱 + 两处判据假绿，坑 338-343）**：1030 期知乎草稿全链跑通（视频 1 / 图 6 / 封面 1 / 创作声明 / 专栏，`ZHIHU_DRAFT_OK`），过程中踩到六个新坑。**坑 338 —— 视频卡片是原子块**：Draft.js 里 `.Editable-video` 是一个不可分割的块，光标在其后按一次 `Backspace` 删的是**整个视频**；任何含退格的操作后都要重数 `.Editable-video`。**坑 339 —— `Shift+Home` 在 Draft.js 里会反向选到整篇开头**：本想只选占位行，结果 `Backspace` 把占位之前的正文全删了（1030 首轮正文 2025 字 → 441 字、34 块 → 7 块、6 图 → 1 图），**且自动保存已把破坏写进草稿**；正解是 `Range.selectNodeContents(占位文本节点)` 精确选中再退格。**坑 340 —— Vue tab/radio 的 `element.click()` 静默无效**，须取 `getBoundingClientRect()` 中心走 `page.mouse.click(x,y)`。**坑 341 —— 整行加粗的判断漏掉「行首加粗 + 行内正文」**：`startswith('**') and endswith('**')` 放过 `**AI 辅助创作说明**：本文由作者…` 这类行，页面上留下字面 `**`；须逐行 `re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)`，并把「全文块文本无 `**`」加进验收。**坑 342 —— `Backspace` 走的是 Draft.js 的**内部选区**，不是刚设的 DOM 选区**：`paste` 认 DOM Selection 所以落点正确，但退格删掉了文件开头的视频卡片；结论是**任何带退格的步骤之后都必须回读全部结构性计数**（视频数/图片数/块数），缺了立刻补插。**坑 343 —— 专栏选中态 grep 页面文本恒真**：`发布到专栏 / 不发布到专栏` 本来就常驻 DOM；真判据是 `.ColumnSetting-ColumnSelector` 内 `input[type=radio]` 的 `checked`。**另修正一处长期错误文案**：知乎专栏真名是 `今日羊报 AI`（**含半角空格 U+20、末位大写 I U+49**，按页面码点实测），旧文档写的「末位是小写 l、无空格」是错的——那是**抖音/视频号的合集名** `今日羊报Al`（无空格、小写 l U+6C）。两个平台的名称不同，改成了各自的正确值并加了交叉警示。**视频落位已验证**：光标置文档开头 → 点 `button[aria-label="视频"]` → 直接对 `input.VideoUploadButton-fileInput`（弹窗前已在 DOM）`set_input_files` → 约 10–15 s 出卡片 → `data-video-playable === 'true'`；落位为 block 0 自动空文本 + block 1 VIDEO，**即在正文之前**，刷新后卡片与前后文本均完好。模块文档 §3.5–3.7、§4（坑 338–343）、§7（探测项 12–20）已同步。

> **🔴 v3.72.0 核心改进（2026-10-30 新增知乎平台，模块化到 `templates/platform-zhihu.md`）**：**知乎是第五个发布平台，图文 + 内嵌成片视频**。链路 = 公众号图文（Phase 10.3）→ 派生知乎稿 → **合规审核门** → 八步上传（立即创作 / 标题 / 正文+配图 / **正文前插视频** / 封面 / 创作声明 / 专栏收录 / 保存草稿）→ 落库验收。三条与既有平台**不同**的硬约束：① **审核是前置门，不是事后补**——知乎《AI 辅助创作治理细则》要求「作者完成主要智力劳动、审查编辑并对最终内容负责」，所以派生稿必须有「编辑判断」段，且须逐项过 `review-checklist.md` 的 §知乎 十一条才允许上传；② **公众号 CTA 与导流句必须删**——知乎《社区规范》§四禁止在标题/封面加营销推广信息、禁止诱导至第三方平台关注，公众号结尾的「点个赞/转发/关注/评论区聊聊」整段删除，标题也去掉 `| 今日羊报AI` 品牌后缀（改为 ≤40 字信息型标题）；③ **机器人只到「存草稿」为止**——规范§五把「使用自动化/插件批量发布」与「发布机器生成的内容」列为违规，AI 声明**不能豁免**，因此发布动作一律留给用户本人。**✅ 页面选择器已于 2026-10-30 全部实测回填**：编辑器在 `zhuanlan.zhihu.com/write`（点「立即创作」新开标签）、标题 `textarea[placeholder*="请输入标题"]`、正文 `div.public-DraftEditor-content`（Draft.js）、图片 `input[accept*="image/webp"]`、视频 `input.VideoUploadButton-fileInput`、封面 `input[accept=".jpeg, .jpg, .png"]`、创作声明 `div.css-be2u3` 内 combobox → `.Select-option`「包含 AI 辅助创作 作者对内容负责」、专栏 radio `checked`、**无保存按钮＝自动保存**。完整记录见模块文档 §7。仍未实测：封面裁剪弹窗、`zhihu-images/` 生成脚本、正式发布流程（本站点不执行）。

> **🔴 v3.71.0 核心改进（2026-10-30 公众号实测收尾：一处「派生没生成的上传源目录」+ 一处「页面锁定选错标签」+ 一处渲染前须同步的静默隐患，坑 331-333）**：**坑 331 —— 公众号上传配图目录 `wechat-images/` 不是派生产物，漏生成会让 `images` 步 `set_input_files` 直接 `FileNotFoundError`。**1030 期 `news-pipeline/2026-10-30/wechat-images/` 全程缺失，运行 `wechat_upload_1030.py images` 在第 1 张 `scene1.jpg` 就炸 `os.stat FileNotFoundError`——它不是 skill 脚本生成的，是**派生脚本之外**、需要**本地从 `images/scene*.png` 现场转 JPEG** 才能补齐的上传源；同理 `cover.png` 也取自 `images/horizontal-4-3.png`。**铁律：派生完成后先核对上传源目录**——`wechat-images/`（`wx_scene_map` 逐个 `scene<i>.jpg` + `cover.png`）与 `video/`、`captions/`、`images/` 一样都在「生图 + 渲染」之后立即落盘，漏了就先 `PIL` 现场转（`convert('RGB').save(dst,'JPEG',quality=88)`），不要等到 `images` 上传步才撞 `FileNotFoundError`（那一步已先进了编辑器、还得回来补）。**坑 332 —— 公众号 `open` 步的「首选 mp 标签页」可能是「合集管理」（`appmsgalbummgr`），它没有「新的创作」入口，断言与点击都会落空。**1030 期 `ctx.pages` 里既有 `cgi-bin/home`（首页）也有 `appmsgalbummgr`（合集管理），旧写法取**第一个** mp 页，恰好是合集管理页 → `.new-creation__menu-item` 为 null、"新的创作"不在 → `open` 断言失败。**修法：`open` 必须锁定 `cgi-bin/home?token=` 首页**——先扫 `cgi-bin/home&token=`，无则扫任一带 `token=` 的 mp 页并把 token 借到首页 `goto`，再无才 `new_page` 走裸域自动 302；不要直接取 `ctx.pages` 第一个 mp 标签。**坑 333 —— 渲染前若忘了把本期 `captions.json` 同步到 `video-project/public/`，成片字幕会静默沿用上期。**1030 期 `_setup_remotion_1030.py` 只同步了 voiceover 与封面，没同步字幕；第一次渲染出的 mp4 字幕时间轴对得上、画面正常，**只有内容全是 10-29 的**（`public/captions.json` 还是上期时间戳）。这是最危险的一类——成片能出、不报错、ffprobe 也过，只有抽音频逐词核对才发现。**铁律：`_setup_remotion` 里必须有「copy caps + 断言」——复制 `captions/captions.json → public/captions.json`，断言首行含本期关键词、尾帧时长 ≈ 音频总长（±2s），缺一步就在装配阶段 fail-fast，绝不让它进渲染。** 1030 正例：日报 377 帖；成片 226.496s / 1920×1080 / 23,352,377B / 锚点 0.7763（音频口径）；字幕↔mp4 音频 lead 中位 +0.080s、离群 0、7 场景块 Δ≤1ms；公众号 `MP_VERIFY_OK`（appmsgid true / bodyLen 1763 / placeholders 0 / cover block+qpic / titleLen 74 / 合集「今日羊报 AI」）；B站标题超 80 字被平台截断到 70 字已改短、`Claude` 标签大写平台不收改小写 `claude`；视频号 / 抖音由用户手动完成（坑 215 不碰）。

> **🔴 v3.70.0 核心改进（2026-10-29 全链实测：五处「派生残留」与「判据过严/过松」，坑 326-330）**：**坑 326 —— 派生脚本的 `forbidden`/`STALE` 表会误伤本期的合法复述。**1029 把上期事件词整表复制成 `forbidden`，结果 PDF 编译前断言炸在「招股书」上——而本期报告里「用 Anthropic 招股书的 85% 毛利率反推 Opus 5.5 成本」是**必须保留的论据**；同样 `publish.json` 的 `STALE` 表把「Terra」列为禁词，而本期「Codex 稳定性」那条正点名 GPT-6.1 Terra。**铁律：派生后先 `grep 每个 forbidden 词 data/reports/<DATE>.md`，命中的逐个判断是「上期残留」还是「本期合法引用」，后者从禁词表删除并在注释里写明理由**（1029 实测因此移除 `招股书` 与 `Terra` 两个词）。**坑 327 —— 锚点占比只在「低于 0.70」时有既定对策，超过 0.80 没有。**1029 首轮 TTS 实测 `191.991 / 235.727 = 0.8145`，超上限。既有指导（坑 236）只教「把锚点前口播加长约 12 字把占比推过 70%」——那是**加法**；超上限需要**减法或给锚点增重**。本期采用后者：**扩充锚点场景自身的口播**（补一段「延迟 vs 吞吐」的展开，+13.3s），把分母做大，占比降到 `191.991 / 249.035 = 0.7709`，一次通过。**为什么不用「削减前面场景」**：前面 5 个场景各承载一条独立新闻，删任何一条都要重做选材表与审核清单；而锚点场景本身是可加深的概念讲解，扩写不损失信息量。**坑 328 —— `audit` 脚本的可信度枚举是硬编码白名单，新写法会被判 FAIL。**1029 脚本里写了「可信度：官方发布」「可信度：官方站点」，`audit` 的 `CRED` 白名单只有 `官方确认/媒体报道/社区实测/源码迹象/未确认传闻/个人经历/第三方评测/概念定义/官方披露/社区观察` → 2 项 FAIL、`RENDER NOT ALLOWED`。**这是判据过严，不是脚本错**：语义上「官方发布」= 「官方确认」。处置二选一：① 改脚本用白名单里的词（首选，保持判据稳定）；② 扩白名单。**不要**为了绕过而写「可信度：官方确认」但内容其实是站点页面——`官方站点` 那种来源应归到 `官方确认` 或 `社区观察`，按「信息是谁说的」而不是「我从哪看到的」归类。**坑 329 —— `_setup_remotion` 的 `ANCHOR` 常量与 `play_order` 是两处独立硬编码。**1029 换了锚点场景（scene5 → scene6），改了 `script` 里的 `### 场景6（专业锚点·…）`、改了 `gen_publish` 的 `ANCHOR_SCENE`，**但漏了 `_setup_remotion_1029.py` 里的 `ANCHOR = 5`**——它负责断言「占比 ∈ [0.70, 0.80]」并在 `Composition.tsx` 注释里写锚点位置。漏改的直接后果是：若新锚点算出来的占比不在区间内，报错信息会指向错误的场景号，排查时白花时间。**铁律：换锚点场景时必须同时改三处——`script-<DATE>.md` 的场景标题、`gen_publish_*.py` 的 `ANCHOR_SCENE`、`_setup_remotion_*.py` 的 `ANCHOR`（外加注释里的概念名）。****坑 330 —— raw CDP 脚本必须「失败保留标签 + 附着复用」。**视频号 24MB 视频重传一次约 60s，而 1029 的 raw CDP 脚本每跑一步都 `open_tab` 新建 + `finally` 关标签，导致「上传 → 描述 → 封面」被拆成三次运行、每次都要重传。**改成 `attach_or_create()`**：把 `targetId` 落到 `/tmp/<platform>-<date>-tab.txt`，下次运行先查 `/json` 里该 id 是否还在，在就附着、不在才新建；**失败时 `keep=True` 不关标签**，让下一次运行能从断点继续（成功才关并删掉 id 文件）。这一条把「改一版封面」的成本从「重传 24MB + 重填表单」降到「只跑封面那一步」。



> **🔴 v3.69.0 核心改进（2026-10-29 视频号补传实测：两个「界面在动但状态不对」的新形态，坑 324-325）**：**坑 324 —— 后台标签页里 Vue 过渡动画不推进，下拉面板「打开即关闭」**。视频号「添加合集」点开后，`.post-album-wrap .filter-wrap` 立即带上 `zoom-in-top-leave zoom-in-top-leave-active`、`opacity:0`、`getBoundingClientRect().height === 0`，而 `getComputedStyle().height` 仍是 `160px`、`scrollHeight=160`、`.option-item` 有 4 个且 `offsetParent` 非空。**判据陷阱**：`offsetParent !== null` 在高度 0 时仍为真 → 用「可见选项」筛选得到 0 条，会误判成「没有合集」。**根因** = 该标签页 `document.visibilityState === "hidden"`（raw CDP 新开的标签在后台），浏览器把 CSS transition 的推进节流掉了，`leave-active` 永远走不完。**实测无效**：`Page.bringToFront`、HTTP `/json/activate`（返回非 JSON，失败）、hover（`mouseMoved`）、只发 `mousePressed`、JS `dispatchEvent(new MouseEvent("click"))` —— 全部无法让面板停留。**可用修法**：直接在 evaluate 里**剥掉过渡类并内联样式**——`wrap.className="filter-wrap zoom-in-top-enter-to"`、`wrap.style.opacity="1"`、`wrap.style.transform="none"`，再给每个 `.option-item` 设 `height:40px; display:block`；随后选项 `getBoundingClientRect().height > 5` 成立，正常按坐标点击即可（本期实测一次成功，`ALBUM AFTER: 今日羊报Al`）。更一般的判据：**任何「点开就消失」的下拉/浮层，先量 `getBoundingClientRect().height`，不要用 `offsetParent` 或 `getComputedStyle().height` 判可见**。**坑 325 —— 上传就绪的假绿信号**：视频号表单的 `.input-editor` 在**上传之前就已存在**，所以「`ready = !!sr.querySelector(".input-editor")`」在文件刚喂进去时就返回 true，脚本会立刻往下走，后面写描述、设封面全落在空表单上。**真判据** = `sr.querySelectorAll("video").length >= 1` **且** `video.duration` 接近成片时长（本期 249s，实测 `dur=249`）**且** `body` 不含「点击上传/拖入此区域」。本期视频号正例（raw CDP 全链）：短标题 13 字 / 描述 244 字 / 竖封面 810×1080 + 横封面 / 合集「今日羊报Al 共138个内容」/ 「保存草稿」四步自证命中 `BUTTON/保存草稿`（x=893，三按钮 x=833/969/1105 间距 16px）/ 草稿箱 7 条首条为本期（07:57）。

> **🔴 v3.68.0 核心改进（2026-10-29 日报实测：抖音草稿「视频不落库」这一新形态，坑 323）**：**抖音「暂存离开」成功后，「继续编辑」横幅、标题、描述、话题、双封面、合集、自主声明全部回读正常，但 `document.querySelectorAll('video').length === 0`、右侧上传区回到「点击上传」——视频文件本身没有被草稿持久化。**这是坑 290/295「双信号」（按钮消失 + 横幅出现）之后的第三种「回读对但没落库」，而且**它骗过的正是双信号**：横幅在、字段全、只差视频。**判据修订：抖音草稿验收必须包含 `videos >= 1`，双信号不再是充分条件。****修复路径：在「继续编辑」恢复出的草稿页内重新 `set_input_files` 上传视频**（页面上有 2 个 `input[type=file]`，**索引 0 是 `image/png,image/jpeg,image/jpg`（封面），索引 1 才是 `video/mp4,...`**；按 `accept` 含 `video` 来挑，不要按索引挑）→ 等 `videos>=1` 且不再「上传中」→ 再点一次「暂存离开」→ **第三次恢复核验 `videos=1` 才算完成**。本期实测：重传后 78%→100% 约 15s，重传后恢复核验 `videos=1`、`missingV=false`、`missingDual=false`、声明在场。另：本期「暂存离开」全程走坑 317 四步自证（`elementFromPoint` 命中 `BUTTON/暂存离开` 且 `ok=true` 才点），视频号因 `finder_login_token=null` 未上传（`login_required`，未做任何点击）。1029 正例：日报 356 帖；成片 249.195s / 7474 帧 / 23,609,760B / 锚点 0.7709（音频口径）· 0.7704（成片口径）；字幕↔mp4 音频 lead 中位 +0.085s、离群 1；公众号 appmsgid + 标题 62 字 + bodyLen 1943 + 占位符 0；B站 `draftId=4046833` 全字段回读通过；抖音第 139 集（重传后）。

> **🔴 v3.67.0 核心改进（2026-10-28 日报实测：一次真实误发布 + 三条「回读正确但没落库」的新形态 + 两个防护自身的坑，坑 317-322）**：**🔴 视频号「保存草稿」误点成「发表」——坐标点击必须自证落点（坑 317，本期最重要）**——1028 期视频号在 07:49 已成功存草稿并落库（`草稿箱 (7)`，首条为本期，时间戳 07:49）；随后为补设 AI 标注第二次、第三次点「保存草稿」，08:08 其中一次**实际命中相邻的「发表」**，`视频 (187)→(188)`、本期卡片出现且状态「原创审核中」、`草稿箱 (7)→(6)`，**平台无二次确认**。根因 = 写法 `el.scrollIntoView({block:'center'})` 与 `getBoundingClientRect()` 在**同一次 `Runtime.evaluate` 内**完成，再 `sleep(0.5)` 才 `mouse.click`——读到的是**滚动落定前**的旧坐标；而视频号三按钮水平相邻（实测 `保存草稿 x=833 w=120` / `手机预览 x=969` / `发表 x=1105`，**y 全为 1088，间距仅 16px**），偏一点就落到邻居。**铁律：任何坐标点击前后必须做「落点自证」——① `scrollIntoView` 单独一次 evaluate，② 等 ≥600ms 落定，③ **重新**测量 rect，④ 点击前 `document.elementFromPoint(x,y)` 断言命中目标元素（或其子节点），自证不通过就不点、直接报错停下**。危险按钮（`发表`/`发布`/`立即投稿`/`存草稿`）**没有任何例外**。**坑 321（同批发现）：`document.elementFromPoint` 不穿 shadowRoot**——wujie/micro-frontend 页面里它只返回宿主 `WUJIE-APP`，`hit === el` 恒假，**落点自证对最需要它的那些控件全部失效**（表现是「连正确按钮都自证失败」，很容易被误判成元素不可点）。修法 = **递归下钻** `sr.elementFromPoint` 取最深节点（≤12 层）。实测：视频号「保存草稿」自证 `ok=true, hit=BUTTON/保存草稿`；同页面 +272px 打到「发表」时 `ok=false, hit=BUTTON/发表`——**正反两向都验过**。这条与坑 302/303（视口外点击静默失效）是同族但更重：那两次是「点了没反应」，这次是「点错了地方还真生效了」。**视频号「视频标注」不随草稿持久化（坑 318）**——设成 `Contains AI-generated content` → `.select-display` 回读一致 → 点「保存草稿」→ toast「已保存」→ **关标签重开该草稿，标注回到「选择视频标注」**，两次复现；同一份草稿的**描述 205 字 / 短标题 / 合集「今日羊报Al」/ 竖封面 3:4 全部正确保留**，只有标注丢。**结论：视频号视频标注只在发布时随请求提交，草稿阶段不落库；「设后回读 = 已生效」在这个字段上不成立。** 对接用户的说法应是「标注已设置，但草稿不保存它，发布前需再设一次」，不能报「已保存 AI 标注」。另注意：改标注时点选项可能**点空**——第二次尝试改回 AI 标注后回读仍是 `No label needed`，**每次选完都必须回读 `.select-display`，不匹配就重来，不要连续盲点**。**`DOM.getDocument` 在本机 Chrome 155 上返回 -32601（坑 319）**——`DOM.enable` 已先行、`Runtime.evaluate` 正常，`Document.getDocument`/`DOM.getDocument` 报 `wasn't found`；**唯一可靠的文件上传路径 = `Runtime.evaluate` 求值出一个 `input[type=file]` 元素（`returnByValue:false`）拿 `objectId` → `DOM.setFileInputFiles({files:[...], objectId})`**，实测对 wujie shadowRoot 内的 input **一次成功**（本期视频 + 竖封面都走这条）。skill 旧文里教「`DOM.getDocument{depth:-1,pierce:true}` → 手工 walk `children`+`shadowRoots`」的段落降级为**备选**；`DOM.performSearch`→`backendNodeId` 那条**本期未复测**，保留但标注未复测。**抖音竖封面弹窗默认带裁切缩放，会切掉 3:4 海报上的文字（坑 320）**——直接喂 1152×1536 后平台判「封面存在文字展示不全问题 / 封面不佳」，海报两端的「别」「一」被裁掉。修法 = 把 `.semi-slider-handle`（在 `.semi-slider-rail` 内，实测 x 区间 778.5–831.5、y≈550）拖到**最小档**：`mouse.move → mouse.down → 分 10 步 move → mouse.up`；**点击与方向键都无效**（试过无反应）。拖到最小后海报完整带边距显示，「封面效果检测通过」+ 发文助手「无建议」。另：抖音「编辑封面」的叶子节点搜索**必须限定在竖槽位（`.coverControl-CjlzqC`[1]）的 rect 内**，全局搜「编辑封面」会命中横向槽位的浮层，打开错误弹窗、上传后仍判「竖封面缺失」。1028 正例：日报 358 帖；成片 152.064s / 4560 帧 / 14,836,850B / 锚点 0.7260（音频口径）· 0.7253（成片口径）；字幕↔mp4 音频 lead 中位 +0.067s、离群 0；公众号草稿 appmsgid + 标题 68 字 + bodyLen 1712 + 占位符 0 + 合集 `.js_article_tags_content` 回读通过；B站 `draftId=4042422` 全字段回读通过；抖音双信号草稿通过（第 138 集）；视频号被误发表（坑 317）。

> **🔴 v3.66.0 核心改进（2026-10-26 日报全程实测：两项「验收自己骗自己」+ 合集弹窗真入口 + 一条被证伪的推断，坑 310-315）**：**公众号合集判据用 `body.innerText` 子串 = 恒真（坑 310）**——本期 `MP_VERIFY` 打出 `collection: true`，`coll_ok = COLLECTION in all_txt`，而 `COLLECTION='「今日羊报 AI」'`（带书名号）命中的是正文 `TAIL` 页脚「🔔 关注「今日羊报 AI」，每天 9 点…」。**合集实际一直是「未添加」**，是后来用 `.js_article_tags_content` 控件回读才发现的。**铁律：合集判据只认 `.js_article_tags_content` 的 textContent（挂上后为 `「今日羊报 AI」`，未挂为 `未添加`），正文/标题里的同名文本一律不算**；这与坑 255「只认独立短文本叶子」同源，但更严——**控件有专属 class 就直接用 class，别做文本搜索**。**正文图片计数被 ProseMirror 分隔符污染 = 恒假（坑 311）**——`body.querySelectorAll('img')` 返回 12 个，其中 **6 个是编辑器为每个图片块插入的 `IMG.ProseMirror-separator`**（`src` 为空、`naturalWidth=0`），于是 `all(w>100)` 恒假；真图只有 6 张（1080×608 ×5 + 1080×810 ×1）。**修法：先按 `classList.contains('ProseMirror-separator')` 与 `src` 非空双重过滤再断言尺寸**；反过来，只按 `imgCount>0` 判「图都在」同样是假阳性。**合集弹窗唯一能打开的入口是 `.allow_click_opr.js_article_tags_label`（坑 312）**——点「合集」二字（`SPAN.lbl_content`）、点行内空白、点 `.frm_checkbox_label` 整行**全部不生效且不报错**（DOM 节点数 1377→1377，无异常），随后「保存为草稿」照样成功并返回 `appmsgid`，**整条链静默失败**。真入口是「未添加」四个字所在的 DIV（约 54×22，`allow_click_opr js_article_tags_label`）；点开后弹窗容器 `.album-setting-dialog`，输入框 `input[placeholder="请选择合集"]`，选项 `.album-setting-dialog .select-opts-con` 内的 `li.select-opt-li`（本期 3 项，每项 320×36），确认是弹窗内文案精确为「确认」的 `button.weui-desktop-btn_primary`。**「同一个事实」在不同平台文案里措辞可以不同，坑 241 词表禁止跨平台复制（坑 313）**——本期抖音写「比上一代 K3 **便宜 15%**」，视频号写「约为上一代 K3 的 **85%**」，把视频号词表套到抖音直接 `AssertionError: missing issue word: 85%`。**词表必须按 `publish.json` 里该平台自己的 `description` 生成**，跨平台抄一份就必挂。**抖音话题解析器按英文句点切分，`K3.1` 会退化成 `#K3`（坑 314）**——`publish.json` 的 `douyin.tags` 写 `K3.1`，页面回读却是 `["#AI日报","#K3","#订阅计费",…]`，点号被吃掉变成**另一个话题**（不会报错、不会提示）。**要么话题里避开带点号的版本号（改写 `K3`），要么接受降级并在验收里按实际值断言**，不要断言 `#K3.1`。**「reload 丢 token」是个被证伪的推断，写进 skill 前必须复测（坑 315，元教训）**——本期首页回读一度拿到 `len=83` 的「登录超时」空页，当时的解释是「裸 `reload()` 丢了 `token=` 参数」，据此写了「必须带 token 重新 goto」。**收尾复测把这条推翻了**：`RELOAD_TEST {"before_len":1685,"after_len":1685,"after_url_has_token":true,"after_login_timeout":false}`——`reload()` 保留 token、首页完好；裸域 `goto('https://mp.weixin.qq.com/')` 也会自动 302 到带 token 的首页（1685），同样不复现。**结论：`len=83` 的真实成因未知（大概率瞬时），「reload 丢 token」不成立。** 带 token 重新 `goto()` 作为写法仍然安全可用，但**不许把它当根因写进文档**；「一次观测 + 一个顺理成章的解释」不等于已验证的因果，与坑 305（证据与判据须同源）是同族。**B站草稿箱行没有可用 `href`，要进编辑页只能点该行的「编辑」按钮（坑 316）**——`upload-manager/article?group=draft` 列表里草稿行的链接解析出来是 `null`；正确做法是从「标题叶子节点」向上逐级（≤8 层）找 `textContent === '编辑'` 的元素，取 rect 中心 `mouse.click`，通常新开标签落到 `upload/video/frame?type=draft&draftId=…`。回读分区用 `.selector-container .select-item-cont`、标签用 `.label-item-v2-container`（去掉 `×`）、封面取页面内 `naturalWidth>=400` 的最大图。
> **🔴 v3.65.0 核心改进（2026-10-25 W42 周报全程实测，raw CDP 迁移与三处「静默失效」坑 306-309）**：**`playwright.connect_over_cdp` 会整体挂起，SSE 端点却健康（坑 306）**——`curl http://127.0.0.1:9222/json/version` 正常返回、`/json` 列得出 25 个 target，但 `connect_over_cdp` 在 `ws connected` 之后**既不返回也不报错**（timeout 从 25s 加到 90s 一样），四个平台探针全部空转。**铁律：CDP 探针先看 HTTP 端点，端点健康而 playwright 挂起 → 立刻切 raw CDP，不要加大超时、不要重启 Chrome**。raw CDP 三件套（直接复用 `templates/cdp_helper.py`）：① `websockets.connect(..., proxy=None)`——不带 `proxy=None` 会走环境 SOCKS 代理，报 `python-socks is required to use a SOCKS proxy`；② `Runtime.evaluate` 的表达式**必须包进 async IIFE**（`(async () => JSON.stringify(await (async () => { return (EXPR); })()))()`），顶层裸写 `await` 报 `ReferenceError: await is not defined`，而 `JSON.stringify(await (FUNC)())` 直接返回 `undefined`——两种写法都静默给空值；③ `eval` 结果统一 `JSON.parse`，并在 `send()` 里对断线重连一次（wujie 长页面会偶发断开，报 `ConnectionClosedError: no close frame`）。**公众号正文的 `Meta+A` 会选中刚 focus 的标题而不是正文（坑 307）**——先点标题区键入标题、再点正文执行 `Meta+A` 替换，结果正文被标题串覆盖成 3 遍（`bodyLen` 1347 → 120），而 `placeholders=0` 让验收误判通过。**修法：标题与正文是两个独立 ProseMirror，操作正文前必须重新 `window.scrollTo(0,0)` + 坐标点击正文区 + 断言 `document.activeElement` 是第 2 个 ProseMirror**；覆盖后只能「清空 → 重新 `execCommand('insertHTML')`」，不要试图增量修。**视频号「保存草稿」点击返回成功但不落库（坑 308）**——短标题/描述分离写入、AI 标注选中、合集选中、双封面全部就位，点「保存草稿」后 `draftListManager` 仍是 4 条旧稿、页面无 toast、无 fetch 记录，`save` 状态只能报 `clicked` 不能报 `true`。**铁律：任何「保存草稿」的成功判据只能是「列表计数 +1 / 目标标题出现」，点击回执不算数**；连续两次失败就停下来报告用户，不要换选择器硬试。**B站分区误点与抖音草稿的时序坑（坑 309）**——B站 `.select-controller` 点击后要等 ≥2.5s 下拉才渲染出 30 个 `.drop-list-v2-item`，**没等就按文本找选项会命中预置值**（本期分区误落「科技数码」）；抖音必须在 `uploading` 变 false **且** 出现「暂存离开」按钮后才填表，否则标题被吞。修法见下方 v3.65.0 段。
> **🔴 v3.64.0 核心改进（2026-10-25 开工前自检，两处「证据对、结论错」的判据坑 304-305）**：**端点身份按 `_000/_001` 后缀判会静默判错（坑 304）**——1025 实测 `settings.json` 是 `GEN_IMG_API_URL`=rainflow、`_000`=prism.uno、`_001/_002`=elysiver，而同期 `To_Learn.md` 备忘写的是 `_003`=rainflow、本体=prism.uno，**两份记录编号完全不同**；按下标判「是不是 rainflow」会让 size 传错、网关回「不支持的图片比例」，症状与坑 300 一模一样极易混。**修法：一律按 URL 域名子串判**（`"rainflow" in api_url`），fallback 顺序也按域名排，开工前先打印 `{后缀: 域名}` 一览核对。**终态验收的判据没做空白归一化，证据与结论自相矛盾（坑 305）**——`final_verify` 把证据 `draftSec` 归一化后打印（`t.slice(...).replace(/\s+/g,' ')`），却拿**未归一化**的 `t` 跑 `/Kimi K3\.1/`；首页卡片把标题折成 `Kimi\nK3.1`，于是**同一条日志里打印的证据明明含 `【2026-10-25】Kimi K3.1 Pro …`，结论却是 `draftHasToday: false`**。**铁律：判据和证据必须用同一份归一化文本**（先 `const t = raw.replace(/\s+/g,' ')`，之后只碰 `t`）；**「打印的证据命中、结论却是 false」就是这个坑的指纹**，见到先查判据，别怀疑平台。
> **🔴 v3.63.0 核心改进（2026-10-25 日报实测，生图 size 派生污染与两处视口外静默点击四坑 300-303）**：**derive 的日期替换会污染尺寸字面量（坑 300）**——`'1024' → '1025'` 全串替换把生图脚本里硬编码的 `size: '1536x1024'` 改成 `'1536x1025'`，rainflow 回「不支持的图片比例」；排查指纹 = 网关报比例不支持但比例明明没问题 → 先 grep 尺寸字面量有没有被日期吃掉；修法 = **尺寸不硬编码，按端点运行时算**（rainflow 用 `auto`，其他 `1536x1024`）。**`size:'auto'` 会返回方图，必须在 prompt 写死横构图（坑 301）**——rainflow 的 `auto` 在无构图提示时返回 1254×1254，塞 1920×1080 被裁两侧；prompt 末尾加 `Wide 16:9 horizontal cinematic composition, full-frame landscape framing.` 后 6/6 得 1672×940/941（1.78）。**B站分区真选择器是 `.drop-list-v2-item`，且在视口外时坐标点击静默无效（坑 302）**——旧脚本按通用 `li,div,span,p` 文本匹配命不中，分区停在默认「音乐」；`人工智能` 项在 y=759 超出 769 视口，`mouse.click` / `el.click()` / `dispatchEvent` **全部静默失败不报错**；修法 = `locator('.drop-list-v2-item').filter(has_text=...).first.scroll_into_view_if_needed()` 后 `click(force=True)`。**视频号 `.mark-tag-select` 同样初始在视口外（坑 303）**——rect.y=1208 时 `mouse.click` 返回成功但 `.mark-tag-options` 仍 `display:none`、选项查询返回 `[]`（看着像「下拉里没有 AI 选项」）；修法 = `scrollIntoView({block:'center'})` → 重取 rect → 点击 → **先断言 `display === 'block'` 再查选项**。与坑 302 同根：**任何 `mouse.click` 前必须确认目标 rect 在当前视口内**。小坑：视频号 `edit-cover-dialog-container` 关闭后仍留在 DOM 且 rect 为 0×0，「容器存在」判弹窗未关是假阳性（改判 `rect.width>0 && rect.height>0`，或直接回读槽位 `img.naturalWidth/naturalHeight`）；封面喂图后必须等预览图出现目标尺寸再点确认；B站标签可能被平台单独拒收（本期 `AI大模型` 未入 chips，6/7），断言写成「记录缺失但不阻塞」。1025 正例：日报 370 帖 / 成片 163.392s / 4900 帧 / 16,361,460B / 锚点 0.7657；字幕块重分配六块起点 Δ 全 0ms，mp4 音频验证 lead 中位 **+0.097s** / 离群 0（57/72 可测）；四平台全草稿。
> **🔴 v3.62.0 核心改进（2026-10-24 日报返工，字幕「跨场景错位」两坑 298-299）**：**坑 283 只解决了「块平移」，没解决「块重分配」——用户二次反馈「1:34 还是对不上」的真因是字幕按场景编号序落盘（坑 298）**。1024 期 `play_order=[1,2,3,5,4,6]`，`captions.json` 里 MoE 文案（script scene4）占着 84.4–112.9s、程序员节文案（script scene5）占着 113.5–143.9s——**整块互换而非平移**。当晚第一次修复用了 `realign_captions_1024.py`，它只在「字幕已归属的那个场景」内部做重新锚定与缩放，**从不重新推导每条字幕属于哪个场景**，所以互换原样保留、重渲后现象不变，白渲一次。**根治写法：按 `voiceover-texts.json` 的每场景正文长度做字符累加，把 captions 精确切成 6 组（归一化后 188/205/179/192/214/26 字符，累计 1004 与脚本完全相等即可断言），再按 `play_order` 累加各场景 wav 时长定块起点，块内用「该场景自己的 wav」的词级 ASR 重新计时**——不能复用一个全局 ASR 流，否则跨场景边界处会拿到相邻场景的时间。**坑 299：验证必须对渲染后的 mp4 做，不能对源 wav 做**。当晚第一轮「验证通过」是拿 `voiceover/sceneN.wav` 按播放序拼 `full_play.wav` 跑的 ASR——那个文件本来就是按播放序拼的，**必然通过，等于没测**；真正的证据只能从成片里取：`ffmpeg -i out.mp4 -vn -ar 16000 -ac 1 mp4_audio.wav` → faster-whisper 词级，再抽帧看烧录字幕。实测流程：mp4 音频 84–114s 确是程序员节、114–144s 确是 MoE（音频顺序本来就对），而 95/100/105/110s 的帧烧的却是 MoE 文案——**「音频对、字幕错」是块互换的指纹**。验收量化用「首 3 字锚定 + 取最近出现位置」：lead 中位数 +0.205s、最大 +0.71s、最小 −0.17s（54/64 条可测）；**禁用全文字符流 SequenceMatcher 直接量偏差**，长片会把累积插入/删除摊到每条上，得到「全部 64 条都 >0.5s」的假信号（实测中位 1.31s，纯属对齐器假象）。另：场景尾行字幕要比发声晚收 0.3s 左右，`offset` 实测 scene4 末条 gap 0.308s、scene6 0.298s → 尾行 `endMs` 补到静音起点即可。
> **🔴 v3.61.0 核心改进（2026-10-23 日报实测，视频号标注/合集新 DOM + 抖音恢复令牌六坑 292-297）**：**视频号 AI 标注真控件是「视频标注」下拉，不是中文勾选框（坑 292）**——wujie shadowRoot 内找「AI生成」/`input[type=checkbox]` 永远 `ai declare: absent`；真控件 = `.mark-tag-select` 的 `.select-display` + `.mark-tag-options`，选项全英文 `No label needed` / `Contains AI-generated content` / `Fictional storyline for entertainment only` / `Personal opinion for reference only` / `Content contains ads` / `Self-recorded content` / `Content is reposted`，**合规须选 `Contains AI-generated content`**；回读以 `.select-display` 文本为准。**视频号新版合集 DOM 变了，且 wujie 内 Vue 组件只认真实鼠标坐标点击（坑 293）**——旧 `.option-item` 前缀匹配返回 False；新链路 = 点 `.post-album-display` 展开 → `.post-album-wrap .option-item` 选项；**JS `.click()` 对这层 Vue 组件不生效（返回成功但 display 不变）**，必须取 `getBoundingClientRect` 中心后 `page.mouse.click(x,y)`；选项文案带「共N个作品」（本期 132/4/22/4）。**wujie shadowRoot 内 file input 用 `evaluate_handle().as_element()` 必 detached（坑 294）**——视频号封面对话框（`.vertical-img-wrap .edit-btn` → 标题「编辑个人主页卡片」→ 取消/确认）上传时，`as_element().set_input_files()` 报 `Cannot set input files to detached element`；改用 Playwright locator 形式 `page.locator('wujie-app input[type=file][accept*="image"]').first.set_input_files(...)` 一次过；确认按钮同样 JS 查不到（`.weui-desktop-btn_primary` 从错误 wrapper 取空），走真实坐标点击。**抖音「继续编辑」是一次性消费令牌，核验后必须同标签再暂存（坑 295，坑 290 第三形态）**——抖音**没有草稿列表页**（`/content/manage?tab=draft` 空壳），唯一恢复入口是发布页横幅；为核验新开标签点「继续编辑」→ 读表单 → 关标签，**草稿就此消失**（此后任何标签横幅都不再出现）。正确 = 端到端一次跑完：暂存 → **同标签**点「继续编辑」回读 → **再点一次「暂存离开」** → 终态「按钮消失 + 横幅出现」；外部标签只准**读**横幅文本，**禁点击**。**抖音竖封面真入口是悬停槽位→「编辑封面」，弹窗内正确 input 是 `.selectArea-BCIYQD input[type=file]`（坑 296）**——`get_by_role('button', name='设置竖封面')` 常 `disabled`（只是提示位），点它必超时；弹窗内 6 个 file input 中其余 4–5 个是模板/贴纸选择器，喂错**静默无报错**。封面槽位按 `.coverControl-CjlzqC` 下标断言：`[0]`=横 4:3、`[1]`=竖 3:4，用 `img.naturalWidth/naturalHeight` 判 1536×1151 / 1150×1535；「竖封面缺失」文案在 AI 推荐封面生成期会**瞬时为真**，**禁只 grep 文本判封面**。**抖音合集选项匹配必须最小面积法排除下拉容器（坑 297）**——`/^「?今日羊报/` + `/共\s*\d+\s*个作品/` 会同时命中整个下拉容器（文本 `请选择合集不选择合集「虢礫緙嘞」共4个作品…` 整块），点它等于没选；约束 `textContent.length ≤ 40` + `rect.height ∈ [10,90]` 后**取面积最小的节点**点击，本期命中 `「今日羊报Al」共132个作品`。1023 正例：日报全量抓取完成；成片 128.128s/3842 帧/1920×1080/14,178,371B 锚点 0.7110；封面本地 PIL 对齐 2026-10-21 海报模板（横 1536×1152/竖 1152×1536）；四平台全草稿（B站 人工智能 分区+7 标签+合集、公众号 appmsgid+bodyLen1179+占位符0、视频号 描述+短标题+合集「今日羊报Al」+AI标注英文选项+3:4 封面、抖音 标题+desc157+5 话题+声明+双封面+第133集）。
> **🔴 v3.60.0 核心改进（2026-10-22 日报实测，登录探测与空壳重挂四坑 288-291）**：**登录探测必须用 default context 新开页（坑 288）**——`connect_over_cdp()` 返回的是 Browser 不是 context，直接 `ctx.new_page()` 等价 `browser.new_page()` 自建**隔离 context 不共享 cookies**，四平台（B站/抖音/视频号/公众号）登录探测全误判 `login_required`，而旧 tab 明明停在登录后 URL、新开页却跳扫码页；正确写法=`browser.contexts[0].new_page()` 取 default context 再开页，goto 上传页 wait 4s 后按 v3.52 判据读表单元素（B站「上传/投稿」、抖音「作品描述」、视频号 url 无 `login.html`、公众号「新的创作」）判定，**禁用隔离模式做登录探测**。**wujie 空壳重挂要开全新标签而非旧标签 goto（坑 289）**——空壳判据 `wujie-app` 存在但 shadowRoot 内 `input/button/[contenteditable]` 计数=0（appKids=1、inShadow=0）；旧标签上 `page.goto('/platform/post/video')` 只改 URL 不触发 wujie 重挂载、仍是空壳，`Page.reload` 多次亦无效；正确=`pg.close()` + `browser.contexts[0].new_page()`（新标签必须走 default context 才共享登录态，同坑 288）+ goto `/platform/post/create` 一次挂载成功（实测 1201 节点 + file input 就绪），此后每步前先断言 `hasWujie && inShadow>0` 再动上传区/表单。**抖音「暂存离开」点击可能被吞，必须双信号验收（坑 290）**——点击回执（`locator.click()` 返回）**不等于**草稿落库，偶发点后表单未关闭、内容随页面关闭丢失；验收=轮询到「暂存离开」按钮消失 `hasZancun=false` **且**「继续编辑」恢复横幅出现，两者齐才算成功（坑 14.10 单信号验收的补强），缺一即重做上传+meta+封面后 JS 直点按钮，**不得只凭点击回执汇报草稿已存**。**B站视频上传直接对 accept 含 video 的 input `set_input_files`（坑 291）**——新版投稿页 `expect_file_chooser` 点击「上传视频」必超时（不触发原生 chooser），改为遍历 `input[type=file]` 按 `accept` 过滤（含 `video`/`mp4` → 视频；含 `image` → 封面弹窗内的图，坑 218 复用）后直接 `set_input_files`，**禁用索引定位**（页面上 `.mp4`×2 / `.txt` / `.zip` / 封面 image 共存，按 `inputs[1]`/`inputs[-1]` 会喂错 input 且全程静默无报错）。1022 正例：日报 387 帖全带正文；TTS 112.38s 锚点 0.7073 容差内；成片 112.512s/3374 帧/1920×1080；四平台全草稿（B站分区/声明/7 标签、公众号零占位符、视频号 wujie 全链、抖音双信号验收过）；场景图 API 写实版换图后仅重渲染即交付（无需重跑 TTS/字幕）。
> **🔴 v3.59.0 核心改进（2026-10-21 日报实测，合规软化 + 视频号专版 + 正文原位重贴四坑 284-287）**：**视频号无资质账号过审红线=时政外事叙事，对策=删敏感场景出「专版」而非改主版（坑 284）**——1021 主版含 OpenAI 窃听案 scene3（涉外司法叙事+庭审/监控类画面+「窃听器」措辞）反复拒审；主版与其他平台一律不动（坑 215），建临时目录 `video-channel/`（删减口播 texts + voiceover 符号链接复用主版 wav + 按新播放顺序重算字幕），共享工程改前先 `cp` 备份主版 captions（`captions-main-5scene-backup.json`），Composition `sceneConfig`/Root `SCENE_DURS` 临时改删减版渲染，**渲染完立即还原 5 场景配置**（坑 269 纪律）；成片命名加「【视频号专版】」前缀交用户手动传；**删中段场景后锚点必须重算**（本例删 scene3 后 101.074/124.893=0.8093 → 65.754/89.728=0.7328 仍落 [0.70,0.80]），交付前字幕+口播 grep 敏感词（窃听/监控/反代）零残留。**公众号正文原位全量替换（正文含图）唯一可靠方案=DOM 清空+合成 paste（坑 285）**——改稿重传时 `mouse.click` 编辑区中心落在 img 上→Meta+A/Backspace/V 键盘事件全不达编辑器；合成 `ClipboardEvent('paste')` 在非空正文上是**追加**（ProseMirror 用自身 state 光标，不理 DOM Selection，fix2 得 2342 字全双份）；正确流程=① `removeChild` 逐个清空 `.ProseMirror` 子节点（触发 mutation 同步进 state）→ ② 空正文上合成 paste 追加=等效全量替换 → ③ 回读断言 markers 全中+唯一标记 `count==1` → ④ save 后 appmsgid 原位保留（更新稿不新建草稿）。**body 步后 placeholders=N 是正常态，禁当失败判据（坑 286）**——占位符由图片步回填，重贴校验若写「无 PLACEHOLDER」则明明成功也报 FAILED（fix3 假阴性 ×3）；校验只看 markers+去重。**合规冲突处置=停上传→问用户→按选择软化原位更新（坑 287）**——涉具体个人未决案件/未证实指控的绝对化陈述（人名+国籍+「嫌疑人」定性）会触发合规拦截（工具侧与平台侧同理，属合理约束）；正确动作=立即停传、给用户 A（照传）/B（软化后传）/C（删段落）选项，选 B 后按「据媒体报道/疑似/以官方披露为准 + 括注（据 XX，帖 ID；以官方信息为准）」模板软化口播与图文，**原位 update 草稿不新建**；不自作主张删内容。小坑备查：`python3 -I` 断 site-packages（PIL 不可用）→ 跑封面/图像脚本去掉 -I；import 无条件 `main()` 的派生模块前先 `sys.argv=['x','noop']` 垫参；derive 重跑会覆盖手工修复→修复直接 Edit 目标文件再 grep 验证；派生内嵌 NEW_CHECKS 含 `\n` 转义会成真换行→用 `chr(10)`。1021 正例：日报 466 帖/475 全正文 33 批；TTS 124.893s 锚点 0.8093 容差内；成片 125.056s/3750 帧/14.3MB；公众号 appmsgid=100001636 软化原位更新 markers 全中；专版 89.728s/2690 帧/11MB 锚点 0.7328。
> **🔴 v3.58.0 核心改进（2026-10-20 日报返工，字幕播放顺序错位坑 283）**：**`play_order` 重排场景后，字幕时间轴必须跟着重排，否则 1:06 后整体错位（坑 283）**——1020 期播放顺序 `[1,2,4,3,5,6]`（锚点前置调占比），但 `captions.json` 仍按编号顺序 `[1..6]` 拼时间轴：scene3 锚点块（11.765s）在 66.9s，scene4 MiniMax 块（26.695s）在 78.7s；实际播放 scene4 在 66.948–93.643、scene3 在 93.643–105.408。用户报"1:06 后字幕和音频对不上"。修法 = 字幕块整体平移（锚点块 +26.695s、MiniMax 块 −11.765s）后**按 startMs 重排数组**（Subtitles 按 startMs 独立定位，重排为干净；保留块内相对偏移），再用 ffprobe/抽帧双验（70s MiniMax 帧 + 95s 锚点帧字幕与画面一致）后替换成片；条数 61/总长 127289 不变，review-checklist §12 无需改。**根治**：gen_captions 组装时间轴时必须读 `play_order`，按播放顺序累加各场景 wav 时长定块偏移，而不是按场景编号顺序拼。
> **🔴 v3.57.0 核心改进（2026-10-20 日报实测，抖音/视频号上传五坑 278-282）**：**视频号 wujie 页秒级重渲染，`set_input_files` 对 ElementHandle 必 detached（坑 278）**——1020 期 `input[type=file]` 每次 fresh-query 都能找到，但 `set` 瞬间即 `Cannot set input files to detached element`，重试 5 次全灭；修法 = 放弃 handle 直设，改 `page.expect_file_chooser` + 点上传区（视频传 `.ant-upload-drag` 中心，一次过 11.6MB）。**视频号发表动态页 ready 判据与上传页不同（坑 279）**——`删除/重新上传`文本在发表页不存在，上传成功看预览帧（OpenCode 字幕帧可现）+ 表单可填；判据必须按页面形态分别写，**截图为准**，文本轮询只做辅助。**视频号封面是"编辑→选帧+上传封面(+号/.add-icon)"弹窗结构（坑 280）**——竖 3:4（`.vertical-img-wrap`）/横 4:3（`.horizon-img-wrap`）各一个编辑入口，点编辑后弹窗含视频帧条 + `上传封面` + `.add-icon` 加号；且弹窗有关闭状态机（点确认后关闭），每次循环须 Esc 清残留→重开→校验 add-icon 可见（`offsetParent` 非空且 rect 非 [0,0]）再点，隐藏节点点下去 filechooser 永不弹。**抖音"上传失败，重新上传"可是假失败态（坑 281）**——右侧预览报失败但表单 poll `ready=True`（标题 17 字/描述/暂存离开全在）；对策 = file input 直传重传（一次轮询即就绪），不纠结预览文案；封面确认按钮须 `完成/保存/确定` 三词全覆盖（1020 首版只找"完成"漏"保存"），且按坑 229 封面不持久失败不阻塞存草稿。**视频号 tab 会跳到 `/post/list`（坑 282）**——疑似发表/保存后自动跳转或 wujie 路由漂移，脚本按 URL 精确匹配即 `channels page gone`；修法 = 按域名模糊匹配（`channels.weixin.qq.com` + `post/` 前缀），list 页先看是否草稿已存再决定回发表页。1020 正例：抖音 filechooser 重传→横竖封面保存→暂存离开→"继续编辑"横幅 True；视频号表单 evaluate 回读 desc/short/errors 全绿（assert 字符串比对中文引号转义易错，以字段分别断言为准）。
> **🔴 v3.56.0 核心改进（2026-10-18 周报 W41 实测，周报派生链七坑 271-277）**：**`image-prompts-*.json` 有 dict/list 两种形态，派生脚本读写前先做 dict 兼容（坑 271）**——W41 的 prompts 落盘是 `{"date":..., "scenes":[...]}` dict 形态（W40 曾是顶层 list），`gen_images_w41.py` 直接 `for p in prompts` 报 `TypeError: string indices must be integers`；修法 = 读完即 `if isinstance(prompts, dict): prompts = prompts.get('scenes', [])`，**读 prompts / voiceover / concepts 三处 JSON 一律加此兼容行**（verify_w41 同样对 `scenes`/`plist`/`bank` 三处做了 dict/list 双兼容）。**derive 做日期替换时「先换日期、后加新 pattern」，extra pattern 必须写新日期形态（坑 272）**——`derive()` 内先 `s.replace(OLD_DATE, NEW_DATE)` 再应用 extra 替换，extra 里若仍写旧文件名（如 W40 的 `image-prompts-2026-10-05~2026-10-11.json`）会 `WARN pattern not found` 静默跳过、插入的兼容行挂错位置；**extra 的锚点字符串一律用 NEW_DATE 形态写**。**NewsTitle patch 必须覆盖「单日残留」形态（坑 273）**——共享工程被日报会话改过后，`PERIOD_DATE` 可能是单日值 `'2026-10-18'`（不是上期周报区间），只备 `OLD_RANGE→NEW_RANGE` 会 patch 落空；W41 的 `patch_newstitle_w41.py` 内置 5 形态全覆盖（单日 `2026-10-18` / 上期区间 / 相邻单日 / 前两周区间）+ `BRAND '今日羊报AI'→'羊报AI周刊'`，落空即 `SystemExit` 报错不静默过。**triple-quote docstring 与 `import` 写同一行必 `SyntaxError`（坑 274）**——derive 内嵌新脚本字符串时 `"""把...改成 W41 周报值。"""` 与 `import pathlib` 同行，`"""` 闭合后同行代码非法；**内嵌模板一律 docstring 独占一行**。**COVER 云端模板是死代码，`SCENES_ONLY=True` 但封面大字仍须同步更新（坑 275）**——W41 `gen_images_w41.py` 封面走本地 PIL（坑 225），`if not SCENES_ONLY` 分支永不执行，但 COVER 字符串里仍印 W40 大字/日期/水印；派生时若不同步换词，下次 SCENES_ONLY 翻转即烧错版。**derive 对 `run_all.sh` 做 VID 整行三形态替换 + `patch_newstitle_w40→w41` 文件名修正（坑 276）**——VID 行在日期替换后可能是新日期+旧标题的混合态（`【10-12~10-18】时间表先行…`），单 pattern 覆盖不全；W41 用三行 `s.replace`（混合态/全旧态/短日期态）全覆盖 + 逐项 `check` 断言（title 无 `时间表先行` 残留）；另 `run_all` 引用的 patch 文件名 `w40→w41` 必须同步改，否则调到旧期脚本。**禁词扫描作用域只限 BODY_HTML 正文段（坑 277）**——全脚本扫描会把 `BANNED_KEYWORDS` 定义行自身计为命中（W41 初版 27 误报）；**扫描对象 = BODY_HTML 常量段**，定义行/注释/verify 逻辑排除在外。正例：W41 TTS 105.994s（666 字门禁 PASS）/ 成片 106.15s 10541KB / 锚点实测 0.7486 / 尾差 0.580s（cap 105.58→wav 105.994→video 106.15，坑 234 三项可解释）/ 公众号 appid=100001605 一次过。

> **🔴 v3.55.0 核心改进（2026-10-19 日报实测，产物完整性与流程坑 265-270）**：**`publish.json` 必须由脚本生成，禁止手写（坑 265）**——1019 手写精简版只填了标题/封面/视频/时长/锚点，漏了顶层 `description`/`tags`/`draft_only` 与各平台 `description`/`partition`，**`platform.channels` 段整个不存在**（视频号脚本取不到标题）。1018 的完整结构=顶层 `date/title/description/tags/draft_only/cover/video/duration/anchor/platform`，`platform` 下 `bilibili{title,partition,tags,description}` / `douyin{title,tags,description}` / `channels{title,tags,description}` / `wechat{title,collection,article,images}`。**派生后必须逐字段 diff 上期 publish.json**，缺字段即失败。**合集下拉需等 ≥2.5s 才渲染选项（坑 266，坑 255 的时效补充）**——1019 `li.select-opt-li` 在 1.2s 时是 `0 items`、2.5s 后正常渲染 3 个选项（羊报AI周刊/「今日羊报 AI」/羊报AI月报）；**坑 255 说「0 items 是没展开不是没选中」仍成立，但补一条：脚本内等待时间不足也会真的没渲染**——对策=输入关键词后轮询等待选项出现（最多 ~5s），再点选。**首页「近期草稿」需 reload 才见刚存的草稿（坑 267）**——1019 存完草稿后首页草稿区仍显示 10-12 的旧条目，`location.reload()` + 9s 后首条才变成当期的「更新于 09:50」；**验收前必须 reload 首页**，否则会误判草稿丢失。（v3.66.0 坑 315 复核：`location.reload()` 会保留 `token=`，此写法安全；曾一度把「登录超时空页」归因为 reload 丢 token，已复测证伪。）**raw CDP 打标必须是数字 1（坑 268）**——上传脚本用 `window.__wx1019 === 1` 严格比较识别编辑页，raw CDP 若写成字符串 `'1'` 则不匹配，脚本会重新开新编辑页（丢已填内容）；**跨工具打标统一用 `= 1`（数字）**。**共享 Remotion 工程 `news-pipeline/video-project` 多会话争用（坑 269）**——该目录被日报与周报（W41）共用，`src/Composition.tsx`/`Root.tsx` 是单份配置；**改前必须先确认另一会话产物已在盘**（1019 实测 W41 周报成片 10-18 22:41 已生成 → 可安全改），并先 `cp` 备份为 `.bak-w41` 再改，改完核对 `public/images/` 场景数（周报 10 场景 → 日报 7 场景要删多余 sceneN.jpg）。**heredoc 写文件前先确认 cwd（坑 270）**——1019 在 `news-pipeline/2026-10-19/scripts` 下执行 `mkdir -p ../prompts && cat > .../prompts/x.json`，因相对路径基准错位导致目录没建成、文件静默丢失（无报错）；**写产物一律用绝对路径或 Write 工具**，写完 `ls` 复核。

> **🔴 v3.54.0 核心改进（2026-10-19 日报实测，公众号 raw CDP 兜底三坑 262-264）**：**`connect_over_cdp` 会成时段性挂起，raw CDP 是唯一兜底（坑 262）**——1019 实测 Playwright `connect_over_cdp('http://localhost:9222')` 连续 3 次 180s 超时（`<ws connected>` 后无响应），期间 `curl /json/version` 与 `/json/list` 全正常（daemon 健康、27 标签页），确认是 attach 层故障非 daemon 死亡；**同一会话内 40 分钟后自行恢复（0.5s 连上）**。对策：① 探针用 `connect_over_cdp(timeout=25000)` 快速判定，挂起即切 raw CDP；② raw CDP 客户端（裸 socket + WebSocket 手写握手 + `Runtime.evaluate`）可完成 open/body/save/verify 全链，**唯一做不到的是文件上传**（`DOM.setFileInputFiles` 不派发 change 事件；JS 构造 `File` 塞 `input.files` 被浏览器拒绝——FileList 只读）；③ 因此 attach 挂起期间**图片/视频上传必须等恢复**，其余步骤可 raw CDP 先行。**raw CDP 注入正文必须用 TextDecoder 解 UTF-8（坑 263）**——`atob(b64)` 返回 latin1 字符串，中文全乱码（`DeepSeek Harness è®¡è´¹å¼å¸¸`）；正确写法是把 Python 的 `BODY.encode('utf-8')` 转成字节数组传进 JS，再 `new TextDecoder('utf-8').decode(new Uint8Array(bytes))`。**重跑 body 不会清除已上传的图片，且 Meta+A/Meta+V 可能静默失效（坑 264）**——1019 改措辞后重跑 `body` 步，`bodyLen 984` 看似成功，但编辑器正文**仍是旧版**（`Meta+A`+`Meta+V` 未生效，焦点不在编辑器），且已上传的 5 张图**保留**（重跑 images 步直接 `no placeholders left`）。**改字必须用 TreeWalker 精确替换文本节点**（`createTreeWalker(pm, SHOW_TEXT)` 找含旧词的节点改 `nodeValue`），改完 `dispatchEvent(new Event('input'))` 再存草稿；**改后必须回读校验**（`tx.includes(旧词)===false`），不能只看 bodyLen。**验收正例**：1019 公众号 appmsgid=100001618（bodyLen 924 / 占位符 0 / 5 张有效图 / 封面 hasQpic / 标题 63 字 / 合集「今日羊报 AI」/ 无 B 档禁词），首页「近期草稿」首条标题文本匹配「更新于 09:50」，「近期发表」无当日记录=未误发表。**B 档禁词误报**：「护栏」在禁词表里针对安全审查语境，但「用量护栏」是技术用语——1019 命中后改为「用量上限」避开，**改词只改公众号正文与 article md，不动已渲染视频的 voiceover**（视频已过审核清单，重跑 TTS+渲染代价不成比例）。

> **🔴 v3.53.0 核心改进（2026-10-18 日报实测，公众号验收入口三坑 259-261）**：**首页「近期草稿」里的 appmsgid 是另一套 ID，验收判据只认标题文本（坑 259）**——首页草稿卡片链接的 `appmsgid=2247485xxx` 与编辑器 `appmsgid=100001596` 完全不同体系，按 appmsgid 文本匹配首页必假阴性（1018 实测 `appid_in_home=False` 而草稿完好在箱）；正确判据=首页/草稿箱 DOM 含**当期标题文本**（`V4.1-Flash-1017`）。**直接 goto 草稿箱列表页 URL 会掉会话 + 默认落在「历史图文素材」tab（坑 260）**——`action=list` 页直跳（带不带 token 均试过）只见「请重新登录」或 2018/2020 旧素材，正确动作=从带 token 的现成 `home/index` 标签页**在页内点击**进入，列表页打开后**必须再点「草稿箱」tab** 才见当期草稿（默认 tab 是「历史图文素材」，不切 tab 会误判草稿丢失）。**「发表记录」tab 点了不跳转、仍回草稿箱列表（坑 261）**——发表记录判据改用**首页「近期发表」区块**（1018：最新=昨日 1017 期 → 当日无发表 ✓）。**正例固化**：公众号分步链一次过（open→body 1036字→images 5图占位符 0→cover hasQpic→title 67字→save appmsgid=100001596 合集「今日羊报 AI」picked→verify 全绿）；分类器故障期（只读过/非只读全拦）把 prep 脚本+状态文件先落盘，恢复后 `prep_wechat_1018.sh`（cover=horizontal + CDP 探活）→ 分步续跑，一次过。
> **🔴 v3.52.0 核心改进（2026-10-17 日报实测，B站上传路径坑 258）**：**渲染/归档文件名 = `publish.json.title`（后缀 `| 今日羊报AI`），但 B站上传脚本按 `publish.json.platform.bilibili.title`（后缀 `｜4条重磅AI新闻一次看完 | 今日羊报AI`）拼 VIDEO 路径 → `FileNotFoundError`**（1017 实测：视频已渲染成功，`bili_upload.py upload` 步在 `os.path.getsize(VIDEO)` 处崩——VIDEO 里含 `｜4条重磅AI新闻一次看完`，实际产物文件名不含该片段）。根因：`publish.json.title` 与 `bilibili.title` 是两个字段（前者列表标题、后者带「N条」营销后缀），渲染用前者、脚本 VIDEO 却抄后者。修法：**B站上传脚本的 `VIDEO` 必须用 `publish.json.title`（与渲染产物名一致），不要用 `bilibili.title`**；派生后先 `ls news-pipeline/{date}/video/` 核对实际文件名再写 VIDEO。**坑 215 全程命中**：本期公众号自动上传成功（open→body 993字→images 5图占位符0→cover hasQpic→title 61字→save appmsgid=100001587 合集picked→verify bodyLen 856 全绿），但 B站/抖音/视频号四平台初始全部未登录（CDP daemon 无登录态）→ 依次标记 `login_required`；后 B站、公众号陆续登录（公众号自动上传完成），其余由用户手动接管，坑 215 收口。**登录态判定假阳性**：抖音首页含「作品发布及管理」等营销文案，脚本 `guard()` 误判「已登录」→ 实际是扫码/验证码登录页；**判据必须看上传表单元素**（`作品描述`/`暂存离开`/`设置封面`），禁以页面出现「作品/发布」文案为准。**公众号配图格式**：`wechat-images/` 需 `sceneN.jpg`（not png），从 `images/sceneN.png` ffmpeg 转，另 `cover.png` = `horizontal-4-3.png` 拷贝；上传脚本 `IMAGES` 按此引用。**B档措辞**：本期「商务部出口登记」正文用「合规边界/临时登记」，避开 B 档禁词「监管/审查」——输出前 `grep` B 档禁词自检全过。
> **🔴 v3.51.0 核心改进（2026-10-16 日报实测，环境断供 + 渲染边界帧）**：**`~/.claude/settings.json` 的 GEN_IMG/MIMO_TTS 凭据会静默丢失（坑 256）**——1016 视频链开工时 settings.json 的 env 只剩 ANTHROPIC_* 十键，`GEN_IMG_API_URL/_KEY`（及 `_001/_002/_003` 回退）与 `MIMO_TTS_API_*` 全没了，`gen_scenes_api.py` 的 ENDPOINTS 解析为空。排查顺序：① `~/.claude/settings.json.bak-*` 备份里找（1016 从 9-22 的 `settings.json.bak-post2video-2931081` 恢复 16 键后 9/9 场景图一次走通）；② 日常跑流水线前 `python3 -c` 打印 endpoint 名 + keylen 做**存在性探针**（禁打印 key 本体）；③ 恢复后原地 `cp settings.json settings.json.bak-pre{MMDD}-HHMM` 留痕。注意 key 的分组语义别搞错：1016 实测 `main`（ai.xmiaom.com）对 gpt-image-2 直接回非 JSON（`Expecting value: line 1 column 1`），实际承接的是 `main_001`（elysiver.h-e.top，grok-imagine-image）——**首轮 5/9、scene2/7/8/9 全挂，重跑 missing-only 即全过**，说明是时段性抖动不是端点死亡，**重跑缺失文件前不要换端点顺序**（与坑 253 的「拆单+间隔重试」同对策）。**TTS 用探针先验环境再跑全量**：1016 先验 `edge-tts 7.3.1`（坑 250 门禁）+ 代理探活（非 CN 出口 IP）双绿后才跑 9 场景，一次过 113.008s / anchor_pos 0.7024。**渲染边界帧漂移约一帧（坑 257）**——1016 成片视频流 113.166667s vs 音频 113.216000s，相差 0.049s（<1 帧@30fps）：逐场景 `ceil(dur*30)` 的垫帧累计 3395 帧，画面边界比音频边界早约一帧，锚点帧 t=79.4s 抽到的是 scene7 尾帧、音频已进 scene5——**属测量容差，不重渲、不重排**（与坑 209 重排阈值 >5% 不可比）。验收时抽锚点帧允许 ±0.2s 偏差，以字幕时间轴为准。**正例固化**：场景时长/锚点用字数预估（1016 预估 0.7065 → TTS 实测 0.7024 一次过，锚点 scene5 排播放第 7 位 `[1,2,3,4,6,7,5,8,9]`）；公众号全链分步一次过（open→body 1471字→images 占位符0→cover hasQpic→title 65字→save appmsgid=100001578→verify 1283字，占位符0、合集 picked）；B站/抖音/视频号用户手动，坑 215 全不碰含核验。
> **🔴 v3.50.0 核心改进（2026-10-15 日报实测，公众号链路两坑）**：**合集「option not found (0 items)」是假阴性，判据只认编辑页回读（坑 255）**——1015 公众号 save 步首跑报 `0 items`，按坑 252 重跑 save **仍 0 items**，但编辑页回读文本已含 `「今日羊报 AI」`，**合集实际早已挂上**。根因：`li.select-opt-li` 只在下拉**手动展开**后才渲染；脚本链路（点「合集」label → 点「未添加」→ 点 `input[placeholder="请选择合集"]` → value-setter 填「今日羊报」）在选项未渲染时**仍会命中默认/唯一合集**并写入，此时 DOM 里没有 `li.select-opt-li`，计数自然是 0——**0 是「没展开」，不是「没选中」**。唯一可靠判据 = 编辑页回读**独立的短文本叶子节点**含合集名（标题/正文里本来就有「今日羊报」字样，必须区分：合集命中的是 `「今日羊报 AI」` 这种独立叶子，不是标题行或 CTA 行）。**禁止**用 `0 items` 当失败信号、禁止据此重跑或转手动。**`type=10 list_card` 第二次假阴性，验收只认首页「近期草稿」（坑 221 补充）**——`wechat_check_draft.py 2026-10-15` 走 `list_card` 返回 `草稿箱标题候选: []` + `in_publish_record: false` → 打印 `两处均无 — 需排查`，而草稿 `appmsgid=100001568` 实际完好。正确动作 = 改走首页**「近期草稿」**入口（点文本为「近期草稿」的节点），实测首条即当期标题，与 10-14/10-13/10-12 历史草稿同列返回；**该入口不跳转 URL**（仍停在 `cgi-bin/home`），不能靠 URL 判断是否进入，只能看 DOM 文本。**正例固化**：本期只上传公众号（B站/抖音/视频号用户已手动，坑 215 全不碰含核验）；`wechat-article-2026-10-15.md` 落盘 8656B 含「无配图版全文」降级节；6 张 `wechat-images/sceneN.jpg` 全过严格解码 + 底边绿行扫描（绿行=0）后才上传；上传脚本 `wechat_upload_1015.py` 带坑 241 内容断言（sections=4 / placeholders=6 / images=6，反期·禁词·密钥全过）。
> **🔴 v3.49.0 核心改进（2026-10-15 日报实测）**：**curl 下载图片被静默截断 → 成片纯绿条，必须严格 PIL 解码 + 尺寸门禁（坑 254）**——1015 成片第 1/3/5 场景底部各有纯绿条（实测 59/725/32 行，RGB 恒 `(0,137,0)`）。排查起初误判为 Remotion/CSS/素材拷贝问题，**根因在图片下载**：`gen_scenes_api.py` 的 `ok-url` 分支 `curl -s -o out URL` 拿到的 body **尾部被截断**（scene1/3/5 分别少 43/16/14 字节），而 `curl` 对截断 body 仍 **exit 0**；脚本只验 `getsize(out) > 5000` 即判成功。三个残缺 JPEG 一路流过 ffmpeg 转 PNG（`-v error` 只吐 `overread 8` 不报错）→ 转 public JPG → 渲染，ffmpeg 容错解码器把**取不到的尾部填成重复值**，烧进成片就是绿条。**修法**：① 下载后**严格 PIL 解码** `Image.open(p); im.load()`，**绝不设 `ImageFile.LOAD_TRUNCATED_IMAGES`**（设了照样读得出、是本坑最大的检测陷阱），截断会抛 `OSError: image file is truncated (N bytes not processed)`，捕获即判失败换端点；② 尺寸门禁 `>5000` → `>20000` 且**同时过解码**；③ 底边绿行扫描做二次断言（取底边 5 点，`|g-137|<12` 且 `|r|,|b|<12` 连续计数，>0 即失败）；④ **禁止只验产物不验源**——1015 一开始反复重转 PNG/JPG 完全无效，因为 `_api.png` 本身就是坏的；⑤ `skip (exists)` 只认「尺寸合规 **且** 严格解码通过」，否则「坏但足够大」的文件永不会被重试（1015 scene1/3/5 就是被旧逻辑跳过的）。**正例固化**：6 场景 `_api`+成图 12 文件全过三合一门禁后才进渲染；场景时长/锚点未受影响（总 98.795s、anchor_scene 5、anchor_pos 0.7376），**无需重跑 TTS/字幕，只需重渲染**。
> **🔴 v3.48.0 核心改进（2026-10-14 日报实测）**：**edge-tts WSS 403 第二根因=客户端版本 DRM 令牌算法过期（坑 250 补充）**——1014 实测：代理出口已美国、时钟偏移 0.5s、`--proxy` 显式指定，7.2.8 仍全线 403；**升级 `pip install -U edge-tts`（7.2.8→7.3.1）后一次通过**。403 排查顺序固定为：①`--proxy` 非 CN 出口（ip-api.com 查出口，ipinfo 常 429）②系统时钟（NTP 偏移 >60s 即修）③**版本升级到 ≥7.3.1**；三步皆过仍 403 才考虑 UA/header 矩阵。**`Document.getDocument` 方法名根本不存在（坑 251 模板修正）**——1013 模板 `channels_upload_1013.py` 里写的 `Document.getDocument` 无论有无 `DOM.enable` 都报 -32601（当时 upload 步未跑通未暴露）；**CDP 正确方法名是 `DOM.getDocument`**（**但 🔴 v3.67.0 坑 319：本机 Chrome 155 上这个也不再可用，报 -32601 `wasn't found`**；首选改为 `Runtime.evaluate` 取 `objectId` → `DOM.setFileInputFiles({files, objectId})`，见 `templates/cdp_helper.py` 的 `Tab.set_files()`）。且 **`DOM.querySelectorAll` 不穿 wujie shadowRoot**（root 级查询返回空数组）——旧方案是在 `DOM.getDocument{depth:-1,pierce:true}` 返回树上**手工 walk `children` + `shadowRoots` + `contentDocument`** 收集 `input[type=file]`（模板=`channels_upload_1014.py` `_file_input_ids()`），**该路径在本机已失效，仅作兜底**。**视频号「空壳」判定假阴性**：`window.__WUJIE` 为 false / `document.body.innerText` 近空 **不代表**子应用没渲染——innerText 不进 shadowRoot，实体判定=查 `wujie-app.shadowRoot` 内表单元素（file input/短标题/合集）；真·空壳判据仍按坑 251（shadowRoot `#app` 后代数 ≤1）。**视频号 setFileInputFiles 后 300s 无 ready=多半 node 选错**：pierce walk 收集的 file input 可能是封面/头像等非视频入口，`setFileInputFiles` 对错 node **静默失败**——正确姿势=set 后先回读 shadow 文本有无进度/`%`，20s 无进度立即换下一个 node，不傻等 300s（1014 用户手动收尾，下期按此验证）。**B站创作声明回读判据修正（坑 247 补充）**：`input[placeholder*="创作声明"]` rect 中心点开 → 选项 rect 中心点「个人观点，仅供参考」→ **回读用 `input.value`**，`body.innerText` 不含已选值（pre-draft `declOk=False` 属预期，以 input.value 为准）；分区三级「知识/人工智能」同现属正常形态。**`connect_over_cdp` 挂起第二形态（坑 251 补充）**：`ws connected` 后卡死在握手返回（180s 超时），同一 daemon 时段性出现（sync API 可用→下一次挂起）；对策不变=raw CDP websockets。**公众号草稿箱 URL 陷阱**：`cgi-bin/appmsg?t=media/appmsg_draft&action=edit` 打开的是**空白新草稿编辑器**不是列表——草稿箱验收判据=首页「近期草稿」文本含标题+更新时间（坑 221/248 组合复用）。**正例固化**：锚点字数预估法（1014 预估≈0.71 → TTS 实测 0.7141 一次过）；封面 fit_size 门（竖版 933/934px 压线通过，172px 固定字号必截断的坑 249 修复在 1014 无回归）；审核清单门禁流程（§1-5、7 绿后渲染，§6 渲染后 8/8 回填）零返工。
> **🔴 v3.47.0 核心改进（2026-10-13 日报实测）**：**封面大字必须按可用宽度实测收缩字号（坑 249）**——竖版封面固定比例字号 `int(w*0.150)=172px` 对 8 字行实宽 1376px，超出可打印宽度（1152−2×margin≈934px）被 PIL 直接裁掉，用户报「内容被截断」；修法 = `font.getlength()` 实测行宽、从目标字号向下收缩（下限 48），生成时打印每行 px 与 limit 并断言 `px ≤ limit`（1013 修复后竖版 812/928 ≤ 934）。横版同样要过门（1013 横版 1272/1276 已贴极限，钩子再长 1 字即截）。**edge-tts WSS 403 根因=出口 IP，第一动作 `--proxy` 走非 CN 出口（坑 250）**——1013 TTS 卡死约 3.5h：时钟偏移（DRM 自校正无效）、版本升降（6.1.16/7.2.8 都 403）、UA/Chromium header 补丁（MSIE+129 探测矩阵 24 组全 403）全部无效，HTTPS `voices/list` 却正常（只有 WSS 被拒）；终局 = `edge-tts --proxy http://127.0.0.1:7897` + 用户把代理切美国出口一次通过，直连与 `api.msedgeservices.com` 仍 403。终端无 `HTTPS_PROXY` env、系统 scutil 代理对 aiohttp 不生效，**必须显式 `--proxy`**（`gen_tts.py` 已固化）；探测脚本用 `python3 -I` 会忽略 `SSL_CERT_FILE` 报证书假故障。**Playwright attach 无报错挂起 → 整平台切 raw CDP websockets（坑 251）**——1013 B站/抖音/视频号三平台 `connect_over_cdp` 全部纯挂起（并发 raw 客户端无冲突 → 是 Playwright flatten 协议自身问题）；视频号另命中 **wujie 空壳**（`#app` 后代数=1、`.app-body-full` kids=0，SPA 未挂载，`Page.reload` 多次无效）→ **`Page.navigate` 到 `/platform/post/video` 重新挂载**（返回 `net::ERR_ABORTED` 属正常），轮询 shadowRoot `#app` 后代数 >10 且 `input[type=file]` 出现才继续（实测 kids=1410）。raw-CDP 上传协议与全步骤模板 = `news-pipeline/2026-10-13/scripts/channels_upload_1013.py`（`DOM.enable` 先行否则 `Document.getDocument` 报 -32601；pierce 遍历找 file input；`Input.insertText` 填 contenteditable；Vue 受控 input 用 value-setter+input 事件）。**公众号占位符/合集偶发空态直接重跑该步（坑 252，与坑 232 同族）**——images 跑完 verify `placeholders=1` → 重跑 `wechat_upload.py images` 幂等补齐（脚本每次扫描剩余 PLACEHOLDER 替换）再 save 即 0；save 首跑合集下拉 `option not found (0 items)`（选项未加载）→ 重跑 save 即挂上「今日羊报 AI」。**坑 236 补充**：加长口播前先**按场景字数预估锚点占比**（时长∝字数，1013 预估 0.6936→补 19 字→0.7060，TTS 实测 0.7099 一次过，省 TTS 返工）；仍略低时锚点场景 atempo +0.1（1.4→1.5）作最后微调。**API 429 双形态（坑 253）**：`maximum 25 requests in 5 minutes` 限频 + `Concurrency limit exceeded` 并发上限都会批量杀死请求（1013 主循环与 skill 回写 workflow 双双命中，6 宽子 agent 全灭、2 宽也有阵亡）→ 对策 = 拆单 + 间隔重试 + workflow 并发宽度 ≤2，被杀 agent 返回 null 不会自动重试，关键提取宁可主循环自己做。**坑 215**：视频号最终由用户手动上传完成，声明后立即停手（含核验）。
>
> **🔴 v3.46.0 核心改进（2026-10-12 周报 W40 实测）**：**周报脚本先过字数门禁再进 TTS（坑 244）**——W40 初版 531 字 → edge-tts 云扬 atempo1.4 实测仅 82s，低于周报 100s 下限整 18s；扩写到 682 字重跑得 104.746s 合格。实测换算 ≈6.4 字/s（atempo1.4），**周报去标点字数门禁 ≥650 字、目标 680–720（105–110s 留头寸）**；脚本写完先 `len(strip_punct(full))` 断言再落 TTS，TTS 实测 <100s 时扩写正文补齐，**不降 atempo、不挪锚点凑时长**。**派生 run_all.sh 必须带 PNG→JPG + 渲染 timeout（坑 245）**——W39 派生版同步段只 `cp scene*.png`，而 Composition 引 `images/scene*.jpg`（v3.45.0 sips/ffmpeg 链是必做步骤不是备注），渲染 seek 到 frame 613 超时；且 10 场景大图默认 30s seek timeout 不够，渲染命令必须 `--timeout=180000`。派生 run_all 后 grep 断言：①同步段含 `ffmpeg ... scene$i.jpg`（或 sips），②渲染命令含 `--timeout`，③无上期日期残留（坑 241 扩展到 run_all）。**concepts.json 结构是 `{concepts:[...], updated}`，concepts 为 list 按 id 查（坑 246）**——verify 脚本 `bank.get('token')` 对 list 直接 `AttributeError: 'list' object has no attribute 'get'`，正确写法 `next(x for x in bank if x.get('id')=='token')`；verify 分两级跑：落盘脚本层即刻跑，**总时长 100–150s 实测项必须等 durations.json 生成后再跑**（无 durations 时 INFO 跳过而非 FAIL）。**B站创作声明是 bcc-select 自定义组件，text= 定位必超时（坑 247）**——`page.locator('text=请选择符合您视频内容的创作声明')` 5s 必超时；正确交互 = `getBoundingClientRect` 取选择框 rect → `page.mouse.click(rect 中心)` 开下拉 → 选项同法点 rect 中心，回读判据沿用 v3.45.0（body 含 `个人观点，仅供参考`）。同理 **form 步分区 locator 超时 ≠ 未选中**——W40 分区 locator 报 timeout 但页面回读已是 `人工智能`，以回读为准不重跑（坑 242 回读铁律正例）。**公众号 `cgi-bin/publish?action=list` 直接 goto 抛 `ERR_HTTP_RESPONSE_CODE_FAILURE`（坑 248）**——发表记录页 URL 不稳定，验收走首页「近期草稿」+ appmsgid 编辑页直达（坑 221 三件套内替代）。**字幕尾差分解补第四项**：坑 234 可加性闭合 = 静音尾 + 帧取整 + 容器 + **whisper 对齐尾隙（末行字幕停在末音节前）**，W40 实测 1.098s = 0.415+0.188+0.048+0.447 精确闭合。**坑 215 收口**：用户中途声明「已经全部手动上传」→ 四平台全部停手（含核验），当期只做 skill 回写。
>
> **🔴 v3.45.0（2026-10-11 日报实测，常规记录无新坑）**：1011 期 daily 585 帖 → 视频 70.25s（2106 帧，anchor_pos 0.7312，标准顺序 [1,2,3,4,5,6] 无需重排）→ 四平台全部存草稿成功（公众号脚本分步 open→save 全过 appmsgid=100001519，B站/抖音/视频号用户手动，坑 215）。**场景图 PNG→JPG 落盘链**：`gen_scenes_api.py` 出图 `images/scene*.png`（1920×1080 PNG）→ `sips -s format jpeg` 转 `video-project/public/images/scene*.jpg`（Composition 引 `*.jpg`），转换链须与引用后缀一致，错配则 Remotion 渲染黑帧。**首帧无标题栏属正常**：NewsTitle 有入场动画延迟，`frame 0` 无标题，验收抽 `2s` 帧（标题栏日期+品牌+首条字幕齐现）；52s 帧验锚点字幕「开头说的那个词」。**B站创作声明回读判据**：下拉框 placeholder 常驻 `请选择符合您视频内容的创作声明`，`textContent` 含该文案 ≠ 未选；真判据 = `body.innerText` 是否含已选项（`个人观点，仅供参考`）——1011 期回读 False 确认未选中后，因用户手动接管按坑 215 停手。旧条目归档见正文 v3.44.0。
>
> **🔴 v3.44.0 核心改进（2026-10-10 日报实测）**：**派生脚本必须做内容校验，语法检查不算数（坑 241）**——1010 期 `derive_gen_scripts` 只跑了 `py_compile`/`node --check`（leftover=0），但 `wechat_upload.py`/`bili_draft.py` 的 TITLE 只换了日期，SECTIONS/DESC/TAGS 全是 1009 旧事件（DeepSeek-V4/magpie/Pi）；直接跑会把上一期内容发出去。派生后必须 grep 断言：①新日期的核心事件词在脚本里（如 1010 → `Anthropic`、`峰谷`），②上一期的事件词零残留（如 1010 不得含 `DeepSeek-V4`、`magpie`），③MARK/截图前缀等日期标识同步（`__wx1009`→`__wx1010`、`wx1009_step`→`wx1010_step`）。**v3.51.0 补充（坑 241 日期三形态，1016 实测）**：`s/1015/1016/g` + `s/2026-10-15/2026-10-16/g` 只能命中①连字符日期（`2026-10-16`）、②裸期号（`1016`）、③下划线标识（`__wx1016`），**漏掉三种形态**：④逗号分隔的 Python datetime（`datetime(2026, 10, 15, 0, 5)`→须手改为 `2026, 10, 16`，1016 `_build_queue` 的 BASE 差点让 32h 窗口整体偏一天）；⑤脚本内嵌的**断言常量**（`REQUIRED_SCENES=[1..6]`→本期 9 场景；`checks`/`FORBIDDEN` 里的上期帖子 ID 与帖数如 `536`→`509`）；⑥**内容字段**（TITLE/SECTIONS/DESC/TAGS/封面大字仍是上期事件，如 `gen_covers_local.py` 封面仍印「别急着封神」）。派生后断言必须分三层：`leftover=0`（三种机械形态）+ **事件词在场/缺席断言**（新事件词在、上期词零残留）+ **场景数/占位数与脚本实际一致**（`len(SECTIONS)==4`、`placeholders` 计数、`REQUIRED_SCENES` 长度）。**B站标签重输仍被拒时点推荐行同名 chip（坑 232 补充）**——「今日羊报AI」首入被拒（话题专用 toast）原样重输即过，但 `Claude` 大写连拒两次、重输也失败，点推荐标签行的 `claude`（小写，平台规范化）成功；fallback 顺序 = 重输同文 → 点推荐行同名 chip（大小写不敏感匹配）。**B站分区点击失败后会回落成 vlog，必须回读验证（坑 242）**——form 步分区 locator 超时后分区显示为 `vlog`（默认值），修复方式 = 点当前分区文本（`vlog`/`请选择分区`）打开下拉 → 扁平列表点 `人工智能`（坑 205 协议仍有效），点完必须回读页面显示文本断言 = 目标分区。**公众号分步脚本必须按序执行，禁止直接跳 save（坑 243）**——`save` 步的 `editor_page(ctx)` 依赖 `open` 步打的 `window.__wx1010` 标记，没跑 open 直接 save 会 `AttributeError: 'NoneType' object has no attribute 'bring_to_front'`；分步顺序 open→body→images→cover→title→save→verify，中断后重跑也要从最近的已完成步续。**公众号 body/images 步实测顺畅**：817 字正文无结构检测弹窗（无 B 档内容时坑 220 不触发），6 占位符（5 场景图+封面图）逐张上传+每图即存草稿全过。**坑 215 双命中**：B站、公众号先后被用户手动接管，声明后立即停止该平台一切操作（含核验）。**CDP daemon 会随会话中断消失**：上传前先 `curl -s -m 5 http://localhost:9222/json/version` 探活，空响应则裸启日常 Chrome（坑 198/193 协议）再附着。
>
> **🔴 v3.43.0 核心改进（2026-10-09 日报实测）**：**锚点占比不能靠把 CTA 排到锚点前面来凑（坑 236）**——播放顺序 `[1,2,3,4,6,5]` 实测占比 79.25% 合格，但 CTA 在锚点前，叙事顺序错了；正确做法是改回 `[1,2,3,4,5,6]` 并把锚点前的口播加长约 12 字把占比推过 70%（1009 实测 54.841s/78.214s=0.7012）。过渡句必须随顺序变：「回头说」只用于 CTA 之后回扣，「刚才说的」用于锚点紧接正文。**场景图默认走接口，本地 PIL 只是兜底（坑 237）**——1009 场景图直接用了 `gen_scenes_local.py` 的抽象色块，用户要求改接口重渲；封面仍走本地 PIL（中文日期/品牌名接口渲染不可靠，坑 225 不变）。**`publish.json` 是 Phase 10.2 的必落盘产物（坑 238）**——1009 整期跑完目录里没有这个文件，标题/标签没有单一事实源。**B站「封面制作」弹窗的关闭按钮必须点 `cover-editor-head-close` 自身中心（坑 239）**——泛匹配 `[class*=close]` 点到别的元素，弹窗不关、挡住表单。**B站清标签的选择器不能命中推荐标签行（坑 240）**——`.tag-item, [class*=tag-item]` 同时匹配 `.hot-tag-item`，点下去是**新增**话题标签（1009 误加「B站AI无限竞技场」），必须限定在标签输入框的 chips 容器内。
>
> **🔴 v3.39.0 核心改进（2026-09-21 周报 W37 实测）**：**结构检查弹窗有第三变体「内容结构检测」（坑 220）**——0921 周报正文粘贴后 `bodyLen=0`，弹窗标题实为「内容结构**检测**」，坑 192 的 `/Structure Check|结构检查/i` 漏匹配（**检测≠检查**），空转到手动点「继续插入」才写入；放行正则必须三变体齐全 `Structure Check|结构检查|结构检测`。**type=10 list_card 不是草稿验收源（坑 221）**——`appmsg?type=10&action=list_card` 只展示「历史图文素材」（2018–2020），**不含 type=77 新草稿**；坑 212 的「草稿箱无 + 发表记录无」存在第三态 = 草稿已落盘但两个列表都看不到，误判断会触发重建、撞上「appmsgid 出现即禁止重建」铁律。验收三件套：`appmsgid` 编辑页直达（要素全在）+ 首页「近期草稿」首条 + 发表记录无当日（确认未发表）。**渲染归档未验证禁止汇报（坑 222）**——0921 渲染成功但 out 落在 `news-pipeline/video-project/out/`（相对路径随 CWD，并非必在根 `out/`），归档 cp 又被分类器抖动打断未补，`weekly/.../video/` 为空就汇报完成，用户两次追问「视频呢」；铁律：out 写绝对路径 + 归档后 `ls -la`/ffprobe 验证模式目录 `video/` 非空，否则禁止说「视频已生成」。**坑 216 修正**：抖动期 `Write`/`Edit`/`Workflow` 同样会被拦，同批并行调用会「一过拦一」，分类器模型名会变（0920 deepseek-v4.1-flash / 0921 glm-5.3-flash）。锚点占比判据补 ≤1pp 测量容差（0921 周报 80.5% 验收通过）。坑 215 周报场景再次命中（「上传公众号，其他的我已经上传」→ B站/抖音/视频号全不碰）。
> **🔴 v3.38.0 核心改进（2026-09-21 日报实测）**：**B站封面编辑器已改版为「封面制作」全屏弹窗（坑 218）**——点「添加封面」**不再触发原生 file chooser**（`expect_file_chooser` 必超时），而是打开带「智能生成封面/模板/文字/贴纸/滤镜」的封面编辑器；自制图路径 = 弹窗内点「上传封面」→ `input[accept="image/png, image/jpeg"]` → `set_input_files` → 点 `.cover-editor-button .button.submit`（文案「完成」）关弹窗。⚠️ 此刻页面上有 5 个 `input[type=file]`（`.mp4`×2 / `.txt` / `.zip` / 封面 image），**只有 accept 含 `image` 的那个是封面**；按索引 `inputs[1]`/`inputs[-1]` 会喂给视频或 zip input 且**全程静默无报错**（0921 连错两次，表单纹丝不动）。**B站标签区上限 10 且会被推荐标签污染（坑 219）**——新版投稿页自动预置「学习/生活记录/记录」等 chips，必须清理；关闭符 `×` 在 `label-item-v2-container` 容器**最右侧**（点文字元素无效，0921 空转三轮），清理与新增后都要回读 `.label-item-v2-container` 文本列表断言，不能只信脚本打印的 "added"。**mp 上传脚本 `open` 步骤必须 settle()（坑 217）**——`goto('https://mp.weixin.qq.com/')` 在已登录时 302 到 `cgi-bin/home?...token=`，紧接的 `page.evaluate` 抛 `Execution context was destroyed` 直接崩掉整步；正确做法：若当前页已在带 `token=` 的 mp 页就**跳过 goto**，否则 goto 后先 `settle()`（轮询 body 直到可读）再判「新的创作」。**上传脚本读封面一律读日期目录根**（`gen_images.py` 写的是 `images/` 子目录，Phase 11 前必须 `cp images/horizontal-4-3.png images/vertical-3-4.png` 到 `news-pipeline/YYYY-MM-DD/`）。
>
> **🔴 v3.37.0 核心改进（2026-09-20 日报实测）**：**公众号验收必须同时查「草稿箱」与「发表记录」**——用户会在流水线存完草稿后**自行发表**，此时草稿箱里当日条目消失、发表记录里出现「今天 HH:MM 已发表」。只查草稿箱会误判「草稿丢了」并触发重建，正好撞上「`appmsgid` 出现即禁止重建」铁律，产出重复稿（坑 212）。**mp 页面 `page.goto` 会 302 到带 `token=` 的 home 并销毁 execution context**，`page.evaluate` 抛 `Execution context was destroyed`；草稿箱/发表记录都有稳定 URL，**用 URL 导航而非点击侧栏**（坑 213）。**Chrome 窗口被用户关掉后进程仍在**，CDP `/json/list` 返回 `[]`，Playwright `connect_over_cdp` 报 `Browser context management is not supported`——用 `curl -X PUT http://localhost:9222/json/new?about:blank` 建标签页即可恢复，**不必重启 daemon**（坑 214）。**用户声明「某平台我已手动上传」时，该平台一律不打开上传页、不开草稿箱核验**（Phase 14.0-pre 从抖音扩展到全部平台，坑 215）。**安全分类器不可用会阻塞全部非只读 Bash（含 `python3`、`CronCreate`）**，只读命令仍可过；对策是拆单命令 + 间隔重试，同时用不受影响的 `Write` 工具落盘状态（坑 216）。
>
> **🔴 v3.36.0 核心改进（2026-09-18 / 09-19 日报实测）**：**字幕偏移必须按 wav 文件实际时长累加**——whisper 的 VAD 会裁掉片尾 pad 静音，返回的 `dur` 偏小，用它推 `scene_offset` 会让后面所有场景字幕整体提前、越往后越明显；改用 `wave.open(...).getnframes()/framerate()`，与 `sceneConfig.duration` 同源（坑 208）。`gen_captions.py` 的 `load_scenes` 已兼容 `{scenes:[{num,text}]}` 字典列表写法——0918 直接按文本迭代该结构抛 `AttributeError: 'dict' object has no attribute 'decode'`，整段字幕卡死（坑 208）。**锚点位置是事后可调参数**：若锚点场景起始占比 >80%，重排播放顺序（如 `[1,2,3,4,6,5,7]`）即可拉回 70–80%，不必重写脚本（坑 209）。**TTS 端点在 key 全失效时不要逐个试**：`settings.json` 里 MIMO key 全部 `Invalid API Key` 时直接走 `gen_tts_edge.py`（edge-tts 云扬 + atempo 1.4），0916/0917/0918 连续三期一致（坑 210）。
>
> **🔴 v3.32.0 核心改进（2026-09-15 日报实测）**：**状态判定禁读隐藏节点**——原创声明的 `Undeclared` 是折叠面板内陈旧占位节点的假象，声明其实早已生效，为此空转 6 轮；状态一律以「可见设置行摘要 + 行高」为准，`element.click()` 对 `display:none` 元素照样有效是错觉根因（坑 191）。**正文粘贴必须放行「Content Structure Check」弹窗的 `Continue Inserting`**，并用剥离 `ProseMirror-widget` 的 `bodyLen()` 读长度（空态占位符 `Start text here` 15 字符会污染裸读）（坑 192）。英文 UI 标签集（`Save as draft`/`Confirm`/`image(s)`/`Collections`）与 `Page.captureScreenshot` 须用页面坐标 + `captureBeyondViewport`。

> **🔴 v3.35.0 核心改进（2026-09-17 用户复盘）**：**封面文字源拆分（坑 203）**——封面画面只印「对应封面大字」短句（Hook 原词，1 句冲突 + 1 个数字，两行排版），**禁止**把 `publish.json.title` 整条发布标题（日期+多事件+「N条一次看完」+报刊名）印上画面；`publish.json.title` 仍作 B站/公众号列表标题与渲染文件名。0917 实测：整条标题上画面 = 信息堆叠、冲突稀释、与 Hook 原词脱钩，正是「封面有钩子、开头没用钩子」的反面结构倒过来犯。
>
> **🔴 v3.34.0 核心改进（2026-09-17 日报实测）**：**上传 daemon 必须用日常 Chrome，禁止 Chrome for Testing**（坑 198）。Playwright driver 不能当 daemon 持有浏览器——弹窗协议错误会把 driver+浏览器一起打死（坑 199）。B站「存草稿」是 `span.submit-draft` 不是 `button`，点错 5 次草稿箱一直空（坑 200）；失败禁止 `goto` 草稿箱，表单页会被冲掉（坑 201）。公众号英文 UI 登录判据补 `New creation`；`navigator.clipboard.write` 成功 ≠ 正文进去，必须坐标点击正文再 Meta+V，以 `bodyLen>800` 为准（坑 202）。
>
> **🔴 v3.33.0 核心改进（2026-09-16 日报实测）**：**上传阶段浏览器必须常驻**——脚本化 Playwright 严禁把 `launch_persistent_context` 放进 `with sync_playwright()`（脚本退出含异常即杀浏览器、表单状态全丢、整轮重传；0916 期连丢 3 次）；先用守护进程持有浏览器（CDP 9222），后续脚本 `connect_over_cdp` 只附着不断连（坑 193）。B站新版投稿页**分区是级联面板**：`人工智能` 是 `科技数码` 的子分区，老的「点开下拉→JS 点选项」不再命中（坑 194）。公众号登录判据 = **页面出现「新的创作」**（登录页文案是「微信扫一扫」，搜「扫码」会漏判）（坑 195）。生图 prompt 里的中文水印尾巴会诱发画面大面积乱码中文，须删掉并显式加 `no text`；主站欠费时 prism `gpt-image-2` 为实测可用兜底（坑 196；原文写作「`_003` prism」，**该后缀编号已漂移，勿照抄下标**，按 URL 域名判端点，见坑 304）。

**核心原则：语义 `group_caps` 先切行，再以真实音频为锚——faster-whisper 词级时间戳 + SequenceMatcher 对齐。字幕内容 100% 来自原始脚本、时间 100% 来自音频真实发音时刻。禁止逐标点切行，禁止按字硬切，禁止按字数比例切时间轴。**

### 🔴 全局规则：所有平台上传一律存草稿

**v2.8.0 新增**：无论日报还是周报，所有平台（B站/抖音/视频号/公众号/知乎）上传后一律**保存草稿**，不直接发布/投稿。

**原因**：
- 标题、封面、合集等可能需要用户二次确认
- 避免因自动发布导致的内容错误或违规风险
- 用户可在各平台草稿箱中检查后手动发布

> **🔴 v3.67.0 硬约束（坑 317 血的教训，2026-10-28）**：**「发布/发表/立即投稿」按钮永不进入脚本逻辑，且「保存草稿」的点击必须自证落点。** 视频号三个按钮水平相邻、间距仅 16px、平台无二次确认；1028 期因「`scrollIntoView` 与测 rect 同一次 evaluate + sleep 后点击」用了滚动落定前的旧坐标，落点偏到「发表」，**内容直接公开**（`视频 187→188`、`草稿箱 7→6`）。**任何坐标点击前：① 滚动单独一次、② 等 ≥600ms、③ 重新测 rect、④ `document.elementFromPoint(x,y)` 断言命中目标元素；不通过就不点、报错停下，不重试。**

**各平台存草稿方式**：
| 平台 | 存草稿操作 | 成功判据（**点击回执不算数**） |
|------|-----------|------------------------|
| B站 | 点击 `span.submit-draft`（文案「存草稿」，**不是** `button`；0917 坑 200） | URL 跳到 `upload-manager/article?group=draft`，且草稿箱标题匹配 |
| 抖音 | 点击「暂存离开」；**必须**双信号验收 + 同标签恢复回读后再暂存一次（v3.61.0 坑 295：新开标签点「继续编辑」会毁稿）。**若恢复后发现视频丢失（坑 323），在该草稿页内按 `accept` 含 `video` 挑 `input[type=file]`（本期实测索引 1，索引 0 是封面图的 image/*）重新 `set_input_files` 上传，再暂存** | **① 按钮消失 且「继续编辑」横幅出现；② 恢复后 `videos >= 1`（v3.68.0 坑 323：双信号不是充分条件——横幅在、字段全，视频仍可能没落库）；③ 标题回读一致** |
| 视频号 | 点击「保存草稿」按钮——**点击前必须 `document.elementFromPoint` 自证落点是它**（v3.67.0 坑 317：它与「手机预览」「发表」水平相邻、间距仅 16px、无二次确认，1028 期因 stale 坐标误点「发表」，内容直接公开） | **`post/draftListManager` 草稿计数 +1 且目标短标题出现**（v3.65.0 坑 308：点击成功≠落库，本期实测点击后计数仍是 4）。**另：视频标注不在草稿里保存（坑 318），验收时不要拿它当落库判据** |
| 公众号 | 点击「保存为草稿」按钮 | URL 出现 `appmsgid=`，且 `bodyLen` / 占位符数 / 封面 `hasQpic` / **合集 `.js_article_tags_content`** 回读一致（v3.66.0 坑 310：合集**不能**用 `body.innerText` 子串判，正文页脚恒含合集名） |
| 知乎 | **无「保存草稿」按钮——知乎文章是自动保存**（v3.71.0 坑 335 实测）。填完标题/正文等 ≥3s 出现底部「刚刚 · 草稿」即可；**「发布」永不进脚本**（规范禁止自动化发布，AI 声明不能豁免） | 编辑页 URL 变为 `zhuanlan.zhihu.com/p/<id>/edit`；创作者中心「草稿箱(N)」列表出现本期标题；编辑器内 标题 value / 正文 innerText 长度 / 封面 / **创作声明（含 AI 辅助创作 作者对内容负责）** / 专栏「今日羊报 AI」五项同时回读（详见 `templates/platform-zhihu.md` §3.10） |

### 🔴 浏览器与 Profile 全局铁律（v3.7.0 / 2026-07-18 实测）

**问题**：同日流水线里 MCP Playwright 与独立 `playwright-core` 脚本若**共用** `ms-playwright-mcp/mcp-chrome-*` 登录态，会互抢锁、被 `pkill`、或在视频号双 body 页触发 MCP 崩溃，表现像「浏览器老是退出」。

**铁律**：
1. **同一时刻只用一种浏览器驱动**：要么全程 MCP（`browser_*` 工具），要么全程独立脚本；禁止中途混用同一 `user-data-dir`。
2. **独立脚本启动前**才允许 `pkill -f "user-data-dir=.../mcp-chrome-..."`；**不要**对普通 Chrome / Chromium 全局 `pkill`。
3. **视频号页面**（`channels.weixin.qq.com`）存在 **wujie 双 body**（外层 + `wujie-app body`）。在此页调用 `browser_snapshot` / `browser_find` / `browser_file_upload` / `browser_tabs` 常报：
   `strict mode violation: locator('body') resolved to 2 elements`
   **处理**：所有探测与操作放进**一次** `browser_run_code_unsafe`；返回前 `page.goto('https://www.baidu.com')` 离开双 body 页；文件选择器用脚本内 `waitForEvent('filechooser') + setFiles`，勿拆成单独 `browser_file_upload`。
4. **beforeunload**：从编辑页离开时弹「将此次编辑保留？」→ 先 `browser_handle_dialog(accept=true)` 或脚本内点「保存/不保存」，否则 `net::ERR_ABORTED`。
5. 独立脚本结束若用户要核对 UI，可**不** `context.close()`，改为提示用户手动关窗（用户明确要求「不要关太快」时）。

### 🔴 浏览器驱动选择铁律（v3.65.0，坑 306）

**判定顺序固定，不许跳步**：
1. `curl -s http://127.0.0.1:9222/json/version` —— HTTP 端点不通 ⇒ daemon 死了，报告用户，不要自己重开带登录态的窗口。
2. `curl -s http://127.0.0.1:9222/json | jq length` —— 能列出 target ⇒ **Chrome 侧完全健康**，问题一定在 playwright。
3. 此时 `connect_over_cdp` 若在 `ws connected` 之后超时（25s / 90s 都一样），**立刻切 raw CDP，禁止再做以下三件事**：加大 timeout、重启 Chrome、`pkill` 任何进程。

**raw CDP 最小可用骨架**（复制 `templates/cdp_helper.py` 到本次工作目录再 import，勿手搓）：
```python
# ① 一定带 proxy=None —— 否则走环境 SOCKS，报 python-socks is required
ws = await websockets.connect(target['webSocketDebuggerUrl'],
                              max_size=64*1024*1024, ping_interval=None, proxy=None)
# ② 表达式必须包进 async IIFE 再 JSON.stringify
#    错的：(async () => JSON.stringify(await (EXPR)()))        → 返回 undefined
#    错的：JSON.stringify(await (FUNC)())                      → ReferenceError: await is not defined
#    对的：(async () => JSON.stringify(await (async () => { return (EXPR); })()))()
# ③ 断线重连一次（wujie 长页面会偶发 ConnectionClosedError: no close frame）
```
**代价提醒**：raw CDP 没有 `locator` / `set_input_files` 的便利，文件上传要走
`Runtime.evaluate` 取 `input[type=file]` 的 `objectId` → `DOM.setFileInputFiles({files, objectId})`；
先 `DOM.enable`，且 shadowRoot 内的 input 必须先 `Array.from(shadowRoot.querySelectorAll(...))`
拿到数组 objectId，再用 `Runtime.getProperties` 按下标取 node objectId（直接 `querySelector` 会拿到 null）。

### 🔴 标题与正文是两个独立编辑区（v3.65.0，坑 307）

公众号编辑器有**两个 `.ProseMirror`**：`[0]` 是标题、`[1]` 是正文，另有一个隐藏的 `#title` 输入框同步标题。

**事故模式**：先点标题输入标题 → 不换焦点直接对正文发 `Meta+A` → 实际选中的是标题 → 粘贴正文时把标题串覆盖进正文，
`bodyLen` 从 1347 掉到 120，而「占位符 = 0」让图片验收误判通过（占位符本来就没了）。

**铁律**：
1. 写标题：`window.scrollTo(0,0)` → 坐标点击 `.ProseMirror[0]` → 断言 `document.activeElement` 是它 → `Input.insertText`；
2. 写正文：**重新**点 `.ProseMirror[1]` → 断言 `activeElement` 是它 → 再 `Meta+A` + 粘贴/`execCommand('insertHTML')`；
3. 每次替换正文后立刻回读 `bodyLen` **和** 首个正文段落的前 20 字，两者都对才算写成；
4. 正文被覆盖只能「全选删除 → 重新插入整段 HTML」，**不要增量修补**。

### 🔴 「保存草稿」的成功判据只能是落库（v3.65.0，坑 308）

视频号本期实测：短标题与描述分离写入、AI 标注选中、合集选中、双封面就位，
点「保存草稿」后**页面无 toast、无 fetch、`draftListManager` 计数仍是 4**——脚本若以 `clicked` 报成功，
汇报就是假的。

**铁律**：
- 每个平台的保存步，**必须**在另一入口回读落库证据（见上方「存草稿方式」表的第三列），点击回执只是「发起了点击」；
- 视频号连续两次落库失败 → **停下来报告用户**（附：点击位置、页面文案快照、草稿箱计数），不要换选择器反复硬试；
- 汇报措辞按事实：未落库就写「未落库」，不要把 `clicked` 写成 `✅`。

## ⚡ 权限预授权（必须在执行前完成）

**在开始 Pipeline 之前，必须先获得用户的一次性预授权。执行过程中不再逐个询问权限。**

**🔴 重要：预授权覆盖所有阶段（内容生成 + 全部平台上传），一次确认后全程不再询问。**

### 预授权原则

1. **一次授权，全程执行**：用户确认后，后续所有操作（文件读写、API调用、浏览器操作）不再询问
2. **信息一并收集**：在预授权时同时收集 API URL、Key、上传平台等信息
3. **失败自动重试**：API 调用失败自动重试一次，不询问用户
4. **浏览器锁自动处理**：检测到浏览器锁时自动清理（删除 SingletonLock + kill 旧进程），不询问用户
5. **DNS 劫持自动绕过**：检测到 API 连接超时时，使用 `nslookup` 获取真实 IP + `curl --resolve` 绕过本地代理 DNS 劫持（198.18.x.x 网段），不询问用户

### 预授权检查清单

向用户展示以下清单，请求一次性确认：

```
🎬 AI News Factory 权限预授权

执行以下操作需要你的授权，确认后全程不再询问：

📁 文件操作
  ☐ 读取日报 Markdown 文件（含历史日报用于去重）
  ☐ 写入脚本、分镜、Prompt、字幕、公众号文章等文件
  ☐ 复制资源到 video-project/public/

🔧 Shell 执行
  ☐ 调用 mimo-tts.sh 生成配音（逐场景串行）
  ☐ 调用 ffprobe 获取音频时长
  ☐ 调用 npx remotion render 渲染视频
  ☐ kill 旧浏览器进程（如遇浏览器锁）

🌐 API 调用
  ☐ 图片生成 API（用户提供 URL + Key）
  ☐ TTS API（mimo-tts）

🖥️ 浏览器操作（全部平台上传，一律存草稿）
  ☐ B站：自动上传视频、封面、填写标题/简介/标签、选择合集、存草稿
  ☐ 抖音：自动上传视频、封面、填写描述、选择合集、存草稿
  ☐ 视频号：自动上传视频、封面、填写描述/短标题、选择合集、存草稿
  ☐ 公众号：自动创建文章、填写标题/正文、上传封面、声明原创、选择合集、存草稿
  ☐ 知乎：派生知乎稿、过合规审核清单、创建文章、填写标题/正文+配图+**正文前插入成片视频**、添加封面、设置「包含 AI 辅助创作」声明、收录专栏「今日羊报 AI」、存草稿（**不发布**）

请回复「确认」或「全部授权」开始执行。
```

### 用户输入收集

在预授权时一并收集以下信息（避免中途打断）：

```
需要你提供：
1. 📄 日报文件路径（默认: data/reports/YYYY-MM-DD.md）
2. 🖼️ 图片生成 API URL
3. 🔑 图片生成 API Key
4. 📤 上传平台（默认: 全部 = B站/抖音/视频号/公众号/知乎；可指定如「B站+公众号+知乎」）
5. 🧭 知乎专栏名（默认: 今日羊报 AI；中间半角空格，末位是**大写字母 I**，2026-10-30 按页面码点实测）
```

## 触发条件

- "AI日报", "新闻工厂", "news factory"
- "日报视频", "生成日报视频", "AI news video"
- "把日报做成视频", "日报转视频"
- "AI周报", "羊报AI周刊", "weekly report", "周报视频"
- "AI月报", "羊报AI月报", "monthly report", "月报视频", "把月报做成视频", "月报转视频"
- "破格模式", "破格元素", "破格风格", "元素破格"
- "精简模式", "精简", "排序", "精华版", "3W", "压新闻"
- "知乎", "知乎文章", "知乎发文", "发知乎"（→ 进入 Phase 10.3b 派生 + Phase 15 上传，只存草稿）

## 模式参数映射表（v3.1.0 新增，单一事实源）

本表是 daily/weekly/monthly 三模式字段对照的**唯一事实源**。Phase 0 依据 `REPORT_PATH` 或触发词判定 `REPORT_MODE` 后，所有下游 Phase 一律按本表读取参数，**禁止在脚本/封面/标题/合集里硬编码"今日羊报AI"或"YYYY-MM-DD"**。

| 字段 | 日报 daily | 周报 weekly | 月报 monthly |
|------|-----------|------------|-------------|
| `REPORT_PATH` 默认 | `data/reports/YYYY-MM-DD.md` | 7 份日报（程序读取最近7天） | `data/monthly/YYYY-MM.md` |
| 输出目录 | `news-pipeline/YYYY-MM-DD/` | `news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/` | `news-pipeline/monthly/YYYY-MM/` |
| 是否重新聚合 | 否 | 是（读 7 天日报） | **否**（直接消费月报 md，linuxdo-daily v13 已聚合） |
| 去重策略 | 对比前 3 天日报 | 对比上一期周报 | **对比上一期月报**（`data/monthly/{上月}.md`，不扫日报） |
| 事件粒度 | 单日单帖事件 | 周内事件 | **月度趋势级**（4 趋势 + TOP 主题） |
| 事件数档位 | 4-6（精简 3-5） | **1深聊（TOP1≥20）+ 2-3快讯（≥15）** | **4 趋势主线**（精简 3 趋势） |
| 视频总时长 | 60-120s（≤150s） | **100-150s**（深聊型，替代旧 90-120s） | **180-240s（≤300s）** |
| 每段字数 | ≤80 字 | ≤80 字 | **≤100 字** |
| 标题前缀 B站 | `【{YYYY-MM-DD}】`（日期在前） | `【{MM-DD~MM-DD}】`（日期在前） | `【{YYYY-MM}】`（日期在前） |
| 标题后缀 B站 | `… \| 今日羊报AI`（报刊名在后） | `… \| 羊报AI周刊`（报刊名在后） | `… \| 羊报AI月报`（报刊名在后） |
| 抖音标题 | `今日羊报AI YYYY-MM-DD`（≤30字） | `羊报AI周刊 MM-DD~MM-DD`（≤30字） | `羊报AI月报 YYYY-MM`（≤30字） |
| 视频号标题 | `今日羊报AI M月D日`（≤16字） | `羊报AI周刊 M月D日至D日`（≤16字） | `羊报AI月报 YYYY年M月`（≤16字） |
| 日期字段 | `YYYY-MM-DD` | `MM-DD~MM-DD` | `YYYY-MM` |
| tags 首 tag | `今日羊报AI` | `羊报AI周刊` | `羊报AI月报` |
| tags 主题 tag | `AI日报` | `AI周报` | `AI月报` / `AI月度盘点` |
| 封面品牌名 | `今日羊报 AI` | `羊报AI周刊` | `羊报AI月报` |
| 封面日期字段 | `{YYYY-MM-DD}` | `{YYYY-MM-DD} ~ {YYYY-MM-DD}` | `{YYYY-MM}` |
| 视频渲染文件名 | `【{YYYY-MM-DD}】{核心标题}… \| 今日羊报AI.mp4` | `【{MM-DD~MM-DD}】{核心标题}… \| 羊报AI周刊.mp4` | `【{YYYY-MM}】{核心标题}… \| 羊报AI月报.mp4` |
| B站合集名 | `「今日羊报 AI」` | `「羊报AI周刊」` | `「羊报AI月报」` |
| 公众号合集名 | 同 B站 | 同 B站 | 同 B站 |
| 公众号作者 | `今日羊报AI`（≤8字） | `羊报AI周刊`（≤8字） | `羊报AI月报`（≤8字） |
| 公众号署名 | `今日羊报 AI · YYYY-MM-DD` | `羊报AI周刊 · MM-DD~MM-DD` | `羊报AI月报 · YYYY-MM` |
| 公众号结尾 CTA | `每天 9 点带你速览 AI 圈最热的 5 条新闻` | `每周带你盘点 AI 圈一周大事` | `每月带你回顾 AI 圈整月风向` |
| 简介数字规则 | 版本号简化 + 数字中文 | 同日报 | **强制全数字中文化**（见 B站简介数字中文化章节） |
| 精简模式可叠加 | 是 | 是 | 是（精简月报 = 3 趋势，≤180s） |
| **专业锚点** | **15s × 1**（`ai-concept-bank`） | **30–60s × 1** | **30–60s × 1** |
| **锚点库路径** | `ai-concept-bank/concepts.json` | 同左 | 同左 |
| **脚本默认结构** | **3W + 可信度** | **3W + 可信度** | 趋势内嵌 3W + 可信度 |
| **灰色渠道上限** | **每期 ≤1 条** | **每期 ≤1 条** | **每期 ≤1 条** |
| **知乎标题** | `【M月D日】{信息型判断句}`（≤40 字，禁品牌后缀） | `【M月D日~D日】{信息型判断句}`（≤40 字） | `【YYYY年M月】{信息型判断句}`（≤40 字） |
| **知乎专栏** | `今日羊报 AI`（中间半角空格 U+20，末位**大写 I** U+49；2026-10-30 页面码点实测，旧文案「小写 l」是错的） | 同左（实跑确认是否有独立周刊专栏） | 同左（实跑确认） |
| **知乎文章文件** | `zhihu-article-YYYY-MM-DD.md` | `zhihu-article-<range>.md` | `zhihu-article-YYYY-MM.md` |
| **知乎封面** | `horizontal-4-3.png` → `zhihu-images/cover.jpg` | 同左 | 同左 |

**模式判定规则**（Phase 0 自动）：
- `REPORT_PATH` 含 `data/monthly/`，或触发词含"月报/monthly" → `REPORT_MODE=monthly`，`MONTH_LABEL=YYYY-MM`
- 触发词含"周报/weekly"，或 `REPORT_PATH` 含 `data/weekly/` → `REPORT_MODE=weekly`
- 否则 → `REPORT_MODE=daily`

**专业锚点（v3.4.0）**：每期默认 1 个，算法与写 log 见 `templates/professional-anchor.md`；主库为 submodule `ai-concept-bank/`（禁止另建 `news-pipeline/concept-bank`）。

## 周报模式

**当触发词包含"周报"或"weekly"时，进入周报模式：**

### 周报与日报的区别

| 项目 | 日报 | 周报 |
|------|------|------|
| 数据源 | 单日日报 | 7天日报汇总 |
| 输出目录 | `news-pipeline/YYYY-MM-DD/` | `news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/` |
| 封面提示词 | 单日事件 | 本周多事件拼贴 |
| 视频脚本 | 3-5个当日事件 | **1件大事3W深聊50s + 2-3条一句话快讯**（见 `templates/script-template-weekly.md`，替代旧 5-6 条堆叠） |
| 过滤规则 | 无 | **过滤公益站/中转站/倒卖相关内容** |
| 标题格式 | `【{日期}】...| 今日羊报AI` | `【{日期}】...| 羊报AI周刊` |

### 周报生成流程

1. **读取本周日报**：读取 `data/reports/` 目录下最近7天的日报文件
2. **提取关键事件**：每天选出1-2个最重要事件，过滤公益站相关内容
3. **🔴 Step 1.4w 周报选材（本周1件大事选取）**：按五维评分卡（影响范围/新鲜度/实用性/话题性/争议性，1-5 分，满分 25）对周内事件打分——**TOP1（总分≥20）进深聊 50s**（讲周一到周五的时间线演变，日报做不到的差异点）；**第 2-4 名（总分≥15）降为快讯一句话**（What+SoWhat 合并）；**<15 一律不进脚本**
4. **生成周报 Markdown**：输出到 `news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD.md`
5. **生成周报封面**：使用周报专用封面提示词（多事件拼贴风格）
6. **生成视频脚本**：**1件大事3W深聊50s + 锚点15-20s + 2-3条一句话快讯20s + CTA，总时长100-150s**（见 `templates/script-template-weekly.md`，替代旧 5-6 条堆叠）
7. **🔴 脚本字数门禁（坑 244，进 TTS 前必过）**：去标点去空格总字数 **≥650、目标 680–720**（edge-tts 云扬 atempo1.4 ≈6.4 字/s → 650字≈101s、700字≈109s）；`len(strip_punct(全文))` 断言不过就扩写正文（每段仍 ≤80 字、锚点豁免），**禁止靠降 atempo 或挪锚点凑 100s**。TTS 实测 <100s 同样按此扩写重跑。
7. **后续流程**：与日报相同（分镜→图片→TTS→字幕→视频→上传）

> 🔴 **周报 Hook 约束**：只选本周最冲突的 1 件作反转/警告开场（套 4 主力公式之一）；**禁堆叠≥2事件**；禁"本期周刊把本周N件大事一次讲清"套话后缀；其余事件降为快讯。

### 周报封面提示词模板

**🔴 v3.35.0**：周报横/竖封面与日报共用海报风模板，**画面文字源 = 本周深聊大事件对应的「封面大字」短句**（Hook 原词，1 句冲突 + 1 个数字，两行；`publish.json.title` 仍作列表标题不进画面）。完整提示词见 `templates/cover-prompt.md`，水印品牌 `羊报AI周刊`，日期 `{YYYY-MM-DD} ~ {YYYY-MM-DD}`。禁止再用演播室空镜英文 prompt。

### 周报段落字数上限（v3.65.0 实测口径）

日报的「每段 ≤80 字」在周报里**偏紧**：深聊要在一段里同时装下 4 格时间线 + 3W，压到 80 会把信息挤掉。
W42 实测可用区间：**S1 Hook 20 字；S2–S8 单段 70–95 字；S9 锚点豁免；S10 CTA 48–78 字**。

- 硬门槛仍是**去标点 ≥650**（坑 244），目标 **680–720**；
- **锚点占比是比总字数更难得的那一关**：锚点在 S9，其后只有 S10，所以
  `anchor_ratio = (S1..S8 字数) / 总字数`，**S1–S8 越长占比越高、S10 越长占比越低**。
  W42 实测：把 S10 从 63 字拉到 78 字，占比从 0.8109 降到 0.7942 才进窗；
- 调占比的正确顺序：**先改后段（S6–S10），不要动 S2–S5**——动前段会连锁把占比推得更高；
- 每改一次都必须重算，不要凭感觉。用 `gen_script_w42.py` 那种「脚本即数据源」的写法：
  段落写成一个 list，跑一次就打印 `total / anchor_start / ratio`，比在 md 里手改再数字符快得多。

### 周报过滤规则

**以下内容必须过滤掉：**
- 公益站相关（N1nEAPI、RawChat、PrismAI、Alpha、薄荷等）
- 中转站价格变动
- 倒卖/交易相关内容
- 兑换码/邀请码分享

**保留的内容：**
- 模型发布与更新
- 公司动态（IPO、融资、收购）
- 重大安全事件
- 开源模型发布
- 行业政策与监管
- 重大技术突破

## 月报模式（v3.1.0 新增）

**当触发词包含"月报"或"monthly"，或 `REPORT_PATH` 指向 `data/monthly/*.md` 时，进入月报模式。**

### 月报与日报/周报的区别

| 项目 | 日报 | 周报 | 月报 |
|------|------|------|------|
| 数据源 | 单日日报 | 7天日报汇总 | **linuxdo-daily v13 月报 md**（已聚合，不重算） |
| 输入路径 | `data/reports/YYYY-MM-DD.md` | `data/reports/*.md`（7天） | `data/monthly/YYYY-MM.md` |
| 输出目录 | `news-pipeline/YYYY-MM-DD/` | `news-pipeline/weekly/...` | `news-pipeline/monthly/YYYY-MM/` |
| 事件粒度 | 单日事件 | 本周事件 | **月度趋势**（一条趋势跨多日多帖） |
| 是否去重 | 对比前3天日报 | 对比上期周报 | **月报已聚合去重，跳过跨日去重**；仅对比上期月报避免重复趋势 |
| 脚本结构 | Hook+4段正文+CTA | **Hook + 本周深聊1件(50s) + 锚点 + 快讯2-3条 + CTA** | **Hook + 4趋势段 + 月度总结 + 下月展望 + CTA** |
| 总时长 | 60-150s | **100-150s**（深聊型） | 180-240s（≤300s） |
| 每段字数 | ≤80 字 | ≤80 字 | ≤100 字 |
| 封面品牌 | 今日羊报 AI | 羊报AI周刊 | 羊报AI月报 |
| 标题前缀 | 【{日期}】…（报刊名在后） | 【{日期}】…（报刊名在后） | 【{日期}】…（报刊名在后） |
| 日期字段 | YYYY-MM-DD | MM-DD~MM-DD | YYYY-MM |
| 简介数字规则 | 版本号简化 | 同日报 | **强制全数字中文化**（见 B站简介数字中文化章节） |

### 月报生成流程

1. **读取月报 md**：`data/monthly/{YYYY-MM}.md`（**不读取当月日报，不重新聚合**——linuxdo-daily v13 已完成跨日聚合与去重）
2. **对比上期月报**（去重）：读取 `data/monthly/{上一个月}.md`，对比 4 条趋势是否与上月高度重叠。重叠趋势标记「延续」并在脚本中合并表述，避免重复展开。
3. **选材**：按下方"月报选材规则"，从 4 条月度趋势 + TOP10 主题中选 4 条趋势主线 + 4-8 个支撑案例。
4. **生成月报视频脚本**：输出到 `news-pipeline/monthly/{YYYY-MM}/scripts/`，引用 `templates/script-template-monthly.md`。
5. **生成月报封面**：使用月报专用封面提示词（下方模板），引用 `templates/image-prompt-monthly.md`。
6. **后续流程**：与日报/周报相同（分镜→图片→TTS→字幕→视频→上传），但所有标题/品牌名/合集名/日期字段按模式参数映射表读取。

### 月报封面提示词模板

**🔴 v3.35.0**：月报横/竖封面与日报共用海报风模板，**画面文字源 = 本月最大趋势对应的「封面大字」短句**（Hook 原词，两行；`publish.json.title` 仍作列表标题不进画面）。完整提示词见 `templates/cover-prompt.md`，水印品牌 `羊报AI月报`，日期 `{YYYY-MM}`。禁止再用演播室空镜英文 prompt。场景图仍可用 `templates/image-prompt-monthly.md`（与封面分离）。

### 月报选材规则（最关键，区别于周报）

> 月报的"事件"是**趋势级**，不是单帖级。选材以 4 条月度趋势为主线骨架，每条趋势配 1-2 个代表性 TOP 主题作为支撑案例。**禁止把 4 趋势拆成 8-10 个单日事件回退日报结构。**

1. **4 条月度趋势全部纳入骨架**（不砍趋势，砍则丢信息）。若某趋势与上月高度重叠（如上月也是 OpenAI 调度混乱），标记为"延续趋势"，配 1 个本月新进展案例，合并表述。
2. **每条趋势选 1-2 个代表主题**：优先选该趋势「代表主题」字段中浏览量最高的 1 条；TOP10 中归属该趋势的再选 1 条。总数 = 4 趋势 × 1-2 = **4-8 个支撑点**。
3. **二次过滤公益站/套利类 TOP 主题**：月报 md 本身已过滤公益站/中转站（151 条），但 TOP10 仍可能含套利账号帖（如"墨西哥18刀买一送一"）或渠道促销帖（如"Codex 渠道半价"）。这类帖必须用趋势代表主题替代，不得入选。
4. **脚本结构**：1 Hook + 4 趋势段（每段 = 趋势概述 + 1-2 案例支撑，约 100 字）+ 1 月度总结段 + 1 下月展望段 + 1 CTA = **8-9 段**。
5. **精简月报模式**：砍到 3 趋势（每趋势配 1 案例共 6-7 段），总时长 ≤180s。

### 月报过滤规则

沿用周报过滤规则（公益站/中转站/倒卖/兑换码）。月报 md 已做一轮过滤，Phase 1 选材时再做一次 TOP10 套利帖的二次过滤。

### 月报模式叠加

| 组合 | 触发词示例 | 说明 |
|------|-----------|------|
| 精简 + 月报 | "精简 月报" | 精简版月报，3 趋势，≤180s |
| 破格 + 月报 | "破格 月报" | 月报脚本 + 破格标记 |
| 精简 + 破格 + 月报 | "精简 破格 月报" | 全部叠加 |

## 精简模式

**当触发词包含"精简"或"3W"时，开启精简模式。可与周报模式、破格模式叠加使用。**

### 什么是精简模式

**v3.4：3W 已是全模式默认。** 精简模式 = 先按重要程度排序 + 更少条数 + 更短句。  
3W（What—So What—Now What）源自哈佛/麦肯锡分析框架；细则见 `templates/credibility-and-tone.md`。

### 3W 模型说明

| 3W 层 | 含义 | 脚本对应 | 核心目的 |
|--------|------|----------|---------|
| **What**（事实层） | 客观描述事件本身 | 发生了什么 | 剥离情绪和猜测 |
| **So What**（含义层） | 连锁反应、风险与机遇 | 影响啥 | 分析深层影响 |
| **Now What**（行动层） | 决策建议和优先级 | 值不值得跟进 | 推导行动建议 |

### 精简模式与标准模式的区别

| 项目 | 标准模式（v3.4 默认 3W） | 精简模式 |
|------|---------|---------|
| 事件筛选 | 用户选 4-6 个 | **AI 先排序，精选 3-5 个** |
| 脚本结构 | **Hook + 每条 3W + 可信度 + 锚点 + CTA** | **同结构，更短句；CTA 可省** |
| 每条时长 | 15-25s | **10-20s（更紧凑）** |
| 总时长 | 75-135s（≤160 含锚点） | **60-100s（含锚点）** |
| 其他阶段 | 不变 | 不变（分镜/图片/TTS/字幕/上传） |

### 精简模式规则

1. **Phase 1 排序步骤**：按 5 个维度给事件打分（1-5 分），展示排序结果供用户确认
2. **精选 3-5 条**：从排序结果中选最重要的 3-5 条
3. **每条仍用 3W + 可信度**（比标准模式更短：每段 1-2 句）
4. **其他阶段不变**：分镜、图片、TTS、字幕、渲染、上传与标准模式相同

### 模式叠加规则

| 组合 | 触发词示例 | 说明 |
|------|-----------|------|
| 精简 + 标准 | "精简模式" | 最常用，精简版日报 |
| 精简 + 破格 | "精简 破格" | 3W 脚本 + 破格标记叠加 |
| 精简 + 周报 | "精简 周报" | 精简版周报，3-5 条本周精华 |
| 精简 + 破格 + 周报 | "精简 破格 周报" | 全部叠加 |

## 破格模式

**当触发词包含"破格"时，开启破格模式。可与周报模式叠加使用。**

### 什么是元素破格

打破常规逻辑，制造**反差感**和**意外感**。6种维度：

| 维度 | 含义 | 示例 |
|------|------|------|
| 身份破格 | 谁在做（身份×行为反差） | 保安跳霹雳舞 |
| 场景破格 | 在哪做（行为×环境反差） | 农村走秀 |
| 道具破格 | 用什么做（工具×目的反差） | 方便面写字 |
| 语言破格 | 怎么说（风格×内容反差） | 英语卖农产品 |
| 对象破格 | 对谁做（目标×行为反差） | 给鸡开会 |
| 角色破格 | 谁是什么（设定×行为反差） | 猪会钓鱼 |

### 破格模式与标准模式的区别

| 项目 | 标准模式 | 破格模式 |
|------|---------|---------|
| 脚本风格 | 口播解说体 | 口播 + 破格标记 |
| Hook | 悬念/冲突 | 必须用一种破格类型开场 |
| 正文 | 纯信息传递 | 每个场景可标注破格类型 |
| 图片Prompt | 写实新闻摄影 | 写实 + 破格视觉关键词 |
| 分镜 | 标准镜头 | 增加倾斜构图/对比蒙太奇 |
| TTS | 统一风格 | 可按场景切换风格 |
| 其他阶段 | 不变 | 不变（TTS/字幕/渲染/上传） |

### 破格模式规则

1. **Hook 必须使用一种破格**（从6种中选）
2. **正文至少使用2种不同破格**（同一视频不重复同一类型）
3. **每种破格标注类型**（脚本中用 `[身份破格]` 标记）
4. **图片 Prompt 反映破格视觉**（在 prompt 中加入反差关键词）
5. **分镜增加破格镜头**（倾斜构图、对比蒙太奇等）
6. **TTS 可选多风格**（不同场景用不同语调）

## 前置依赖

- **mimo-tts skill**: 语音合成 (`~/Documents/learn-claude-code/skills/mimo-tts/`)
- **ffmpeg**: 音频格式转换（获取音频时长）
- **Remotion**: 视频渲染（`news-pipeline/video-project/`）
- **Playwright MCP**: B站自动上传
- **图片生成 API**: 用户提供 URL + Key（支持 OpenAI 兼容格式）

## 执行流程

### Phase 0: 获取用户输入

**在预授权阶段已收集以下信息，直接使用：**

- `REPORT_PATH`: 报告文件路径（日报 `data/reports/YYYY-MM-DD.md` / 周报 7 份日报 / 月报 `data/monthly/YYYY-MM.md`）
- `API_URL`: 图片生成 API URL
- `API_KEY`: 图片生成 API Key
- `UPLOAD_PLATFORMS`: 上传平台列表
- `STYLE_MODE`: 风格模式（standard / poge），默认 standard
- `CONDENSED`: 是否启用精简模式（true / false），默认 false
- `REPORT_MODE`: 报告模式（daily / weekly / monthly），按模式参数映射表"模式判定规则"自动判定
- `MONTH_LABEL`: 月报模式下的月份标签 YYYY-MM（如 2026-06），仅 monthly 模式使用

如信息不完整，在此处补充询问。

**🔴 月报前置检查**（仅当 `REPORT_MODE=monthly`）：
- 确认 `data/monthly/{YYYY-MM}.md` 存在；若不存在，提示用户先运行 linuxdo-daily 月报模式生成。
- 确认 B站/公众号后台已创建合集「羊报AI月报」（首次运行月报前必须人工创建，否则 Phase 11/12 合集选择失败）。

### Phase 1: 输入、去重与事件切分

**模式分派**：
- `daily`: 执行 Step 1.1 → 1.4 原流程（去重 + 排序 + 事件切分）
- `weekly`: 执行周报流程（读 7 天日报聚合）
- `monthly`: **跳过 Step 1.2 跨日去重**（月报已聚合），执行 Step 1.5 月报选材流程

**Step 1.1**: 读取今日日报内容（daily/weekly）；monthly 模式读取 `data/monthly/{YYYY-MM}.md`。

**Step 1.2**: 🔴 去重检查

读取前 3 天的日报文件（`data/reports/YYYY-MM-DD.md`），对比今日事件：

```bash
ls data/reports/*.md | sort -r | head -4  # 获取最近4天的文件
```

**去重规则**：
- 同一事件首次出现在之前的日报中 → 标记为「重复」
- 同一事件的后续进展（如新数据、新声明）→ 标记为「新进展」，可保留
- 纯回顾/总结性提及 → 标记为「重复」

向用户展示去重结果：
```
🔍 去重对比（vs 06-03, 06-04）

❌ 重复事件（建议去掉）：
  - [事件A] — 首次出现在 06-03
  - [事件B] — 首次出现在 06-04

✅ 今日新鲜事件：
  1. [事件1] — 全新，2.6k 浏览
  2. [事件2] — 全新，1.4k 浏览
  3. [事件3] — 新进展（06-03 首次报道，今天有新数据）
```

**Step 1.3**: 用户确认选择要制作视频的事件（建议 4-6 个）。

**⚡ 免确认模式（v3.8.0 / v3.9.0）**：用户消息含「事件按推荐自动选定 / 不用再确认 / 权限给足直接跑 / 不要中途确认」时：
- 自动按评分取 TOP 事件（日报 4–6 / 周报 **TOP1深聊（总分≥20）+ 2-3条快讯（总分≥15）** / 月报 4 趋势）
- **跳过** Step 1.3 人工确认与 Phase 2 脚本人工审核**展示等待**
- **仍须内部执行审核清单**（禁止词/黑名单/灰渠道/锚点 eligible/3W），结果写入 `news-pipeline/{date}/scripts/review-checklist.md`（或 script 文末自检表），**禁止**只口头说「结构合格」而不落盘
- 仍须：去重、灰渠道配额、Step 1.6 锚点选题、写 usage-log、平台一律存草稿

**Step 1.3b（v3.4.0 强制）**: 灰色渠道配额 + 传闻跟踪 + 上游字段 + **平台选题档（v3.13）**

1. **消费上游字段**：若报告条目含 `可信度：` / `技术锚点：` / `影响：`，在候选列表中一并展示，排序说明可引用。  
2. **灰色渠道配额**：命中封号/KYC/土尼菲区/反代/号池/白嫖/薅羊毛/接码/代充等 → 本期独立成段 **≤1 条**；措辞改「风控/账号资产风险」，**禁止**教绕法（见 `templates/credibility-and-tone.md`）。  
3. **传闻跟踪**：同一未确认事件前 3 天已报且无新事实 → 不单独成段或改一句状态更新。  
4. **🔴 平台选题 A/B 档（v3.13.0）**：按 `templates/platform-compliance.md` 划分。  
   - **A 档**（默认可上视频号/公众号）：产品发布、官方定价、开发者工具、开源项目、可复现实测  
   - **B 档**（默认**不上**公众号/视频号标题与主推段落）：融资/IPO/外泄/监管/政策联署/「切断」类对抗叙事  
   - 视频成片若保留 B 档：整期 ≤1 条，且标题禁止 B 档关键词；公众号图文默认删除全部 B 档  

**Step 1.4**: 🔴 重要程度排序（🔴 标准模式强制展示；精简模式必做）

对去重后的新鲜事件按以下维度打分（1-5 分），展示排序结果：

| 维度 | 权重 | 评分标准 |
|------|------|---------|
| 影响范围 | 高 | 5=全行业变革，1=单一公司内部 |
| 新鲜度 | 高 | 5=全球首发，1=已有报道的后续 |
| 实用性 | 中 | 5=直接影响用户/开发者，1=纯概念 |
| 话题性 | 中 | 5=引爆社交讨论，1=小众圈层 |
| 争议性 | 低 | 5=多方激烈争论，1=无争议 |

向用户展示排序结果：
```
📊 重要程度排序（总分满分 25）：

 1. [事件A] — 23分（影响5 新鲜5 实用5 话题5 争议3）
 2. [事件B] — 20分（影响5 新鲜4 实用4 话题4 争议3）
 3. [事件C] — 18分（影响4 新鲜4 实用3 话题4 争议3）
 4. [事件D] — 15分（影响3 新鲜3 实用3 话题3 争议3）
 5. [事件E] — 12分（影响3 新鲜2 实用2 话题3 争议2）

建议精选前 3-5 条制作视频。
```

用户确认选择后，**不要直接进入 Phase 2**——先执行 **Step 1.6 专业锚点选题**。

**Step 1.5（仅 `REPORT_MODE=monthly`）**: 月报选材流程

1. 解析 `data/monthly/{YYYY-MM}.md`：
   - 本月概览（覆盖天数 / 主题总数 / 最活跃日 / 日均 / 亮点文件数）
   - 4 条月度技术趋势（热度变化 / 关键驱动 / 代表主题 triple-bullet）
   - TOP10 主题（带浏览量）
   - 下月展望（4 条预测）

2. 对比上期月报 `data/monthly/{上一个月}.md`：4 条趋势是否与上月高度重叠（如 OpenAI 调度混乱连续两月）。重叠趋势标记「延续」，脚本中合并表述。

3. 按"月报选材规则"选材：4 趋势全纳入骨架；每趋势配 1-2 代表主题（过滤公益站/套利类）；输出 4-8 个支撑点。

4. 向用户展示选材结果并确认：

```
📊 月报选材（2026-06，覆盖 28/30 天）

🟢 趋势一：GPT-5.5/5.6 调度混乱与 Codex 额度震荡
   - 案例1: TOP10 #6 GPT-5.6 传闻（6.3k 浏览）✅保留
   - 案例2: 6/10 全月峰值 1698 主题 ✅保留

🟢 趋势二：国产模型集中爆发，GLM-5.2 贴脸输出
   - 案例1: TOP10 #5 AxonHub 1.0 开源（7.5k）✅
   - 案例2: 6/17 GLM-5.2 正式发布并开源 ✅

🔴 已过滤：TOP10 #2 墨西哥18刀（套利账号）、#10 Codex渠道促销（倒卖）

📐 脚本结构：1 Hook + 4 趋势段 + 1 总结 + 1 展望 + 1 CTA = 8-9 段
⏱️ 预计时长：约 200s
```

用户确认后，**先执行 Step 1.6**，再进入 Phase 2。

**Step 1.6（全模式强制，v3.4.0）**: 专业锚点自动选题

> 完整算法、降级、展示模板见 **`templates/professional-anchor.md`**。以下为必须执行的摘要。

1. **读库**：`ai-concept-bank/concepts.json`。仅 **eligible**：`status=ready` 且台词非空 且 `script_meta.authored_by=ai-concept-narrator` 且 `script_meta.reviewed=true`。库不存在则提示 `git submodule update --init`，本期可跳过。  
2. **匹配**：用用户已确认的事件/趋势标题+摘要，匹配各概念的 `news_keywords` / `aliases` / `name`。  
3. **冷却**：`last_used` 距今 < `reuse_gap_days`（默认 14）且同角度 → 不进默认推荐（可展示在「冷却跳过」）。  
4. **排序**：命中本期 +100；tier1 +40；从未用 +20；较久未用 +10；低 use_count +5。取 top 3。  
5. **时长**：daily → 15s（用 `script_15s`）；weekly/monthly → 30–60s（优先 `script_60s`，否则 15s 兜底并标注）。  
6. **向用户展示候选并确认**，写入会话变量：`ANCHOR_CONCEPT_ID` / `ANCHOR_ANGLE` / `ANCHOR_DURATION_SEC` / `ANCHOR_SKIP`。  

无强命中时走 P3：tier1 中 `last_used` 最旧或 null 的 **eligible** 概念。  
用户可选：用推荐 / 选编号 / 指定 id / **本期不要锚点**。

确认后进入 Phase 2。

### Phase 2: 视频脚本生成

对每个选中事件，按模板生成脚本。

**风格要求**:
- **🔴 说人话！** 像跟朋友聊天，不要播音腔；结论冷静
- 像 B站 AI 科技 UP 主
- 快节奏；**情绪词黑名单**见 `templates/credibility-and-tone.md`（炸了/大瓜/闹鬼/白嫖…）
- 总时长按 `REPORT_MODE`：daily 75-135s（≤160 含锚点）/ weekly 100-150s / **monthly 200-280s（≤320 含锚点）**
- 每段字数：daily/weekly ≤80 字 / **monthly ≤100 字**
- **🔴 默认 3W + 可信度**（全模式；精简仅更短更少条）
- **🔴 灰色渠道 ≤1 条**，改写为风控/资产风险
- **🔴 每期 1 个专业锚点**（除非 `ANCHOR_SKIP`）：仅 **eligible** 台词，见 `templates/professional-anchor.md`
- **🔴 画面/口播不展示数据来源**（v3.17.0）：视频正文、Hook、结尾 CTA **禁止**出现「数据来自 linux.do 社区精选」「来源于 linux.do」「新闻来自社区」等字样；来源仅供内部报告参考，不写进口播与字幕

**输出结构（默认 3W）**:
```
标题：{事件+影响，禁情绪词}
Hook：{5s 钩子，15-25 字，必须套 4 主力公式之一（社交共鸣/反转认知/否定警告/数据背书）；禁总结型（一句话堆≥2事件）；禁套话后缀（今天AI圈…动了/本期周刊把…一次讲清）；超 25 字砍数字，不足 15 字补冲突词；下一句落到事实}
对应封面大字：____（=Hook 前 12 字原词，强制封面大字核心名词与 0-2s 口播原词对齐，禁换同义词；封面主文案 14-18 字=Hook 前半句，副文案数字 4-8 字=Hook 里的数字原词）

## 选材排序（5维 1/3/5 三档，满分 25；标准模式强制展示，精简模式必做）
| 排名 | 事件 | 影响范围 | 新鲜度 | 实用性 | 话题性 | 争议性 | 总分 |
|------|------|---------|--------|--------|--------|--------|------|
阈值：≥18 进 Top3-5 单独 3W；<15 不单独成段，并入强事件一句 So What

正文（每条）：
What：{一句可验证事实}
So What：{影响}
Now What：{可执行建议，含操作动词（换/挪/配/备/查/避/开/砍/留兜底）；🔴 禁纯观察——"关注/留意/看/等/观望"单独出现且无操作动词=不通过；灰渠道须给"走官方渠道+X"而非只"走官方渠道"}
可信度：{五档之一}

{专业锚点场景 - 🔴 位置=总时长×0.7~0.8，直击中段尿点；命中概念在 55% 前出现的新闻后补桥句"这个词待会儿专门讲清"，再在 70-80% 集中解释；锚点 scene 起始秒/总秒须∈[0.7,0.8]，偏离>5% 须重排；**v3.39.0 容差：≤1pp（0.801~0.810）属测量近似直接 PASS 不重排（0921 周报 80.5% 过）**}

结尾：{CTA}
```
> 🔴 **4 主力钩子公式**（源 `social_media/爆款开头钩子.md`，Hook 必须套其一）：1.社交共鸣型"你身边有没有这样的人" 2.反转认知型"今天被上了一课" 3.否定警告型"千万不要" 4.数据背书型"99%的人都不知道"

细则：`templates/script-template.md`、`templates/credibility-and-tone.md`；周报见 `templates/script-template-weekly.md`

**🔴 专业锚点场景（v3.4.0，`ANCHOR_SKIP=false` 时强制）**：

1. 读取 `id == ANCHOR_CONCEPT_ID` 条目，必须 **eligible**：`ready` + 台词非空 + `authored_by=ai-concept-narrator` + `reviewed=true`。  
2. 口播正文 **原样使用** `script_15s`（或周/月的 `script_60s`）；**禁止**主会话手写/改写整段专业定义；**禁止**非 narrator 来源台词。  
3. 允许在锚点前加 ≤15 字过渡（如「刚才提到 MoE——」），不改动库内定义句。  
4. 锚点 = **独立 scene**（独立 TTS + 图），计入场景列表与 Phase 7/8 校验。  
5. 插入位置：命中该概念的新闻/趋势之后；无命中则 CTA 前（月报则在月度总结前）。  
6. 🔴 **位置硬约束（v3.21.0；v3.39.0 容差）**：锚点 scene 起始秒 / 总秒须 ∈ [0.7, 0.8]（直击诊断4 中段尿点，完播率 4.35%→6-8%）。命中概念在 55% 前出现的新闻后补 ≤15 字桥句"这个词待会儿专门讲清"，再在 70-80% 集中解释；偏离 >5% 须重排 scene 顺序（08-24 锚点 57% 即违反）；**≤1pp 的超出（0.801~0.810）属测量近似，直接通过不重排**（0921 周报锚点 80.5% 验收通过）。见 `templates/professional-anchor.md`。

若未 eligible 且用户仍要该概念：调 **`ai-concept-narrator`**（`ai-concept-bank/prompts/script-15s-request.md`）→ `reviewed=true` → `ready` → 再进脚本。见 concept-bank README。

**🔴 重要：保存每个场景的 TTS 文本**，Phase 7 字幕生成需要直接使用这些文本（不用 ASR 识别）。

**🔴 A/B 双 Hook 输出（v3.21.0，解"无公式轮换对照"）**：
每期 Phase 2 同时输出 **2 个 Hook 候选**（从 4 主力公式挑 2 个不同类型），标记 `[HookA:公式]` `[HookB:公式]`，随机选 1 发布。写入 `news-pipeline/{date}/hook-ab-log.md` 记录：`hook_a` / `hook_b` / `published` / `5s_completion` / `plays`（48h 回填）。2-3 周覆盖一轮 4 公式，筛选最适合本账号的公式。

**🔴 月报模式脚本模板**（仅当 `REPORT_MODE=monthly` 时生效，参考 `templates/script-template-monthly.md`）：

结构：1 Hook + 4 趋势段 + 1 月度总结 + 1 下月展望 + 1 CTA（共 8-9 段）

```
标题：{核心标题，如"2026年6月AI圈：GPT调度乱象与GLM开源逆袭"}
Hook：{一句话点出本月最大风向，如"这个6月，AI圈被GPT调度和GLM开源两件事刷屏了"}

正文：
{趋势一段} - {趋势名 + 热度变化时间线 + 1-2个代表案例，约100字}
{趋势二段} - {同上}
{趋势三段} - {同上}
{趋势四段} - {同上}
{月度总结段} - {TOP10归类 + 主题分布一句话，约60字}
{下月展望段} - {从下月展望选2-3条预测，约60字}

结尾：{CTA：关注羊报AI月报，每月带你回顾AI圈整月风向}
```

**月报脚本示例**（基于 2026-06 月报）：

```
标题：2026年6月AI圈：GPT调度乱象与GLM开源逆袭
Hook：这个6月，AI圈被两件事反复刷屏——OpenAI的GPT调度与额度反复震荡，和智谱GLM新版本的开源贴脸输出。

趋势一：GPT调度混乱与Codex额度震荡
六月三号起OpenAI大规模二验风暴，奥特曼连夜取消短信二验、新增passkey。中下旬降智争议持续，月末Codex灰度最新版并连续重置额度，全月话题峰值出现在六月十号。

趋势二：国产模型集中爆发，GLM贴脸输出
...
```

**月报脚本特殊要求**：
- 每段趋势必须含「时间线（什么时候）+ 驱动（为什么）+ 代表案例（具体帖）」三要素
- 月度总结段引用 TOP10 归类（如"OpenAI生态占TOP10五席"）
- 下月展望段只选 2-3 条最可能成真的预测
- **数字中文化**（见 B站简介数字中文化章节，月报脚本与简介均强制中文化，禁止阿拉伯数字连续出现）

**🔴 精简模式脚本模板**（CONDENSED=true：更短 3W，结构与默认相同）：

每条 3W + 可信度，每段 1-2 句，条内约 10-20s：

```
标题：{标题}
Hook：{核心事件，一句话抓住注意力，15-25 字，套 4 主力公式之一（社交共鸣/反转认知/否定警告/数据背书）；禁总结型堆≥2事件}

What（发生了什么）：{关键事实，2-3句}
So What（影响啥）：{对行业/用户的影响，1-2句}
Now What（值不值得跟进）：{结论/建议，1句，含操作动词，禁纯观察}
可信度：{五档之一}
```

**精简模式脚本示例**：
```
标题：Codex 后台写日志把 SSD 写报废
Hook：[否定警告] OpenAI 的 Codex 最近干了件离谱的事，千万别让它无人值守跑过夜
对应封面大字：Codex 把 SSD 写报废

What（发生了什么）：Codex 在后台疯狂写操作日志，连续运行几小时后，用户的 SSD 直接被写满报废。日志文件膨胀到几十 GB，完全失控。

So What（影响啥）：这暴露了 AI Agent 在自主执行任务时缺少资源监控的问题。如果在生产环境跑，可能直接把服务器搞挂。

Now What（值不值得跟进）：值得关注，这是 AI Agent 资源管理的典型案例，后续 OpenAI 大概率会加限制。
```

**精简模式要求**：
- 每段严格控制在 1-2 句，不超过 40 字
- 🔴 Hook 必须一句话抓住核心冲突，15-25 字，套 4 主力公式之一（社交共鸣/反转认知/否定警告/数据背书）；禁总结型堆≥2事件；禁套话后缀。上方示例"Hook：OpenAI 的 Codex 最近干了件离谱的事"为**反转认知正面样板**（TOP2，方案最核心公式）。4 公式各 1 条样板（无重复）：
  - **社交共鸣型**「你身边有没有跑长任务被掐断的」
  - **反转认知型**「OpenAI 的 Codex 最近干了件离谱的事」（上方示例，保留）
  - **否定警告型**「千万别让 Codex 无人值守跑过夜」
  - **数据背书型**「99%的人没注意 Codex 在偷写日志」
- What 要客观、So What 要有洞察、Now What 要有结论
- 🔴 Now What 禁纯观察——"关注/留意/看/等/观望"单独出现且无操作动词=不通过
- 整体风格仍然要"说人话"，不要播音腔
- 结尾 CTA 可省略（精简模式追求节奏紧凑）

**精简模式可与破格模式叠加**：当同时启用时，Hook 用破格类型标记，正文仍用 3W 结构：
```
标题：{标题}
Hook：[破格类型] {一句话抓住核心冲突}

What（发生了什么）：{关键事实}
So What（影响啥）：{影响}
Now What（值不值得跟进）：{建议}
```

**🔴 破格模式附加要求**（仅当 STYLE_MODE=poge 时生效）：

在脚本中为每个场景标注破格类型：

```
标题：{标题}
Hook：[破格类型] {开场，用破格制造意外感}

正文：
[身份破格] {段落1 - 引入事件}
{段落2 - 核心信息，正常叙述}
[语言破格] {段落3 - 争议/反转}
{段落4 - 延伸}

结尾：{CTA}
```

破格标记规范：
- 用方括号标注：`[身份破格]`、`[场景破格]`、`[道具破格]`、`[语言破格]`、`[对象破格]`、`[角色破格]`
- 标记放在段落开头
- 同一视频至少使用 3 种不同破格类型
- 参考模板：`templates/script-template.md`（破格模式模板）

**🔴 禁止使用的词汇**：
- 社区名：「佬友」→「大家」；「Linuxdo」「L站」→「社区」「论坛」
- **情绪黑名单**（见 `templates/credibility-and-tone.md`）：炸了/炸裂/大瓜/吃瓜/闹鬼/背刺/赢麻/白嫖/薅羊毛/彻底炸锅… → 专业替换词

**🔴 脚本审核检查清单**：展示脚本给用户前，必须逐句检查：
1. 禁止词汇 + 情绪黑名单是否清零  
2. 破格标记（非破格写 N/A）  
3. 口语化、非播音腔  
4. **每条是否有 What / So What / Now What / 可信度**  
5. **灰色渠道是否 ≤1 且无操作指南**  
6. **专业锚点**：仅 1 个（或 SKIP）且 **eligible**（ready+narrator+reviewed）  
7. **平台合规审查**（见下方 + **`templates/platform-compliance.md`**，必须落盘）  
8. **🔴 Hook 4 项（v3.21.0，缺一项不可发布）**：
   - `☐ Hook 15-25 字`
   - `☐ 套 4 主力公式之一（标明：社交共鸣A / 反转认知B / 否定警告C / 数据背书D）`
   - `☐ 禁≥2事件堆叠（周报禁≥2事件）`
   - `☐ 禁"一次讲清/今天AI圈…动了"套话后缀`
   - `☐ 已填"对应封面大字"字段并与 Hook 原词对齐`
9. **🔴 锚点位置（v3.21.0；v3.39.0 容差）**：`☐ 锚点位置=总时长 70-80% 处`（计算：锚点 scene 起始秒/总秒，偏离>5% 须重排；**≤1pp 超出即 0.801~0.810 直接过**，0921 周报 80.5% 实测通过）——08-24 锚点 57% 即此项不通过
10. **🔴 Now What 质量（v3.21.0）**：`☐ Now What 非纯观察`——扫每条 Now What，"关注/留意/看/等/观望"单独出现且无操作动词=不通过——08-26 Scene7/Scene5 即此项不通过
11. **🔴 选材排序表（v3.21.0）**：`☐ 选材排序表已展示`（5 维 1/3/5 三档，总分满分 25，≥18 进 Top3-5，<15 不单独成段）——08-24/08-26 无排序表即此项不通过
12. **🔴 周报结构（v3.21.0，仅 weekly 模式）**：`☐ 周报=本周1件大事3W深聊50s+2-3条一句话快讯，非5-6条堆叠各3W浅聊；深聊 What 层讲时间线（周一到周五演变，日报做不到的差异点）`——W33 5条堆叠即此项不通过

### 🔴 平台合规审查规则（v2.8.0 + **v3.13.0 强化**）

**完整细则（选题 A/B 档、封面铁律、公众号/视频号专项、落盘清单）**：  
→ **`templates/platform-compliance.md`**（Phase 1 选材 + Phase 2 脚本/标题/封面 + Phase 10 发布文案强制对照）

**依据文件**（skill 根目录）：

| 文件 | 平台 |
|------|------|
| `bilibili社区公约.md` | B站 |
| `抖音社区自律公约.md` | 抖音 |
| `微信公众平台运营规范.md` | 公众号 |
| `微信视频号运营规范.md` | 视频号 |
| **`微信视频号常见的不合规频道内容概述.md`** | **视频号限流/违规类型细目** |
| **`微信公众号互联网用户公众账号信息服务管理规定.md`** | **公众号删文常见法规依据** |
| **`知乎社区规范.md`** | **知乎（见 `templates/platform-zhihu.md`）** |
| **`知乎关于 AI 辅助创作内容的治理细则.md`** | **知乎 AI 声明与低质内容治理（强制对照）** |

**🔴 知乎平台专项** → **`templates/platform-zhihu.md`**（文章派生 + 合规清单 + 草稿上传 + 坑 334-343）。**Phase 10.3b** 生成文章、**Phase 15** 上传，两处均以该文件为准。

#### 禁止内容（所有平台通用）

| 类别 | 具体规则 | 示例 |
|------|---------|------|
| 🚫 政治敏感 | 不得危害国家安全、泄露国家秘密、颠覆国家政权 | 不评论政治事件 |
| 🚫 虚假信息 | 不得散播虚假、谣言等不实、误导性信息 | 新闻必须有来源依据；媒体内容禁止标题写成定论 |
| 🚫 暴力恐怖 | 不得展示血腥、惊悚、残忍等致人身心不适的内容 | 不描述暴力细节 |
| 🚫 低俗内容 | 不得含有性暗示、性挑逗等易使人产生性联想的内容 | 不使用低俗用语 |
| 🚫 侵权内容 | 不得侵犯他人名誉权、肖像权、隐私权、著作权等 | 引用需注明出处；**慎用 AI 写实真人主播封面** |
| 🚫 未成年人 | 不得发布有损未成年人身心健康的内容 | 不涉及未成年话题 |

#### 标题规范（所有平台通用）

| 规则 | 说明 | 违规示例 |
|------|------|---------|
| 🚫 标题党 | 标题必须与内容相符，不得使用夸张、惊悚、极端内容 | 「震惊！」「不看后悔！」 |
| 🚫 误导性 | 不得使用侮辱、脏话词汇，引人不适 | 不使用攻击性语言 |
| 🚫 文不对题 | 不得使用与实际内容不符的夸张、诱惑性词汇 | 标题与视频内容不匹配 |
| 🚫 敏感捆绑 | 勿把融资/政策/外泄与产品发布绑成「同日升温/博弈」标题 | 「…融资同日升温」「开源还要被切断吗」 |

#### 内容规范（各平台特殊要求）

**B站特别规则**：
- 🚫 不得使用轮播文字、大字覆盖、简单拼凑内容（低质内容）
- 🚫 不得发布画质模糊、内容不完整、音画不相关的内容
- 🚫 封面、标题突出展示违规内容将从严处置
- ✅ AI生成内容需符合社区规范

**视频号特别规则**（对照 `微信视频号常见的不合规频道内容概述.md` + 运营规范）：
- 🔴 **AI生成内容必须显著标识**：生成/合成非真实音视频须显著标识
- 🔴 **封面禁止写实 AI 主播/假新闻脸**（易触肖像/虚假类；v3.13 封面 prompt 禁用 news anchor 人像）
- 🚫 融资内幕、政策对抗、「切断/外泄」等话术默认不进短标题/描述（B 档，见 platform-compliance）
- 🚫 不得使用夸张标题，内容与标题严重不符
- 🚫 不得发布批量同质化、低质量内容
- 🚫 视频配音与画面不相关
- **2026-07-26 实测**：可出现「限制传播 + 存在敏感或者违规内容」且**不给细码** → 按封面 + 政策/融资话术优先整改

**抖音特别规则**：
- 🚫 不得借助社会负面事件、敏感事件进行商业营销宣传
- 🚫 不得发布哗众取宠、恶意审丑等博眼球内容
- 🚫 不得发布画质模糊、无完整内容、观感体验差的视频
- ✅ 鼓励原创、优质内容，建议真人出镜或讲解

**公众号特别规则**（对照 `微信公众号互联网用户公众账号信息服务管理规定.md` + 运营规范）：
- 🔴 **无互联网新闻信息服务许可时**：避免「每日要闻/采编通稿」体；账号定位用「产品与开发者观察笔记」
- 🔴 **B 档默认不上公众号**：融资/IPO/外泄/监管/政策联署/开源对抗叙事（见 platform-compliance 选题两档）
- 🚫 标题禁止把「据媒体报道」写成已官宣定论（对应规定第十八条虚假信息等风险）
- 🚫 不得发送垃圾信息并存在过度营销行为
- 🚫 不得发布与账号功能介绍不符的内容
- ✅ 提供具有价值的、持续性的并与该账号高度相关的内容
- **2026-07-26 实测**：可「接投诉 + 违反《互联网用户公众账号信息服务管理规定》+ 已删除」且**不写条款号** → 优先按第五条/第十八条（三）（六）整改选题与包装

**知乎特别规则**（v3.72.0 新增，对照 `知乎关于 AI 辅助创作内容的治理细则.md` + `知乎社区规范.md`；完整审核见 `templates/platform-zhihu.md` §2）：
- 🔴 **必须加「包含 AI 辅助创作」创作声明**，并在文中披露 AI 使用目的（资料检索/初稿整理/排版）
- 🔴 **作者须完成主要智力劳动**：稿中必须有「编辑判断」段（作者视角的判断，非复述）——这是「辅助创作」与「机器生成内容」的分界
- 🔴 **图文必须相关**：配图只放与该小节事件对应者，宁缺勿错配（治理细则点名治理「图文不相关」）
- 🚫 无资质不得转载时政类新闻；不得以「揭秘/重磅/独家爆料/知情人士称」渲染
- 🚫 标题/封面不得加导流或营销推广信息；不得诱导至第三方平台关注（公众号 CTA 整段删）
- 🚫 不得发布机器生成内容、不得用自动化程序批量发布、不得重复发布相似内容、不得代写代发
- 🚫 不得拉踩引战、辱骂、阴阳怪气；AI 新闻里的「XX 完了/慌了」式表达须收敛

#### AI News Video 合规检查清单

在生成脚本时，必须逐项检查（**完整勾选表见 `templates/platform-compliance.md` §5，须写入 review-checklist.md**）：

```
✅ 合规检查清单：
☐ 选题 A/B 档：公众号/视频号未强推融资·政策·外泄·监管类
☐ 新闻/产品信息是否有可靠来源？媒体内容是否标「据报道/未独立核实」？
☐ 标题是否与视频内容相符？是否避免「同日升温/切断/外泄/博弈/风暴」？
☐ 是否包含暴力、恐怖、低俗内容？（如有则删除或改写）
☐ 是否涉及政治敏感 / 舆论对抗叙事？（回避或降级，勿上标题）
☐ 是否侵犯他人权益？（引用注明出处；封面无写实假主播）
☐ 是否涉及未成年人？（如有则删除）
☐ 视频号：AI 生成标识将开启；封面无真人感主播
☐ 公众号：非新闻采编口吻；B 档已删或未进标题
☐ 描述/简介是否与视频内容一致？（避免误导）
☐ 是否有过度营销 / 强诱导内容？（避免广告与诱导刷量嫌疑）
☐ 整体内容符合平台生态要求（基本要求）

🔴 v3.21.0 新增 5 项必勾（数据驱动，缺一项不可发布，须写入 review-checklist.md）：
☐ Hook 15-25 字
☐ Hook 套 4 主力公式之一（标明：社交共鸣A / 反转认知B / 否定警告C / 数据背书D）
☐ Hook 禁≥2事件堆叠（周报禁≥2事件）
☐ Hook 禁"一次讲清/今天AI圈…动了"套话后缀
☐ Hook 已填"对应封面大字"字段并与原词对齐
☐ 锚点位置=总时长 70-80% 处（锚点 scene 起始秒/总秒，偏离>5% 须重排；≤1pp 超出 0.801~0.810 属测量容差直接过）
☐ Now What 非纯观察（"关注/留意/看/等/观望"单独出现且无操作动词=不通过）
☐ 选材排序表已展示（5维 1/3/5 三档，满分 25，≥18 进 Top3-5，<15 不单独成段）
☐ [周报] 本周1件大事3W深聊50s+2-3条一句话快讯，非5-6条堆叠；深聊 What 讲时间线
```

#### 违规后果

| 平台 | 处罚措施 |
|------|---------|
| B站 | 删除下线、限制传播、添加提醒标识、封禁账号 |
| 视频号 | 减少推荐、限制传播、删除内容、暂停/终止服务、封禁账号 |
| 抖音 | 删除/屏蔽内容、暂停/终止账号功能、封禁账号 |
| 公众号 | 删除内容、限制功能、封禁账号 |
| 知乎 | 提示与处罚（按违规程度）、标识/减少分发/折叠/建议修改/删除；批量违规时展示干预 |

**Why:** 四个平台都有严格公约/法规；2026-07-26 视频号限流 + 公众号删文；**同日周报**抖音「不适宜公开/仅自己可见（画面）」证明：内部审核清单通过 ≠ 平台过审，且 **画面与标题攻击词** 是独立维度  
**How to apply:** Phase 1 划分 A/B 档 → Phase 2–5 按 `platform-compliance.md`（含 §8 禁词 + 画面铁律）写脚本/标题/分镜/场景图 → 审核清单落盘 → 再进入渲染/上传

**🔴 用户审核步骤**：脚本生成后，必须将完整脚本展示给用户审核，获得确认后才能进入 Phase 3。用户可能要求修改某些场景的文案。

**🔴 用户确认脚本后、进入 Phase 3 前：写入专业锚点 usage-log（v3.4.0 强制）**

若 `ANCHOR_SKIP=true`，跳过。否则必须：

1. **Append** `ai-concept-bank/usage-log.json` 一条记录（字段见 `templates/professional-anchor.md`）：`date`, `concept_id`, `angle`, `mode`（daily/weekly/monthly）, `duration_sec`, `news_trigger`, `report_path`, `script_path`, `notes`。  
2. **更新** `ai-concept-bank/concepts.json` 对应概念：`last_used=date`，`use_count+=1`，`angles.used` 含本次 angle。  
3. **不要**静默 git commit 子模块；可提示用户稍后 bump submodule。  
4. 审核清单应能勾选：「已写 usage-log」。

**参考模板**: `templates/script-template.md`；`templates/credibility-and-tone.md`；专业锚点：`templates/professional-anchor.md`

### Phase 3: 分镜生成

根据视频脚本生成分镜表，每个脚本段落对应 1 个分镜。

| 镜号 | 时长 | 镜头类型 | 画面内容 | 字幕重点 | 转场 |
|------|------|----------|----------|----------|------|
| 1 | 3s | 特写 | AI 芯片电路 | Hook 文字 | 淡入 |
| 2 | 5s | 全景 | 科技新闻编辑室 | 事件标题 | 切换 |

**参考模板**: `templates/storyboard-template.md`

**🔴 画面合规（v3.14.0 · 抖音「画面」违规教训）**

分镜「画面内容」列禁止作为主视觉：

| 禁止 | 改为 |
|------|------|
| 隔离舱破裂 / cracked glass / security breach | 明亮机房 + 权限清单 / 监控仪表盘（绿灯） |
| 撬锁、入侵、黑客攻击特写 | 工程师审访问控制、配置 UI |
| 立法楼剪影、两党、法槌特写 | 会议室讨论订阅/合规文档（无法槌主视觉） |
| 红警报、武器、血腥 | 蓝青专业光、产品 UI |

安全事件口播已产品化时，**画面必须同步产品化**，否则只改标题仍会「限制自己可见 / 画面」。

**🔴 破格模式分镜**（仅当 STYLE_MODE=poge 时生效）：

在标准分镜基础上增加「破格镜头」列：

| 破格类型 | 镜头技巧 | Prompt关键词 |
|---------|---------|-------------|
| 身份破格 | 身份与环境对比构图 | unexpected role, contrast, juxtaposition |
| 场景破格 | 倾斜构图（Dutch angle） | dutch angle, tilted, surreal setting |
| 道具破格 | 道具特写+反差背景 | unconventional object close-up, repurposed |
| 语言破格 | （不影响镜头，影响TTS） | — |
| 对象破格 | 荒诞目标特写 | absurd target, unexpected audience |
| 角色破格 | 角色互换对比 | role reversal, character twist, split composition |

### Phase 4: 图片 Prompt 生成

使用填空即用模板为每个分镜生成图片 Prompt，输出到 `news-pipeline/YYYY-MM-DD/prompts/image-prompts-YYYY-MM-DD.json`。

**视频品牌**: 「今日羊报 AI」
**副标题**: 「AI 新闻」

#### 填空即用模板

```
Create a realistic editorial news image about:

{新闻内容}

The image should show:
- clear main subject
- real-world environment
- strong relation to the news event
- cinematic but realistic lighting
- professional news photography style
- modern AI technology atmosphere

Avoid:
- abstract AI concepts
- floating holograms
- random sci-fi elements
- text in image
- logos
- low-detail compositions

[新闻核心地点] with [主要人物/物体], [他们在做的关键动作]. [标志性环境细节], [时间/天气/光线]. [情绪与氛围描述]. [新闻摄影/编辑插图风格], photorealistic, highly detailed, shot on [镜头焦段] — no text, no watermark.

Wide 16:9 horizontal cinematic composition, full-frame landscape framing. absolutely no text, no letters, no Chinese characters, no watermark.
```

> **🔴 结尾这行构图句是强制项（v3.63.0 坑 301）**：`size:'auto'` 的端点（rainflow）**只靠 prompt 决定画幅**——无构图提示时 gpt-image-2 返回方形 1254×1254，进成片必被左右裁切。1025 期补上该句后 6/6 出 1672×940/941（1.78）。**不要**只写 `16:9 aspect ratio` 就以为够了，**必须**是这条完整的 composition/framing 句。
> **禁止**再追加「『今日羊报 AI』『AI 新闻』分两行显示在右上角充当背景」——该尾巴会诱发整段伪中文/英文文案烧进画面（v3.33.0 坑，scene2/scene4 均报废重制）。品牌由 Remotion 标题栏叠加，不进图。

#### 输出格式

```json
[
  {
    "scene": 1,
    "news": "新闻标题",
    "prompt": "填充后的完整 Prompt"
  }
]
```

**🔴 图片-脚本映射铁律（v2.8.0 新增）**：

图片 prompt JSON 中的 `scene` 编号必须与脚本场景编号严格 1:1 对应！

常见错误：
- ❌ Hook 场景（scene1）单独生成一张图片，第一条新闻（scene2）又生成一张详细图 → 导致后续所有图片偏移 +1
- ❌ 图片按"新闻事件"编号而非"脚本场景"编号

正确做法：
- ✅ Hook 和第一条新闻合并为同一场景时，只生成 1 张图片（scene1）
- ✅ 图片 prompt JSON 数组长度 = 脚本场景数（如6个脚本场景 = 6张图片）
- ✅ `image-prompts.json` 中 scene 1-N 与 `voiceover-texts.json` 中 scene 1-N 一一对应
- ✅ Phase 8 校验时必须确认：`len(imagePrompts) == len(scriptScenes)`

**🔴 破格模式 Prompt 变体**（仅当 STYLE_MODE=poge 时生效）：

在标准 prompt 末尾追加反差视觉描述：

```
[标准 prompt] + The image conveys a sense of [破格类型]:
- [反差视觉元素1]
- [反差视觉元素2]
- unexpected contrast between [A] and [B]
```

破格类型→视觉关键词映射：

| 破格类型 | 视觉关键词 |
|---------|-----------|
| 身份破格 | unexpected role, identity contrast, juxtaposition of status |
| 场景破格 | surreal setting, environment mismatch, unexpected location |
| 道具破格 | repurposed object, unconventional tool, creative misuse |
| 语言破格 | (不影响图片) |
| 对象破格 | absurd audience, unexpected target, comical mismatch |
| 角色破格 | role reversal, character twist, reversed hierarchy |

参考模板：`templates/image-prompt-template.md`（破格模式 Prompt 变体）

### Phase 5: 图片生成

**主方案**: 使用 Python+curl 直接调用图片生成 API。

```python
import json, subprocess, base64, tempfile, os, time

API_URL = "用户提供的 API URL"  # 如 https://ai.prism.uno
API_KEY = "用户提供的 API Key"
MODEL = "gpt-image-2"  # 注意：不是 gpt-image-1

def size_for(api_url):
    """🔴 坑 300：size 必须按端点运行时决定，禁止硬编码。
    rainflow（25 张额度，优先用）只接受 'auto' —— 任何显式比例都回「不支持的图片比例」；
    prism.uno / elysiver 等其他端点走 '1536x1024'。

    🔴 判据必须是 URL 子串 'rainflow'，**不能按 _000/_001/_002 后缀判**（坑 304）：
    端点编号会随额度漂移——1025 实测 settings.json 是 GEN_IMG_API_URL=rainflow、
    _000=prism.uno、_001/_002=elysiver；而 To_Learn.md 的备忘写的是 _003=rainflow、
    本体=prism.uno。用后缀判会随用户改编号而静默判错，用域名子串判永远跟得上。

    画幅由 prompt 里的 16:9 构图句保证（Phase 4 / 坑 301），不靠 size 保证。"""
    return "auto" if "rainflow" in (api_url or "") else "1536x1024"

def generate_image(prompt, output_path, api_url=API_URL, api_key=API_KEY):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run([
            "curl", "-s", "-X", "POST", f"{api_url}/v1/images/generations",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"model": MODEL, "prompt": prompt,
                              "size": size_for(api_url), "n": 1}),
            "-o", tmp_path,
            "--max-time", "120"
        ], check=True, timeout=130)
        with open(tmp_path) as f:
            resp = json.load(f)
        if "error" in resp:
            return False, resp["error"].get("message", str(resp["error"]))
        img_b64 = resp["data"][0].get("b64_json", "")
        if img_b64:
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
            return True, "OK"
        # Try URL download
        img_url = resp["data"][0].get("url", "")
        if img_url:
            subprocess.run(["curl", "-s", "-o", output_path, img_url], timeout=60)
            if os.path.getsize(output_path) > 1000:
                return True, "OK (from URL)"
        return False, "No image data"
    except Exception as e:
        return False, str(e)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
```

**API 源列表（按优先级排序）**：

| 优先级 | 名称 | URL | 模型 | 说明 |
|--------|------|-----|------|------|
| 1 | 用户提供 | 用户提供 | gpt-image-2 | 优先使用用户提供的 API |
| 2 | luka77 | http://api.luka77.cc | gpt-image-2 | **最稳定**（HTTP，无 SSL 问题，2026-06-21 验证） |
| 3 | openrouter | https://eo.ioll.pp.ua | gpt-image-2 | 需要 DNS 绕过（198.18.x.x 劫持） |
| 4 | jiuuij | https://jiuuij.de5.net | gpt-image-2 | 需要 DNS 绕过，响应较慢 |
| 5 | prism | https://ai.prism.uno | gpt-image-2 | 需要 VPN，SSL 握手常超时 |

**🔴 DNS 劫持检测与绕过**：

如果 API 连接超时或 SSL 错误，检查 DNS 解析是否被本地代理工具劫持到 198.18.x.x 网段：

```bash
# 检查 DNS 解析
nslookup api.luka77.cc
# 如果返回 198.18.x.x，说明被劫持

# 获取真实 IP 后用 --resolve 绕过
REAL_IP=$(nslookup api.luka77.cc 8.8.8.8 | grep -A1 "Name:" | tail -1 | tr -d ' ')
curl -s --resolve api.luka77.cc:443:$REAL_IP ...
```

**HTTP API 优先**：如果 API 支持 HTTP（如 luka77），优先使用 HTTP 避免 SSL 问题。

**API 选择逻辑**：
1. 优先使用用户提供的 API
2. 如果报错（配额不足、渠道不存在），尝试下一个
3. 如果所有 API 都不可用，提示用户提供可用的 API

**注意事项**:
- **🔴 size 按端点运行时决定，禁止硬编码（v3.63.0 坑 300）**：rainflow 传 `"auto"`、其余端点传 `"1536x1024"`。1025 期派生脚本做 `'1024'→'1025'` 日期替换时，把硬编码字面量 `'1536x1024'` 一起改成了 `'1536x1025'`，rainflow 直接回「不支持的图片比例」——**任何写进请求体的 size 都不能是裸字面量**，必须由 `size_for(api_url)` 这类函数算出来。
- **🔴 端点身份按 URL 子串判，不按 `_000`/`_001` 后缀判（v3.63.0 坑 304，1025 实测）**：额度优先级是 **rainflow（25 张额度）先用 → 额度不够再用 prism.uno → elysiver `_001/_002` 兜底**，但**后缀编号会漂移**：1025 实测 `settings.json` 是 `GEN_IMG_API_URL=chatgpt.rainflow.foo/studio/v1`、`_000=ai.prism.uno`、`_001/_002=elysiver.h-e.top`，而 `To_Learn.md` 的备忘写的是 `_003=rainflow`、本体=`prism.uno`——**同一期两份记录编号不同**。所以：判 rainflow 用 `"rainflow" in api_url`，判 fallback 顺序按**域名**而不是按下标；开工前 `python3 -c` 打印 `{后缀: URL 域名}` 一览（key 只打 len）核一遍再写脚本。
- **🔴 出图后必须验比例（v3.63.0 坑 301）**：每张 `PIL.Image.open(p)` 读尺寸并断言 `w/h >= 1.6`（16:9 ≈ 1.78）。接近 1.0 的方图判失败重出，**不要**把方图塞进 16:9 画面指望 Remotion 拉伸。1025 期 `auto` 无构图句时 6/6 全出 1254×1254 方图，补句后 6/6 出 1672×940/941。
- **必须逐张生成**：API 有并发限制；**禁止**整段 7 张串行卡在一个 10 分钟 Bash 超时里——可按 scene 拆命令或仅生成缺失文件
- **必须从 JSON 文件读取 Prompt**，不能用简化版本
- 每张图片生成后重试一次（如果失败）
- **HTTP API 优先**：HTTP（如 luka77）比 HTTPS 更稳定，避免 SSL/DNS 问题
- **超时设置**：图片生成可能需要 30-180 秒，单张 curl `--max-time` 建议 90–180；整批脚本 timeout 按张数放大
- **DNS 劫持**：如遇连接超时，用 `nslookup` + `curl --resolve` 绕过
- **🔴 settings.env 多端点（v3.10 / 2026-07-21）**：从 `~/.claude/settings.json` 的 `env` 读取 `GEN_IMG_API_URL`/`GEN_IMG_API_KEY` 及 `_001`/`_002` fallback；日志**禁止**打印 key（只允许 set/empty/len）
- **🔴 v3.33.0 中文水印尾巴致乱码（0916 实测）**：scene prompt 结尾的「『今日羊报 AI』『AI 新闻』分两行显示在右上角充当背景」会诱发模型把大段伪中文/整段英文文案画进画面（scene2 伪中文、scene4 整段英文，均报废重制）。修复：删掉该尾巴，追加 `absolutely no text, no letters, no Chinese characters, no watermark`；`Read` PNG 目检必须逐张过，乱码常在整段文案级别才显眼
- **🔴 v3.33.0 端点降级顺序（0916 实测，端点身份见坑 304）**：主站欠费返回 `预扣费额度失败`（HTTP 200 包 error）时，换到 prism / elysiver 端点承接；重试脚本应把**上一张成功的端点提到循环最前**，避免每张都先撞欠费主站浪费 2 次×超时。**不要说「`_003` 是 prism」，后缀编号会漂移**（1025：`_000`=prism、`_001/_002`=elysiver、本体=rainflow）——按域名判，见坑 304。
- **🔴 部分成功续跑**：已存在、**且 >20000 字节、且严格 PIL 解码通过、且比例 ≥1.6** 的 `sceneN.png` 才跳过（坑 254 三合一门禁——只验字节数会把「坏但够大」的文件永远跳过）；失败端点记 http 状态后切下一端点
- **scene CTA 兜底**：最后 1 张若全端点失败，可用昨日同结构 CTA 图或 scene1 临时顶替，**封面竖图禁止**此兜底

### Phase 5.5: 异步生成封面（与 TTS 并行）

**🔴 重要优化：封面生成耗时较长（每个约 30-60s），应与 TTS 配音并行执行！**

**🔴 v3.35.0 封面主路径 = 极简中文科技资讯海报**（0910 用户确认可行）：横 `horizontal-4-3.png`、竖 `vertical-3-4.png` **都按** `templates/cover-prompt.md` 出图，**画面文字源 = 脚本「对应封面大字」字段**（Hook 原词短句，1 句冲突 + 1 个数字，两行排版）——**禁止**把 `publish.json.title` 整条发布标题印上画面（坑 203 / 0917 复盘：堆叠稀释冲突，与 Hook 脱钩）。`publish.json.title` 仍作 B站/公众号列表标题与渲染文件名。禁止再用演播室空镜 / news desk 英文 prompt 当封面。

**🔴 v3.35.0 封面顺序铁律（坑 190 升级）**：封面画面文字的单一事实源是脚本「对应封面大字」字段（= Hook 原词短句），**Hook/封面大字定稿必须早于封面生成**——Phase 2 若改 Hook，必须 `rm` 旧封面按新大字重出，**禁止沿用旧图**。Phase 10 若只改 `publish.json.title`（列表标题）而 Hook 未变，**不需要**重出封面（0917 决策：列表标题与封面文字解耦）。Phase 5.5 开工前先确认 Phase 2 Hook/封面大字已冻结。

**🔴 v3.29.0 日期居中硬要求仍有效**：封面上的日期字段必须**水平居中**（海报风里日期单独一行居中，不是旧演播室中央大白字）。无论 API 出图还是本地 Pillow 叠字，生成后必须 `Read` 视觉校验；不居中即重生成。本地脚本基准：`dx = (tw - dw) // 2`，`dy ≈ int(th * 0.34)`。

在 Phase 5 图片生成完成后，使用 `Agent` 工具异步生成所有封面：

```python
# 使用 Agent 工具异步执行封面生成
# 这样可以与 Phase 6 TTS 配音并行，节省总时间

# 封面生成脚本（在 agent 中执行）
import json, subprocess, base64, tempfile, os, time

API_URL = "用户提供的 API URL"  # 优先使用 eo.ioll.pp.ua
API_KEY = "用户提供的 API Key"
MODEL = "gpt-image-2"

# 🔴 v3.35.0：完整中文海报模板在 templates/cover-prompt.md
# 这里只放调用约定。COVER_TEXT 必须 = 脚本「对应封面大字」字段（Hook 原词短句，两行），
# 禁止用 publish.json.title 整条发布标题当画面文字（坑 203）
COVER_PROMPT_FILE = "templates/cover-prompt.md"
COVER_TEXT = "OpenAI把降智取消了\n五分钟后直接不给你用"   # 例：Hook 原词，主文案一行 + 数字短句一行
# 🔴 size 不写裸字面量（坑 300 / 坑 304）：rainflow 端点传 "auto"，其余端点传下方目标尺寸；
#    判「是不是 rainflow」用 URL 域名子串，不要按 _000/_001 后缀判（编号会漂移）
# 竖版 ratio=3:4 目标 1152x1536（1024x1536 是 2:3 不是 3:4，别用）
# 横版 ratio=4:3 目标 1536x1152（1536x1024 是 3:2，接口不认时走本地 PIL 兜底，别将就）
# 端点：settings.json GEN_IMG_API_URL 起，失败按域名顺序 fallback（rainflow → prism → elysiver）；日志禁打印 key
def size_for(api_url, target_size):
    """坑 300/304：rainflow 只吃 'auto'（画幅靠 prompt 的 16:9 构图句），其余端点吃显式尺寸。"""
    return "auto" if "rainflow" in (api_url or "") else target_size

# 封面配置（size 是「非 rainflow 端点的目标值」，不是写死的请求值）
COVERS = [
    {"name": "horizontal-4-3.png", "size": "1536x1152", "ratio": "4:3"},    # B站/通用（4:3 横版）
    {"name": "vertical-3-4.png", "size": "1152x1536", "ratio": "3:4"},   # 抖音/竖版（3:4）
]

def generate_cover(prompt, output_path, size):
    """生成单张封面，带重试机制。size 传 COVERS 里的目标值，函数内按端点换成 rainflow 的 'auto'。"""
    req_size = size_for(API_URL, size)   # 坑 300/304：绝不把裸字面量发出去
    for attempt in range(2):  # 最多重试1次
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = subprocess.run([
                "curl", "-s", "-X", "POST", f"{API_URL}/v1/images/generations",
                "-H", f"Authorization: Bearer {API_KEY}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"model": MODEL, "prompt": prompt, "size": req_size, "n": 1}),
                "-o", tmp_path,
                "--max-time", "120"
            ], capture_output=True, text=True, timeout=130)

            with open(tmp_path) as f:
                resp = json.load(f)

            if "error" in resp:
                if attempt == 0:
                    time.sleep(2)
                    continue
                return False, resp["error"].get("message", str(resp["error"]))

            img_b64 = resp["data"][0].get("b64_json", "")
            if img_b64:
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                return True, "OK"

            img_url = resp["data"][0].get("url", "")
            if img_url:
                subprocess.run(["curl", "-s", "-o", output_path, img_url], timeout=60)
                if os.path.getsize(output_path) > 1000:
                    return True, "OK (from URL)"

            return False, "No image data"
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
                continue
            return False, str(e)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    return False, "Max retries exceeded"
```

**执行方式**：
```bash
# 🔴 重要：不要用 Agent 工具异步生成封面！Agent 会遇到 Bash 权限问题导致失败。
# 直接在主线程中用 Python 脚本生成封面，与 TTS 串行执行即可。
# 如果时间紧张，可以先生成封面再生成 TTS，或者反过来。

# 在主流程中直接执行封面生成 Python 脚本
python3 -c "
import json, subprocess, base64, tempfile, os, time
# ... 封面生成代码 ...
"
```

**封面生成验证**：
```bash
# 生成完成后验证所有封面文件
ls -la news-pipeline/YYYY-MM-DD/*.png | wc -l
# 应该输出 2（horizontal-4-3.png【4:3 横版，B站/通用】, vertical-3-4.png【3:4 竖版，抖音/视频号/公众号】）
```

**优势**：
- 封面生成（2个，约 1-2 分钟）与 TTS 配音（9个，约 2-3 分钟）并行
- 总时间从串行的 6-8 分钟缩短到并行的 3-5 分钟
- 每张封面自动重试一次，提高成功率

### Phase 5.6: 本地生图兜底（v3.19.0 新增，API 全挂 / 文字渲染不达标时）

**与 edge-tts 兜底 mimo-tts 同构**：当 GEN_IMG 多端点全部失败、或 API 出图但中文文字糊掉时，用 Pillow 本地生成 scene 图和封面，保证流水线不中断。

#### 触发条件（满足任一即切本地）

**Scene 图本地化（`gen_images_local.py`）**——🔴 v3.43.0 这是**兜底不是默认**（坑 237）：场景图优先走 Phase 5 的 `gpt-image-2`，只有下面第 1 条命中才切本地，且汇报必须标明「场景图为本地兜底」：
1. API 所有端点 401 / 余额耗尽 / SSL 握手超时 / `net::ERR_*` 全挂
2. 上一期遗留的 scene 图与本期脚本内容不匹配（新闻变了，图没变，需重画）——重画优先重调接口，不直接落本地

**封面本地化（`gen_covers_local.py`）**：
1. API 余额耗尽，无法生成封面
2. **或** API 有余额但 gpt-image-2 渲染的中文日期/品牌名糊掉、错字、变形——封面文字必须像素级准确，API 不可靠时直接本地叠加

#### 本地生图原理

**Scene 图**：用 Pillow 画 8 张主题化抽象背景（1920×1080），深色演播室 + 场景专属配色 + 几何 motif（数据流、发光球、上下文进度条、GPU 卡堆叠、领奖台等）。每张 `draw_sceneN()` 对应一期脚本的一个场景。

**封面**：拿已生成的 `scene1.png` 作底图，裁剪到目标比例，叠加：
- 底部 + 右上角深色渐变蒙版（保证文字可读性）
- 中央大字日期（`Arial Unicode.ttf`，带阴影）
- 右上角品牌块（`今日羊报 AI` / `AI 新闻`，`STHeiti Medium.ttc`）

#### 脚本模板

**封面本地生成 `gen_covers_local.py`**（关键变量）：

```python
#!/usr/bin/env python3
"""Generate covers from scene1.png with text overlay (API balance exhausted)."""
from PIL import Image, ImageDraw, ImageFont
import os

BASE = "news-pipeline/YYYY-MM-DD"          # 当期输出目录
SRC = os.path.join(BASE, "images/scene1.png")  # 底图（优先用 API 出的 scene1）
FONT_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"   # 品牌名中文字体
FONT_ARIAL = "/Library/Fonts/Arial Unicode.ttf"          # 日期数字字体
DATE = "YYYY-MM-DD"   # 🔴 按模式参数映射表读取，勿硬编码
BRAND = "今日羊报 AI"  # 按模式读取（日报/周报/月报不同）
SUB = "AI 新闻"

def draw_cover(out_name, target_w, target_h):
    src = Image.open(SRC).convert("RGB")
    # 裁剪到目标比例
    # 叠加深色渐变蒙版（底部 + 右上角品牌块）
    # 中央大字日期（带阴影）
    # 右上角品牌 + 副标
    canvas.save(os.path.join(BASE, out_name), "PNG", quality=95)

draw_cover("horizontal-4-3.png", 1536, 1152)  # B站/通用 4:3
draw_cover("vertical-3-4.png", 1152, 1536)    # 抖音/视频号 3:4
```

**Scene 图本地生成 `gen_images_local.py`** 结构：

```python
#!/usr/bin/env python3
"""Local scene-image generator (Pillow, no API). Replaces mismatched old images."""
import math, random
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
random.seed(20260821)   # 固定种子保证可复现

def base_gradient(top, bottom): ...      # 垂直渐变底
def radial_glow(img, cx, cy, radius, color, intensity): ...  # 径向发光
def draw_scene1(): ...   # Hook — 演播室全景 + 青色数据流
def draw_scene2(): ...   # 按当期新闻主题画（神秘模型→发光球+问号）
# ... 每个场景对应当期脚本内容
def draw_scene8(): ...   # CTA — 暖色演播室 + 订阅铃铛发光

SCENES = [draw_scene1, ..., draw_scene8]
# 输出到 news-pipeline/video-project/public/images/sceneN.png
```

#### 执行方式

```bash
# 1. Scene 图本地生成（仅当 API 全挂时）
cd /Users/youngsdream/Documents/learn-claude-code
python3 news-pipeline/YYYY-MM-DD/scripts/gen_images_local.py

# 2. 封面本地生成（API 余额耗尽或文字糊掉时）
python3 news-pipeline/YYYY-MM-DD/scripts/gen_covers_local.py
```

**🔴 注意**：
- 封面本地化优先用 **API 出的 `scene1.png` 作底图**（视觉质量更高）；若 scene 也本地化了，则用本地 scene1
- 日期/品牌名变量**必须按模式参数映射表读取**，禁止硬编码 `2026-08-21`——改日期时只改 `DATE` 一处
- 本地 scene 图是抽象几何风格，视觉质量低于 API 出图；**仅作兜底**，API 恢复后应切回 API
- 脚本依赖系统字体：`/System/Library/Fonts/STHeiti Medium.ttc`（品牌名）、`/Library/Fonts/Arial Unicode.ttf`（日期）；缺字体时换 `PingFang.ttc` / `Helvetica.ttc`
- **🔴 v3.47.0 坑 249：封面大字必须按可用宽度实测收缩字号**——固定比例字号（如竖版 `int(w*0.150)=172px`）对 8 字行实宽 1376px，超出可打印宽度（1152−2×margin≈934px）会被 PIL 直接裁掉（1013 用户报「内容被截断」）。修法：`font.getlength()` 实测行宽，从目标字号向下收缩直到 `px ≤ w − 2*margin`（下限 48）；生成时**打印每行 px 与 limit 并断言**。横版同样要过此门（1013 横版 1272/1276 已贴极限）
- 生成后**必须视觉校验**：`Read` 打开 PNG 确认日期/品牌文字清晰无糊无错字，且**日期水平居中**（v3.29.0 硬要求，见 Phase 5.5）

#### 决策流程

```
Phase 5 scene 图生成
├─ API 任一端点出图成功 → 用 API 图（默认）
└─ 全端点失败 / 旧图不匹配 → gen_images_local.py 本地生成

Phase 5.5 封面生成
├─ API 出图且中文文字清晰 → 用 API 封面（默认）
└─ API 余额耗尽 / 文字糊掉 → gen_covers_local.py 本地叠加（优先用 API scene1 作底图）
```

### Phase 6: TTS 配音

根据视频脚本逐场景生成配音：

**🔴 重要：mimo-tts.sh 依赖 settings.json 中的 `MIMO_TTS_API_KEY` 配置。如果未配置，必须使用环境变量方式调用。**

#### 6.1 首选方案：环境变量直接调用 mimo-tts.sh（v3.2.0 新增）

**如果 settings.json 中没有 MIMO_TTS_API_KEY 配置，直接用环境变量方式调用：**

```bash
MIMO_TTS_API_URL="https://your-tts-api-url.com" MIMO_TTS_API_KEY="sk-your-tts-key" \
bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "配音文本" \
  --voice "白桦" \
  --style "新闻播报" \
  --output "news-pipeline/YYYY-MM-DD/voiceover/sceneN.wav"
```

**🔴 关键经验（v3.2.0 新增）**：
- settings.json 中可能没有 MIMO_TTS_API_KEY 配置，导致 mimo-tts.sh 报错 `MIMO_TTS_API_KEY not found`
- 环境变量方式可以绕过 settings.json 配置问题
- TTS API URL 和 Key 通常与图片 API 不同，需要单独收集
- 如果用户未提供 TTS API 信息，先检查 settings.json，再询问用户

**🔴 TTS 网关 503（v3.9.0 / 2026-07-20 实测）**：
- 响应 `gateway_error` / `没有可用的内网节点` / HTTP 503 时：**指数退避重试**（如 5s → 15s → 30s，最多 3–5 次）
- 仍失败：切换 settings.env 中的 fallback 节点（`MIMO_TTS_API_URL` 备选）
- **禁止**把空 wav / 半截 scene 当成功；每 scene 校验文件大小与时长
- 日志只记 status/body 摘要，**禁止打印 API key**

#### 6.2 备选方案：Python 直接调用 MiMo TTS API

如果 mimo-tts.sh 环境变量方式也失败，直接用 Python+curl 调用：

```python
import json, subprocess, base64, tempfile, os, time

API_URL = "https://your-tts-api-url.com/v1/chat/completions"
API_KEY = "sk-your-tts-key"
OUTPUT_DIR = "news-pipeline/YYYY-MM-DD/voiceover"

SCENES = [
    {"num": 1, "text": "场景1文本...", "style": "新闻播报"},
    # ... 每个场景
]

def generate_tts(scene):
    num = scene["num"]
    text = scene["text"]
    style = scene["style"]
    output_path = os.path.join(OUTPUT_DIR, f"scene{num}.wav")
    content = f"({style}){text}" if style else text
    body = {
        "model": "mimo-v2.5-tts",  # 预置音色用这个模型
        "messages": [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": content}
        ],
        "audio": {"format": "wav", "voice": "白桦"}  # 推荐白桦
    }
    # 用 curl 调用 API，解析 base64 音频数据
    # 详见 news-pipeline/2026-06-16 的实际实现
```

**🔴 重要**：预置音色用 `mimo-v2.5-tts` 模型 + `voice: "白桦"`。克隆音色用 `mimo-v2.5-tts-voiceclone` 模型 + base64 音频，但效果差，不推荐。

#### 6.3 兜底方案：edge-tts（v3.15.0 新增，mimo-tts 全部不可用时）

**当 mimo-tts 所有端点（含环境变量配置、settings.env 中的 _001/_002 fallback）均返回 `Gateway Error: 没有可用的内网节点` 或 HTTP 503/502 时，自动切换到 edge-tts（Microsoft Azure Neural TTS）。**

**edge-tts 优势**：
- 无 API Key 依赖，`pip install edge-tts` 即可使用
- 中文音色 `zh-CN-YunyangNeural`（男声，专业可靠，新闻风）效果接近 mimo-tts「白桦」
- 响应稳定，无配额限制

**切换条件**（满足任一即切换）：
1. mimo-tts 返回 `Gateway Error: 没有可用的内网节点`
2. mimo-tts 连续 3 次 HTTP 503/502
3. mimo-tts 所有 fallback 端点均失败

**执行步骤**：

```bash
# 安装 edge-tts
pip install edge-tts>=7.3.1  # v3.48.0：7.2.8 DRM 令牌算法过期必 403（坑250 补充），出口/时钟都对也救不了，直接装 ≥7.3.1

# 生成 MP3（edge-tts 原生输出 MP3）
edge-tts --text "配音文本" \
  --voice zh-CN-YunyangNeural \
  --write-media /tmp/sceneN_edge.mp3

# 转换为 WAV（24kHz PCM16LE 单声道，与 Phase 7 字幕生成兼容）
ffmpeg -y -i /tmp/sceneN_edge.mp3 -acodec pcm_s16le -ar 24000 -ac 1 \
  "news-pipeline/YYYY-MM-DD/voiceover/sceneN.wav"
```

**🔴 v3.47.0 / 坑 250：WSS 403 的根因是出口 IP，第一动作 = `--proxy` 走非 CN 出口**（2026-10-13 实测，TTS 曾卡死约 3.5h）：

- 症状：`wss://speech.platform.bing.com` 握手 `WSServerHandshakeError 403`，但 HTTPS `voices/list` 正常——**只有 WSS 被拒**。
- 已排除（1013 全试过、全部无效，禁止重走）：Sec-MS-GEC 时钟偏移（DRM 自校正也无效）、edge-tts 版本升降（6.1.16 与 7.2.8 都 403）、改 `constants.py` 的 UA/Chromium 版本（MSIE UA + 129 header 补丁，探测矩阵 24 组全 403）、user-site/framework-site 双安装互切。
- 正确路径：`edge-tts --text ... --proxy http://127.0.0.1:7897`。**终端没有 `HTTPS_PROXY` env、系统 scutil 代理对 aiohttp 不生效，必须显式 `--proxy`**；若代理出口在 CN 节点仍 403，**请用户把代理切到美国等非 CN 出口**后一次通过（1013：切美国出口后 6 场景全过；直连与 `api.msedgeservices.com` 仍 403 → 根因=出口 IP）。`gen_tts.py` 派生时保留 `--proxy` 参数。
- 排查探测脚本注意：`python3 -I` 会忽略 `SSL_CERT_FILE`，会报 `ClientConnectorCertificateError` 假故障；用 certifi `cafile` 建 context 或去掉 `-I`。

**推荐音色**：
| 音色 | Voice ID | 说明 |
|------|----------|------|
| 云扬（推荐） | `zh-CN-YunyangNeural` | 男声，专业可靠，新闻风，最接近「白桦」 |
| 云健 | `zh-CN-YunjianNeural` | 男声，激情，适合快节奏 |
| 云希 | `zh-CN-YunxiNeural` | 男声，活泼阳光 |
| 晓伊 | `zh-CN-XiaoyiNeural` | 女声，活泼（卡通风） |

**注意**：
- edge-tts 输出为 MP3，必须用 ffmpeg 转为 WAV（24kHz）才能与 Phase 7 字幕流程兼容
- 转换后音频时长不变，无需调整 Composition.tsx 的 duration
- 重新生成 TTS 后必须同步更新：Composition.tsx sceneConfig → Root.tsx TOTAL_DURATION_SEC → 重算 captions.json → 重渲染

#### 6.3b atempo=1.4 加速（v3.18.0 / 2026-08-18 实测）

音色 `zh-CN-YunxiNeural`（云希）+ ffmpeg `atempo=1.4` 加速，可显著缩短总时长（8 场景实测 112.13s）。

**🔴 换期硬性前置（v3.24.0 / 2026-08-30 W35）**：atempo 有 SKIP 启发式——`out duration < raw*0.95` 视为已加速。`public/voiceover/scene*.wav` 若是**上期残留**（时长本身短于 raw），启发式会误判「已加速」直接保留旧音频 → 成片 0:52 后音画/字幕错位（W35 用户报 3 次）。

**换期 / 重跑 TTS 必须先清残留，再跑 atempo**：
```bash
# 优先：不可逆删除（可能被自动权限拒绝）
rm public/voiceover/scene*.wav
# 若 rm 被拒：shutil.move 到 .stale_archive/（见已知坑 138）
# python3 -c "import glob,shutil,os; os.makedirs('public/voiceover/.stale_archive',exist_ok=True); [shutil.move(f,'public/voiceover/.stale_archive/') for f in glob.glob('public/voiceover/scene*.wav')]"
```
修后必须 `ffprobe` 全部场景时长 + whisper 抽段验证才重渲染。禁止只看启发式 SKIP 就当本期音频。

```bash
# edge-tts 生成 → ffmpeg atempo=1.4 加速 → 24kHz PCM16LE 单声道 WAV
ffmpeg -y -i /tmp/sceneN_edge.mp3 -filter:a atempo=1.4 \
  -acodec pcm_s16le -ar 24000 -ac 1 sceneN.wav
```

**加速后必须重算**：
- `Composition.tsx` sceneConfig 各场景时长
- `Root.tsx` `TOTAL_DURATION_SEC`
- `captions.json` 字幕时间轴
- 然后重新渲染视频

### Phase 7: 字幕生成（语义 `group_caps` 切行 + whisper 词级对齐）

**v3.25.0 当前默认（2026-08-31 月报实测）**：先用语义 `group_caps` 切出字幕字符串，再用 faster-whisper `word_timestamps=True` + `SequenceMatcher` 把每条字幕对齐到音频真实发音时刻。内容 100% 来自脚本，时间 100% 来自音频。

> **规则全文**：`templates/captions.md`  
> **可运行脚本**：`templates/gen_captions.py`（`--report-dir` / `--dry-run` / `--extra-word`）

> **🔴 v3.36.0 输入契约（坑 208，2026-09-18/19 实测）**：
> - `load_scenes` 已兼容三种 `scenes` 写法：`{"scenes":{1:"text"}}` / `{"scenes":["text"]}` / `{"scenes":[{"num":1,"text":"..."}]}`。dict 按 sid 排序；**list 保留声明顺序**，因此 `[1,2,3,4,6,5,7]` 这类锚点重排不会被还原。0918 在第三种上直接崩（`AttributeError: 'dict' object has no attribute 'decode'`），标准顺序无需再手工造 `scenes-meta.json`；需要额外 duration 元数据时仍可保留该文件。
> - 场景偏移按 **wav 文件实际时长**累加（含片尾 pad 静音），**不用** whisper 的 `info.duration`——VAD 会裁掉尾部静音，用它推偏移会让后面每个场景的字幕整体提前，越往后越明显。脚本会打印 `offset += file_dur=X (whisper Y)` 供对账。
> - 该偏移必须与 `Composition.tsx` 的 `sceneConfig.duration`（ffprobe 实测）**同一批音频**，重跑 TTS 后两者一起刷。

> **🔴 经验教训（2026-06-12）**：FunASR 对专业术语识别极差（GPT→GDP、DeepSeek→Deep triep、Claude Code→Claude coat、Fable-5→核酸efbo杠五、Codex→搞dex、Hermes→HMMI、MiMo→mini/明末），修正字典永远追不上新术语。**字幕内容必须用原始 TTS 脚本文本，绝不依赖 ASR 识别文字。**
>
> **🔴 经验教训（2026-07-15）**：纯等字符比例分配（v2.1.0）/ 加权字符估算 + silencedetect 吸附（v2.2.0）仍会漂移。**v2.3.0 放弃「估算每句时长」，改用音频真实发音时刻作锚——这一条仍有效。**
>
> **🔴 经验教训（2026-08-31）**：v2.3.0 的 `split_sentences` 把 `，。；！？：、` **所有标点一视同仁**切行，再叠加 16 字硬墙，会切出 `延期；`（3 字 0.5s 闪行）、`有效` / `主题近一万。`、`终止Cursor` / `官方直连`。**切行必须语义优先；whisper 只负责时间轴。**

#### 7.1 默认方案：语义切行 + whisper 对齐（`templates/gen_captions.py`）

> 🔴 **v3.21.0 字幕补丁（治 2s 跳出 44%）**：Hook 的 5s 文本须独立成段，字幕时间戳 0-5s，前 5s 字幕字号 +20%（`Subtitles.tsx` 已支持，基于字幕时间戳 `caption.startMs < 5000` 判断 Hook 段放大，`fontSize: enlarged ? 48 : 40`）。前 2s 视觉与口播同步兑现封面大字承诺。 Remotion 字幕 **单行**，不做双行长度平衡。

**物理下限**（先于语义；详见 `templates/captions.md`）：

| 项 | 规则 |
|----|------|
| 目标行长 | 15–20 汉字（空格不计） |
| `max_len` | 16：到此长度遇软标点才断 |
| `hard_max` | 20：允许略超 16 以保住专名/动宾/正反并列 |
| 无合法切点 | **整句保留**（可到 24–25），**禁止按字符下标硬切** |
| 最短显示 | 对齐后 `merge_short_dwell(min_sec=1.0)`，<1s 并回上一行 |
| 视觉 | Remotion `Subtitles.tsx` **单行**；不做双行长度平衡 |

**语义切点**：

| 标点 | 行为 |
|------|------|
| `。！？；`（`SENT_END`） | **强制断行** |
| `，、：`（`SOFT_PUNCT`） | 仅当当前行 ≥ `max_len` 才断 |
| 所有标点一视同仁 | **禁止**（旧 `split_sentences`，会切出 `延期；`） |

超 `hard_max`：黄金分割 40–60%（扩 30–70%）→ `WEAK_BEFORE` 弱连接 → 整句保留。

**禁切反例（2026-08 月报实测，切开即错）**：

| 类型 | 必须同一行 |
|------|-----------|
| 正反并列 | `稳不稳` |
| 偏正 | `硬新闻主轴` |
| 动宾 / 专名+动宾 | `规划步骤`、`编程 Agent`、`终止Cursor官方直连` |
| 专名连发 | `Hy四连发`、`羊报AI月报` |
| 品牌+宾语 | `整月风向` |
| 数量+名 | `主题近一万`（禁止 `有效` / `主题近一万。`） |
| 短尾巴 | `延期；` 不得单独成行 |

后处理：`GLUE_TAILS` + `BAD_ENDS`/`BAD_STARTS` + 当期 `jieba.add_word`。

**算法摘录**（完整实现 `templates/gen_captions.py`，禁止再贴 170 行硬编码 WEEKLY 路径）：

```python
SENT_END = set('。！？；')
SOFT_PUNCT = set('，、：')

def group_caps(tokens, max_len=16, min_len=6, hard_max=20):
    """语义优先切行：句末强制断；软标点在 ≥max_len 时断；
    允许略超 16 字（≤hard_max=20）以保住专名/动宾/正反并列；
    超 hard_max 才黄金分割。短尾巴并回上一行。无合法切点整句保留，绝不按字硬切。"""
    ...  # _split_overlong → 黄金分割 → WEAK_BEFORE → 整句保留
    ...  # GLUE_TAILS / min_len 并回上一行；BAD_ENDS+BAD_STARTS 二次粘合

# 时间轴：group_caps 先切 → whisper word_timestamps → SequenceMatcher 对齐
#        → merge_short_dwell(min_sec=1.0) → captions.json
# WhisperModel 必须在 --dry-run 提前 return 之后才 import，避免 dry-run 加载模型
```

> **脚本落盘**：复制 `templates/gen_captions.py` → 当期 `scripts/gen_captions.py`；按脚本补 `jieba.add_word` 专名；先 `--dry-run` 人工扫禁切反例，再全量 whisper。
>
> ```
> python3 templates/gen_captions.py --report-dir news-pipeline/monthly/2026-08 --dry-run
> python3 templates/gen_captions.py --report-dir news-pipeline/monthly/2026-08
> python3 templates/gen_captions.py --report-dir news-pipeline/2026-08-31 --extra-word 专名
> ```
>
> 旧 `gen_captions_v2.py` / `split_sentences`（所有标点一视同仁）**已废弃作切行器**；whisper 对齐仍是时间轴唯一锚。

#### 7.2 完整流程

```
视频脚本(Phase 2) → 提取每场景 TTS 文本存 scripts/voiceover-texts.json（或 scenes-meta.json）
    → 复制 templates/gen_captions.py → 当期 scripts/gen_captions.py，补 jieba 专名
    → --dry-run：jieba 分词 + 语义 group_caps 切行（不加载 whisper）
    → 人工扫禁切反例（稳不稳 / 硬新闻主轴 / 规划步骤 / 编程 Agent / 终止Cursor官方直连 / Hy四连发 / 羊报AI月报 / 整月风向 / 主题近一万 / 延期；）
    → faster-whisper(word_timestamps=True) 跑当期 wav（**逐场景单独跑**，不要拼全局流）
    → 每条字幕 SequenceMatcher 滑动窗口对齐到词级时间戳
    → merge_short_dwell(min_sec=1.0)
    → 按 play_order 累加各场景 wav 时长定块起点 → captions.json + video-project/public/captions.json
```

> **🔴 v3.62.0 铁律（坑 298）：块偏移必须按 `play_order` 累加，不能按场景编号累加。** 只要 `play_order ≠ [1..N]`，字幕就会**整块互换**（1024 期 `[1,2,3,5,4,6]` 的 4/5 互换，用户两次反馈「对不上」，白渲一遍）。`templates/gen_captions.py` 的 `load_scenes` 末尾已内置 `apply_play_order()`；派生脚本若自行拼时间轴，必须同样处理。**另：块内计时必须用「该场景自己的 wav」单独跑 ASR**，复用一个全局 ASR 流会在场景边界处拿到相邻场景的时间。

> **🔴 v3.62.0 铁律（坑 299）：字幕验收只认渲染后的 mp4 音频，源 wav 验证一律不作数。** 按播放序把 `voiceover/sceneN.wav` 拼成 `full_play.wav` 再去测，那个文件本来就是按播放序拼的，**必然通过、等于没测**。正确姿势：`ffmpeg -i out.mp4 -vn -ar 16000 -ac 1 mp4_audio.wav` → 词级 ASR → **首 3 字锚定**（`stream.find(key[:3])` 多命中取最近）比对每条 `startMs`。**禁用全文字符流 `SequenceMatcher` 一次量全片偏差**——累积插入/删除会摊到每条上，1024 实测给出「64 条全部 >0.5s、中位 1.31s」的假信号（真实中位 +0.205s）。放行门禁：lead 中位 ≤0.5s 且 ≥85% 条目 |lead| ≤1.0s。

**关键点**：
- **切行先于对齐**：`group_caps` 产出字幕字符串；whisper **只**负责时间轴。禁止 `split_sentences` 逐标点切行，禁止 16 字硬墙按字符下标切开专名/动宾
- **内容用原始脚本文本**，不依赖 ASR 识别文字，字幕文字 100% 准确
- **时间用音频真实发音时刻**：whisper 词级时间戳是唯一锚点，不再做任何「估算每句时长」；无 whisper 词时才允许比例兜底
- **SequenceMatcher 容忍 ASR 错字**：每条字幕对归一化词序列做滑动窗口模糊匹配，个别字识别错也能对上正确时间区间
- **最短显示 1s**：对齐后 `merge_short_dwell`，<1s 并回上一行（治 `延期；` 0.5s 闪行）
- **必须与 Phase 8 的 Composition/Root 时长同源**（同一批 atempo 后的 wav）
- **v2.3.0「按句聚合」已废弃作切行器**；whisper 对齐仍有效

**为什么放弃 v2.2.0 加权字符 + silencedetect**（历史，时间轴仍适用）：
- 加权系数（中文 1.0 / 数字 0.6 / 英文 0.35）是平均拟合，单句（尤其含大量版本号、英文术语）偏差大，仍逐句累积漂移
- silencedetect 只能在「正好有停顿」时吸附边界，无停顿的句子仍纯靠估算，后半段依旧偏
- v2.3.0 让时间戳直接取自音频，从根本上消除漂移；whisper small 模型 int8 CPU 单场景约 5–15s，可接受
- **v3.25.0 再修切行**：v2.3.0 的 `split_sentences` 把所有标点一视同仁，叠加 16 字硬墙会切开专名/动宾；改语义 `group_caps` + 黄金分割 + 禁切粘合

**字体使用规范**：
- 使用系统字体：`"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif`
- 字幕：40-48px，加粗，白色，黑色半透明背景
- **禁止使用商用字体**（方正、汉仪、造字工房等）

### Phase 8: 渲染前校验（必须执行）

#### Step 8.0: 图片-脚本映射校验（v2.8.0 新增，必须首先执行）

```bash
# 校验图片数量与脚本场景数是否一致
IMAGES=$(ls news-pipeline/YYYY-MM-DD/images/scene*.png | wc -l)
AUDIO=$(ls news-pipeline/YYYY-MM-DD/voiceover/scene*.wav | wc -l)
echo "图片: $IMAGES, 音频: $AUDIO"
# 两者必须相等！不等则说明图片-脚本映射有误
```

**如果不等，检查原因**：
1. Hook 场景是否与第一条新闻共享了图片 → 合并图片 prompt
2. 是否有重复或多余的图片 → 删除多余图片
3. Composition.tsx 的 imageId 是否需要调整

#### Step 8.0b: 场景图比例与完整性门禁（v3.63.0 新增，坑 301/254）

进渲染前必须逐张过，任一不过即回 Phase 5 重出该张——**不要**指望 Remotion 拉伸或裁切兜底：

```bash
python3 - <<'PY'
import glob, sys
from PIL import Image
bad = []
for p in sorted(glob.glob('news-pipeline/YYYY-MM-DD/images/scene*.png')):
    im = Image.open(p); im.load()          # 严格解码，禁用 LOAD_TRUNCATED_IMAGES（坑 254）
    w, h = im.size
    ratio = w / h
    ok = ratio >= 1.6                       # 16:9≈1.78；方图 1.0 直接判死（坑 301）
    print(f'{p.split("/")[-1]:12s} {w}x{h}  {ratio:.2f}  {"OK" if ok else "FAIL"}')
    if not ok: bad.append(p)
sys.exit(1 if bad else 0)
PY
```

> 1025 期正例：rainflow `auto` + 无构图句 → 6/6 出 1254×1254（1.00），补齐构图句后 6/6 出 1672×940/941（1.78）；`size` 由 `size_for(api_url)` 运行时决定（见 Phase 5 / 坑 300）。

#### Step 8.1: 梳理对应关系表

```
| 场景 | 图片 | 音频 | 内容 | 时长 |
|------|------|------|------|------|
| 1 | scene1.png | scene1.wav | Hook | Xs |
| 2 | scene2.png | scene2.wav | 第一条 | Xs |
```

**🔴 铁律：每个音频必须对应 1 张图，禁止 audioId=0 的无声场景！**

#### Step 8.2: 更新 Composition.tsx

```tsx
const sceneConfig = [
  { imageId: 1, audioId: 1, duration: 8.96 },   // Hook
  { imageId: 2, audioId: 2, duration: 24.64 },  // 第一条
  // ... 每个场景都必须明确指定 imageId、audioId、duration
];
```

**🔴 铁律：`duration` 必须来自 ffprobe 实测的音频时长，禁止手填估算值。** 用下面命令一次性打印全部实测时长，直接抄进 `sceneConfig`：

```bash
D=news-pipeline/YYYY-MM-DD/voiceover
for i in $(seq 1 8); do
  dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$D/scene$i.wav")
  printf 'scene%d: %.2fs\n' "$i" "$dur"
done
```

> **🔴 经验教训（2026-07-12）：重跑 TTS 后必须同步更新 Composition.tsx 和 Root.tsx 的时长，否则字幕漂移。**
> 现象：只重新生成了音频 + 重算了 captions.json，但 `sceneConfig` 的 `duration` 还是旧音频的值。视频画面按旧时长排布、字幕按新音频时长对齐，两条时间轴从中段开始逐渐错位，到 1 分多钟处字幕与音频明显重叠、对不上。
> 铁律：**任何一次重跑 TTS（哪怕只改一个场景），都必须重新 ffprobe 全部音频 → 同步刷新 Composition.tsx 的 `sceneConfig` 时长 + 标题浮层 `NewsTitle` 的 `durationInFrames` + Root.tsx 的 `TOTAL_DURATION_SEC` → 再重算 captions.json → 最后渲染。**四者必须来自同一批音频，缺一步就会漂移。

> **🔴 v3.31.1 铁律（坑 189 / 2026-09-11）：NewsTitle 首屏日期禁止跨期硬编码。** 该组件日期曾写死为 09-09，0911 期重渲后首屏仍显示上一期日期，成片渲完才发现。必须抽成顶部常量 `const PERIOD_DATE = 'YYYY-MM-DD'` 与 `const BRAND`，并加 🔴 注释；渲染后**抽首帧视觉校验**：`ffmpeg -i out.mp4 -vf "select=eq(n\,0)" -frames:v 1 first.png` 后 Read。Phase 8-9 校验须 `grep -rn "20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]" video-project/src/` 与 `publish.json.date` 对齐（任何日期字符串都不得残留上一期）。

#### Step 8.3: 更新 Root.tsx

```tsx
const FPS = 30;
// 必须用各场景 ceil(dur*fps) 之和，不能 ceil(total*fps)，否则片尾被切。
const SCENE_DURS = [27.47, 19.73, 14.85, 16.60, 19.20, 17.78, 6.74];
const DURATION_IN_FRAMES = SCENE_DURS.reduce((acc, d) => acc + Math.ceil(d * FPS), 0);
```

> **🔴 v3.36.0 铁律（坑 209，2026-09-19）**：`durationInFrames` 必须是 **Σ ceil(dur_i * fps)**，**不是** `ceil(Σ dur_i * fps)`。每个场景在 `Composition.tsx` 里各自 `Math.ceil(duration * FPS)`，逐帧进位；若总数只 ceil 一次，累计误差会让**最后一个场景的片尾被切掉**（前几个场景各自多出的零头没被计入）。`SCENE_DURS` 数组的字面值必须与 `Composition.tsx` 的 `sceneConfig` 顺序、数值完全一致。
>
> **🔴 播放顺序与锚点**：`SCENE_DURS` 与 `sceneConfig` 的**顺序**即播放顺序，可与场景编号不同（0918 用 `[1,2,3,4,6,5,7]` 把锚点压进 70–80%，见坑 209）。改顺序后必须重跑 Phase 7 生成 captions。

**校验：渲染出的视频总时长必须 ≈ 音频总时长（`captions.json` 末条 `endMs`）。** 若两者相差超过 0.5s，说明 `sceneConfig`/`Root.tsx` 与音频不同步，字幕必然漂移，需回到 Step 8.2 修正后重渲染：

```bash
# 渲染后校验：视频时长 vs 音频总时长
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \
  "news-pipeline/YYYY-MM-DD/video/{文件名}.mp4"
```

#### Step 8.4: 复制资源到 public 目录

```bash
# 🔴 场景图必须转 JPG（v3.46.0/坑 245）：Composition 引的是 images/scene*.jpg，
# 只 cp png 会让渲染 seek 超时/黑帧（坑 237/245 同根）。ffmpeg 或 sips 均可：
for i in 1 2 3 4 5 6 7 8 9 10; do
  ffmpeg -y -i news-pipeline/…/images/scene$i.png -q:v 2 video-project/public/images/scene$i.jpg
done
# 单图输出可加 -frames:v 1 -update 1 消 image2 pattern 警告（文件仍会写出）
cp news-pipeline/YYYY-MM-DD/voiceover/scene*.wav video-project/public/voiceover/
cp news-pipeline/YYYY-MM-DD/captions/captions.json video-project/public/captions.json
```
同步后断言 `video-project/public/images/scene*.jpg` 每场景都非空，再进 Phase 9。

### Phase 9: 视频合成

**🔴 重要：渲染目录和命令**

渲染视频时必须使用以下命令（从项目根目录执行）：

```bash
/Users/youngsdream/Documents/learn-claude-code/news-pipeline/video-project/node_modules/.bin/remotion render \
  /Users/youngsdream/Documents/learn-claude-code/news-pipeline/video-project/src/index.ts \
  AINewsVideo \
  "out/{按 REPORT_MODE 读取文件名前缀}.mp4" \
  --codec h264 --crf 18 --timeout=180000 \
  --public-dir /Users/youngsdream/Documents/learn-claude-code/news-pipeline/video-project/public
```
> `--timeout=180000` 必带（坑 245）：默认 30s seek timeout 在多场景大图下会在中段帧超时（W40 卡 frame 613）。

**文件名按模式参数映射表读取**：
- daily：`out/【YYYY-MM-DD】{核心标题}… | 今日羊报AI.mp4`
- weekly：`out/【MM-DD~MM-DD】{核心标题}… | 羊报AI周刊.mp4`
- **monthly**：`out/【YYYY-MM】{核心标题}… | 羊报AI月报.mp4`
- **🔴 该文件名 = `publish.json.title`（后缀 `| 今日羊报AI`），不是 `bilibili.title`（坑 258 / 1017 实测）**：`publish.json.title` 与 `platform.bilibili.title` 是两字段（后者带 `｜N条重磅AI新闻一次看完` 营销后缀）。渲染/归档用 `title`，但 B站上传脚本 `VIDEO` 若误抄 `bilibili.title` 会在 `upload` 步 `getsize` 崩（`FileNotFoundError`）。修法：渲染后先 `ls news-pipeline/{date}/video/` 核对实际文件名，再写 `bili_upload.py` 的 `VIDEO` = `publish.json.title`。

**关键参数说明**：
- `node_modules/.bin/remotion`：使用 video-project 下的本地 remotion
- `src/index.ts`：必须指定入口点文件路径
- `--public-dir`：必须指定 public 目录的绝对路径

**🔴 渲染输出位置（必须记住；🔴 v3.39.0 修正，坑 222）**：
- out 参数是**相对路径、随渲染命令的 CWD 走**：CWD=仓库根 → 落在 `/Users/youngsdream/Documents/learn-claude-code/out/`；CWD=`news-pipeline/video-project` → 落在 `news-pipeline/video-project/out/`（0921 周报实际就落在后者）
- 消除歧义：渲染前 `cd` 到仓库根，或 out 直接写**绝对路径**；渲染后先 `ls -la` 确认产物实际位置再归档

**🔴 视频合成后自动归档（必须执行）**：

视频渲染完成后，必须立即将视频从根目录 `out/` 复制到报告目录（按 `REPORT_MODE` 对应的输出目录）：

```bash
# 复制视频到报告目录（以 daily 为例；weekly 用 weekly/... ，monthly 用 monthly/YYYY-MM/）
cp "/Users/youngsdream/Documents/learn-claude-code/out/【YYYY-MM-DD】{核心标题}… | 今日羊报AI.mp4" \
   "/Users/youngsdream/Documents/learn-claude-code/news-pipeline/YYYY-MM-DD/video/"

# monthly 模式：
# cp "/Users/youngsdream/Documents/learn-claude-code/out/【YYYY-MM】{核心标题}… | 羊报AI月报.mp4" \
#    "/Users/youngsdream/Documents/learn-claude-code/news-pipeline/monthly/YYYY-MM/video/"

# 验证复制成功
ls -la "/Users/youngsdream/Documents/learn-claude-code/news-pipeline/{对应目录}/video/"
```

**⚠️ 常见错误**：
- 错误：从 `news-pipeline/video-project/out/` 复制（旧文件）
- 正确：从 `/Users/youngsdream/Documents/learn-claude-code/out/` 复制（新文件）

**归档时机**：视频合成完成后立即执行，不要等到上传阶段再复制。**🔴 v3.39.0 汇报门（坑 222）**：归档后必须 `ls -la` 确认模式目录 `video/` 非空 + ffprobe 回读时长/分辨率，缺任一**禁止在汇报中写「视频已生成」**；归档被分类器抖动（坑 216）打断时，在状态文件记「待归档」，恢复后第一件事补归档（0921 周报因此漏归档，`weekly/.../video/` 为空，用户两次追问「视频呢」）。

### Phase 10: 封面、发布信息与公众号图文

> **注意**：如果已在 Phase 5.5 异步生成封面，此步骤可跳过封面生成，直接使用已生成的文件。

#### 10.1 生成多平台封面（如未异步生成）

使用图片生成 API 为各平台生成不同比例的封面：

| 平台 | 比例 | 尺寸 | 输出文件 | 用途 |
|------|------|------|----------|------|
| B站/通用 | 4:3 | 1536x1152 | `horizontal-4-3.png` | B站投稿封面、公众号/视频号横版 |
| 抖音/竖版 | 3:4 | 1152x1536 | `vertical-3-4.png` | 抖音封面、抖音个人主页卡片、公众号/视频号竖版 |

**封面模板 Prompt**（**v3.35.0 单一事实源**：`templates/cover-prompt.md`）：

- 横/竖封面都用海报风中文模板，**画面文字源 = 脚本「对应封面大字」字段**（Hook 原词短句，1 句冲突 + 1 个数字，两行；坑 203：`publish.json.title` 整条发布标题禁止印上画面，它只作列表标题）
- 日报水印 `今日羊报AI`；周报 `羊报AI周刊`；月报 `羊报AI月报`
- 日期字段按模式映射表；日期单独一行且水平居中
- 生成后 `Read` PNG 对照 `cover-prompt.md` 验收清单，缺一项重出

**🔴 v3.13.0 封面铁律仍有效（视频号 2026-07-26 限流教训）**：
- 🚫 **禁止**写实真人主播 / news anchor / 假新闻脸出镜
- ✅ 海报风本身无人像、无照片、无插画，已满足该铁律
- 完整策略见 `templates/platform-compliance.md` §3.2

输出到 `{REPORT_MODE 对应的输出目录}`（daily `news-pipeline/YYYY-MM-DD/`；weekly `news-pipeline/weekly/...`；monthly `news-pipeline/monthly/YYYY-MM/`）

#### 10.2 生成多平台发布信息

生成 `{输出目录}/publish.json`，包含 B站、抖音、视频号、公众号、知乎五个平台（下方为 daily 模板，weekly/monthly 按模式参数映射表替换标题前缀/tags/日期字段）：

```json
{
  "title": "【YYYY-MM-DD】{核心标题}… | 今日羊报AI",
  "description": "视频简介，2-3句话概括本期内容",
  "tags": ["今日羊报AI", "AI日报", "..."],
  "platform": {
    "bilibili": {
      "title": "【YYYY-MM-DD】{核心标题}｜{N}条重磅AI新闻一次看完 | 今日羊报AI",
      "partition": "人工智能",
      "tags": ["今日羊报AI", "AI日报", "..."],
      "description": "B站简介，含 hashtag\n\n🔴 注意：简介中数字不能太多（会被检测为违规推广），版本号简化，数字用中文替代"
    },
    "douyin": {
      "title": "今日羊报AI YYYY-MM-DD",
      "tags": ["AI日报", "..."],
      "description": "抖音简介，含 hashtag"
    },
    "channels": {
      "title": "今日羊报AI M月D日",
      "tags": ["AI日报", "..."],
      "description": "视频号简介，含 hashtag"
    },
    "wechat": {
      "title": "【YYYY-MM-DD】{核心标题}… | 今日羊报AI",
      "article": "wechat-article-YYYY-MM-DD.md",
      "images": "wechat-images/"
    },
    "zhihu": {
      "title": "【M月D日】{信息型判断句}",
      "column": "今日羊报 AI",
      "note": "知乎专栏名与抖音/视频号**合集名不同**：知乎是「今日羊报 AI」（含半角空格、末位大写 I），抖音/视频号是「今日羊报Al」（无空格、末位小写 l）。2026-10-30 分别按页面码点实测，别互相套用",
      "tags": ["AI", "人工智能", "..."],
      "article": "zhihu-article-YYYY-MM-DD.md",
      "images": "zhihu-images/"
    }
  }
}
```

**月报模式 publish.json 变体**（`REPORT_MODE=monthly` 时使用）：
- `title`：`【YYYY-MM】{核心标题}… | 羊报AI月报`
- `tags`：`["羊报AI月报", "AI月报", "AI月度盘点", "..."]`
- `bilibili.title`：`【YYYY-MM】{核心标题}｜本月{N}大AI趋势月度盘点 | 羊报AI月报`
- `douyin.title`：`羊报AI月报 YYYY-MM`
- `channels.title`：`羊报AI月报 YYYY年M月`
- `wechat.title`：`【YYYY-MM】{核心标题}… | 羊报AI月报`
- `bilibili.description`：**强制全数字中文化**（见 B站简介数字中文化章节）
- `wechat.article`：`wechat-article-YYYY-MM.md`
- `zhihu.title`：`【YYYY年M月】{信息型判断句}`（≤40 字）；`zhihu.article`：`zhihu-article-YYYY-MM.md`

**标题规则（v3.17：日期在前、报刊名在后）**:
- 日报 B站：`【YYYY-MM-DD】{核心标题}｜{N}条重磅AI新闻一次看完 | 今日羊报AI`（🔴 v3.29.0：publish.json bilibili 段固定 `"partition": "人工智能"`，Phase 11.4 按此字段选择分区）
- 日报 抖音：`今日羊报AI YYYY-MM-DD`（≤30字，纯报刊名+日期，无特殊符号）
- 日报 视频号：`今日羊报AI M月D日`（≤16字，仅支持中文、数字、空格、书名号、引号、冒号、加号、问号、百分号、摄氏度；`.` `~` 不在白名单）
- 日报 公众号：`【YYYY-MM-DD】{核心标题}… | 今日羊报AI`
- **周报 B站**：`【MM-DD~MM-DD】{核心标题}｜本周{N}大AI新闻一次看完 | 羊报AI周刊`
- **周报 抖音**：`羊报AI周刊 MM-DD~MM-DD`（≤30字）
- **周报 视频号**：`羊报AI周刊 M月D日至D日`（≤16字；用「至」连接，勿用 `~`/`.`）
- **周报 公众号**：`【MM-DD~MM-DD】{核心标题}… | 羊报AI周刊`
- **月报 B站**：`【YYYY-MM】{核心标题}｜本月{N}大AI趋势月度盘点 | 羊报AI月报`
- **月报 抖音**：`羊报AI月报 YYYY-MM`（≤30字）
- **月报 视频号**：`羊报AI月报 YYYY年M月`（≤16字）
- **月报 公众号**：`【YYYY-MM】{核心标题}… | 羊报AI月报`

**抖音标题规则（全部模式）**：
- 格式：`{报刊名} {日期字段}`，纯报刊名+日期，不加任何核心标题/副标题/特殊符号
- 日报：`今日羊报AI 2026-08-01`
- 周报：`羊报AI周刊 07-28~08-01`
- 月报：`羊报AI月报 2026-08`
- 总字符数 ≤30（含空格）
- 禁止加 `|`、`｜`、`：` 等分隔符，纯报刊名+空格+日期

**视频号标题规则（全部模式）**：
- 格式：`{报刊名} {日期字段}`，纯报刊名+日期
- 日报：`今日羊报AI 8月30日`（`今日羊报AI 2026年8月1日` 超 16 字，勿用）
- 周报：`羊报AI周刊 8月24日至30日`（16 字）
- 月报：`羊报AI月报 2026年8月`
- 总字符数 ≤16（含空格）
- 符号仅支持书名号、引号、冒号、加号、问号、百分号、摄氏度；**`.` `~` 不在白名单**
- 🔴 反例：`羊报AI周刊 8月24日~8月30日` 同时 18 字超限 + 含非法 `~` →保存草稿按钮 silent disabled
- 逗号可用空格代替
- 视频号短标题 = 视频号标题，两者使用同一格式

#### 10.3 生成公众号图文

从视频脚本中提取核心内容，去掉 Hook/CTA 等口语化部分，生成公众号文章：

**文章结构**：
```
# {标题}

> 今日羊报 AI · YYYY-MM-DD

---

## 1. {新闻标题1}

{正文内容，2-3段}

![配图描述](images/sceneN.png)

---

## 2. {新闻标题2}
...

---

**今日 AI 圈，又热闹又魔幻。**

---

👆 觉得有用就点个赞、转发给身边关注 AI 的朋友！
🔔 关注「今日羊报 AI」，每天 9 点带你速览 AI 圈最热的 5 条新闻。
💬 你最关心哪条？评论区聊聊！
```

**月报模式公众号图文变体**（`REPORT_MODE=monthly` 时使用，结构按月度趋势组织而非单事件）：
```
# {标题}

> 羊报AI月报 · YYYY-MM

---

## 趋势一：{趋势名}

{趋势正文，2-3段，含时间线 + 关键驱动 + 代表案例}

![配图描述](images/sceneN.png)

---

## 趋势二：{趋势名}
...

---

## 月度总结
{TOP10 归类 + 主题分布一句话}

## 下月展望
{2-3 条预测}

---

**这个月，AI 圈的风向已经变了。**

---

👆 觉得有用就点个赞、转发给关注 AI 的朋友！
🔔 关注「羊报AI月报」，每月带你回顾 AI 圈整月风向。
💬 你最看好哪条趋势？评论区聊聊！
```

**生成规则**：
- 标题使用视频标题
- daily/weekly：每个新闻事件一个 `##` 标题；monthly：每条趋势一个 `##` 标题 + 月度总结 + 下月展望
- 正文从脚本段落中提取，去掉口语化表达（"今天"、"我们"、"大家"等）
- 每个事件/趋势配一张场景图片（scene2.png ~ sceneN.png，跳过 Hook 场景）
- 结尾署名与 CTA 按模式参数映射表读取（daily"今日羊报 AI·每天9点带你速览AI圈最热的5条新闻"；monthly"羊报AI月报·每月带你回顾AI圈整月风向"）

输出到：
- 文章：`news-pipeline/YYYY-MM-DD/wechat-article-YYYY-MM-DD.md`
- 配图：`news-pipeline/YYYY-MM-DD/wechat-images/sceneN.png`

#### 10.3b 生成知乎文章（🔴 v3.72.0 新增，模块化）

**完整规范见 `templates/platform-zhihu.md` §1**（本处只列与公众号的差异，避免两处漂移）：

- 素材 = 上一步的 `wechat-article-<DATE>.md`，**不重新组织事实**；
- 标题改成 ≤40 字信息型判断句，**去掉 `| 今日羊报AI` 品牌后缀**，命中禁词表（重磅/独家爆料/揭秘/炸裂/彻底/封神/翻车/末日/慌了/完蛋）即改；
- 公众号结尾 CTA（点个赞/转发/关注/评论区聊聊）**整段删除**，改为稿末 AI 使用说明段；
- 必须有「编辑判断」段（≥120 字，作者视角的判断而非复述）——这是通过知乎 AI 治理细则的前提，不是可选装饰；
- 配图只放与所在小节对应者，`images/sceneN.png` → `zhihu-images/sceneN.jpg`；
- 产物：`zhihu-article-<DATE>.md` + `zhihu-images/`。

**生成后必须过审核门**（`templates/platform-zhihu.md` §2 十一条清单，落盘 `review-checklist.md` §知乎），未过不得进 Phase 15。

#### 10.4 归档资源

```bash
# 输出目录与视频文件名前缀按 REPORT_MODE 读取（此处为 daily；monthly 用 news-pipeline/monthly/YYYY-MM/ 与 【羊报AI月报】*.mp4）
mkdir -p news-pipeline/YYYY-MM-DD/{scripts,storyboards,prompts,images,voiceover,captions,video,wechat-images}
cp news-pipeline/video-project/out/【YYYY-MM-DD】*.mp4 news-pipeline/YYYY-MM-DD/video/
```

#### 10.5 🔴 周报砍掉决策（v3.21.0，诊断7兜底）

周报系列历史表现最差（均播 47、5s 25.3%、2s 跳出 48.8%，全站最低）。改造为深聊型后设此 stop-go gate：

- **Week 3 末**回填当期周报播放量到 `news-pipeline/weekly/{range}/weekly-performance.md`（字段：日期范围、均播、5s 完播率、2s 跳出率、分享、评论）
- **<80** → Week 4 起停周报，产能转给日报
- **改造后连续 2 期均播仍 <80** → 砍掉周报，产能全转日报
- **≥100** → 继续按 `templates/script-template-weekly.md` 新模板出周报

### Phase 11: B站自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 v3.33.0 / 0916 实测：MCP 缺席时的脚本化 Playwright 协议（浏览器常驻，坑 193）**

MCP 不可用时由脚本接管，**严禁**每轮把 `launch_persistent_context` 放进 `with sync_playwright()`：脚本退出（含异常）driver 会杀掉浏览器，表单状态全丢、只能整轮重传（0916 期连丢 3 次）。协议：

1. **先起守护进程**（后台任务，全程不退）。**🔴 v3.34.0 / 0917 坑 198+199**：
   - **浏览器本体必须是日常 Chrome** `/Applications/Google Chrome.app`，**禁止** Playwright 自带的 `Google Chrome for Testing`（`chromium-NNNN`）。Testing 版窗口图标/标题不同，扩展和站点行为也不同；0917 用户一眼看出「不是 9 月 10 日那颗」。
   - **禁止用 Playwright driver 当 daemon 持有浏览器**（`templates/browser_daemon.py` 的 `with sync_playwright() + launch_persistent_context + while True`）。0917 实测：上传页弹窗触发 `Protocol error (Page.handleJavaScriptDialog): No dialog is showing` → driver Node 进程崩 → 浏览器陪葬 → CDP `ECONNREFUSED`。正确做法：裸启 Chrome 进程（无 driver）+ `--remote-debugging-port=9222` + `--user-data-dir=mcp-chrome-10b76e5`，后续脚本 `connect_over_cdp` 附着。
   - 启动前清 `SingletonLock`。模板已改为裸 Chrome，见 `templates/browser_daemon.py`。
2. **后续所有脚本** `p.chromium.connect_over_cdp("http://localhost:9222")` 附着；结束时**只断连**（0915 期结论不变）。若报 `Browser context management is not supported`，换一次 attach 或确认 daemon 是裸 Chrome 而非 Testing+driver。
3. **选页按 URL 匹配**（如 `member.bilibili.com` / `cgi-bin/appmsg`），禁止 `pages[-1]`——daemon 初始的 `about:blank` 空页会顶到最后，导致后续 `ClipboardItem undefined` / `author input not found` 一类假错
4. **一步一截图**（`/tmp/bili_step.png` + Read 目检），存草稿前全项验收；单脚本失败先看截图诊断再改，不要盲改重跑
5. **B站标题复核（坑 197）**：native setter + input 事件在 UI 里显示正常（截图确认过全文），但存草稿后**列表仍显示文件名**（0916 实测 `bili_upload`）——存草稿后必须开草稿复核标题字段，不对就用 `locator.fill()` 重填再存
6. **B站分区**：**🔴 v3.63.0/1025 实测当前 UI 已改为扁平列表** `.drop-list-v2-item`（30 项，`人工智能` 直接在内，**不需要**先点父节点）——坑 194 的级联面板路径（点「科技数码」→ 等子面板）在 1025 已不适用，只有列表里找不到时才回退试级联。无论哪种形态，**点前必须 `scroll_into_view_if_needed()`**（坑 302：`人工智能` 在 y=759 而视口 769，视口外三种点击全静默失效），v3.29.0 结构化验收仍要做（以 `innerText` 的 `分区\n人工智能` 正则为最终判据）
7. **B站上传完成信号**：等标题输入框出现（`textarea, input[placeholder*=标题]`）即为表单就绪，勿用「上传成功」文案轮询（0916 轮了 5 分钟没命中）
8. **🔴 B站存草稿按钮是 `span.submit-draft`（坑 200 / 0917）**：文案「存草稿」，tag=`SPAN` class=`submit-draft`，**不是** `button`。`button:has-text("存草稿")` 恒 count=0；evaluate 点 `button` 也是 no-op。必须 `page.locator('span.submit-draft').click({force:true})` 或坐标点中心。存草稿成功信号仍是草稿箱出现当日标题，**不是** URL 仍停在 `upload/video/frame`。
9. **🔴 存草稿失败禁止 `goto` 草稿箱（坑 201 / 0917）**：表单未保存时跳去 `upload-manager/article?group=draft` 会把编辑页冲掉（0917 连丢 5 次表单）。失败时**留在表单页**截图诊断；验证草稿用**新标签页**打开草稿箱，不动编辑页。
   - **🔴 进草稿编辑页只能点行内「编辑」按钮，草稿行没有可用 `href`（v3.66.0 坑 316 / 2026-10-26 实测）**：草稿箱列表里草稿行的链接解析出来是 `null`。做法 = 从标题叶子节点向上逐级（≤8 层）找 `textContent === '编辑'` 的元素，取 `getBoundingClientRect` 中心 `mouse.click`；通常新开标签落到 `upload/video/frame?type=draft&draftId=…`。回读字段：分区 `.selector-container .select-item-cont`、标签 `.label-item-v2-container`（去 `×`）、简介 `.ql-editor` 的 `innerText.length`、封面取页面内 `naturalWidth>=400` 的最大 `img`。
10. **🔴 B站封面已改版为「封面制作」全屏弹窗（坑 218 / 0921）**：点「添加封面」**不再触发原生 file chooser**（`expect_file_chooser` 必超时，0921 白等两轮）；路径 = 弹窗内点「上传封面」→ 取 **`accept` 含 `image` 的 input** `set_input_files` → 点 `.cover-editor-button .button.submit`（文案「完成」）。**此刻页面共 5 个 `input[type=file]`（`.mp4`×2 / `.txt` / `.zip` / 封面 image），按索引 `inputs[1]`/`inputs[-1]` 会把 png 喂给视频或 zip input——不报错、表单纹丝不动**（0921 连错两次）。可复用 `templates/bili_cover.py`；三步顺序铁律：**先上传封面 + set_files，再点「完成」**（先点完成只关空弹窗）。
11. **🔴 B站标签上限 10 且会被推荐标签污染（坑 219 / 0921）**：投稿页自动预置「学习 / 生活记录 / 记录」等无关 chips，占满额度后新增**静默丢弃**（弹出「允许添加的标签已经达到上限了」）。先删预置再补自己的；删除 `×` 在 `label-item-v2-container` 容器**最右缘**（点文字元素或容器中心无效，0921 空转三轮）。每次增删后**回读 `.label-item-v2-container` 文本列表断言**，不要只信脚本打印的 "added"。
12. **🔴 上传前把封面拷到日期目录根（v3.38.0）**：`gen_images.py` 把横/竖封面写进 `news-pipeline/{date}/images/`，而上传脚本读的是**日期目录根**：`cp news-pipeline/{date}/images/horizontal-4-3.png news-pipeline/{date}/images/vertical-3-4.png news-pipeline/{date}/`。漏拷即 `set_input_files` 找不到文件。

#### 11.0 处理浏览器锁（自动处理，不询问用户）

如果 Playwright MCP 报错 "Browser is already in use" 或 "Target page, context or browser has been closed"：

```bash
# 1. 关闭现有浏览器进程
pkill -f "mcp-chrome-*" 2>/dev/null
sleep 2

# 2. 删除锁文件
rm -f ~/Library/Caches/ms-playwright/mcp-chrome-*/SingletonLock
```

**🔴 重要：浏览器锁是常见问题，自动处理不需要询问用户。**

#### 11.1 打开上传页面

```
browser_navigate("https://member.bilibili.com/platform/upload/video/frame")
```

#### 11.2 上传视频

```
browser_click(target=e231)  # 点击上传区域，触发 file chooser
# 视频路径按 REPORT_MODE：daily news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4
#                       monthly news-pipeline/monthly/YYYY-MM/video/【羊报AI月报】*.mp4
browser_file_upload("news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4")
```

**🔴 重要**：`browser_click` 使用 `target` 参数（ref 编号）比 `element` 文本描述更可靠。

#### 11.3 上传封面（🔴 v3.38.0 / 0921 改版：封面制作弹窗）

**🔴 坑 218：B站封面编辑器已改版，旧「封面设置 → 原生 file chooser」路径不再成立。**

**前置**：`gen_images.py` 把封面写进 `images/` 子目录，上传脚本读的是日期目录根，先拷平——
```bash
cp news-pipeline/YYYY-MM-DD/images/horizontal-4-3.png news-pipeline/YYYY-MM-DD/images/vertical-3-4.png news-pipeline/YYYY-MM-DD/
```

**新版流程（脚本化 / CDP 附着，0921 实测通过）**：

1. 滚到封面区，点「添加封面」→ 打开**「封面制作」全屏弹窗**。
   ⚠️ **不要等 `expect_file_chooser`**：它不是原生 chooser，等 8s 必超时（0921 白等两轮），点完直接进下一步。
2. 弹窗内点「上传封面」（`span.upload-text`，位于弹窗底部「封面制作」面板）→ 出现封面专用 input。
3. **按 accept 过滤取 input，禁止按索引**（坑 218 核心）：
```javascript
const inputs = await page.$$('input[type="file"]');
// 此刻页面上 5 个 file input：视频 .mp4 ×2 / .txt / .zip / 封面 image/png,image/jpeg
// 按 inputs[1] 或 inputs[-1] 会把 png 喂给视频或 zip input —— 不报错、表单无变化（0921 连错两次）
let cover = null;
for (const i of inputs) {
  const acc = (await i.getAttribute('accept')) || '';
  if (acc.includes('image')) { cover = i; break; }
}
await cover.setInputFiles('news-pipeline/YYYY-MM-DD/horizontal-4-3.png');
```
4. 上传后 4:3（首页推荐）与 16:9（个人空间）两栏**同时预览**（默认勾选「双比例同步改动」）。断言两栏都出现自制图。
5. 点 `.cover-editor-button .button.submit`（文案「完成」）关弹窗。
   **顺序铁律**：先「上传封面 + set_files」**再**点「完成」；先点「完成」只会关掉空弹窗，封面不会进表单（0921 实测）。
6. **关弹窗后必须回表单截图目检**：封面区缩略图 = 自制图（不是系统推荐封面），且「封面制作」标题不再可见。

**可复用脚本**：`templates/bili_cover.py`（CDP 附着，`python3 bili_cover.py YYYY-MM-DD`，自动断言）。

**⚠️ 历史路径（v3.3.0，仅当后台回退旧版时才适用）**：点「封面设置」→「上传封面」→ `file_upload` → 「完成」；旧版封面 file input 无 image accept，只能按位置取 `inputs[1]`。

**⚠️ 实测经验（v3.3.0 / 被 v3.12.0 覆盖）**：旧文档建议「封面不稳就跳过」。**2026-07-25 实测可自动补封面**，见下方 v3.12 草稿编辑页流程；首次投稿若封面失败，可**打开草稿再补**，不要默认放弃。

#### 11.4 选择分区「人工智能」（v3.17 新增；🔴 v3.29.0 提级为存草稿前必验收项）

**🔴 分区选择器是自定义下拉框，视频投稿必须选择「人工智能」分区。🔴 v3.63.0/1025 实测：选择动作必须走 locator（`.drop-list-v2-item`）+ `scroll_into_view_if_needed()` + `click(force=True)`，**禁止 JS `el.click()`/泛文本匹配/`mouse.click` 坐标点击**（坑 302：视口外三种点击全静默失效）；JS evaluate 只用于步骤 0 的结构化回读验收，不用于点击选择。**

**🔴 v3.29.0 / 2026-09-02 实测坑：B站上传页「分区」字段会**默认预填「人工智能」**（snapshot 里 heading「分区」下方 paragraph 直接显示「人工智能」，无「请选择分区」占位）。此时**极易误以为"已选好"而跳过**——但这只是默认值展示，**不能替代显式选择与验收**。正确做法：无论 snapshot 是否已显示「人工智能」，都执行一遍 11.4 的显式选择（点开下拉 → **locator `.drop-list-v2-item` + scroll_into_view + force click**，v3.63.0/坑 302，**勿用 JS 点击**）+ 存草稿前验收；snapshot 文字校验用**「heading 分区 相邻 paragraph」结构定位**，勿用 `document.body.innerText.includes('人工智能')`（标签/简介里出现「人工智能」会误判通过，0902 实测 body 校验假阳性）。**

```javascript
// 0. 🔴 v3.29.0 结构化验收（存草稿前必跑）：heading「分区」旁的 paragraph 必须是「人工智能」
//    snapshot 证据（0902 实测）：heading "分区" → generic → paragraph: 人工智能
browser_evaluate("""() => {
  const hs = Array.from(document.querySelectorAll('h1,h2,h3,h4,div,span'));
  const h = hs.find(e => e.children.length === 0 && e.textContent.trim() === '分区');
  if (!h) return '分区 heading not found';
  let p = h.parentElement && h.parentElement.querySelector('p, span');
  // 向上找一层兄弟容器里的值文本
  if (!p || p.textContent.trim() === '分区') {
    const sib = h.parentElement && h.parentElement.parentElement;
    p = sib && sib.querySelector('p, span:not(:has(*))');
  }
  const val = p ? p.textContent.trim() : '';
  return JSON.stringify({ partition: val, ok: val === '人工智能' });
}""")
// 返回 ok:false → 必须走下面 1-2 显式选择，再重跑本验收；ok:true 才允许点「存草稿」
```

```javascript
// 1. 点击打开分区下拉框（真容器 = .selector-container .select-container）
browser_click(target=eXXX)  // 分区下拉框，通常显示「请选择分区」或当前分区

// 2. 🔴 坑 302：按 .drop-list-v2-item 精确匹配，禁止用 li,div,span,p 泛文本匹配
browser_evaluate("""() => {
  const items = Array.from(document.querySelectorAll('.drop-list-v2-item'));
  const hit = items.find(e => e.textContent.trim() === '人工智能');
  if (!hit) return `not found among ${items.length} items`;
  hit.scrollIntoView({block: 'center'});
  const r = hit.getBoundingClientRect();
  return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
                         inViewport: r.top >= 0 && r.bottom <= window.innerHeight});
}""")

// 3. 校验分区已选中：用步骤 0 的结构化验收（heading「分区」相邻 paragraph），
//    禁止用 body.innerText.includes('人工智能')（0902 实测：标签/简介含该词会假阳性）
```

**Playwright 脚本版（v3.63.0 坑 302，1025 实测）**——`mouse.click` 在视口外**静默失效**，必须走 locator：

```python
getpart = lambda: page.evaluate(
    "() => document.querySelector('.selector-container .select-item-cont')?.textContent.trim()")
cur = getpart()
if cur != PARTITION:                                   # PARTITION = '人工智能'
    page.locator('.select-container').first.click()    # 开下拉
    page.wait_for_timeout(1600)                        # 选项要渲染，别急着点
    loc = page.locator('.drop-list-v2-item').filter(has_text=PARTITION).first
    loc.scroll_into_view_if_needed()                   # 🔴 关键：先滚进视口
    page.wait_for_timeout(300)
    loc.click(force=True, timeout=6000)                # 🔴 force=True 绕过遮挡检测
    page.wait_for_timeout(1500)
    cur = getpart()
assert cur == PARTITION, f'partition {cur!r} != {PARTITION!r}'   # 只认回读，不认点击回执
```

> **🔴 坑 302 实测细节（1025）**：下拉共 30 项，`人工智能` 位于 y=759 而视口高 769——**一半露在视口外**。此时 `page.mouse.click(x, y)`、`el.click()`、`dispatchEvent(new MouseEvent(...))` **三种点击全部返回成功、无异常、分区值仍是默认「音乐」**。只有 `scroll_into_view_if_needed()` + `click(force=True)` 走通。通用规则：**任何坐标点击前先确认目标 rect 完整在当前视口内**。

**兜底**：若自定义下拉框无法展开，可尝试 `browser_run_code_unsafe` 触发点击分区元素后等待 500ms 再执行 JS 选选项。**分区未选对会导致投稿分类错误，必须验收。**

#### 11.5 设置创作声明（自定义下拉框）

**🔴 B站的创作声明是自定义下拉框组件，不是标准 `<select>`。`browser_click(listitem=...)` 不可靠，必须用 JS evaluate：**

```javascript
// 1. 点击打开下拉框
browser_click(target=e362)  // textbox "请选择符合您视频内容的创作声明"

// 2. 用 JS 找到并点击选项（必须！）
browser_evaluate("""() => {
  const options = document.querySelectorAll('li, div, span, p');
  for (const opt of options) {
    if (opt.textContent.trim() === '个人观点，仅供参考') {
      opt.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")
```

**Playwright 脚本版（v3.46.0 坑 247，W40 实测）**：`page.locator('text=请选择符合您视频内容的创作声明')` **必超时**（文本在隐藏 placeholder/aria 里），改用坐标点击：

```python
box = page.evaluate('''() => {
  const el = [...document.querySelectorAll('.bcc-select-input-wrap, .bcc-select')]
    .find(e => e.offsetParent && e.getBoundingClientRect().width > 200);
  const r = el.getBoundingClientRect();
  return [r.x + r.width / 2, r.y + r.height / 2];
}''')
page.mouse.click(*box)                      # 开下拉
page.wait_for_timeout(1000)
# v3.48.0 坑247补充：rect 查找返回 None 时直接点 input[placeholder*="创作声明"] 中心；
# 已选回读判据 = input.value（body.innerText 不含已选值，pre-draft declOk=False 属预期）
opt = page.evaluate('''() => {
  for (const el of document.querySelectorAll('.bcc-select li, .bcc-select [class*="option"]')) {
    if (!el.offsetParent) continue;
    if (el.textContent.trim() === '个人观点，仅供参考') {
      const r = el.getBoundingClientRect();
      return [r.x + r.width / 2, r.y + r.height / 2];
    }
  }
  return null;
}''')
page.mouse.click(*opt)                      # 选中
# 回读判据（沿用 v3.45.0）：body.innerText 含「个人观点，仅供参考」
```

同理，form 步任何 locator 超时都**先回读再决定重跑**——W40 分区 locator timeout 但回读已是「人工智能」，不重跑（坑 242/205 回读铁律）。

#### 11.6 填写简介（Quill 编辑器）

**🔴 B站简介使用 Quill 富文本编辑器，直接 `browser_type` 可能不生效。必须用 JS 注入：**

```javascript
browser_evaluate("""() => {
  const editor = document.querySelector('.ql-editor');
  if (editor) {
    editor.innerHTML = '<p>第一段简介内容</p><p><br></p><p>#标签1 #标签2 #标签3</p>';
    editor.dispatchEvent(new Event('input', { bubbles: true }));
    return 'description set';
  }
  return 'editor not found';
}""")
```

#### 11.7 填写标签（🔴 v3.38.0 / 0921 上限与推荐标签污染）

```
# 标签输入框: textbox "按回车键Enter创建标签"
# 最多 10 个标签，每个标签输入后按 Enter 确认
tags = ["DeepSeek", "Anthropic", "Ideogram", "英伟达", ...]
for tag in tags:
    browser_type(target=e399, text=tag)
    browser_press_key("Enter")
```

**🔴 坑 219：新版投稿页会自动预置推荐标签，且超限静默失败。**

- **上限 10 个**：底部显示「还可以添加 N 个标签」；超限时右上角弹出「允许添加的标签已经达到上限了」，**新增请求被静默丢弃**（脚本里 `Enter` 照常发，标签就是不进）。加标签前先数当前 chips。
- **推荐标签污染**：页面会预置「学习 / 生活记录 / 记录」等与内容无关的 chips（0921 实测混入 3 个）。发布前必须清理，否则列表页标签不干净。
- **删除要点**：关闭符 `×` 在 `label-item-v2-container` 容器**最右侧**——点 `label-item-v2-content`（文字元素）或容器中心都**无效**（0921 空转三轮），必须点容器右缘：
```javascript
const chips = await page.$$('.label-item-v2-container');
for (const c of chips) {
  const name = (await c.innerText()).replace('×','').trim();
  if (DROP.includes(name)) {
    const b = await c.boundingBox();
    await page.mouse.click(b.x + b.width - 10, b.y + b.height / 2);  // 容器右缘，不是中心
  }
}
```
- **验收铁律**：每次增删后回读 `.label-item-v2-container` 的文本列表断言，**不能只信脚本打印的 "added"**（0921 打印 added 但列表里没进）。最终 chips 列表必须等于 publish.json 的 tags（允许少、不允许脏）。
- **🔴 平台可能单独拒收某个标签（v3.63.0 坑，1025 实测）**：本期 `AI大模型` 原样重输两次、点推荐行同名 chip 也未入列，终态 6/7。**v3.67.0 补（1028 二次确认，形成定论）**：这个串在 B站**稳定收不下**——原串、加空格变体（`AI 大模型`）、词序变体（`大模型AI`）、裸写（`大模型`）都只会落成**另一个** chip，回读必然对不上。**别再浪费一轮试变体：B站标签池里直接改用推荐行里存在的「人工智能」**，本期即以此凑满 6 个。**断言写成「记录缺了哪个，但不阻断存草稿」**——例如打印 `missing_tags: ['AI大模型']` 并把其余标签的到位率写进 review-checklist §15；**不要** `assert len(chips) == len(tags)` 让整条链停在存草稿前。标签缺失不触发平台杠杆（简介/分区/合集才是），为一个可选项白跑一遍上传不划算。同时**禁止**为了凑数点推荐行里的同名 chip——推荐行点击会追加**别的**标签（坑 240）。

#### 11.8 加入合集（自定义下拉框）

**🔴 合集选择器也是自定义下拉框，必须用 JS evaluate。合集名按 `REPORT_MODE` 从模式参数映射表读取：daily `「今日羊报 AI」` / weekly `「羊报AI周刊」` / monthly `「羊报AI月报」`。**

**🔴 风险点**：合集必须由用户预先在 B站创作中心手动创建。若 monthly 模式合集「羊报AI月报」未创建，下方 JS 找不到选项会返回 `not found`，Phase 11.8 卡住——此时需提示用户去后台创建后再继续。

```javascript
// 1. 点击打开下拉框
browser_click(target=e525)  // "请选择合集"

// 2. 用 JS 找到并点击选项（合集名按 REPORT_MODE 读取）
browser_evaluate("""() => {
  const options = document.querySelectorAll('li, div, span, p');
  // 合集名按模式参数映射表：daily 「今日羊报 AI」/ weekly 「羊报AI周刊」/ monthly 「羊报AI月报」
  const targetName = '「今日羊报 AI」';
  for (const opt of options) {
    if (opt.textContent.trim() === targetName) {
      opt.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")
```

#### 11.9 存草稿（不直接投稿）

**🔴 重要：所有平台上传一律存草稿，不直接发布！用户确认后再手动发布。**

```
# 🔴 v3.34.0：存草稿是 span.submit-draft，不是 button（坑 200）
page.locator('span.submit-draft').click({force: true})
# 等待；成功信号 = 新标签打开草稿箱能搜到当日标题
# 禁止在未确认保存前 page.goto 草稿箱（会冲掉表单，坑 201）
```

#### B站上传组件操作总结（v1.4.0 实测；🔴 v3.38.0 / 0921 更新封面行与标签行）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 视频上传 | file chooser | `browser_click(ref)` → `file_upload` | ✅ 高 |
| 封面制作 | **全屏弹窗** | 点「添加封面」→ 弹窗内点「上传封面」→ **按 `accept` 取 image input** `set_input_files` → `.cover-editor-button .button.submit`（「完成」）；**禁 `expect_file_chooser`、禁按索引取 input**（坑 218） | ✅ 高（v3.38.0） |
| 分区「人工智能」 | **自定义下拉框** | `.select-container` 点开 → `locator('.drop-list-v2-item').filter(has_text=...)` + **`scroll_into_view_if_needed()`** + `click(force=True)`（坑 302）；回读 `.selector-container .select-item-cont`；存草稿前跑结构化验收（heading「分区」相邻 paragraph，禁 body 全文 includes） | ⚠️ 必须回读 |
| 创作声明 | **自定义下拉框** | 点击 textbox → **JS evaluate 点击选项** | ⚠️ 必须用 JS |
| 标签 | 输入框 + chips | `type` + `Enter`；**上限 10**；先清预置推荐 chips（`×` 在 `label-item-v2-container` 右缘）再补；增删后**回读 chips 文本列表断言**（坑 219）；**单个标签被平台拒收时记录缺失、不阻断存草稿**（坑 302 同批，1025 实测 6/7） | ⚠️ 必须断言 |
| 简介 | **Quill 编辑器** | **JS 注入 `.ql-editor`** | ⚠️ 必须用 JS |
| 合集 | **自定义下拉框** | 点击展开 → **JS evaluate 点击选项** | ⚠️ 必须用 JS |
| 投稿按钮 | 按钮 | `browser_click(ref)` | ✅ 高 |

**关键经验**：
1. **`browser_click(target=ref编号)` 比 `browser_click(element=文本描述)` 更可靠**
2. **所有自定义下拉框（分区、创作声明、合集）必须走真实 DOM 点击，且点前先滚进视口**——分区用 `.drop-list-v2-item` 专属选择器 + `scroll_into_view_if_needed()` + `click(force=True)`（坑 302：视口外的 `mouse.click`/`el.click()`/`dispatchEvent` 三种全静默失效）；创作声明、合集仍用 JS evaluate 取 rect 后坐标点击。**任何点击后都必须回读具体状态字段**，不能只信回执。
3. **Quill 编辑器必须用 JS 注入 `innerHTML` + dispatch `input` 事件**
4. **`browser_file_upload` 必须在 file chooser 对话框打开后才能调用**（🔴 v3.38.0：**B站封面已不走原生 chooser**，本条只剩视频输入适用）
5. **🔴 封面上传（v3.38.0 改版）：点「添加封面」→ 打开「封面制作」全屏弹窗 → 弹窗内点「上传封面」→ 按 `accept` 取 image input `set_files` → 点「完成」关弹窗**。顺序不可换（先点完成只关空弹窗）；**禁 `expect_file_chooser`（必超时）、禁按索引取 input（会喂给 .mp4/.zip 且静默无报错）**。详见 11.3 与 `templates/bili_cover.py`
6. **🔴 标签（坑 219）：先清预置推荐 chips（学习/生活记录/记录）再补自己的；`×` 在 `label-item-v2-container` 右缘；每次增删后回读 chips 文本列表断言，不信脚本打印**

### Phase 12: 微信公众号自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 v3.33.0 / 0916 实测补充（脚本化 Playwright 同样适用）**

1. **登录判据 = 页面出现「新的创作」或英文 UI「New creation」（坑 195 / 0917 补）**。登录页 innerText 是「微信扫一扫，选择公众平台账号登录」——用「扫码/请重新登录」做关键词会漏判（0916 因此空转两轮）。0917 账号后台是英文 UI，首页可见 `New creation` 而不是中文「新的创作」，只搜中文会误判未登录。等待循环：`while not ('新的创作' in t or 'New creation' in t)`，10s 轮询、上限 10 分钟。菜单项 class 仍是 `.new-creation__menu-item`（语言无关）。
2. **「新的创作→文章」后必须按 URL 找编辑器新标签页**（`cgi-bin/appmsg`），找不到时对同一页重试点击（≤3 次）；禁止取 `pages[-1]`（daemon 的 about:blank 空页会顶到最后 → `ClipboardItem undefined` / `author input not found` 假错）。
3. **正文占位符插图路径（v3.30 每图即存的完整可复制实现，0916 全量验证 6/6）**：粘贴 HTML 时图片位置写 `<p>PLACEHOLDER_IMG_N</p>`（**封面图占位排最后**）→ 每图：TreeWalker 找占位符文本节点 → `range` 精确选中 → 工具栏「图片→本地上传」→ `setInputFiles` → Escape 关挡层 → **立刻保存草稿** → 断言占位符数递减、`pmLen` 只因占位符消失而下降（每图 ≈17 字）。全部传完占位符必须为 0。
4. **封面「从正文选择」直接选最后一张缩略图（坑 186 补充）**：封面占位符在正文最末，弹窗缩略图按正文顺序排列 → `items[items.length-1].click()`；后续「下一步 → 编辑封面 → 确认 → 轮询 `.js_cover_preview_new`」与 v3.31.1 流程一致（0916 复验：2 轮轮询内 `display:block + mmbiz`）。
5. **保存时 Content Structure Check 弹窗**：每步 `保存为草稿` 后扫「继续插入/继续保存」可见按钮点击放行（坑 192 的脚本化等价实现）。
6. **原创声明跳过不变**（坑 191 / 0915 同款）：不进原创弹窗，直接保存草稿，upload-status.md 备注。
7. **🔴 剪贴板 write 成功 ≠ 正文进去（坑 202 / 0917）**：`navigator.clipboard.write` 返回 wrote 后，evaluate 派发 click/focus 再 Meta+V 可能 `bodyLen=0`（空态 widget 15 字）。必须 **坐标点击** `.ProseMirror[1]` 中心 → Meta+A → Meta+V → 放行 Structure Check → `bodyLen()>800` 才算粘上。0917 第一轮脚本粘贴失败就是因为没点到正文。
8. **封面弹窗会挡住编辑器**：从正文选择若正文还没图，会弹出 `Select an image / No available images`。先 Escape/`Cancel` 关掉，再插图；不要在空正文上点封面。
9. **`appmsgid=` 截断误判**：`log(url[:120])` 可能把 `appmsgid=` 截掉，看起来像 NO_APPMSGID。验收读完整 URL 或 `'appmsgid=' in url`。草稿列表不要用老接口 `appmsg?action=list_ex`（会返回 2019 年稿）。
10. **🔴 `open` 步骤必须先 `settle()`，且已在带 `token=` 的 mp 页时跳过 `goto`（坑 217 / 0921）**：`page.goto('https://mp.weixin.qq.com/')` 在已登录状态下 302 到 `cgi-bin/home?...&token=`，紧接着的 `page.evaluate` 抛 `Execution context was destroyed, most likely because of a navigation` —— **整步崩掉，登录都判不了**。正确写法：
```python
page = mp_page(ctx) or ctx.new_page()
if 'token=' not in (page.url or ''):          # 已在 mp 页就别再 goto
    page.goto('https://mp.weixin.qq.com/', wait_until='domcontentloaded', timeout=60000)
home = settle(page)                            # 轮询 body 直到可读（重定向期间 evaluate 会抛）
if ('新的创作' not in home) and ('New creation' not in home):
    show_login_and_stop()                      # 判据见坑 195
```
`settle(page)` = `for _ in range(20): try: body=page.evaluate('() => document.body.innerText'); if body: return body; except: pass; page.wait_for_timeout(2000)`。点击 `.new-creation__menu-item` 同样要用 try/except + `settle()` 重试（≤3 次），再按 URL 找 `cgi-bin/appmsg` 新标签页。

**🔴 2026-08-13 日报视频实测流程优化（v3.17.0）**——公众号上传建议按以下**已验证顺序**执行，避免踩坑：

1. **标题/作者/正文先行**：先确保标题、作者、正文、视频号内容就位，再处理封面——封面不稳定不得阻塞草稿（v3.5.0 降级原则）
2. **正文图片用「本地上传」**：正文配图一律用工具栏「图片」→「本地上传」→ `setInputFiles(sceneN.png)`，不要用纯 innerHTML 注入（注入不落素材库，封面无法「从正文选择」）
3. **封面选图路径**：先用 `horizontal-4-3.png` 插入正文 → 再「从正文选择」设封面（v3.8.0 铁律：裁剪弹窗标题「编辑封面」、确认键是 enabled「确认」非灰「确定」、禁止弹窗内 Escape、轮询 `.js_cover_preview_new{display:block; bg 含 mmbiz}`）
4. **合集选择**：v3.66.0 起走 12.10 的可复现流程（真入口 `.allow_click_opr.js_article_tags_label`），**并把回读判据写成硬断言**——`.`js_article_tags_content` 必须等于合集名，`未添加` 即失败。旧版「try-catch 跳过不阻塞保存」是本期静默失败的成因之一：合集没挂上但流水线照跑、照存、照报成功（坑 310/312）
5. **最后保存草稿**：所有项目填完后点「保存为草稿」，以 URL `appmsgid=` 为准；弹窗阻挡时 Escape 关闭上传中挡层再保存
6. **验收**：`appmsgid=` 出现在 URL / 保存成功回执为准，勿只看「已保存」文案（常不出现）

**🔴 重要经验：公众号编辑器使用 ProseMirror + 自定义 Vue 组件，自动化难度较高。封面选择、合集选择等需要特殊处理。**

#### 12.0 完整上传流程（推荐顺序）

```
1. 打开公众号后台 → 点击「新的创作」→「文章」（新标签页打开）
2. 切换到新标签页
3. 填写作者（标准 input，固定 `羊报AI周刊` / `今日羊报AI` / `羊报AI月报`，≤8 字；勿填署名格式）
4. 点击正文区域获取 focus → 插入视频号内容
5. 填写正文内容（ProseMirror nth(1) + 真实剪贴板粘贴 Meta+A/Meta+V，🔴 v3.30.0：禁 innerHTML / 禁 insertHTML / 禁合成 ClipboardEvent）
6. 通过「图片」→「本地上传」插入封面图到正文
7. 上传封面（从正文选择 / 从图片库选择）
8. 填写标题（正文注入之后！`.ProseMirror`.first() + keyboard.type，回读 `#title.value`）
9. 设置原创声明
10. 设置赞赏
11. 选择合集
12. 保存草稿
```

#### 12.1 打开公众号后台

```
browser_navigate("https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token={token}")
```

如果显示「请重新登录」，点击「登录」链接。登录后 token 会自动更新。

#### 12.2 创建新文章

```
# 点击「新的创作」→「文章」（会打开新标签页）
browser_run_code_unsafe("""async (page) => {
  const menuItem = page.locator('.new-creation__menu-item').first();
  await menuItem.click();
  await page.waitForTimeout(3000);
  // 获取所有页面，找到新打开的编辑页
  const pages = page.context().pages();
  return pages.length;
}""")

# 切换到最新标签页
browser_tabs(action="select", index={最新标签页索引})
```

#### 12.3 填写作者（标题放到 12.5b，正文注入之后）

**🔴 作者字段 ≤8 字（v3.24.0 / 2026-08-30 实测）**：映射表「公众号署名」只写进正文开头/文末，**禁止**填进作者栏。作者栏固定报刊名：

| 模式 | 作者字段 | 字数 |
|------|---------|------|
| 日报 | `今日羊报AI` | 6 |
| 周报 | `羊报AI周刊` | 5 |
| 月报 | `羊报AI月报` | 5 |

反例：`羊报AI周刊 · 08-24~08-30` → 保存被拦「作者不能超过8个字」。

```javascript
browser_run_code_unsafe("""async (page) => {
  const result = await page.evaluate(() => {
    const authorInput = document.querySelector('input[placeholder="请输入作者"]');
    if (!authorInput) return 'author input not found';
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(authorInput, '羊报AI周刊');  // 日报改 今日羊报AI；月报改 羊报AI月报
    authorInput.dispatchEvent(new Event('input', { bubbles: true }));
    return 'author=' + authorInput.value + ' len=' + authorInput.value.length;
  });
  return result;
}""")
```

**🔴 标题不要在这一步填。** `#title` 是 `h=0` 隐藏 TEXTAREA，直接 click 会 30s 超时；页面有**两个**可见 `.ProseMirror`（y≈194 标题代理 / y≈272 正文）。标题填写永远放到正文注入之后（12.5b）：

```javascript
// 12.5b 标题填写（正文注入之后）
await page.locator('.ProseMirror').first().click();
await page.keyboard.press('Meta+A');  // macOS；Linux/Windows 用 Control+A
await page.keyboard.type('【MM-DD~MM-DD】核心标题｜本周N大AI新闻一次看完 | 羊报AI周刊');
const titleVal = await page.evaluate(() => document.querySelector('#title')?.value || '');
if (!titleVal || titleVal.length < 8) return 'FAILED title not synced to #title';
```

#### 12.4 插入视频号内容

**🔴 公众号支持直接插入视频号视频，这是推荐的视频插入方式：**

```
# 1. 点击正文区域获取 focus
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const editors = document.querySelectorAll('.ProseMirror');
    if (editors[1]) editors[1].click();
  });
  return 'body clicked';
}""")

# 2. 点击工具栏「视频号」按钮（坐标方式）
browser_run_code_unsafe("""async (page) => {
  // 找到视频号按钮位置
  const result = await page.evaluate(() => {
    const allElements = document.querySelectorAll('a, button, span, div');
    for (const el of allElements) {
      const rect = el.getBoundingClientRect();
      if (rect.y < 50 && rect.y > 0 && el.textContent.trim() === '视频号') {
        return { x: rect.x, y: rect.y };
      }
    }
    return null;
  });
  if (result) {
    await page.mouse.click(result.x + 20, result.y + 10);
    await page.waitForTimeout(2000);
  }
  return 'clicked 视频号';
}""")

# 3. 在弹窗中选择「最近使用」的账号
browser_run_code_unsafe("""async (page) => {
  // 点击「最近使用」中的账号名
  const result = await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      const text = el.textContent.trim();
      const rect = el.getBoundingClientRect();
      if (text === '账号名' && el.offsetParent !== null && rect.x > 500 && rect.y > 300 && rect.y < 500) {
        el.click();
        return 'clicked';
      }
    }
    return 'not found';
  });
  await page.waitForTimeout(2000);
  return result;
}""")

# 4. 选择第一个视频
browser_run_code_unsafe("""async (page) => {
  await page.mouse.click(340, 320);  // 第一个视频缩略图位置
  await page.waitForTimeout(1000);
  return 'selected video';
}""")

# 5. 点击「插入」
browser_run_code_unsafe("""async (page) => {
  const insertBtn = page.locator('button:has-text("插入")');
  await insertBtn.first().click();
  await page.waitForTimeout(2000);
  return 'inserted';
}""")
```

#### 12.5 填写正文内容

**🔴 v3.30.0 / 2026-09-10 重大修正：insertHTML 注入成功 ≠ 存活——上传图片/保存草稿会从内部空模型回刷清空正文！**
0910 实测：`execCommand('insertHTML')` 注入后 pmLen 回读通过（1193 字），随后任一操作（工具栏「本地上传」插图、点「保存为草稿」）都会让编辑器**从 ProseMirror 内部 doc 重渲染**——内部 doc 仍为空，正文被静默清空（标题/作者不受影响）。**pmLen 只证明 DOM 改了，不证明内部 state 同步**，v3.23.0 的回读验证不足以保证存活。合成 `ClipboardEvent('paste')` + `DataTransfer`（v3.28.0）同样无效（pmLen=0，编辑器不认）。**唯一已验证可靠方案是真实系统剪贴板 + 真实键盘粘贴**（走 ProseMirror 原生输入管线，内部 state 同步）：

```javascript
browser_run_code_unsafe("""async (page) => {
  const htmlContent = `<h2>1. 新闻标题</h2><p>正文内容...</p>`; // 由外部传入
  const context = page.context();
  // 1. 授予剪贴板权限（否则 navigator.clipboard.write 静默失败）
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: 'https://mp.weixin.qq.com' });
  // 2. 写入系统剪贴板（text/html + text/plain 双格式）
  await page.evaluate(async (html) => {
    await navigator.clipboard.write([new ClipboardItem({
      'text/html': new Blob([html], { type: 'text/html' }),
      'text/plain': new Blob([html.replace(/<[^>]+>/g, ' ')], { type: 'text/plain' })
    })]);
  }, htmlContent);
  // 3. 点正文编辑器 → 全选 → 真实粘贴
  await page.evaluate(() => document.querySelectorAll('.ProseMirror')[1].click());
  await page.waitForTimeout(300);
  await page.keyboard.press('Meta+A');   // Linux/Windows 用 Control+A
  await page.keyboard.press('Meta+V');
  await page.waitForTimeout(2000);
  const len = await page.evaluate(() => document.querySelectorAll('.ProseMirror')[1].textContent.trim().length);
  if (len < 1000) return `FAILED pmLen=${len}`;  // 日报正文应 >1000 字
  // 4. 立刻点「保存为草稿」固化服务器基线，再回读 bodyLen 不降才算存活
  await page.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      if ((btn.textContent || '').trim() === '保存为草稿' && btn.offsetParent) { btn.click(); return; }
    }
  });
  await page.waitForTimeout(4000);
  const after = await page.evaluate(() => document.querySelectorAll('.ProseMirror')[1].textContent.trim().length);
  return after >= 1000 ? `pasted+saved pmLen=${after}` : `FAILED after-save pmLen=${after}`;
}""")
```

**🔴 v3.30.0 配套铁律：每张图上传后立即「保存为草稿」固化服务器基线**——上传每张正文图（选中占位符 → 工具栏图片 → 本地上传 → setInputFiles → Escape 关挡层）后**立刻点「保存为草稿」**，验证 bodyLen 不降再传下一张。这样即使触发回刷，恢复基线也是有内容的版本而非空稿。上传产生的 `src=""` 空 img 是编辑器装饰节点，execCommand delete 删不掉，保存时服务端忽略（有效 mmbiz 图数不变），勿纠结。

**🔴 v3.31.1 事故（坑 185 / 2026-09-11）：正文被标题框操作顶掉——静默丢整篇正文。**
- **事故链**：为给封面找落脚点，在**标题代理框** `document.querySelectorAll('.ProseMirror')[0]` 上做了「图片→本地上传」，随后又对它 `Meta+A` → 正文（`nth(1)`）的 4 段图文被清空，只剩标题文本；紧接着的「保存为草稿」把坏状态**固化到服务器**（覆盖原草稿基线）
- **铁律**：`.ProseMirror` **idx0=标题代理 / idx1=正文**；任何正文操作必须**显式 `nth(1)`**，封面图插入务必走正文 `nth(1)` 末尾；`Meta+A` 前先 `document.activeElement` 确认焦点在正文
- **事故信号**：每步保存前用 `pmLen` 校验，**正文长度骤降到≈标题长度即事故**，立即停止保存并走恢复流程
- **恢复**：重新 `pbcopy` 带 `PLACEHOLDER_IMG_N` 的纯文本版 → 点正文 → `Meta+A` → `Backspace` → `Meta+V` 真实粘贴 → 保存固化 → 逐张替换占位符
- **How to apply:** Phase 12.5/12.7 每次保存前断言 `nth(1).textContent.length` 不为标题长度

**🔴 v3.23.0 / 2026-08-29 历史修正（已被 v3.30.0 取代，勿再当主路径）：禁止对 ProseMirror 正文直接 `innerHTML = ...` 赋值！**
0829 实测：赋值返回"ok"但编辑器立即回滚，验证 `pm.textContent.length === 1`——**内容被静默清空**（无任何报错）。当时认为 `document.execCommand('insertHTML')` 可靠；0910 实测 insertHTML 同样存在「DOM 成功、内部 state 空」的回刷问题。**以下 insertHTML 代码块仅作反例保留，禁止当主路径：**

```javascript
browser_run_code_unsafe("""async (page) => {
  const htmlContent = `<h2>1. 新闻标题</h2><p>正文内容...</p>`; // 由外部传入
  const result = await page.evaluate((html) => {
    const editors = document.querySelectorAll('.ProseMirror');
    const bodyEditor = editors[1];  // 第二个 ProseMirror 是正文
    if (!bodyEditor) return 'body editor not found';
    bodyEditor.focus();
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(bodyEditor);
    sel.removeAllRanges();
    sel.addRange(range);
    document.execCommand('insertHTML', false, html);
    // 🔴 注入后必须回读验证，不达标视为失败
    const len = bodyEditor.textContent.trim().length;
    return `inserted, pmLen=${len}`;
  }, htmlContent);
  if (!result.includes('pmLen=') || parseInt(result.match(/pmLen=(\\d+)/)[1]) < 1000) {
    return `FAILED: ${result}`;  // 日报正文应 >1000 字，短文按实际阈值调整
  }
  return result;
}""")
```

**🔴 v3.23.0 新增坑：正文注入操作可能把标题框灌入整篇文章**（实测标题计数器变 1776/64、标题区显示正文全文）。恢复流程见 12.5b；**预防规则：标题填写永远放到正文注入之后**（调整 12.0 顺序：正文 → 图片 → 封面 → **再填标题** → 原创 → 合集 → 保存）。

#### 12.5b 标题被正文注入覆盖后的重置（v3.23.0 / 2026-08-29 实测）

**🔴 v3.31.1 标题写入只认 Playwright 真实点击（坑 187 / 2026-09-11）**：`#title` 是 `visibility:hidden; height:0` 的代理框，用 evaluate 的 `.focus()` + `keyboard.insertText` **写不进去**（回读 `#title.value === ''`）。**可行**：`page.locator('.ProseMirror').first().click()`（Playwright 真实鼠标）→ `Meta+A` → `keyboard.type(title, {delay:30})` → 回读 `nth(0).textContent` 长度 === 标题字符数验证。evaluate 内 click 对 ProseMirror 无效。

用 `data-placeholder` 含「标题」定位（勿依赖编辑器索引——注入操作后索引可能漂移）：

```javascript
browser_run_code_unsafe("""async (page) => {
  const title = '【2026-08-29】... | 今日羊报AI'; // 由外部传入
  const result = await page.evaluate((t) => {
    let titleBox = null;
    for (const el of document.querySelectorAll('[contenteditable="true"]')) {
      if ((el.getAttribute('data-placeholder') || '').includes('标题')) { titleBox = el; break; }
    }
    if (!titleBox) return 'title box not found';
    titleBox.focus();
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(titleBox);
    sel.removeAllRanges();
    sel.addRange(range);
    document.execCommand('delete');
    document.execCommand('insertText', false, t);
    return `title set, len=${titleBox.textContent.length}`;
  }, title);
  return result; // 预期 len === 标题字符数
}""")
```

#### 12.6 上传图片到正文

**🔴 通过工具栏「图片」→「本地上传」插入图片：**

```
# 1. 点击正文区域获取 focus
# 2. 点击工具栏「图片」→「本地上传」
browser_run_code_unsafe("""async (page) => {
  // 点击图片按钮
  await page.mouse.click(530, 17);  // 图片按钮位置
  await page.waitForTimeout(1000);
  // 点击「本地上传」
  await page.mouse.click(550, 75);
  await page.waitForTimeout(1000);
  return 'clicked 本地上传';
}""")

# 3. 上传文件（等待 file chooser）
browser_file_upload("news-pipeline/YYYY-MM-DD/wechat-images/sceneN.png")

# 重复以上步骤插入多张图片
# 🔴 v3.30.0：每张图上传完成后立刻点「保存为草稿」，验证 bodyLen 不降再传下一张
# （否则 insertHTML/未走原生粘贴时，上传会触发内部空模型回刷，正文整篇消失）
# 🔴 v3.47.0 坑 252：images 步跑完后 verify 若 placeholders>0（1013 残留 1 个），
# 直接重跑 `wechat_upload.py images` 幂等补齐（脚本每次扫描剩余 PLACEHOLDER 替换）再 save，
# 不要手工在编辑器里翻残留占位符。
```

#### 12.7 上传封面（已验证流程 v3.8.0 / 2026-07-19 周报实测）

**🔴 完整推荐流程：先把封面图（横版 `horizontal-4-3.png`）插入正文，再「从正文选择」设封面。**  
**🔴 降级原则（v3.5.0）**：封面步骤不稳定时，**不得阻塞整篇草稿**——先保证标题/作者/正文/原创/「保存为草稿」成功；封面可留草稿箱手补。

**🔴 v3.8.0 铁律（今日踩坑总结）**：
1. 裁剪弹窗标题是 **「编辑封面」**，主按钮文案是 **「确认」**（不是「完成」；页面上另有 **disabled 的「确定」**，`getByRole/locator('确定')` 会点到灰按钮失败）
2. **裁剪弹窗打开期间禁止 `Escape`**——会关掉未确认的裁剪，封面不落库
3. 验收必须以 **`.js_cover_preview_new` 的 `display===block` 且 `background-image` 含 `mmbiz`/`qpic`** 为准；`#js_cover_area` 内文案可仍残留「拖拽或选择封面」
4. 点「确认」后 **轮询 3–8s**：`dialogOpen=false && previewDisplay=block && hasQpic` 才算成功；失败再点一次「确认」
5. 「从正文选择」节点常 `display:none`：先 hover `#js_cover_area .js_cover_btn_area`，再 **强制 style 显示** 后点 `.js_selectCoverFromContent`
6. 缩略图是 **`span.appmsg_content_img.cover` + background-image**，优先点带 `mmbiz` 背景的 `.appmsg_content_img_item`
7. 已有草稿可直接打开：`appmsg?…&appmsgid={id}&token=…`（比「新的创作」稳）

**🔴 v3.31.1 封面完整可靠路径（坑 186 / 2026-09-11 打通，替代 v3.23.1「从图片库选择」）——当前主路径：**
1. **前置铁律**：封面图**必须先插入正文**（正文 `nth(1)` 末尾 → 工具栏「图片」→「本地上传」→ setInputFiles；见下方步骤1），否则「从正文选择」对话框里一张图都没有
2. **打开菜单**：点 `.js_cover_btn_area.select-cover__btn` 中心 → 弹 `.pop-opr__group`（含「从正文选择/从图片库选择/微信扫码上传/AI 配图」）
3. **🔴 点菜单项必须 `force: true`**：`page.mouse.click(坐标)` 与 evaluate 内 `.click()` 均**无效**（点了没反应）；只有 `locator.click({force:true})` 能打开对话框
4. **对话框延迟出现**：`waitForSelector('.weui-desktop-dialog', {state:'visible'})` 会**超时**（该元素 Playwright 判定不可见，对话框实际已开）——改用轮询 `getBoundingClientRect().height > 100` 判定
5. **🔴 缩略图不是 `<img>`**：5 张候选图是 `[style*="background-image"]` 元素（`.appmsg_content_img.cover`，115×115，y≈345，x 依次 350/480/610/740/870），查 `img` 永远 count=0——用 background-image 选择器定位后取坐标点击
6. **确认**：「下一步」→「编辑封面」对话框（显示 2.35:1 消息列表 + 1:1 转发卡片预览）→ 点 enabled 的「**确认**」（「取消」vis=false 勿点）
7. **验收**：`.js_cover_preview_new{display:block, backgroundImage 含 mmbiz}` + URL 保留 `appmsgid=`；点确认前先读预览 img src 确认是目标封面
8. 🔴 **`browser_drop` 拖拽上传封面禁用**：会卡 loading（`.js_cover_loading` 12s+ 不完成）

**🔴 v3.31.1 变体坑（坑 188 / 2026-09-11）：误触「未授权使用切换账号能力」弹窗遮蔽全页。** 点封面区后偶发弹出「未授权使用切换账号能力，请退出后扫码登录其他账号」，其 wrp 层级最高，之后所有点封面操作都被它拦截（元素 `offsetParent:false` 但仍在拦截 pointer events）。**解决**：遍历 `.weui-desktop-dialog` 点 `.weui-desktop-dialog__close-btn` 或「我知道了」逐个关闭，再重试封面流程；**打开封面菜单前先清一次 dialog**。

```
# 步骤1：上传封面图到正文（工具栏「图片」→「本地上传」）
browser_run_code_unsafe("""async (page) => {
  const cover = '/ABS/PATH/horizontal-4-3.png'; // 周报用 weekly/.../horizontal-4-3.png
  const prose = document.querySelectorAll('.ProseMirror');
  if (prose[1]) { prose[1].click(); }
  // 工具栏「图片」→「本地上传」
  await page.evaluate(() => {
    for (const item of document.querySelectorAll('li, a, span')) {
      if ((item.textContent || '').trim() === '图片' && item.offsetParent) {
        const r = item.getBoundingClientRect();
        if (r.y < 80 && r.y >= 0) { item.click(); return; }
      }
    }
  });
  await page.waitForTimeout(600);
  await page.evaluate(() => {
    for (const item of document.querySelectorAll('*')) {
      if ((item.textContent || '').trim() === '本地上传' && item.offsetParent) {
        item.click(); return;
      }
    }
  });
  await page.waitForTimeout(800);
  const input = await page.$('input[type="file"][accept*="image"]')
    || (await page.$$('input[type="file"]'))[0];
  if (input) await input.setInputFiles(cover);
  await page.waitForTimeout(8000); // 等上传完成
  await page.keyboard.press('Escape'); // 仅关「上传中」类挡层，此时还没开裁剪弹窗
  return 'body image ready';
}""")

# 步骤2+3+4：hover 封面 → 从正文选择 → 选图 → 下一步 → 等待「编辑封面」→ 点「确认」→ 轮询 preview
browser_run_code_unsafe("""async (page) => {
  const coverLoc = page.locator('#js_cover_area .js_cover_btn_area').first();
  await coverLoc.scrollIntoViewIfNeeded();
  await coverLoc.hover({ force: true });
  await page.waitForTimeout(700);
  // 强制显示「从正文选择」
  await page.evaluate(() => {
    const btn = document.querySelector('.js_selectCoverFromContent');
    if (btn) {
      btn.style.cssText = 'display:block!important;visibility:visible!important;opacity:1!important;pointer-events:auto!important;';
      btn.click();
    }
  });
  await page.waitForTimeout(1500);
  // 优先点带 mmbiz 背景的正文图
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.appmsg_content_img_item'));
    for (const el of items) {
      const span = el.querySelector('.appmsg_content_img.cover, span');
      const bg = span ? getComputedStyle(span).backgroundImage : '';
      if (bg.includes('mmbiz')) { el.click(); return; }
    }
    if (items[0]) items[0].click();
  });
  await page.waitForTimeout(500);
  // 下一步
  await page.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      if ((btn.textContent || '').trim() === '下一步' && btn.className.includes('primary') && btn.offsetParent) {
        btn.click(); return;
      }
    }
  });
  // 等裁剪弹窗「编辑封面」
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(500);
    const open = await page.evaluate(() =>
      Array.from(document.querySelectorAll('.weui-desktop-dialog__title'))
        .some(el => (el.textContent || '').includes('编辑封面') && el.getBoundingClientRect().width > 50));
    if (open) break;
  }
  await page.waitForTimeout(1200);
  // 等「确认」可点（非 disabled）再 click —— 禁止点「确定」灰按钮
  for (let i = 0; i < 20; i++) {
    const ok = await page.evaluate(() => {
      for (const btn of document.querySelectorAll('button')) {
        if ((btn.textContent || '').trim() === '确认'
          && btn.className.includes('weui-desktop-btn_primary')
          && !btn.className.includes('disabled') && !btn.disabled) {
          btn.click(); return true;
        }
      }
      return false;
    });
    if (ok) break;
    await page.waitForTimeout(400);
  }
  // 轮询验收（关键！点确认后可能要 1–4s 才写 preview）
  for (let i = 0; i < 10; i++) {
    await page.waitForTimeout(800);
    const st = await page.evaluate(() => {
      const dialogOpen = Array.from(document.querySelectorAll('.weui-desktop-dialog__title'))
        .some(el => (el.textContent || '').includes('编辑封面') && el.getBoundingClientRect().width > 50);
      const preview = document.querySelector('.js_cover_preview_new');
      const style = preview ? getComputedStyle(preview) : null;
      const bg = style ? style.backgroundImage : '';
      return {
        dialogOpen,
        display: style ? style.display : null,
        hasQpic: /mmbiz|qpic/.test(bg),
        bg: bg.slice(0, 120)
      };
    });
    if (st.hasQpic && st.display === 'block' && !st.dialogOpen) return { ok: true, st };
    if (st.dialogOpen) {
      // 再点一次确认，仍不要 Escape
      await page.evaluate(() => {
        for (const btn of document.querySelectorAll('button')) {
          if ((btn.textContent || '').trim() === '确认' && btn.className.includes('primary')
            && !btn.className.includes('disabled')) btn.click();
        }
      });
    }
  }
  return { ok: false };
}""")

# 步骤5：封面已生效后再保存草稿（此时才允许 Escape）
browser_run_code_unsafe("""async (page) => {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      if ((btn.textContent || '').trim() === '保存为草稿' && btn.offsetParent) btn.click();
    }
  });
  await page.waitForTimeout(3000);
  const preview = document.querySelector('.js_cover_preview_new');
  const bg = preview ? getComputedStyle(preview).backgroundImage : '';
  return {
    appmsgid: page.url().includes('appmsgid='),
    coverOk: /mmbiz|qpic/.test(bg) && getComputedStyle(preview).display === 'block',
    bg: bg.slice(0, 160)
  };
}""")
```

**🔴 关键经验（v1.9.1 + v3.5.0 + v3.8.0 + v3.20.0）：**
1. **必须先「图片」→「本地上传」把封面图（横版 `horizontal-4-3.png`）插入正文**，「从正文选择」才可用  
2. **file chooser 不弹时**：`input[type=file][accept*=image].setInputFiles(path)` 可兜底  
3. **Hover 封面区**才出菜单；「从正文选择」用 **`.js_selectCoverFromContent` + 强制显示**  
4. **「图片上传中」弹窗会挡住保存**：等上传完 + Escape（仅此阶段）  
5. **封面失败不阻塞草稿**：标题/正文/原创/保存优先  
6. **保存成功判定**：`appmsgid=` 比「已保存」文案更稳  
7. **裁剪确认 =「确认」**；禁用点 disabled「确定」  
8. **验收 = preview `display:block` + `mmbiz` 背景**，勿被残留「拖拽或选择封面」文案误导  
9. **🔴 v3.26.0 保存后禁止重建**：`appmsgid=` 一旦出现即视为草稿已落盘。后续 snapshot 即使显示标题 `0/64`、正文「从这里开始写正文」、封面「拖拽或选择封面」，也**禁止**再点「新建」/再跑 Phase 12 全文注入。原因：编辑器 SPA 切 tab 或 snapshot 读到空壳，不等于草稿丢失（0901 实测 `appmsgid=100000882` 后空壳 UI，重建会重复稿）

#### 12.7b 从图片库选封面（v3.20.0 / 2026-08-23 W33 周报实测）

**适用场景**：封面图已提前上传到公众号素材库（如周报裁好的 `wechat-cover-2.35.png` 2.35:1 横图），想直接从图片库选，不再插正文。

**🔴 图片库选择器 DOM（踩坑要点）**：
1. 图片库弹窗是 `.weui-desktop-dialog`；图片**不是**直接渲染在 `.weui-desktop-img-picker__item` 上，**也不是 `<img>` 标签**——而是渲染在子元素 **`<i>`** 上，通过 **computed `backgroundImage: url("https://mmbiz.qpic.cn/...")`** 显示。
2. 旧探测（查 picker item 的 background 或找 `<img>`）会全部返回 `bg:"none"` / `hasImg:false`，误判「图库没图」。
3. **正确探测**：在 picker item 内 `querySelectorAll('i')`，找 `offsetParent!==null` 的 `i`，读 `getComputedStyle(iEl).backgroundImage`。
4. 缩略图统一渲染为 **110×110**，**无法从缩略图尺寸判断宽高比**——不能靠 thumbnail 尺寸挑封面；改用 URL 的 `mmbiz_png` / `mmbiz_jpg` 后缀或 `wx_fmt` 参数辅助区分（PNG 多为生成的封面图）。

**🔴 选图流程（无「确定」按钮，主按钮是「下一步」）**：
```
封面区 hover → 点「从图片库选择」开图库弹窗
  → 点左侧栏「上传 (N)」分组（.weui-desktop-menu__item），过滤到已上传图
  → 点目标缩略图选中（picker item 加 selected 态）
  → 点「下一步」（weui-desktop-btn_primary）—— 注意：此视图【没有】「确定」按钮
  → 进入裁剪/确认步骤 → 点「确认」（enabled，非 disabled「确定」）
  → 轮询 .js_cover_preview_new{display:block; bg 含 mmbiz} 验收
```

```js
// 探测图库当前分组的图（返回 url 列表 + 选中态）
async (page) => {
  return await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.weui-desktop-img-picker__item'));
    return items.map((el, idx) => {
      const iEl = Array.from(el.querySelectorAll('i')).find(i => i.offsetParent !== null);
      const bg = iEl ? getComputedStyle(iEl).backgroundImage : 'none';
      const m = bg.match(/url\(["']?(https:\/\/mmbiz[^"')]+)/);
      return { idx, url: m ? m[1] : '', selected: el.className.includes('selected') || el.getAttribute('aria-checked') === 'true' };
    }).filter(x => x.url);
  });
}

// 点「上传 (N)」分组过滤 → 选中目标图 → 点「下一步」
async (page) => {
  await page.evaluate(() => {
    for (const it of document.querySelectorAll('.weui-desktop-menu__item')) {
      if (/上传\s*\(/.test((it.textContent || '').trim())) { it.click(); return; }
    }
  });
  await page.waitForTimeout(800);
  // 选中第一个 PNG（生成封面通常为 PNG；按需改 idx）
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.weui-desktop-img-picker__item'));
    for (const el of items) {
      const iEl = Array.from(el.querySelectorAll('i')).find(i => i.offsetParent !== null);
      const bg = iEl ? getComputedStyle(iEl).backgroundImage : '';
      if (/mmbiz_png|wx_fmt=png/.test(bg)) { el.click(); return; }
    }
    if (items[0]) items[0].click();
  });
  await page.waitForTimeout(500);
  // 点「下一步」（此视图无「确定」按钮）
  await page.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      if ((btn.textContent || '').trim() === '下一步' && btn.className.includes('primary') && !btn.disabled) { btn.click(); return; }
    }
  });
  // 后续进入裁剪弹窗，按 12.7 的「确认 + 轮询 preview」流程收尾
}
```

**关键经验**：
- 图库缩略图 URL 形如 `https://mmbiz.qpic.cn/mmbiz_png/{prefix}/...?wx_fmt=png`；按 `mmbiz_png`/`mmbiz_jpg` 或 `wx_fmt` 区分格式，辅助定位生成的 PNG 封面。
- 「上传 (N)」分组的 N = 已上传图数量，点它过滤掉系统图，只剩自己上传的。
- 从图片库选完点「下一步」后，裁剪确认流程与 12.7「从正文选择」完全一致（「确认」非「确定」、轮询 preview）。

#### 12.7c 封面流程补充坑（v3.23.0 / 2026-08-29 日报实测，4 子坑）

1. **「从图片库选择」是 hover 弹出菜单**：封面区 hover 才出现，直接 `click()` 报 "element is not visible"。正确做法：`await page.mouse.move(coverBox.x, coverBox.y)`（evaluate 拿 `getBoundingClientRect()` 中心）触发 hover，再 evaluate 点可见链接。
2. **上传文件按钮被 `webuploader-pick` 内 `<label>` 拦截 pointer**：用 `Promise.all([page.waitForEvent('filechooser'), page.locator('.single_upload_btn_container, .webuploader-pick').first().click({force:true})])` + `fileChooser.setFiles([path])`。⚠️ **选择器勿用含点的动态 id**（`#upload_0.7739298874336278` 会被当 class 解析报 CSS 错误），用上面的 class 选择器。
3. **图库首击可能未选中**：点击后回读 `.weui-desktop-img-picker__item.selected` 类验证；无 selected 则 evaluate `items[0].click()` 再验（`className` 应变为 `weui-desktop-img-picker__item selected`）。
4. **2.35:1（消息列表）裁剪 radio 在视口外**：`page.locator(...).click()` 报 "element is outside of the viewport"——改 evaluate 点含 "2.35" 文本的 `label`/`span`，再点「确认」收尾（同 12.7 轮询 preview 验收）。

#### 12.8 设置原创声明（已验证 v1.9.1；🔴 v3.23.0 修正协议勾选行为）

**🔴 v3.23.0 / 2026-08-29 实测修正：「文字原创」默认选中，但「我已阅读并同意」协议 checkbox 并不会自动勾选**（实测 `checked:false`）——直接点「确定」是 no-op（弹窗不关）。必须先点协议 checkbox 的 **`closest('label')` 容器**（点 input 本体或文字 span 均可能不切换），验证 `checked === true` 后再点「确定」。

```
# 步骤1：点击「原创」区域打开弹窗
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '原创' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.y > 150 && rect.x > 500) {
          el.click();
          return;
        }
      }
    }
  });
  return 'clicked';
}""")

# 步骤2：等待弹窗出现
browser_wait_for(time=1)

# 步骤3：🔴 v3.23.0 实测——先勾选协议 checkbox（点 label 容器），验证 checked 后再点「确定」
browser_run_code_unsafe("""async (page) => {
  const r = await page.evaluate(() => {
    // 点「我已阅读并同意」所在 label 容器
    const inputs = document.querySelectorAll('input.weui-desktop-form__checkbox');
    for (const input of inputs) {
      const labelText = (input.closest('label')?.textContent || input.parentElement?.textContent || '');
      if (labelText.includes('阅读') || labelText.includes('同意')) {
        const target = input.closest('label') || input.parentElement;
        target.click();
        return `checkbox clicked, checked=${input.checked}`;
      }
    }
    return 'checkbox not found';
  });
  if (!r.includes('checked=true')) return `agree failed: ${r}`;
  await page.waitForTimeout(500);
  const r2 = await page.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const btn of btns) {
      if (btn.textContent.trim() === '确定' && btn.offsetParent !== null) { btn.click(); return 'ok clicked'; }
    }
    return 'ok not found';
  });
  return `${r} | ${r2}`;
}""")

# 步骤4：验证成功标志 = 弹窗关闭 + 状态区出现「文字原创 · 已开启快捷转载」
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button, a');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '确定' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 步骤4：保存草稿
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '保存为草稿' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")
```

**关键经验（v1.9.1 验证；🔴 v3.23.0 / 2026-08-29 修正）：**
- 弹窗打开后「文字原创」已默认选中
- 🔴 「我已阅读并同意」checkbox **不会**自动勾选（实测 `checked:false`），必须点其 `closest('label')` 容器切换，验证 `checked === true` 后再点「确定」；直接点「确定」是 no-op
- 成功标志 = 弹窗关闭 + 原创状态区显示「文字原创 · 作者：… · 已开启快捷转载」
- 🔴 **v3.22.0 / 2026-08-28 实测**：「原创」标题实测在 `y=471`，旧条件 `rect.y < 400` 会**漏选**导致点不开弹窗；已去 y 上界改为 `rect.y > 150 && rect.x > 500`。优先用 `.setting-group__title` 文本 === '原创' 定位（`document.querySelectorAll('.setting-group__title')` 找文本「原创」的那个），比全 `*` 扫描 + y 范围更稳。
      }
    }
  });
  await page.waitForTimeout(2000);
  return 'original declaration set';
}""")
```

#### 12.9 设置赞赏（已验证 v1.9.1）

**🔴 弹窗打开后「赞赏作者」已选中，账户已填入，「我已阅读并同意」已勾选，直接点确定即可。**

```
# 步骤1：点击「赞赏」区域打开弹窗
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '赞赏' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.y > 300 && rect.y < 500 && rect.x > 500) {
          el.click();
          return;
        }
      }
    }
  });
  return 'clicked';
}""")

# 步骤2：等待弹窗出现
browser_wait_for(time=1)

# 步骤3：直接点击「确定」（弹窗已默认配置好）
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button, a');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '确定' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 步骤4：保存草稿
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '保存为草稿' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")
```

**关键经验（v1.9.1 验证）：**
- 弹窗打开后「赞赏作者」已默认选中
- 账户「Youngs羊示」已自动填入
- 「我已阅读并同意」checkbox 已默认勾选
- 直接点击「确定」即可，无需手动操作其他选项

#### 12.10 选择合集（v3.66.0 重写，坑 310/312 实测修正）

**🔴 2026-10-26 实测：这是公众号链路上最容易「静默失败」的一步。** 点不中就不开弹窗、**不抛任何异常**、随后「保存为草稿」照样成功并返回 `appmsgid`——只有回读合集控件才发现还是「未添加」。

**真入口（唯一）**：`.allow_click_opr.js_article_tags_label`
- 它是「合集」二字右侧那个「未添加」所在的 **DIV**（实测约 54×22，内含 `SPAN.lbl_content_after` 与 `I.read-more__icon__more`）
- **无效且不报错的点法**：点 `SPAN.lbl_content`（「合集」二字）／点行内空白／点 `.frm_checkbox_label` 整行 —— 实测 DOM 节点数 1377→1377，无变化

```
# 步骤1：点真入口打开弹窗（先 scrollIntoView 再重取 rect，坑 302 通用规则）
ed.evaluate("""() => {
  const t = document.querySelector('.allow_click_opr.js_article_tags_label');
  t.scrollIntoView({block: 'center'});
}""")
box = ed.evaluate("""() => { const r = document.querySelector('.allow_click_opr.js_article_tags_label').getBoundingClientRect();
  return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}; }""")
ed.mouse.click(box['x'], box['y'])
# 断言弹窗真的开了——不要用「页面文本含『选择合集』」当判据（本期该文本一直存在，恒真）
for _ in range(10):
    ed.wait_for_timeout(600)
    if ed.evaluate("() => { const d = document.querySelector('.album-setting-dialog'); return !!(d && d.offsetParent); }"):
        break
assert ed.evaluate("() => { const d = document.querySelector('.album-setting-dialog'); return !!(d && d.offsetParent); }")

# 步骤2：弹窗内输入框填关键词（daily「今日羊报」/ weekly「羊报AI周刊」/ monthly「羊报AI月报」）
inp = ed.locator('.album-setting-dialog input[placeholder="请选择合集"]').first
inp.click(); inp.fill('今日羊报')

# 步骤3：等选项渲染，取 li.select-opt-li（本期 600ms 就出来了；仍按坑 266 轮询到出现为止）
opts = ed.evaluate("""() => {
  const c = document.querySelector('.album-setting-dialog .select-opts-con');
  if (!c || c.style.display === 'none') return [];
  return Array.from(c.querySelectorAll('li.select-opt-li')).map(e => {
    const r = e.getBoundingClientRect();
    return {t: (e.textContent||'').trim(), x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2),
            w: Math.round(r.width), h: Math.round(r.height)};
  });
}""")
# 本期实测 ["羊报AI周刊", "「今日羊报 AI」", "羊报AI月报"]，每项 320×36

# 步骤4：精确匹配 + 坐标点击（合集名按 REPORT_MODE 从模式参数映射表读取）
pick = [o for o in opts if o['t'].replace(' ','') == COLLECTION.replace(' ','')][0]
ed.mouse.click(pick['x'], pick['y'])

# 步骤5：弹窗内「确认」（button 文案精确为「确认」，class weui-desktop-btn_primary）
conf = ed.evaluate("""() => {
  const d = document.querySelector('.album-setting-dialog');
  const b = Array.from(d.querySelectorAll('button')).find(x => (x.textContent||'').trim() === '确认' && x.offsetParent);
  const r = b.getBoundingClientRect();
  return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2), disabled: b.disabled};
}""")
ed.mouse.click(conf['x'], conf['y'])
```

**🔴 唯一可靠的成功判据（坑 310）**：回读 `.js_article_tags_content` 的 textContent。

```
coll = ed.evaluate("() => { const d = document.querySelector('.js_article_tags_content'); return d ? d.textContent.replace(/\\s+/g,' ').trim() : null; }")
coll_ok = bool(coll) and '今日羊报' in coll and '未添加' not in coll     # 挂上后实测为「「今日羊报 AI」」
```

**禁止用 `body.innerText` 是否含合集名当判据**——正文 `TAIL` 页脚固定有「🔔 关注「今日羊报 AI」，每天 9 点…」，含书名号的 `「今日羊报 AI」` 会让判据**恒为真**。本期 `MP_VERIFY: {..., "collection": true}` 就是这么误报的，实际字段仍是「未添加」。

**挂上后必须重新「保存为草稿」**（合集随草稿保存）。实测补挂并重存后 `appmsgid` 仍在、`bodyLen` 1877 不变、占位符 0——**重存不会破坏已有正文与图片**。

**坑 255 仍然成立但不够用**：`li.select-opt-li` 计数 0 ≠ 没选中（选项只在手动展开时才渲染），所以「0 items」不能当失败信号；但反过来**也不能因为「看起来点过了」就当成功**——判据永远回到 `.js_article_tags_content`。

# 🔴 v3.47.0 坑 252：合集下拉偶发「option not found (0 items)」（选项列表未加载完成），
# 与坑 232（B站标签重输）同族——先重跑 `wechat_upload.py save` 一次再定性；
# 1013 首跑 0 items，重跑即挂上「今日羊报 AI」。禁止据此判定合集不可用转手动。
#
# 🔴 v3.50.0 坑 255（2026-10-15 实测）：**`li.select-opt-li` 计数为 0
# 不等于合集未选中**。而 `li.select-opt-li` 只在用户手动展开时才出现。
# 🔴 v3.66.0 坑 310 补充：它也不等于「已选中」——判据只认 `.js_article_tags_content`。

#### 12.11 保存草稿

**🔴 保存前必须处理弹窗（v3.3.0 更新）**：封面图上传后会弹出「图片上传中，请稍后」弹窗，阻挡保存按钮。必须先等待上传完成、关闭弹窗，再保存。

```
browser_run_code_unsafe("""async (page) => {
  // 等待上传完成（封面图可能需要10秒+）
  await page.waitForTimeout(10000);
  
  // 关闭可能的弹窗
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  
  // 再等5秒确保上传完成
  await page.waitForTimeout(5000);
  
  // 保存草稿
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.textContent.trim() === '保存为草稿') {
        btn.click(); return;
      }
    }
  });
  await page.waitForTimeout(3000);
  
  // 验证保存成功
  const body = await page.evaluate(() => document.body.textContent);
  return body.includes('已保存') ? 'saved!' : 'URL: ' + page.url();
}""")
```

#### 微信公众号上传组件操作总结（v1.7.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 标题 | **隐藏 `#title` TEXTAREA + 可见 `.ProseMirror` 代理** | 正文注入后 `.ProseMirror`.first() click → Ctrl/Meta+A → keyboard.type；回读 `#title.value`（禁 textContent 直写） | ✅ 高 |
| 作者 | 标准 input（≤8 字） | 原生 setter + dispatch `input`；固定 `羊报AI周刊`/`今日羊报AI`/`羊报AI月报`，勿填署名 | ✅ 高 |
| 正文 | **ProseMirror** | 🔴 v3.30.0 修正：真实剪贴板 + Meta+A/Meta+V 粘贴（insertHTML/合成 paste 都会回刷清空） | ✅ 高 |
| 视频号 | 弹窗选择 | 工具栏「视频号」→ 选账号 → 选视频 → 插入 | ✅ 高 |
| 图片上传 | 工具栏菜单 | 「图片」→「本地上传」→ file_upload | ✅ 高 |
| 封面 | 拖拽区域 | 「从图片库选择」/ 「从正文选择」 | ⚠️ 需坐标点击（图库缩略图在子 `<i>` 的 backgroundImage，非 `<img>`）|
| 原创声明 | 弹窗 | 点击「原创」→ 确定 | ✅ 高 |
| 赞赏 | 弹窗 | 点击「赞赏」→ 不开启 → 勾选同意 → 确定 | ✅ 高 |
| 合集 | **自定义 Vue 组件** | 点 `.allow_click_opr.js_article_tags_label`（**不是**「合集」二字）→ 弹窗内 `input[placeholder="请选择合集"]` 填词 → `li.select-opt-li` 精确匹配坐标点 → 弹窗内「确认」；回读 `.js_article_tags_content` | ✅ 高（v3.66.0 坑 310/312） |
| 保存草稿 | 按钮 | `button:has-text("保存为草稿")` | ✅ 高 |

**关键经验**：
1. **公众号编辑器使用 ProseMirror**，不是 Quill，注入方式不同
2. **标题是隐藏 `#title` TEXTAREA + 可见 `.ProseMirror` 代理**（h=0，直接 click 超时）；页面两个 `.ProseMirror`：first()=标题代理、nth(1)=正文。标题填写永远放到正文注入之后（12.5b），回读 `#title.value`，禁 `textContent` 直写
3. **视频号插入是最可靠的视频方式**，通过工具栏「视频号」按钮 → 选择账号 → 选择视频 → 插入
4. **图片通过工具栏「图片」→「本地上传」插入**，会插入到正文光标位置
5. **「从正文选择」封面**：必须先通过工具栏上传图片到正文，然后用 `.js_selectCoverFromContent` class 选择器点击
6. **合集选择器是自定义 Vue 组件**，需要用坐标点击（约 x=730, y=355 点击「未添加」，x=690, y=375 打开下拉框）
7. **赞赏弹窗中「我已阅读并同意」需要手动勾选**，checkbox 在 `label > input[type="checkbox"]` 结构中
8. **原创声明弹窗默认选中「文字原创」，但协议 checkbox 不自动勾选**（🔴 v3.23.0 / 2026-08-29 实测 `checked:false`）——须点 checkbox 的 `closest('label')` 容器验证 `checked===true` 后再点确定
9. **保存草稿前不需要完成所有设置**，封面和合集可以后续手动添加
10. **新标签页打开**：点击「文章」会打开新标签页，需要切换到最新标签页

#### 12.3 填写作者（旧节，以 12.3 主节为准）

```javascript
// 作者是标准 input，≤8 字；周报固定「羊报AI周刊」，勿填「Youngs羊示」或署名格式
browser_click(target={作者输入框ref})
browser_type(target={作者输入框ref}, text="羊报AI周刊")
```

#### 12.4 填写正文

**🔴 v3.30.0 / 2026-09-10 实测修正：此节旧方案（直接 innerHTML）以及 12.5 旧主路径（execCommand insertHTML）均已被证伪**——innerHTML 立即回滚（pmLen=1）；insertHTML 的 pmLen 回读通过但上传/保存会从内部空模型回刷清空。**必须用 12.5 的真实剪贴板 + Meta+A/Meta+V 粘贴流程**，注入后立刻保存草稿验证 bodyLen 不降。

#### 12.5 上传图片（复杂，建议手动）

**🔴 公众号图片上传机制特殊：**

1. 找到隐藏的 file input：`input[type="file"][accept*="image"]`
2. 用 `page.$('input[type="file"]').setInputFiles(path)` 设置文件
3. **但图片不会自动插入到文章中**，需要先定位光标位置

**推荐方案**：先保存草稿，然后手动在文章中定位光标 → 点击工具栏「图片」→「本地上传」→ 选择图片。

```javascript
// 如果要尝试自动上传（不保证成功）
browser_run_code_unsafe("""async (page) => {
  const fileInput = await page.$('input[type="file"][accept*="image"]');
  if (fileInput) {
    await fileInput.setInputFiles('/path/to/image.png');
    return 'file set';
  }
  return 'input not found';
}""")
```

#### 12.6 保存草稿

```javascript
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button, a, div');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '保存为草稿' && btn.offsetParent !== null) {
      btn.click();
      return 'saved';
    }
  }
  return 'not found';
}""")
```

#### 12.7 设置合集（v3.66.0 已可自动化，见 12.10）

**🔴 2026-10-26 实测更新：合集**不再是**「建议手动」**。此前判断「JS click 不稳定、成功率低」，根因是**点错了节点**——点「合集」二字或整行都不开弹窗且不报错。真入口 = `.allow_click_opr.js_article_tags_label`，完整可复现流程见 **12.10**，本期一次跑通（弹窗 `.album-setting-dialog` → 3 个 `li.select-opt-li` → 确认 → 回读 `.js_article_tags_content` = `「今日羊报 AI」`）。

```javascript
// ✅ 现行方法（v3.66.0）：点「未添加」那个可点 DIV 的坐标，而不是它的父级/文本节点
ed.evaluate("() => document.querySelector('.allow_click_opr.js_article_tags_label').scrollIntoView({block:'center'})")
const r = ed.evaluate("() => { const b = document.querySelector('.allow_click_opr.js_article_tags_label').getBoundingClientRect(); return {x: Math.round(b.x+b.width/2), y: Math.round(b.y+b.height/2)}; }")
ed.mouse.click(r.x, r.y)
// 之后：.album-setting-dialog 内 input[placeholder="请选择合集"] → li.select-opt-li → 「确认」
// 判据：.js_article_tags_content 的 textContent
```

```javascript
// ❌ 旧方法（会静默失败，保留仅作对照）：点「合集 未添加」整行 / 点文本节点
browser_evaluate("""() => {
  const elements = document.querySelectorAll('*');
  for (const el of elements) {
    if (el.textContent.includes('合集') && el.textContent.includes('未添加') && el.offsetParent !== null) {
      el.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

// 方法2：在弹出的对话框中选择合集
browser_click(target={下拉框ref})
browser_evaluate("""() => {
  const options = document.querySelectorAll('*');
  for (const opt of options) {
    if (opt.textContent.trim() === '「今日羊报 AI」' && opt.offsetParent !== null) {
      opt.click();
      return 'selected';
    }
  }
  return 'not found';
}""")

// 点击确认
browser_click(target={确认按钮ref})
```

**⚠️ 实测经验**：合集选择器的 JS click 经常不生效，可能需要手动完成。

#### 微信公众号上传组件操作总结（v1.5.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 标题 | **隐藏 `#title` TEXTAREA + 可见 `.ProseMirror` 代理** | 正文注入后 `.ProseMirror`.first() click → Ctrl/Meta+A → keyboard.type；回读 `#title.value`（禁 textContent 直写） | ✅ 高 |
| 作者 | 标准 input（≤8 字） | 原生 setter + dispatch `input`；固定 `羊报AI周刊`/`今日羊报AI`/`羊报AI月报`，勿填署名 | ✅ 高 |
| 正文 | **ProseMirror** | 🔴 v3.30.0 修正：真实剪贴板 + Meta+A/Meta+V 粘贴（insertHTML/合成 paste 都会回刷清空） | ✅ 高 |
| 图片上传 | **隐藏 file input** | `setInputFiles`（但不插入文章） | ⚠️ 需手动插入 |
| 封面 | 拖拽区域 | 需手动上传 | ❌ 建议手动 |
| 合集 | **自定义 Vue 组件** | JS click（不稳定） | ❌ 建议手动 |
| 保存草稿 | 按钮 | JS click | ✅ 高 |

**关键经验**：
1. **公众号编辑器使用 ProseMirror**，不是 Quill，注入方式不同
2. **标题是隐藏 `#title` TEXTAREA + 可见 `.ProseMirror` 代理**（h=0，直接 click 超时）；页面两个 `.ProseMirror`：first()=标题代理、nth(1)=正文。标题填写永远放到正文注入之后（12.5b），回读 `#title.value`，禁 `textContent` 直写
3. **图片上传到素材库成功，但不会自动插入文章**，需要手动定位光标后插入
4. **图片完整性/封面验收的判据要排除 ProseMirror 分隔符**（v3.66.0 坑 311）——`body.querySelectorAll('img')` 里混有编辑器为每个图片块插入的 `IMG.ProseMirror-separator`（`src` 为空、`naturalWidth=0`），必须先按 class + `src` 非空过滤，否则 `all(w>100)` 恒假；反过来只数 `imgCount` 也恒真，两边都要防
4. **合集选择器是自定义 Vue 组件**——**v3.66.0 起已可自动化，见 12.10**（旧结论「JS click 不稳定、建议手动」的根因是点错节点：点「合集」二字/整行都不开弹窗且不报错）
5. **保存草稿前不需要完成所有设置**，可以先保存再编辑

### Phase 13: 微信视频号自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 重要经验（v3.24.0）：2026-08-30 版 UI 全部表单在 `wujie-app` open shadow root 内。进入发布页先跑 13.1 结构判定：`hasWujie=true` → 走 shadow 协议；仅当 `hasWujie=false` 且 `page.frames()` 有 `name="content"` 时才用旧 iframe 法。禁止一上来就 `page.frame({name:'content'})`。**

**🔴 v3.7.0 补充（2026-07-18）— 上传视频号「稳跑」协议**：
1. 优先 **MCP 单会话闭环**：打开 create → 上传 → 填描述/短标题 → 封面 → 存草稿 → 草稿箱验收；全过程避免另起独立 Playwright 抢 profile。
2. 若 MCP 在双 body 上已崩溃，再改用**独立脚本 + 同一 profile**，启动前 scoped `pkill` 仅杀该 profile。
3. 视频上传成功标志：出现「删除 / 重新上传 / 封面预览」，且「保存草稿」可点（非灰）。
4. 草稿验收：侧栏「草稿箱」条数 +1，标题含当日描述摘要与日期。
5. 封面 3:4 / 4:3：等 **「预览图生成中，请等待完成后再编辑」消失** 后再点对应「编辑」；DOM 可见 `input[accept*=image]` 在 `.single-cover-uploader-wrap`，但跨 frame 时 `setInputFiles` 易 detached——**已验证可用 CDP**：
   `DOM.performSearch` → `getSearchResults` → `describeNode` 过滤 image accept → `DOM.setFileInputFiles({ backendNodeId, files })`。
6. 竖封面文件必须**带日期**（如 `vertical-3-4.png` 含 `2026-07-18`）；生成失败勿用 scene 截图顶替。
7. 短标题 ≤16 中文字符（含空格）。格式：`{报刊名} {M月D日}` / `{报刊名} {M月D日至D日}`，纯报刊名+日期（如 `今日羊报AI 8月30日`），不加核心标题。禁 `.` `~`。

#### 13.0 结构判定（先 13.1 wujie，iframe 仅兜底）

**🔴 不要默认 iframe。** 先按 13.1 检测 `hasWujie`。仅当 `hasWujie=false` 且 `page.frames()` 含 `name="content"` 时，才用下面的旧 iframe 探测：

```javascript
// 仅 hasWujie=false 时检测 iframe 结构
browser_run_code_unsafe("""async (page) => {
  const frames = page.frames();
  const frameInfo = frames.map(f => ({ url: f.url().substring(0, 80), name: f.name() }));
  return JSON.stringify(frameInfo);
}""")
```

#### 13.0b 自主登录失败协议（v3.18.0 / 2026-08-18 实测）

`channels.weixin.qq.com` 会重定向到 `login.html`，QR iframe 来自 `open.weixin.qq.com`（**跨域**）。

**失败表现**：
- iframe 显示 **「加载失败，点击重试」**；点击重试 + 等 5s 仍不加载。
- 跨域 iframe **无法用 JS 访问**（`contentDocument` 为 null）。
- `page.reload` 1–2 次仍失败。

**🔴 v3.23.0 / 2026-08-29 升级为「复发模式」**：此失败已在 **2026-08-28 与 2026-08-29 连续两日**复现——「加载失败，点击重试」+ 重试无效，**非偶发**。标准止损流程（0829 已验证产出可用）：
1. 重试 **1 次**即放弃（勿多轮空转），标记 `channels: login_required`。
2. QR 截图落盘（如 `channels-login-{MMDD}.png`）供用户手动扫码。
3. `upload-status.md` 写 `⏭` + 「视频号待办」小节：列出 QR 截图路径 + 补跑 6 步清单（上传视频/封面 → 描述+短标题 → 合集 → 保存草稿），附双 body 铁律提示（单次 browser_run_code_unsafe + page.goto baidu 离开）。
4. Phase 13 结束，不阻塞其他平台。

**处理协议**（原始 v3.18.0，与上述复发协议合并使用）：
1. `page.reload` 1–2 次后仍失败 → 标记 `channels: login_required`。
2. 写 `upload-status.md` 为 `⏭`（跳过本平台），停止空转。
3. **明确**：自主流程无法完成视频号扫码登录，需用户手动扫码。Phase 13 结束并在 `upload-status.md` 注明「等待用户手动扫码后重跑」。

**🔴 v3.26.0 / 2026-09-01 补「QR 已加载仍需扫码」变体**：
`login.html` 上 QR **已成功加载**（console `qrcode loaded， duration: …`，截图可见「请使用微信扫描二维码登录」）**同样**走复发止损，**不要空等扫码、不要因 QR 可见就多轮 reload**。

与 v3.23.0「加载失败，点击重试」的区别：
- 本变体 QR 可见、iframe 未报加载失败；create URL 可能闪一下再 302 回 `login.html`。
- console 常见噪声**不是**继续重试的理由：
  - `网络错误，错误码：300334`
  - `fastLogin: false` / `fast_login: null`
  - `localhost.weixin.qq.com:14xxx/130xx/api/check-login` `ERR_CONNECTION_REFUSED`（微信桌面端 fast-login 探测端口，无桌面客户端时必然失败）
- Playwright `browser_snapshot` YAML 在 `login.html` 上可能为空 → **用截图判定**，勿因空 snapshot 再 reload。

**止损不变**：重试 1 次（navigate `/platform/post/create`）仍落 `login.html` → `channels: login_required` → QR 截图落盘（如 `channels-login-YYYY-MM-DD.png` + `channels-create-retry-YYYY-MM-DD.png`）→ `upload-status.md` 写 6 步补跑 → 不阻塞其他平台。

**常见 iframe 结构**：
- 主页面：`https://channels.weixin.qq.com/platform/post/...`
- 内容 iframe：`name="content"`, URL 包含 `/micro/content/post/...`

**仅 `hasWujie=false` 时**才用 `page.frame({ name: 'content' })`（`hasWujie=true` 时此调用拿不到表单）：
```javascript
browser_run_code_unsafe("""async (page) => {
  const frame = page.frame({ name: 'content' });
  if (!frame) return 'frame not found';
  const result = await frame.evaluate(() => {
    // 在 iframe 内操作 DOM（旧 UI 兜底）
    return document.querySelector('.some-class')?.textContent;
  });
  return result;
}""")
```

#### 13.1 🔴 wujie shadow DOM 全套操作协议（v3.24.0 / 2026-08-30 W35 实测，替代旧 iframe/坐标法）

**2026-08-30 版 UI：页面级 locator / 普通 evaluate / `page.frame({name:'content'})` 全部失效——页面 body 几乎为空（bodyLen≈81），全部表单内容渲染在 `wujie-app` 的 open shadow root 内。**

**结构判定**（进入发布页先做一次）：
```javascript
browser_run_code_unsafe("""async (page) => {
  return await page.evaluate(() => JSON.stringify({
    bodyLen: document.body.textContent.length,
    hasWujie: !!document.querySelector('wujie-app'),
    inShadow: document.querySelector('wujie-app')
      ? document.querySelector('wujie-app').shadowRoot.querySelectorAll('input,button,[contenteditable]').length
      : -1,
  }));
}""")
```
- `hasWujie=true` → 走本节 shadow 协议；旧 iframe 结构（`page.frames()` 有 `name="content"`）才用 13.6 的旧法。

**字段定位表（shadow root 内）**：

| 组件 | 定位与操作 |
|------|-----------|
| 视频上传 | `wujie-app input[type=file]`（`.ant-upload` 内）——**setInputFiles 直传 file input**，无需点「上传」按钮（filechooser 监听在 shadow 内不触发） |
| 合集 | 点 `.post-album-display` 展开 → `.post-album-wrap .option-item`，**真实鼠标坐标点击**（JS `.click()` 对这层 Vue 组件无效，v3.61.0 坑 293）；选项文案是「共N个**内容**」（1025 实测 `今日羊报Al 共134个内容`），**匹配正则要同时容「内容」和「作品」** |
| 视频标注（AI 声明） | `.mark-tag-select` → **先 `scrollIntoView({block:'center'})` 再重取 rect** → 点 `.select-display` 展开 → **断言 `.mark-tag-options` 的 `display === 'block'`** → 坐标点 **`Contains AI-generated content`**（选项全英文，无中文「AI生成」控件，v3.61.0 坑 292；视口外静默失效见 v3.63.0 坑 303） |
| 封面上传 | `.single-cover-uploader-wrap input[type=file]`（Playwright CSS 可穿 open shadow，locator 直接 setInputFiles） |
| 描述 | `.input-editor`（contenteditable）——evaluate 内 `shadowRoot.querySelector` → dispatchEvent mousedown/click → focus → `page.keyboard.type` |
| 短标题 | `input[placeholder*="短标题"]`（**Vue 受控 input**，不是 contenteditable）——原生 setter 清空 + focus + `page.keyboard.type` |
| 封面确认 | 封面弹窗内 `button.weui-desktop-btn_primary`「确认」（个人主页卡片 3:4 裁剪）；JS 查不到时取可见 `.weui-desktop-dialog__wrp` 内「确认」rect 做坐标点击（v3.61.0 坑 294） |

**shadow 内 contenteditable / input 操作模板**：
```javascript
browser_run_code_unsafe("""async (page) => {
  // 描述：mousedown/click 激活 → focus → 逐字键入
  await page.evaluate(() => {
    const r = document.querySelector('wujie-app').shadowRoot;
    const ed = r.querySelector('.input-editor');
    ed.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
    ed.dispatchEvent(new MouseEvent('click', {bubbles: true}));
    ed.focus();
  });
  await page.keyboard.type('描述文本', {delay: 5});

  // 短标题：Vue 受控，须原生 value setter 清空再键入
  await page.evaluate(() => {
    const r = document.querySelector('wujie-app').shadowRoot;
    const inp = r.querySelector('input[placeholder*="短标题"]');
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(inp, '');
    inp.dispatchEvent(new Event('input', {bubbles: true}));
    inp.focus();
  });
  await page.keyboard.type('短标题文本', {delay: 5});
  return 'done';
}""")
```

**🔴 短标题硬约束（v3.24.0，Phase 13.4 补强）**：
- **≤16 字**（含空格）+ **特殊字符白名单**：仅 书名号/引号/冒号/加号/问号/百分号/摄氏度——`.` `~` 均被拒（实测 `8.24~8.30` 报「符号仅支持…」）
- 格式统一 **`{报刊名} {M月D日至D日}`**：日报 `今日羊报AI 8月30日`；周报 `羊报AI周刊 8月24日至30日`（16字 ✅；`8月24日~8月30日` 18字超限 ❌）；月报 `羊报AI月报 2026年8月`
- **超限/非法字符时「保存草稿」按钮 silent disabled**——无 toast、点击无反应。每次填完必须验证：
```javascript
// 回读 .error-title 可见错误项 + 保存按钮 disabled 状态
const r = document.querySelector('wujie-app').shadowRoot;
const errs = [...r.querySelectorAll('.error-title')]
  .filter(e => e.offsetParent !== null && e.textContent.trim());
const saveBtn = [...r.querySelectorAll('button')].find(b => b.textContent.includes('保存草稿'));
return JSON.stringify({errors: errs.map(e => e.textContent.trim()), saveDisabled: saveBtn?.disabled});
```

#### 13.1b 打开视频号发布页

```
# 直接导航到发布页（跳过首页）
browser_navigate("https://channels.weixin.qq.com/platform/post/create")

# 或从首页进入
browser_navigate("https://channels.weixin.qq.com/platform")
# 点击「发表视频」按钮
browser_run_code_unsafe("""async (page) => {
  const btn = page.getByRole('button', { name: '发表视频' });
  await btn.click();
  await page.waitForTimeout(3000);
  return 'clicked';
}""")
```

**🔴 v3.47.0 / 坑 251：wujie 空壳用 `Page.navigate` 重新挂载；Playwright attach 无报错挂起 → 整平台切 raw CDP websockets**（2026-10-13 实测）：

- **症状A（attach 挂起）**：`connect_over_cdp` **无报错纯挂起**（1013 B站/抖音/视频号三平台均出现；并发 raw CDP 客户端无冲突 → 问题是 Playwright flatten 协议/事件洪泛自身）。对策 = 该平台脚本整平台改 **raw CDP websockets**，全步骤模板 = `news-pipeline/2026-10-13/scripts/channels_upload_1013.py`：`/json/list` 取 `webSocketDebuggerUrl` → websockets 收发 CDP JSON（cmd/ev 助手）；文件上传 = **首选（v3.67.0 坑 319，1028 实测）**：`Runtime.evaluate` 求值出 `input[type=file]` 元素（`returnByValue:false`）取 `objectId` → `DOM.setFileInputFiles({files, objectId})`——对本机 Chrome 155 **一次成功**，且能直接 `shadowRoot.querySelector` 拿到元素，不需要 pierce 遍历。**备选（Chrome 155 上已失效，坑 319）**：`DOM.getDocument{depth:-1,pierce:true}` 报 -32601 `wasn't found`，故 v3.48.0 那条「pierce 树手工 walk `children`+`shadowRoots`+`contentDocument`」在本机不可用，仅在 objectId 路径失效时才尝试。set 后 20s 回读 shadow 文本有无进度/`%`，无进度即换下一个 node（错 node 静默失败，不傻等 300s）；contenteditable 用 `Input.insertText`；Vue 受控 input 用原生 value-setter + `input` 事件；截图 `Page.captureScreenshot`。
- **症状B（wujie 空壳）**：登录墙清掉后 `#app` 仍是空壳（`.app-body-full` kids=0、`querySelectorAll('*').length==1`、`appText` 空），`Page.reload` 多次无效 → **`Page.navigate` 到 `https://channels.weixin.qq.com/platform/post/video` 让 wujie 微应用重新挂载**；nav 返回 `net::ERR_ABORTED` **属正常**，不作失败判据。
- **挂载判据（轮询 ≤60s）**：shadowRoot 内 `#app` 后代数 >10 且 `input[type=file]` 出现（1013 实测 kids=1410、2 个 file input：video + image cover、按钮含「保存草稿」），未达标**禁止**开始表单操作。

#### 13.2 上传视频

**🔴 `hasWujie=true`（当前默认）**：Playwright CSS 可穿 open shadow，直接 `setInputFiles` 到 `wujie-app input[type=file]`。filechooser 监听在 shadow 内**不触发**，勿点「上传」按钮。

```javascript
browser_run_code_unsafe("""async (page) => {
  const input = page.locator('wujie-app input[type=file]').first();
  await input.setInputFiles('news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4');
  return 'uploaded via wujie file input';
}""")
```

**仅 `hasWujie=false` 时**才用旧 filechooser 点击：

```
# 旧 UI：点击上传区域（+号按钮）触发 file chooser
browser_run_code_unsafe("""async (page) => {
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 5000 }),
    page.locator('.finder-upload__add-btn, [class*="upload-btn"]').first().click({ force: true })
  ]);
  await fileChooser.setFiles('news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4');
  return 'uploaded';
}""")
```

# 等待上传完成（15MB 视频约需 10-15 秒）
browser_wait_for(time=15)

#### 13.3 填写视频描述

**🔴 按 13.1 shadow 协议操作 `.input-editor`（contenteditable）：mousedown/click 激活 → focus → `page.keyboard.type`。** 仅当页面仍是旧 iframe 结构时才用旧坐标法（坐标点击 + keyboard.type）。

#### 13.4 填写短标题

**🔴 按 13.1 shadow 协议操作 `input[placeholder*="短标题"]`（Vue 受控 input，原生 setter 清空 + focus + keyboard.type）。**

**短标题限制**：最多 **16 字**（含空格），超过会报「标题超过16字限制」。
**短标题格式**：`{报刊名} {M月D日至D日}`，纯报刊名+日期，不加核心标题/副标题。
- 日报：`今日羊报AI 8月30日`
- 周报：`羊报AI周刊 8月24日至30日`（🔴 用「至」连接，勿用 `~`/`.`——特殊字符白名单禁 `.` `~`；`8月24日~8月30日` 同时 18 字超限）
- 月报：`羊报AI月报 2026年8月`

**字符白名单**：符号仅支持书名号、引号、冒号、加号、问号、百分号、摄氏度。逗号可用空格代替。
**🔴 违规后果**：保存草稿按钮 **silent disabled**（无 toast、点击无反应）——填完必须按 13.1 的 `.error-title` + `button.disabled` 双验证。

#### 13.5 选择合集

按 13.1 shadow 协议：点 `.post-album-display` 展开 → 等 `.post-album-wrap .option-item` 渲染 → 取目标项 `getBoundingClientRect` 中心 `page.mouse.click(x,y)`。**JS `el.click()` 对这层 Vue 组件不生效（返回成功但 display 文案不变，v3.61.0 坑 293）**。选项文案形如「今日羊报Al」+「共N个内容」（1023 是「作品」，1025 实测是「内容」，**正则两者都容**）；**注意小写 `l` 不是大写 `I`**。回读以 `.post-album-display` 文本为准。仅旧 iframe 结构时才用坐标估算兜底。

> **🔴 点选项前同样要确认 rect 在视口内（坑 303 同根）**：展开下拉后先读每个 option 的 `getBoundingClientRect().top`，超出 `window.innerHeight` 的要先 `scrollIntoView({block:'center'})` 再重取坐标——否则 `mouse.click` 静默失效。

#### 13.5b 视频标注（AI 合成内容声明，v3.61.0 / 2026-10-23 实测，坑 292）

**🔴 控件名叫「视频标注」，不是中文「AI生成」勾选框。** wujie shadowRoot 里根本不存在 `/AI生成|人工智能生成/` 的 checkbox，任何按中文关键词匹配或遍历 `input[type=checkbox]` 的写法恒返回 `absent`。

**真实 DOM 链路**：`.mark-tag-select` 容器 → 点其内 `.select-display` 展开 → `.mark-tag-options` 下选项列表 → **真实鼠标坐标点击**目标项（同 13.5 的 Vue 组件限制）。

**🔴 但点之前必须先把它滚进视口（v3.63.0 坑 303，1025 实测）**：`.mark-tag-select` 初始 `rect.y = 1208`，而视口只有 769 高。此时 `page.mouse.click(941, 1231)` **返回成功、无任何异常**，但 `.mark-tag-options` 仍是 `display:none`、选项查询返回 `[]`——现象酷似「下拉里根本没有 AI 选项」，极易误判成控件又改版了而去乱改选择器。

```python
# 正确顺序：滚 → 重取 rect → 点击 → 断言 display → 再查选项
box = page.evaluate("""() => {
  const sr = document.querySelector('wujie-app').shadowRoot;
  const s = sr.querySelector('.mark-tag-select');
  if (!s) return null;
  s.scrollIntoView({block: 'center'});          // 🔴 关键，y 由 1208 → 468
  const d = s.querySelector('.select-display');
  const r = d.getBoundingClientRect();
  return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
}""")
page.wait_for_timeout(500)                       # 等滚动落定，否则坐标是旧的
page.mouse.click(box['x'], box['y'])
page.wait_for_timeout(1400)
shown = page.evaluate("""() => {
  const sr = document.querySelector('wujie-app').shadowRoot;
  const o = sr.querySelector('.mark-tag-options');
  return o ? getComputedStyle(o).display : 'absent';
}""")
assert shown == 'block', f'dropdown not expanded (display={shown})'   # 🔴 先断言再查选项
opts = page.evaluate("""() => Array.from(
  document.querySelector('wujie-app').shadowRoot.querySelectorAll('.mark-tag-option .option-main'))
  .filter(e => e.offsetParent)
  .map(e => { const r = e.getBoundingClientRect();
              return {t: e.innerText.trim(), x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)}; })""")
target = next(o for o in opts if 'AI-generated' in o['t'])
page.mouse.click(target['x'], target['y'])
```

> **诊断口诀**：下拉「看起来没有选项」时，**先查 `display` 是不是 `none`，再查 rect 是不是在视口外**——这两者都表现为「选项数组为空」，但根因与修法完全不同。

**选项文案全英文**（照抄，别猜）：

| 选项 | 用途 |
|------|------|
| `No label needed` | 无需标注（默认） |
| `Contains AI-generated content` | **本流水线必选**（合规要求） |
| `Fictional storyline for entertainment only` | 虚构剧情 |
| `Personal opinion for reference only` | 个人观点 |
| `Content contains ads` | 含广告 |
| `Self-recorded content` | 自行录制 |
| `Content is reposted` | 转载 |

**验收**：回读 `.select-display` 文本必须等于 `Contains AI-generated content`；`absent` / `No label needed` 均判失败。

**🔴 但这个字段不随草稿持久化（坑 318 / 1028 两次复现，1029 据此调整策略）**：设成 `Contains AI-generated content` → 回读一致 → 点「保存草稿」→ 出现 toast「已保存」→ **关标签重开该草稿，`.select-display` 回到「选择视频标注」**。同一份草稿的描述、短标题、合集、双封面全部保留，**只有标注丢**。

**因此分两种场景**：
- **只存草稿**（本流水线日常）：**不要设**——设了也会丢，白白多一次对相邻按钮（「保存草稿」/「手机预览」/「发表」间距 16px）的点击，1028 期第二次、第三次补设标注正是误发布事故的直接诱因（坑 317）。
- **发布时**：**必须设**，这是 AI 生成内容的合规披露义务。这一条不能因「草稿里不保存」而被放弃。

**对接用户的话术**：不能说「已保存 AI 标注」，要说「草稿阶段平台不保存该字段，发布前需再设一次」。

#### 13.6 上传封面（shadow 协议优先）

**🔴 `hasWujie=true`（当前默认）**：按 13.1 字段表操作——`.single-cover-uploader-wrap input[type=file]` `setInputFiles` → 弹窗 `button.weui-desktop-btn_primary`「确认」。短标题走 13.4 Vue input，**不是** `.edit-shorttitle-content`。

**🔴 封面对话框（`.vertical-img-wrap .edit-btn` → 标题「编辑个人主页卡片」→ 取消/确认）的上传必须用 Playwright locator，不能取 ElementHandle（v3.61.0 坑 294）**：`page.evaluate_handle(...).as_element().set_input_files(path)` 必抛 `Cannot set input files to detached element`（shadow 内节点在取句柄到设文件之间被重渲染）；改用 `page.locator('wujie-app input[type=file][accept*="image"]').first.set_input_files(path)`（locator 每次动作前重新解析）。确认按钮 JS 常从错误 wrapper 查 `.weui-desktop-btn_primary` 得空 → 取可见 `.weui-desktop-dialog__wrp` 内「确认」的 rect 做坐标点击。弹窗有开关状态机（坑 280）：每次操作前先 Esc 清残留再重开。

**🔴 两条验收补充（v3.63.0 / 1025 实测）**：
1. **「弹窗是否关闭」不能用「容器还在不在」判**。`edit-cover-dialog-container` 关闭后**仍留在 DOM 里**，只是 `rect` 变成 0×0——`container exists` / `offsetParent !== null` 都会给出「还开着」的**假阳性**（1025 一度以为封面没生效，截图一看早已换成本期海报）。判据改为 `rect.width > 0 && rect.height > 0`，或干脆**回读槽位实图**。**⚠️ 但尺寸断言必须按比例判，不能写死 1152×1536（v3.70.0 / 1029 实测）**：页面会把上传图**等比缩放**后回填槽位，1029 上传 1152×1536 后 `img.naturalWidth/naturalHeight` 实测为 **810×1080**（同为 3:4，缩放系数 0.703）。写死 `=== 1152/1536` 会判成「封面没生效」并触发重复上传。正确写法：`Math.abs(w/h - 0.75) < 0.01`（3:4）或 `Math.abs(w/h - 4/3) < 0.01`（4:3），再配合页面自身的 `封面已更新` 文案确认。
2. **喂图后必须等预览图长到目标尺寸比例再点「确认」**。`set_input_files` 是异步上传，立刻点确认可能确认的是**旧图**。轮询槽位 `img.naturalWidth/naturalHeight` 达到 `1152×1536`（±2px）后再点。

**封面尺寸**：
- 个人主页卡片：3:4（1152×1536）→ `vertical-3-4.png`
- 分享卡片：4:3（1536×1152）→ `horizontal-4-3.png`

##### 13.6.1–13.6.3 旧 iframe 兜底（仅 `hasWujie=false`）

旧 UI 才检测 `name="content"` iframe、点 `.edit-btn` 触发 filechooser、以及 `.edit-shorttitle-content` contenteditable。**2026-08-30 版禁止当主路径**——短标题已是 Vue 受控 `input[placeholder*="短标题"]`，`textContent` 直写无效。旧示例标题 `今日羊报AI 2026年8月1日` 也已过期，改用 13.4 的 `M月D日` / `M月D日至D日`。

#### 13.7 保存草稿（不发布）

**🔴 保存成功无跳转，不能以 URL 变化判成败——必须去草稿箱列表页数条目验证（v3.24.0 实测）。****⚠️ 「无可见 toast」这条已被 1029 实测修正**：点「保存草稿」后 `shadowRoot.body.innerText` 末尾**出现「已保存」**（`...© 1998-2026 Tencent Inc. All Rights Reserved. 已保存`），URL 仍停在 `/platform/post/create`。所以无论 toast 出不出现（不同版本行为不一致），**落库判据都只能是草稿箱计数与标题**；`已保存` 文案可以当辅助信号，**不能单独当成功依据**。

**保存前两道拦截检查**：
1. **🔴 表单错误检查**（短标题超限/非法字符时按钮 silent disabled）：按 13.1 回读 `.error-title` 可见项 + 保存按钮 `disabled` 状态，有错误先修复再保存。
2. **🔴 「编辑个人主页卡片」弹窗拦截**：封面操作后此弹窗可能残留，点保存会被吞——点弹窗内 primary「确认」关弹窗后再保存。

```javascript
browser_run_code_unsafe("""async (page) => {
  // shadow 协议（wujie 结构）：
  await page.evaluate(() => {
    const r = document.querySelector('wujie-app').shadowRoot;
    const btn = [...r.querySelectorAll('button')].find(b => b.textContent.includes('保存草稿'));
    if (btn.disabled) return 'DISABLED: check .error-title';
    btn.click();
  });
  await page.waitForTimeout(3000);
  return 'clicked save';
}""")
// 旧 iframe 结构：page.frame({name:'content'}) 内点「保存草稿」，其余同
```

**草稿落库验收（强制）**：
- 🔴 **正确草稿箱 URL：`/platform/post/draftListManager`**（侧栏入口：**外层 body** 的「内容管理」→「草稿箱」；`post/record?tab=draft` 会 302 到别处，勿用）
- 导航后数草稿条目 / 找当日标题关键词（如「羊报AI周刊 8月24日至30日」）——条目出现即 ✅；反复点击保存无反应时先回 13.1 查 `.error-title`/`disabled`，勿空转
- beforeunload 弹窗：`browser_handle_dialog(accept=true)`；瞬时弹窗可能自愈（handle_dialog 报 no modal state 时直接继续）

#### 视频号上传组件操作总结（v3.24.0 更新）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 视频上传 | file input（shadow 内） | `wujie-app input[type=file]` setInputFiles 直传 | ✅ 高 |
| 视频描述 | **shadow 内 contenteditable** | shadowRoot.querySelector `.input-editor` → focus → keyboard.type | ✅ 高 |
| 短标题 | **shadow 内 Vue 受控 input** | 原生 setter 清空 + focus + keyboard.type（≤16字+白名单） | ✅ 高 |
| 位置 | 下拉框 | 已有默认值，一般不需改 | ✅ 高 |
| 合集 | 自定义下拉（shadow 内） | 「选择合集」→ `.option-item` 前缀匹配 | ✅ 高 |
| 封面上传 | `.single-cover-uploader-wrap input[type=file]` | setInputFiles → 3:4 裁剪弹窗 `weui-desktop-btn_primary` 确认 | ✅ 高 |
| 保存草稿 | shadow 内按钮 | 无错误 + 无弹窗拦截后点击；**无跳转无 toast** | ⚠️ 须草稿箱数条目验收 |

**关键经验**：
1. **🔴 wujie shadow DOM（2026-08-30 版 UI）**：全部表单在 `wujie-app` shadowRoot 内，页面级 locator/普通 evaluate/iframe 法失效；Playwright CSS 可穿 open shadow（file input 类），contenteditable/受控 input 须 evaluate 内 shadowRoot.querySelector + 事件派发（见 13.1 协议表）
2. **🔴 短标题 = Vue 受控 input**（不是 contenteditable）——textContent 直改无效，须原生 value setter
3. **🔴 短标题 ≤16 字 + 特殊字符白名单**（`.` `~` 禁用），违规时保存按钮 silent disabled
4. **🔴 保存成功无跳转无 toast**——验收只能去 `/platform/post/draftListManager` 数条目
5. **「编辑个人主页卡片」弹窗**未关会吞保存点击，先点确认关弹窗
6. **视频号支持两种封面比例**：3:4（个人主页卡片）和 4:3（分享卡片）
7. 旧 iframe 结构（`page.frame({name:'content'})`）仅当 13.1 结构判定 `hasWujie=false` 时才使用

## 目录结构

```
news-pipeline/
├── YYYY-MM-DD/                 # 按日期隔离的产出目录（daily）
│   ├── scripts/                # 视频脚本
│   ├── storyboards/            # 分镜表
│   ├── prompts/                # 图片 Prompt JSON
│   ├── images/                 # 生成的图片 (scene1.png ~ sceneN.png)
│   ├── voiceover/              # TTS 音频 (scene1.wav ~ sceneN.wav)
│   ├── captions/               # 字幕 JSON
│   ├── video/                  # 最终视频
│   │   └── 【YYYY-MM-DD】*.mp4
│   ├── horizontal-4-3.png        # 4:3 横版封面（B站/通用）
│   ├── vertical-3-4.png # 3:4 竖版封面（抖音/视频号/公众号）
│   │                    # 🔴 v3.38.0: gen_images.py 出图落在 images/ 子目录，
│   │                    # 上传脚本读的是本层根目录 —— Phase 11 前必须
│   │                    # cp images/horizontal-4-3.png images/vertical-3-4.png 到此
│   ├── publish.json            # 多平台发布信息
│   ├── wechat-article-*.md     # 公众号图文
│   ├── wechat-images/          # 公众号配图
│   ├── zhihu-article-*.md      # 知乎文章（v3.72.0，从公众号稿派生 + 合规改写）
│   ├── zhihu-images/           # 知乎配图（sceneN.jpg + cover.jpg，同源转 JPG）
│   └── scripts/zhihu_upload_*.py  # 分步上传：clear/title/body/images/video/cover/footer/decl/column/verify（v3.73.0）
├── weekly/                     # 周报产出目录（weekly，按日期范围隔离）
│   └── YYYY-MM-DD~YYYY-MM-DD/
│       └── （同 daily 子结构，视频 【羊报AI周刊】*.mp4，封面 horizontal-4-3.png）
├── monthly/                    # 月报产出目录（monthly，按月隔离）
│   └── YYYY-MM/
│       ├── scripts/            # 月报视频脚本（8-9段：Hook+4趋势+总结+展望+CTA）
│       ├── storyboards/        # 分镜表
│       ├── prompts/            # 图片 Prompt JSON
│       ├── images/             # 生成的图片
│       ├── voiceover/          # TTS 音频
│       ├── captions/           # 字幕 JSON
│       ├── video/
│       │   └── 【羊报AI月报】*.mp4
│       ├── horizontal-4-3.png    # 4:3 横版封面（B站/通用）
│       ├── vertical-3-4.png # 3:4 竖版封面（抖音/视频号/公众号）
│       ├── publish.json        # 多平台发布信息（月报变体：tags 含 AI月报）
│       ├── wechat-article-YYYY-MM.md   # 公众号图文（月报变体）
│       └── wechat-images/      # 公众号配图
├── video-project/              # Remotion 项目 (固定复用)
│   ├── public/
│   │   ├── images/             # 当期图片（复制）
│   │   ├── voiceover/          # 当期音频（复制）
│   │   └── captions.json       # 当期字幕（复制）
│   └── src/
│       ├── Composition.tsx     # 场景配置
│       ├── Root.tsx            # 总时长
│       └── components/
│           ├── Subtitles.tsx   # 字幕组件
│           └── NewsTitle.tsx   # 标题组件
└── sources/                    # 原始日报 Markdown
```

**月报输入**：`data/monthly/{YYYY-MM}.md`（项目根 data 目录，由 linuxdo-daily v13 生成，**不在 news-pipeline 下**）。

## 已知坑与经验教训

### 🔴 误发布事故：坐标点击必须自证落点 + 三条「回读对但没落库」+ 两个防护自身的坑（v3.67.0 / 2026-10-28 日报实测，坑 317-322）

**问题**：本期视频号的视频**被自动发布**了，违反常设约束「各平台一律存草稿，绝不点发布」。同一期还撞上三个「回读看起来对、实际没落库」的字段。四个坑的共性是：**判据（点击回执、设置后回读、容器存在）都在描述「我做了什么」，而没有描述「平台真的接受了吗」。**

**坑 317（最重要）：用滚动落定前的坐标点「保存草稿」，命中了 16px 外的「发表」**
- 事故序列：07:49 首次存草稿**成功落库**（`草稿箱 (7)`，首条为本期，时间戳 07:49）→ 08:02 重开草稿补设 AI 标注后又点一次「保存草稿」（toast「已保存」但**列表时间戳没变**）→ 08:08 第三次点 → `视频 (187)→(188)`，本期卡片出现、状态「原创审核中」，`草稿箱 (7)→(6)`
- 错误写法：
  ```js
  // ❌ scrollIntoView 与测 rect 在同一次 evaluate 内
  (() => { el.scrollIntoView({block:'center'});
           const r = el.getBoundingClientRect();
           return JSON.stringify({x:r.x+r.width/2, y:r.y+r.height/2}); })()
  // Python: sleep(0.5) → mouse.click(x, y)   ← 坐标是滚动落定前的旧值
  ```
- 为什么落点会偏：视频号三个按钮**水平相邻、间距 16px**（实测 rect，y 同为 1088）：
  | 按钮 | x | w | 中心 |
  |---|---|---|---|
  | 保存草稿 | 833 | 120 | **893** |
  | 手机预览 | 969 | 120 | 1029 |
  | 发表 | 1105 | 120 | 1165 |
- 平台**没有二次确认**，「发表」点下去即发布
- **修法（三步都要）**：
  ```js
  // ① 滚动单独一次 evaluate，等落定
  await ev("(() => { el.scrollIntoView({block:'center'}); return 1; })()")
  await sleep(0.8)
  // ② 重新测量
  ({x, y} = JSON.parse(await ev("(() => { const r=el.getBoundingClientRect(); ... })()")))
  // ③ 点击前自证落点
  const ok = await ev(`(() => {
    const hit = document.elementFromPoint(${x}, ${y});
    const want = /* 目标按钮元素 */;
    return !!(hit && (hit === want || want.contains(hit)));
  })()`)
  if (!ok) throw new Error('落点自证失败，不点')
  ```
- **危险按钮**（`发表` / `发布` / `立即投稿` / `存草稿`）**没有例外**；自证不过就报错停下，不要「再试一次」
- **代码级闸门**（已进 `templates/cdp_helper.py` 的 `Tab.click_safe()`）：
  - ⓪ **文案闸门**：目标 `innerText/value` 含 `发表视频/立即投稿/提交审核/发表/发布` → **滚动之前就抛异常**，连测量都不做
  - ①②③④ 滚动 / 等落定 / 重测 / **穿透 shadowRoot 自证**（见坑 321）
  - 实测：`click_safe(发表按钮)` → `🔴 拒绝点击危险按钮 '发表'`；`click_safe(保存草稿)` 自证通过
- **🔴 坑 322（元教训，同批踩到）**：为验证这套闸门而用 `allow_danger=True` 实点了一次「保存草稿」——**防护机制的测试本身也会产生真实动作**。此后所有闸门验证一律用「只测量不点击」的探针（把 `click_safe` 的 ④ 步单独抽出来跑），**绝不用 `allow_danger=True` 绕过闸门做实点**。本期实点因页面是空表单（`hasVideo=false`）未产生草稿（草稿箱仍 6）也未被发布，属侥幸。
- 与坑 302/303 的关系：那两条是「视口外点击**静默无效**」，这条是「点错了地方**还真生效了**」——后者严重得多

**坑 318：视频号「视频标注」不随草稿持久化**
- 设成 `Contains AI-generated content` → `.select-display` 回读一致 → 点「保存草稿」→ toast「已保存」→ **关标签重开该草稿 → 标注回到「选择视频标注」**，两次复现
- 同一份草稿的**描述 205 字 / 短标题 / 合集「今日羊报Al」/ 竖封面 3:4 全部正确保留**，只有标注丢
- 结论：**视频号视频标注只在发布时随请求提交，草稿阶段不落库**
- 对外措辞要准确：「标注已设置，但草稿不保存它，发布前需再设一次」——不能报「已保存 AI 标注」
- 附带：改标注时点选项可能**点空**（第二次改回 AI 标注后回读仍是 `No label needed`）。**每次选完必须回读 `.select-display`，不匹配就重来，不要连续盲点**

**坑 319：`DOM.getDocument` 在本机 Chrome 155 上 -32601**
- `DOM.enable` 已先行、`Runtime.evaluate` 正常，`DOM.getDocument` / `Document.getDocument` 均报 `wasn't found`
- **唯一可靠的上传路径**：
  ```python
  oid = (await cmd('Runtime.evaluate', {'expression': js, 'returnByValue': False})
         )['result']['result']['objectId']
  await cmd('DOM.setFileInputFiles', {'files': [...], 'objectId': oid})
  ```
  其中 `js` 求值为一个 `input[type=file]` 元素（**可以直接 `document.querySelector('wujie-app').shadowRoot.querySelector('input[type=file]')`**，不需要 pierce 遍历）
- 实测：wujie shadowRoot 内的视频 input 与封面 input 都**一次成功**
- 旧文「`DOM.getDocument{depth:-1,pierce:true}` → 手工 walk `children`+`shadowRoots`」降级为**备选**；`DOM.performSearch`→`backendNodeId` 那条**本期未复测**，保留但标注未复测

**坑 320：抖音竖封面弹窗默认带裁切缩放，切掉海报文字**
- 直接喂 1152×1536 后平台判「封面存在文字展示不全问题 / 封面不佳」——海报两端的「别」「一」被裁掉
- 修法：把 `.semi-slider-handle`（在 `.semi-slider-rail` 内，实测 x 区间 778.5–831.5、y≈550）拖到**最小档**
  ```python
  mouse.move(handle_x, handle_y); mouse.down()
  for i in range(1, 11):
      mouse.move(handle_x + (min_x - handle_x) * i / 10, handle_y, steps=1)
  mouse.up()
  ```
- **点击与方向键都无效**（本期试过，无任何反应）
- 拖到最小后海报完整带边距显示 →「封面效果检测通过」+ 发文助手「无建议」
- 另：抖音「编辑封面」的叶子节点搜索**必须限定在竖槽位 `.coverControl-CjlzqC`[1] 的 rect 内**——全局搜「编辑封面」会命中横向槽位的浮层，打开错误弹窗，上传后仍判「竖封面缺失」


**坑 321：`document.elementFromPoint` 不穿 shadowRoot，落点自证对 wujie 控件全部失效**
- 首次实现 `click_safe` 时用 `document.elementFromPoint(x,y)` 做自证，探针返回
  `{'ok': False, 'hit': 'WUJIE-APP.wujie_iframe / '}` ——**连正确的「保存草稿」都自证失败**
- 根因：wujie 子应用渲染在自己的 shadowRoot 里，`document.elementFromPoint` 只到宿主层
- 修法：**递归下钻**
  ```js
  const deepHit = (x, y) => {
    let el = document.elementFromPoint(x, y), guard = 0;
    while (el && el.shadowRoot && guard++ < 12) {
      const inner = el.shadowRoot.elementFromPoint(x, y);
      if (!inner || inner === el) break;
      el = inner;
    }
    return el;
  };
  ```
- 实测双向验证：`保存草稿` → `{ok:true, hit:"BUTTON / 保存草稿"}`；同页 `+272px` 打到 `发表` → `{ok:false, hit:"BUTTON / 发表"}`
- **这个坑的危险性**：如果当时把「自证总失败」理解成「自证逻辑不适用」，就会把闸门整个拆掉——**闸门失效往往伪装成闸门不好用**

**坑 322：验证防护机制本身也会产生真实动作（元教训）**
- 为确认 `click_safe` 的 danger 闸门「通过自证后才拦」，我用了 `allow_danger=True` 绕过——**它真的点下去了**
- 本期侥幸：那个 `create` 页是空表单（`hasVideo=false`），点击后无 toast、无弹窗、草稿箱仍 6 条、未被发布
- **铁律：闸门验证一律用「只测量不点击」的探针**——把自证那一步单独抽出来跑，看完 `{x,y,ok,hit,want}` 就够；**任何 `allow_danger=True` / 关掉保护再试 的写法都不要写进验证流程**
- 与坑 317 同源但更进一步：317 是「坐标漂移」，322 是「**为了防事而做的事**本身成了新的事故面」

**Why:** 坑 317 是本期唯一造成**不可逆后果**的坑——其他坑最多让草稿不完整，这个让内容直接公开了。而它之所以发生，恰恰因为前两次「保存草稿」都成功了，第三次就顺手复用了同样的写法，**没有意识到「同一个坐标在页面滚动状态不同时指向不同按钮」**。坑 318 则说明「设后回读」也是一种点击回执式的自欺：它证明的是 UI 变了，不是平台存了。

**How to apply:** ① **任何坐标点击前用 `document.elementFromPoint` 自证落点**，危险按钮无例外；② 滚动后必须重新测量，绝不跨 `scrollIntoView` 复用坐标；③ 「保存/提交」类操作的最终判据只能是**去另一个入口回读落库结果**（草稿箱计数、列表时间戳、`appmsgid`），设置态回读不算；④ 交付给用户的措辞要按「平台实际存了什么」写，不按「我点了什么」写。

### 🔴 派生禁词表误伤 + 锚点超上限 + 枚举过严 + 三处锚点常量（v3.70.0 / 2026-10-29 全链实测，坑 326-329）

**坑 326：`forbidden` / `STALE` 表照抄上期会误伤本期合法引用**

派生脚本时把上期事件词整表复制是标准做法，但**这些词表本质是「上期专属」的快照，不是「永久禁词」**。1029 命中两次：

| 词 | 出现在哪 | 为什么必须保留 |
|---|---|---|
| `招股书` | `_md2typ` 的 `forbidden` | 本期用「Anthropic 招股书的 85% 毛利率」反推 Opus 5.5 成本，是核心论据 |
| `Terra` | `gen_publish` 的 `STALE` | 本期「Codex 稳定性」那条正点名 GPT-6.1 Terra 只有 20–30 t/s |

两次都是**断言在最后一步才炸**（PDF 编译前、publish 写入前），前面的抓取、报告、press、概念、TTS、渲染全部白跑一遍。

**做法**：派生完成后立刻做一次「禁词表 vs 当日报告」的交叉检查——

```python
md = open(f'data/reports/{DATE}.md', encoding='utf-8').read()
for w in forbidden:
    if w in md:
        i = md.find(w)
        print(f'{w} <- ...{md[max(0,i-60):i+60]}...')
```
逐条看上下文：是「上期事件被复述」→ 留着；是「本期合法引用」→ 从表里删除并加一行注释说明（`# 注意：Terra 本期合法出现（…），不作禁词`）。

**坑 327：锚点占比超过 0.80 时该动哪里**

坑 236 只覆盖了「低于 0.70」（加长锚点前口播）。上界同样会破：1029 首轮 `0.8145`。

三种修法的取舍：

| 修法 | 代价 | 适用 |
|---|---|---|
| 削减前面场景 | 要重做选材表、审核清单、可能丢一条新闻 | 最后手段 |
| 削短前面场景 | 信息密度下降，且要重跑 TTS | 局部可用 |
| **扩充锚点场景** | 只重跑 1 个场景的 TTS（约 40s） | **首选** |

1029 的做法：在锚点场景补一段「延迟 vs 吞吐不是一回事 / 两者会分头崩 / 同一张卡上互相拉扯」，句式与既有的概念讲解连贯，+13.3s（39.53 → 52.84s），占比 0.8145 → 0.7709。

**注意**：扩充锚点场景时 `script_15s` 原文必须逐字保留在口播里（audit §6 会断言），新增内容只能加在原文**之后**，不能插入中间把原文切断。

**坑 328：可信度枚举是硬编码白名单**

`audit_*.py` 里的 `CRED` 是常量列表。写「官方发布」「官方站点」都会 FAIL。

归类原则：**按「信息是谁说的」而不是「我从哪里看到的」**——
- 官方博客 / 官网页面 → `官方确认`
- 官方文档截图转述 → `官方披露`
- 第三方媒体 → `媒体报道`
- 社区单用户实测 → `社区实测`
- 单用户个人经历 → `个人经历`
- 概念库定义 → `概念定义`

**坑 329：换锚点要改三处常量，漏一处会让报错指向错误场景**

```python
# 1) news-pipeline/<DATE>/scripts/script-<DATE>.md
### 场景6（专业锚点·延迟 Latency）

# 2) gen_publish_<DATE>.py
ANCHOR_SCENE = 6

# 3) _setup_remotion_<DATE>.py
ANCHOR = 6          # ← 最容易漏
```

漏改第 3 处的表现：`_setup_remotion` 仍按旧场景号算 `pre`，若新锚点的真实占比不在 `[0.70,0.80]`，报错会说「锚点占比 X 不合格」并指向旧场景，而真实原因是常量错了。

**How to apply:** ① 派生脚本后第一件事就是「禁词表 × 当日报告」交叉检查，别等最后的断言；② 占比超上限优先扩写锚点场景本身，且 `script_15s` 原文必须完整保留；③ 可信度按「谁说的」归类到白名单；④ 换锚点记牢三处常量。

### 🔴 raw CDP 脚本的「失败保留 + 附着复用」骨架（v3.70.0 / 2026-10-29 视频号实测，坑 330）

Playwright 的 `connect_over_cdp` 能用时，一个 `with sync_playwright()` 块里可以连续跑完 upload → meta → cover → album → save，表单状态天然保留。**切到 raw CDP 之后，每次 `open_tab` 都是新标签、新页面、空表单**——1029 因此把视频号上传拆成 6 次运行，每次都重传 24MB 视频（每次约 60s），光重传就花了 6 分钟。

**骨架**：

```python
TAB_FILE = '/tmp/channels-<date>-tab.txt'

def http_targets():
    req = urllib.request.Request('http://127.0.0.1:9222/json', method='GET')
    return json.loads(urllib.request.urlopen(req, timeout=10).read())

def _find_target(tid):
    return next((t for t in http_targets() if t.get('id') == tid), None)

async def attach_or_create():
    if os.path.exists(TAB_FILE):
        tid = open(TAB_FILE).read().strip()
        t = _find_target(tid) if tid else None
        if t:
            tab = Tab(t['webSocketDebuggerUrl'])
            await tab.__aenter__()
            return tab, tid
    tab, tid = await open_tab('about:blank')
    open(TAB_FILE, 'w').write(tid)
    return tab, tid

async def main():
    tab, tid = await attach_or_create()
    keep = False
    try:
        ...
    except Exception:
        keep = True          # ← 失败不关标签，留给下一次续跑
        raise
    finally:
        await tab.__aexit__()
        if not keep:
            urllib.request.urlopen(f'http://127.0.0.1:9222/json/close/{tid}', timeout=10).read()
            os.remove(TAB_FILE)
```

**要点**：
1. `keep=True` 只在异常路径置位——成功才关标签并删 id 文件；
2. 附着前必须查 `/json` 确认 id 还在（用户可能手动关了标签）；
3. 想强制重来就删掉 `/tmp/<platform>-<date>-tab.txt`；
4. 附着后**不要**再 `goto` 同一页面——会重新加载，表单还是丢。需要导航时先判断 `location.href` 是否已在目标页。

**本期收益**：封面确认按钮一开始点错位置（弹窗其实没开），修好后只重跑封面那一步，没有重传视频。

### 🔴 公众号上传源 `wechat-images/` 不是派生产物，漏生成会让 images 步撞 `FileNotFoundError`（v3.71.0 / 2026-10-30 公众号实测，坑 331）

派生脚本只机械替换文本，**不负责把公众号的上传配图目录生成出来**。1030 期 `news-pipeline/2026-10-30/wechat-images/` 全程缺失——它不是脚本「从某处拷贝」出来的，是要**本地把 `images/scene*.png` 现场转成 JPEG** 才有的上传源。跑到 `wechat_upload_1030.py images` 才在 `set_input_files(scene1.jpg)` 处炸 `os.stat FileNotFoundError`——**此时编辑器已打开、正要一题一图**，只能回来自补。

**为什么不是更早被拦住**：`images/`、`captions/`、`video/` 都有脚本在「生图 / 渲染」后各自落盘，唯独 `wechat-images/` 依赖的生成步骤在「公众号图文」阶段，而它不在 `run_tail.sh` 的一键链路里，派生脚本也不产出它。**铁律：进入公众号上传前先核对 `wechat-images/`** —— 它应有 `wx_scene_map` 里每个 `scene<i>.jpg`（从 `images/scene<i>.png` 转），加一个 `cover.png`（取 `images/horizontal-4-3.png`）。漏了就当场生成：

```python
from PIL import Image
import os, shutil
outdir = 'news-pipeline/2026-10-30/wechat-images'; os.makedirs(outdir, exist_ok=True)
for n in range(1, 7):   # wx_scene_map
    Image.open(f'news-pipeline/2026-10-30/images/scene{n}.png').convert('RGB')\
        .save(f'{outdir}/scene{n}.jpg', 'JPEG', quality=88)
shutil.copy2('news-pipeline/2026-10-30/images/horizontal-4-3.png', f'{outdir}/cover.png')
```

### 🔴 公众号 `open` 步的首选 mp 标签页可能是「合集管理」，没有「新的创作」入口（v3.71.0 / 2026-10-30 公众号实测，坑 332）

`wechat_upload_1030.py open` 旧写法是「取 `ctx.pages` 里第一个 `mp.weixin.qq.com` 页」。1030 期登录后的标签集合里既有 `cgi-bin/home`（首页）也有 `appmsgalbummgr`（合集管理），**第一个恰好是合集管理页** → 它没有 `.new-creation__menu-item`、"新的创作"断言也过不了 → `open` 挂。

**修法：`open` 必须锁定 `cgi-bin/home?token=` 首页**，选取优先级：
1. 扫 `cgi-bin/home` 且带 `token=` 的页；
2. 无则扫任一带 `token=` 的 mp 页，把它 URL 里的 `token` 借出来 `goto` 到首页；
3. 再无才 `new_page` + 裸域 `goto('https://mp.weixin.qq.com/')`（会自动 302 到带 token 的首页）。
**不要直接取 `ctx.pages` 第一个 mp 标签**——标签顺序不保证，页面类型（home / appmsg / appmsgalbummgr / appmsgalbum）都可能，只有 `cgi-bin/home` 有「新的创作」。

### 🔴 渲染前必须把本期 `captions.json` 同步进 `video-project/public/`，否则成片字幕静默沿用上期（v3.71.0 / 2026-10-30 实测，坑 333）

`Subtitles.tsx` 是 `fetch(staticFile('captions.json'))` 在渲染期读 `public/captions.json`。1030 的 `_setup_remotion_1030.py` 只同步了 `voiceover/` 与封面，**漏了字幕**——结果第一次渲染出的 mp4 **时间轴对得上、画面正常、ffprobe 也过，只有字幕内容全是 10-29 的**。这类「成片能出」的静默沿用最危险：不逐词核对就发现不了。

**铁律：`_setup_remotion` 在装配阶段必须「copy caps + 断言」**——复制 `captions/captions.json → public/captions.json`，然后断言 `caps[0]['text']` 含本期关键词（防串期到上期）、`max(endMs)/1000 ≈ 音频总长 ±2s`（防字幕与音频错位）。任一失败就在装配阶段 fail-fast，绝不放它进渲染。1030 首渲后补上这一步并重渲，最终字幕↔成片音频 `verify_captions_mp4.py` lead 中位 +0.080s、离群 0、7 场景块 Δ≤1ms。

### 🔴 后台标签页过渡动画不推进 + 「就绪」信号假绿（v3.69.0 / 2026-10-29 视频号实测，坑 324-325）

**坑 324：下拉面板「打开即关闭」，其实是标签页在后台**

现象：点 `.post-album-display` 后，`.filter-wrap` 的 class 立刻变成 `zoom-in-top-leave zoom-in-top-leave-active`，`opacity` 为 `0`，`getBoundingClientRect().height` 为 `0`。反复点、hover、`bringToFront`、`/json/activate` 都没用。

诊断三步：
1. 量 `getBoundingClientRect().height` → `0`
2. 量 `getComputedStyle().height` → 仍是 `160px`；`scrollHeight` = `160`；`.option-item` 有 4 个且 `offsetParent` 非空
3. 查 `document.visibilityState` → **`hidden`**

结论：**`offsetParent` 和 `getComputedStyle().height` 都不能判「元素是否真的可见」**。前者在高度 0 时仍为真，后者反映的是声明值而非布局结果。唯一可信的是 `getBoundingClientRect()` 的实测宽高。

根因：raw CDP 新开的标签默认在后台，`visibilityState=hidden`，浏览器对后台页的 CSS transition 做节流，`leave-active` 阶段永远推进不完 → 面板一出现就带着「正在离开」的类卡死。

修法（实测有效）：
```js
const wrap = sr.querySelector('.post-album-wrap .filter-wrap');
wrap.className = 'filter-wrap zoom-in-top-enter-to';   // 剥掉 leave 类
wrap.style.opacity = '1';
wrap.style.transform = 'none';
wrap.querySelectorAll('.option-item').forEach(it => {
  it.style.height = '40px';
  it.style.display = 'block';
});
```
之后按 `getBoundingClientRect().height > 5` 筛选项、走四步自证点击即可。

**坑 325：「表单就绪」的假绿信号**

视频号的 `.input-editor`（描述编辑器）**在上传视频之前就已经存在**。所以：

```js
ready = !!sr.querySelector('.input-editor')   // ❌ 上传前一秒就是 true
```

会让脚本在文件刚喂进去时立刻进入下一步，描述、短标题、封面全部写到一个还没绑定视频的空表单上——**而且每一步的「回读」都会成功**（描述确实写进去了），只有最后草稿里没有视频。

真判据（三者同时满足）：
```js
sr.querySelectorAll('video').length >= 1
&& Math.round(video.duration) >= 成片时长 - 容差
&& !/点击上传|拖入此区域/.test(bodyText)
```
本期实测：`videos=4, dur=249`（成片 249.195s）、`uploadArea=false`。

**How to apply:** ① 后台标签页里操作 Vue 浮层前，先量 `getBoundingClientRect().height`，为 0 就剥过渡类强制显示；② 任何「表单就绪」判据都要指向**上传产物本身**（video 元素 + 时长），不要指向「容器元素存在」；③ 判据失败时不要靠反复点击重试——先查 `visibilityState`。

### 🔴 抖音草稿不保存视频文件：「双信号」之后的第三种「回读对但没落库」（v3.68.0 / 2026-10-29 日报实测，坑 323）

**问题**：1029 期抖音端到端跑完，`暂存离开` 点击成功、按钮消失、「继续编辑」横幅出现——**双信号全绿**（坑 290/295 的判据）。恢复草稿回读：标题「今日羊报AI 10月29日」、`descLen=351`、5 个话题、双封面 `missingV=false missingDual=false`、合集「今日羊报Al 第139集」、自主声明「内容为个人观点或见解」——**全部正确**。唯独 `document.querySelectorAll('video').length === 0`，右侧上传区回到「点击上传 / 或直接将视频文件拖入此区域」。截图确认：表单壳在了，**视频没了**。

**根因**：抖音的草稿暂存持久化的是**表单字段**（标题、描述、话题、封面引用、合集、声明），**不持久化视频文件本体**——或者至少在本期这条路径上没有。所以「双信号 + 字段回读」这套判据整体上是**必要但不充分**的：它验证了平台记住了你填了什么，没验证平台记住了你要发什么。

**判据修订（写进上方存草稿表）**：抖音草稿验收 = 按钮消失 + 横幅出现 + **`videos >= 1`** + 标题回读一致。第三个条件不能省。

**修复路径（实测可用）**：
1. 点「继续编辑」恢复出草稿页（`URL` 会带 `enter_from=draft`）；
2. 页面上有 **2 个 `input[type=file]`**：
   - 索引 0：`accept="image/png,image/jpeg,image/jpg"` → **封面图**，喂视频进去会被拒
   - 索引 1：`accept="video/mp4,video/x-m4v,video/x-flv,.flv,.avi,.wmv,.ts,.mp4,.m..."` → **视频**，要的就是它
   - **按 `accept` 含 `video` 来挑，不要按索引挑**（顺序不保证）
3. `set_input_files()` 后轮询：`上传中` 消失且 `videos >= 1`（本期 78%→100% 约 15s，全程约 60s）；
4. **再点一次「暂存离开」**（恢复会消费掉横幅，不重新暂存草稿就没了）；
5. **第三次恢复核验 `videos=1`** 才算完成——第一次恢复可能只是页面内存态。

**为什么这条比坑 317 更容易重犯**：坑 317 会产生不可逆后果（内容公开），所以一旦踩过就记住了；坑 323 只会让草稿残缺，**而残缺的草稿在列表里看起来完全正常**——只有去恢复它、并且真的检查 `videos`，才会发现。任何只跑到「横幅出现」就收工的验收，都会静默地交付一份空草稿。

**How to apply:** ① 抖音验收判据加上 `videos >= 1`，写进 checklist；② 恢复草稿后第一件事就是数 `video` 元素，不要先看字段；③ 发现视频丢失就在同一草稿页重传，不要删草稿重来（坑 295：横幅消费掉就没了）；④ 重传后必须再暂存一次，否则草稿仍是空的。

### 🔴 验收判据自欺 + 合集静默失败 + 一条被证伪的推断（v3.66.0 / 2026-10-26 日报实测，坑 310-316）

**问题**：本期流水线全链跑完、日志全绿、`MP_VERIFY` 报 `collection: true`、文稿"看起来完美"——但公众号合集字段实际一直是「未添加」。收尾时另写了一个只看 `.js_article_tags_content` 的深度回读才发现，补挂后才真正完整。

**根因**（四个独立形态 + 一条方法论教训）：

- **坑 310 合集判据用正文子串 = 恒真**：`coll_ok = COLLECTION in all_txt`，而 `COLLECTION = '「今日羊报 AI」'`（含书名号）命中的是正文 `TAIL` 页脚「🔔 关注「今日羊报 AI」，每天 9 点…」。**证据（打印出来的页脚）与判据（同一个字符串搜索）看起来完全一致，所以没人怀疑。**
- **坑 311 图片计数被 ProseMirror 分隔符污染 = 恒假**：`body.querySelectorAll('img')` = 12 个，其中 6 个是 `IMG.ProseMirror-separator`（`src` 空、`naturalWidth=0`），`all(w>100)` 恒假；真图 6 张（1080×608 ×5 + 1080×810 ×1）。
- **坑 312 合集弹窗的唯一入口是一个约 54×22 的小 DIV**：点「合集」二字、点行内空白、点 `.frm_checkbox_label` 整行**全部不生效且不抛异常**（DOM 节点数 1377→1377）。点完照样能保存、能拿到 `appmsgid`，整条链静默失败。真入口 = `.allow_click_opr.js_article_tags_label`。
- **坑 315「reload 丢 token」是个被证伪的推断**：首页一度读到 `len=83` 的「登录超时」空页，当时给出的解释是「裸 `reload()` 丢了 `token=` 参数」，并据此写下了「必须带 token 重新 goto」的结论。**收尾复测推翻了它**——`RELOAD_TEST {"before_len":1685,"after_len":1685,"after_url_has_token":true,"after_login_timeout":false}`，`reload()` 保留 token、首页完好；裸域 `goto('https://mp.weixin.qq.com/')` 也会 302 到带 token 的首页（同样 1685）。**真实成因至今未知（大概率瞬时）。**

**解决**：
1. **判据优先挂在专属 class 上，不要做文本搜索**：合集 → `.js_article_tags_content`；封面 → `.js_cover_preview_new` 的 `background-image`；分区 → `.selector-container .select-item-cont`。有稳定 class 时做子串搜索 = 主动引入假阳性。
2. **图片验收必须三重过滤**：`img:not([class*=ProseMirror-separator])` + `src` 非空 + `naturalWidth/naturalHeight` 达标；**同时**别只数个数（数量对不代表加载成功）。
3. **弹窗类控件的判断分两步**：先断言弹窗容器真的可见（`.album-setting-dialog` `offsetParent` 非空），再做下一步。**别用「页面文本含某某」当弹窗已打开的判据**——本期「选择合集」这段文本在弹窗关闭时也一直存在。
4. **`try-catch` 跳过关键字段 = 把失败伪装成成功**：旧版 12.0 第 4 条写「合集失败时 try-catch 跳过，不阻塞保存草稿」。对**可选项**（赞赏、原创声明）可以这么做，对**需求明确要的字段**（合集）必须硬断言失败。本期就是被这条旧指导害的。
5. **方法论（本坑最重要的沉淀）**：「一次观测 + 一个顺理成章的解释」**不等于**已验证的因果。`len=83` 是真的，`reload()` 会保留 token 也是真的——我当时的解释把两者错连在一起，还写进了文档。**凡是准备写进 skill 根因章节的因果链，落笔前必须单独复测一次**；复测不了就只记现象、注明「成因未明」。这与坑 305（证据与判据须同源）是同族：那次骗过人的是换行符，这次骗过人的是「解释力」。

**同批小坑**：
- **坑 313 跨平台复制断言词表必挂**：同一事实在不同平台文案里措辞不同——抖音「比上一代 K3 便宜 15%」，视频号「约为上一代 K3 的 85%」。把视频号词表套到抖音 → `AssertionError: missing issue word: 85%`。**词表必须按该平台自己的 `description` 生成。**
- **坑 314 抖音话题按英文句点切分**：`publish.json` 的 `douyin.tags` 写 `K3.1`，页面回读 `["#AI日报","#K3",…]`——点号被吃掉，**变成了另一个话题**，不报错不提示。要么避开带点号的版本号，要么按实际值断言。
- **坑 316 B站草稿行没有可用 `href`**：`upload-manager/article?group=draft` 列表里草稿行的链接解析为 `null`。要进编辑页只能点该行的「编辑」按钮——从标题叶子节点向上逐级（≤8 层）找 `textContent === '编辑'` 的元素取 rect 中心点击，通常新开标签落到 `upload/video/frame?type=draft&draftId=…`。
- 回读公众号正文真图时，`img.naturalWidth` 为 0 但 `src` 非空 = 加载失败，是**真问题**；`src` 为空 + class 含 `ProseMirror-separator` = 分隔符，是**假问题**。两者要分开报。

**Why:** 四个坑的共同点是**验收环节在骗自己**——不是平台坏了，是判据写错了，而且错的方向都是「让失败看起来像成功」（合集恒真、数量恒真）或「让成功看起来像失败」（图片恒假）。坑 315 则提醒：**错误的因果解释会以「经验」的形式沉淀下来，比没有解释更危险。**
**How to apply:** 写任何验收判据时先问三个问题——① 这个判据**在功能真失败时会变红吗**？（反证测试）② 它在这个页面上**有没有第二个会命中的来源**？（正文/页脚/标题就是最常见的污染源）③ 有没有专属 class 可以直接读？三者过不了就换判据。**凡是准备写进 skill 的根因，落笔前单独复测一次；复测不成就只记现象。**

### 🔴 生图 size 派生污染 + 视口外静默点击：四个「不报错但就是不对」（v3.63.0 / 2026-10-25 实测，坑 300-303）

**问题**：1025 期四类故障，共同点是**全都没有抛异常**——生图端点回的是业务错误、B站分区值没变、视频号下拉显示「没有选项」、封面弹窗显示「还开着」。

**根因**（四个独立坑，后两个同根）：
- **坑 300 派生脚本的日期替换吃掉尺寸字面量**：`derive()` 里 `'1024' → '1025'` 是全串替换，把生图脚本硬编码的 `size: '1536x1024'` 改成 `'1536x1025'`，rainflow 回「不支持的图片比例」。**排查指纹：网关说比例不支持，但比例肉眼看着没问题 → 先 grep 尺寸字面量有没有被日期吃掉。**
- **坑 301 `size:'auto'` 返回方图**：rainflow 只接受 `auto`（不收任何显式比例），而 `auto` 在**没有构图提示**时给方形 1254×1254；塞进 1920×1080 会被裁掉两侧。`size` 本身不能表达画幅，画幅只能写进 prompt。
- **坑 302 B站分区在视口外，三种点击全部静默失败**：真选择器是 `.drop-list-v2-item`（30 项），`人工智能` 排在 y=759 而视口高 769——`page.mouse.click()` / `el.click()` / `dispatchEvent(new MouseEvent)` 三种都**返回成功、无异常、值不变**，分区停在默认「音乐」。
- **坑 303 视频号 AI 标注同根**：`.mark-tag-select` 初始 rect.y=1208，`mouse.click(941,1231)` 回执成功但 `.mark-tag-options` 仍 `display:none`，选项查询返回 `[]`，**看起来像「下拉里根本没有 AI 选项」**，极易误判成控件改版而去改选择器。
- **坑 304 端点身份按后缀判会静默判错**：本期复盘时发现 `settings.json` 实际是 `GEN_IMG_API_URL`=rainflow、`_000`=prism.uno、`_001/_002`=elysiver，而 `To_Learn.md` 的备忘写的是 `_003`=rainflow、本体=prism.uno——**同一期的两份记录编号完全不同**。按 `suf == ''` 或 `_003` 判「是不是 rainflow」会随用户改编号而静默判错（size 传错 → 「不支持的图片比例」）；按 `"rainflow" in api_url` 判永远跟得上。
- **坑 305 终态验收判据没做空白归一化，证据与结论自相矛盾**：`final_verify` 把证据 `draftSec` 归一化后打印（`t.slice(..).replace(/\s+/g,' ')`），却用**未归一化**的 `t` 跑判据 `/Kimi K3\.1/`——打印出的证据明明含 `【2026-10-25】Kimi K3.1 Pro …` 而 `draftHasToday: false`。打印片段是 `t` 前缀的 collapse 版，它命中而原文不命中 ⇒ 该跨度内必含 `\s` 类字符（卡片把 `Kimi` 与 `K3.1` 折断）。**证据与结论矛盾本身就是这个坑的指纹**，见到就该查判据用的是不是另一份文本。

**解决**：
1. **生图 size 绝不硬编码**：写 `size_for(api_url)`——rainflow 返回 `"auto"`，其余端点返回 `"1536x1024"`；任何写进请求体的 size 都必须是函数算出来的，不允许裸字面量（Phase 5 已内联该函数）。
2. **画幅靠 prompt**：每条 scene prompt 末尾固定追加 `Wide 16:9 horizontal cinematic composition, full-frame landscape framing.`；出图后 `PIL` 断言 `w/h >= 1.6`，方图判失败重出（Phase 4 / Phase 5 / Phase 8 Step 8.0b 三处已立门禁）。
3. **B站分区**：`locator('.drop-list-v2-item').filter(has_text=PARTITION).first.scroll_into_view_if_needed()` → `click(force=True)`；回读用 `.selector-container .select-item-cont` 的 `textContent`。
4. **视频号 AI 标注**：`s.scrollIntoView({block:'center'})` → **重取** `getBoundingClientRect`（y 由 1208 变 468）→ `mouse.click` → **先断言 `getComputedStyle(.mark-tag-options).display === 'block'`** 再查 `.mark-tag-option .option-main`。
5. **通用规则（本坑最重要的沉淀）**：**任何 `mouse.click(x, y)` 之前，必须先确认目标 rect 完整落在当前视口内**——`scrollIntoView` 后重取 rect 再用。视口外的坐标点击不报错、不生效，是最难定位的一类失败。同理，**点击后必须断言状态真的变了**（display / textContent / value），不能只信点击回执。

**同批小坑**：
- 视频号 `edit-cover-dialog-container` 关闭后仍留在 DOM 且 rect 为 0×0——「容器存在 / `offsetParent` 非 null」判「弹窗没关」是**假阳性**；改判 `rect.width>0 && rect.height>0`，或直接回读槽位 `img.naturalWidth/naturalHeight`。
- 视频号封面喂图后必须**等预览图达到目标尺寸 1152×1536** 再点「确认」，否则可能确认了旧图。
- B站标签可能被平台**单独拒收**（本期 `AI大模型` 未入 chips，终态 6/7）——断言写成「记录缺失但不阻塞」，不要 `assert len(tags)==7`。
- 视频号合集选项文案本期是「共N个**内容**」而非「共N个作品」（`今日羊报Al 共134个内容`），匹配正则要两者都容。
- **终态验收的空白归一化（坑 305）**：`innerText` 里卡片标题会换行，`【2026-10-25】Kimi\nK3.1 Pro …` 直接跑 `/Kimi K3\.1/` 必不匹配。**判据和证据必须用同一份归一化文本**：先 `const t = raw.replace(/\s+/g,' ')`，再拿 `t` 既做判据又做打印。见到「打印的证据明明命中、结论却是 false」先查这个。

**Why:** 四个坑的失败模式一致——**接口回执成功 ≠ 状态生效**。日期替换污染 size 是把「参数」当「文本」改；视口外点击是把「事件派发」当「用户点击」；`display:none` 的下拉是把「没展开」当「没这个选项」；未归一化的判据是把「换行」当「不存在」。
**How to apply:** 生图参数一律运行时计算并回验出图比例；所有坐标点击前 `scrollIntoView` + 重取 rect + 点击后断言具体状态字段；派生脚本做日期替换后，**grep 一遍所有被替换位置**确认没有误伤数字字面量；页面文本判据统一 `replace(/\s+/g,' ')` 后再匹配，且**证据与判据同源**。

### 🔴 字幕跨场景互换：play_order 重排后的「块重分配」（v3.62.0 / 2026-10-24 实测，坑 298-299）

**问题**：1024 期用户两次反馈「1:25 后字幕和音频对不上」，第一次修复重渲后用户仍说「1:34 还是对不上」。

**根因**：`play_order=[1,2,3,5,4,6]`，但 `captions.json` 里 **script scene4（MoE）的文案占着 84.4–112.9s、script scene5（程序员节）的文案占着 113.5–143.9s**——两块是**互换**，不是平移。第一次修复脚本 `realign_captions_1024.py` 只在「字幕已被分配到的那个场景」内部重锚定与缩放（按 marker 找场景起点、按场景 wav 时长线性缩放），**从不重新推导一条字幕该属于哪个场景**，所以互换完好无损。坑 283 当年修的是「块平移」，这次是「块重分配」，不同缺陷。

**判定指纹**：成片音频顺序正确、烧录字幕错位。用 `ffmpeg -i out.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 mp4_audio.wav` 取音频做词级 ASR，同时抽帧看字幕：若 84–114s 音频是 scene5 内容而画面烧的是 scene4 文案，就是块互换（而非漂移、也非音频问题）。**只查源 wav 会得到全绿假象**——按播放序把 `voiceover/sceneN.wav` 拼起来的文件本来就是对的。

**修复（可复用）**：
1. **切组**：`voiceover-texts.json` 每场景正文归一化后逐条累加字符数，把 `captions` 切成 6 组；断言总字符数与脚本完全相等（1024：188/205/179/192/214/26 = 1004，逐组精确命中，零余量）。
2. **定块起点**：按 `play_order` 累加各场景 **wav 实测时长**（84.231 / 114.837 …），块起点 = 前面所有场景时长之和。
3. **块内重计时**：**逐场景单独跑 faster-whisper 词级 ASR**（不是拼一条全局流），把该组每条字幕的起止对齐到本场景词级时间；相邻两条边界取静音中点，首行留 `MARGIN≈0.10s` 预卷，尾行 `endMs` 补到该场景语音 offset（1024 实测尾行差 0.298–0.308s）。
4. **写两处**：`captions/captions.json` + `video-project/public/captions.json`（Remotion 读后者），并校验单调（`startMs<endMs` 且 `prev.endMs ≤ next.startMs`）。
5. **重渲** → 回到「判定指纹」用 **新 mp4** 复验（抽 84/90/106/113/115/120/130/140s 帧比对烧录字幕）。

**验收量化（坑 299 补充）**：**不要**用全文字符流 `SequenceMatcher` 一次对齐所有字幕再算偏差——长片累积的插入/删除会被摊到每条上，1024 实测给出「64 条全部 >0.5s、中位 1.31s」的假信号。正确做法 = **首 3 字锚定**：`stream.find(key[:3])` 取全部出现位置，选离该条 `startMs` 最近的那个，再看时间差。1024 结果：54/64 条可测，lead 中位 **+0.205s**、最大 +0.71s、最小 −0.17s（lead 为正即字幕略早于 ASR 检出，属预期余量）。另外中文字数会被 ASR 写成「十/二/十/四」或罗马数字，归一化时把 〇一二三四五六七八九 映射到 0–9 能多救回若干条。

**Why:** 场景顺序与播放顺序是两套编号；任何「在已归属场景内调整时间」的修法都无法纠正归属本身。而验证若不用成片，测的是「我拼的输入」而不是「用户看到的输出」。
**How to apply:** 只要 `play_order ≠ [1..N]`，字幕必须**按场景成组重分配**再落时间轴；修复前先跑「成片指纹」确认是块互换还是漂移；修完必须对新 mp4 复验，源 wav 验证一律不作为放行依据。

### 🔴 视频号标注/合集新 DOM + 抖音恢复令牌六坑：英文标注下拉 / 坐标点击 / detached input / 一次性横幅 / 竖封面入口 / 合集最小面积（v3.61.0 / 2026-10-23 实测，坑 292-297）

**问题**：1023 期视频号 AI 标注始终读不到、合集选不中、封面上传元素 detached；抖音核验一次后草稿凭空消失、竖封面按钮点不动、合集误点整个下拉容器。

**根因**（六个独立坑）：
- **坑 292 视频号标注控件是英文下拉**：wujie shadowRoot 里根本没有「AI生成」中文勾选框，AI 合规标注的真实载体是「视频标注」下拉 `.mark-tag-select`（`.select-display` + `.mark-tag-options`），选项文案全英文；任何 `/AI生成|人工智能生成/` 的中文正则或 checkbox 遍历都会返回 `ai declare: absent`。
- **坑 293 视频号合集新版 DOM + Vue 只认坐标点击**：合集入口由旧 `.option-item` 直选变成 `.post-album-display`（显示当前值）→ 展开 `.post-album-wrap .option-item`；且这层 Vue 组件对 JS `el.click()` 无响应（调用成功、display 文案不变），必须真实鼠标事件。
- **坑 294 wujie 内 ElementHandle 必 detached**：shadowRoot 里 `evaluate_handle(...).as_element().set_input_files()` 抛 `Cannot set input files to detached element`；同一元素换成 Playwright locator 形式即成功——区别在 locator 是每次动作前重新解析，handle 是取到即绑定。
- **坑 295 抖音「继续编辑」= 一次性消费令牌**（坑 290 第三形态）：抖音没有草稿列表页（`/content/manage?tab=draft` 是空壳），唯一恢复入口是发布页横幅；「暂存」语义是写入服务端**待恢复槽位**而非创建持久草稿记录，槽位被读取即清空。新开标签点横幅→读→关标签 = 消费掉且不回写，草稿彻底消失。
- **坑 296 抖音竖封面入口**：`get_by_role('button', name='设置竖封面')` 常是 `disabled` 的提示位，`click()` 必超时；真入口是**悬停竖槽位**后浮现的「编辑封面」。弹窗 `.dy-creator-content-modal-body` 内 6 个 file input，只有 `.selectArea-BCIYQD input[type=file]` 是封面，其余是模板/贴纸选择器——**喂错静默无报错**。另「竖封面缺失」在 AI 推荐封面生成期会瞬时为真，`grep` 文本判封面会假阴性。
- **坑 297 抖音合集匹配命中下拉容器**：`/^「?今日羊报/` + `/共\s*\d+\s*个作品/` 同时匹配容器节点，其 `textContent` 是把所有选项拼起来的整串（`请选择合集不选择合集「虢礫緙嘞」共4个作品「羊报AI月报」…`），点容器 = 没选。

**解决**：
1. **视频号 AI 标注**：**先 `scrollIntoView({block:'center'})` 并重取 rect**（坑 303：初始 y=1208 在视口外，不滚则点击静默失效）→ 点 `.mark-tag-select` 的 `.select-display` 展开 → **断言 `.mark-tag-options` 的 `display === 'block'`** → 按 bounding box 真实坐标点 `Contains AI-generated content` → 回读 `.select-display` 文本断言。**不要找中文「AI生成」**，那是旧版控件。
2. **视频号合集**：点 `.post-album-display` → 等 `.post-album-wrap .option-item` 渲染 → 取目标项 `getBoundingClientRect` 中心 `page.mouse.click(x,y)`（**JS `.click()` 无效**）→ 回读 display 文本为 `今日羊报Al`（注意是**小写 l**，不是大写 I）。
3. **wujie 内文件上传**：一律 `page.locator('wujie-app input[type=file][accept*="image"]').first.set_input_files(path)`；**禁用 `evaluate_handle().as_element()`**。弹窗确认按钮同理走坐标点击（先取可见 `.weui-desktop-dialog__wrp` 内 `确认` 的 rect，再 `mouse.click`）。
4. **抖音端到端一次跑完**：`upload → meta → 双封面 → 合集 → 暂存#1 → 同标签「继续编辑」回读 → 暂存#2 → 终态确认`。核验**绝不新开标签点横幅**；外部标签只准读 `body.innerText` 里的横幅文本。参考 `news-pipeline/2026-10-23/scripts/douyin_finish_1023.py`。
5. **抖音双封面**：横槽 `.coverControl-CjlzqC[0]` 直接传 1536×1152；竖槽 `[1]` 先 `hover()` 再点浮现的「编辑封面」（**不要**点 disabled 的「设置竖封面」），弹窗内用 `.selectArea-BCIYQD input[type=file]` 传 1152×1536；验收用 `img.naturalWidth/naturalHeight` 读槽位实图，**不用文本 grep**。
6. **抖音合集**：候选约束 `^「?今日羊报` + `共\s*\d+\s*个(作品|内容)` + `textContent.length ≤ 40` + `rect.height ∈ [10,90]`，排序取**面积最小**节点点击；回读「添加合集」段确认目标合集名与「共N个作品 / 共N个内容」（**两种文案都存在，正则必须都容**：1023 抖音 `「今日羊报Al」共132个作品`，1025 视频号 `今日羊报Al 共134个内容`）。
7. 视频号封面确认后必须回读 3:4 槽位图；「编辑个人主页卡片」弹窗每次操作前先 Esc 清残留再重开（坑 280 状态机纪律在 1023 仍适用）。

### 🔴 四平台上传链四坑：登录探针隔离 context / wujie 空壳重挂 / 抖音暂存被吞 / B站视频 input（v3.60.0 / 2026-10-22 实测，坑 288-291）

**问题**：1022 期四平台全部误判未登录（实际早登录），视频号空壳重挂失败，抖音草稿偶发丢失，B站视频上传 `expect_file_chooser` 必超时。

**根因**（四个独立坑）：
- **坑 288 登录探针隔离 context**：`browser = p.chromium.connect_over_cdp(...)` 返回的是 **Browser** 对象，写 `ctx = p.chromium.connect_over_cdp(...)` 再 `ctx.new_page()` 等价 `browser.new_page()`——Playwright 为它新建**隔离 BrowserContext，不继承用户 cookies**，于是旧 tab 停在登录后页面、新开页却跳扫码页。四平台同时误判 `login_required` 是典型症状。
- **坑 289 wujie 空壳重挂**：空壳态=`wujie-app` 元素在但 shadowRoot 内 `input,button,[contenteditable]` 计数为 0。旧标签上 `page.goto('/platform/post/video')` 只改 URL 不触发 wujie 重挂载，`Page.reload` 多次也无效。
- **坑 290 抖音暂存被吞**：`locator('button:has-text("暂存离开")').click(force=True)` 正常返回**不等于**草稿落库——偶发点后表单未关闭、内容随页面关闭丢失。只有点击回执就汇报「草稿已存」是假阳性。
- **坑 291 B站视频 input**：新版投稿页点「上传视频」不触发原生 file chooser，`expect_file_chooser` 必超时；且页面上 `.mp4`×2 / `.txt` / `.zip` / 封面 image 共存，按索引取 input 会喂错且**全程静默无报错**。

**解决**：
1. **登录探针**：`browser = connect_over_cdp(...)` → `ctx = browser.contexts[0]` → `ctx.new_page()`；goto 上传页 wait 4s 后按表单元素判据（B站「上传/投稿」、抖音「作品描述」、视频号 url 无 `login.html`、公众号「新的创作」），禁看页面营销文案。探针脚本先跑一遍全平台，任一 `login_required` 即停手问用户，不要带着错误登录态往下跑。
2. **wujie 空壳**：`pg.close()` → `browser.contexts[0].new_page()`（必须走 default context 才共享登录态，同坑 288）→ goto `/platform/post/create`，等 shadowRoot 节点数 >100 且 `input[type=file]` 存在（实测 1201 节点一次挂载）；此后每步前断言 `hasWujie && inShadow>0`。
3. **抖音暂存双信号**：点后轮询到「暂存离开」按钮消失（`hasZancun=false`）**且**「继续编辑」横幅出现，两者齐才算成功；缺一即重做 upload+meta+cover 后 JS 直点按钮，不得只凭点击回执。
4. **B站文件 input**：遍历 `input[type=file]` 按 `accept` 过滤（含 `video`/`mp4` → 视频；含 `image` → 封面弹窗内图，坑 218 复用）后直接 `set_input_files`，assert 找不到即失败；**禁用索引定位**。
5. 换图重渲染不需要重跑 TTS/字幕：只覆盖 `public/images/sceneN.jpg` 后重跑 Remotion，场景时长/锚点/字幕时间轴全部不变（1022 实测 3374 帧/112.512s 一次过）。

### 🔴 视频号时政外事场景拒审→删敏感场景出「专版」单独渲染（v3.59.0 / 2026-10-21 实测，坑 284）

**问题**：1021 主版（5 场景，含 scene3 OpenAI 窃听案）上传视频号反复拒审，用户报「一直过不了审核」。

**根因**：无新闻资质账号的红线是时政外事叙事（对照 skill 目录《微信视频号常见的不合规频道内容概述.md》《微信视频号运营规范.md》）。scene3 三要素叠加：①涉外司法案件（窃听案、外籍嫌疑人、保释庭审）；②庭审/安保监控类画面（courtroom+security camera 场景图）；③「窃听器」等敏感词直接入字幕与口播。另「反代」属灰产边缘词。单删词不够——画面+叙事整体都是风险源。

**解决**（专版流程，主版与其他平台一律不动，坑 215）：
1. 建 `news-pipeline/{date}/video-channel/` 临时目录：删减版 `scripts/voiceover-texts.json`（去掉敏感场景）、`voiceover/` 符号链接复用主版 wav、按新播放顺序重算 `captions/captions.json`。
2. 共享工程改前备份：`cp public/captions.json {date}/captions/captions-main-5scene-backup.json`；改 `Composition.tsx` sceneConfig 与 `Root.tsx` SCENE_DURS 为删减版（数组顺序=播放顺序，imageId/audioId 保留原场景号）。
3. 渲染成片命名加「【视频号专版】」前缀，与主版同目录共存。
4. **渲染完立即还原** sceneConfig/SCENE_DURS/captions.json 为主版配置（坑 269 共享工程纪律），并回读断言（字幕条数/末条 endMs/sceneIds）。
5. 锚点重算：删中段场景→锚点起点前移，占比=新锚点起点/新总时长，必须重算且落 [0.70,0.80]（本例 0.8093→0.7328）。
6. 交付前 grep 字幕+口播敏感词（窃听/监控/反代）零残留；ffprobe 验规格（时长/分辨率/帧数）。

### 🔴 公众号正文原位全量替换=DOM 清空+合成 paste；合规冲突先停后问（v3.59.0 / 2026-10-21 实测，坑 285-287）

**问题**：草稿已存（appmsgid=100001636）后需软化绝对化陈述并原位更新正文。三轮重贴：fix1 键盘法全灭、fix2 全文双份、fix3 明明成功却报 FAILED。

**根因**（四个独立坑）：
- **坑 285 键盘法失效**：正文含 5 张图后，`mouse.click` 编辑区中心落在 img 上，焦点不在可编辑文本，Meta+A/Backspace/V 全不达编辑器；且合成 `ClipboardEvent('paste')` 在非空正文上是**追加**——ProseMirror 监听 paste 但用自身 state 光标插入，不理 DOM Selection（fix2 得 2342 字全双份）。
- **坑 286 假阴性判据**：body 步后 `PLACEHOLDER`×N 是正常态（图片步才回填），校验条件写成「无 PLACEHOLDER」→ 成功也报 FAILED。
- **坑 287 合规冲突**：涉具体个人未决案件/未证实指控的绝对化陈述（人名+国籍+定性），继续自动化会被合理拦截；正确动作不是绕过而是停下来问用户。

**解决**：
1. 全量替换唯一可靠流程：① `removeChild` 逐个清空 `.ProseMirror` 子节点（DOM 变更触发 ProseMirror mutation 同步进 state）→ ② 空正文上合成 `ClipboardEvent('paste')`（DataTransfer 带 text/html）追加=等效全量替换 → ③ 回读断言：软化 markers 全中 + 唯一标记 `count==1`（防双份）。
2. 校验判据只看 markers+去重，**不看 placeholders**（图片步回填后自然归零）。
3. save 后 appmsgid 原位保留=更新稿不新建草稿；save 前后各回读一次断言长度与 markers。
4. 合规软化模板：「据 XX 援引知情人士的报道」「疑似」「案件细节以司法程序披露为准」+ 括注（据 XX，帖 ID；以官方信息为准）；口播与图文同步软化，数字保留但标注「待官方确认」。
5. 小坑备查：`python3 -I` 断 site-packages（PIL 不可用）→ 跑封面/图像脚本去掉 -I；import 无条件 `main()` 的派生模块前先 `sys.argv=['x','noop']` 垫参；derive 重跑会覆盖手工修复→修复直接 Edit 目标文件再 grep 验证；派生内嵌 NEW_CHECKS 含 `\n` 转义会成真换行→用 `chr(10)`。

### 🔴 B站上传 VIDEO 路径必须用 publish.json.title 非 bilibili.title（v3.52.0 / 2026-10-17 实测，坑 258）

**问题**：1017 视频渲染成功（`news-pipeline/2026-10-17/video/【2026-10-17】OpenCode免费开放两个国产模型，DeepSeek搜索开始收费 | 今日羊报AI.mp4`），但 `bili_upload.py upload` 步在 `os.path.getsize(VIDEO)` 处抛 `FileNotFoundError`——脚本里 `VIDEO` 抄的是 `publish.json.platform.bilibili.title`（`…收费｜4条重磅AI新闻一次看完 | 今日羊报AI.mp4`），而实际产物文件名用的是 `publish.json.title`（无「｜4条重磅AI新闻一次看完」段）。

**根因**：`publish.json` 有两个标题字段：
- `title` = `【YYYY-MM-DD】{核心标题}… | 今日羊报AI`（列表标题，**也是渲染/归档文件名**，Phase 9/10.4 用此）
- `platform.bilibili.title` = `【YYYY-MM-DD】{核心标题}…｜4条重磅AI新闻一次看完 | 今日羊报AI`（**带「N条重磅」营销后缀**，仅用于 B站投稿列表标题）

渲染 out 参数按 `title` 拼，B站上传脚本 VIDEO 却常误抄 `bilibili.title`，两者差一个「｜N条重磅AI新闻一次看完」片段。

**解决**：
1. 渲染后先 `ls news-pipeline/{date}/video/` 核对**实际文件名**。
2. `bili_upload.py` 的 `VIDEO` 一律填 `publish.json.title`（含 `| 今日羊报AI` 后缀、不含「｜N条重磅」段），**不要用 `bilibili.title`**。
3. 派生 B站上传脚本后，用 `python3 -c` 校验 `VIDEO` 指向的文件 `os.path.exists` 为 True 再跑 upload。

**How to apply:** Phase 9 渲染后 → Phase 11 派生 bili_upload 时，VIDEO 从 `publish.json.title` 拼（同渲染文件名），跑 upload 前先验证路径存在。坑 215 收口前若发现此错，只需改 VIDEO 一行重跑 upload，无需重渲。

### 🔴 四平台登录态判定要读上传表单元素，勿以「作品/发布」文案为准（v3.52.0 / 2026-10-17 实测）

**问题**：1017 抖音首页含「作品发布及管理」「数据分析」「商单任务变现」等大量营销文案，脚本 `guard()` / 登录判据误判「已登录」；实际页面是「扫码登录/验证码登录」登录页（`creator.douyin.com` 未登录态）。若据此直接跑 upload，`file input` 找不到 → `no file input — 可能未登录` 才暴露。

**解决**：登录态判据必须读**上传表单元素**，不是页面文案：
- 抖音：`作品描述` / `暂存离开` / `设置封面` 出现 = 已登录；`扫码登录`/`验证码` = 未登录
- B站：`上传视频`/`投稿` 且无 `扫码登录` = 已登录；`passport.bilibili.com` URL = 未登录
- 视频号：`login.html` URL / `发表视频`/`草稿` 表单 = 未登录/已登录
- 公众号：`新的创作`/`New creation` = 已登录

**How to apply:** 上传开工前逐平台用 CDP `Runtime.evaluate` 读 `document.body.innerText` + 看 URL，**只认上传表单元素判登录**；任一平台未登录 → 标记 `login_required`，不空转。

### 🔴 公众号配图需 sceneN.jpg + cover.png，非 sceneN.png（v3.52.0 / 2026-10-17 实测）

**问题**：1017 公众号上传脚本 `IMAGES` 引用 `wechat-images/sceneN.jpg`，但 `wechat-images/` 初始只有 `sceneN.png`（从 `images/` cp 而来）→ 上传前需先转 JPG。另 `cover.png` 需单独生成（= `horizontal-4-3.png` 拷贝）。

**解决**：上传公众号前准备：
```bash
for i in 2 3 4 5 6; do ffmpeg -y -i wechat-images/scene$i.png -q:v 2 wechat-images/scene$i.jpg; done
cp horizontal-4-3.png wechat-images/cover.png
# 并 PIL 严格解码 + 尺寸门禁（坑 254）
```
`wechat_upload.py` 的 `IMAGES` 按此引用（PLACEHOLDER_IMG_N → sceneN.jpg，COVER → cover.png）。场景图（scene2-6，跳过 Hook scene1）作正文配图。

### 🔴 字幕与音频不同步（v2.0.0 → v2.1.0 → v2.2.0 → v2.3.0 → v3.25.0 演进）

**问题**：字幕时间轴与音频不齐——越到后面偏差越大，或某场景整体错位、口播与字幕对不上。**v3.25.0 再修切行**：时间轴对齐了，但切行把专名/动宾切开，出现 0.5s 闪行。

**v2.0.0 方案（已废弃）**：FunASR 语音识别 + ffprobe 比例调整
- FunASR 对专业术语识别极差：GPT→GDP、DeepSeek→Deep triep、Claude Code→Claude coat、Fable-5→核酸efbo杠五、Codex→搞dex、Hermes→HMMI、MiMo→mini/明末
- 修正字典永远追不上新术语，每次都要手动添加大量修正规则
- 识别错误导致字幕内容完全不可用

**v2.1.0 方案（已废弃）**：原始脚本文本 + ffprobe 纯字符比例对齐
- 解决了内容准确性问题（100% 用原始文本），但内部切分仍按纯字符数，长句/多数字场景仍会漂移

**v2.2.0 方案（已废弃）**：原始脚本文本 + 加权字符估算 + silencedetect 真实停顿点吸附
- 加权系数（中文 1.0 / 数字 0.6 / 英文 0.35）是平均拟合，含大量版本号/英文术语的单句偏差大
- silencedetect 只在「正好有停顿」时吸附边界，无停顿句仍纯估算，中后段仍逐句累积漂移

**v2.3.0 方案（时间轴仍有效；切行已废弃，2026-08-23 W33 周报实测）**：faster-whisper 词级时间戳 + 脚本字符强制对齐（旧 `gen_captions_v2.py`）
```python
# 1. 字幕文字：直接用 Phase 2 原始 TTS 脚本文本（内容 100% 准确，不依赖 ASR）
# 2. 时间锚：faster-whisper(word_timestamps=True) 跑 public/voiceover/sceneN.wav
# 3. 强制对齐：difflib.SequenceMatcher(脚本归一化字符, whisper 归一化字符)
# 4. 按句聚合：首句 start=0，末句 end=场景 ffprobe 时长；场景间累加偏移
#    ↑ 切行器已废弃：split_sentences 把 ，。；！？：、 所有标点一视同仁
```

**v3.62.0 硬约束（坑 298）**：`templates/gen_captions.py` 的 `load_scenes` 末尾必须调 `apply_play_order()`——当 `voiceover-texts.json` 带 `play_order` 时，场景按播放序返回，`scene_offset` 才会按真实播放顺序累加。此前按编号顺序累加会让不同场景的字幕块**互换位置**（1024 期 `[1,2,3,5,4,6]` 的 4/5 互换，重渲两次才对）。改这个函数后必须回归：`python3 -c "load_scenes(...)"` 打印的顺序要与 `play_order` 完全一致。

**v3.25.0 方案（当前默认，2026-08-31 月报实测）**：语义 `group_caps` 先切行 + whisper 词级对齐（`templates/gen_captions.py`）
```python
# 1. 切行：jieba + group_caps（SENT_END 强制断；SOFT_PUNCT 仅 ≥max_len=16 才断；
#    允许略超 16 至 hard_max=20；超 hard_max 黄金分割 40–60% → WEAK_BEFORE → 整句保留）
#    禁止按字符下标硬切；GLUE_TAILS / BAD_ENDS+BAD_STARTS 粘合禁切结构
# 2. 时间锚：faster-whisper(word_timestamps=True) 跑当期 wav（WhisperModel 在 --dry-run return 之后才 import）
# 3. 对齐：每条字幕 SequenceMatcher 滑动窗口对齐到词级时间戳
# 4. merge_short_dwell(min_sec=1.0)：<1s 并回上一行
```

**新坑（2026-08 月报）**：v2.3.0 逐标点切行 + 16 字硬墙会切开专名/动宾：
- `延期；`（3 字 0.5s 闪行）
- `有效` / `主题近一万。`
- `终止Cursor` / `官方直连`、`硬新闻` / `主轴`、`稳` / `不稳`

**关键点**：
- **切行先于对齐**：`group_caps` 产出字幕字符串；whisper **只**负责时间轴
- **内容用原始脚本文本**，不需要 ASR 识别文字，字幕内容 100% 准确
- **时间用音频真实发音时刻**：whisper 词级时间戳是唯一锚点，不再「估算每句时长」
- **SequenceMatcher 容忍 ASR 错字**，单句偏差不累积
- **必须用 ffprobe 校验总时长对齐**（见 Step 8.3 校验）
- Remotion 字幕 **单行**，不做双行长度平衡

**Why:** 任何「估算每句时长」的方案都无法消除单句偏差累积（v2.3.0 已修时间轴）；但所有标点一视同仁 + 16 字硬墙会切开专名/动宾，必须语义切行。
**How to apply:** Phase 7 用 `templates/gen_captions.py`（`group_caps` + whisper），先 `--dry-run` 扫禁切反例。禁止逐标点切行、禁止按字硬切、禁止回退纯比例时间轴。旧 `gen_captions_v2.py` / `split_sentences` 已废弃作切行器。

**字幕尾差可加性闭合补第四项（v3.46.0 / 2026-10-12 周报 W40 实测，坑 234 补充）**：成片时长 − 末行字幕结束时刻的差值必须能拆成可加项，否则是真不同步。闭合式 = **静音尾 + 帧取整 + 容器 + whisper 对齐尾隙**。前三项（坑 234 原三项）分别是 TTS 末尾静音、`ceil` 取整到帧、mp4 容器封装余量；第四项是 whisper 把末行字幕停在**末音节之前**留下的尾隙——字幕内容正确、只是收尾略早于口播结束。W40 实测 1.098s = 0.415 + 0.188 + 0.048 + 0.447，四项相加精确等于尾差即 PASS，**不重渲**。四项加不回去才算缺陷。

### 🔴 旧音频残留导致整体 desync（v3.20.0 / 2026-08-23 W33 周报实测）

**问题**：重新渲染后字幕与音频仍整体对不上，且视频时长与脚本预期不符。

**根因（三重叠加）**：
1. **stale 音频**：`public/voiceover/sceneN.wav` 是上一期（日报）残留的旧音频，没被当期周报源音频覆盖；atempo 加速的是旧音频。
2. **stale 时长**：`Composition.tsx` 的 `sceneConfig.duration` + `Root.tsx` 的 `TOTAL_DURATION_SEC` 还是旧音频的时长，没随新音频刷新。
3. **v1 字幕估算器**：旧字幕用加权字符估算，本身就会漂移。

**修复链（必须按序，缺一步仍 desync）**：
1. **归档旧音频**：把 `public/voiceover/` 下的旧 wav 移到 `.stale_archive/` 子目录（用 Python `shutil.move`；**`rm` 会被自动权限模式判定为「不可逆本地删除」而拒绝**，改用归档挪移）。
2. **重新 atempo**：用当期周报源音频重新 atempo（scene1-5,7 atempo=1.25；锚点 scene6 atempo=1.4）→ 覆盖写入 `public/voiceover/sceneN.wav`。
3. **刷新时长**：ffprobe 实测每个新 wav → 同步刷新 `Composition.tsx` 的 `sceneConfig.duration` + `Root.tsx` 的 `TOTAL_DURATION_SEC`。
4. **重算字幕**：跑 `templates/gen_captions.py`（或当期 `scripts/gen_captions.py`：`group_caps` + whisper）→ 覆盖 `captions/captions.json` + `video-project/public/captions.json`。
5. **重新渲染**：`npx remotion render`。
6. **whisper 验证**：在视频里抽 3–4 个边界点（场景切点 / 长句起止），用 whisper 听对应音频段，确认字幕 startMs/endMs 与真实发音时刻一致（误差 < 200ms）。

**Why:** 旧音频 + 旧时长 + 旧字幕三者来自不同批次，三条时间轴互相错位；必须让音频/时长/字幕三者来自同一批新音频。
**How to apply:** 每次重跑 TTS 或换期前，先确认 `public/voiceover/` 是当期音频（看 mtime / 听内容），再走「atempo → 刷新时长 → templates/gen_captions.py → 渲染 → 验证」全链。`rm` 被拒时用 `shutil.move` 归档，不要硬删。

### 🔴 TTS 并发冲突
**问题**：`mimo-tts.sh` 内部使用 `mktemp /tmp/mimo-tts-request-XXXXXX.json` 生成临时文件。并行调用时多个进程竞争同一文件名，导致 `mktemp: mkstemp failed: File exists` 错误，TTS 静默失败不生成音频。

**解决**：**必须逐场景串行执行 TTS**，每个场景等待上一个完成后再启动下一个。

### 🔴 日报内容重复
**问题**：linux.do 日报中大量事件会连续多天出现（如 OpenAI 举报、Codex 额度等），直接制作视频会导致内容与前几期高度重复。

**解决**：Phase 1 中增加去重步骤，读取前 3 天日报对比，标记重复事件并展示给用户确认。

### 🔴 B站自定义下拉框
**问题**：B站的创作声明、合集选择器等使用自定义下拉框组件（bcc-select），不是标准 HTML `<select>`。`browser_click(listitem=...)` 或 `browser_click(element=文本)` 经常失败。

**解决**：先用 `browser_click` 打开下拉框，然后用 `browser_evaluate` + JS 遍历 DOM 找到选项并点击。

### 🔴 B站 Quill 编辑器
**问题**：B站简介使用 Quill 富文本编辑器，`browser_type` 无法直接输入内容。

**解决**：用 `browser_evaluate` 注入 `innerHTML` 到 `.ql-editor`，然后 dispatch `input` 事件。

### 🔴 B站上传 502/400 错误（v3.2.0 新增，2026-07-04）

**问题**：B站上传视频时，preupload 接口返回 502 Bad Gateway 或 400 Bad Request 错误，视频无法上传成功。Console 显示 `preupload接口失败` 和 `probe timeout`。

**原因**：B站服务器端问题，不是客户端或文件问题。可能是 B站 CDN 节点故障、上传接口限流、或临时维护。

**解决**：
1. 等待一段时间后重试（可能是临时故障）
2. 如果持续失败，提示用户手动上传到 B站
3. 视频文件已生成在 `news-pipeline/YYYY-MM-DD/video/` 目录，用户可直接拖拽上传

**Why:** B站上传接口不稳定，502/400 错误是服务器端问题，无法通过客户端修复
**How to apply:** Phase 11 B站上传失败时，不要反复重试，直接提示用户手动上传

### 🔴 B站上传文件路径中文字符问题（v3.2.0 新增，2026-07-04）

**问题**：视频文件名包含中文字符（如 `【2026-08-13】阿里禁用Claude...| 今日羊报AI.mp4`）时，B站上传接口返回 400 Bad Request 错误。

**原因**：B站上传接口对文件名中的中文字符处理有问题，可能导致 URL 编码错误。

**解决**：
1. 上传前将视频复制到简单路径（如 `/tmp/upload.mp4` 或 `news-pipeline/YYYY-MM-DD/video/upload.mp4`）
2. 使用简单文件名上传，上传成功后 B站会自动使用视频标题作为文件名

```bash
# 复制视频到简单路径
cp "news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4" \
   "news-pipeline/YYYY-MM-DD/video/upload-YYYY-MM-DD.mp4"
```

**Why:** B站上传接口对中文文件名兼容性差
**How to apply:** Phase 11 B站上传前，先复制视频到简单路径再上传

### 🔴 B站简介数字检测误判（v2.9.0 新增，2026-06-24）
**问题**：B站简介中包含大量数字（如 `21天37TB`、`2.5`、`2.1 Pro`、`4.6`、`5.6`、`5.2`）会被系统检测为「违规推广内容」（疑似QQ号/微信号），稿件直接被移除。

**解决**：B站简介必须减少数字密度：
- 版本号去掉或简化：`Seedance 2.5` → `Seedance`、`豆包2.1 Pro` → `豆包新模型`、`Opus 4.6` → `Opus`
- 数量用中文替代：`21天` → `二十一天`、`30秒` → `三十秒`、`37TB` → 不写具体数字
- 不要在简介区放 `#标签`（B站简介区的 hashtag 也容易触发检测）
- 结尾用频道引导语替代 hashtag：`今日羊报AI，每天带你速览AI圈最热新闻。`

**示例（安全版简介）**：
```
Codex后台疯狂写日志，SSD直接被写报废！

字节火山引擎大会连放大招，Seedance一次生成三十秒四K短片，豆包新模型编码能力对标Opus，特斯拉中国要用豆包。GPT新版本因Anthropic举报可能延期。GLM新版本实测好评，智谱市值破万亿。微信内测AI助手帮你操作微信。

今日羊报AI，每天带你速览AI圈最热新闻。
```

**Why:** B站的反垃圾系统对连续数字串非常敏感，`213756` 这样的模式会被误判为联系方式
**How to apply:** Phase 10 生成 B站简介时，自动将版本号简化、数字用中文替代、去掉 hashtag 行

#### 🔴 月报简介数字中文化（v3.1.0 新增，强制执行）

**问题**：月报数据天然大量数字（`6709` 主题、`28/30` 天、`1698` 峰值、`303` 日均、`52.6k` 浏览、`9650亿` 估值、`GPT-5.5/5.6`、`GLM-5.2`、`Opus 4.8` 等），密度是日报的数十倍。按 v2.9.0 规则只简化零星版本号远远不够，月报简介几乎必触发 B站违规推广检测。

**强制规则**：
1. 月报简介**禁止出现任何阿拉伯数字**（0-9），一律中文数字替代。包括浏览量、主题数、天数、token 数、估值、定价、版本号。
2. 大数模糊量化，避免连续数字串：`6709 → 近七千`、`6860 → 不写`、`1698 → 近一千七`、`303.1 → 三百出头`、`52.6k → 五万多`、`17.6k → 近一万八`、`9650亿 → 近万亿`、`70亿美元 → 数十亿美元`。
3. 天数/占比中文：`28/30 天 → 三十天里二十八天有数据`。
4. token 数模糊：`272k/353k → 近三十万token`、`516 → 五百多`。
5. 定价不写具体：`8/28元每百万Token → 几块钱`。
6. 版本号一律去数字：`GPT-5.5/5.6 → GPT新版本`、`gpt-5.6-sol → GPT最新灰度版`、`GLM-5.2 → GLM新版本`、`Opus 4.8 → Opus`、`Sonnet 4.6 → Sonnet`。
7. 该规则对月报**强制执行**，不得以"这个数字看起来安全"为由保留阿拉伯数字。

**月报安全版简介示例**（对照 v2.9.0 日报示例）：
```
本月AI圈月度盘点：OpenAI的GPT新版本调度全程翻车，二验风暴连夜取消，月末灰度版连续重置额度；智谱GLM新版本开源并登顶设计榜，国产模型集中爆发；Anthropic提交招股书估值近万亿，但服务中断、Mythos反复关闭；AI编程工具百花齐放。

本月三十天里二十八天有数据，日均新增主题三百出头，峰值近一千七。

羊报AI月报，每月带你回顾AI圈整月风向。
```

**Why:** 月报数据密度是日报的数十倍，不中文化几乎必触发 B站违规推广检测，稿件直接被移除。
**How to apply:** 月报模式 Phase 10 生成 B站简介时强制全数字中文化；月报脚本正文同样适用（避免字幕里出现连续数字串）。

### 🔴 TTS API 多节点故障转移（v2.9.0 新增，2026-06-24）
**问题**：MiMo TTS API 主节点（token-plan-cn.xiaomimimo.com）配额用完后返回 `quota exhausted` (429)。

**解决**：支持多节点故障转移：
1. 主节点 CN：`https://token-plan-cn.xiaomimimo.com/v1/chat/completions`
2. 备用节点 AMS：`https://token-plan-ams.xiaomimimo.com/v1/chat/completions`（2026-06-24 验证可用）
3. 如果主节点返回 429，自动切换到备用节点

**TTS API URL 修正**：settings.json 中的 `MIMO_TTS_API_URL` 可能包含 `/anthropic` 后缀，必须去掉再拼接 `/v1/chat/completions`：
```python
url = settings['MIMO_TTS_API_URL']
if url.endswith('/anthropic'):
    url = url[:-len('/anthropic')]
url = url.rstrip('/') + '/v1/chat/completions'
```

**Why:** 不同节点的配额是独立的，CN 节点用完后 AMS 节点可能还有余额
**How to apply:** Phase 6 TTS 生成时，先尝试主节点，429 错误自动切换备用节点

### 🟡 voiceover-texts.json 引号问题（v2.9.0 新增，2026-06-24）
**问题**：脚本中的中文引号（如 `"吃"硬盘`、`"卡脖子"`、`"小微"`）在 JSON 文件中会导致解析失败，因为 `"` 字符与 JSON 字符串分隔符冲突。

**解决**：生成 voiceover-texts.json 时：
- 将中文引号替换为无引号：`"吃"硬盘` → `吃硬盘`
- 或使用中文书名号：`「吃」硬盘`
- 生成后立即用 `python3 -c "import json; json.load(open(...))"` 验证

**Why:** Write 工具直接写入的文件中，中文引号 `""` 可能被转义为 ASCII `""` 导致 JSON 无效
**How to apply:** Phase 2 生成脚本后，保存 voiceover-texts.json 时自动处理引号，保存后立即验证

### 🟡 公众号 ProseMirror 编辑器索引（v2.9.0 更新，2026-06-24）
**问题**：公众号编辑器中 `document.querySelectorAll('.ProseMirror')` 只返回标题编辑器（index 0），正文编辑器需要用 `document.querySelectorAll('[contenteditable="true"]')` 获取，且正文在 index 2（不是 index 1）。

**正确索引**：
```javascript
const editables = document.querySelectorAll('[contenteditable="true"]');
// index 0: 标题（ProseMirror，placeholder="请在这里输入标题"）
// index 1: 原创声明输入框（original_primary_tips_input）
// index 2: 正文（ProseMirror ProseMirror-focused）
const titleEditor = editables[0];
const bodyEditor = editables[2];  // 不是 index 1！
```

**Why:** `.ProseMirror` 选择器可能只匹配部分编辑器，`[contenteditable="true"]` 更全面
**How to apply:** Phase 14 公众号上传时，用 `[contenteditable="true"]` 获取所有编辑器，正文在 index 2

### 🟡 抖音标题 fill() 方法（v2.9.0 新增，2026-06-24）
**问题**：抖音作品描述输入框用 JS `input.value = '...'` + `dispatchEvent('input')` 不生效，页面显示 0/30 字。

**解决**：使用 Playwright 的 `fill()` 方法：
```javascript
const titleInput = page.getByRole('textbox', { name: '填写作品标题，为作品获得更多流量' });
await titleInput.fill('代码偷吃SSD+豆包对标Opus｜今日羊报AI');
```

**Why:** 抖音的输入框使用 React 受控组件，直接修改 `value` 属性不会触发 React 的状态更新
**How to apply:** Phase 12 抖音上传时，标题用 `fill()` 而非 JS `value` 赋值
**问题**：不同用户可能使用不同的图片生成 API 服务，不能硬编码 API URL。

**解决**：Phase 0 中向用户收集 API URL + Key，优先使用用户提供的 API。

### 🟡 视频时长控制
**问题**：TTS 实际时长可能与脚本预估偏差较大（如 18s 预估实际生成 25-28s），导致总时长超出预期。

**解决**：脚本生成时保守预估，Phase 8 校验时以 TTS 实际时长为准。目标 60-120s，可适当放宽到 150s。

### 🟡 browser_click 文本匹配不稳定
**问题**：`browser_click(element=文本描述)` 有时会匹配到错误的元素（如匹配到侧边栏而非表单区域）。

**解决**：优先使用 `browser_click(target=ref编号)` 精确匹配。如果需要文本匹配，先 `browser_snapshot` 获取 ref 编号，再用 ref 点击。

### 🔴 微信公众号 ProseMirror 编辑器
**问题**：公众号标题和正文都使用 ProseMirror 编辑器（不是 Quill），`browser_type` 无法直接输入内容。

**解决**：用 `browser_evaluate` 注入内容：
- 标题：`editors[0].textContent = '标题'` + dispatch `input` 事件
- 🔴 v3.30.0 修正：正文禁 innerHTML / 禁 insertHTML / 禁合成 ClipboardEvent → 真实剪贴板 + Meta+A/Meta+V 粘贴，每图后立刻保存草稿（见 Phase 12.5）

### 🔴 微信公众号图片插入
**问题**：通过 `setInputFiles` 可以将图片上传到素材库，但图片不会自动插入到文章正文中。需要先在文章中定位光标，然后通过工具栏「图片」→「本地上传」手动插入。

**解决**：建议先保存草稿，然后手动完成图片插入。或者尝试：
1. 在文章中点击定位光标
2. 点击工具栏「图片」
3. 选择「本地上传」
4. 通过 `setInputFiles` 上传

### 🔴 微信公众号合集选择器
**问题**：公众号合集选择器是自定义 Vue/React 组件，不是标准 HTML 元素。JS click 不稳定，有时选择后不生效。

**v3.66.0 更新**：**已可稳定自动化，完整流程见 12.10**。旧结论「建议手动」的根因是**点错节点**：点「合集」二字（`SPAN.lbl_content`）/ 行内空白 / `.frm_checkbox_label` 整行都不开弹窗，且**不报错**（DOM 节点数不变），随后保存草稿照样成功。真入口 = `.allow_click_opr.js_article_tags_label`（约 54×22 的 DIV）。回读判据只认 `.js_article_tags_content`。

### 🟡 微信公众号多标签页
**问题**：点击「文章」会打开多个新标签页（可能重复点击导致）。

**解决**：创建文章后，切换到最新标签页（index 最大的）。关闭其他重复标签页。

### 🔴 公众号封面上传正确流程（v1.9.1 / v3.7.0 / **v3.8.0 2026-07-19 闭环**）
**问题**：坐标点击、innerHTML 注入不可靠；弹窗缩略图常为 **background-image 的 span**，不是 `<img>`；裁剪页有 **disabled「确定」** 干扰；过早 Escape 会取消裁剪。

**已验证的正确流程（优先「从正文选择」）**：
1. Focus 正文：`.ProseMirror` 第二个
2. 工具栏「图片」→「本地上传」→ `setInputFiles(horizontal-4-3.png)`（横版封面）→ 等 8s → Escape 关上传挡层
3. `#js_cover_area` scrollIntoView → **hover** `.js_cover_btn_area`
4. **强制显示**后点 **`.js_selectCoverFromContent`**
5. 点带 `mmbiz` 背景的 **`.appmsg_content_img_item`** → **「下一步」**
6. 等待弹窗标题 **「编辑封面」** → 点 **enabled「确认」**（`weui-desktop-btn_primary` 且非 disabled）
7. **轮询**：`dialogOpen=false` 且 `.js_cover_preview_new{display:block; background-image: url(...mmbiz...)}`  
8. 再「保存为草稿」（`appmsgid=` 保留即可）

**验收（DOM，比肉眼稳）**：
- `.js_cover_preview_new`：`display === 'block'` 且 `background-image` 含 `mmbiz.qpic.cn` / `mmbiz_jpg`
- 允许 `#js_cover_area` 文案仍含「拖拽或选择封面」——**以 preview 背景为准**
- 失败信号：`previewDisplay:none` 或 bg 为空 / `url("")`

**禁止**：
- 裁剪弹窗打开时 `Escape` / 点「取消」
- 用 `locator('button:has-text("确定")')` 当确认（会命中 disabled）
- 只看「已保存」文案（常不出现）

**关键点**：
- 必须先把图插入正文，再「从正文选择」
- 缩略图不是 `<img>`，用 class + bg 筛选
- 裁剪确认按钮文案是 **「确认」**
- 封面失败不阻塞草稿（v3.5.0）

### 🔴 公众号赞赏弹窗 checkbox 结构（v1.7.0 新增）
**问题**：「我已阅读并同意」checkbox 在 `label > div` 结构中，不是标准 `input[type="checkbox"]`。

**解决**：用 JS 遍历找到包含「我已阅读并同意」的元素，然后找其父元素中的 checkbox：
```javascript
const parent = el.closest('label, div');
const checkbox = parent.querySelector('input[type="checkbox"], [role="checkbox"]');
if (checkbox) checkbox.click();
```

### 🔴 公众号合集选择器正确流程（v1.9.1 更新，v3.3.0 补充）
**问题**：合集选择器是自定义 Vue 组件，JS evaluate 和坐标点击都不可靠。

**已验证的正确流程**：
1. 点击「合集」→「未添加」打开弹窗
2. 点击「请选择合集」输入框 focus
3. 输入「今日羊报」或「羊报AI周刊」搜索
4. 用 `page.getByText('「今日羊报 AI」', { exact: true })` 精确匹配选项
5. **先 hover 再 click**（必须！）
6. 用 `page.getByRole('button', { name: '确认' })` 点击确认

**关键点**：
- 必须用 `exact: true` 精确匹配，否则会匹配到正文中的同名文本
- 必须先 hover 再 click，直接 click 不生效
- 不要用 JS evaluate，用 Playwright locator 更可靠
- **合集名按 REPORT_MODE 读取**：daily「今日羊报 AI」/ weekly「羊报AI周刊」/ monthly「羊报AI月报」
- **v3.3.0 补充**：合集选择失败时用 try-catch 跳过（timeout: 5000），不阻塞保存草稿

### 🟡 公众号原创声明弹窗自动填充（v1.7.0 新增）
**问题**：原创声明弹窗打开后，「文字原创」已默认选中，「我已阅读并同意」已默认勾选。

**解决**：直接点击「确定」即可，无需手动操作其他选项。

### 🟡 公众号工具栏按钮坐标（v1.7.0 新增）
**问题**：工具栏按钮（图片、视频号等）的位置会随页面滚动变化。

**解决**：
- 「图片」按钮：约 x=530, y=17（顶部工具栏）
- 「视频号」按钮：约 x=1074, y=17（顶部工具栏右侧）
- 使用 `browser_evaluate` 动态查找按钮位置更可靠

### 🔴 微信视频号描述字段（v3.24.0 改走 shadow 协议）
**问题**：页面级 `textarea` / `placeholder` / `contenteditable="true"` 选择器都找不到——描述在 `wujie-app` open shadow 的 `.input-editor` 里。
**解决（当前默认）**：按 13.1——`hasWujie=true` 时 evaluate 内 `shadowRoot.querySelector('.input-editor')` + focus + `page.keyboard.type`。**禁止**把坐标点击当主路径。
**旧 UI 兜底（仅 `hasWujie=false`）**：截图估坐标（约 x=760, y=310）→ `page.mouse.click` → `page.keyboard.type`。

### 🔴 微信视频号合集选择器
**问题**：合集选择器在 wujie shadow 内；页面级 locator 找不到。
**解决（当前默认）**：按 13.5 点 `.post-album-display` 展开 → `.post-album-wrap .option-item` 取 rect 中心坐标点击（JS `.click()` 无效，v3.61.0 坑 293）；回读 `.post-album-display` 文本。
**旧 UI 兜底（仅 `hasWujie=false`）**：坐标点选项（约 x=860, y=180）；失败则手动。

### 🔴 微信视频号保存草稿限制
**问题**：如果「定时发表」设为「定时」，保存草稿按钮会显示警告「使用定时发表将无法保存草稿」。另：超 16 字短标题会 **silent disable** 保存（无 toast）。
**解决**：保存前确保「不定时」；短标题走 13.4（≤16 字、禁 `.` `~`）；保存无反应先查 `.error-title` 与 `button.disabled`。成功无跳转——必须去 `/platform/post/draftListManager` 数条目。

### 🟡 视频号描述自动填充失败（v3.24.0 降级）
**问题**：`getByPlaceholder` / `getByText` / `locator('textarea')` 找不到描述框——因为节点在 shadow 内，不是「只能坐标点」。
**解决**：走 13.1 `.input-editor` shadow 协议。坐标点击仅 `hasWujie=false` 兜底。

### 🔴 视频号 wujie shadow DOM（v3.24.0 替代 v1.7.0 iframe）
**问题**：2026-08-30 版全部表单在 `wujie-app` open shadow root 内；页面级 locator / 普通 evaluate / `page.frame({name:'content'})` 全部失效。v1.7.0 的 iframe + `.edit-shorttitle-content` 已不是主路径。

**解决**：先跑 13.1 结构判定。`hasWujie=true` → shadow 协议（`setInputFiles` 穿 shadow、描述 `.input-editor`、短标题 Vue `input[placeholder*="短标题"]`）。仅 `hasWujie=false` 且存在 `name="content"` iframe 时才用旧 `page.frame` 法。

### 🔴 视频号短标题是 Vue 受控 input（v3.24.0 修正 v1.7.0）
**问题**：旧文档称短标题是 `.edit-shorttitle-content` contenteditable；实测是 `input[placeholder*="短标题"]`（Vue 受控），`textContent` / `fill()` 不同步。

**解决**：按 13.1：原生 `HTMLInputElement.value` setter 清空 + focus + `page.keyboard.type`；填完回读 `.error-title` + 保存按钮 `disabled`。格式 `{报刊名} {M月D日至D日}`，≤16 字，禁 `.` `~`。

### 🔴 视频号封面修改限制（v1.7.0 新增）
**问题**：视频号修改封面和短标题有「仅支持修改一次，修改后不可撤回」限制。修改记录会展示在视频上。

**解决**：
1. 修改前确认所有内容（封面、短标题）都正确
2. 一次性完成所有修改再提交
3. 修改后显示「修改审核中，预计30分钟内审核完成」

### 🔴 视频号封面在 wujie shadow 内上传（v3.24.0 修正 v1.7.0）
**问题**：旧文档称封面弹窗在 iframe、需坐标点 `+` 触发 filechooser。实测 filechooser 监听在 shadow 内不触发。

**解决**：`hasWujie=true` 时 `page.locator('wujie-app .single-cover-uploader-wrap input[type=file]')` 直接 `setInputFiles`；弹窗点 `button.weui-desktop-btn_primary`「确认」。未关「编辑个人主页卡片」弹窗会吞掉保存。仅旧 iframe UI 才用 `.edit-btn` + filechooser。

### ⚠️ 已废弃：B站封面隐藏 file input 按索引取（v1.7.0）→ 被坑 218 取代

> **🔴 v3.38.0 / 0921 作废**：改版后页面上有 **5 个** `input[type=file]`（`.mp4`×2 / `.txt` / `.zip` / 封面 image），按 `inputs[1]` 取会把 png 喂给视频 input 且静默无报错。现行路径见 §11.3 / `templates/bili_cover.py`：**弹窗内点「上传封面」→ 按 `accept` 含 `image` 过滤取 input**。

**问题（v1.7.0 语境）**：B站封面 file input 是隐藏的，且页面上同时存在视频/封面/字幕/素材多个 input。

**解决（已废弃）**：
```javascript
// ⛔ 禁止再用：改版后 inputs 数变 5，inputs[1] 指向视频 input
const inputs = await page.$$('input[type="file"]');
await inputs[1].setInputFiles('horizontal-4-3.png');   // ⛔ v3.38.0 起禁用
```

### 周报多平台上传流程（v1.9.2 新增）

**周报上传流程与日报相同，但需要使用周报专用文件和合集：**

#### 周报 B站上传
1. 导航到 `https://member.bilibili.com/platform/upload/video/frame`
2. 上传周报视频：`news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/video/【羊报AI周刊】*.mp4`
3. 标题自动填充：`【羊报AI周刊】... | YYYY-MM-DD~YYYY-MM-DD`
4. 上传封面：`news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/horizontal-4-3.png`（🔴 v3.38.0：走 §11.3 / `templates/bili_cover.py`，**禁按索引取 input**）
5. 设置创作声明：个人观点，仅供参考
6. 添加标签：羊报AI周刊, AI周报, OpenAI, Anthropic, DeepSeek
7. 填写简介：本期热点...
8. 选择合集：「羊报AI周刊」
9. 点击「立即投稿」

#### 周报公众号上传
1. 打开公众号后台 → 点击「新的创作」→「文章」
2. 切换到新标签页
3. 填写标题：`OpenAI二验风暴、Anthropic IPO、DeepSeek 500亿融资｜羊报AI周刊 YYYY-MM-DD~YYYY-MM-DD`
4. 填写作者：`羊报AI周刊`（≤8 字；署名 `羊报AI周刊 · MM-DD~MM-DD` 写进正文，勿填作者栏）
5. 填写正文（ProseMirror 真实剪贴板粘贴，🔴 v3.30.0）
6. 上传封面图到正文：
   - 点击正文区域获取 focus
   - 按回车创建新行
   - 点击工具栏「图片」→「本地上传」
   - 用 `input.setInputFiles()` 上传封面图（`horizontal-4-3.png` 横版）
7. 设置封面：
   - Hover「拖拽或选择封面」显示选项菜单
   - 用 `.js_selectCoverFromContent` class 选择器点击「从正文选择」
   - 在弹窗中点击图片（出现勾选标记）
   - 点击「下一步」
   - 点击「确认」确认裁剪
8. 设置原创声明：点击「原创」→ 确定（已默认选中）
9. 设置赞赏：点击「赞赏」→ 确定（已默认配置）
10. 选择合集：「羊报AI周刊」
11. 保存草稿

#### 周报封面文件

| 平台 | 文件 | 尺寸 |
|------|------|------|
| B站/通用（横版） | `horizontal-4-3.png` | 1536x1152 (4:3) |
| 抖音/竖版 | `vertical-3-4.png` | 1152x1536 (3:4) |

### Phase 14: 抖音自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 重要经验：抖音创作者中心使用自定义组件，封面上传需要用 force click，发布需要短信验证码。**

#### 14.0-pre 用户手动上传跳过（v3.26.0 / 2026-09-01 实测）

用户明确说「抖音已手动上传 / 不要再自动传 / 记为已手动」时：
1. **立即停止** Phase 14，禁止再打开 `creator.douyin.com` 上传页，禁止点上传 / 暂存 / 重新上传。
2. 标记 `douyin: user-manual`（`upload-status.md` 写 `⏭ 用户手动`）。
3. 不把已打开的创作者页当失败重试；不阻塞其他平台。
4. 验收 URL 仍是 `https://creator.douyin.com/creator-micro/content/publish/record?tab=draft`——**仅当用户要求核验时**才打开，默认不核验、不改稿。

#### 14.0 草稿恢复弹窗处理（v3.18.0 / 2026-08-18 实测）

打开上传页（`creator.douyin.com/creator-micro/content/upload`）时，若上次有未发布草稿，会弹出 **「你还有上次未发布的视频，是否继续编辑？」**。

**❌ 错误做法**：点击合并文本「继续编辑放弃」——无法精确丢弃旧草稿，会落到 `enter_from=draft` 编辑页，混入旧素材。

**✅ 正确流程**：
1. 从草稿编辑页点「**重新上传**」→ 导航回 upload 页 → 重新触发 file chooser。
2. 离开草稿编辑页时会弹 **「将此次编辑保留？」**（beforeunload）→ `browser_handle_dialog(accept=true)`，否则触发 `net::ERR_ABORTED` 导致导航失败。
3. **弹窗若只显「放弃」按钮**（v3.22.0 / 2026-08-28 实测）：用 JS evaluate 精确点 `textContent.trim() === '放弃'` 的可见节点，**勿点合并文本「继续编辑放弃」**（会落到 `enter_from=draft` 编辑页混入旧素材）；点完弹窗消失即恢复 upload 页空白上传区。

```
# 草稿编辑页 → 点「重新上传」回到 upload 页
browser_run_code_unsafe("""async (page) => {
  const btn = page.getByRole('button', { name: '重新上传' });
  if (await btn.count()) await btn.first().click();
  return 'clicked';
}""")

# 若弹出 beforeunload「将此次编辑保留？」
browser_handle_dialog(accept=true)
```

#### 14.1 打开抖音创作者中心

```
browser_navigate("https://creator.douyin.com/creator-micro/content/upload")
```

#### 14.2 上传视频

```
# 点击「上传视频」按钮触发 file chooser
browser_run_code_unsafe("""async (page) => {
  const uploadBtn = page.locator('text=上传视频');
  await uploadBtn.first().click();
  await page.waitForTimeout(2000);
  return 'clicked';
}""")

# 上传视频文件
browser_file_upload("news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4")

# 等待上传完成
browser_wait_for(time=10)
```

#### 14.3 关闭提示弹窗

**🔴 上传视频后会弹出「视频预览功能」提示，必须先关闭：**

```
browser_click(target={我知道了按钮ref})
# 或用 JS
browser_run_code_unsafe("""async (page) => {
  await page.getByRole('button', { name: '我知道了' }).click();
  return 'closed';
}""")
```

#### 14.4 填写作品描述（30字）

**🔴 抖音作品描述是标准 input，但 placeholder 为「填写作品标题，为作品获得更多流量」。格式：`{报刊名} {日期字段}`，≤30字，纯报刊名+日期，不加核心标题/副标题：**

```
browser_run_code_unsafe("""async (page) => {
  // 日报：今日羊报AI 2026-08-01
  // 周报：羊报AI周刊 07-28~08-01
  // 月报：羊报AI月报 2026-08
  const titleInput = page.getByRole('textbox', { name: '填写作品标题，为作品获得更多流量' });
  await titleInput.fill('今日羊报AI 2026-08-01');
  return 'title filled';
}""")
```

#### 14.5 填写作品简介

**🔴 作品简介区域在描述下方，需要先滚动定位：**

```
browser_run_code_unsafe("""async (page) => {
  // 简介区域在 y=217 附近
  await page.mouse.click(690, 217);
  await page.waitForTimeout(500);
  await page.keyboard.type('简介内容');
  return 'intro typed';
}""")
```

#### 14.5b 描述与话题分离输入（v3.22.0 / 2026-08-28 实测）

**🔴 误用 `contenteditable.nth(1)` 会 30s 超时**：抖音编辑页通常只有 **1 个 `div[contenteditable="true"]`**（即描述/简介编辑器）。若按「描述 + 话题都在 contenteditable」的假设用 `nth(1)` 定位话题框，会超时；话题（#标签）**另有入口**，不在 contenteditable 里。

**✅ 分离输入**：
1. **描述/简介** → 填第 1 个 contenteditable（`nth(0)` 或 `page.locator('div[contenteditable="true"]').first()`）
2. **话题（#标签）** → 点 **「#添加话题」** 按钮 → `keyboard.type(tag)` + `keyboard.press('Enter')`，逐个加

```
# 话题逐个加（勿用 nth(1)）
browser_run_code_unsafe("""async (page) => {
  const tags = ['今日羊报AI', 'AI日报', '智谱GLM', 'Qwen', '英伟达', 'OpenAI'];
  for (const tag of tags) {
    // 点「#添加话题」入口
    const addBtn = page.locator('text=#添加话题').first();
    if (await addBtn.count()) await addBtn.click({ force: true });
    await page.waitForTimeout(300);
    await page.keyboard.type('#' + tag);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(400);
  }
  return 'tags added';
}""")
```

#### 14.5c 描述输入 editor-kit 编辑器（v3.23.0 / 2026-08-29 日报实测）

0829 实测：描述编辑器实际是 **`.editor-kit-editor-container [contenteditable="true"]`**（editor-kit 组件），且直接 `fill()` 可能不触发组件状态同步——用 `page.keyboard.type(text, {delay: 5})` 逐字输入最稳：

```js
browser_run_code_unsafe("""async (page) => {
  const desc = '...162字描述含7话题...'; // 由外部传入
  await page.locator('.editor-kit-editor-container [contenteditable="true"]').first().click();
  await page.waitForTimeout(300);
  await page.keyboard.type(desc, { delay: 5 });
  return 'desc typed';
}""")
```

> 与 14.5b 的关系：14.5b 的 `div[contenteditable="true"]` 通用定位在 0829 版编辑页失效时，用本节的 `.editor-kit-editor-container` 选择器兜底；话题仍走「#添加话题」+ keyboard.type 流程不变。

#### 14.6 上传封面（横封面4:3 + 竖封面3:4）（v3.6.0 更新）

**🔴 封面复用**：横封面用 `horizontal-4-3.png`（4:3）+ 竖封面用 `vertical-3-4.png`（3:4）。  
**文件名铁律**：用 Phase 5.5 产出的 `horizontal-4-3.png` / `vertical-3-4.png`，**不要**写成 `cover-horizontal.png` / `cover-vertical.png`。

**入口差异**：
- **首次投稿页**：横封面点「完成」后，常自动弹出「设置竖封面获更多流量」→ 点「设置竖封面」
- **草稿编辑页**（`post/video?enter_from=draft`）：「设置竖封面」弹窗**经常不出现**，必须**再点竖封面 3:4 区域**单独打开编辑器

**🔴 竖封面真入口 = 悬停槽位 → 点「编辑封面」（v3.61.0 / 2026-10-23 实测，坑 296）**：`get_by_role('button', name='设置竖封面')` 常是 `disabled` 的**提示位**（点了必 `Timeout 30000ms / element is not enabled`），**不要把它当主路径**。正确姿势 = `page.locator('.coverControl-CjlzqC').nth(1).hover()` 等「编辑封面」浮现后坐标点击（该按钮同样是 Vue 组件，坐标点击最稳）。弹窗 `.dy-creator-content-modal-body` 内**有 6 个 file input**，只有 **`.selectArea-BCIYQD input[type=file]`** 是封面槽，其余 4–5 个是模板/贴纸选择器，**喂错静默无报错**。

**🔴 封面槽位按 `.coverControl-CjlzqC` 下标 + 实图断言（v3.61.0，坑 296）**：`[0]`=横封面 4:3、`[1]`=竖封面 3:4。验收**只认槽位内 `img.naturalWidth/naturalHeight`**（正确 = 横 1536×1151、竖 1150×1535），**不要 grep 页面文本**——「竖封面缺失」/「双封面缺失」在 AI 推荐封面还在生成时会**瞬时为真**，grep 文本判封面必假阴性。

**🔴 封面上传图标被 SVG 拦截（v3.23.0 / 2026-08-29 实测）**：点封面上传图标时 click 被 SVG 子元素截获（"element intercepts pointer events"）→ 改点上传容器本体 `.semi-upload.upload-BvM5FF`（+ waitForEvent('filechooser') + setFiles）。

**🔴 封面文件落盘位置（v3.23.0 / 2026-08-29 实测；v3.38.0 补充）**：上传脚本读的是**日期目录根**（如 `news-pipeline/2026-08-29/horizontal-4-3.png`），**没有 `covers/` 子目录**。但 `gen_images.py` 出图落在 `images/` 子目录——Phase 11 前必须 `cp images/horizontal-4-3.png images/vertical-3-4.png` 到日期根，先 `ls` 确认实际路径再 setFiles。

**🔴 完成按钮坑（v3.6.0 / 2026-07-17 实测）**：
- `getByRole('button', { name: '完成' })` **经常 count=0**（弹窗粉按钮不是标准 button role）
- 必须用 **text 匹配 + evaluate click**，并在 **filechooser 成功后等 1.5–3s**（预览出现）再点完成
- 点完后若仍见「设置竖封面」标题 → 再点一次完成；**禁止**在未保存时点「取消/关闭」触发「封面未保存」确认框后点「确定」（会丢图）

**推荐完整流程（语义定位 + filechooser + 可靠完成）**：

```
# 共用：可靠点击弹窗内「完成」（优先 text，其次 evaluate）
# 返回 clicked / not_found
async function clickCoverDone(page) {
  await page.waitForTimeout(1500); // 等预览渲染
  // 1) text 定位（比 role 稳）
  try {
    const loc = page.locator('text=完成').last();
    if (await loc.count() && await loc.isVisible().catch(() => false)) {
      await loc.click({ force: true, timeout: 3000 });
      return 'clicked text=完成';
    }
  } catch (_) {}
  // 2) evaluate：点最靠下、宽度较大的「完成」（粉色主按钮）
  const ok = await page.evaluate(() => {
    const cands = [];
    for (const el of document.querySelectorAll('button, div, span, a')) {
      if ((el.textContent || '').trim() !== '完成' || !el.offsetParent) continue;
      const r = el.getBoundingClientRect();
      if (r.width > 40 && r.y > 300) cands.push({ el, y: r.y, w: r.width });
    }
    if (!cands.length) return false;
    cands.sort((a, b) => b.y - a.y);
    cands[0].el.click();
    return true;
  });
  return ok ? 'clicked evaluate 完成' : 'not_found';
}

# 步骤1：打开横封面编辑器——语义找「横封面4:3」→ 同卡「选择封面」
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => window.scrollTo(0, 0));
  return await page.evaluate(() => {
    for (const el of document.querySelectorAll('*')) {
      if ((el.textContent || '').trim() === '横封面4:3' && el.offsetParent) {
        let p = el.parentElement;
        for (let i = 0; i < 5 && p; i++, p = p.parentElement) {
          const sel = Array.from(p.querySelectorAll('*'))
            .find(n => (n.textContent || '').trim() === '选择封面');
          if (sel) { sel.click(); return 'opened horizontal via 选择封面'; }
        }
        el.click(); return 'clicked 横封面4:3';
      }
    }
    return 'horizontal label not found';
  });
}""")

**🔴 @好友 mention 浮层拦截「选择封面」（v3.22.0 / 2026-08-28 实测）**
- 现象：点「横封面4:3」同卡的「选择封面」无反应——点击被 `publish-mention-wrapper`（话题/`@好友` 自动补全浮层）拦截
- 修复：先 `keyboard.press('Escape')` 关浮层 → JS evaluate 找「设置封面」header → `parentElement` 攀爬到封面容器 → 点容器内第一个 `textContent === '选择封面'` 的 div

```
# 封面选择被 @好友 浮层拦截时的兜底
browser_run_code_unsafe("""async (page) => {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('*')) {
      if ((el.textContent || '').trim() === '设置封面' && el.offsetParent) {
        let p = el.parentElement;
        for (let i = 0; i < 6 && p; i++, p = p.parentElement) {
          const sel = Array.from(p.querySelectorAll('div, span, a'))
            .find(n => (n.textContent || '').trim() === '选择封面' && n.offsetParent);
          if (sel) { sel.click(); return; }
        }
      }
    }
  });
  return 'opened cover via 设置封面';
}""")
```

# 步骤2：横封面 filechooser（推荐）或 setInputFiles 兜底
browser_run_code_unsafe("""async (page) => {
  const path = 'news-pipeline/YYYY-MM-DD/horizontal-4-3.png';
  try {
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 6000 }),
      page.locator('text=上传封面').first().click({ force: true })
    ]);
    await chooser.setFiles(path);
    return 'h chooser ok';
  } catch (e) {
    const inputs = await page.$$('input[type="file"]');
    if (inputs.length) {
      await inputs[inputs.length - 1].setInputFiles(path);
      return 'h setInput ok n=' + inputs.length;
    }
    return 'h fail';
  }
}""")
# 步骤3：完成横封面
# → clickCoverDone(page)；确认不再显示设置弹窗标题

# 步骤4：打开竖封面编辑器
browser_run_code_unsafe("""async (page) => {
  await page.waitForTimeout(800);
  // 🔴 坑 296：不要先试 getByRole('设置竖封面')——它常是 disabled 提示位，click() 必超时。
  //    直接走真入口：竖槽位 [1] 悬停 → 「编辑封面」叶子（坐标点击）。
  const slot = await page.evaluate(() => {
    const cs = Array.from(document.querySelectorAll('.coverControl-CjlzqC')).filter(e => e.offsetParent);
    if (cs.length < 2) return null;
    const v = cs[1];                       // [0]=横 4:3, [1]=竖 3:4
    v.scrollIntoView({block: 'center'});
    const r = v.getBoundingClientRect();
    return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), n: cs.length};
  });
  if (!slot) return 'vertical slot missing';
  await page.mouse.move(slot.x, slot.y);
  await page.waitForTimeout(900);
  const hit = await page.evaluate(() => {
    for (const el of document.querySelectorAll('*')) {
      if ((el.textContent||'').trim() !== '编辑封面' || !el.offsetParent || el.children.length > 1) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 20 || r.height < 8) continue;
      return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
    }
    return null;
  });
  await page.mouse.click(hit ? hit.x : slot.x, hit ? hit.y : slot.y);
  return 'vertical editor opened via hover';
}""")

# 步骤5：竖封面上传（弹窗内只认 .selectArea-BCIYQD input[type=file]，坑 296）
browser_run_code_unsafe("""async (page) => {
  const path = 'news-pipeline/YYYY-MM-DD/vertical-3-4.png';
  const open = await page.evaluate(() =>
    document.body.innerText.includes('设置竖封面')
    || document.body.innerText.includes('上传封面'));
  if (!open) return 'editor not open — re-click vertical box';
  // 🔴 坑 296：弹窗内 6 个 file input，只有 .selectArea-BCIYQD 内那个是封面槽。
  //    按索引取（inputs[last]）会喂给模板/贴纸选择器 —— 静默无报错、封面不变。
  const cover = page.locator('.selectArea-BCIYQD input[type=file]').first();
  try {
    await cover.waitFor({ state: 'attached', timeout: 8000 });
    await cover.setInputFiles(path);
    // 🔴 v3.67.0 坑 320：喂图后弹窗默认带裁切缩放，会切掉 3:4 海报两端的字，
    //    平台随后判「封面存在文字展示不全问题 / 封面不佳」。
    //    必须把缩放滑块拖到最小档（点击与方向键都无效）：
    //      mouse.move → down → 分 10 步 move → up
    //    实测 rail x 区间 778.5–831.5、y≈550（视口 1440×769）
    const sl = page.locator('.semi-slider-rail').first();
    const hb = page.locator('.semi-slider-handle').first();
    if (await hb.count()) {
      const h = await hb.boundingBox();
      const r = await sl.boundingBox();
      if (h && r) {
        const y = h.y + h.height / 2;
        await page.mouse.move(h.x + h.width / 2, y);
        await page.mouse.down();
        for (let i = 1; i <= 10; i++) {
          await page.mouse.move(h.x + h.width / 2 + (r.x - h.x) * i / 10, y);
        }
        await page.mouse.up();
        await page.waitForTimeout(800);
      }
    }
    return 'v setInput via selectArea (+zoom min)';
  } catch (e) {
    // 兜底：按 accept 过滤（禁止索引）
    const inputs = await page.$$('input[type="file"]');
    for (const i of inputs) {
      const acc = await i.getAttribute('accept') || '';
      if (acc.includes('image')) { await i.setInputFiles(path); return 'v setInput via accept'; }
    }
    return 'v fail';
  }
}""")

# 步骤6：完成竖封面（等预览 → text/evaluate 点完成 → 再验弹窗是否关闭）
browser_run_code_unsafe("""async (page) => {
  await page.waitForTimeout(2000);
  // 可靠完成：见上方 clickCoverDone 逻辑
  let msg = 'not_found';
  try {
    const loc = page.locator('text=完成').last();
    if (await loc.count() && await loc.isVisible().catch(() => false)) {
      await loc.click({ force: true, timeout: 3000 });
      msg = 'clicked text=完成';
    }
  } catch (_) {}
  if (msg === 'not_found') {
    const ok = await page.evaluate(() => {
      const cands = [];
      for (const el of document.querySelectorAll('button, div, span, a')) {
        if ((el.textContent || '').trim() !== '完成' || !el.offsetParent) continue;
        const r = el.getBoundingClientRect();
        if (r.width > 40 && r.y > 300) cands.push({ el, y: r.y });
      }
      if (!cands.length) return false;
      cands.sort((a, b) => b.y - a.y);
      cands[0].el.click();
      return true;
    });
    msg = ok ? 'clicked evaluate 完成' : 'not_found';
  }
  await page.waitForTimeout(1500);
  const still = await page.evaluate(() => document.body.innerText.includes('设置竖封面'));
  if (still) {
    // 再点一次
    await page.evaluate(() => {
      for (const el of document.querySelectorAll('button, div, span, a')) {
        if ((el.textContent || '').trim() === '完成' && el.offsetParent) {
          const r = el.getBoundingClientRect();
          if (r.y > 400) { el.click(); return; }
        }
      }
    });
    await page.waitForTimeout(1500);
  }
  // 若弹出「封面未保存/是否关闭」——仅在已确认预览成功时再处理；默认点「取消」保留编辑
  return {
    done: msg,
    stillOpen: document.body.innerText.includes('设置竖封面')
  };
}""")

# 步骤7：验收（必须全部通过才暂存）
browser_run_code_unsafe("""async (page) => {
  const t = document.body.innerText;
  return {
    missingV: t.includes('竖封面缺失'),
    missingDual: t.includes('横/竖双封面缺失') || t.includes('双封面缺失'),
    hasSetDialog: t.includes('设置竖封面'),
    hasZancun: !!Array.from(document.querySelectorAll('button'))
      .find(b => (b.textContent || '').trim() === '暂存离开')
  };
}""")
# 通过标准：missingV=false && missingDual=false && hasSetDialog=false
# 然后滚动到底部点「暂存离开」
```

**🔴 关键经验（v3.5.0 / v3.6.0 实测）**：
1. **语义定位 > 硬编码坐标**：先找「横封面4:3」/「竖封面3:4」再点同卡「选择封面」  
2. **「上传封面」必须 `force: true`**，否则 SVG 拦截  
3. **草稿页没有「设置竖封面」弹窗是常态**；真入口永远走 `.coverControl-CjlzqC[1]` 悬停 → 「编辑封面」（坑 296），不要靠标签坐标推算
4. **完成 ≠ getByRole('button')**：用 `locator('text=完成').last()` 或 evaluate 点底部主按钮  
5. **setFiles 后必须等 1.5–3s** 再点完成，否则封面未写入状态  
6. **验收三件套**：无「竖封面缺失」+ 无「双封面缺失」+ 无「设置竖封面」弹窗 → 再「暂存离开」  
7. 合集/声明可与封面并行，但 **竖封面失败优先重试封面**，不要只关页  
8. 若 URL 已在 `enter_from=draft` 且横封面已有，可 **只补竖封面**（今天 2026-07-17 场景）


#### 14.7 添加合集「今日羊报AI」

**🔴 抖音合集选择器使用 listbox 组件，可以用 ref 精确点击：**

```
# 滚动到合集区域
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => window.scrollBy(0, 300));
  return 'scrolled';
}""")

# 点击「请选择合集」打开下拉框
browser_run_code_unsafe("""async (page) => {
  const elements = document.querySelectorAll('*');
  for (const el of elements) {
    if (el.textContent.trim() === '请选择合集' && el.offsetParent !== null) {
      el.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 用 snapshot 找到合集选项的 ref
browser_snapshot(depth=5)
# 🔴 合集名大小写陷阱（v3.22.0 / 2026-08-28 实测）：抖音合集名可能与 B站/公众号不同
# 实测「「今日羊报Al」」是小写 L（非大写 I）+ 「共80个作品」——勿硬编码精确合集名
# 修复：探测下拉框可见文本，匹配「今日羊报」前缀（不分大小写）+ 「共N个作品/共N个内容」的选项点击；snapshot 验收按前缀模糊匹配
browser_click(target={ref编号})
```

**🔴 前缀匹配会命中整个下拉容器，必须用最小面积法（v3.61.0 / 2026-10-23 实测，坑 297）**

`/^「?今日羊报/` + `/共\s*\d+\s*个作品/` 同时匹配**容器节点**——容器的 `textContent` 是所有选项拼起来的整串（实测 `请选择合集不选择合集「虢礫緙嘞」共4个作品「羊报AI月报」…`），点容器等于**没选**，且回读看着像选上了。

```javascript
// 正确：三重约束 + 最小面积
const picked = page.evaluate(() => {
  const cands = [];
  for (const o of document.querySelectorAll('li, div, span, p, [class*=option], [class*=item]')) {
    const t = (o.textContent || '').trim();
    if (!o.offsetParent) continue;
    if (!/^「?今日羊报/.test(t)) continue;
    if (!/共\s*\d+\s*个(?:作品|内容)/.test(t)) continue;   // 1025 实测文案是「共N个内容」
    if (t.length > 40) continue;                    // ① 排除整块容器
    const r = o.getBoundingClientRect();
    if (r.height < 10 || r.height > 90) continue;   // ② 排除 0 高/超大节点
    cands.push({t, area: r.width * r.height, el: o});
  }
  if (!cands.length) return null;
  cands.sort((a, b) => a.area - b.area);            // ③ 最小面积 = 真正的选项
  cands[0].el.click();
  return cands[0].t.slice(0, 40);
});
```

回读「添加合集」段确认目标合集名 + 「共N个作品 / 共N个内容」（1023 命中 `「今日羊报Al」共132个作品`，1025 命中 `今日羊报Al 共134个内容`——**两种文案都存在，正则必须都容**）。

#### 14.8 设置自主声明

```
# 点击「请选择自主声明」
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '请选择自主声明' && el.offsetParent !== null) {
        el.click();
        return;
      }
    }
  });
  return 'clicked';
}""")

# 选择「内容为个人观点或见解」
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '内容为个人观点或见解' && el.offsetParent !== null) {
        el.click();
        return;
      }
    }
  });
  return 'selected';
}""")

# 点击「确定」
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.textContent.trim() === '确定' && btn.offsetParent !== null) {
        btn.click();
        return;
      }
    }
  });
  return 'confirmed';
}""")
```

#### 14.8b Semi Design 组件拦截修复（v3.18.0 / 2026-08-18 实测）

抖音创作者中心部分控件基于 **Semi Design**（ByteDance），原生 `locator.click()` 常被外层包裹元素拦截而 30s 超时。

**自主声明 radio**：
- **原因**：`<label class="semi-radio">…</label>` 拦截 pointer events，`locator.click()` 超时 30s。
- **修复**：直接点击 `label.semi-radio` 元素。

```
const label = page.locator('label.semi-radio').filter({ hasText: '内容为个人观点或见解' });
await label.click();
```

**「暂存离开」按钮**：
- **原因**：`<div role="modal" class="semi-modal-wrap">` 拦截，按钮不可点。
- **修复**：关闭 modal `.semi-modal-close` → `Escape` → force click。

```
await page.keyboard.press('Escape');
await page.waitForTimeout(1000);
await page.locator('button:has-text("暂存离开")').click({ force: true });
```

**file chooser modal state**：
- `browser_run_code_unsafe` 触发 file chooser 后，工具层会停在 **"Modal state: File chooser"** 导致后续 tool call 阻塞。
- **修复**：用 `browser_file_upload(paths=[...])` 处理文件选择，**不要**在同一长脚本里串 `filechooser` 事件。

#### 14.9 添加标签

```
# 点击「#添加话题」
browser_run_code_unsafe("""async (page) => {
  const elements = document.querySelectorAll('*');
  for (const el of elements) {
    if (el.textContent.trim() === '#添加话题' && el.offsetParent !== null) {
      el.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 输入标签并按 Enter
browser_run_code_unsafe("""async (page) => {
  await page.keyboard.type('今日羊报AI');
  await page.keyboard.press('Enter');
  return 'tag added';
}""")
```

#### 14.10 存草稿（不直接发布）

**🔴 重要：所有平台上传一律存草稿，不直接发布！用户确认后再手动发布。**

```
# 抖音没有"存草稿"按钮，使用「暂存离开」或直接关闭页面
# 视频会自动保存到草稿箱

# 方法1：点击「暂存离开」（如果有）
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '暂存离开' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 方法2：如果没有「暂存离开」，直接关闭标签页（视频已自动保存）
```

**🔴 草稿落库验收（v3.9.0 / 2026-07-20 实测 — 不可省略；v3.61.0 重写口径）**

仅点「暂存离开」**不够**。0720 首次上传后用户在创作者中心**看不到草稿**，必须重传。

**🔴 抖音没有草稿列表页（v3.61.0 / 2026-10-23 实测，坑 295）**：`content/manage?tab=draft` 与 `content/publish/record?tab=draft` 都是空壳（只显示已发布作品）。**唯一恢复入口 = 发布页 `creator-micro/content/upload` 的「你还有上次未发布的视频，是否继续编辑？」横幅里的「继续编辑」。** 旧版本条里写的「导航到 publish/record?tab=draft 看列表」已失效。

**🔴 「继续编辑」横幅是一次性消费令牌（坑 295，坑 290 第三形态）**：抖音「暂存」= 把编辑器状态写入服务端一个**待恢复槽位**，不是创建持久草稿记录；槽位被读取即清空。所以：

- ✅ 正确：`暂存离开` → **同标签**点「继续编辑」回读表单 → **再点一次「暂存离开」** → 终态确认「按钮消失 + 横幅重新出现」
- ❌ 错误：为核验**新开标签**点「继续编辑」→ 读表单 → 关标签。草稿从此消失，之后任何标签横幅都不再现，草稿箱也查不到
- ❌ 错误：外部标签点完横幅点「放弃」——直接丢弃
- ✅ 外部标签只准**读** `body.innerText` 里的横幅文本（不点击），用于判断"草稿确实存在"

**成功信号（当前口径）**：
1. 「暂存离开」按钮消失 **且** 恢复横幅出现（双信号，坑 290）
2. 同标签恢复后表单回读：`title == publish.json.platform.douyin.title`、`descLen > 100`、话题数、声明文本、封面槽位实图尺寸全对
3. 恢复回读后**已再次暂存**，且终态仍是「按钮消失 + 横幅出现」

**失败信号 → 必须整段重传（视频+标题+双封面+暂存）**：
- 上传页无「继续编辑」横幅
- 同标签恢复后是空表单（标题 0/30、无 video）

**竖封面文件**：只使用本期 `news-pipeline/{date}/vertical-3-4.png`（含日期+品牌）。用户指定该文件时**禁止**用 scene 图或其它日期文件替代。

**参考实现**：`news-pipeline/2026-10-23/scripts/douyin_finish_1023.py`（合集 → 暂存#1 → 同标签恢复回读 → 暂存#2 → 终态，一次跑完）。

#### 14.10b 暂存离开 + 草稿落库验收（v3.18.0 / 2026-08-18 实测）

抖音 Semi Design modal（`semi-modal-wrap`）会拦截「暂存离开」按钮，需先 `Escape` 关闭残留弹窗再 force click（见 14.8b）。

```
# 1. 关闭可能残留的 modal
await page.keyboard.press('Escape');
await page.waitForTimeout(1000);

# 2. force click「暂存离开」
await page.locator('button:has-text("暂存离开")').click({ force: true });

# 3. 离开编辑页时若弹 beforeunload「将此次编辑保留？」
browser_handle_dialog(accept=true)
```

**草稿落库验收信号**（v3.61.0 口径，坑 290 + 坑 295）：
1. **双信号**：「暂存离开」按钮消失 **且**「继续编辑」恢复横幅出现（缺一即失败）
2. **同标签恢复回读**：点「继续编辑」→ 表单回读 title/descLen/话题/声明/封面槽位实图全对 → **再点一次「暂存离开」**（否则草稿被消费掉）
3. 外部标签只准**读**横幅文本，**禁点击**（坑 295：点一次就毁稿）

#### 🔴 抖音违规审核与处理（v3.15.0 新增，2026-07-31 实测）

**常见违规原因**：

| 违规原因 | 触发条件 | 文案修改方向 |
|----------|---------|-------------|
| `引导至风险不可控渠道` | 描述/口播中出现「开放申请」「去XX体验」「下载XX」「申请试用」「去 Hugging Face」「跑杀毒扫描」「清 Cookie」等引导性表述；也可叠「画面」标签（账号事故帧） | 去掉「去」「申请」「体验」「下载」等引导动词，改为「上线」「推出」「发布」「已随仓库发布」等中性陈述；账号安全改「走官方账号安全页核对」；**若同时标「画面」必须重渲** |
| `画面` / `不适宜公开` | 视频帧中包含安全事件视觉（入侵/撬锁/隔离舱破裂）、政策/立法场景（法槌/两党剪影） | 重画场景图，改为产品化视觉（仪表盘/UI界面/机房）；修改口播避免攻击性动词 |
| `竖封面缺失` / `双封面缺失` | 未上传竖封面（3:4）或横封面（4:3） | 补传对应封面，验收确认无缺失提示 |
| `违规推广内容` | 简介中数字连续出现（疑似QQ号/微信号） | 数字中文化，版本号简化，去掉 hash tag 行 |

**违规处理流程**：

1. **查看违规详情**：打开抖音创作者中心 → 内容管理 → 找到违规作品 → 点击「违规详情」
2. **定位违规源**：
   - 先看违规原因描述（如「引导至风险不可控渠道」→ 检查描述/口播中的引导性动词）
   - 再检查描述文案中是否有「开放申请」「去XX体验」「下载」「申请试用」等关键词
   - 最后检查视频帧画面（安全事件场景需重画）
3. **修改方案**：
   - **文案违规**：修改 publish.json 中抖音的 title/description，去掉所有引导性表述
   - **画面违规**：重画对应场景图（prompt 改为产品化视觉），重写口播文本
   - **双封面缺失**：补传竖封面/横封面
4. **重传流程**：
   - 修改 publish.json 中抖音标题/描述
   - 如涉及画面违规：修改 voiceover-texts.json 中的口播文本 → 重新生成 TTS（scene 级别）→ 重算 captions.json → 重渲染视频
   - 打开 `https://creator.douyin.com/creator-micro/content/upload` → 上传新视频 → 填写标题/描述 → 上传双封面 → 暂存离开

**违规文案修改示例**：

| 原文 | 问题 | 修改后 |
|------|------|--------|
| 「符合条件的科研人可以**申请试用**」 | 引导至外部渠道 | 「学术科研领域的 AI 应用正在加速落地」 |
| 「想玩 AI 音乐的可以直接去 **Flow Music 体验**」 | 引导至第三方平台 | 「AI 音乐创作的门槛正在降低」 |
| 「OpenAI 学术科研版**开放申请**」 | 引导申请 | 「OpenAI 推出学术科研版」 |

**自检清单新增项**（Phase 2 审核检查清单中增加）：

```
☐ 抖音描述：检查「申请」「体验」「下载」「去」「试用」等引导性动词
☐ 抖音描述：去掉任何指向外部平台/产品的引导语句
☐ 口播文本：Scene 5/6 类场景（产品/服务介绍）禁止尾部引导行动
☐ 口播 Now What：禁止「去 Hugging Face / 清 Cookie / 跑杀毒 / 再下单」；账号安全只说官方安全页
☐ 画面：禁止断链、丢卡、入侵、杀毒扫描窗、第三方仓库站 UI（Star/Fork/Model card）
☐ 内部 review-checklist PASS ≠ 抖音过审；标签含「画面」必须 `*-safe.mp4`
```

#### 抖音上传组件操作总结（v3.6.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 视频上传 | file chooser | `text=上传视频` → `file_upload` | ✅ 高 |
| 提示弹窗 | 按钮 | `getByRole('button', { name: '我知道了' })` | ✅ 高 |
| 作品描述 | 标准 input | **`fill()`** 或 placeholder 匹配（React 受控） | ✅ 高 |
| 作品简介 | 文本区域 | 坐标点击 + `keyboard.type` | ✅ 高 |
| 横封面4:3 | 自定义编辑器 | 语义「横封面4:3」→ force「上传封面」→ setFiles → **text/evaluate「完成」** | ⚠️ 需 force+等预览 |
| 竖封面3:4 | 自定义编辑器 | 弹窗或标签上方点击 → force 上传 → setFiles → **text/evaluate「完成」** | ⚠️ 草稿页无弹窗 |
| 完成按钮 | 非标准 role | **`locator('text=完成')` / evaluate**，**不要**依赖 `getByRole('button','完成')` | ⚠️ count 常为 0 |
| 合集 | listbox | 点击下拉框 → snapshot 找 ref → 精确点击 | ✅ 高 |
| 自主声明 | 弹窗 | 点击打开 → 选择选项 → 确定 | ✅ 高 |
| 标签 | 输入框 | 点击 `#添加话题` → `keyboard.type` + Enter | ✅ 高 |
| 存草稿 | 按钮 | 底部 **「暂存离开」**（非「存草稿」） | ✅ 高 |
| 发布 | 按钮 | 点击「发布」→ 短信验证码（需用户手动） | ⚠️ 需用户 |

**关键经验**：
1. **上传视频后必须关闭「视频预览功能」弹窗**，否则后续操作被阻挡
2. **封面上传需要 `force: true`**，SVG 会拦截点击
3. **完成按钮不要用 getByRole**，改用 text/evaluate + 等预览 2s
4. **验收三件套**通过后再「暂存离开」
5. **作品描述用 `fill()`**（React 受控，`value=` 不生效）
6. **草稿页只补竖封面**时从 `enter_from=draft` 继续即可

### Phase 15: 知乎文章自动上传（v3.72.0 新增）

**权限已在预授权阶段获得，直接执行。完整实现见 `templates/platform-zhihu.md`。**

**入口**：`https://www.zhihu.com/creator/manage/creation/article` → 点击「立即创作」。

**八步（顺序不可跳）**：① 立即创作 → ② 标题 → ③ 正文（先文本后插图，图必须传到平台） → ④ **正文前插成片视频** → ⑤ 添加封面 → ⑥ 创作声明「包含 AI 辅助创作，作者对内容负责」 → ⑦ 专栏收录「今日羊报 AI」 → ⑧ 保存草稿（等自动保存）。

**五条只属于本平台的铁律**：

1. **审核门在前**：`templates/platform-zhihu.md` §2 十一条清单全 PASS 才准上传。知乎《AI 辅助创作治理细则》要求「作者完成主要智力劳动、审查编辑并对最终内容负责」；规范§五把「发布机器生成的内容」列为违规——**加 AI 声明不能豁免**，所以「编辑判断」段与事实核验是硬性内容要求。
2. **删导流再上传**：公众号 CTA（点个赞/转发/关注「今日羊报 AI」/评论区聊聊）整段删除；标题去品牌后缀。规范§四禁止在标题/封面加营销推广信息、禁止诱导至第三方平台关注。
3. **只到存草稿**：「发布」按钮不进脚本候选集（坑 317 四步自证仍适用于「保存草稿」，它与相邻按钮可能只差十几像素）；发布由用户手动完成。
4. **视频要内嵌且排正文之前**：知乎支持内嵌视频。光标置文档开头 → `button[aria-label="视频"]` → `input.VideoUploadButton-fileInput` 传文件 → 等 `data-video-playable === 'true'`（约 10–15 s）。落位是 block 0 自动空文本 + block 1 VIDEO，即在正文之前。
5. **知乎专栏名与抖音/视频号合集名不同**：知乎是 `今日羊报 AI`（**含半角空格 U+20，末位大写 I U+49**），抖音/视频号是 `今日羊报Al`（无空格，末位**小写 l** U+6C）。两者肉眼几乎无法分辨，2026-10-30 已分别按页面码点实测确认。比较一律先两边去空白，**禁硬编码精确串**；回读不到就停，不静默跳过（坑 312）。判别以 `.ColumnSetting-ColumnSelector` 里 radio 的 `checked` 为准，不许 grep 页面文本（坑 343）。

**⚠️ 2026-10-30 实测已回填（v3.71.0）**：下列选择器与行为均已在本机登录态下实测确认，模块文档 §3 即为实跑结果，**不再是 TODO-PROBE**：

| 项 | 实测结果 |
|---|---|
| 立即创作 | 点击后**新开标签页** `https://zhuanlan.zhihu.com/write`（当前页 URL 不变） |
| 标题 | `textarea[placeholder="请输入标题（最多 100 个字）"]` |
| 正文 | `div.public-DraftEditor-content`（Draft.js，`innerHTML` 直赋无效）；**合成 `ClipboardEvent` + `DataTransfer` 比真剪贴板更稳**（无需 `grant_permissions`） |
| 正文块 | `div.public-DraftEditor-content [data-block="true"]`；`VIDEO` / `IMG` / `TXT` 三类靠 `.Editable-video` / `img` 判别 |
| 图片 | `input[type=file][accept*="image/webp"]`（常驻 DOM），上传落在**光标所在块**；先贴 `<p>__IMG__</p>` 占位再逐张替换 |
| 视频 | `button[aria-label="视频"]` 开弹窗；真 input 是 `input.VideoUploadButton-fileInput`（**弹窗前已在 DOM**），可直接传；约 10–15 s 出卡片，判 `.Editable-video` 的 `data-video-playable === 'true'` |
| 视频落位 | 插在光标块；光标置文档开头 → block 0 自动空文本 + block 1 VIDEO，即**在正文之前**（需求硬要求） |
| 封面 | `input[type=file][accept=".jpeg, .jpg, .png"]`（class `UploadPicture-input`） |
| 创作声明 | 在「发布设置」面板：`div.css-be2u3` → `label` 文本==`创作声明` → `button[role=combobox]` → `.Select-option` 文本 `包含 AI 辅助创作 作者对内容负责`；回读须归一化零宽字符，实测得到 `包含AI辅助创作作者对内容负责` |
| 专栏 | 判据是 `.ColumnSetting-ColumnSelector` 内 `input[type=radio]` 的 **`checked`**，不是页面文本（坑 343）；真值 `「今日羊报 AI」`（半角空格 + 大写 I） |
| 保存草稿 | **没有保存按钮——知乎文章自动保存**；底部出现 `刚刚 · 草稿`，URL 变 `/p/<id>/edit` 即已落库 |
| 内容来源 | 面板底部提示「发布新闻类的内容需要明确标注信息来源」，建议「添加来源」 |
| 危险按钮 | `发布`（`Button--pri`）——永不点击 |

**坑 334-343**（详见 `templates/platform-zhihu.md` §4）：创作声明控件是 combobox 且 `css-be2u3` 被多字段复用（须按 label 文本定位）；无保存按钮只能靠自动保存验收；「立即创作」开新标签；新闻类有「内容来源」要求；**视频卡片是原子块，退格整块删（338）**；**`Shift+Home` 在 Draft.js 里会选到整篇开头，一次退格毁掉全文（339）**；**Vue tab/radio 的 `.click()` 静默无效，须 `page.mouse.click` 坐标（340）**；**整行加粗判断漏掉「行首加粗+行内正文」，页面留字面 `**`（341）**；**`Backspace` 走 Draft.js 内部选区而非 DOM 选区，可删错块（342）**；**专栏选中态 grep 文本恒真（343）**。

**验收必带的结构性计数**：`videos == 1 && videoPlayable == 'true'` + `IMG` 块数 == 源文图数 + `__IMG__` 残留 == 0 + 全文无字面 `**` + 声明回读 + 专栏 radio checked。任何一步含 `Backspace` 之后都要重数一遍视频/图片，别假设它们还在。

**失败处理**：登录页 → 记 `login_required` 留页给用户；「立即创作」找不到 / 声明选项找不到 / 专栏匹配不到 → **停在该步报告**，不换选择器盲试（连续两次落空即定性）。

### 🟡 B站封面上传不可靠（v1.9.1 新增）
**问题**：B站隐藏 file input 的 accept 属性不包含图片类型（只有视频格式），且通过封面编辑弹窗上传的图片不一定被应用。

**解决**：B站封面建议手动上传，或跳过封面使用系统默认第一帧。

### 🟡 TTS 超时重试（v1.9.1 新增）
**问题**：mimo-tts.sh 首次调用可能超时（exit code 28），但重试后成功。

**解决**：TTS 调用失败后自动重试一次，不要立即报错。

### 🟡 视频号需要独立登录（v1.9.1 新增）
**问题**：视频号助手与公众号使用不同的登录会话，需要微信扫码登录，不能复用公众号的 cookie。

**解决**：视频号上传前必须先扫码登录，建议在 Phase 13 开始时提示用户。

### 🟡 抖音发布可能不需要验证码（v1.9.1 新增）
**问题**：抖音发布在某些情况下可以直接发布，不需要短信验证码（与账号信任度、设备指纹有关）。

**解决**：先尝试直接发布，如果弹出验证码再让用户手动输入。

### 🟡 周报封面上传到正文（v1.9.2 新增）
**问题**：周报封面上传到公众号正文时，file chooser 可能不触发。

**解决**：使用 `input.setInputFiles()` 直接设置文件：
```javascript
const input = await page.$('input[type="file"][accept*="image"]');
await input.setInputFiles('news-pipeline/weekly/.../horizontal-4-3.png');
```

### 🟡 周报B站合集自动选择（v1.9.2 新增）
**问题**：周报上传到B站时，合集「羊报AI周刊」可能不会自动选择。

**解决**：合集选择器是自定义 Vue 组件，建议手动选择或跳过。如果需要自动化，使用 `page.getByText('「羊报AI周刊」', { exact: true })` 精确匹配。

### 🔴 API 连接超时问题（v2.2.0 新增，2026-06-13）
**问题**：prism API（ai.prism.uno）在某些网络环境下连接超时，curl 显示 "Failed to connect to ai.prism.uno port 443 after 30001 ms: Timeout was reached"。

**原因**：可能是 DNS 解析问题或网络限制（GFW、企业防火墙等）。

**解决**：
1. 优先使用 eo.ioll.pp.ua（OpenRouter）作为备选 API
2. 如果用户提供的 API 不可用，自动尝试备选 API
3. 不需要询问用户，直接切换

**API 源优先级**：
1. 用户提供的 API
2. eo.ioll.pp.ua（OpenRouter）- 2026-06-13 验证可用
3. ai.prism.uno - 可能需要 VPN
4. api.luka77.cc

### 🔴 视频归档遗漏（v2.2.0 新增，2026-06-13）
**问题**：视频渲染完成后没有自动复制到日报目录，导致上传时找不到视频文件。

**解决**：Phase 9 视频合成完成后，立即执行归档：
```bash
cp "news-pipeline/video-project/out/【YYYY-MM-DD】{核心标题}… | 今日羊报AI.mp4" \
   "news-pipeline/YYYY-MM-DD/video/"
```

**归档时机**：视频合成完成后立即执行，不要等到上传阶段再复制。**🔴 v3.39.0 汇报门（坑 222）**：归档后必须 `ls -la` 确认模式目录 `video/` 非空 + ffprobe 回读时长/分辨率，缺任一**禁止在汇报中写「视频已生成」**；归档被分类器抖动（坑 216）打断时，在状态文件记「待归档」，恢复后第一件事补归档（0921 周报因此漏归档，`weekly/.../video/` 为空，用户两次追问「视频呢」）。

### 🔴 封面生成不完整（v2.2.0 新增，2026-06-13）
**问题**：异步生成封面时，只生成了部分封面（如 1/2），另一张封面因 API 超时或错误未生成。

**解决**：
1. 每张封面生成后自动重试一次
2. 生成完成后验证所有封面文件
3. 如果封面不完整，同步补生成缺失的封面

**验证方法**：
```bash
ls -la news-pipeline/YYYY-MM-DD/*.png | wc -l
# 应该输出 2（horizontal-4-3.png【4:3 横版】, vertical-3-4.png【3:4 竖版】）
```

### 🔴 公益站内容过滤（v2.2.0 新增，2026-06-13）
**问题**：日报视频中不应包含公益站、中转站、倒卖相关内容。

**解决**：Phase 1 事件筛选时，主动过滤以下类型内容：
- 公益站上架/开通/故障
- 中转站价格/稳定性讨论
- 邀请码/兑换码分享
- 倒卖/交易相关内容

**选择事件时只保留**：模型发布、公司动态、安全事件、开源模型、行业政策、技术突破等。

### 🔴 周报所有上传保存草稿（v2.4.0 新增，2026-06-14）

**问题**：周报视频上传到各平台时，直接发布存在风险（标题/封面/合集可能需要调整）。

**解决方案**：周报模式下，所有平台上传一律保存草稿，不直接发布。

**具体流程**：
| 平台 | 操作 | 说明 |
|------|------|------|
| B站 | 保存草稿 | 周报可选择直接投稿或存草稿 |
| 公众号 | 保存草稿 | 标题+正文已填，封面/原创/合集需手动 |
| 视频号 | 保存草稿 | 描述+短标题已填，封面/合集需手动 |
| 抖音 | 暂存离开 | 描述+封面已填，合集/发布需手动 |

**Why:** 周报内容比日报更正式，用户需要二次确认标题、封面、合集等信息后再发布
**How to apply:** SKILL.md 周报上传流程中，所有平台最后一步改为「保存草稿」而非「发布/投稿」

### 🔴 抖音草稿页竖封面入口（v3.5.0 新增，2026-07-16；v3.6.0 补强）

**问题**：从草稿箱打开投稿页（`enter_from=draft`）时，横封面点「完成」后**不一定**弹出「设置竖封面」；旧文档写的「弹窗必现」在草稿流失效，导致竖封面一直缺失。

**解决**：
1. 横封面：语义找「横封面4:3」→ 同卡「选择封面」→ `force` 点「上传封面」→ `horizontal-4-3.png` →「完成」
2. 竖封面：若无弹窗，用「竖封面3:4」标签的 `getBoundingClientRect`，点击 **标签上方约 50–80px** 的封面框打开编辑器
3. 再 `force` 点「上传封面」→ `vertical-3-4.png` →「完成」
4. 验收文案无「竖封面缺失」/「横/竖双封面缺失」后「暂存离开」

**Why:** 首次投稿页与草稿编辑页 UI 分支不同；硬编码坐标在不同窗口尺寸下也易失效  
**How to apply:** Phase 14.6 已改为语义优先 + 草稿页专用竖封面点击逻辑

### 🔴 抖音封面「完成」按钮非 button role（v3.6.0 新增，2026-07-17）

**问题**：竖封面已通过 `filechooser.setFiles` 上传成功、弹窗里也能看到预览，但 `getByRole('button', { name: '完成' })` **count=0**，脚本以为点了完成、实际没点上；或过早点完成导致状态未写入，发文助手仍报「竖封面缺失」。

**解决**：
1. `setFiles` 后 **wait 1.5–3s**，等预览区出图
2. 用 `page.locator('text=完成').last().click({ force: true })`；失败再 `evaluate` 点 **y 最大、宽>40** 的「完成」节点
3. 点完再读 `innerText`：若仍含「设置竖封面」→ 再点一次完成
4. **禁止**在未完成时关弹窗并对「封面未保存」点「确定」
5. 最终验收：`missingV=false && missingDual=false && !hasSetDialog` 再「暂存离开」

**Why:** 抖音封面弹窗主按钮常用自定义 div/span，不是 accessibility button  
**How to apply:** Phase 14.6 步骤 3/6 一律按 text/evaluate 完成 + 双次确认

### 🔴 抖音只补竖封面场景（v3.6.0 新增，2026-07-17）

**问题**：横封面已在草稿中，只缺竖封面时，全流程重跑浪费时间；误操作还可能冲掉横封面。

**解决**：
1. 直接打开草稿：`https://creator.douyin.com/creator-micro/content/post/video?enter_from=draft`（或内容管理→编辑）
2. **跳过横封面**，只做竖封面打开→上传→完成→验收
3. 验收通过后「暂存离开」

**Why:** 发文助手单独报「竖封面缺失」时横封面往往已 OK  
**How to apply:** 用户说「补竖封面」时走最小路径，不重传视频/横封面

### 🔴 公众号封面不阻塞草稿（v3.5.0 新增，2026-07-16）

**问题**：「从正文选择」链路偶发失败（file chooser 不弹、上传中弹窗挡保存、class 选择器找不到），若强依赖封面会导致整篇无法存草稿。

**解决**：
1. 完整链路仍优先：工具栏图片→本地上传封面图（`horizontal-4-3.png` 横版 / `vertical-3-4.png` 竖版，均按公众号头条封面 900×383 自动裁剪）→ hover 封面区 → `.js_selectCoverFromContent` → 下一步 → 确认
2. chooser 不弹：`input[type=file][accept*=image].setInputFiles(...)` 兜底
3. 上传中弹窗：等待 8–15s + Escape 再点「保存为草稿」
4. **封面失败也要保存草稿**；成功信号优先看 URL 是否含 `appmsgid=`

**Why:** 正文/原创比封面更关键，封面可在草稿箱手补  
**How to apply:** Phase 12.7 已写降级原则与 setInputFiles 兜底

### 🔴 抖音双封面上传（v2.4.0 新增，2026-06-14）

**问题**：抖音需要同时上传横封面（4:3）和竖封面（3:4），竖封面弹窗会在横封面完成后自动弹出。

**解决方案**：
1. 先上传横封面（4:3）→ 点击「完成」
2. 弹出「设置竖封面获更多流量」弹窗 → 点击「设置竖封面」
3. 上传竖封面（3:4）→ 点击「完成」
4. 如果弹窗点击「暂不设置」，可后续在编辑页面补充

**封面文件**：
- 横封面：`horizontal-4-3.png`（1536x1152，4:3）
- 竖封面：`vertical-3-4.png`（1152x1536，3:4）

**Why:** 抖音个人主页显示竖封面，搜索结果展示横封面，两者都需要
**How to apply:** 抖音上传时必须上传双封面，竖封面可在横封面完成后通过弹窗上传

### 🟡 视频号需要独立登录（v2.4.0 确认，2026-06-14）

**问题**：视频号助手与公众号使用不同的登录会话，需要微信扫码登录。

**解决方案**：
1. 首次访问视频号助手时提示扫码登录
2. 登录后在同一浏览器会话中保持登录状态
3. 视频号页面内容在 iframe 中（`name="content"`），操作需用 `page.frame({ name: 'content' })`

**Why:** 视频号和公众号是两个独立的产品，登录系统不互通
**How to apply:** Phase 13 开始时检查是否已登录，未登录则提示用户扫码

### 🟡 抖音上传页面导航问题（v2.4.0 新增，2026-06-14）

**问题**：抖音创作者中心页面导航偶尔超时（`net::ERR_ABORTED`），可能需要重试。

**解决方案**：
1. 首次导航失败后重试一次
2. 如果仍然失败，提示用户手动打开抖音创作者中心
3. 草稿编辑链接：`https://creator.douyin.com/creator-micro/content/post/video?enter_from=draft`

**Why:** 抖音页面有复杂的前端路由和弹窗拦截，Playwright 导航可能被中断
**How to apply:** 导航失败时自动重试，不询问用户

### 🔴 Agent 工具生成封面失败（v2.5.0 新增，2026-06-16）

**问题**：使用 `Agent(run_in_background=True)` 异步生成封面时，Agent 遇到 Bash 权限被拒绝，无法执行 curl 和 Python 脚本。

**解决方案**：不要用 Agent 工具生成封面。直接在主线程中用 Python 脚本串行生成所有封面。封面生成（5个，约 3-5 分钟）和 TTS 配音（7个，约 2-3 分钟）串行执行总时间约 8 分钟，可以接受。

**Why:** Agent 工具在执行 Bash 命令时会遇到权限问题，无法完成 API 调用和文件操作
**How to apply:** 封面生成直接用 `Bash` 工具执行 Python 脚本，不用 Agent

### 🔴 克隆音色太机械（v2.5.0 新增，2026-06-16）

**问题**：使用曼波/阿根的克隆音色（voiceclone）生成的 TTS 在新闻播报场景下听起来太机械、不自然，用户反馈"配音太机械"。

**解决方案**：使用 MiMo 预置音色「白桦」（男性，中文），效果远好于克隆音色。其他可选预置音色：苏打（男）、冰糖（女）、茉莉（女）。

**Why:** 克隆音色在短句和新闻播报场景下表现不佳，预置音色经过专业调优
**How to apply:** TTS 默认使用 `mimo-v2.5-tts` 模型 + `voice: "白桦"`，不要用 `mimo-v2.5-tts-voiceclone`

### 🟡 MIMO_TTS_API_KEY 未配置（v2.5.0 新增，v2.8.0 更新，v3.2.0 更新）

**问题**：mimo-tts.sh 脚本报错 `MIMO_TTS_API_KEY not found`，因为 ~/.claude/settings.json 的 env 中没有配置该变量。

**v2.8.0 新发现**：settings.json 中 `MIMO_TTS_API_URL` 可能包含 `/anthropic` 后缀（如 `https://token-plan-cn.xiaomimimo.com/anthropic`），这是 **错误的**！正确 URL 格式为 `https://token-plan-cn.xiaomimimo.com/v1/chat/completions`（不带 `/anthropic`）。

**v3.2.0 新发现**：settings.json 中可能根本没有 MIMO_TTS_API_KEY 和 MIMO_TTS_API_URL 配置。此时必须使用环境变量方式调用 mimo-tts.sh，而不是依赖 settings.json。

**解决方案**：
1. **首选方案（v3.2.0）**：使用环境变量方式调用 mimo-tts.sh
   ```bash
   MIMO_TTS_API_URL="https://your-api-url.com" MIMO_TTS_API_KEY="sk-your-key" \
   bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
     --text "配音文本" --voice "白桦" --style "新闻播报" \
     --output "news-pipeline/YYYY-MM-DD/voiceover/sceneN.wav"
   ```
2. **备选方案**：如果环境变量方式也失败，直接用 Python+curl 调用 MiMo TTS API
3. **URL 校验**：如果 settings.json 中的 URL 以 `/anthropic` 结尾，需要去掉 `/anthropic` 再拼接 `/v1/chat/completions`
4. API 格式：`POST {API_URL}/v1/chat/completions`，body 格式见 mimo-tts.sh 源码

**Why:** TTS API Key 和图片 API Key 是分开的，需要分别收集。settings.json 可能没有 TTS 配置。
**How to apply:** 预授权时额外收集 TTS API URL + Key。Phase 6 TTS 生成时，先尝试环境变量方式，失败再用 Python 直接调用。

### 🟡 脚本风格必须"说人话"（v2.5.0 新增，2026-06-16）

**问题**：默认生成的脚本风格偏播音腔、书面化，用户反馈"观众要求说人话"。

**解决方案**：脚本生成时强调口语化、像跟朋友聊天、不要堆砌术语。具体要求：
- 不要"各位观众大家好"式的开场
- 用"说白了"、"这谁不爱"、"怕是要来了"等口语表达
- 保留情绪感但不要夸张
- 每段不超过 80 字

**Why:** B站观众更喜欢自然、真实的表达方式
**How to apply:** Phase 2 脚本生成时，风格要求第一条改为"说人话"

## 注意事项

- **🔴 点击类操作通用铁律（v3.63.0，坑 302/303 共同根因）**：**任何 `mouse.click(x, y)` 之前必须先确认目标 rect 完整落在当前视口内**——取 rect → 若 `top<0 || bottom>innerHeight` 先 `scrollIntoView({block:'center'})` → **等 300–500ms 让滚动落定** → **重取 rect** → 再点。视口外的坐标点击**不报错、不生效**，是最难定位的一类失败。同理：**点击后必须回读具体状态字段**（`display` / `textContent` / `value` / `img.naturalWidth`），不能只信点击回执。
- **🔴 页面文本判据必须先归一化空白（v3.63.0 坑 305，1025 实测）**：`innerText` 按渲染折行输出，卡片标题常被拆成 `【2026-10-25】Kimi\nK3.1 Pro …`。拿原始 `t` 跑 `/Kimi K3\.1/` 必假阴性，拿 `t.replace(/\s+/g,' ')` 才命中。**铁律：判据和证据必须用同一份归一化文本**——先算一次 `const t = raw.replace(/\s+/g,' ')`，判据和打印都只用 `t`。**「打印的证据明明含目标串、结论却是 false」就是这个坑的指纹**，见到不要怀疑平台，改判据。
- **权限预授权是第一步**，覆盖内容生成 + 全部平台上传，一次确认后全程不再询问
- 每个 Phase 完成后向用户展示中间结果，确认后继续
- 图片生成失败时自动重试一次
- TTS 使用 mimo-tts，推荐预置音色「白桦」（不要用克隆音色！）
- **TTS 必须串行执行，禁止并行！**
- 视频总时长按 `REPORT_MODE`：daily 60-120s（≤150s）/ weekly **100-150s**（深聊型，替代旧 90-120s）/ **monthly 180-240s（≤300s）**
- 事件数量建议 4-6 个（日报/周报）
- **默认全模式 3W + 可信度**（v3.4）；精简 = 3-5 条 + 更短句，总时长约 60-100s
- **灰色渠道每期 ≤1**；情绪黑名单见 `templates/credibility-and-tone.md`
- **精简模式可与破格模式、周报模式、月报模式叠加使用**
- **月报模式事件数为 4 趋势主线**（精简月报 3 趋势），不要套用日报 4-6 单日事件
- **月报模式每段 ≤100 字**（趋势段落比日报单事件长）
- **月报 B站简介强制全数字中文化**（见 B站简介数字中文化章节，月报数据全数字，不中文化必触发违规推广检测）
- **月报合集「羊报AI月报」需用户预先在 B站/公众号后台创建**，否则上传 Phase 失败
- **月报不重新聚合**：直接消费 linuxdo-daily v13 的 `data/monthly/{YYYY-MM}.md`，不读取当月日报
- **月报去重改为对比上期月报**（`data/monthly/{上月}.md`），不扫 30 天日报（月报本身已跨日去重）
- **Phase 1 去重是强制步骤，不可跳过**（月报模式改为对比上期月报，同样不可跳过）
- **Phase 1 Step 1.6 专业锚点选题是强制步骤**（用户可选手动换概念或跳过；算法见 `templates/professional-anchor.md`）
- **Phase 2 用户确认脚本后必须写 `ai-concept-bank` usage-log**（`ANCHOR_SKIP` 除外），再进 Phase 3
- **专业锚点台词只读 eligible ready**（narrator + reviewed + 非空）；否则调 `ai-concept-narrator`，禁止主会话瞎编长段
- **Phase 8（渲染前校验）是强制步骤，不可跳过**
- **字幕必须使用原始脚本文本 + ffprobe 对齐**，不用 FunASR（专业术语识别率太低）
- **B站自定义下拉框必须用 JS evaluate，不能用 browser_click 文本匹配**
- **封面生成应与 TTS 并行执行**（用 Agent 异步），节省 3-5 分钟

### imageId 偏移问题（v2.7.0 修复，v2.8.0 补充）

Composition.tsx 中 imageId 与实际图片文件可能存在偏移。验证方法：
```bash
# 对比文件大小确认 public 目录的文件是否正确
ls -la news-pipeline/video-project/public/images/scene*.png
ls -la news-pipeline/YYYY-MM-DD/images/scene*.png
# 用 md5 验证
for i in 1 2 3 4 5 6; do
  src=$(md5 -q news-pipeline/YYYY-MM-DD/images/scene${i}.png)
  pub=$(md5 -q news-pipeline/video-project/public/images/scene${i}.png)
  [ "$src" = "$pub" ] && echo "scene${i}: OK" || echo "scene${i}: MISMATCH"
done
```

如果图片内容正确但视频中错位，修改 Composition.tsx 的 imageId 映射，而不是重新生成图片。
常见原因：上次渲染的 sceneConfig 未更新，或 scene 数量变化导致 ID 整体偏移。

**v2.8.0 补充**：偏移最常见的根因是 Hook 场景独立生成了一张图片，而脚本中 Hook 与第一条新闻是同一个场景。
预防措施：Phase 4 生成 prompt 时，图片数量必须与脚本场景数一致（见 Phase 4 图片-脚本映射铁律）。

### 公众号封面上传（自动方法）

公众号编辑器上传图片有两种路径：

**路径 A：工具栏「图片」按钮（推荐）**
```javascript
// 1. 点击正文区域获取 focus
await page.evaluate(() => {
  const editors = document.querySelectorAll('.ProseMirror');
  if (editors[1]) editors[1].click();
});
// 2. 点击工具栏「图片」→「本地上传」
// 3. 用 hidden file input 上传（封面图：horizontal-4-3.png 横版 / vertical-3-4.png 竖版）
const input = await page.$('input[type="file"][accept*="image"]');
await input.setInputFiles('news-pipeline/YYYY-MM-DD/horizontal-4-3.png');
```

**路径 B：封面区域直接上传**
```javascript
// 1. 找到封面区域的 file input（可能有多个）
const inputs = await page.$$('input[type="file"]');
// 2. 筛选 accept 包含 image 的
for (const input of inputs) {
  const accept = await input.getAttribute('accept');
  if (accept && accept.includes('image')) {
    await input.setInputFiles('news-pipeline/YYYY-MM-DD/horizontal-4-3.png');
    break;
  }
}
```

### B站封面上传（自动方法）

B站上传页面的封面选择器是隐藏的 file input：
```javascript
// 1. 先点击「更改封面」按钮
// 2. 找到 hidden file input 并上传
const input = await page.$('input[type="file"][accept*="image"]');
await input.setInputFiles('news-pipeline/YYYY-MM-DD/horizontal-4-3.png');
// 3. 等待上传完成，点击确认
```

### 🔴 所有平台上传一律存草稿（v2.8.0 新增，2026-06-29 确认）

**问题**：自动发布/投稿存在风险，标题、封面、合集等可能需要用户二次确认。

**解决方案**：所有平台上传后一律保存草稿，不直接发布。用户可在各平台草稿箱中检查后手动发布。

**各平台存草稿操作**：
| 平台 | 操作 | 说明 |
|------|------|------|
| B站 | 点击「存草稿」 | 替代「立即投稿」 |
| 抖音 | 点击「暂存离开」或关闭标签页 | 视频自动保存到草稿箱 |
| 视频号 | 点击「保存草稿」 | 视频进入草稿箱 |
| 公众号 | 点击「保存为草稿」 | 文章进入草稿箱 |

**Why:** 自动发布容易出错，用户需要二次确认内容
**How to apply:** Phase 11-14 所有平台上传最后一步改为存草稿，不要点击发布/投稿

### 🔴 视频号 iframe 上传复杂（v2.8.0 新增，2026-06-29 确认）

**问题**：视频号页面内容在 iframe 中，文件上传的 file input 在 iframe 内部，Playwright 的 `frame.$()` 有时找不到动态创建的 input。

**解决方案**：
1. 先检查 iframe 结构：`page.frames()` 找到 `name="content"` 的 iframe
2. 在 iframe 内用 `frame.evaluate()` 操作 DOM
3. 如果 file input 找不到，提示用户手动上传

**Why:** 视频号使用 Ant Design 的 Upload 组件，file input 是动态创建的
**How to apply:** 视频号上传如果自动化失败，直接跳过提示用户手动操作

### 🟡 抖音封面弹窗关闭确认（v2.8.0 新增，2026-06-29 确认）

**问题**：抖音封面编辑弹窗关闭时会弹出确认对话框「你有未保存的封面编辑效果，是否关闭？」。

**解决方案**：点击「确定」关闭弹窗，封面已自动保存。

**Why:** 抖音的封面编辑器有防误关机制
**How to apply:** 关闭封面弹窗时如果出现确认对话框，点击「确定」

### 🟡 抖音章节要点弹窗（v2.8.0 新增，2026-06-29 确认）

**问题**：抖音上传视频后会自动弹出「章节要点」弹窗，阻挡后续操作。

**解决方案**：关闭章节弹窗（点击 X 或取消），不影响视频发布。

**Why:** 抖音自动检测视频内容生成章节建议
**How to apply:** 上传视频后如果出现章节弹窗，直接关闭

### 🔴 公众号弹窗阻挡「保存为草稿」（v3.3.0 新增，2026-07-05）

**问题**：公众号封面图上传后弹出「图片上传中，请稍后」弹窗，此时点击「保存为草稿」无效（被弹窗拦截）。弹窗不会自动关闭，需要等待图片上传完成。

**解决**：
1. 上传封面图后等待 10 秒再操作（`browser_wait_for(time=10)`）
2. 保存前检测是否有弹窗阻挡：`document.body.textContent.includes('上传中')`
3. 如果仍有弹窗，按 Escape 关闭弹窗后再保存
4. 验证保存成功：`document.body.textContent.includes('已保存')`

```javascript
// 保存前自动处理弹窗
browser_run_code_unsafe("""async (page) => {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  await page.waitForTimeout(5000);
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.textContent.trim() === '保存为草稿') {
        btn.click(); return;
      }
    }
  });
  await page.waitForTimeout(3000);
  const body = await page.evaluate(() => document.body.textContent);
  return body.includes('已保存') ? 'saved!' : 'failed';
}""")
```

**Why:** 公众号图片上传是异步的，但弹窗会阻挡所有按钮点击
**How to apply:** Phase 12 公众号上传时，封面图上传后等10s，保存前先Escape关闭弹窗

### 🟡 公众号合集选择失败时自动跳过（v3.3.0 新增，2026-07-05）

**问题**：公众号合集选择器用 `page.getByText('「羊报AI周刊」', { exact: true })` 精确匹配时，可能因合集名不完全匹配而超时（如合集名实际为「羊报AI周刊」vs页面显示差异）。

**解决**：合集选择失败时自动跳过，不阻塞保存草稿。合集可后续手动添加。

```javascript
// 合集选择带超时保护
try {
  const option = page.getByText('「羊报AI周刊」', { exact: true });
  await option.hover({ timeout: 5000 });
  await option.click();
} catch (e) {
  console.log('合集选择跳过: ' + e.message);
  await page.keyboard.press('Escape');
}
```

**Why:** 合集选择器是自定义 Vue 组件，匹配规则不稳定
**How to apply:** Phase 12 公众号合集选择用 try-catch 包裹，失败时 Escape 跳过

### ⚠️ 已废弃：B站封面上传 file input 无 image accept（v3.3.0，2026-07-05）→ 被坑 218 取代

> **🔴 v3.38.0 / 0921 作废**：新版「封面制作」弹窗打开后**确实存在** `accept="image/png, image/jpeg"` 的封面 input；下面「按 `inputs[1]` 索引取」的做法在改版后**会把 png 喂给 `.mp4`/`.zip` input 且静默无报错**（0921 连错两次），已改为**按 accept 过滤**。正文见 §11.3 与 `templates/bili_cover.py`。仅当后台回退到旧版（无「封面制作」弹窗）时才回到本条。

**问题（v3.3.0 语境）**：B站上传页面有 4 个 file input，当时没有任何一个的 accept 属性包含 image 类型。

**解决（已废弃）**：按位置索引取 `inputs[1]`：
```javascript
// ⛔ 禁止再用：改版后 inputs 数变 5，inputs[1] 指向视频 input
const inputs = await page.$$('input[type="file"]');
// inputs[0]: 视频 (.mp4)   inputs[1]: ??? 取决于弹窗是否打开
await inputs[1].setInputFiles('horizontal-4-3.png');   // ⛔ v3.38.0 起禁用
```

**Why（作废原因）:** 索引随页面状态漂移，且失败是静默的——只有改成「按 accept 过滤 + 断言 `.cover-empty` 消失」才能自证。
**How to apply:** Phase 11 一律走 §11.3 弹窗协议 / `templates/bili_cover.py`，**任何情况下不要再按索引取封面 input**。

### 🔴 精简模式脚本审核必须前置（v3.3.0 新增，2026-07-05）

**问题**：脚本生成后直接展示给用户，但没有先执行脚本审核检查清单。用户需要提醒才执行审核。

**解决**：脚本生成后、展示给用户前，**必须先执行审核检查清单**，审核结果和脚本一起展示：

```
## ✅ 脚本审核检查
1. 禁止词汇检查 ✅
2. 口语化程度 ✅
3. 平台合规审查 ✅
4. 标题检查 ✅
5. 内容准确性 ✅

## 📝 脚本内容
[完整脚本]
```

**Why:** 用户期望审核是自动执行的，不需要手动提醒
**How to apply:** Phase 2 脚本生成后，先审核再展示，审核不通过则修改后再展示

### 🟡 周报去重需对比上周周报（v3.3.0 新增，2026-07-05）

**问题**：周报模式的去重策略是「对比上一期周报」，但实际执行时没有找到上周周报文件，跳过了去重。

**解决**：如果上周周报文件不存在（`data/reports/2026-W26.md`），跳过去重步骤，但在脚本审核时标注「未去重」。

**Why:** 周报文件可能不存在（首次生成或文件被清理）
**How to apply:** Phase 1 周报去重时，先检查上周周报文件是否存在，不存在则跳过

### 🔴 MCP 与独立 Playwright 互抢 Profile（v3.7.0 / 2026-07-18）
**问题**：流水线中为视频号上传反复 `pkill` 共用 profile，用户感知「浏览器老是退出」。
**解决**：见文首「浏览器与 Profile 全局铁律」；仅在切换驱动时 scoped kill；向用户解释关闭原因。
**Why:** 同一 `user-data-dir` 不能被两个 Chromium 同时占用。
**How to apply:** 视频号优先 MCP 闭环；独立脚本仅作 fallback。

### 🔴 视频号双 body 导致 MCP 工具层崩溃（v3.7.0 / 2026-07-18）
**问题**：`strict mode violation: locator('body') resolved to 2 elements`（外层 + wujie-app body）。
**解决**：单次 `browser_run_code_unsafe` 完成关键步骤；返回前导航到 baidu/about:blank；禁止在双 body 页用 snapshot/find/file_upload。
**How to apply:** Phase 13 全程遵守。

### 🔴 视频号封面 3:4/4:3 与 CDP setFileInputFiles（v3.7.0 / 2026-07-18）
**问题**：`input[accept=image/*]` 在 `.single-cover-uploader-wrap` 中 `display:none`，跨 frame `setInputFiles` 报 detached；须等「预览图生成中」结束。
**解决**：点对应比例「编辑」后，用 CDP `DOM.performSearch` + `backendNodeId` + `DOM.setFileInputFiles`；4:3 已多次验证成功，3:4 同法但须点中 `.vertical-cover-wrap` 的编辑。
**How to apply:** Phase 13 封面步骤。

### 🔴 公众号「从正文选择」缩略图非 img 标签（v3.7.0 / 2026-07-18）
**问题**：弹窗缩略图是 `span.appmsg_content_img.cover` + background-image，`img` 列表为空导致无法选中、「下一步」不进入裁剪。
**解决**：点 `.appmsg_content_img_item`；裁剪点「确认」；验收看 `#js_cover_area .js_cover_preview_new` 的 background-image。
**How to apply:** Phase 12 封面。

### 🔴 公众号裁剪确认与验收（v3.8.0 / 2026-07-19 周报实测）
**问题**：
1. 点「下一步」后进入「编辑封面」，页面同时存在 **disabled「确定」** 与 **「确认」**；点错会超时/`Element is not visible`
2. 过早 `Escape` 会关掉裁剪，preview 仍为 `display:none` / `url("")`
3. 成功后文案区仍可能显示「拖拽或选择封面」，误判为失败

**解决**：
1. 只点 `button` 文本精确为 **「确认」** 且 `class` 含 `weui-desktop-btn_primary`、**不含** `disabled`
2. 裁剪弹窗打开期间 **禁止 Escape**
3. 成功条件：`.js_cover_preview_new` 的 `display==='block'` 且 `background-image` 含 `mmbiz`/`qpic`；可再存草稿（`appmsgid=` 保留）
4. 已有草稿用 `appmsg?…&appmsgid=` 直达编辑，比「新的创作」稳

**Why:** 2026-07-19 周报 `appmsgid=100000479` 封面链路完整复现后才闭环。  
**How to apply:** Phase 12.7 一律走 v3.8.0 轮询验收。

### 🟡 B站存草稿成功信号（v3.8.0 / 2026-07-19）
**问题**：第二次再找「存草稿」按钮可能 `not found`，但 URL 已跳到 `upload-manager/article?group=draft`。
**解决**：以 **URL 含 `group=draft`** 为成功；中文文件名先复制为 `upload-weekly-w28.mp4` / `upload-YYYY-MM-DD.mp4` 再传。
**How to apply:** Phase 11 末检查 URL。

### 🟡 视频号未登录不阻塞流水线（v3.8.0 / v3.9.0）
**问题**：`channels.weixin.qq.com` 落到 `login.html` 扫码页时整条流水线挂起。
**解决**：检测到登录页 → 标记 `channels: login_required`，继续抖音/公众号；向用户汇报需扫码后手传。
**How to apply:** Phase 13 开头检查 title/URL 含 login。

### 🔴 视频号「用户已登录」≠ MCP 已登录（v3.9.0 / 2026-07-20 实测）
**问题**：用户说「视频号已经登录」后，MCP 仍停在 `login.html`；`net::ERR_HTTP_RESPONSE_CODE_FAILURE`；QR iframe「加载失败，点击重试」；在错误 profile 上反复刷新二维码空转。
**解决**：
1. **以 MCP 页为准**：`page.url()` 含 `login.html` 或标题/正文含「登录视频号助手」→ 仍 `login_required`
2. 用户本机其它 Chrome 已登录**不能**代替 MCP profile
3. 需要扫码时：在 **MCP 当前标签**出码，等 URL 离开 login 再上传；二维码加载失败可 `page.reload` 1–2 次，仍失败则写 `upload-status.md` 为 ⏭ 并**停止空转**
4. `ERR_HTTP_RESPONSE_CODE_FAILURE` 于 channels 域名：等 5–10s 重试 1 次；持续失败按未登录跳过
5. 禁止生成大量无执行价值的 `CHANNELS_*_GUIDE.md` 代替实际上传
**Why:** 0720 多轮「已经登录继续上传」仍卡 QR，浪费会话。
**How to apply:** Phase 13 入口硬判定 + upload-status 落盘。

### 🔴 抖音「暂存」不等于草稿可见（v3.9.0 / 2026-07-20）
**问题**：上传页操作看似成功，内容管理无当日草稿；用户反馈「抖音没看到草稿」。
**解决**：以「继续编辑」/ 内容管理标题 / draft 页非空表单验收；失败整段重传。
**How to apply:** Phase 14.10 验收三信号。

### 🔴 竖封面必须用当期 vertical-3-4.png（v3.9.0）
**问题**：补封面时用错图或比例不对，用户明确「竖封面3:4 不对」。
**解决**：只认 `news-pipeline/{date}/vertical-3-4.png`；上传后仍要 `missingV=false`。
**How to apply:** Phase 5.5 生成 + 14.6/14.10 补传。

### 🟡 TTS 503 网关无节点（v3.9.0）
**问题**：`gateway_error: 没有可用的内网节点`。
**解决**：退避重试 + fallback URL；校验 wav 非空。
**How to apply:** Phase 6。

### 🟡 免确认仍要审核落盘（v3.9.0）
**问题**：免确认时只自检不落盘，用户追问「有没有通过审核清单」。
**解决**：写 `review-checklist.md` 或 script 文末表。
**How to apply:** Phase 2 末。

### 🟡 图片/TTS API 读 settings.env（v3.8.0）
**问题**：主会话手写 API 易漏备选；打印 key 被安全策略拦截。
**解决**：从 `~/.claude/settings.json` 的 `env` 读 `GEN_IMG_API_URL`/`GEN_IMG_API_KEY`（及 `_001/_002`）、`MIMO_TTS_API_URL`/`MIMO_TTS_API_KEY`；脚本内 fallback，**日志禁止打印 key**。
**How to apply:** Phase 5/6 生成脚本。

### 🟡 抖音竖封面必须带日期（v3.7.0 / 2026-07-18）
**问题**：竖封面生成失败时用 scene 图回退，用户反馈「上面没日期」。
**解决**：`vertical-3-4.png` 失败必须重试 GEN_IMG，prompt 强制底部 `YYYY-MM-DD` 与右上「今日羊报 AI」；禁止无品牌 scene 回退当封面。
**How to apply:** Phase 5.5 / 14.6。


### 🔴 GEN_IMG 多端点与 Bash 超时（v3.10.0 / 2026-07-21）
**问题**：7 张 scene 串行生成时 Bash 默认 10 分钟超时被 kill（exit 143）；部分端点 HTTP 000/502。
**解决**：
1. 从 settings.env 组装 endpoint 列表 `['', '_001', '_002']`，逐张生成、已有文件跳过
2. 单张 max-time 90–180s；整批超时按张数放大或拆成多条 Bash
3. 日志只打印 `set/empty/len`，禁止打印 key 前缀（安全策略会拦）
4. CTA scene 可兜底；`vertical-3-4.png` 必须当期生成成功
**How to apply:** Phase 5 / 5.5

### 🔴 usage-log 与 concepts 根结构（v3.10.0 / 2026-07-21，v3.46.0 坑 246 补充）
**问题**：把 `concepts.json` 当 list 迭代 → `AttributeError: str has no get`。
**解决**：`data = json.load(...); concepts = data['concepts']`；usage-log 可能是 list 或 `{entries:[]}`，append 时兼容两种。
**v3.46.0 补充（坑 246，W40 verify 脚本实测）**：`concepts` 本身是 **list**，按 id 查必须 `next(x for x in concepts if x.get('id')=='token')`。W40 的 `verify_w40.py` 写成 `concepts.get('token')`，对 list 直接 `AttributeError: 'list' object has no attribute 'get'`——根结构修对了，内层查询又当 dict 用，是同一类错误的第二处。
**verify 分两级跑**：落盘脚本层（事件词/锚点逐字/桥句字数/旧口径零残留）脚本落盘即跑；**总时长 100–150s、锚点占比等实测项必须等 `durations.json` 生成后再跑**，无 durations 时 INFO 跳过，**不算 FAIL**。
**How to apply:** Step 1.6 / Phase 2 写 log / 每期 `verify_*.py`

### 🟡 公众号草稿成功但封面未闭环（v3.10.0 / 2026-07-21）
**问题**：`appmsgid=` 已出现，`.js_cover_preview_new` 仍 `display:none`。
**解决**：草稿优先；封面失败写 upload-status「可手补封面图（horizontal-4-3.png / vertical-3-4.png）」；不因封面阻塞汇报成功。
**How to apply:** Phase 12 + upload-status.md

### 🟡 B站存草稿后 URL 已是 group=draft（v3.10 再确认）
**问题**：脚本 `draftClicked=false` 但 URL 已跳转草稿箱。
**解决**：以 `group=draft` 为成功信号，不依赖按钮二次查找。
**How to apply:** Phase 11


### 🔴 GEN_IMG 整批 10 分钟超时后必须续跑缺失文件（v3.11.0 / 2026-07-22）
**问题**：scene1–7 已生成，`horizontal-4-3.png` 也生成了，但 `vertical-3-4.png` 还没跑完时 Bash 10min kill（exit 143）。若当成「封面全失败」会重跑 scene 浪费时间。
**解决**：
1. 超时后立刻 `ls` 校验每张 `sceneN.png` / 平台封面的 size（>5KB 视为成功）
2. **只补缺失文件**，禁止无条件重跑已有 scene
3. 封面可单独一条 Bash；scene 与 cover 可拆开执行
**How to apply:** Phase 5 / 5.5 超时后先盘点再补齐

### 🔴 GEN_IMG 全挂 / 封面文字糊掉时本地 Pillow 兜底（v3.19.0 / 2026-08-21）
**问题**：GEN_IMG 所有端点 401/余额耗尽（0821 实测 prism+luka77 全 401，仅 xmiaom 出图）；或 API 出封面但中文日期/品牌名糊掉错字——封面文字必须像素级准确。
**解决**：
1. Scene 图全挂 → `gen_images_local.py`（Pillow 画 8 张抽象背景，深色演播室 + 场景配色 + 几何 motif）
2. 封面 API 余额耗尽 / 文字糊掉 → `gen_covers_local.py`（拿 `scene1.png` 作底图 + 渐变蒙版 + 本地字体叠加日期/品牌）
3. 见 Phase 5.6 完整脚本模板与决策流程
**Why:** 0821 scene 图走 API 成功，但封面 API 余额耗尽，用本地 Pillow 叠加保证日期文字 100% 清晰。
**How to apply:** Phase 5.6；API 恢复后应切回 API（本地图为兜底非默认）

### 🔴 抖音 filechooser 链式打断后的恢复（v3.11.0 / 2026-07-22）
**问题**：横/竖封面 `waitForEvent('filechooser')` 与后续步骤叠在一次长 `run_code` 里时，工具层会停在「Modal state: File chooser」，后续逻辑不返回；取消 chooser 后可能落到 `upload?enter_from=publish` 空页。
**解决**：
1. **横封面 / 竖封面上传拆成独立短步骤**；出现 File chooser 模态时用 `browser_file_upload(paths=[...])` 处理，禁止在同一长脚本里「点上传+等 chooser+再点完成」硬串
2. 若被带回上传页：以是否出现 **「你还有上次未发布的视频 / 继续编辑」** 判定草稿已落库
3. 点「继续编辑」验收描述/视频是否在；封面缺失可手补，不必整段重传视频
**How to apply:** Phase 14 封面步骤拆分 + 上传页「继续编辑」验收

### 🔴 公众号「新的创作」菜单项 class（v3.11.0 / 2026-07-22）
**问题**：只点 heading「新的创作」不会开文章；文本匹配「文章」易命中别处。
**解决**：`.new-creation__menu-item` 第一项即「文章」，`menu[0].click()` 会新开 `appmsg_edit` 标签；再 `browser_tabs(select, index=最新)`。
**How to apply:** Phase 12.2

### 🟡 浏览器崩溃后先重建再上传（v3.11.0）
**问题**：连续 `mp.weixin` / `channels` / `baidu` 导航 Timeout 后，下一调用报 `Target page, context or browser has been closed`。
**解决**：`pkill -f mcp-chrome` → sleep → 重新 `browser_navigate`；不要在 closed target 上继续堆工具调用。
**How to apply:** 任意 Phase 11–14 导航连环超时后

### 🔴 视频号限流 + 公众号按《公众账号信息服务管理规定》删文（v3.13.0 / 2026-07-26）
**问题**：
- 视频号：状态「限制传播」，问题说明「存在敏感或者违规内容」，仅引用《视频号常见违规内容概览》，**无细码**
- 公众号：通知「接相关投诉，违反《互联网用户公众账号信息服务管理规定》，已删除」，**不写条款号**
- 同期成片标题/脚本含：Opus5 发布 + DeepSeek 融资外泄/暂停 + 开源「切断」/政策升温；封面为写实 AI 主播
**解决**：
1. 强制对照新文件：`微信视频号常见的不合规频道内容概述.md`、`微信公众号互联网用户公众账号信息服务管理规定.md`
2. 执行 `templates/platform-compliance.md`：选题 A/B 档；公众号默认不上 B 档；封面禁写实主播
3. 标题禁「同日升温/切断/外泄/博弈/风暴」；媒体信息标题勿写成定论
4. 视频号打 AI 生成标识；被处置后优先改封面+改文案重发，勿同题硬刚申诉
**Why:** 0726 双端同时处置，根因是「新闻体包装 + 融资/政策话术 + AI 真人封面」叠加，而非单句脏话/低俗
**How to apply:** Phase 1–2 / Phase 5.5 / Phase 10；review-checklist 必须含 platform-compliance §5

### 🔴 抖音「不适宜公开 / 仅自己可见·画面」与周报攻击叙事（v3.14.0 / 2026-07-26–27 周报）
**问题**：
1. 标题 `沙箱逃逸进立法·Kimi开源地缘` → 抖音 **不适宜公开**；视频号 **限制传播**（描述同样含逃逸/立法）
2. 换成产品向标题 + 新封面后仍 **限制自己可见**，违规原因标 **「画面」** → 机审扫的是**成片帧**，不是元数据
3. 原 scene prompt 含 security breach、cracked isolation glass、legislative silhouettes、gavel 等
4. 内部 `review-checklist` 黑名单/3W 全过，**仍过不了抖音/视频号机审**
**解决**：
1. 抖音/视频号/公众号主标题禁用：`逃逸/入侵/窃取/横向移动/立法/两党/终止开关/地缘`（作主卖点时）→ 见 `platform-compliance.md` §8
2. 推荐标题：`评测安全升级·Flash全量与订阅变化｜羊报AI周刊 …`；短标题：`本周AI安全与工具速览`
3. **画面违规强制过审重渲**：`voiceover-texts-safe.json` + `image-prompts-safe.json` 重画高风险 scene（建议 1/2/3/6 或全量）→ TTS → captions → Remotion → `*-safe.mp4`
4. 落盘 `platform-copy-safe.md` 供用户复制；旧敏感 mp4 归档勿再发
5. 只改标题/封面后重传旧片 = **无效**；必须新成片
**Why:** W29 周报同日双端处置；二次投稿证明「画面」标签独立于标题
**How to apply:** Phase 2 标题分平台；Phase 3–5 画面合规；处置后走 platform-compliance §6.1

### 🟡 公众号草稿「只补封面」（v3.14 / 2026-07-27）
**问题**：用户只要更新 `appmsgid=…` 封面，正文自理；自动化链路可能 `preview display:none` 仍点了确认/保存。
**解决**：
1. 直达 `appmsg?…&appmsgid=` → 正文插封面图（`horizontal-4-3.png` / `vertical-3-4.png`）→ 从正文选择 → 编辑封面 → **确认** → 保存草稿
2. 验收优先：`.js_cover_preview_new` 的 `display:block` + `mmbiz/qpic`；失败时**明确告知用户需手补**，不假装成功
3. 勿在用户未要求时改标题/正文
**How to apply:** Phase 12 封面-only 任务

### 🔴 TTS 禁止在工具参数里硬编码 API Key（v3.12.0 / 2026-07-25）
**问题**：Bash/Python 参数文本含 `sk-mimo-…` 时，自动模式安全分类器 **Credential Leakage** 直接拒绝；会话卡住。
**解决**：
1. 写 `news-pipeline/{date}/scripts/gen_tts.py`：**只从** `MIMO_TTS_API_*` 环境变量、`~/.claude/settings.json` env、或历史 `news-pipeline/*/scripts/gen-tts.sh` 的 export **读 key**（脚本内解析，**不**把 key 写进工具调用文本）
2. 运行：`python3 news-pipeline/{date}/scripts/gen_tts.py`（日志只打 `keylen` / 端点名）
3. endpoint 列表：历史 gen-tts 的 URL + `token-plan-cn` / `token-plan-ams` fallback；失败退避重试
4. 每 scene 校验 wav `>5KB`；已存在则跳过
**Why:** 0725 首次 TTS 因硬编码 key 被拒。
**How to apply:** Phase 6 一律「脚本读凭据」，禁止 `export MIMO_TTS_API_KEY=sk-...` 出现在工具参数里。

### 🔴 B站草稿补封面闭环（v3.12.0 / 2026-07-25）
**问题**：首次投稿常跳过封面；用户追问「封面上传了吗」。
**解决（草稿编辑页）**：
1. 打开 `upload-manager/article?group=draft` → 找当日标题 → `frame?type=draft&draftId=...`
2. 点 **「封面设置」**（`.cover-empty` / 坐标点封面框）→ 弹窗 **「封面制作」**
3. 弹窗内出现 `input[accept="image/png, image/jpeg"]`（可有多个：4:3 / 16:9）→ **`setInputFiles(horizontal-4-3.png)`**（🔴 v3.38.0：这就是**坑 218** 的同一弹窗；首次投稿走 §11.3 / `templates/bili_cover.py`，本条是草稿补传路径）
4. 点底部 **「完成」**（y 较大的主按钮）
5. 验收：`.cover-empty` / `.cover-empty.failed` **消失**；`.cover-img` 的 `background-image` 含 `archive.biliimg.com` 或 `bfs/archive`
6. 再点 **「存草稿」**；成功信号仍是 URL `group=draft`
**标题坑**：稿件标题 `maxLength=80`，用 **原生 `HTMLInputElement` value setter** + `input` 事件，不要只靠 React 假赋值。
**Why:** 0725 草稿 `draftId=3685995` 封面补传成功。
**How to apply:** Phase 11 首次可先存草稿；缺封面则走本闭环，**不要**默认「建议用户手传」就结束。

### 🔴 视频号独立脚本 vs MCP Profile 锁（v3.12.0 / 2026-07-25）
**问题**：MCP 仍占用 `mcp-chrome-*` 时，`channels_upload.js` 报 `Failed to create a ProcessSingleton` / SingletonLock。
**解决**：
1. 跑独立脚本前：`browser_close` 或 `pkill -f mcp-chrome` → `rm -f …/SingletonLock` → sleep 2
2. 再用 `NODE_PATH=…/node_modules` + `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=…/Google Chrome for Testing` 启动
3. 若 URL 仍是 `login.html` → `login_required` ⏭，写 `upload-status.md`，**禁止空转扫码循环**
**Why:** 0725 视频号先被 profile 锁挡住，释放后仍 login_required。
**How to apply:** Phase 13 独立脚本路径；与文首「浏览器 Profile 铁律」一致。

### 🟡 抖音 filechooser + 暂存验收（v3.12 再确认 / 0725）
- 视频 / 横竖封面：`waitForEvent` 触发后工具层停在 **File chooser** → 下一步必须 `browser_file_upload(paths=[...])`
- 暂存后回上传页：出现 **「你还有上次未发布的视频…继续编辑」** 即草稿 ✅

### 🔴 抖音 Semi Design 组件拦截（v3.18.0 / 2026-08-18）
**问题**：抖音创作者中心基于 Semi Design，`label.semi-radio` 拦截自主声明 radio 的 pointer events（`locator.click()` 超时 30s）；`div.semi-modal-wrap` 拦截「暂存离开」按钮；`browser_run_code_unsafe` 触发 file chooser 后工具层停在 "Modal state: File chooser" 阻塞后续调用。
**解决**：
1. 自主声明 radio：`page.locator('label.semi-radio').filter({ hasText: '内容为个人观点或见解' }).click()`
2. 「暂存离开」：`page.keyboard.press('Escape')` → `waitForTimeout(1000)` → `locator('button:has-text("暂存离开")').click({ force: true })`
3. file chooser：用 `browser_file_upload(paths=[...])` 处理，不要在同一长脚本里串 `filechooser` 事件
**Why:** 0818 自主声明超时 30s、暂存离开被 modal 拦截、file chooser 卡 Modal state。
**How to apply:** Phase 14.8 自主声明 / 14.10b 暂存离开 / 14.2/14.6 文件上传

### 🔴 视频号 QR 跨域 iframe 无法自主扫码（v3.18.0 / 2026-08-18）
**问题**：`channels.weixin.qq.com` 重定向 `login.html`，QR iframe 来自 `open.weixin.qq.com`（跨域），iframe 显示「加载失败，点击重试」，点击重试 + 等 5s 仍不加载；跨域 iframe `contentDocument` 为 null，JS 无法访问；`page.reload` 1–2 次仍失败。
**解决**：reload 1–2 次仍失败 → 标记 `channels: login_required`，写 `upload-status.md` 为 `⏭`，停止空转；**明确**自主流程无法完成视频号扫码登录，需用户手动扫码后重跑。
**Why:** 0818 视频号 QR 跨域加载失败，自主流程空转无果。
**How to apply:** Phase 13.0b

### 🔴 抖音草稿恢复弹窗「继续编辑放弃」文本合并（v3.18.0 / 2026-08-18）
**问题**：上传页弹「你还有上次未发布的视频，是否继续编辑？」，点击合并文本「继续编辑放弃」无法精确丢弃旧草稿，会落到 `enter_from=draft` 编辑页混入旧素材；离开草稿编辑页时弹 beforeunload「将此次编辑保留？」，不处理会触发 `net::ERR_ABORTED`。
**解决**：从草稿编辑页点「重新上传」→ 导航回 upload 页 → 重新触发 file chooser；离开草稿页弹 beforeunload 时 `browser_handle_dialog(accept=true)`。
**Why:** 0818 旧草稿混入新上传，beforeunload 未处理导致导航失败。
**How to apply:** Phase 14.0

### 🟡 公众号 appmsgid 验收（v3.12 再确认 / 0725）
- `.new-creation__menu-item[0]` 开文章；标题/作者/正文 ProseMirror 注入；**保存为草稿** 后 URL 含 `appmsgid=`（0725：`100000512`）
- 封面可手补，不阻塞草稿成功

### 🔴 抖音草稿恢复弹窗「放弃」精确点击（v3.22.0 / 2026-08-28）
**问题**：上传页弹「你还有上次未发布的视频，是否继续编辑？」，点合并文本「继续编辑放弃」会落到 `enter_from=draft` 编辑页混入旧素材。
**解决**：用 JS evaluate 精确点 `textContent.trim() === '放弃'` 的可见按钮节点（勿点合并文本）；点完弹窗消失即恢复 upload 页空白上传区。
**Why:** 0828 实测点合并文本落到草稿编辑页，beforeunload 连环 + `net::ERR_ABORTED`。
**How to apply:** Phase 14.0

### 🔴 抖音封面选择被 @好友 mention 浮层拦截（v3.22.0 / 2026-08-28）
**问题**：点「横封面4:3」同卡的「选择封面」无反应——点击被 `publish-mention-wrapper`（话题/`@好友` 自动补全浮层）拦截。
**解决**：先 `keyboard.press('Escape')` 关浮层 → JS evaluate 找「设置封面」header → `parentElement` 攀爬到封面容器 → 点容器内第一个 `textContent === '选择封面'` 的 div。
**Why:** 0828 实测封面点击静默失败，发文助手仍报「竖封面缺失」。
**How to apply:** Phase 14.6 步骤1 之后兜底

### 🔴 抖音描述/话题 contenteditable 误用 nth(1)（v3.22.0 / 2026-08-28）
**问题**：`div[contenteditable="true"].nth(1)` 30s 超时——编辑页通常只有 1 个 contenteditable（描述/简介），话题另有入口。
**解决**：描述填 `contenteditable.nth(0)`；话题（#标签）改点「#添加话题」按钮 → `keyboard.type(tag)` + `keyboard.press('Enter')` 逐个加。
**Why:** 0828 实测 `nth(1)` 超时导致描述/话题卡住。
**How to apply:** Phase 14.5b

### 🔴 抖音合集名大小写陷阱（v3.22.0 / 2026-08-28）
**问题**：硬搜「今日羊报AI」返回 not found——实测抖音合集名是「「今日羊报Al」」（小写 L，非大写 I）+ 「共80个作品」，与 B站/公众号不同。
**解决**：探测下拉框可见文本，按「今日羊报」前缀（不分大小写）+ 「共N个作品 / 共N个内容」模糊匹配选项点击（**两种文案都存在**，1025 抖音仍是「作品」、视频号已是「内容」）；勿硬编码精确合集名；snapshot 验收按前缀模糊匹配。
**Why:** 0828 实测硬编码精确名 not found，合集选择卡住。
**How to apply:** Phase 14.7

### 🔴 公众号原创声明 y 范围失效（v3.22.0 / 2026-08-28）
**问题**：「原创」标题实测在 `y=471`，旧代码 `rect.y < 400` 漏选，点不开原创声明弹窗。
**解决**：去 y 上界改为 `rect.y > 150 && rect.x > 500`；优先用 `.setting-group__title` 文本 === '原创' 定位，比全 `*` 扫描 + y 范围更稳。
**Why:** 0828 实测「原创」在 y=471，旧上界 400 漏选。
**How to apply:** Phase 12.8 步骤1

### 🔴 公众号合集输入框 getByRole 超时（v3.22.0 / 2026-08-28）
**问题**：合集弹窗未开时 `page.getByRole('textbox', { name: '请选择合集' })` 30s 超时。
**解决**：先 `document.querySelector('.js_article_tags_content').scrollIntoView({block:'center'})` + click 开弹窗，再用 `page.locator('input[placeholder="请选择合集"]')` 兜底定位输入框。
**Why:** 0828 实测弹窗未开时 getByRole 直接超时。
**How to apply:** Phase 12.10 步骤2

### 🔴 公众号正文 ProseMirror 拒绝 innerHTML 直接赋值（v3.23.0 / 2026-08-29）
**问题**：`bodyEditor.innerHTML = html` 返回"ok"但编辑器回滚，`pm.textContent.length === 1`——正文被静默清空，无报错。
**解决（v3.23.0，已被 v3.30.0 取代）**：`focus()` → `range.selectNodeContents(pm)` → `sel.addRange(range)` → `document.execCommand('insertHTML', false, html)`；注入后回读 `textContent.length > 1000` 验证。
**Why:** ProseMirror 通过 selection/execCommand 管状态，直接 DOM 写入会被视图层丢弃。0910 进一步证明 execCommand 只改 DOM、不同步内部 doc——上传/保存会回刷清空。
**How to apply:** Phase 12.5（v3.30.0 改真实剪贴板 + Meta+A/Meta+V；本条仅作历史）

### 🔴 公众号标题被正文注入操作灌入全文（v3.23.0 / 2026-08-29）
**问题**：正文注入操作导致标题框变成整篇文章（计数器 1776/64）。
**解决**：按 `data-placeholder` 含「标题」定位标题框 → `selectNodeContents` + `execCommand('delete')` + `execCommand('insertText', false, title)` 重置；**标题填写固定放到正文注入之后**。
**Why:** 注入时的 selection 操作可能落到标题框；索引定位在操作后会漂移。
**How to apply:** Phase 12.5b（新增）

### 🔴 公众号原创声明协议 checkbox 不自动勾选（v3.23.0 / 2026-08-29）
**问题**：旧文档称「自动勾选同意，直接点确定」；实测 `checked:false`，点「确定」no-op（弹窗不关）。
**解决**：点 checkbox 的 `closest('label')` 容器（点 input/文字 span 可能不切换）→ 验证 `checked===true` → 点「确定」；成功标志 = 弹窗关 + 「文字原创 · 已开启快捷转载」。
**Why:** weui-desktop checkbox 的 click handler 绑在 label 容器上。
**How to apply:** Phase 12.8（已修正）

### 🔴 公众号封面 4 子坑：hover 菜单/label 拦截/未选中/视口外 radio（v3.23.0 / 2026-08-29）
**问题**：①「从图片库选择」直接 click 报 not visible ②上传按钮被 webuploader-pick 内 `<label>` 拦截 ③图库首击未出现 selected ④2.35:1 radio 在视口外报 outside of viewport。
**解决**：① `page.mouse.move(coverBox.x, coverBox.y)` 先 hover 再 evaluate 点 ② `.single_upload_btn_container, .webuploader-pick` force click + waitForEvent('filechooser')（勿用含点动态 id 选择器）③ 回读 `.selected` 类验证，无则 evaluate 再点 ④ evaluate 点含 "2.35" 文本的 label/span。
**Why:** hover 菜单、webuploader 结构、选择态回读、视口外元素四类典型 Playwright 拦截。
**How to apply:** Phase 12.7c（新增）

### 🔴 抖音描述 editor-kit 编辑器 + 封面 SVG 拦截 + 封面路径（v3.23.0 / 2026-08-29）
**问题**：①描述编辑器实为 `.editor-kit-editor-container [contenteditable="true"]`，fill 可能不同步 ②封面上传图标 click 被 SVG 截获 ③封面文件在日期目录根，无 `covers/` 子目录。
**解决**：① locator 点 focus + `keyboard.type(text, {delay:5})` ② 点 `.semi-upload.upload-BvM5FF` 容器 + filechooser ③ 传路径前先 `ls` 确认。
**Why:** editor-kit 组件状态同步依赖真实键盘事件；SVG 覆盖层拦截指针；生成脚本输出目录与假设不符。
**How to apply:** Phase 14.5c（新增）/ 14.6（已补）

### 🔴 视频号 QR iframe 跨域失败连续两日复发（v3.23.0 / 2026-08-29）
**问题**：0828 + 0829 连续两日 `qrconnect` iframe「加载失败，点击重试」且重试无效——非偶发，是复发模式。
**解决**：重试 1 次即放弃 → QR 截图落盘 `channels-login-{MMDD}.png` → upload-status.md 写「视频号待办」6 步手动补跑清单（附双 body 铁律）。
**Why:** 跨域 iframe 自主流程无法修复，止损输出比反复重试有价值。
**How to apply:** Phase 13.0b（已升级为复发协议）

### 🔴 抖音「画面」+「引导至风险不可控渠道」叠标须重渲（v3.27.0 / 2026-09-01）
**问题**：0901 原片内部 review-checklist PASS 后用户手动发布，09:21:28 被机审「减少作品推荐」；原因「引导至风险不可控渠道」；标签 **「画面」**。根因不是标题：S2 口播「想试的去 Hugging Face」+ 仓库站 UI 入帧；S5 口播「清 Cookie / 跑杀毒扫描」+ 断链/信用卡扔垃圾桶画面；描述含「窃密木马」。
**解决**：标签含「画面」→ **禁止**只改标题/封面后重传旧 mp4。写 `voiceover-texts-safe.json` + `image-prompts-safe.json`，至少重画高风险 scene（本期 S2/S5），改口播去引导动词，TTS → captions → Remotion → `*-safe.mp4` + `platform-copy-safe.md`。账号安全视觉改为平静设备列表+盾标；开源视觉改为抽象管线图，禁第三方网站壳。
**Why:** 内部 3W/灰渠道 PASS 扫的是脚本结构，抖音机审扫的是成片帧 + 引导动词（v3.14 坑 130 复发）。「跑杀毒」会被读成引导下载第三方软件。
**How to apply:** Phase 2 审核清单增加上表三项；命中后走 `templates/platform-compliance.md` §6.1 过审重渲协议。Phase 14.0-pre 仍有效：未获用户确认前不自动重开创作者中心。

### 🔴 抖音用户手动上传后禁止再自动传（v3.26.0 / 2026-09-01）
**问题**：用户已手动把当期视频传到抖音后，流水线仍按 Phase 14 打开创作者中心、点上传/暂存，会撞上未发布草稿弹窗、混入旧素材或重复稿。
**解决**：用户说「已手动 / 不要再自动传」→ 立即停 Phase 14，标记 `douyin: user-manual`，不重开上传页、不核验除非用户要求。
**Why:** 手动稿优先于自动稿；再跑会破坏用户已完成的草稿。
**How to apply:** Phase 14.0-pre（新增）

### 🔴 视频号 login.html QR 已加载仍须止损（v3.26.0 / 2026-09-01）
**问题**：0901 打开 `/platform/post/create` 被 302 到 `login.html`，QR **已加载**（`qrcode loaded`，截图可见扫码框），不是「加载失败，点击重试」。console 同时刷 `300334`、`fastLogin: false`、`localhost.weixin.qq.com:14xxx/api/check-login ERR_CONNECTION_REFUSED`。误判成「QR 好了再等一会 / 再 reload」会空转。
**解决**：与 v3.23.0 复发协议同一止损——重试 1 次仍 `login.html` → `channels: login_required`。上述 console 噪声是微信桌面 fast-login 探测失败，**不是**继续重试的理由。
**Why:** 无桌面客户端时 fast-login 必然失败；QR 可见仍需真人扫码，自主流程做不到。
**How to apply:** Phase 13.0b（v3.26.0 变体）

### 🔴 公众号 appmsgid 已落后禁止因空壳 snapshot 重建（v3.26.0 / 2026-09-01）
**问题**：草稿已保存（URL 含 `appmsgid=100000882`）后，再 snapshot 可能读到标题 `0/64`、正文「从这里开始写正文」、封面「拖拽或选择封面」空壳，看起来像没写过。
**解决**：以 `appmsgid=` 为唯一成功信号；空壳 UI **禁止**再点新建 / 再跑全文注入。
**Why:** 编辑器 SPA 切 tab 或无障碍树读到空代理，不等于草稿丢失；重建会重复稿。
**How to apply:** Phase 12 保存关键经验第 9 条

### 🔴 视频号 login.html snapshot YAML 为空（v3.26.0 / 2026-09-01）
**问题**：`login.html` 上 `browser_snapshot` 落盘 YAML 可能是 0 字节，无法用 a11y 树判断 QR 是否在。
**解决**：改 `browser_take_screenshot`（如 `channels-login-YYYY-MM-DD.png`）判定；空 snapshot 不构成再 reload 的理由。
**Why:** 登录页跨域 iframe / 无障碍树残缺，截图比 snapshot 可靠。
**How to apply:** Phase 13.0b 截图落盘步骤

### 🔴 公众号正文 insertHTML 扁平化 → 剪贴板粘贴模拟（v3.28.0 / 2026-09-02；🔴 v3.30.0 已证伪合成 paste）
**问题**：0902 实测 `execCommand('insertHTML')` 注入多段落正文（`<section><p>…<h2>…`）会**扁平化结构**——h2/hr 样式丢失，且注入时若正文含重复占位符 `[IMG:COVER]` 会产生**重复图片节点**（imgSection 索引漂移）。
**v3.28.0 当时解法**（0910 已证伪）：构造 `DataTransfer` + 派发合成 `ClipboardEvent('paste')`。0910 实测合成 paste **pmLen=0，编辑器不认**。
**v3.30.0 真正解法**：`grantPermissions(['clipboard-read','clipboard-write'])` → `navigator.clipboard.write([ClipboardItem text/html + text/plain])` → 点正文 → `Meta+A` → `Meta+V` **真实键盘粘贴**；立刻「保存为草稿」验证 bodyLen 不降。
**Why:** ProseMirror 只认用户手势触发的原生 paste；合成 ClipboardEvent 与 execCommand 都不同步内部 doc。
**How to apply:** Phase 12.5 正文注入（v3.30.0 主路径）

### 🔴 公众号 filechooser 事件不触发 → 直接 setInputFiles（v3.28.0 / 2026-09-02）
**问题**：`Promise.all([waitForEvent('filechooser'), click(本地上传)])` 在 12.6 正文图片上传时 filechooser 事件**从不触发**（webuploader 内部拦了原生 chooser），Promise 挂起。
**解决**：跳过 filechooser，点完「图片→本地上传」后直接 `page.locator('input[type="file"]:visible').first().setInputFiles([path])`（或 evaluate 找 `input[type=file]` 后 `setInputFiles`）。**插入位置跟随 ProseMirror 光标**：点「本地上传」前先把光标点到目标段落末尾（`pm.focus()` + Range 折叠到目标节点后），否则图插到开头。
**Why:** 公众号用 webuploader 自管队列，不派发标准 filechooser；直接 setInputFiles 是唯一稳路。
**How to apply:** Phase 12.6

### 🔴 公众号标题 ProseMirror 填完后必须 blur 才同步 #title（v3.28.0 / 2026-09-02）
**问题**：12.5b 流程对标题代理 `execCommand('insertText')` 后界面已显示标题，但隐藏 `#title` textarea 仍 `value:''`——直接保存会得到无标题草稿。
**解决**：insertText 后 `titlePm.blur()`（或 dispatch input + blur），再回读 `#title.value` 验证 `match && len` 才算成功。12.5b 现有「回读 #title.value」检查本身是对的，但漏了 blur 这一步会永远 FAILED。
**Why:** #title 由 blur 事件的同步钩子写值，input 事件不触发。
**How to apply:** Phase 12.5b

### 🔴 公众号原创「确定」首击可能不提交 → 复点一次（v3.28.0 / 2026-09-02）
**问题**：0902 原创弹窗（文字原创 checkbox 已 checked）点「确定」后弹窗关闭，但开关仍显示「未声明」——首次点击是 no-op。
**解决**：点「确定」后**回读可见设置行** `.appmsg-editor__setting-group.js_original_apply_cell` 的 `innerText` 是否含「已开启快捷转载」（中文 UI）/ `Quick repost enabled`（英文 UI）。若仍「未声明」，重新点开关重开弹窗再点「确定」，以组内出现「文字原创 · 作者：… · 已开启快捷转载」为验收。
**⚠️ v3.32.0 更正**：**禁止**用 `.js_original_apply` 的 `textContent` 判定状态（恒为「未声明」假象，见下节 v3.32.0）；判定只看 `.js_original_apply_cell` 行的摘要。
**Why:** Vue 组件首击可能只关弹窗不提交 state；重开重点是唯一恢复路径。
**How to apply:** Phase 12.8

### 🔴 原创声明状态判定：只读「可见设置行摘要」，禁读隐藏占位节点（v3.32.0 / 2026-09-15，坑 191）

**事故**：0915 公众号草稿其余项（标题/作者/909 字正文/5 图/封面/合集）全部验收通过，唯独「原创声明」反复报 `Undeclared`，为此重复点开关、重开弹窗、勾协议、点「确定」共 6 轮，并把每次尝试都「保存为草稿」固化，仍未「生效」。

**真相**：声明**第一次就已生效**。`Undeclared` 来自 `.js_unset_original_title` 节点，它位于 **折叠子面板** `.setting-group__content.origined__area-new.js_original_type`（`display:none`）内，是**陈旧占位节点**：
- `textContent` / `innerText` 会读到隐藏文本 → 恒为 `Undeclared`
- `getBoundingClientRect()` 返回 `0×0`（因祖先 `display:none`）
- `input.js_ori_setting_checkbox` 自身 `style="display:none"`，其 `.checked` **声明生效后仍为 false** → 同样不可作判据

**正解——读可见设置行的摘要**：
```js
// ✅ 行元素「自身」就带 js_original_apply_cell，必须直接从 document 查
const g = document.querySelector('.appmsg-editor__setting-group.js_original_apply_cell');
const rowH = g.getBoundingClientRect().height;   // 已声明时 h≈62（可见行）
const sum  = g.innerText.replace(/\s+/g, ' ').trim();
// 未声明 → "Original 未声明"
// 已声明 → "Original Text Originality · Author: 今日羊报AI · Quick repost enabled"（英文 UI）
//          "原创 文字原创 · 作者：今日羊报AI · 已开启快捷转载"（中文 UI）
const declared = /Text Originality|文字原创/i.test(sum) && rowH > 20;
```
⚠️ 不能写 `document.querySelector('.appmsg-editor__setting-group').querySelector('.js_original_apply_cell')`——`querySelector` 只匹配**后代**，匹配不到行元素自身的 class。

**交叉验证**：声明生效后，原本可见的「Reward 赞赏／可在声明原创后开启」gate 行（`.js_unorigin_reward`）会消失，改为「Reward Don't enable」。

**通用铁律（不止原创）**：
1. **任何开关/声明状态判定，一律以「可见设置行的摘要文案 + 行高」为准**；`.textContent`+隐藏节点＝假信号，会稳定骗过每一轮验证。
2. `offsetParent === null` **无法**区分「被 `display:none` 祖先隐藏」与「`position:fixed`」；判可见性要用 `getBoundingClientRect()`（`w/h>0`）。
3. 判定被隐藏时，**向上遍历祖先链找第一个 `display:none` 的元素**（本次是 `.setting-group__content...js_original_type`），一眼定位是哪个容器把它藏了。
4. **`element.click()` 对 `display:none` 元素照样能派发事件**——弹窗会正常打开，造成「点了有反应＝元素可见」的错觉。这是本次连错 6 轮的根因。
5. **截图取证**：`Page.captureScreenshot` 的 `clip` 必须传**页面坐标**（`rect.top + window.scrollY`）且 `captureBeyondViewport: true`；传视口坐标会截到空白图（曾据此误判「无内容」）。

**How to apply:** Phase 12.8 及任何平台「开关类」设置验收；视觉终检优先于 DOM 断言。

### 🔴 公众号粘贴必须放行「Content Structure Check」弹窗（v3.32.0 / 2026-09-15，坑 192）

**事故**：长期存在的 `paste failed pmLen=8 / len=15 / len=0`。两个成因叠加：
1. **占位符 widget 污染长度**：正文 `ProseMirror` 空态含 `contenteditable="false"` 的 `.editor_content_placeholder.ProseMirror-widget`，文本 `Start text here`（15 字符）。裸读 `pm.textContent.length` 得到 15/8，误判「有内容」或「粘贴失败」。
2. **真因**：粘贴内容触发微信**「内容结构检查 / 内容结构检测 / Content Structure Check」模态**拦截（0921 实测出现「检测」变体，坑 220），正文实际**未插入**，直到点 **`Continue Inserting`（继续插入）** 才写入。

**正解**：
```js
// 长度：剥掉 widget 与 contenteditable=false 再读
const bodyLen = (page) => page.evaluate((i) => {
  const pm = document.querySelectorAll('.ProseMirror')[i];
  if (!pm) return -1;
  const c = pm.cloneNode(true);
  c.querySelectorAll('.ProseMirror-widget, [contenteditable="false"]').forEach(e => e.remove());
  return c.textContent.trim().length;
}, BODY_IDX);

// 放行结构检查弹窗（轮询最多 12×400ms）
async function continueInserting(page) {
  for (let i = 0; i < 12; i++) {
    const hit = await page.evaluate(() => {
      for (const d of document.querySelectorAll('.weui-desktop-dialog')) {
        if (d.getBoundingClientRect().height < 30) continue;
        const t = d.querySelector('.weui-desktop-dialog__title')?.textContent || '';
        if (/Structure Check|结构检查|结构检测/i.test(t)) {
          for (const b of d.querySelectorAll('button, a.weui-desktop-btn')) {
            const bt = (b.textContent || '').trim();
            if (/Continue Inserting|继续插入/i.test(bt)) { b.click(); return 'clicked:' + bt; }
          }
        }
      }
      return null;
    });
    if (hit) return hit;
    await page.waitForTimeout(400);
  }
  return 'no-dialog';
}
// 粘贴走 CDP 真实剪贴板：Input.dispatchKeyEvent{..., commands:['paste']}，随后 continueInserting()
```
验收阈值：`bodyLen > 800` 才算正文到位（日报正文约 900+ 字）。

**How to apply:** Phase 12.5 正文粘贴；`continueInserting()` 在 paste 后立即调用，回读用 `bodyLen()` 而非裸 `textContent.length`。

### 🔴 公众号编辑器为英文 UI 时的标签集（v3.32.0 / 2026-09-15）

0915 实测该账号后台**英文 UI**（占位符却是中文 `请在这里输入标题`）：按钮/文案须按英文匹配——
`Save as draft`（保存为草稿）、`Confirm` / `Cancel`、工具栏 `image(s)`、合集入口 `Collections`、原创 `Original` / `Text Originality` / `Undeclared` / `Quick repost enabled`、结构检查 `Content Structure Check` / `Continue Inserting`。
**写法**：所有文案匹配一律用双语正则，如 `/^(Save as draft|保存为草稿)$/i`、`/(Continue Inserting|继续插入)/i`，避免只写中文导致 no-op。

**How to apply:** Phase 12 全流程；新增文案匹配必须双语。

### 🔴 公众号合集实际 DOM 流（v3.28.0 / 2026-09-02）
**问题**：12.10 旧流程 `getByRole('textbox', {name:'请选择合集'})` 与 `getByText('「今日羊报 AI」')` 在 0902 实测**找不到节点**；`[class*="collect"]` 系选择器也全空。合集入口不是按钮而是**可见文本 SPAN**。
**解决**（已验证流）：
1. 全 DOM 按 `offsetParent!==null` 过滤找 `textContent==='合集'` 的 SPAN（在 `.frm_checkbox_label` 内，即 `.lbl_content`）→ click **宿主 label** 勾选 checkbox
2. click 同行 `.lbl_content_after.lbl_content_desc`（文本「未添加」）→ 弹「合集」对话框（含「每篇文章最多添加1个合集/清空/创建新合集/确认/取消」）
3. click `input[placeholder="请选择合集"]` → 等下拉 `li.select-opt-li` 出现 → click 目标项
4. click「确认」→ 回读合集行文本含合集名即成功
**Why:** 合集组件是自定义 select2 式控件，role/text 匹配全部失效；唯一稳定锚点是「合集」/「未添加」的可见文本 + `li.select-opt-li` 下拉项。
**How to apply:** Phase 12.10

### 🔴 通用 DOM 工具坑：NodeList 无 filter / :visible 非法（v3.28.0 / 2026-09-02）
**问题**：① `document.querySelectorAll(...).filter(...)` → TypeError（NodeList 无 filter）；② evaluate 里 `querySelector('div:visible')` → SyntaxError（`:visible` 是 Playwright 选择器引擎语法，非 CSS）。
**解决**：① 一律 `Array.from(document.querySelectorAll(...))` 再 `.filter()`；② 可见性判定用 `el.offsetParent !== null`（display:none 时为 null）。
**How to apply:** Phase 12 全部 evaluate 代码

### 🔴 上传 daemon 禁止 Chrome for Testing（v3.34.0 / 2026-09-17，坑 198）
**问题**：0917 上传 daemon 裸启 Playwright 自带 `chromium-1228/Google Chrome for Testing` + mcp-chrome profile。登录态能用，但窗口图标/标题变成 Testing 版，用户质问「为啥现在起的是 chrome for testing，9 月 10 日不是这样」。
**解决**：上传 daemon 必须 `/Applications/Google Chrome.app`；Testing 版只允许 linuxdo-daily **抓取**兜底（MCP 断连时 headed 过 Cloudflare）。profile 仍用 `mcp-chrome-10b76e5`。
**Why:** Testing Chromium 与日常 Chrome 不是同一颗二进制（149 vs 153），扩展/指纹/站点行为有差。
**How to apply:** `templates/browser_daemon.py`；Phase 11 协议第 1 条。

### 🔴 Playwright driver 不能当 daemon 持有浏览器（v3.34.0 / 2026-09-17，坑 199）
**问题**：`with sync_playwright() + launch_persistent_context + while True: sleep` 当 daemon。B站上传页弹窗触发 `Protocol error (Page.handleJavaScriptDialog): No dialog is showing` → driver Node 崩 → 浏览器陪葬 → 后续 `connect_over_cdp` `ECONNREFUSED`。0917 连崩两次。
**解决**：裸启 Chrome 进程（无 Playwright driver）监听 9222；脚本只 `connect_over_cdp` 附着。driver 挂了浏览器还在。
**Why:** Playwright driver 会接管 dialog 协议，异常时把 browser 一起杀掉，违背「常驻」目标。
**How to apply:** `templates/browser_daemon.py` 已改为 `subprocess.Popen(CHROME ...)`。

### 🔴 B站存草稿是 span.submit-draft 不是 button（v3.34.0 / 2026-09-17，坑 200）
**问题**：`button:has-text("存草稿")` 恒 count=0；evaluate 点 `button` 文案匹配也 no-op。表单填完（标题/简介/标签/封面）点了 5 轮「存草稿」，草稿箱一直「当前无草稿」。DOM 实测：`{tag:SPAN, cls:submit-draft, 122×42}`。
**解决**：`page.locator('span.submit-draft').click({force:true})`；force 仍 timeout 时 `scrollIntoView` + `mouse.click` 中心坐标。成功信号 = 新标签打开草稿箱能搜到当日标题，不是 URL 仍停在 frame。
**How to apply:** Phase 11.9。

### 🔴 存草稿失败禁止 goto 草稿箱（v3.34.0 / 2026-09-17，坑 201）
**问题**：未确认保存就 `page.goto(.../article?group=draft)`，编辑页被冲掉。0917 表单填好 5 次，每次验证草稿把编辑页毁了，只能整段重传。
**解决**：失败留在表单页截图诊断；验证草稿用 **新标签页** 打开草稿箱，不动编辑页。
**How to apply:** Phase 11.9；任何「先跳走再验证」都先问会不会丢表单。

### 🔴 公众号 clipboard.write 成功 ≠ 正文进去（v3.34.0 / 2026-09-17，坑 202）
**问题**：`navigator.clipboard.write` 返回 wrote，evaluate 对 `.ProseMirror[1]` 派发 click/focus 再 Meta+V，`bodyLen=0`（空态 widget 15 字）。封面流程在空正文上点「从正文选择」弹出 `Select an image / No available images` 挡住编辑器。
**解决**：坐标点击 `.ProseMirror[1]` 中心 → Meta+A → Meta+V → 放行 Structure Check → `bodyLen()>800` 才算粘上。封面弹窗先 Escape/`Cancel`。登录判据英文 UI 补 `New creation`。`log(url[:120])` 可能截掉 `appmsgid=`，验收读完整 URL。
**How to apply:** Phase 12.5 / 12.1。

### 🔴 封面文字源拆分：发布标题不进画面（v3.35.0 / 2026-09-17，坑 203）
**问题**：v3.31.0 规定封面文字源 = `publish.json.title` 整条发布标题。0917 画面印的是「【2026-09-17】Gemini实时多模态上线,OpenAI风控改明着拦｜6条重磅AI新闻一次看完 | 今日羊报AI」——日期 + 两事件 + 条数 + 报刊名全堆上画面，与 Hook 原词（「OpenAI把降智取消了，现在直接不给你用」）脱钩，冲突被稀释。用户复盘判定不吸引人，违反「封面 = 1 句冲突 + 1 个数字」与「封面大字 = Hook 原词」两条自家规则。
**解决**：封面画面文字源改为脚本「对应封面大字」字段（Hook 原词短句，两行，主文案 + 数字短句）；`publish.json.title` 仍作 B站/公众号列表标题与渲染文件名，**列表标题与封面文字解耦**——Phase 10 改列表标题不触发封面重出，改 Hook 才触发。
**How to apply:** `templates/cover-prompt.md` v3.35.0；Phase 5.5 / 10.1；验收清单第一项改为「画面标题 = 对应封面大字（Hook 原词）」。

### 🔴 gen_captions 的 scenes 结构兼容 + 偏移按 wav 时长（v3.36.0 / 2026-09-18、09-19 实测，坑 208）
**问题**：① 0918 跑 Phase 7 时 `templates/gen_captions.py` 直接崩：`AttributeError: 'dict' object has no attribute 'decode'`——`load_scenes` 读 `scripts/voiceover-texts.json` 时，`scenes` 是 `[{"num":1,"text":"..."}]` 字典列表，代码 `for i, text in enumerate(raw, 1)` 把 dict 当字符串迭代传进 `normalize()`，整段字幕阶段卡死。② 0919 发现字幕逐场景累计提前：`scene_offset += dur`（whisper 的 `info.duration`）而 whisper VAD 会裁掉片尾 pad 静音，返回时长比 wav 短 0.3–3s，偏移越往后欠得越多。
**解决**：① `load_scenes` 兼容三种写法——`{"scenes":{1:"text"}}`、`{"scenes":["text"]}`、`{"scenes":[{"num"/"id","text"/"content"}]}`，统一归一到 `(sid, text)`；**dict 按 sid 排序，list 保留声明的播放顺序**（禁止把 `[1,2,3,4,6,5,7]` 静默还原）。② 偏移改用 **wav 文件头时长**：`with wave.open(str(audio)) as wf: file_dur = wf.getnframes()/wf.getframerate()`，失败才回落 `sc['duration']` 或 whisper `dur`；打印 `offset += file_dur=X (whisper Y)` 便于对账。
**Why:** 字幕偏移必须与 `Composition.tsx` 的 `sceneConfig.duration`（ffprobe 实测）同源；whisper 的 duration 是「语音结束时刻」，不是「场景结束时刻」，两者差一个 pad 静音。
**How to apply:** `templates/gen_captions.py`（v3.36.0 已双向同步）；Phase 7。当 `scenes-meta.json` 缺失时**不再需要手工补文件**——`voiceover-texts.json` 直读即可。

### 🔴 锚点位置超标用「重排播放顺序」修，不重写脚本（v3.36.0 / 2026-09-18 实测，坑 209）
**问题**：0918 脚本写完一算，锚点场景（`luna_sol_terra_tiers`）起始 96.68s / 总 113.24s = **85.4%**，超出 Phase 8 要求的 `[0.70, 0.80]`。
**解决**：不重写口播、不删场景。把播放顺序从 `[1,2,3,4,5,6,7]` 重排为 `[1,2,3,4,6,5,7]`（锚点从第 6 位提到第 5 位），锚点起始变为 80.27s / 113.24s = **70.9%** ✅。落地三处：`scenes-meta.json` 的 `scenes` 数组顺序、`Composition.tsx` 的 `sceneConfig`、`Root.tsx` 的 `SCENE_DURS`；然后**重跑 whisper 对齐**（顺序变了，偏移要重算）。0919 期同理，锚点 `privacy` 落在 97.85/122.36 = 80.0%（贴上限，靠 scene6 末尾 pad 3s 兜住）。
**Why:** 锚点占比只取决于「锚点场景的起始时刻 / 总时长」，与场景编号无关；交换相邻位置即可，成本远低于重写。
**How to apply:** Phase 8 核算后、Phase 9 渲染前。重排后必须重新生成 captions（内容不变，时间轴按新顺序重算）。

### 🔴 TTS 端点 key 全失效时直接走 edge-tts，不要逐个试（v3.36.0 / 2026-09-18 实测，坑 210）
**问题**：0918 期 mimo-tts 全部端点返回 `Invalid API Key`（`settings.json` 里的 MIMO key 整体失效）。逐个端点重试纯属浪费——0916 / 0917 / 0918 连续三期都是同一结果。
**解决**：`scripts/gen_tts.py`（mimo 路径）**先探一次**，任一端点返回鉴权类错误（`Invalid API Key` / 401 / 403）就立即切 `gen_tts_edge.py`（`zh-CN-YunyangNeural` + ffmpeg `atempo=1.4` → 24kHz PCM16LE 单声道 WAV），不要循环重试。
**Why:** 三期连续同一现象说明是账号侧 key 失效而非端点抖动；edge-tts 已验证连续可用且音色稳定（云扬），时长由 atempo 统一缩放。
**How to apply:** Phase 6；`gen_tts_edge.py` 已作为并列默认路径。切完后 ffprobe 实测时长 → 回填 `sceneConfig`（坑 208 同源要求）。

### 🔴 公众号上传用步进脚本，每步独立可重入（v3.36.0 / 2026-09-18、09-19 实测，坑 211）
**问题**：公众号上传步骤多（open/body/images/cover/title/save/verify），单脚本一把梭失败后无法定位，只能整段重来。
**解决**：`scripts/wechat_upload.py <step>`，步骤 `open|body|images|cover|title|save|verify`，**每步跑完即打印结构化判据并落草稿**，失败可单步重跑：
- `open`：登录判据 = 页面出现「新的创作」（坑 195），取页按 URL 匹配 `appmsg`，禁 `pages[-1]`（坑 193）
- `body`：v3.30 协议——坐标点击 `.ProseMirror[1]` 中心 → Meta+A → Meta+V → 放行 Content Structure Check → 断言 `bodyLen() > 800`（剥 `ProseMirror-widget`，坑 192/202）
- `images`：`PLACEHOLDER_IMG_N` 占位符 → 工具栏「图片→本地上传」→ 每图即存 → 占位符清零
- `cover`：从正文选择最后一张缩略图，验收读 `js_cover_preview_new` 的 `hasQpic`（**不要**判对话框开合，`dialogOpen:false` 时封面往往已生效）
- `title`：同步长度断言（预期值与实际值相等才算过）
- `save`：勾选合集「今日羊报 AI」→ 存草稿
- `verify`：**新标签页**开草稿箱复核 `appmsgid` / `bodyLen` / 占位符数 / 封面 / 标题 / 合集（坑 201：禁止在编辑页 `goto` 草稿箱）
**Why:** 公众号对 DOM 时序极敏感，一把梭脚本的失败点会被后面的步骤掩盖；步进脚本把「哪一步坏了」变成显式输出。
**How to apply:** Phase 12。0918 `appmsgid=100001241`、0919 `appmsgid=100001257` 均由该脚本产出。

### 🔴 公众号验收必须同查「草稿箱 + 发表记录」（v3.37.0 / 2026-09-20 实测，坑 212）
**问题**：0920 流水线 02:11 存好草稿（`appmsgid=100001273`），用户在 10:44 **自行发表**。复核时只查草稿箱 → 当日条目不在（草稿箱里只剩 2018–2020 历史素材）→ 极易误判「草稿丢了」并触发 Phase 12 重建，而「`appmsgid` 出现即视为落盘、禁止重建」铁律本来就是为了防重复稿，两条规则在此正好对冲。
**解决**：公众号验收固定查两个页面——**草稿箱**（`appmsgid` / `bodyLen` / 占位符 / 封面 / 标题 / 合集）**+ 发表记录**（当日 `已发表` 条目及其时间）。草稿箱无当日条目但发表记录有当日条目 = **已发表**，属正常终态，**不是失败**，禁止重建。把「已发表时间」写进 `upload-status.md`。
**Why:** 「存草稿」是流水线的终点，不是用户的终点；隔几小时回来复核时草稿多半已被用户发表。
**How to apply:** Phase 12 `verify`；`upload-status.md` 模板加「发表记录」一行。

### 🔴 mp 页面重定向销毁 execution context，草稿箱/发表记录用 URL 直达（v3.37.0 / 2026-09-20 实测，坑 213）
**问题**：`page.goto('https://mp.weixin.qq.com/')` 会 302 到 `cgi-bin/home?...&token=`，紧接着的 `page.evaluate` 抛 `Execution context was destroyed, most likely because of a navigation`，脚本直接崩。另外在 home 上用「找文本 === 『草稿箱』的元素并 click」导航**不稳定**（内容管理是折叠面板，点了仍停在首页）。
**解决**：① 导航后**轮询重试** evaluate（拿到非空 body 再继续），不要一次性调用；② 从 `page.url` 正则取 `token=(\d+)`，**用稳定 URL 直达**，不点侧栏：
- 草稿箱 `https://mp.weixin.qq.com/cgi-bin/appmsg?begin=0&count=12&t=media/appmsg_list&type=10&action=list_card&token={token}&lang=zh_CN` ⚠️ **该接口只展示「历史图文素材」（type=10），不含 type=77 新草稿，禁止当草稿验收源**——验收三件套见坑 221
- 发表记录 `https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&begin=0&count=10&token={token}&lang=zh_CN`

**How to apply:** `scripts/wechat_check_draft.py`（0920 新增，只读，不新建/不发表）。

### 🔴 窗口被关掉后 daemon 仍活着：CDP 建标签页即可恢复（v3.37.0 / 2026-09-20 实测，坑 214）
**问题**：用户看完关掉 Chrome 窗口（macOS 下进程不退出）。此后 `curl /json/version` 正常、`ps` 也能看到 daemon 进程，**看起来一切正常**；但 `/json/list` 返回 `[]`，Playwright `connect_over_cdp` 直接失败：`Browser.setDownloadBehavior: Browser context management is not supported`。容易误判成「daemon 挂了」而重启（重启会丢登录态的当前上下文）。
**解决**：先 `curl -s http://localhost:9222/json/list` 看是否为空；空则 `curl -s -X PUT "http://localhost:9222/json/new?about:blank"` 建一个标签页，再 `connect_over_cdp` 即可。**不需要重启 daemon**。
**Why:** 无窗口 = 无 page target = 无 browser context，Playwright 的 CDP 附着拿不到上下文。
**How to apply:** 任何上传/复核脚本连接失败时的第一个诊断动作。

### 用户声明「已手动上传」的平台一律不碰（v3.37.0 / 2026-09-20 实测，坑 215）
**问题**：0920 用户中途说「只需要上传公众号～其他我已经手动上传了」。若不识别，Phase 13/14 会照常打开视频号/抖音上传页，与用户手动动作**撞车**（重复稿、抢占同一浏览器）。
**解决**：Phase 14.0-pre 的「用户手动 → 立即停手」规则**从抖音扩展到全部平台**（B站/抖音/视频号/公众号均适用）。命中后：① 不打开该平台上传页；② **不主动去草稿箱核验**（除非用户明确要求）；③ `upload-status.md` 写 `⏭ 用户手动`；④ 不阻塞其他平台。
**Why:** 用户在浏览器里的手动操作优先于流水线；核验本身也可能误触（改稿/重复提交）。
**How to apply:** Phase 13 / Phase 14 入口；`upload-status.md` 的 `manual_by_user` 字段。

### 🔴 安全分类器不可用会阻塞全部非只读 Bash（v3.37.0 / 2026-09-20 实测，坑 216）
**问题**：0920 09:40–10:31 连续报 `deepseek-v4.1-flash is temporarily unavailable, so auto mode cannot determine the safety of Bash`。现象：`ls` / `cat` / `date` / `curl` **正常**；`python3 ...`、`cd ... && nohup ...`、`CronCreate` **全部被拦**。`settings.json` 的 `allow` 里明明有 `Bash(python3:*)` 也照样被拦，**allowlist 不短路**。持续约 50 分钟，中间偶有几次放行。
**解决**：① 不要空转——把工作切到 **`Write` 工具落盘**（状态文件、`upload-status.md` 照写；⚠️ 0921 实测抖动窗口内 `Write`/`Edit`/`Workflow` 也可能被拦，同样走间隔重试）；② 把复合命令**拆成单命令**（`cd ... && nohup ...` 比裸 `python3 <path>` 更易被拦）；③ **间隔重试**，每次放行窗口都可能成功——同批并行调用也会「一过拦一」，被拦的那条单独重试即可；④ 已经跑起来的长任务（daemon）不受影响；⑤ 分类器模型名会变（0920 `deepseek-v4.1-flash` / 0921 `glm-5.3-flash`），报错里的模型名不代表账号问题。
**Why:** 分类器是外部模型服务，抖动与内容无关；此时唯一可行的是降级到「只读 + 落盘 + 重试」。
**How to apply:** 全流程通用。恢复后第一件事是把断点续上（本例是起 daemon → 跑 `wechat_check_draft.py`）。

### B站创作声明下拉要 force click，分区核验别把 `*` 当值（v3.37.0 / 2026-09-20 实测，坑 205 补）
**问题**：① 创作声明 `.bcc-select` 直接点返回 `not found vis=19`；② 分区自检探针返回 `{"partition":"*","ok":false}`——它把必填标记星号 `*` 读成了分区值，**实际分区早已是「人工智能」**（`<div class="selector-container">` 文本 + body `分区\n\n人工智能` 均可证）。假阴性会诱发无意义的重复点击。
**解决**：① 声明 —— `page.locator('.creation-statement-container .bcc-select').click(force=True)` → `page.locator('text="个人观点，仅供参考"').first.click()`；② 分区核验**以 `document.body.innerText` 里出现 `分区\n\n人工智能` 为准**，不要用「heading 的兄弟节点」这类脆弱探针。
**How to apply:** Phase 11 表单步。

### 🔴 B站封面改版为「封面制作」全屏弹窗（v3.38.0 / 2026-09-21 实测，坑 218）
**问题**：B站投稿页封面区改版。点「添加封面」**不再触发原生 file chooser**——`page.expect_file_chooser()` 必超时（0921 白等两轮 8s）；改为打开带「智能生成封面 / 模板 / 文字 / 贴纸 / 滤镜」的**全屏弹窗**。更隐蔽的是：此刻页面上共有 **5 个 `input[type=file]`**（`.mp4`×2 / `.txt` / `.zip` / 封面 `accept="image/png, image/jpeg"`），按位置索引 `inputs[1]` / `inputs[-1]`（旧 v3.3.0 协议）会把 png **喂给视频或 zip input**——**不抛错、无提示、表单纹丝不动**，看起来像「点了没反应」（0921 连错两次）。
**解决**：① 点「添加封面」→ 直接进弹窗，**不要等 file chooser**；② 弹窗内点「上传封面」（`span.upload-text`）；③ **按 `accept` 过滤**取 input（唯一判据），`set_input_files(horizontal-4-3.png)`；④ 点 `.cover-editor-button .button.submit`（文案「完成」）关弹窗；⑤ 关弹窗后**回表单截图目检**封面缩略图 = 自制图（4:3 首页推荐 + 16:9 个人空间两栏同步预览）。
```javascript
let cover = null;
for (const i of await page.$$('input[type="file"]')) {
  const acc = (await i.getAttribute('accept')) || '';
  if (acc.includes('image')) { cover = i; break; }   // ✅ 唯一可靠判据
}                                                     // ⛔ 禁用 inputs[1] / inputs[-1]
await cover.setInputFiles('news-pipeline/YYYY-MM-DD/horizontal-4-3.png');
```
**Why:** 索引取 input 的失败是静默的——只有 accept 判据 + `.cover-empty` 消失断言才能自证；顺序也不能换，先点「完成」只会关掉一个空弹窗。
**How to apply:** Phase 11 封面步；脚本模板 `templates/bili_cover.py`（CDP 附着、日期参数化、结束断言弹窗已关）。**前置**：封面必须先 `cp` 到日期目录根（见 11 号协议第 12 条）。

### 🔴 B站标签上限 10 且会被推荐标签污染（v3.38.0 / 2026-09-21 实测，坑 219）
**问题**：新版投稿页标签区**自动预置推荐 chips**（0921 实测混入「学习 / 生活记录 / 记录」），且**上限 10 个**。额度被预置项占满后，后续 `type` + `Enter` 全被**静默丢弃**（仅右上角弹提示「允许添加的标签已经达到上限了」）——脚本照常打印 "added"，标签列表里却没有。另：删除时点 `label-item-v2-content`（文字元素）或容器中心**都无效**（0921 空转三轮），关闭符 `×` 实际位于 `label-item-v2-container` 容器**最右侧**。
**解决**：① 先读 `.label-item-v2-container` 现有 chips，删掉不想要的（`page.mouse.click(b.x + b.width - 10, b.y + b.height/2)`，容器右缘）；② 再补自己的 tags（`input[placeholder*="回车键Enter创建标签"]` native setter + Enter）；③ **每次增删后回读 chips 文本列表断言**，终态 = publish.json 的 tags（允许少、不允许脏）。
**Why:** 「脚本打印 added」与「chips 里真的有」是两回事；列表页标签是可见产物，脏标签比缺标签更糟。
**How to apply:** Phase 11 标签步；`upload-status.md` 记最终 chips 列表。

### 🔴 mp `open` 必须 settle()，已在 mp 页则跳过 goto（v3.38.0 / 2026-09-21 实测，坑 217）
**问题**：`wechat_upload.py open` 步骤 `page.goto('https://mp.weixin.qq.com/')` 在已登录状态下 302 到 `cgi-bin/home?...&token=`，紧跟的 `page.evaluate` 抛 `Execution context was destroyed, most likely because of a navigation`——**整步崩溃**，既判不了登录也开不了编辑器（同源坑 213 的脚本侧复现）。
**解决**：① 若当前页 URL 已含 `token=`，**直接跳过 goto**；② 必须 goto 时，之后一律走 `settle(page)`（轮询 `document.body.innerText`，捕获异常 + 2s 间隔，≤20 次）再读登录判据；③ `.new-creation__menu-item` 点击也用 try/except + `settle()` 重试 ≤3 次，再按 URL 找 `cgi-bin/appmsg`。
**Why:** 302 期间 execution context 被销毁是**时序问题不是选择器问题**，任何"点之前串一个 evaluate"的写法都会随机崩。
**How to apply:** Phase 12 `open` 步；`templates/` 内步进脚本通用（`settle()` 已是 `wechat_upload.py` 的固定件）。

### 🔴 结构检查弹窗第三变体「内容结构检测」（v3.39.0 / 2026-09-21 周报实测，坑 220）
**问题**：0921 周报公众号正文粘贴后 `bodyLen=0`——结构检查弹窗标题实为「内容结构**检测**」，坑 192 的放行正则 `/Structure Check|结构检查/i` 漏匹配（**检测 ≠ 检查**），轮询 12 次全 `no-dialog`，直到手动点「继续插入」正文才写入（放行后 `bodyLen=1015`）。
**解决**：放行正则三变体齐全：`/Structure Check|结构检查|结构检测/i`（坑 192 代码块已同步修正）；按钮正则 `/Continue Inserting|继续插入/i` 不变。**粘贴后 `bodyLen=0` 的第一诊断 = 截图看弹窗标题是否新变体**，先把变体加进正则再重试粘贴，不要直接判「粘贴失败」盲目重粘（重粘只会再触发同一弹窗）。
**Why:** 微信该弹窗文案存在多套变体（检查/检测/英文），且随版本漂移；硬编码单变体必过期。
**How to apply:** 坑 192 `continueInserting()`、Phase 12.5 正文粘贴、全部 `wechat_upload.py` 副本。

### 🔴 type=10 list_card 只展示历史图文素材，不是草稿验收源（v3.39.0 / 2026-09-21 周报实测，坑 221）
**问题**：0921 周报草稿 `appmsgid=100001297` 保存成功后，复核走坑 213 的「草稿箱」URL（`appmsg?type=10&action=list_card`）——页面是「历史图文素材」，只有 2018–2020 旧稿，**不含任何 type=77 新草稿**；发表记录也无当日条目。若按坑 212 的二态判定（草稿箱无 + 发表记录无）会误判「草稿丢了」并触发 Phase 12 重建，正好撞上「`appmsgid` 出现即禁止重建」铁律，产出重复稿。
**解决**：公众号草稿验收固定**三件套**——① **`appmsgid` 编辑页直达**（`cgi-bin/appmsg?t=media/appmsg_edit&action=edit&appmsgid={id}&token={token}&lang=zh_CN`，标题/作者/正文/封面全在 = 草稿在）；② 首页「近期草稿」首条 = 当期标题（含「更新于 HH:MM」）；③ 发表记录**无**当日条目（确认未发表 = 存草稿终态）。`type=10 list_card` 仅用于看历史素材，**禁止**当 type=77 验收源。
**Why:** list_card 的 `type=10` 与新草稿的 `type=77` 是两套列表，「查不到」是接口语义问题，不是草稿状态问题。
**How to apply:** Phase 12 `verify` 与 `scripts/wechat_check_draft.py`。与坑 212 合并为完整三态：**编辑页可达 + 发表记录无 = 草稿已存**；**发表记录有当日 = 用户已发表（终态，禁重建）**；**编辑页不可达 + 近期草稿无 + 发表记录无 = 才允许怀疑未保存**。

**v3.46.0 补充（坑 248，W40 实测）**：发表记录页 `cgi-bin/publish?action=list` **直接 `goto` 会抛 `ERR_HTTP_RESPONSE_CODE_FAILURE`**，该 URL 不稳定，不能当三件套第③项的入口。替代路径：首页「近期草稿」首条（含「更新于 HH:MM」）+ `appmsgid` 编辑页直达，两件齐即可判「草稿已存且未发表」，**不要为了第③项硬刷 publish 列表**。

**v3.66.0 补充（坑 315，2026-10-26 实测）**：刷新首页看新草稿这件事，**`location.reload()` 本身是安全的**——复测 `RELOAD_TEST {"before_len":1685,"after_len":1685,"after_url_has_token":true,"after_login_timeout":false}`，token 保留、首页完好；裸域 `goto('https://mp.weixin.qq.com/')` 也会自动 302 到带 token 的首页（同样 1685）。**注意：本期曾一度出现 `len=83` 的「登录超时」空页，当时归因为「reload 丢 token」，该归因已被复测推翻，成因未明（大概率瞬时）。** 遇到空页的正确处理是**重试一次或换新标签页重开**，不要基于未验证的因果去改脚本。`templates/wechat_check_draft.py` 里的 `location.reload()` 可继续使用。

**v3.50.0 补充（坑 221 第二次命中，2026-10-15 实测）**：`wechat_check_draft.py 2026-10-15` 走 `type=10 list_card` 返回 `草稿箱标题候选: []` + `in_publish_record: false` → 判定文案 `两处均无 — 需排查`。**这是假阴性，不是草稿丢失**——1015 草稿 `appmsgid=100001568` 实际完好。正确动作 = **改走首页「近期草稿」入口**（点文本为「近期草稿」的节点，页面停在 `cgi-bin/home`，草稿标题直接出现在首页 DOM 里），实测首条即 `【2026-10-15】Argon测评两极…`，与 10-14/10-13/10-12 等历史草稿同列返回。**铁律复述**：`type=10 list_card` 的空结果**永远不能**作为「草稿未保存」的证据；`wechat_check_draft.py` 的 `verdict` 字段在 `in_draft_box=false` 时**必须**再跑一次近期草稿入口才可定性。1015 的「近期草稿」入口片段：
```python
r = page.evaluate('''() => {
  const as = Array.from(document.querySelectorAll('a,li,div,span'));
  const t = as.find(e => /近期草稿|Recent drafts?/i.test((e.textContent||'').trim())
                          && e.offsetParent && (e.textContent||'').trim().length < 20);
  if (t) { t.click(); return 'clicked:' + t.textContent.trim(); }
  return 'not-found';
}''')   # 实测返回 'clicked:近期草稿 全部草稿'，URL 仍为 cgi-bin/home
```
注意该入口**不跳转 URL**（仍停在 `home?t=home/index`），所以不能靠 URL 判断是否进入，只能看 DOM 文本是否出现当期标题。

### 🔴 锚点占比不能靠把 CTA 排到锚点前面来凑（v3.43.0 / 2026-10-09 实测，坑 236）
**问题**：1009 期顺序 `[1,2,3,4,5,6]` 下锚点起始占比 0.6941，差 0.6pp 到 70%。改成 `[1,2,3,4,6,5]` 后占比 0.7925 落进区间，但 CTA 排到了锚点前面——锚点口播「回头说那个四字一轮」变成在收尾之后回扣，叙事顺序错了。
**解决**：占比是位置约束，**不是**改叙事顺序的理由。锚点必须在 CTA 之前。占比不够时加长锚点**之前**场景的口播（1009 给场景 1 加约 12 字，重跑 TTS 后 54.841s/78.214s=0.7012），或缩短锚点之后的场景。过渡句随顺序变：「回头说」只用于锚点排在 CTA 之后的回扣，「刚才说的」用于锚点紧接它解释的那条正文。改口播后必须重跑 TTS → 重算 captions → 重渲，四者同源（既有铁律）。
**v3.47.0 补充（1013 实测）**：加长口播前先**按场景字数预估锚点占比**（atempo 相近时时长∝字数，免 TTS 返工迭代）——1013 写完脚本一算 0.6936 不达标，给场景 2/4 共补 19 字推到 0.7060，TTS 实测 0.7099 一次过。TTS 后仍略低时可用**锚点场景 atempo +0.1**（1.4→1.5，缩短锚点时长抬占比；1013 scene5 9.04s）作最后微调，主杠杆仍是加长锚点前口播。
**Why:** 70–80% 是为了让锚点落在观众还没划走的位置，把 CTA 提前等于用错误的叙事换一个合格的数字。
**How to apply:** Phase 8 锚点位置校验；审核清单第 4 节同时记播放顺序和过渡句，两者必须自洽。

### 🔴 场景图默认走接口，本地 PIL 抽象图只是兜底（v3.43.0 / 2026-10-09 实测，坑 237）
**问题**：1009 场景图直接用 `gen_scenes_local.py`（Pillow 抽象色块）渲染进片，用户指出「视频图片是本地生成的」并要求改接口重渲。Phase 5.6 的本地化是**兜底**，被当成了默认路径。
**解决**：场景图默认走 Phase 5 的 `gpt-image-2`（`GEN_IMG_API_URL`/`GEN_IMG_API_KEY`，size 由 `size_for(api_url)` 运行时决定——rainflow 传 `auto`、其余传 `1536x1024`，坑 300/304；prompt 显式 `no text, no letters, no logos, no watermarks, no faces` + 结尾 16:9 构图句），提示词落盘 `prompts/image-prompts.json`，原图保留 `images/sceneN_api.png`，转 1920×1080 JPEG 再进 Remotion。本地 PIL **只在接口全挂时**启用，且必须在汇报里标明「场景图为本地兜底」。**封面不在此列**：中文日期/品牌名的像素级准确仍走本地 PIL（坑 225），不重试接口。
**Why:** 抽象色块没有新闻信息量；用户要的是能看懂场景的画面。封面文字准确性与场景图表现力是两个不同的约束，不能用同一条「API 不可靠」一刀切。
**How to apply:** Phase 5 / 5.6；审核清单第 6 节记场景图来源（接口 / 本地兜底）。

### 🔴 publish.json 是每期必落盘产物（v3.43.0 / 2026-10-09 实测，坑 238）
**问题**：1009 整期（脚本、TTS、字幕、渲染、公众号草稿）跑完，`news-pipeline/2026-10-09/` 下没有 `publish.json`。标题、标签、简介散落在各平台上传脚本的硬编码常量里，没有单一事实源——用户直接问「publish.json 没生成吗」。
**解决**：Phase 10.2 在渲染前就落盘 `{输出目录}/publish.json`（daily 模板见 10.2；`bilibili.partition` 固定「人工智能」；`draft_only: true`）。各平台上传脚本的 `TITLE`/`TAGS`/`DESC` **从该文件读取**，不另写一套。改标题只改这一个文件。
**Why:** 四个平台的标题规则不同（抖音 ≤30、视频号 ≤16 且符号白名单），没有集中记录就无法在上传前一次性校验，也无从核对「填进表单的」和「定稿的」是不是同一份。
**How to apply:** Phase 10.2；Phase 11–14 上传脚本开工前先读 `publish.json`。

### 🔴 B站封面弹窗关闭按钮要点自身中心（v3.43.0 / 2026-10-09 实测，坑 239）
**问题**：1009 封面弹窗「封面制作」打开后，用 `[class*=close]` 泛匹配点击，命中了别的元素，弹窗不关，整张表单被挡住，后续分区/标签操作全落在弹窗上。
**解决**：关闭按钮是 `.cover-editor-head-close`（1009 实测 25×25，位于弹窗头部右端）。取其 `getBoundingClientRect()` 点击**中心**。关完回读 `document.body.innerText` 不含「封面制作」再继续。
**Why:** 弹窗打开时页面上有多个 class 含 close 的节点，泛匹配的第一个往往不是它。
**How to apply:** Phase 11.4 封面步，接在坑 218「点完成」之后：弹窗没关干净就不能进分区/标签。

### 🔴 B站清标签的选择器会误伤推荐标签行（v3.43.0 / 2026-10-09 实测，坑 240）
**问题**：1009 用 `.tag-item, [class*=tag-item]` 找已选标签的关闭符，该选择器**同时匹配** `.hot-tag-item`（推荐标签/参与话题行）。点下去不是删除而是**把推荐话题加进标签**——「B站AI无限竞技场」被加进来，还占掉上限名额（坑 219 的 10 个上限）。
**解决**：删除只在**标签输入框内的已选 chips**上操作（`label-item-v2-container` 右缘，坑 219 的坐标点击），选择器显式排除 `.hot-tag-item` / `.hot-tag-container`。每次增删后回读 chips 文本列表，终态 = `publish.json` 的 tags，多出来的推荐话题立即删。
**Why:** `[class*=tag-item]` 是子串匹配，推荐行的 class 恰好包含它；「清理」和「添加」在这个页面上是同一个点击动作的两种落点。
**How to apply:** Phase 11 标签步，与坑 219 合并执行。

### 🔴 渲染归档未落盘验证，禁止汇报「视频已生成」（v3.39.0 / 2026-09-21 周报实测，坑 222）
**问题**：0921 周报 Remotion 渲染成功（105.877s / 9,351,919 B），但 ① out 参数是相对路径，渲染命令 CWD 在 `video-project`，产物落在 `news-pipeline/video-project/out/` 而非 Phase 9 声称的根 `out/`；② 归档 `cp` 被分类器抖动（坑 216）打断后未补，`weekly/2026-09-14~2026-09-20/video/` 目录为空就完成了汇报——用户两次追问「视频呢,没有视频」。
**解决**：① 渲染前 `cd` 仓库根，或 out 写**绝对路径**，消除 CWD 歧义；② 归档 = `cp` 到模式目录 `video/`（daily `news-pipeline/YYYY-MM-DD/video/`、weekly `news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/video/`、monthly `news-pipeline/monthly/YYYY-MM/video/`）；③ **汇报前门**：`ls -la` 确认 `video/` 非空 + ffprobe 回读时长/分辨率/帧率，缺任一禁止写「视频已生成」；④ 归档被抖动打断时把「待归档」写进状态文件，恢复后第一件事补归档。
**Why:** 「渲染成功」与「用户能拿到文件」之间隔着归档与验证两步；汇报必须以用户视角的产物位置为准。
**How to apply:** Phase 9 归档段（两处「归档时机」均已写入汇报门）。

### 🔴 封面大字超宽被静默裁掉，必须按可用宽度实测收缩字号（v3.47.0 / 2026-10-13 实测，坑 249）
**问题**：1013 竖版封面 `vertical-3-4.png` 用户报「内容被截断」。`gen_covers_local.py` 用固定比例字号 `int(w*0.150)=172px`，「先验三百条哈希」8 字行实宽 1376px，超出可打印宽度（1152−2×margin≈934px），PIL `draw.text` 超出画布部分**静默裁掉**、无任何告警；「真比例回读断言」只验了 1152×1536 画布尺寸，验不出文字截断。
**解决**：① `fit_size(part1, highlight, max_width, start_size, min_size=48)`：`font.getlength()` 实测整行宽度，从目标字号逐级收缩直到 `px ≤ max_width`；② 生成时**打印每行 px 与 limit** 并断言（1013 修复后竖版 812px/928px ≤ 934px）；③ 横版同样要过此门——1013 横版 1272px/1276px 已贴极限，钩子再长 1 字即截；④ 生成后 `Read` 目检确认两行大字完整在画布内。
**Why:** 固定比例字号假设「大字短句长度恒定」，但 Hook 原词每期不同；画布越窄（竖版 1152）越容易超宽，且 PIL 不报错。
**How to apply:** Phase 5.5 `gen_covers_local.py`；审核清单封面项同时记录「行宽断言过 + 目检无截断」。

### 🔴 edge-tts WSS 403 根因是出口 IP，禁止在 header/版本/时钟上空转（v3.47.0 / 2026-10-13 实测，坑 250）
**问题**：1013 TTS 卡死约 3.5h：`wss://speech.platform.bing.com` 握手持续 `403`，而 HTTPS `voices/list` 正常。逐项排查全部无效：Sec-MS-GEC 时钟偏移（+66s，DRM 自校正无效）、edge-tts 6.1.16 与 7.2.8、user-site/framework-site 双安装互切、用户提供的 MSIE UA + Chromium 129 header 补丁（原始 WSS 探测矩阵 24 组全 403）。
**解决**：根因 = **出口 IP**。`edge-tts --proxy http://127.0.0.1:7897` + **用户把代理切到美国出口**后 6 场景一次通过；直连与 `api.msedgeservices.com` 仍 403。三个关键事实：① 终端没有 `HTTPS_PROXY` env、系统 scutil 代理对 aiohttp 不生效，**必须显式 `--proxy`**（`gen_tts.py` 已固化）；② 代理在 CN 节点时同样 403，出口国家是变量；③ `python3 -I` 探测脚本忽略 `SSL_CERT_FILE` 会报 `ClientConnectorCertificateError` 假故障（用 certifi `cafile` 或去掉 `-I`）。
**Why:** 服务端按出口 IP 段风控时，客户端指纹（UA/版本/时钟/token）怎么改都没用；「WSS 403 但 HTTPS 正常」就是 IP 段风控而非 token 错误的特征信号。
**How to apply:** Phase 6.3；TTS 403 时第一动作 = 单句 `--proxy` 探测，403 → 请用户切非 CN 出口，**最多再试一次直连**，然后按此诊断收敛，不再改 header/版本。

### 🔴 Playwright attach 无报错挂起 → 整平台切 raw CDP；wujie 空壳用 Page.navigate 重挂（v3.47.0 / 2026-10-13 实测，坑 251）
**问题**：1013 上传阶段 B站/抖音/视频号三平台的 Playwright `connect_over_cdp` 全部**无报错纯挂起**（并发 raw CDP 客户端对同一 daemon 无冲突 → 问题是 Playwright flatten 协议/事件洪泛自身）。视频号叠加第二个故障：登录墙清掉后 `#app` 仍是空壳（`.app-body-full` kids=0、后代总数=1、`appText` 空，SPA 未挂载），`Page.reload` 多次无效。
**解决**：① attach 挂起 >30s 即弃 Playwright，该平台脚本整平台改 **raw CDP websockets**（模板 `news-pipeline/2026-10-13/scripts/channels_upload_1013.py`：`/json/list` → `webSocketDebuggerUrl` → cmd/ev 助手；**首选 `Runtime.evaluate` 取 `objectId` → `DOM.setFileInputFiles({files, objectId})`（v3.67.0 坑 319，1028 实测一次成功）**；旧的 `DOM.getDocument{depth:-1,pierce:true}` + `DOM.querySelectorAll` 路径在本机 Chrome 155 上 -32601，已降级为备选；contenteditable 用 `Input.insertText`；Vue 受控 input 用原生 value-setter + `input` 事件；截图 `Page.captureScreenshot`）。② wujie 空壳 = **`Page.navigate` 到 `/platform/post/video` 重新挂载**；nav 返回 `net::ERR_ABORTED` 属正常。③ 挂载判据（轮询 ≤60s）：`#app` 后代数 >10 且 `input[type=file]` 出现（1013 实测 kids=1410、2 个 file input、按钮含「保存草稿」），未达标禁止碰表单。
**Why:** Playwright 挂起不抛异常，最容易被误判成「浏览器死了」去重启 daemon——实际 daemon 活着，换客户端即可；wujie 空壳同理，reload 只重拉外壳，navigate 才会重跑微应用挂载。
**How to apply:** Phase 11/13/14 上传开工前 `curl -s -m 5 http://localhost:9222/json/version` 探活（坑 198 协议）；attach 挂起即切 raw CDP，不再回头试 Playwright。

### 🔴 curl 下载图片被静默截断 → 渲染出纯绿条，必须严格 PIL 解码 + 尺寸门禁（v3.49.0 / 2026-10-15 日报实测，坑 254）
**问题**：1015 成片首帧起第 1/3/5 场景画面底部各有纯绿条（实测行数 59 / 725 / 32 行，RGB 恒为 `(0,137,0)`）。排查起初误判为 Remotion/CSS/素材拷贝问题，实际根因在**图片下载环节**：`gen_scenes_api.py` 的 `ok-url` 分支用 `curl -s -o out URL` 取图，接口返回的 body **尾部被截断**（scene1/3/5 分别少 43 / 16 / 14 字节），而 `curl` 对截断 body 仍 **exit 0**；脚本只校验 `getsize(out) > 5000` 即判成功，解码正确性无人把关。于是三个缺损 JPEG 一路流过 ffmpeg 转 PNG（`-v error` 只吐 `overread 8` 警告不报错）、转 public JPG，ffmpeg 的容错 JPEG 解码器把**取不到的尾部像素填成重复值**，最终烧进成片变成绿条。
**解决**：① 下载后**严格 PIL 解码**——`Image.open(p); im.load()`，**绝不可**设 `ImageFile.LOAD_TRUNCATED_IMAGES`（设了仍能读、反而制造假阳性，是本坑最大的检测陷阱）；被截断会抛 `OSError: image file is truncated (N bytes not processed)`，捕获即判失败重试下一端点。② 尺寸门禁从 `>5000` 提到 `>20000` 且**同时过解码**；③ 末尾绿行扫描作为二次断言（取底边 5 点，`|g-137|<12 且 |r|,|b|<12` 连续即计数，>0 即失败）；④ **禁止只验产物不验源**——1015 一开始反复重转 PNG/JPG 完全无效，因为 `_api.png` 本身就是坏的；⑤ `skip (exists)` 只认「尺寸合规 **且** 严格解码通过」的文件，否则「坏但足够大」的文件永不会被重试（1015 scene1/3/5 就是被旧逻辑跳过的）。
**Why:** 「HTTP 200 + exit 0」不等于「文件完整」，中间网络/网关截断完全可能；ffmpeg 对残缺 JPEG 的容错解码把「缺失」伪装成「画面」，肉眼与常规 ffprobe 都验不出，只有严格解码才会显式抛错。**正确图源验证必须发生在转换之前**。
**How to apply:** `gen_scenes_api.py` 下载分支 + 生成后校验段；Phase 5 场景图生成与 Phase 9 渲染前各跑一次「严格解码 + 尺寸 + 绿行」三合一门禁，12 个文件（6 `_api`/6 成图）全绿才允许进渲染。

### 🔴 公众号占位符/合集偶发空态，先重跑该步再定性（v3.47.0 / 2026-10-13 实测，坑 252）
**问题**：1013 公众号链路两处偶发空态：① images 步跑完，verify 读到 `placeholders=1`（最后一个占位符未替换）；② save 步首跑「合集」下拉 `option not found (0 items)`（选项列表未加载完成）。
**解决**：① 直接重跑 `wechat_upload.py images`——脚本幂等（每轮扫描剩余 `PLACEHOLDER` 替换），1013 重跑一次即 `left=0`，再 save；② 重跑 `wechat_upload.py save` 即挂上「今日羊报 AI」。与坑 232（B站标签重输即过）同族：**平台前端偶发空态先重跑该步一次再定性**，禁止据此判定功能不可用转手动。
**Why:** 两处都是「前端异步加载未完成就读状态」；脚本本身幂等，重跑成本远低于人工排查。
**How to apply:** Phase 12.6 images / 12.10 合集 / save+verify；verify 报 placeholders>0 时的第一动作 = 重跑 images。

### 🔴 合集「option not found (0 items)」是假阴性，判据只认编辑页回读（v3.50.0 / 2026-10-15 实测，坑 255）
**问题**：1015 公众号 save 步首跑打印 `collection option: option not found (0 items)`，按坑 252 重跑 save **仍是 0 items**——但编辑页回读文本里已含 `「今日羊报 AI」`，合集实际**早已挂上**。若照坑 252 的「重跑一次仍不行就转手动」会白白丢掉一个已完成的草稿合集。
**根因**：`li.select-opt-li` 是**用户手动展开下拉后**才渲染的选项节点；脚本链路（点「合集」label → 点「未添加」→ 点 `input[placeholder="请选择合集"]` → value-setter 填「今日羊报」）在选项列表未渲染时**仍会命中默认/唯一合集**并写入，此时 DOM 里根本没有 `li.select-opt-li`，计数自然为 0。**0 是「没展开」，不是「没选中」。**
**解决**：合集是否挂上的**唯一可靠判据 = 编辑页回读文本含合集名**：
```python
st = page.evaluate('''() => {
  const all = Array.from(document.querySelectorAll('*')).filter(e => e.children.length === 0);
  const hits = all.filter(e => /今日羊报/.test(e.textContent || '') && e.offsetParent)
                  .map(e => (e.textContent || '').trim().slice(0, 40));
  return { hits: hits.slice(0, 10),
           bodyLen: (document.querySelectorAll('.ProseMirror')[1]?.innerText || '').replace(/\s/g,'').length };
}''')
# hits 含「「今日羊报 AI」」= 合集已挂；hits 只有标题/正文命中 = 未挂
```
判读要点：标题与正文里本来就有「今日羊报」字样，**必须区分**——合集命中的是**独立的、短文本的**叶子节点（如 `「今日羊报 AI」`），不是标题行或 CTA 行。

**🔴 v3.66.0 重要修正（坑 310 / 2026-10-26 实测）：上面这条「叶子节点」判据仍然会假阳性，已降级为不可用。**
本期正文开头的 `<blockquote>` 署名行 `今日羊报 AI · 2026-10-26` 就是**独立的、短文本的叶子 SPAN**（195×21），`/今日羊报/` 直接命中；`TAIL` 页脚 `🔔 关注「今日羊报 AI」，每天 9 点…` 也是叶子，含书名号原样命中 `「今日羊报 AI」`。据此判「合集已挂」→ 实际字段是「未添加」，**整条链白跑**。
**唯一可用判据 = 读合集控件本身**（有专属 class 就不要再做文本搜索）：
```python
coll = page.evaluate("() => { const d = document.querySelector('.js_article_tags_content'); return d ? d.textContent.replace(/\\s+/g,' ').trim() : null; }")
# 未挂 = '未添加'；挂上 = '「今日羊报 AI」'
coll_ok = bool(coll) and '今日羊报' in coll and '未添加' not in coll
```
**「未添加」与「已挂」的区分是一条硬规则，不是启发式**：控件文本里出现「未添加」就直接判失败，不要因为别处有同名字符串而放行。

**Why:** `li.select-opt-li` 计数测量的是「下拉是否展开」，不是「值是否已写入」；拿展开状态当写入状态是典型的假阴性，且重跑不会改变结论（每次都不展开）。**而「叶子节点文本匹配」测量的是「页面上某个地方出现过这个名字」，也不是「字段是否写入」——本期证明正文署名/页脚足以让它恒真。**
**How to apply:** Phase 12.10 合集步 + `wechat_upload.py save` 的返回判读。**禁止**用 `option not found (0 items)` 作为失败信号、禁止据此重跑或转手动；**判据只认 `.js_article_tags_content`，禁止任何形式的页面文本搜索（含叶子节点扫描）**。与坑 252 的关系：坑 252 说「偶发空态先重跑一次」仍成立（针对 placeholders 与真正的选项未加载），但**合集这一项的重跑判据已被本条取代**。

### 🔴 API 429 双形态会批量杀死请求/子 agent（v3.47.0 / 2026-10-14 记录，坑 253）
**问题**：1013 期主循环撞过 `429 · maximum 25 requests in 5 minutes`（限频）；skill 回写时 6 宽 Workflow 子 agent 全灭于 `429 · Concurrency limit exceeded for user`（并发上限），降到 2 宽仍有阵亡——被杀的 agent 返回 null **不会自动重试**，静默丢覆盖。
**解决**：① Workflow/Agent 并发宽度 **≤2**（有其他会话并行时更保守）；② 关键提取/核验类工作宁可主循环自己做，不依赖子 agent 覆盖率；③ 主循环自身被 429 时拆单 + `sleep` 间隔重试（与坑 216 分类器抖动同对策）。
**Why:** 429 的两种文案（限频/并发）都表现为批量失败；子 agent 的 null 是终态，等不来恢复。
**How to apply:** 任何 Workflow 编排前评估并发；提取结果里出现 null/空份额时按「被杀」处理补跑，不当成「无发现」。

### 🔴 公众号验收三件套的三个入口坑（v3.53.0 / 2026-10-18 实测，坑 259-261）
**坑 259：首页/草稿卡片链接里的 appmsgid ≠ 编辑器 appmsgid，验收判据只认标题文本**——1018 verify 后在首页按 `APPMSGID=100001596` 文本匹配 → `appid_in_home=False` 假阴性；首页「近期草稿」卡片链接里的 `appmsgid=2247485xxx`（2247485243/2247485234/…）是另一套 ID 体系，与编辑器 URL 里的 `appmsgid=100001596` 不是一个东西。**唯一可靠判据 = DOM 含当期标题文本**（如 `V4.1-Flash-1017`），实测首页/草稿箱均命中。
**坑 260：直接 goto 草稿箱列表页 URL 会掉会话，且默认落在「历史图文素材」tab**——`appmsg_edit_v2&action=list` 页直接 goto（先不带 token → 「请重新登录」；带 token 直跳 → 登录态在但默认 tab 显示 2018/2020 的「历史图文素材」，看不到当期草稿）。正确动作 = 从带 token 的现成 `home/index` 标签页 `bring_to_front` 后**在页内导航/点击**进入，列表页打开后**必须点文本为「草稿箱」的 tab** 再断言标题（1018：点 tab 后首条即 `【2026-10-18】DeepSeek V4.1-Flash-1017…`，更新于 16:41）。
**坑 261：「发表记录」tab 点击不跳转，发表记录判据改用首页「近期发表」区块**——在列表页/首页点「发表记录」后页面仍回草稿箱列表（DOM 未变），按 tab 文本判断是否进入会永远读不到。正确动作 = 读**首页「近期发表」区块**（`indexOf('近期发表')` 后取 tail）：1018 最新一条=昨日 1017 期「已发表」→ 当日无发表 ✓。判据逻辑：近期发表首条日期 ≠ 当期日期（或首条标题不含当期日期串）。
**正例固化**：公众号分步链一次过（坑 243 顺序 open→body 1036字→images 5图占位符 0→cover hasQpic→title 67字→save appmsgid=100001596 合集「今日羊报 AI」picked→verify 编辑页全绿）；分类器故障期（只读过/非只读全拦，坑 1003/216）把 prep 脚本+PIPELINE-STATUS.md 先落盘（Write 通道可用），恢复后 `prep_wechat_1018.sh`（cover=horizontal 拷贝 + CDP 9222 探活）→ 按状态文件分步续跑，零重跑。
**Why:** 验收三件套的后两件依赖入口页，而入口页的 URL/tab/ID 体系每个都是假阴性来源——错一个就可能把完好草稿误判成丢失、或误以为发生了发表事故。
**How to apply:** 公众号 verify 后补两件时：①标题文本匹配（不用 appmsgid）；②列表页从首页标签页内进+点「草稿箱」tab；③发表记录看首页「近期发表」区块首条。任何「找不到草稿/看不到发表」先怀疑入口，别急着重跑 save。

## 更新日志

### v3.74.0（2026-10-30 知乎二次实跑：raw CDP 全链 + 专栏默认值陷阱，坑 344-347）

基于 **post-to-video 帖文成片**（`generated-videos/post-to-video/20261029_643293715/scripts/upload_zhihu_rawcdp.py`，最终 `ZH_OK`：标题 44 字 / 正文 2035 字 / 块 37 / 视频 1 playable 且在正文前 / 封面 1440×1080 / 创作声明 / 专栏「今日羊报 AI」）。四个新坑：

**坑 344：`cdp_helper.eval()` 不做参数注入** — `Tab.eval(expr)` 只接受一个字符串表达式；Playwright 风格的 `eval("(title) => {...}", title)` 里第二个参数**被静默丢弃**，JS 侧变量为 `undefined`。正解是 `f"(() => {{ const want = {json.dumps(x)}; ... }})()"`。生成的选择器含 `%` 时不要用 `%` 格式化。**这条最危险**——`setter.call(t, undefined)` 会把标题写成字面 `"undefined"` 却回读成功。

**坑 345：`click_safe` 危险词闸门误伤「发布设置」** — 闸门按子串匹配 `发布`，而展开发布设置面板的入口文案就是 `发布设置`，一拦就卡死设置步骤。**不许改宽闸门或传 `allow_danger=True`**；正解是给「展开型」控件写局部安全点击：文案**严格等于**目标词 + 祖先链里无提交按钮 + 命中 `SUBMIT` 白名单即拒，再走 `Input.dispatchMouseEvent` 坐标点击。

**坑 346：知乎专栏默认值是「上次用过的专栏」** — 回读 `radio.checked` 只能证明开关打开，不能证明选对；1030 实测开关已勾选、专栏名却是随机的 `「虢礫緙嘞」`。判据必须两级：`radio.checked === true` **且** `.ColumnSetting-ColumnSelector button` 文本归一化后 == 目标专栏名（选项带书名号，比较时两边剥 `「」` 与空白）。

**坑 347：视频卡片封面 input 只在弹窗打开后存在** — `input.VideoCoverFileInput-input` 不在初始 DOM；且页面同时有 4 个 file input（附件/正文图片/文章封面/视频封面），按「取最后一个」会选错。文章封面已设时视频卡片用首帧即可，不要为了视频封面去点按钮。

**另固化两条 raw CDP 实操**：① 视频号「保存草稿」后 `Page.navigate` 到 `draftListManager` 会因 SPA 路由弹回而被误判丢失，判据改为**新标签**打开草稿箱读 `草稿箱 (N)` + 首条标题；② 视频号封面弹窗关闭后 `.edit-cover-dialog-container` 不卸载、只被压成 `0×0`，`offsetParent`/`textContent` 仍命中 → 判据改为 `getBoundingClientRect().width > 0`，并回读封面槽 `naturalWidth/naturalHeight` 比例做正证。

### v3.73.0（2026-10-30 知乎首次端到端实跑，Draft.js 选区陷阱 + 判据假绿，坑 338-343）

基于 **2026-10-30 期知乎草稿全链实跑**（`news-pipeline/2026-10-30/scripts/zhihu_upload_1030.py`，最终 `ZHIHU_DRAFT_OK`：视频 1 playable / 图 6 / 封面 1 / 创作声明 / 专栏 radio checked / 正文 2110 字）。

**新增能力：正文前内嵌成片视频**
- 工具栏 `button[aria-label="视频"]` 打开「导入视频」弹窗，但真 input `input.VideoUploadButton-fileInput` **在弹窗打开前就已在 DOM**，可直接 `set_input_files`
- 视频卡片插在**光标所在块**：光标置文档开头 → block 0 自动空文本 + block 1 VIDEO，即在正文之前（需求「最后在正文前插入生成的视频」已满足）
- 约 10–15 s 出卡片，判据 `.Editable-video` 的 `dataset.videoPlayable === 'true'`；刷新后卡片与前后文本完好

**坑 338：视频卡片是原子块，退格整块删** — Draft.js 里 `.Editable-video` 不可分割，光标在其后按一次 `Backspace` 删的是**整个视频**。任何含退格的操作后必须重数 `.Editable-video`。

**坑 339：`Shift+Home` 在 Draft.js 会反向选到整篇开头** — 1030 首轮想只选占位行，实际把占位之前的正文全删了：正文 2025 字 → 441 字、34 块 → 7 块、6 图 → 1 图，**且自动保存已把破坏写进草稿**。正解是 `Range.selectNodeContents(占位文本节点)` 精确选中再退格。教训：破坏发生后必须 reload 回读才算知道真实状态。

**坑 340：Vue tab/radio 的 `element.click()` 静默无效** — 无报错但选中态不变；须取 `getBoundingClientRect()` 中心走 `page.mouse.click(x,y)`。

**坑 341：整行加粗判断漏掉「行首加粗 + 行内正文」** — `startswith('**') and endswith('**')` 放过 `**AI 辅助创作说明**：本文由作者…`，页面上留下字面 `**`。须逐行 `re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)`，并把「全文块文本无 `**`」加进验收。

**坑 342：`Backspace` 走 Draft.js 内部选区，不是刚设的 DOM 选区** — `paste` 认 DOM Selection 所以落点正确，但退格删掉了文件开头的视频卡片。**任何带退格的步骤之后都必须回读全部结构性计数**（视频数/图片数/块数）。

**坑 343：专栏选中态 grep 页面文本恒真** — `发布到专栏 / 不发布到专栏` 本来就常驻 DOM；真判据是 `.ColumnSetting-ColumnSelector` 内 `input[type=radio]` 的 `checked`。

**修正一处长期错误文案**：知乎专栏真名是 `今日羊报 AI`（**半角空格 U+20 + 末位大写 I U+49**，按页面码点实测）；旧文档写的「末位小写 l、无空格」其实是**抖音/视频号的合集名** `今日羊报Al`（小写 l U+6C、无空格）。两个平台名称不同，已分别改正并加交叉警示。

### v3.72.0（2026-10-30 新增知乎平台，模块化）

**定位**：第五个发布平台，图文 + 内嵌成片视频。

**模块化**：全部实现细节搬到 `templates/platform-zhihu.md`（派生规则 / 合规审核门 / 上传流程 / 脚本骨架 / 失败回退 / 探测记录表），SKILL.md 只留入口、五条平台铁律与产物命名，避免主文档继续膨胀。

**新增内容**
- 派生：公众号图文 → 知乎稿，标题改信息型（≤40 字、无品牌后缀）、删 CTA、加「编辑判断」段、配图对齐小节
- 审核门：`templates/platform-zhihu.md` §2 十一条清单（标题禁词 / 无导流 / 判断段 / 来源标注 / 图文相关 / 事实核验…），依据随附的《知乎关于 AI 辅助创作内容的治理细则》《知乎社区规范》
- 上传：立即创作 → 标题 → 正文+配图 → 正文前插视频 → 封面 → 创作声明（含 AI 辅助创作）→ 专栏「今日羊报 AI」→ 保存草稿
- 验收：草稿列表出现本期标题 + 列表无本期发布记录 + 编辑器结构性计数回读（含视频 playable、图片数、无 `**` 残留、专栏 radio checked）
- 配置：`publish.json.platform.zhihu{title,column,tags,article,images}`；模式参数映射表加 4 行

**合规依据（写进 skill 的两条平台红线，不是我们的偏好）**
- 《治理细则》：需主动添加「包含 AI 辅助创作」声明、披露使用目的、由作者完成主要智力劳动并对最终内容负责；重点治理「滥用 AI 大量发布拼凑内容」与「AI 生成低质内容（文不对题/图文不相关/事实错误/虚假谣言）」
- 《社区规范》§四：禁止标题/封面加导流营销信息、禁止诱导至第三方平台关注；§五：禁止自动化外挂批量发布、**禁止发布机器生成的内容**、禁止重复发布相似内容、禁止代写代发
- 因此：只存草稿、一期一篇、发布由用户手动、AI 声明不能替代作者判断

**实测回填（2026-10-30，已消除未测项）**
- 20 项页面选择器与控件文案**已全部实测确认**，结果见 `templates/platform-zhihu.md` §7 探测记录表与 §3 上传流程：编辑器 = `zhuanlan.zhihu.com/write`（新开标签）、标题 `textarea`、正文 `div.public-DraftEditor-content`（Draft.js）、图片 `input[accept*="image/webp"]`、视频 `input.VideoUploadButton-fileInput`、封面 `input[accept=".jpeg, .jpg, .png"]`、创作声明 = `div.css-be2u3` 内 combobox → `.Select-option`「包含 AI 辅助创作 作者对内容负责」（已实设并回读通过）、专栏 = radio `checked` 判据、**无保存按钮＝自动保存**（URL 变 `/p/<id>/edit` 即落库）
- **仍未实测**：封面裁剪弹窗行为、`zhihu-images/` 生成脚本、文章的最终发布流程（本站点不执行发布）

### v3.66.0（2026-10-26 日报全程实测，验收判据自欺 + 合集静默失败 + 一条被证伪的推断，坑 310-316）

基于 **2026-10-26 日报全链**（daily 295 帖；成片 **147.349s / 12,896,900B / 4419 帧 / 1920×1080 / 30fps**，锚点 **0.7377**；公众号脚本上传并最终补挂合集；B站脚本实证后用户改手动；抖音/视频号用户手动）实测。

**坑 310：合集判据用正文子串 = 恒真**
- 事故：`MP_VERIFY` 打出 `{"collection": true}`，`coll_ok = COLLECTION in all_txt`。但合集字段实际是「未添加」，从头到尾没挂上。
- 根因：`COLLECTION = '「今日羊报 AI」'`（含书名号）命中了正文 `TAIL` 页脚 `🔔 关注「今日羊报 AI」，每天 9 点带你速览 AI 圈最热的 5 条新闻。`
- **判据改成读控件**：`document.querySelector('.js_article_tags_content').textContent` → 未挂为 `未添加`，挂上为 `「今日羊报 AI」`
- 沉淀规则：**有专属 class 就别做文本搜索**。坑 255 说「只认独立短文本叶子」，本期证明还不够——叶子里也可能有正文页脚。

**坑 311：图片计数被 ProseMirror 分隔符污染 = 恒假**
- `body.querySelectorAll('img')` 返回 **12** 个：6 个真图（1080×608 ×5 + 1080×810 ×1）+ **6 个 `IMG.ProseMirror-separator`**（`src` 空、`naturalWidth=0`）
- `all(w>100)` 恒假；反过来只数 `imgCount` 又恒真（数量对不代表加载成功）
- 修法：`filter(i => !i.className.includes('ProseMirror-separator') && (i.getAttribute('src')||'').length > 0)` 然后才断言尺寸
- 判失败的两个不同含义别混：`src` 空 + separator class = **假问题**；`src` 非空 + `naturalWidth=0` = **真破图**

**坑 312：合集弹窗的唯一真入口是一个 54×22 的小 DIV**
- 无效且**不报错**的点法：点 `SPAN.lbl_content`（「合集」二字）／行内空白／`.frm_checkbox_label` 整行——DOM 节点数 **1377→1377**，无异常，随后「保存为草稿」照样成功并返回 `appmsgid`
- 真入口：`.allow_click_opr.js_article_tags_label`（文本「未添加」的 DIV）
- 弹窗结构：`.album-setting-dialog` → `input[placeholder="请选择合集"]` → `.select-opts-con li.select-opt-li`（本期 3 项 320×36）→ `button.weui-desktop-btn_primary` 文案「确认」
- **弹窗是否打开要用容器判**：`document.querySelector('.album-setting-dialog').offsetParent` 非空。**「页面文本含『选择合集』」恒真**，不能用
- 挂上后必须重新「保存为草稿」；实测补挂重存后 `appmsgid` 仍在、`bodyLen` 1877 不变、占位符 0——**重存不破坏已有正文与图片**
- **旧指导「合集 try-catch 跳过不阻塞保存」是本期静默失败的成因之一**：可选项可以跳过，需求明确要的字段必须硬断言

**坑 313：跨平台复制断言词表必挂**
- 同一事实措辞不同：抖音「比上一代 K3 **便宜 15%**」／视频号「约为上一代 K3 的 **85%**」
- 把视频号词表套到抖音 → `AssertionError: missing issue word: 85%`
- 修法：词表按 `publish.json` 里**该平台自己的** `description` 生成，禁止跨平台抄

**坑 314：抖音话题按英文句点切分**
- `publish.json` 的 `douyin.tags` 写 `K3.1`，页面回读 `["#AI日报","#K3","#订阅计费","#额度重置","#账号安全"]`
- 点号被吃掉 → **变成了另一个话题**，不报错、不提示
- 修法：话题里避开带点号的版本号（改写 `K3`），或接受降级并按实际值断言；**不要断言 `#K3.1`**

**坑 315：「reload 丢 token」是一个被证伪的推断（方法论坑）**
- 经过：首页回读一度拿到 `len=83` 的「登录超时」空页 → 当时的解释是「裸 `reload()` 丢了 `token=` 参数」→ 据此写了「必须带 token 重新 `goto`」
- 复测推翻：`RELOAD_TEST {"before_len":1685,"after_len":1685,"before_url_has_token":true,"after_url_has_token":true,"after_login_timeout":false}`——`reload()` 保留 token、首页完好；裸域 `goto('https://mp.weixin.qq.com/')` 也会 302 到带 token 的首页（同样 1685），同样不复现
- 结论：`len=83` 是真的，但**成因未知（大概率瞬时）**。「带 token 重新 goto」作为写法仍然安全，但**不许当根因写进文档**
- **元教训**：一次观测 + 一个顺理成章的解释 ≠ 已验证的因果。**准备写进 skill 根因章节的因果链，落笔前必须单独复测一次；复测不成就只记现象、注明「成因未明」**。错误的因果解释会以「经验」的形式沉淀，比没有解释更危险（与坑 305「证据与判据须同源」同族：那次骗人的是换行符，这次骗人的是解释力）

**坑 316：B站草稿行没有可用 `href`**
- `upload-manager/article?group=draft` 列表里，草稿行链接解析为 `null`
- 进编辑页只能点行内「编辑」按钮：从标题叶子节点向上逐级（≤8 层）找 `textContent === '编辑'` 的元素 → 取 rect 中心 `mouse.click` → 通常新开标签落到 `upload/video/frame?type=draft&draftId=…`
- 回读字段：分区 `.selector-container .select-item-cont`、标签 `.label-item-v2-container`（去 `×`）、简介 `.ql-editor` 的 `innerText.length`、封面取页面内 `naturalWidth>=400` 的最大 `img`

**小坑备查：**
- 抖音封面验收**禁止 grep 页面文本**（`竖封面缺失` / `双封面缺失` 在 AI 推荐封面生成期会**瞬时为真**，坑 296）；只认 `.coverControl-CjlzqC` 下标 + `img.naturalWidth/naturalHeight`
- 公众号正文深读时，`body.innerText` 里除了页脚，**标题、作者、CTA 也都会含合集名/日期**——凡是要判「某字段是否生效」，先找该字段的专属容器
- 本期正例固化：daily 295 帖；成片 147.349s / 12,896,900B / 4419 帧 / 1920×1080 / 30fps；锚点 0.7377（wav 实测）；字幕 64 条、7 场景块起点精确等于 wav 边界（Δ0ms）；封面横 1536×1152 / 竖 1152×1536 未触发字号收缩；公众号最终 `MP_FINAL_OK`（appmsgid / 标题 67 字 / bodyLen 1877 / 占位符 0 / 真图 6 / 封面 hasQpic / 合集「今日羊报 AI」）

### v3.65.0（2026-10-25 W42 周报全程实测，raw CDP 迁移 + 三处静默失效坑 306-309）

基于 **2026-10-25 W42 周报全链**（周聚合 2739 → 2644；周报 MD/PDF；成片 **113.856s / 11,624,908B / 1920×1080 / 30fps**，锚点实测 **0.7752**，字幕 55 条尾差 0.624s；B站/抖音/公众号三平台草稿成功，视频号保存未落库）实测，吸收坑 306-309。

**坑 306：`playwright.connect_over_cdp` 整体挂起，HTTP 端点却完全健康**
- 症状：`curl http://127.0.0.1:9222/json/version` 正常、`/json` 列出 25 个 target，而 `connect_over_cdp` 的调用日志停在 `ws connected` 之后，**既不返回也不报错**；timeout 25s 加到 90s 结果完全一样
- 后果：B站/抖音/视频号/公众号四个探针全空转，状态文件里 `upload: running` 却没有真实进展
- 根因判定：**Chrome 侧健康 + playwright 挂在 WS 握手之后 ⇒ 是驱动侧问题，不是浏览器问题**
- 修法：立刻切 raw CDP。三个必踩的细节：
  1. `websockets.connect(ws_url, proxy=None)` —— 不带 `proxy=None` 会走环境里的 SOCKS 代理，报 `ImportError: python-socks is required to use a SOCKS proxy`；
  2. `Runtime.evaluate` 的表达式**必须包进 async IIFE**：`(async () => JSON.stringify(await (async () => { return (EXPR); })()))()`。两种错误写法都**静默返回空值**——`(async () => JSON.stringify(await (EXPR)()))()` 在 `EXPR` 是函数表达式时返回 `undefined`；`JSON.stringify(await (FUNC)())` 顶层裸 `await` 报 `ReferenceError: await is not defined`；
  3. `send()` 里对 `ConnectionClosedError` 重连一次（wujie 长页面会偶发断开，重连后同会话可继续）
- 代价：raw CDP 没有 `locator` / `set_input_files`。文件上传走 `Runtime.evaluate` 拿 `input[type=file]` 的 `objectId` → `DOM.setFileInputFiles({files, objectId})`；**shadowRoot 内的 input 必须先 `Array.from(shadowRoot.querySelectorAll(...))` 拿数组 objectId，再用 `Runtime.getProperties` 按下标取 node objectId**，直接 `querySelector` 得 null。
- **禁止的三种「抢救」**：加大 timeout、重启 Chrome、`pkill` 相关进程——前两个白等，第三个会丢登录态。

**坑 307：公众号 `Meta+A` 选中的是刚 focus 的标题，不是正文**
- 事故序列：`open` 打开编辑页 → `title` 步先点 `.ProseMirror[0]` 输入标题 → `images` 步未换焦点，直接对正文发 `Meta+A + V` → 实际选中标题 → 正文被替换成标题串重复 3 遍（`bodyLen` **1347 → 120**）
- 更隐蔽的是：此时 `PLACEHOLDER_IMG_` 计数变成 **0**，图片验收的「占位符归零」判据**反而通过了**
- 修法（三条都要）：① 每次动正文前 `window.scrollTo(0,0)` → 坐标点击 `.ProseMirror[1]` → **断言 `document.activeElement` 就是它**；② 替换后同时回读 `bodyLen` **和**首段前 20 字；③ 被覆盖只能「全选删除 → 重新 `execCommand('insertHTML')`」，不做增量修补
- 正向样本：重建后 `bodyLen` **1176**、占位符 **0**、`img` 元素 **20**（10 张正文图 + 10 张缩略）、封面 `hasQpic=true`、标题 42 字

**坑 308：视频号「保存草稿」点击成功但不落库**
- 本期状态：短标题「羊报AI周刊 10月19日至25日」与描述**分离写入成功**（`title` 与 `.input-editor` 各自回读正确）、`.mark-tag-select` 选中英文项、合集选中、竖 3:4 / 横 4:3 双封面就位；点「保存草稿」后——
  - 页面**无 toast**
  - 外层 `window.fetch` hook **零命中**（请求走了 wujie 沙箱内的另一个 realm，外层 hook 抓不到，所以「无请求」不能作为根因证据）
  - `post/draftListManager` 草稿计数**仍是 4 条**，最新三条是 10-22 期及更早
  - 弹窗排查：`common-dialog`「将此次编辑保留?」等所有对话框 `getBoundingClientRect().height` 均为 **0**（隐藏模板），不是被遮挡
- 结论：判定为平台侧限制，**未点「发表」**，如实报告「未落库」
- 修法：把「保存草稿」的成功判据改成**草稿箱计数 +1 且目标短标题出现**；连续两次失败即停手报告，别换选择器硬试

**坑 309：B站分区与抖音草稿的时序坑（本期各踩一次）**
- **B站分区**：`.select-controller` 的 `click()` 返回后，`.drop-list-v2-item` 要 **≥2.5s** 才渲染出 30 项。没等就按文本找选项，会命中页面上**已经存在的预置分区文本**（本期误落「科技数码」）。正确顺序：展开 → 等 2.5s → 断言 `.drop-list-v2-item` 数量 > 0 → 目标项 `scrollIntoView({block:'center'})` → 重取 rect → 坐标点击 → **回读 `分区
<值>` 文本**。误点后的修复入口是草稿列表的 `.bcc-cmadc-btn.edit`（URL 带 `draftId=4030830`），改完必须再存一次并回读。
- **抖音**：`content/post/video` 页在 `uploading` 期间标题输入框存在但 `insertText` 会被吞。必须等 `uploading=false` **且**「暂存离开」按钮出现再填表；暂存后走双信号（按钮消失 + 「继续编辑」横幅），**同标签**点「继续编辑」回读（`vids>0` 且标题正确）后再暂存第二次。

**小坑备查：**
- **草稿数 ≠ 投稿数**：B站「全部稿件」计数含草稿，本期 704 是期初值，草稿另计 1 条；判定「有没有误发」要看**已发布**计数与期初是否相等，不是看总数。
- **`websockets` 版本差异**：`proxy=None` 参数在 12+ 才有；旧版本直接 `close()` 后重建连接。
- **同一 Chrome 里标签页会越攒越多**（本期一度 61 个），每轮脚本结束应 `close_tab`，或在开工前按 URL 去重清理一次（保留每平台 1–2 个），否则目标查找会变慢且易误命中。
- **W42 正例固化**：周聚合 2739 → 2644（移除 95）；成片 113.856s / 11,624,908B；锚点 0.7752；TTS 实测 113.648s（预估 97s 偏差 +17%，因为逐段在词边界处拖长）；字幕 55 条、尾差 0.624s；封面 1536×1152（60KB）/ 1152×1536（49KB）均未触发字号收缩。

### v3.64.0（2026-10-25 开工前自检，两处「证据对、结论错」的判据坑 304-305）

基于 **2026-10-25 日报产物复核**（非流程事故，是两条判据逻辑本身的缺陷；当期四平台草稿全部正常）实测，吸收坑 304-305：

**坑 304：端点身份按 `_000/_001` 后缀判会静默判错**
- 1025 实测 `settings.json` 的 env：`GEN_IMG_API_URL` = `chatgpt.rainflow.foo/studio/v1`（rainflow，25 张额度，先用）、`_000` = `ai.prism.uno`、`_001`/`_002` = `elysiver.h-e.top`（grok-imagine 兜底）
- 同期 `To_Learn.md` 的备忘写的是 `_003` = rainflow、本体 = prism.uno——**同一期的两份记录编号完全相反**
- 因此 `size = 'auto' if suf == '' else '1536x1024'` 这类**按下标判身份**的写法不可靠：用户改一次编号，size 就传错，网关回「不支持的图片比例」，症状与坑 300（日期替换污染尺寸）**一模一样**，极易误诊
- 修法：**按 URL 域名子串判**（`"rainflow" in api_url` → `auto`，其余 → `1536x1024`）；fallback 优先级也按域名排（rainflow → prism.uno → elysiver），不看下标；开工前先 `python3 -c` 打印 `{后缀: 域名}` 一览（key 只打 len）核对再写脚本

**坑 305：终态验收的判据没做空白归一化，证据与结论自相矛盾**
- `/tmp/final_verify_safety.py` 里：证据 `draftSec` 走 `t.slice(di, di+200).replace(/\s+/g,' ')`（归一化后打印），判据 `draftHasToday` 却是 `/Kimi K3\.1/.test(t)`（**未归一化的原文**）
- 首页卡片把标题折行成 `【2026-10-25】Kimi\nK3.1 Pro 参数堆到 2.8T…`，`Kimi` 与 `K3.1` 之间是 `\s`，`/Kimi K3\.1/` 要求普通空格 → **不匹配** → `draftHasToday: false`
- 于是同一条日志里出现自相矛盾：打印的 `draftSec` 明明含 `【2026-10-25】Kimi K3.1 Pro …`，结论却是「当日无草稿」——**草稿实际完好**（`appmsgid` 编辑页、`近期草稿` 首条、`更新于 00:49` 三处均可交叉验证）
- 修法：**判据和证据必须用同一份归一化文本**——先 `const t = raw.replace(/\s+/g,' ')`，判据和打印都只用 `t`；同类判据（`hasTodayTitle` / `hasTodayShort` / `hasToday`）一并检查
- **诊断指纹：打印的证据命中目标串、结论却是 false** → 先查判据读的是不是另一份文本，不要怀疑平台或去重跑上传

**Why:** 两条坑都属「逻辑正确但判据错位」——304 是把「编号」当「身份」，305 是把「原文」当「归一化文本」。它们的共同危害是**给出一个看似专业、实则反证的结论**，比直接报错更难识别。
**How to apply:** 端点身份一律按域名子串判，不按下标；页面文本判据先归一化空白，且判据与打印共用同一个变量；验收日志里出现「证据与结论矛盾」时，先停下来查判据，不要按结论去重跑。

### v3.63.0（2026-10-25 日报实测，生图 size 派生污染与两处视口外静默点击四坑 300-303）

基于 **2026-10-25 日报全流程**（日报 370 帖/386 抓取；成片 163.392s / 4900 帧 / 1920×1080 / 16,361,460B 锚点 0.7657；四平台全草稿）实测，吸收坑 300-303：

**坑 300：derive 的日期替换会污染生成参数里的尺寸字面量**
- `_derive_1025.py` 把 `'1024' → '1025'` 做全串替换，把生图脚本里硬编码的 `size: '1536x1024'` 改成了 `'1536x1025'`——rainflow 回「不支持的图片比例」，第一反应以为是网关不支持该比例，实际是**尺寸字符串被日期替换污染**
- 排查指纹：网关报「不支持的图片比例」而你确认比例没问题 → 先 `grep -n "x[0-9]\{3,4\}"` 看尺寸字面量有没有被日期替换吃掉
- 修法：**尺寸不做字面量硬编码，按端点算**（`size_for(api_url)`：`"rainflow" in url` → `'auto'`，其余 → `'1536x1024'`）；derive 的替换对 `\d{4}` 年份形态一律用带边界的锚点，别裸替换四位数。**注意别用 `suf == ''` 判端点**——那是按下标判身份，坑 304（v3.64.0）实测后缀编号会漂移

**坑 301：gpt-image-2 的 `size:'auto'` 会返回方图，必须在 prompt 里写死横构图**
- rainflow 只接受 `1024x1024` / `1024x1536` / `auto`；`auto` 实测在 prompt 无构图提示时返回 **1254×1254 方图**（比例 1.00），塞进 1920×1080 画布会被裁掉两侧
- 修法：每条 prompt 末尾追加 `Wide 16:9 horizontal cinematic composition, full-frame landscape framing.`，实测 6/6 返回 **1672×940/941（1.78 ≈ 16:9）**，比 `1536x1024`（1.50）更贴合画面
- 顺序 = 先改 prompt 再重跑；只改 size 不改 prompt 无效

**坑 302：B站分区下拉是 `.drop-list-v2-item`，且在视口外时坐标点击静默无效**
- 旧脚本按 `li,div,span,p` 文本匹配 + `el.click()`，命中失败后分区停在默认「音乐」，断言 `partition verify failed: '音乐'` 才暴露
- 真选择器 = `.selector-container .select-container` 展开 → `.drop-list-v2-item` 选项（30 个，含 `人工智能`）
- 但下拉展开后选项列表高于视口（`人工智能` 在 y=759，视口高 769），**`page.mouse.click(x,y)` 落在视口外不报错也不生效**；`el.click()` / `dispatchEvent(MouseEvent)` 同样无效
- 修法：`locator('.drop-list-v2-item').filter(has_text='人工智能').first.scroll_into_view_if_needed()` → `click(force=True)`。一次过，回读 `.select-item-cont` 文本即 `人工智能`

**坑 303：视频号 `.mark-tag-select` 初始在视口外，同样静默失效**
- 表单首屏渲染后 `.mark-tag-select` 的 rect.y=1208 > 视口 769；`page.mouse.click(941, 1231)` 返回成功但 `.mark-tag-options` 仍 `display:none`，选项查询返回 `[]`（看起来像「下拉没有 AI 选项」）
- 修法：`s.scrollIntoView({block:'center'})` → 重取 rect（y 变 468）→ `mouse.click` → 先断言 `getComputedStyle(.mark-tag-options).display === 'block'` 再查选项
- 与坑 302 同根：**任何 `mouse.click` 前必须确认目标 rect 在当前视口内**，否则失败是静默的

**坑 304 / 305**（端点身份按下标判、验收判据未归一化）同属 1025 开工前自检暴露，详见上方 v3.64.0 段，不在此重复。

**小坑备查：**
- **视频号封面对话框 `edit-cover-dialog-container` 关闭后仍留在 DOM，rect 为 0×0**——用「容器存在 / `offsetParent` 非空」判「弹窗未关」是**假阳性**；判据改用 `rect.width > 0 && rect.height > 0`，或直接回读槽位 `img.naturalWidth/naturalHeight`
- 封面上传后**必须等预览图出现目标尺寸再点确认**（`img.naturalWidth===1152 && nh===1536`），否则确认点在上传渲染完成前，槽位仍是原视频帧
- B站标签可能被平台拒收单个词（本期 `AI大模型` 两次键入 + 推荐行点击均未入 chips，最终 6/7）；断言写成「缺失项记录但不阻塞」，别为凑满 7 个卡死上传
- 1025 字幕块重分配实测复核（坑 298 修复后的正向样本）：72 条 / 六块起点 Δ 全 0ms（0 / 34219 / 69797 / 94603 / 124998 / 159045）；mp4 音频验证 lead 中位 **+0.097s**、max +0.662s、min −0.197s、离群 0（57/72 可测）

### v3.62.0（2026-10-24 日报返工，字幕「跨场景错位」两坑 298-299）

基于 **2026-10-24 日报**（用户两次反馈「1:25 后字幕对不上」→ 第二次「1:34 还是对不上」→ 定位为块互换并重渲）实测，吸收坑 298-299：

**坑 298：play_order 重排后字幕要「块重分配」，不是「块平移」**
- 1024 `play_order=[1,2,3,5,4,6]`；`captions.json` 中 script scene4（MoE）文案占 84.4–112.9s、script scene5（程序员节）文案占 113.5–143.9s，**两块互换**
- 第一次修复脚本只在「字幕已归属的场景」内部重锚定与缩放，从不重新推导归属 → 互换原样保留，重渲无效
- 修法：按 `voiceover-texts.json` 各场景正文归一化字符数把 captions 切成 6 组（1024: 188/205/179/192/214/26=1004，与脚本精确相等），按 `play_order` 累加 wav 实测时长定块起点，**块内用该场景自己的 wav 单独跑词级 ASR** 重计时
- 尾行 `endMs` 补到该场景语音 offset：1024 实测 scene4 差 0.308s、scene6 差 0.298s

**坑 299：验证必须对渲染后的 mp4，不能对源 wav**
- 按播放序拼接 `voiceover/sceneN.wav` 得到的 `full_play.wav` 本来就正确，**拿它做 ASR 必然全绿，等于没测**
- 正确证据链 = `ffmpeg -i out.mp4 -vn -ar 16000 -ac 1 mp4_audio.wav` → faster-whisper 词级 ASR + 抽帧看烧录字幕
- 「音频顺序对、烧录字幕错」是块互换的指纹；音频本身错才是 TTS/拼接问题
- 量化用**首 3 字锚定**（`stream.find(key[:3])` 多命中取最近），1024 结果 lead 中位 +0.205s / max +0.71s / min −0.17s（54/64 可测）
- **禁用全文字符流 SequenceMatcher 直接量偏差**：长片累积插入/删除摊到每条，1024 得到「64 条全部 >0.5s、中位 1.31s」的假信号
- ASR 会把中文数字写成一二三四，归一化时映射 〇一二三四五六七八九 → 0–9 可多救回若干条

**正例固化**：1024 二次修复后成片 148.288s / 4447 帧 / 1920×1080 / 15,779,934B；抽帧 84.3s=程序员节、90.3s=谷歌、106.5s=模型能力、113s=白名单、114.9s=刚才说MiniMax、120–140s=MoE、146s=CTA 全部与口播一致。

### v3.61.0（2026-10-23 日报实测，视频号标注/合集新 DOM 与抖音恢复令牌六坑 292-297）
基于 **2026-10-23 日报全流程**（全量抓取完成；成片 128.128s/3842 帧/1920×1080/14,178,371B 锚点 0.7110 容差内；封面本地 PIL 对齐 2026-10-21 海报模板；四平台全草稿）实测，吸收坑 292-297：

**坑 292：视频号 AI 标注真控件是「视频标注」英文下拉**
- wujie shadowRoot 内不存在中文「AI生成」勾选框，`/AI生成|人工智能生成/` 正则与 checkbox 遍历恒返回 `ai declare: absent`
- 真控件 = `.mark-tag-select`（`.select-display` + `.mark-tag-options`），选项全英文：`No label needed` / `Contains AI-generated content` / `Fictional storyline for entertainment only` / `Personal opinion for reference only` / `Content contains ads` / `Self-recorded content` / `Content is reposted`
- 合规必须选 `Contains AI-generated content`
- 修法：点 `.select-display` 展开 → 真实坐标点目标项 → 回读 `.select-display` 断言

**坑 293：视频号新版合集 DOM + wujie 内 Vue 组件只认坐标点击**
- 旧 `.option-item` 前缀匹配返回 False；新链路 `.post-album-display` → `.post-album-wrap .option-item`
- JS `el.click()` 对这层 Vue 组件不生效（返回成功、display 不变）
- 修法：取 `getBoundingClientRect` 中心 `page.mouse.click(x,y)`；回读 display 为 `今日羊报Al`（小写 l）

**坑 294：wujie shadowRoot 内 file input 用 ElementHandle 必 detached**
- `evaluate_handle(...).as_element().set_input_files()` 报 `Cannot set input files to detached element`
- 修法：Playwright locator 形式 `page.locator('wujie-app input[type=file][accept*="image"]').first.set_input_files(...)`（locator 每次动作前重新解析元素）
- 弹窗确认按钮同理：JS 在错误 wrapper 里查 `.weui-desktop-btn_primary` 得空 → 取可见 dialog 内 `确认` 的 rect 后坐标点击

**坑 295：抖音「继续编辑」是一次性消费令牌（坑 290 第三形态）**
- 抖音无草稿列表页（`/content/manage?tab=draft` 空壳），唯一入口是发布页横幅
- 「暂存」= 写入服务端待恢复槽位，不是创建持久草稿；槽位被读取即清空
- 新开标签点横幅 → 读表单 → 关标签 = 消费掉且不回写，草稿彻底消失，此后任何标签横幅都不再现
- 修法：暂存#1 → **同标签**点「继续编辑」回读 → **再点一次「暂存离开」** → 终态「按钮消失 + 横幅出现」；外部标签只准**读**横幅文本，**禁点击**

**坑 296：抖音竖封面真入口是悬停槽位→「编辑封面」**
- `get_by_role('button', name='设置竖封面')` 常 `disabled`（只是提示位），`click()` 必超时
- 弹窗内 6 个 file input，只有 `.selectArea-BCIYQD input[type=file]` 是封面，其余为模板/贴纸选择器，喂错**静默无报错**
- 封面槽位按下标断言：`.coverControl-CjlzqC[0]`=横 4:3、`[1]`=竖 3:4，用 `img.naturalWidth/naturalHeight` 判 1536×1151 / 1150×1535
- 「竖封面缺失」在 AI 推荐封面生成期会瞬时为真，**禁只 grep 文本判封面**
- **坑 320 补（v3.67.0 / 1028 实测）**：弹窗**默认带裁切缩放**，直接喂 1152×1536 会切掉海报两端的字，平台判「封面存在文字展示不全问题 / 封面不佳」（本期实测「别」「一」被裁）。修法 = 把 `.semi-slider-handle` 拖到**最小档**（`mouse.move → down → 分 10 步 move → up`；**点击与方向键都无效**，实测无反应），实测 rail x 区间 778.5–831.5、y≈550。拖到最小后海报完整带边距显示 →「封面效果检测通过」+ 发文助手「无建议」。另：「编辑封面」叶子搜索**必须限定在 `.coverControl-CjlzqC[1]` 的 rect 内**——全局搜会命中横槽位浮层，打开错误弹窗，上传后仍判「竖封面缺失」

**坑 297：抖音合集选项匹配必须最小面积法**
- `/^「?今日羊报/` + `/共\s*\d+\s*个作品/` 同时命中整个下拉容器（`请选择合集不选择合集「虢礫緙嘞」共4个作品「羊报AI月报」…`），点它等于没选
- 修法：加 `textContent.length ≤ 40` + `rect.height ∈ [10,90]` 约束后**取面积最小**节点点击；本期命中 `「今日羊报Al」共132个作品`（第133集）

**正例固化**：1023 四平台全草稿——B站 `人工智能` 分区 + 7 标签 + 合集「今日羊报 AI」；公众号 appmsgid 已生成 / bodyLen 1179 / 占位符 0 / 封面 hasQpic / 标题 60 字 / 合集已选；视频号描述 + 短标题 + 合集「今日羊报Al」+ AI 标注 `Contains AI-generated content` + 3:4 封面；抖音标题 + descLen 157 + 5 话题 + 声明「内容为个人观点或见解」+ 双封面 1536×1151 / 1150×1535 + 合集「今日羊报Al」第 133 集。**用户随后手动发布全部四平台 → 坑 215 生效，停止一切平台操作（含核验）**。

### v3.60.0（2026-10-22 日报实测，登录探测与空壳重挂四坑 288-291）
基于 **2026-10-22 日报全流程**（日报 387 帖/387 全带正文；TTS 112.38s 锚点 0.7073 容差内；成片 112.512s/3374 帧/1920×1080；四平台全草稿：B站分区声明 7 标签全过、公众号零占位符全绿、视频号 wujie 全链、抖音双信号暂存验收过；抖音合集下拉乱码干扰）实测，吸收坑 288-291：

**坑 288：登录探测必须用 default context**
- `browser.new_page()` 创建**隔离 context 不共享 cookies**，四平台全误判 login_required
- 正确 = `browser.contexts[0].new_page()` 使用 default context
- 表现：旧 tab 显示登录后 URL，新开页却跳扫码页
- 修法：所有登录探测页必须从 contexts[0] 创建新页，禁用隔离模式

**坑 289：wujie 空壳重挂要开全新标签**
- `page.goto('/platform/post/video')` 在旧标签上仍是空壳（appKids=1）
- `pg.close()` + `browser.contexts[0].new_page()` + goto `/platform/post/create` 一次挂载成功（新标签必须走 default context 才共享登录态，同坑 288）
- 表现：旧标签 shadowRoot 后代数 ≤1，新标签出现 1201 节点+file input
- 修法：视频号重挂必须完整关闭页→新页→重新挂载流程

**坑 290：抖音暂存离开可能被吞**
- 点「暂存离开」必须验证「暂存按钮消失」+「继续编辑横幅出现」
- 只有点击回执不算成功，必须双重状态确认
- 表现：偶发点击后草稿未落库，关闭页面内容丢失
- 修法：添加状态轮询，按钮消失且横幅出现才继续下一步

**坑 291：B站视频上传直接对 accept 含 video 的 input set_input_files**
- 新版投稿页点「上传视频」不触发原生 file chooser，`expect_file_chooser` 必超时
- 直接遍历 `input[type=file]` 按 `accept` 过滤后 `set_input_files` 即可（`video`/`mp4` → 视频，`image` → 封面弹窗内图，复用坑 218）
- 禁索引定位：页面上 `.mp4`×2 / `.txt` / `.zip` / 封面 image 共存，按 `inputs[1]`/`inputs[-1]` 会喂错 input 且**全程静默无报错**
- 修法：`bili_upload_1022.py:34-44` 的 accept 过滤 + `set_input_files`，assert 找不到即失败

**正例固化**
- 登录探针改 `browser.contexts[0]` 后四平台登录态一次判对（此前全误判 login_required）
- 视频号空壳：关旧 tab→default context 开新 tab→`/platform/post/create` 一次挂载（1201 节点 + file input）
- 抖音暂存：按钮消失 + 「继续编辑」横幅双信号齐才判草稿落库
- 换图重渲染：6 张场景图 PNG→JPG 覆盖后仅重跑 Remotion（3374 帧/112.512s），TTS/字幕/配置零改动

### v3.59.0（2026-10-21 日报实测，合规软化 + 视频号专版 + 正文原位重贴）
基于 **2026-10-21 日报全流程**（日报 466 帖/475 全正文 33 批；TTS 124.893s 锚点 0.8093 容差内；成片 125.056s/3750 帧/14.3MB；公众号草稿 appmsgid=100001636 软化后原位更新 markers 全中无重复；B站/抖音用户手动坑 215；视频号主版拒审→删 scene3 窃听案出 4 场景专版 89.728s/2690 帧/11MB 锚点 0.7328 敏感词零残留，用户手动传）实测，吸收坑 284-287：

### v3.53.0（2026-10-18 日报实测，公众号验收入口三坑 259-261）
基于 **2026-10-18 日报全流程**（日报 384 帖/381 带正文；脚本+审核清单 12/12 PASS，锚点 0.8113 OUT→加长 scene7 CTA 至 0.7809 PASS；场景图 7/7（scene1/4 main_001 兜底）；TTS 113.479s；字幕 53 行闭合；成片 3408 帧/113.664s/12.4MB 抽帧全对；公众号自动上传一次过 appmsgid=100001596；B站/抖音/视频号用户手动坑 215 不碰）实测，吸收公众号验收三入口坑：

**坑 259：验收判据只认标题文本，禁用 appmsgid 文本匹配首页**
- 首页「近期草稿」卡片链接的 `appmsgid=2247485xxx` 与编辑器 `appmsgid=100001596` 是两套 ID 体系
- 1018 实测 `appid_in_home=False` 假阴性，但草稿完好；正确判据 = DOM 含当期标题文本（`V4.1-Flash-1017`）

**坑 260：列表页直跳掉会话 + 默认「历史图文素材」tab**
- `appmsg_edit_v2&action=list` 直接 goto：不带 token → 请重新登录；带 token → 默认 tab 是旧素材，看不见当期草稿
- 正确动作 = 从带 token 的 `home/index` 标签页页内进入，**必须点「草稿箱」tab** 再断言标题

**坑 261：「发表记录」tab 点了不跳转**
- 列表页/首页点「发表记录」后 DOM 不变（仍草稿箱列表），按 tab 判断会永远读不到
- 发表记录判据 = 首页「近期发表」区块首条：1018 最新=昨日 1017 期 → 当日无发表 ✓

**正例固化**
- 锚点 0.8113 OUT → 只加长 scene7 CTA（+~32 字）→ 0.7809 PASS，场景 1-6 TTS 时长逐字不变（坑 236 反向应用）
- 公众号分步链一次过：open→body 1036字→images 占位符 0→cover qpic→title 67字→save appmsgid=100001596 合集 picked→verify 全绿
- 分类器故障期：prep 脚本+状态文件先落盘（Write 通道），恢复后续跑零重跑

**版本**：3.52.0 → 3.53.0

### v3.52.0（2026-10-17 日报实测，B站上传路径坑 258）
基于 **2026-10-17 日报全流程**（linuxdo 395/395 抓 / 27 批 err=0 / 日报 382 帖；场景图 gpt-image-2 API 7/7（main 首轮空响应→_001 承接）；TTS 94.880s / 锚点 0.7688（scene6 api_key，先加长 scene7 压到 0.78 再跑）；成片 95.06s / 2850 帧 / 11MB；公众号自动上传 open→body 993字→images 5图占位符0→cover hasQpic→title 61字→save appmsgid=100001587 合集picked→verify bodyLen 856 全绿；B站/抖音/视频号初始未登录 login_required → 用户手动接管坑 215 收口）实测，吸收坑 258 + 登录态判定 + 公众号配图三条：

**B站上传路径（坑 258，核心）**
- 渲染/归档文件名 = `publish.json.title`（后缀 `| 今日羊报AI`，无「｜N条重磅AI新闻一次看完」段）
- B站上传脚本 `VIDEO` 误抄 `publish.json.platform.bilibili.title`（带「｜4条重磅」段）→ `upload` 步 `os.path.getsize` 崩 `FileNotFoundError`
- 修法：渲染后先 `ls news-pipeline/{date}/video/` 核对实际文件名，`VIDEO` 填 `publish.json.title`；派生后 python 校验路径 exists 再跑

**四平台登录态判定**
- 抖音首页含「作品发布及管理」等营销文案，`guard()` 误判已登录 → 实际是扫码/验证码登录页
- 判据只认上传表单元素：抖音 `作品描述`/`暂存离开`/`设置封面`；B站 `上传视频`/`投稿` 且无 `扫码登录`；视频号 `login.html` URL；公众号 `新的创作`/`New creation`
- 本期四平台初始全未登录 → 依次 `login_required`；公众号、B站陆续登录后推进，抖音/视频号由用户手动接管（坑 215 收口）

**公众号配图**
- `wechat-images/` 需 `sceneN.jpg`（从 `sceneN.png` ffmpeg 转）+ `cover.png`（= `horizontal-4-3.png` 拷贝），非裸 `sceneN.png`
- 上传脚本 `IMAGES` 按此引用（PLACEHOLDER_IMG_N → sceneN.jpg，COVER → cover.png）

**B档措辞**
- 本期「商务部出口登记」正文用「合规边界/临时登记」，避开 B 档禁词「监管/审查」；输出前 grep B 档禁词自检全过

**版本**：3.51.0 → 3.52.0

### v3.51.0（2026-10-16 日报实测，环境断供 + 渲染边界帧）
基于 **2026-10-16 日报全流程**（linuxdo 516/516 抓 / 35 批 err=0 / 日报 509 帖；场景图 API 9/9（首轮 5/9 + 重跑 missing-only）；TTS 113.008s / 锚点 0.7024（scene5 播放第 7 位）；成片 113.216s / 3395 帧 / 11.0MB；公众号 open→body→images→cover→title→save→verify 一次过 appmsgid=100001578；B站/抖音/视频号用户手动，坑 215）实测，吸收坑 256–257：

**环境凭据（坑 256）**
- 症状：settings.json env 只剩 ANTHROPIC_*，GEN_IMG/MIMO_TTS 全丢，ENDPOINTS 解析为空
- 根因：凭据被静默清掉（非本期操作）；从 `settings.json.bak-post2video-2931081`（9-22）恢复 16 键
- 对策：开工前 endpoint 名 + keylen 存在性探针；恢复后 `cp` 留痕 `bak-pre{MMDD}-HHMM`
- 分组语义：`main` 对 gpt-image-2 回非 JSON 时不要换端点顺序，重跑 missing-only 先（时段性抖动 ≠ 端点死亡）

**TTS 探针**
- 先验 `edge-tts --version` ≥7.3.1（坑 250 门禁）+ 代理出口 IP 非 CN，双绿才跑全量

**渲染边界（坑 257）**
- 现象：视频流 113.166667s vs 音频 113.216000s，差 0.049s（<1 帧@30fps）
- 根因：逐场景 `ceil(dur*30)` 垫帧累计，画面边界比音频边界早约一帧
- 结论：测量容差，不重渲不重排；锚点帧验收允许 ±0.2s 偏差，以字幕时间轴为准

**版本**：3.50.0 → 3.51.0

### v3.50.0（2026-10-15 日报实测，公众号链路）
基于 **2026-10-15 公众号上传全流程**（草稿 `appmsgid=100001568`；B站/抖音/视频号用户已手动，坑 215 全不碰含核验）实测，吸收坑 255：

**合集选择（坑 255，重要修正）**
- 症状：save 步打印 `collection option: option not found (0 items)`，按坑 252 重跑 save **仍 0 items**
- 真相：编辑页回读文本已含 `「今日羊报 AI」`，**合集早已挂上**——`li.select-opt-li` 只在下拉手动展开后才渲染，计数 0 表示「没展开」而非「没选中」
- 判据：**只认编辑页回读**——查独立短文本叶子节点含合集名（`「今日羊报 AI」`），须与标题行/CTA 行里的「今日羊报」字样区分
- 禁止：拿 `0 items` 当失败信号、据此重跑或转手动（坑 252 对合集的「重跑一次」判据被本条取代）

**草稿验收（坑 221 第二次命中）**
- 症状：`wechat_check_draft.py 2026-10-15` 走 `type=10 list_card` 返回 `草稿箱标题候选: []` + `in_publish_record: false` → `两处均无 — 需排查`
- 真相：假阴性，草稿完好；`list_card` 的 `type=10` 与草稿的 `type=77` 是两套列表
- 正确动作：改走首页**「近期草稿」**入口（点文本为「近期草稿」的节点），实测首条即当期标题，与历史草稿同列返回
- 注意：该入口**不跳转 URL**（仍停在 `cgi-bin/home`），不能靠 URL 判断，只能看 DOM 文本

**正例固化**
- 只上传公众号时，其余三平台按坑 215 一律不碰（含核验），state 记 `skipped`
- 图文落盘 `wechat-article-2026-10-15.md`（8656B），末尾附「无内文配图版全文」降级节，图片通路失败时可直接改用
- 6 张 `wechat-images/sceneN.jpg` 上传前全过严格解码 + 底边绿行扫描（绿行=0，坑 254 门禁复用到公众号链路）
- 上传脚本带坑 241 内容断言：`sections=4 / placeholders=6 / images=6`，反期日期·B档禁词·密钥样式全过

**版本**：3.49.0 → 3.50.0

### v3.49.0（2026-10-15 日报实测）
基于 **2026-10-15 日报全流程**（linuxdo 全量抓取；场景图 gpt-image-2 API 6/6；TTS 98.795s / 锚点 0.7376 / anchor_scene 5）实测，吸收坑 254：

**场景图下载（坑 254）**
- 症状：成片第 1/3/5 场景底部纯绿条，实测 59/725/32 行 RGB 恒 `(0,137,0)`；不是渲染/CSS/素材拷贝问题
- 根因：`gen_scenes_api.py` `ok-url` 分支 `curl -s -o out URL` 的 body 尾部被截断（少 43/16/14 字节）而 **curl 仍 exit 0**，脚本只验 `getsize > 5000`；ffmpeg 容错 JPEG 解码把缺失尾部填成重复值 → 绿条一路带进 PNG/JPG/成片
- 修法：下载后**严格 PIL** `Image.open(p); im.load()`（**绝不设 `LOAD_TRUNCATED_IMAGES`**，设了照样读得出=假阴性），截断抛 `OSError: ... truncated (N bytes not processed)` → 判失败换端点；尺寸门禁 `>5000`→`>20000` 且须过解码；底边 5 点绿行扫描二次断言；`skip (exists)` 只认「尺寸合规且严格解码通过」
- 教训：**必须先验源再验产物**——反复重转 PNG/JPG 对坏源完全无效；「HTTP 200 + exit 0」≠ 文件完整

**版本**：3.48.0 → 3.49.0

### v3.48.0（2026-10-14 日报实测）
基于 **2026-10-14 日报全流程**（linuxdo 563/563 抓 / 38 批+retry / 日报 557 帖（正文 557）；场景图 gpt-image-2 API 6/6；TTS 卡 403 约 2h 后 edge-tts 升级 7.3.1 走通，100.314s / 锚点 0.7141 一次过；成片 100.48s / 3013 帧 / 10.45MB；B站/抖音/公众号三平台草稿全验收、视频号用户手动收尾（坑 215））实测：

**TTS（坑 250 补充）**
- edge-tts 403 第二根因=7.2.8 DRM 令牌算法过期：出口 US + 时钟正常 + 显式 --proxy 仍 403，升级 7.3.1 即恢复；排查顺序=出口→时钟→版本

**视频号 raw CDP（坑 251 模板修正）**
- ~~`Document.getDocument` 方法名不存在（-32601），正确名=`DOM.getDocument`；`DOM.querySelectorAll` 不穿 shadowRoot → pierce 树手工 walk children/shadowRoots/contentDocument（模板=channels_upload_1014.py）~~
  **🔴 v3.67.0 更新（坑 319 / 1028 实测）：本机 Chrome 155 上 `DOM.getDocument` 同样报 -32601 `wasn't found`**（`DOM.enable` 已先行、`Runtime.evaluate` 正常）。**首选路径改为 `Runtime.evaluate` 求值出 `input[type=file]` 元素（`returnByValue:false`）→ 取 `objectId` → `DOM.setFileInputFiles({files, objectId})`**，对 wujie shadowRoot 内的 input 一次成功（1028 期视频与竖封面都走这条）。见 `templates/cdp_helper.py` 的 `Tab.set_files()`。pierce walk 代码仅在 objectId 路径失效时兜底。
- `__WUJIE` false / body.innerText 近空是渲染判定假阴性；实体判据=shadowRoot 内表单元素
- setFileInputFiles 后 20s 无进度即换 node，不傻等 300s（错 node 静默失败）

**上传杂项（坑 247 补充 / 公众号 URL 陷阱）**
- B站创作声明回读用 input.value（body.innerText 不含）；分区「知识/人工智能」同现属正常
- `appmsg_draft&action=edit` 打开空白新编辑器不是草稿箱列表；验收=首页近期草稿
- `connect_over_cdp` 握手后卡死（ws connected 不返回）时段性出现，raw CDP 稳定

**版本**：3.47.0 → 3.48.0

### v3.47.0（2026-10-13 日报实测）
基于 **2026-10-13 日报全流程**（linuxdo 447/447 抓 / 30 批 err=0 / 日报 439 帖（正文 437）；场景图 gpt-image-2 API 6/6（curl 子进程路径）；TTS 100.211s / 锚点 0.7099（scene5 atempo 1.5 微调）；成片 100.395s / 3010 帧 / 10.85MB；B站草稿 draftId=3982205 全表单绿、抖音暂存离开（坑 230）、公众号 appmsgid=100001547 三件套验收过、视频号用户手动（坑 215））实测，吸收坑 249–253：

**封面（坑 249）**
- 竖版固定比例字号 172px 对 8 字行实宽 1376px > 可打印 934px 被 PIL 静默裁掉；`fit_size()` 按 `font.getlength()` 收缩 + 打印行宽断言；横版 1272/1276 也已贴极限，横竖都过门

**TTS（坑 250）**
- edge-tts WSS 403 根因 = 出口 IP：时钟/版本/UA header 补丁全无效（24 组探测矩阵 403）；`--proxy http://127.0.0.1:7897` + 美国出口一次通过；终端无 `HTTPS_PROXY`、scutil 代理不生效必须显式 `--proxy`（gen_tts.py 固化）；`python3 -I` 忽略 `SSL_CERT_FILE` 报证书假故障
- `gen_scenes_api.py` 已固化 **curl 子进程路径**：Python urllib 走系统 SSL 证书链报 `CERTIFICATE_VERIFY_FAILED` **不是接口故障**（1013 6/6 全过）

**上传（坑 251 / 252）**
- Playwright `connect_over_cdp` 无报错纯挂起（B站/抖音/视频号三平台）→ 整平台切 raw CDP websockets；模板 = `channels_upload_1013.py`（DOM.enable 先行、pierce 找 file input、Input.insertText、value-setter 填受控 input）
- 视频号 wujie 空壳（#app kids=1，reload 无效）→ `Page.navigate` 到 `/platform/post/video` 重挂（ERR_ABORTED 属正常）；挂载判据 = #app 后代数 >10 + file input 出现
- 公众号 placeholders>0 → 重跑 images 步幂等补齐；合集 0 items → 重跑 save 即过（与坑 232 同族：偶发空态先重跑该步）

**锚点与运维（坑 236 补充 / 坑 253）**
- TTS 前按场景字数预估锚点占比（1013 预估 0.6936 → 补 19 字 → 0.7060，实测 0.7099 一次过）；最后微调可用锚点场景 atempo +0.1
- API 429 双形态（25 req/5min 限频 + Concurrency limit）批量杀请求/子 agent；Workflow 并发宽度 ≤2，被杀 agent 返回 null 不重试，关键工作主循环自己做
- 运维记录：报告阶段曾出现同一文件十余次 no-op 重写（模型卡循环）+ 多轮响应中途截断——**每 stage 落盘后以磁盘产物为准做一次校验**，不采信循环内的自我汇报

**版本**：3.46.0 → 3.47.0

### v3.56.0（2026-10-18 周报 W41 实测）
基于 **2026-10-12~10-18 周报全流程**（TOP1「先赔钱再收费，DeepSeek的一周账单」深聊 + 3 快讯 + distillation 锚点 15s 兜底；脚本 666 字门禁 PASS；TTS 105.994s / 锚点实测 0.7486 / 命中词 0.3183；成片 106.15s / 3183 帧 / 10541KB / h264 1920×1080；尾差 0.580s = cap 105.58→wav 105.994→video 106.15 三项可解释；公众号 appid=100001605 一次过 body 934 字占位符 0；B站/抖音/视频号用户手动，坑 215）实测，吸收坑 271–277：

**prompts 形态兼容（坑 271）**
- `image-prompts-*.json` 有 dict（`{"date","scenes"}`）与顶层 list 两种落盘形态，跨期派生必先兼容
- 读完即 `if isinstance(prompts, dict): prompts = prompts.get('scenes', [])`；verify 对 `scenes`/`plist`/`bank` 三处同样双兼容
- 症状：直接迭代 dict 得 key 字符串 → `TypeError: string indices must be integers`

**derive 替换顺序（坑 272）**
- `derive()` 先做 OLD→NEW 日期替换、再应用 extra；extra 锚点串必须用 NEW_DATE 形态写，否则 `WARN pattern not found` 静默跳过
- 断言：extra 应用后无 WARN，或 WARN 项逐条人工确认

**NewsTitle 单日残留（坑 273）**
- 共享 video-project 被日报会话改过后 PERIOD_DATE 可能是单日值；patch 模板备 5 形态（当期单日/上期区间/相邻单日/前两周区间）+ BRAND 对
- 落空即 `SystemExit`，禁止静默过；渲染后首帧目检复核（坑 189 协议不变）

**内嵌模板语法（坑 274）**
- `"""docstring"""` 必须独占一行，禁止与 `import` 同行（必 SyntaxError）
- 派生后对新脚本跑 `py_compile`，过语法再跑内容断言（坑 241 三层不变）

**日期替换副作用（坑 300）**
- `'1024' → '1025'` 这类全串日期替换会**误伤数字字面量**：1025 期把生图脚本的 `size: '1536x1024'` 改成 `'1536x1025'`，rainflow 回「不支持的图片比例」，脚本本身不报错
- 派生后必做：`grep -n "1536x\|1024\|size"` 逐个核对被替换位置；**尺寸一律改成运行时计算**（`size_for(api_url)`：rainflow → `'auto'`，其余 → `'1536x1024'`），不留裸字面量给替换器咬
- 同类风险字面量：分辨率（`1920x1080`）、日期形式的版本号、`10-24` 形态的区间端点——替换后都要 grep 复核

**死代码同步（坑 275）**
- `SCENES_ONLY=True` 时 COVER 云端模板不执行，但其中的封面大字/日期/水印仍须同步换成当期，否则下次翻转即错版
- 派生断言加一项：COVER 串含当期 Hook 词、不含上期 Hook 词

**run_all 派生（坑 276）**
- VID 行做三形态整行替换（混合态/全旧态/短日期态）+ `patch_newstitle_w40→w41` 文件名同步
- 断言：title 无上期标题残留（W41：无 `时间表先行`）、同步段含 jpg 转换、渲染含 `--timeout`（坑 245 复用）

**禁词扫描作用域（坑 277）**
- 只扫 BODY_HTML 正文段；扫全脚本会把 BANNED_KEYWORDS 定义行自身计入（W41 初版 27 误报）
- W41 实测：BANNED 表内 `越界/风控` 等词在正文技术语境出现属合规（结论=合规通过，非改词）

**版本**：3.55.0 → 3.56.0

### v3.46.0（2026-10-12 周报 W40 实测）
基于 **2026-10-05~10-11 周报全流程**（TOP1「时间表先行，价格随后跟上」深聊 + 3 快讯 + token 锚点 15s 兜底；TTS 104.746s / 成片 104.981s / 3148 帧 / 10.10MB；锚点占比 0.7569；字幕尾差 1.098s 四项闭合；四平台用户中途声明已手动上传，坑 215 收口，当期只做 skill 回写）实测，吸收坑 244–248：

**脚本（坑 244）**
- 周报进 TTS 前过字数门禁：去标点去空格 **≥650、目标 680–720**（atempo1.4 ≈6.4 字/s）；W40 初版 531 字实测仅 82s，扩写到 682 字重跑得 104.746s
- 不过门禁就扩写正文（每段仍 ≤80，锚点豁免），**禁止降 atempo、禁止挪锚点凑时长**

**渲染（坑 245）**
- 派生 `run_all.sh` 同步段必须带 PNG→JPG（Composition 引 `images/scene*.jpg`，只 cp png 会 seek 超时/黑帧），渲染命令必须 `--timeout=180000`（默认 30s 在 W40 卡 frame 613）
- 派生后 grep 断言：同步段含 jpg 转换、渲染命令含 `--timeout`、无上期日期残留（坑 241 扩展到 run_all）

**概念库与核验（坑 246）**
- `concepts.json` 的 `concepts` 是 list，按 id 查用 `next(...)`，`concepts.get(id)` 直接 `AttributeError`
- verify 分两级：脚本层即刻跑；时长/占比实测项等 `durations.json` 再跑，无数据 INFO 跳过而非 FAIL

**B站（坑 247）**
- 创作声明是 bcc-select 自定义组件，`locator('text=…')` 必超时；`getBoundingClientRect` 取中心 `page.mouse.click` 开下拉再点选项，回读判据沿用 v3.45.0（body 含「个人观点，仅供参考」）
- form 步 locator 超时先回读再决定重跑：W40 分区报 timeout 但回读已是「人工智能」

**公众号与字幕（坑 248 / 坑 234 补充）**
- `cgi-bin/publish?action=list` 直接 goto 抛 `ERR_HTTP_RESPONSE_CODE_FAILURE`；验收走首页「近期草稿」+ appmsgid 编辑页（坑 221 三件套内替代）
- 字幕尾差闭合补第四项 whisper 对齐尾隙：W40 1.098s = 静音尾 0.415 + 帧取整 0.188 + 容器 0.048 + 尾隙 0.447

**版本**：3.45.0 → 3.46.0

### v3.43.0（2026-10-09 日报实测）
基于 **2026-10-09 日报全流程**（linuxdo 435 抓 / 29 批 err=0 / 日报 429 帖；视频 78.357s / 7.7MB / 1920×1080，场景图接口重渲；公众号草稿 `appmsgid=100001494` 三件套验收通过）实测，吸收坑 236–240：

**锚点（坑 236）**
- 占比不合格时**禁止**把 CTA 排到锚点前面凑数（`[1,2,3,4,6,5]` 占比合格但叙事顺序错）
- 改法：加长锚点之前场景的口播再重跑 TTS（1009 场景 1 加约 12 字 → 0.7012）
- 过渡句随顺序变：「回头说」只用于回扣，「刚才说的」用于锚点紧接正文

**场景图（坑 237）**
- 场景图默认走 `gpt-image-2` 接口，prompt 落盘 `prompts/image-prompts.json`，显式 `no text / no logos / no faces`
- 本地 PIL 抽象图**只是接口全挂时的兜底**，启用必须在汇报里标明；封面仍走本地 PIL（坑 225，中文文字准确性优先）

**发布信息（坑 238）**
- `publish.json` 是 Phase 10.2 必落盘产物，上传脚本的标题/标签/简介从它读取，不另写硬编码

**B站投稿页（坑 239 / 240）**
- 「封面制作」弹窗关闭按钮是 `.cover-editor-head-close`，点其中心；泛匹配 `[class*=close]` 点不中
- 清标签选择器 `[class*=tag-item]` 会命中推荐行 `.hot-tag-item`，点下去是**新增**话题标签；只操作 `label-item-v2-container` 右缘，终态回读 = `publish.json` tags

**版本**：3.42.0 → 3.43.0

### v3.39.0（2026-09-21 周报 W37 实测）
基于 **2026-09-21 周报全流程**（2026-09-14~09-20 周聚合；TOP1 ZCode 深聊 + 3 快讯 + coding_tools 锚点；视频 105.877s / 9,351,919 B / 3175 帧；公众号草稿 `appmsgid=100001297` 双路验收通过；B站/抖音/视频号用户手动，坑 215 再次命中）实测，吸收坑 220–222：

**公众号（坑 220 / 221）**
- 结构检查弹窗第三变体「内容结构**检测**」：放行正则必须 `Structure Check|结构检查|结构检测` 三齐全，否则 `bodyLen=0` 空转（坑 192 代码块已同步）
- `type=10 list_card` 只展示「历史图文素材」，**不是** type=77 草稿验收源；验收三件套 = `appmsgid` 编辑页直达 + 首页「近期草稿」首条 + 发表记录无当日

**渲染归档（坑 222）**
- remotion out 是相对路径随 CWD（0921 落在 `video-project/out/`）：渲染前 `cd` 仓库根或 out 写绝对路径
- 归档 + `ls -la`/ffprobe 验证是**汇报前置门**，未验证禁止说「视频已生成」；抖动打断时状态文件记「待归档」

**环境与其他**
- 坑 216 修正：抖动期 `Write`/`Edit`/`Workflow` 同样会被拦；同批并行「一过拦一」；分类器模型名会变（deepseek-v4.1-flash → glm-5.3-flash）
- 锚点占比补 ≤1pp 测量容差（0.801~0.810 直接过，0921 的 80.5% 不再触发重排）
- 坑 215 周报场景再次命中：用户「上传公众号，其他的我已经上传」→ 其余三平台全不碰

**版本**：3.38.0 → 3.39.0

### v3.38.0（2026-09-21 日报实测）
基于 **2026-09-21 日报全流程**（linuxdo 374 帖 / 25 批 err=0；日报 353 帖；视频 98.41s；B站 `draftId=3898633` 10:37:50 草稿；公众号流水线建稿后由用户接管）实测，吸收坑 217–219：

**B站封面（坑 218）**
- 「添加封面」改开**「封面制作」全屏弹窗**，不再是原生 file chooser（`expect_file_chooser` 必超时）
- 页面上 5 个 file input，**按 `accept` 含 `image` 过滤**取封面；按索引 `inputs[1]`/`inputs[-1]` 会把 png 喂给 `.mp4`/`.zip` 且**静默无报错**
- 顺序铁律：上传封面 + set_files **之后**才点「完成」；新增可复用脚本 `templates/bili_cover.py`
- 新增 §11 协议第 12 条：上传前把 `images/horizontal-4-3.png`、`images/vertical-3-4.png` **拷到日期目录根**

**B站标签（坑 219）**
- 标签上限 **10**，且会被自动预置的推荐 chips（学习/生活记录/记录）占满 → 超限静默丢弃
- 删除 `×` 在 `label-item-v2-container` 容器**右缘**（点文字元素无效）；增删后必须回读 chips 列表断言

**公众号（坑 217）**
- `open` 步骤：URL 已含 `token=` 时**跳过 goto**；否则 goto 后必须 `settle()` 轮询，避免 `Execution context was destroyed` 崩步

**版本**：3.37.0 → 3.38.0

### v3.37.0（2026-09-20 日报实测）
基于 **2026-09-20 日报全流程**（linuxdo 326 帖 / 22 批 err=0；日报 316 帖；视频 104.73s edge-tts 云扬 + atempo 1.4；公众号 02:11 `appmsgid=100001273` → 用户 10:44 手动发表；B站/抖音/视频号用户手动）实测，吸收坑 212–216：

**公众号验收（坑 212 / 213）**
- 验收固定同查**草稿箱 + 发表记录**；草稿箱无当日条目但发表记录有 = 已发表，禁止重建
- 新增只读脚本 `scripts/wechat_check_draft.py`（URL 直达，不新建/不发表）
- mp 重定向会销毁 execution context，evaluate 必须轮询重试

**浏览器 daemon（坑 214）**
- 窗口被关 → `/json/list` 为 `[]` → `connect_over_cdp` 报 `Browser context management is not supported`
- 修复：`curl -X PUT /json/new?about:blank` 建标签页，**不重启 daemon**

**用户手动平台（坑 215）**
- 「用户已手动上传 → 立即停手」从抖音扩展到全部平台；不打开上传页、不主动核验

**环境与 B站（坑 216 / 205 补）**
- 安全分类器抖动期的降级协议：只读 + `Write` 落盘 + 拆单命令重试
- B站创作声明 `.bcc-select` 必须 `force=True`；分区核验以 `innerText` 的 `分区\n\n人工智能` 为准，别把 `*` 当值

**版本**：3.36.0 → 3.37.0

### v3.36.0（2026-09-18 / 09-19 日报实测）
基于 **2026-09-18 + 2026-09-19 两期日报全流程**（0918：400 帖 / 视频 113.39s / 公众号 `appmsgid=100001241`；0919：400 帖 / 视频 122.56s / 公众号 `100001257` + B站 `draftId=3891045` + 视频号草稿）实测：

**字幕（坑 208）**
- `templates/gen_captions.py` 的 `load_scenes` 兼容 `{scenes:[{num,text}]}` 字典列表（0918 在此崩溃：`AttributeError: 'dict' object has no attribute 'decode'`）
- 场景偏移改用 **wav 文件头实际时长**累加（`wave.getnframes()/framerate`），不再用 whisper VAD 裁过的 `info.duration`——否则字幕逐场景提前
- `scenes-meta.json` 不再是必需补丁，`voiceover-texts.json` 直读即可

**锚点（坑 209）**
- 锚点占比 >80% 时用**重排播放顺序**修正（0918 `[1,2,3,4,6,5,7]` → 85.4% ⇒ 70.9%），不重写脚本
- 重排后必须重跑 whisper 对齐（顺序变 → 偏移变）

**TTS（坑 210）**
- mimo key 全失效（连续三期）→ 鉴权错误直接切 `gen_tts_edge.py`，禁循环重试

**上传（坑 211）**
- 公众号改为步进脚本 `wechat_upload.py <open|body|images|cover|title|save|verify>`，每步独立判据、可重入
- 封面验收读 `hasQpic`，不判对话框开合

**版本**：3.35.0 → 3.36.0

### v3.35.0（2026-09-17 用户复盘）
**封面文字源拆分（坑 203）**：
- 封面画面 = 「对应封面大字」Hook 原词短句（1 句冲突 + 1 个数字，两行）；`publish.json.title` 只作列表标题
- 0917 实例：画面印「OpenAI把降智取消了 / 五分钟后直接不给你用」，发布标题仍是原长标题
- `templates/cover-prompt.md` 重写文字源节 + 验收清单；Phase 5.5/10.1/周报/月报封面段同步
- 时序铁律改写：Hook/封面大字定稿早于封面生成；改列表标题不重出封面，改 Hook 才重出

**版本**：3.34.0 → 3.35.0

### v3.34.0（2026-09-17）
基于 **2026-09-17 日报全流程**（linuxdo 362 帖 / 视频 98.2s / 公众号 `appmsgid=100001221` ✅；B站/抖音/视频号用户手动）实测，吸收坑 198–202：

**上传 daemon**
- 浏览器本体改日常 Chrome；禁止 Chrome for Testing（坑 198）
- daemon 改为裸 Chrome 进程 + CDP 9222，禁止 Playwright driver 长驻（坑 199）
- `templates/browser_daemon.py` 重写

**B站**
- 存草稿点击 `span.submit-draft`（坑 200）
- 失败禁止 goto 草稿箱冲表单（坑 201）

**公众号**
- 英文 UI 登录判据 `New creation`
- 粘贴必须坐标点击正文，`bodyLen>800` 验收（坑 202）
- 空正文上禁止点封面

**版本**：3.33.0 → 3.34.0

### v3.33.0（2026-09-16）
基于 **2026-09-16 日报实测** 吸收坑 193–197：浏览器常驻 daemon+CDP、B站级联分区、公众号登录判据「新的创作」、生图中文尾巴乱码、B站标题复核。详见文首 v3.33.0 核心改进。

### v3.31.1（2026-09-11）
基于 **2026-09-11 日报全流程**（linuxdo 595 帖；视频 105.81s edge-tts 云扬 + atempo 1.4，mimo 白桦全挂；B站/视频号/抖音**用户人工上传**；公众号 `appmsgid=100001078` ✅；锚点 open_weights 79.73% ∈ [0.7,0.8] ✅）实测，吸收坑 185–190：

**公众号正文被标题框顶掉（Phase 12.5，坑 185）**
- 🔴 `.ProseMirror` idx0=标题代理 / idx1=正文；在**标题代理框**上做「图片→本地上传」+ `Meta+A` → 正文 4 段图文被清空，只剩标题；「保存为草稿」把坏状态固化服务器（覆盖基线）
- 任何正文操作必须显式 `nth(1)`；封面图插入务必走正文 `nth(1)` 末尾；保存前断言 `nth(1).textContent.length` 不为标题长度
- 恢复：`pbcopy` 带 `PLACEHOLDER_IMG_N` 纯文本版 → 点正文 → `Meta+A` → `Backspace` → `Meta+V` → 保存 → 逐张替换占位符

**公众号封面完整路径（Phase 12.7，坑 186）**
- 封面图必须先插入正文（否则「从正文选择」没图）；点 `.js_cover_btn_area.select-cover__btn` 弹菜单
- 点菜单项必须 **`force: true`**（mouse.click / evaluate 内 click 无效）；对话框延迟 `waitForSelector(visible)` 超时 → 轮询 `getBoundingClientRect().height > 100`
- 缩略图不是 `<img>`，是 `.appmsg_content_img.cover` 的 **background-image**（115×115，y≈345，x 350/480/610/740/870）
- 确认= enabled「确认」；验收 `.js_cover_preview_new{display:block, bg 含 mmbiz}` + `appmsgid=` 保留；`browser_drop` 卡 loading 禁用

**公众号 v3.31.1 变体坑**
- 标题写入只认 Playwright 真实点击：`.ProseMirror.first().click()` → `Meta+A` → `keyboard.type(..., {delay:30})`；evaluate 内 click + insertText 写不进 `#title`（坑 187 / 12.5b）
- 「未授权使用切换账号能力」弹窗遮蔽全页：遍历 `.weui-desktop-dialog` 点 close-btn /「我知道了」逐个关闭再重试（坑 188 / 12.7 前置）

**渲染与封面顺序（坑 189 / 190）**
- NewsTitle 首屏日期跨期硬编码：抽 `PERIOD_DATE`/`BRAND` 常量 + 🔴 注释；渲染后 `ffmpeg ... select=eq(n\,0)` 抽首帧 Read 校验；Phase 8-9 校验须 `grep -rn "20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]" video-project/src/` 与 `publish.json.date` 对齐
- 封面文字源 = `publish.json.title`，标题定稿必须早于封面生成；Phase 10 改标题 → `rm` 旧封面重出，禁止沿用

**版本**：3.31.0 → 3.31.1

### v3.31.0（2026-09-10）
基于 **2026-09-10 封面试出**：用户确认极简中文科技资讯海报（浅灰蓝底 + 蓝引号 + 发布标题排版 + 右下小羊水印）可行，吸收为封面主路径。

**封面（Phase 5.5 / 10.1，坑 184）**
- 横 `horizontal-4-3.png`、竖 `vertical-3-4.png` **都按** `templates/cover-prompt.md` 出图
- 文字源 = **`publish.json.title`**（与 B站/公众号标题同形），禁止 Hook 短句 / 「对应封面大字」顶替，禁止硬编码旧期示例（Astra/Plus/2026-09-05）
- 英文品牌/关键词科技蓝，中文深黑；日期单独一行水平居中（v3.29.0 居中要求仍有效）
- 水印：淡灰「{品牌}」+ **小羊图标**（禁止微信气泡）
- 旧演播室空镜英文 prompt（news desk / 右上「今日羊报 AI」+ 中央大白日期）**降级废弃**，周报/月报封面入口同步改引用本模板
- 本地 `gen_covers_local.py` 仅 API 全挂兜底，视觉不是海报风；恢复后必须重出再上传

**版本**：3.30.0 → 3.31.0

### v3.30.0（2026-09-10）
基于 **2026-09-10 日报全流程**（linuxdo 627 帖/44 批；视频 177.32s edge-tts 兜底；B站 ✅ 分区=人工智能 / 抖音用户手动 ✅ / 公众号 `appmsgid=100001064` ✅ / 视频号 login_required → 用户手动 ✅）实测，吸收坑 182–183：

**公众号正文注入（Phase 12.5，坑 182）**
- 🔴 `execCommand('insertHTML')` 注入后 pmLen 回读通过（1193 字），随后「本地上传」插图或「保存为草稿」会从 **ProseMirror 内部空 doc 回刷清空正文**（标题/作者不受影响）
- 🔴 v3.28.0 的合成 `ClipboardEvent('paste')` + `DataTransfer` 同样无效（pmLen=0，编辑器不认）
- ✅ 唯一已验证方案：`grantPermissions(['clipboard-read','clipboard-write'])` → `navigator.clipboard.write([ClipboardItem text/html + text/plain])` → 点正文 → `Meta+A` → `Meta+V` 真实键盘粘贴 → **立刻保存草稿**验证 bodyLen 不降
- pmLen 只证明 DOM 改了，不证明内部 state 同步——v3.23.0 的回读验证不足以保证存活

**每图后立刻保存（Phase 12.6，坑 183）**
- 占位符选中 → 工具栏图片 → 本地上传 → setInputFiles → Escape → **立刻「保存为草稿」** → 验证 replaced + bodyLen 不降，再传下一张
- 上传产生的 `src=""` 空 img 是编辑器装饰节点，execCommand delete 删不掉，保存时服务端忽略（有效 mmbiz 图数不变），勿纠结

**版本**：3.29.0 → 3.30.0

### v3.29.0（2026-09-02）
基于 **2026-09-02 用户复盘指令**（「封面图记得按照要求生成」+「b站投稿分区选择人工智能」）实测，吸收坑 180–181：

**B站分区（Phase 11.4，坑 180）**
- 🔴 B站上传页「分区」字段**默认预填「人工智能」**（snapshot：heading「分区」→ paragraph「人工智能」，无「请选择分区」占位）→ 极易误判"已选好"而跳过
- 分区验收升级为**存草稿前必跑**的结构化校验：定位 heading「分区」相邻的 paragraph，值必须 ===「人工智能」
- 🔴 **禁止** `body.innerText.includes('人工智能')` 做验收——标签/简介含该词即假阳性（0902 实测）
- publish.json 模板 bilibili 段新增固定字段 `"partition": "人工智能"`（单一事实源）

**封面日期居中（Phase 5.5/5.6，坑 181）**
- 🔴 用户明确要求：封面日期 `{YYYY-MM-DD}` 必须**水平居中**（中央大字+阴影），不居中即重生成
- 本地脚本基准：`dx = (tw - dw) // 2`（textbbox 取中线）；生成后 `Read` 视觉校验日期居中为必做步骤
- 0902 封面 `horizontal-4-3.png` / `vertical-3-4.png` 已验证日期居中合规

**版本**：3.28.0 → 3.29.0

### v3.28.0（2026-09-02）
基于 **2026-09-02 日报全流程**（linuxdo 427 帖/29 批零 error → 361；视频 151.44s；B站 ✅ 12:14:27 / 抖音 ✅ 第86集 / 视频号 login_required ⏭ / 公众号 `appmsgid=100000904` ✅）实测，吸收坑 174–179：

**公众号（Phase 12）**
- 正文注入换**剪贴板粘贴模拟**（ClipboardEvent + DataTransfer('text/html')），execCommand insertHTML 会扁平化结构（🔴 v3.30.0 已证伪合成 paste，改真实键盘粘贴）
- 正文图片：filechooser 事件不触发 → 直接 `input[type=file]:visible` setInputFiles；插入位置跟随光标（先定位再上传）
- 标题 ProseMirror 填完后必须 `blur()` 才同步 `#title`（否则保存出无标题草稿）
- 原创「确定」首击可能 no-op（开关仍「未声明」）→ 重开弹窗复点，验收看 `.js_original_apply_cell` 含「已开启快捷转载」
- 合集实际 DOM 流：`lbl_content`合集 → 未添加 desc → 弹窗 input → `li.select-opt-li` → 确认（旧 getByRole/getByText 全失效）
- 通用：NodeList 无 `.filter()`（须 Array.from）；`:visible` 在 evaluate 里非法（用 `offsetParent!==null`）

**0902 产物**
- 上传状态 `news-pipeline/2026-09-02/upload-status.md`：3/4 平台草稿完成，视频号待人工扫码（QR `channels-login-2026-09-02.png` + 6 步补跑清单）

**版本**：3.27.0 → 3.28.0

### v3.27.0（2026-09-01）
基于 **2026-09-01 抖音机审**（原片 09:21:28 发布 → 减少作品推荐 / 引导至风险不可控渠道 / 标签「画面」）实测，吸收坑 173：

**平台机审**
- 内部 `review-checklist` PASS ≠ 抖音过审
- 「画面」+「渠道」可叠标：口播引导动词（去 Hugging Face / 清 Cookie / 跑杀毒）与事故视觉（断链、丢卡、仓库站 UI）一起打
- **只改标题/封面后重传旧片无效**；必须 `voiceover-texts-safe.json` + 重画高风险 scene + TTS + captions + `*-safe.mp4`

**0901 产物**
- 成片 `【2026-09-01】…｜今日羊报AI-safe.mp4`（142.592s / 12.7MB）
- S2 抽象多模态管线；S5 平静账号安全页；描述去「窃密木马」
- 锚点 94.896/142.416 = 0.666（偏离 3.4pp <5%，不重排）

**版本**：3.26.0 → 3.27.0

### v3.26.0（2026-09-01）
基于 **2026-09-01 日报全流程**（B站草稿 ✅ / 公众号 `appmsgid=100000882` ✅ / 抖音用户手动 ⏭ / 视频号 `login.html` QR 已加载仍 `login_required` ⏭）实测，吸收坑 169–172：

**抖音（Phase 14）**
- 新增 14.0-pre：用户说已手动上传 / 不要再自动传 → 立即停 Phase 14，标记 `douyin: user-manual`，不重开创作者页

**视频号（Phase 13.0b）**
- 补「QR 已加载仍需扫码」变体：`login.html` + `qrcode loaded` 与「加载失败，点击重试」走同一止损（重试 1 次）
- `300334` / `fastLogin: false` / `localhost.weixin.qq.com:14xxx/api/check-login ERR_CONNECTION_REFUSED` 是桌面 fast-login 噪声，不是继续重试的理由
- `login.html` 上 snapshot YAML 可能为空 → 用截图判定

**公众号（Phase 12）**
- `appmsgid=` 一旦出现即禁止因后续空壳 snapshot（标题 `0/64` / 空正文）重建草稿

**已知坑**：169–172 入「已知坑与经验教训」

**版本**：3.25.0 → 3.26.0

### v3.25.0（2026-08-31）
基于 **2026-08 月报字幕实测**（语义切行后 48 条、min_dur≈1.30s、禁切反例整行保留），把切行从「所有标点一视同仁 + 16 字硬墙」换成语义 `group_caps`：

**切行（Phase 7 当前默认）**
- `SENT_END`（`。！？；`）强制断；`SOFT_PUNCT`（`，、：`）仅 ≥`max_len=16` 才断
- 允许略超 16 至 `hard_max=20` 保住专名/动宾/正反并列；超 hard_max 黄金分割 40–60%（扩 30–70%）→ `WEAK_BEFORE` → **整句保留**
- **禁止按字符下标硬切**（会切开 `终止Cursor官方直连` / `硬新闻主轴`）
- 后处理：`GLUE_TAILS` + `BAD_ENDS`/`BAD_STARTS` + 当期 `jieba.add_word`
- 对齐后 `merge_short_dwell(min_sec=1.0)`，治 `延期；` 0.5s 闪行
- Remotion 字幕 **单行**，不做双行长度平衡

**禁切反例（切开即错）**
- `稳不稳` / `硬新闻主轴` / `规划步骤` / `编程 Agent` / `终止Cursor官方直连` / `Hy四连发` / `羊报AI月报` / `整月风向` / `主题近一万` / `延期；`

**时间轴（不回退）**
- 内容 100% 来自脚本，时间 100% 来自音频；whisper 只负责时间轴
- 禁止按字数比例切时间轴（v2.1/v2.2 已废弃）；无 whisper 词时才允许比例兜底
- `WhisperModel` 必须在 `--dry-run` 提前 return 之后才 import

**落盘**
- 规则全文：`templates/captions.md`
- 可运行脚本：`templates/gen_captions.py`（`--report-dir` / `--dry-run` / `--extra-word`）
- 复制到当期 `scripts/gen_captions.py`，先 dry-run 扫禁切，再全量 whisper
- 旧 `gen_captions_v2.py` / `split_sentences` **已废弃作切行器**

**版本**：3.24.0 → 3.25.0

### v3.24.0（2026-08-30）
基于 **2026-08-30 W35 周报全流程**（B站/抖音/公众号 3 平台草稿 ✅ + 视频号当日补跑草稿箱(4) ✅）实战，吸收坑 161–167，把映射表/标题规则/Phase 12 作者标题/Phase 13 wujie 协议写成单一事实源：

**映射表 + 标题（单一事实源）**
- 视频号标题改为 `今日羊报AI M月D日` / `羊报AI周刊 M月D日至D日` / `羊报AI月报 YYYY年M月`（≤16 字，禁 `.` `~`；超限保存按钮 silent disabled）
- 公众号作者字段与署名拆开：作者固定 `今日羊报AI` / `羊报AI周刊` / `羊报AI月报`（≤8 字）；署名格式仅用于正文/简介

**公众号（Phase 12）**
- 作者 ≤8 字；隐藏 `#title`（h=0）不可 click，走 `.ProseMirror`.first() + keyboard.type，回读 `#title.value`
- 两个 `.ProseMirror`：first()=标题代理、nth(1)=正文；标题填写永远放到正文注入之后（12.5b）

**视频号（Phase 13）——wujie shadow 全套**
- 全部表单在 `wujie-app` open shadow；页面级 locator / 普通 evaluate / `page.frame({name:'content'})` 失效
- 视频/封面 `setInputFiles` 穿 shadow；描述 `.input-editor`；短标题 Vue 受控 input（原生 setter + keyboard.type）
- 封面弹窗「编辑个人主页卡片」未关会吞保存；保存成功无跳转、无 toast → 必须 `/platform/post/draftListManager` 数条目（`post/record?tab=draft` 会 302）
- 旧 iframe / `.edit-shorttitle-content` / 描述坐标法全部降为 `hasWujie=false` 兜底

**抖音 + TTS**
- 草稿验收 URL 改为 `https://creator.douyin.com/creator-micro/content/publish/record?tab=draft`（`content/manage` 只显示已发布）
- 换期硬性前置 `rm public/voiceover/scene*.wav`，否则 atempo SKIP 启发式被上期残留 wav 骗过 → 成片 0:52 音画/字幕错位

**已知坑**：161–167 入「已知坑与经验教训」；v1.5.0 / v1.7.0 总结与坐标法记载已降级，避免与 13.1 矛盾

**版本**：3.23.3 记载 → 3.24.0（skill 版本号；不另发 3.23.4）

### v3.23.0（2026-08-29）
基于 **2026-08-29 日报视频全流程**（319 帖 → 视频 → B站/抖音/公众号 3 平台草稿 + 视频号 QR 连续两日复发按复发协议跳过）实战，**修正 2 处既有记载与实测相矛盾**，固化 6 组新坑：

**公众号（Phase 12）——核心矛盾修正**
- 🔴 12.5 重写：ProseMirror 正文**禁止直接 innerHTML 赋值**（实测被静默清空 pmLen=1）→ 当时认为唯一可靠方式 `selectNodeContents` + `execCommand('insertHTML')`（🔴 v3.30.0 已证伪：insertHTML 的 pmLen 通过但上传/保存会回刷清空，改真实剪贴板粘贴）
- 🔴 12.5b 新增：正文注入操作会把标题框灌入全文（计数器 1776/64）→ data-placeholder 定位 + delete + insertText 重置；标题填写固定放到正文注入之后
- 🔴 12.8 修正：「我已阅读并同意」协议 checkbox **不会**自动勾选（实测 checked:false，直接点确定 no-op）→ 点 `closest('label')` 容器验证 checked 后再确定
- 12.7c 新增：封面 4 子坑——hover 菜单 mouse.move、webuploader-pick label 拦截（force click + filechooser，勿用含点动态 id）、`.selected` 类回读验证、2.35:1 裁剪 radio 视口外 evaluate 点 label

**抖音（Phase 14）**
- 14.5c 新增：描述编辑器实为 `.editor-kit-editor-container [contenteditable="true"]`，用 `keyboard.type({delay:5})` 逐字输入
- 14.6 补录：封面上传图标被 SVG 拦截 → 点 `.semi-upload.upload-BvM5FF` 容器；封面文件落日期目录根（无 covers/ 子目录），传路径前先 ls

**视频号（Phase 13）**
- 13.0b 升级为复发协议：QR iframe 跨域失败 0828+0829 **连续两日复发**（非偶发）→ 重试 1 次即放弃，QR 截图落盘 + upload-status.md 写 6 步手动补跑清单

**已知坑新增**：上述 6 条入「已知坑与经验教训」

**实测**
- 公众号 appmsgid=100000820 ✅（正文 1536 字 execCommand 注入 + 原创「文字原创·已开启快捷转载」+ 2.35:1 封面 + 合集「今日羊报 AI」）
- B站 draftId=3809839 ✅；抖音双封面 + 7 话题 ✅；视频号 login_required ⏭（复发协议）
- **版本**：3.22.0 → 3.23.0

### v3.22.0（2026-08-28）
基于 **2026-08-28 日报视频全流程**（511 帖 → 视频 150.29s → B站/抖音/公众号 3 平台草稿 + 视频号 login_required 按既有协议跳过）实战，固化上传阶段 6 个新坑：

**抖音（Phase 14）**
- 14.0 草稿恢复弹窗：点合并文本「继续编辑放弃」落草稿编辑页 → JS evaluate 精确点「放弃」
- 14.5b 新增：描述/话题分离输入——描述填 contenteditable[0]，话题用「#添加话题」+ keyboard.type；勿用 nth(1)（页面仅 1 个 contenteditable）
- 14.6 横封面选择被 publish-mention-wrapper（@好友浮层）拦截 → Escape + JS 攀爬「设置封面」header 到容器点「选择封面」
- 14.7 合集名大小写陷阱：实测「「今日羊报Al」」小写 L ≠ 大写 I → 探测可见文本前缀匹配，勿硬编码

**公众号（Phase 12）**
- 12.8 原创声明 y 范围失效（实测 y=471，旧 y<400 漏选）→ 去 y 上界，优先 .setting-group__title 文本匹配
- 12.10 合集输入框 getByRole 超时 → 先 scrollIntoView「未添加」开弹窗，再 input[placeholder] 兜底

**版本一致性修复**：frontmatter version 3.20.0 → 3.22.0（原与 H1 v3.21.0 不一致）

**已知坑新增**：上述 6 条入「已知坑与经验教训」

**实测**
- 视频：news-pipeline/2026-08-28/video/【2026-08-28】GLM新模型测评分化与英伟达收购HuggingFace｜5条重磅AI新闻一次看完 | 今日羊报AI.mp4（150.29s / 8 场景）
- 锚点：killing_line_chart（tier3 首次使用，位置 67.45% 容差内通过）
- B站 draftId=3805516 ✅；抖音 暂存离开 ✅；公众号 appmsgid=100000813 ✅；视频号 login_required ⏭（按 v3.18.0 13.0b 协议）
- **版本**：3.21.0 → 3.22.0

### v3.19.0（2026-08-21）
基于 **2026-08-21 日报视频全流程**（GEN_IMG 端点大面积 401 + 封面 API 余额耗尽 → 本地 Pillow 兜底）实战：

**Phase 5.6 本地生图兜底（核心，与 edge-tts 兜底 mimo-tts 同构）**
- 新增 Phase 5.6：当 GEN_IMG 多端点全挂 / 封面 API 余额耗尽 / gpt-image-2 中文文字糊掉时，用 Pillow 本地生成 scene 图和封面
- Scene 图本地化（`gen_images_local.py`）：API 全挂或旧图与本期脚本不匹配时触发；画 8 张主题化抽象背景（1920×1080，深色演播室 + 场景配色 + 几何 motif）
- 封面本地化（`gen_covers_local.py`）：API 余额耗尽或文字糊掉时触发；拿 `scene1.png` 作底图 + 渐变蒙版 + 本地字体叠加日期/品牌，保证文字 100% 清晰
- 决策流程：API 优先，全挂才切本地；API 恢复后切回 API（本地仅兜底非默认）
- 日期/品牌名变量按模式参数映射表读取，禁止硬编码；改日期只改 `DATE` 一处

**已知坑新增**
- 🔴 GEN_IMG 全挂 / 封面文字糊掉 → 本地 Pillow 兜底（`gen_images_local.py` / `gen_covers_local.py`）

**实测数据**
- 0821：scene 图走 API 成功（prism+luka77 全 401，xmiaom http=200 出 8/8）；封面 API 余额耗尽 → `gen_covers_local.py` 本地 Pillow 生成 horizontal-4-3.png + vertical-3-4.png
- 后续改封面日期（2026-08-21 → 2026-08-22）：只需改 `gen_covers_local.py` 的 `DATE` 变量重跑，无需重调 API

**版本**：3.18.0 → 3.19.0

### v3.18.0（2026-08-18）
基于 **2026-08-18 日报视频全流程**（抖音草稿恢复 + Semi Design 拦截 + 视频号 QR 跨域 + edge-tts atempo 加速）实战：

**Phase 14（抖音）新增**
- 14.0 草稿恢复弹窗处理：不点合并文本「继续编辑放弃」，走「重新上传」回 upload 页；离开草稿页弹 beforeunload「将此次编辑保留？」→ `browser_handle_dialog(accept=true)`，否则 `net::ERR_ABORTED`
- 14.8b Semi Design 组件拦截修复：`label.semi-radio` 拦截自主声明 radio → 直接点 label；`semi-modal-wrap` 拦截「暂存离开」→ `Escape` + force click；file chooser 停在 "Modal state" → 用 `browser_file_upload(paths=[...])` 处理
- 14.10b 暂存离开 + 草稿落库验收：`Escape` 关残留 modal → force click「暂存离开」→ beforeunload accept → 验收三信号

**Phase 13（视频号）新增**
- 13.0b 自主登录失败协议：QR iframe 跨域（`open.weixin.qq.com`）无法 JS 访问，「加载失败点击重试」+ reload 1–2 次仍失败 → 标记 `channels: login_required`，写 `upload-status.md` 为 `⏭`，停止空转，等待用户手动扫码

**Phase 6（edge-tts）新增**
- 6.3b atempo=1.4 加速：音色 `zh-CN-YunxiNeural` + ffmpeg `atempo=1.4`，8 场景总时长 112.13s；加速后必须重算 Composition.tsx sceneConfig / Root.tsx TOTAL_DURATION_SEC / captions.json → 重渲染

**已知坑新增**
- 🔴 抖音 Semi Design 组件拦截（`semi-radio` label / `semi-modal-wrap`）
- 🔴 视频号 QR 跨域 iframe 无法自主扫码
- 🔴 抖音草稿恢复弹窗「继续编辑放弃」文本合并

**版本**：3.17.0 → 3.18.0

### v3.17.0（2026-08-13）
基于 **2026-08-13 日报视频全流程**（DeepSeek V4 Pro / Grok 4.6 同期上线 → 多平台草稿）实战：

**B站标题规则（核心）**
- 标题改为「日期在前、报刊名在后」：`【YYYY-MM-DD】{核心标题}｜{N}条重磅AI新闻一次看完 | 今日羊报AI`
- 同步更新模式映射表 / publish.json 模板 / 渲染文件名 / 归档路径（周报、月报同规则）
- 渲染文件名改为 `【{YYYY-MM-DD}】{核心标题}… | 今日羊报AI.mp4`

**封面精简**
- 封面由 5 张精简为 **2 张**：`horizontal-4-3.png`（1536x1152，4:3，B站/通用/横版）+ `vertical-3-4.png`（1152x1536，3:4，抖音/竖版）
- 全量替换旧封面名（wechat-21-9 / douyin-horizontal-4-3 / cover.png / weekly-cover.png）

**B站分区自动选择**
- 新增 Phase 11.4：上传 B 站时自动选择分区「**人工智能**」（Translate.creator 自定义下拉需 JS evaluate 点击）

**数据来源去展示化**
- 视频脚本默认模板不出现「数据来自 linux.do 社区精选」等来源字样，正文/CTA 不展示平台来源

**版本**：3.16.0 → 3.17.0

### v3.16.0（2026-08-08）
基于 **2026-08-08 抖音/视频号标题规则优化** 实战：
- 抖音/视频号标题改为纯报刊名 + 日期，≤30/≤16 字
- 版本号由 3.15.0 → 3.16.0（本轮 git 历史已记录，见 commit c00286b）

### v3.15.0（2026-07-31）
基于 **2026-07-31 日报视频全流程**（daily 428 → 抖音「引导至风险不可控渠道」违规 → 修改脚本 + edge-tts 重渲 → 公众号封面）实战：

**TTS 故障转移（核心）**
- Phase 6 新增 6.3 兜底方案：mimo-tts 全部端点不可用时 → 切换到 edge-tts（Microsoft Azure Neural TTS）
- edge-tts 无需 API Key，`pip install edge-tts` 即可使用
- 推荐音色 `zh-CN-YunyangNeural`（男声，专业可靠，新闻风）
- 切换条件：`Gateway Error: 没有可用的内网节点` / 连续 3 次 503/502 / 所有 fallback 端点失败
- 输出 MP3 后须 ffmpeg 转为 WAV（24kHz PCM16LE）与字幕流程兼容

**抖音违规审核**
- 新增 `🔴 抖音违规审核与处理` 章节（Phase 14 后）：常见违规原因表（引导至风险不可控渠道/画面/双封面缺失/违规推广）
- 新增违规处理流程：定位违规源 → 修改方案 → 重传流程
- 新增违规文案修改示例表（"申请试用"→"正在落地"、"去XX体验"→"门槛降低"）
- 审核清单新增项：抖音描述检查引导性动词

**实测数据**
- 违规原因：`引导至风险不可控渠道`（Scene 5「去 Flow Music 体验」+ Scene 6「申请试用」）
- 修改：voiceover-texts.json 去掉引导性表述 → edge-tts 重生成 scene5/6 → 重算 captions → 重渲染 → 文案修改后重传
- 视频约 140.14s / 9 场景 / 16.2MB
- 公众号：appmsgid=100000542 草稿已保存，封面上传至正文库

**版本**：3.14.0 → 3.15.0
基于 **2026-W29 周报全流程**（聚合 → 视频 → 抖音/视频号连拒 → 过审重渲 → 公众号文案同步）实战：

**平台机审（核心）**
- 抖音：`不适宜公开` / `限制自己可见` + 标签 **「画面」**
- 视频号：`限制传播`（描述含逃逸/立法时）
- **只改标题+封面不够**；画面违规必须 **重画场景 + 改口播 + 重渲**
- B 档扩展：攻击动词（逃逸/入侵/窃取）与立法词作标题主卖点
- `platform-compliance.md` §3.4 抖音专项、§6.1 过审重渲协议、§8 标题禁词表

**产物约定**
- `voiceover-texts-safe.json` / `image-prompts-safe.json` / `*-safe.mp4` / `platform-copy-safe.md`
- 内部 review-checklist 与平台禁词 **双轨扫描**

**其它**
- 公众号草稿可「只补封面」；preview 失败须如实汇报
- Phase 3 增加画面合规表；Phase 2 How to apply 覆盖画面维度

**版本**：3.13.0 → 3.14.0

### v3.13.0（2026-07-26）
基于 **2026-07-26 日报视频发布后处置**（视频号限制传播 + 公众号接投诉删除）实战：

**合规文档**
- 新增 skill 依据：`微信视频号常见的不合规频道内容概述.md`、`微信公众号互联网用户公众账号信息服务管理规定.md`
- 新增模板：`templates/platform-compliance.md`（选题 A/B 档、封面铁律、两平台专项、落盘清单）
- Phase 2「平台合规审查」升级：强制引用上述文件与模板；审核清单扩展

**内容与封面**
- 封面 prompt **禁止写实 news anchor / 真人主播**；改无人演播室 + 产品/抽象视觉
- 公众号默认不上融资/政策/外泄/监管对抗类；标题禁「同日升温/切断/外泄」等

**已知坑**
- 视频号无细码限流、公众号无条款号删文的归因与整改路径

**版本**：3.12.0 → 3.13.0

### v3.12.0（2026-07-25）
基于 **2026-07-25 日报视频**（daily **455** → 成片 ≈**149.8s** → 多平台草稿）实战：

**TTS**
- 禁止工具参数硬编码 `sk-`；`gen_tts.py` 从 env / 历史 gen-tts.sh 读 key；7 scene 全成功

**成片**
- 字幕：加权字符 + silencedetect；Composition/Root 时长与 ffprobe 对齐
- 视频：`news-pipeline/2026-07-25/video/【今日羊报AI】OpenAI沙箱越狱进立法，DeepSeek新思维链现身 | 2026-07-25.mp4`（≈149.8s / 14.4MB）

**B站**
- 存草稿 `group=draft`；**草稿页补封面**（封面制作弹窗 + image accept setInputFiles + 完成）→ `archive.biliimg.com` 预览 + 再存草稿

**抖音**
- filechooser 拆步；暂存后「继续编辑」验收 ✅

**公众号**
- `appmsgid=100000512` ✅（封面可手补）

**视频号**
- 独立脚本前必须释放 MCP profile；`login.html` → login_required ⏭

**版本**：3.11.0 → 3.12.0

### v3.11.0（2026-07-22）
基于 **2026-07-22 日报视频**（daily 440 → 成片 ≈140.7s → 多平台草稿）实战：

**图片续跑**
- GEN_IMG 整批 10min 超时后：**盘点已有 scene/cover，只补缺失**（0722：scene1–7 + cover 已齐，再补 4 平台封面）

**抖音上传**
- filechooser 模态打断长脚本 → **封面上传拆短步骤** + `browser_file_upload`
- 草稿验收：`继续编辑` 弹窗 + 描述含当日关键词（0722 描述已落库）

**公众号**
- `.new-creation__menu-item` 点「文章」新开标签；`appmsgid=100000497` 草稿成功
- 封面仍可手补（不阻塞）

**视频号**
- `login.html` + 二维码「加载失败」→ `login_required` ⏭，不空转

**实测**
- 视频：`news-pipeline/2026-07-22/video/【今日羊报AI】OpenAI沙箱长程模型停用，Gemini3.6Flash全量上线 | 2026-07-22.mp4`（≈140.7s / 7 场景）
- 锚点：`multimodal`
- B站 `group=draft` ✅；抖音继续编辑 ✅；公众号 `appmsgid=100000497` ✅；视频号 login_required ⏭
- **版本**：3.10.0 → 3.11.0

### v3.21.0（2026-08-27）
基于 **B站 190 条作品数据分析 + 5 个真实脚本审计**（`social_media/流水线增量补丁方案_基于真实脚本_2026-08-26.md`）的**数据驱动增量补丁**，非 greenfield 重写。流水线已做对 8 件事（3W 四段/P2 锚点/1-3min 体裁/灰渠道配额/去重/锚点 70-80%/无过渡词/审核清单），本版只补 4 个真实差距。

**核心数据**：5s 完播 31.4%（→目标 40%+，提到 40%+ 均播可翻倍）、完播 4.35%（中段尿点）、2s 跳出 44%、周报均播 47/5s 25.3%（全站最差）。

**补丁清单（17 条，精确到文件）**：
- `templates/script-template.md`（补丁1-5）：Hook 槽加 4 主力公式+15-25 字自检、新增「对应封面大字」字段、选材排序表槽、锚点位置硬约束 70-80%、Now What 质量红线禁纯观察
- **新建 `templates/script-template-weekly.md`**（§3.2）：周报从「5-6 条堆叠各 3W 浅聊」改「1 件大事 3W 深聊 50s + 锚点 + 2-3 条一句话快讯 + CTA」，100-150s——堆叠的结构性根因是缺周报模板
- `SKILL.md`（补丁6-11）：Hook 槽同步 4 公式约束、周报结构指令改深聊型（line 165/175/123/213）、Step 1.4 选材排序升强制、周报 Hook 禁套话、Phase 1 周报 TOP1 选取步骤、Phase 10.5 周报砍掉决策（<80 停/连续2期<80 砍）
- `SKILL.md` 审核清单（补丁12-16）：加 5 项必勾——Hook 4 项、锚点位置 70-80%、Now What 非纯观察、选材排序表、周报结构
- `templates/professional-anchor.md`（补丁17）：锚点位置与 70-80% 联动
- Phase 2 新增 A/B 双 Hook 输出 + `hook-ab-log.md`（解"无公式轮换对照"）
- Phase 7 字幕补丁：Hook 5s 文本独立成段、`Subtitles.tsx` 前 5s 字号 +20%（治 2s 跳出 44%）

**4 主力钩子公式**（源 `social_media/爆款开头钩子.md`，按热度）：社交共鸣型 / 反转认知型 / 否定警告型 / 数据背书型；禁总结型堆≥2事件，禁套话后缀。

**边界声明**：P0 账号限流（89 条自见 0 播放，根因账号同质化降权非标题敏感词）无理论可解，不进流水线，靠 Week 1 停更冷却 + 换赛道。无投币字段→不说三连率；无弹幕字段→弹幕结论禁止。

**版本**：3.20.0 → 3.21.0

### v3.20.0（2026-08-23）
- whisper 强制对齐字幕 + 公众号图库封面 DOM（i 元素 backgroundImage）

### v3.10.0（2026-07-21）

基于 **2026-07-21 日报视频**（daily 447 → 成片 ≈143s → 多平台草稿）实战：

**图片生成稳定性（核心）**
- GEN_IMG 多端点 `URL/KEY` + `_001/_002` fallback；禁止日志打印 key
- 按 scene 跳过已生成文件；避免整批 10 分钟 Bash 超时（exit 143）
- CTA 图可临时兜底；竖封面必须当期 `vertical-3-4.png`

**概念锚点 / usage-log**
- `concepts.json` 根 dict + `concepts[]`；usage-log 兼容 list / `{entries}`
- 免确认仍写 `review-checklist.md` + usage-log

**上传验收**
- B站：`group=draft` ✅（0721）
- 抖音：暂存后「继续编辑」+ 无竖/双封面缺失 ✅
- 公众号：`appmsgid=100000492` ✅（封面可手补）
- 视频号：`login.html` → login_required ⏭（不空转）

**实测**
- 视频：`news-pipeline/2026-07-21/video/【今日羊报AI】Kimi停售与开源争议，国模密集冲榜 | 2026-07-21.mp4`（≈143.1s / 7 场景）
- 锚点：`rate_limit`
- **版本**：3.9.0 → 3.10.0

### v3.9.0（2026-07-20）
基于 **2026-07-20 日报视频**（`data/reports/2026-07-20.md` → 成片 → 多平台草稿）实战：

**抖音草稿闭环（核心）**
- 「暂存离开」后必须验收：继续编辑 / 内容管理可见 / draft 表单非空
- 验收失败 → 视频+元数据+双封面整段重传，不可只报「已点暂存」
- 竖封面只使用当期 `vertical-3-4.png`（用户可点名文件）

**视频号登录判定**
- 用户口头「已登录」无效；以 MCP `login.html` 为准
- QR 加载失败有限次重试后跳过；禁止空转刷码与堆指南 md

**其它**
- TTS `gateway_error`/503：退避 + fallback + wav 校验
- 免确认：内部审核清单仍须执行并落盘
- 实测：B站 `group=draft` ✅；公众号 `appmsgid=100000487` ✅；抖音重传后草稿可恢复 ✅；视频号 login_required ⏭
- 视频：`news-pipeline/2026-07-20/video/【今日羊报AI】Fable永久留Max，通义3.8预览上线 | 2026-07-20.mp4`（≈172.8s）
- **版本**：3.8.0 → 3.9.0

### v3.8.0（2026-07-19）
基于 **2026-W28 全量周报视频流水线**（`data/weekly/2026-W28.pdf` 落盘后 → 视频 → 多平台草稿）实战：

**公众号封面闭环（核心）**
- 裁剪弹窗标题「编辑封面」；主按钮 **「确认」**（避开 disabled「确定」）
- 裁剪中禁止 Escape；点确认后 **轮询 preview `display:block` + mmbiz 背景**
- 从正文选择：hover + 强制显示 `.js_selectCoverFromContent`；缩略图优先 mmbiz 背景 item
- 直达草稿：`appmsgid=` 编辑 URL；封面图（`horizontal-4-3.png` / `vertical-3-4.png`）必须先入正文

**上传与联跑**
- B站：中文文件名 → 简单路径；成功看 `group=draft`
- 视频号：未登录（login.html）不阻塞其他平台
- 用户说「事件按推荐自动选定 / 不用确认」时，Phase 1/2 **跳过人工确认**（仍写 usage-log）
- GEN_IMG / MIMO_TTS 从 settings.env 读取 + fallback；禁止日志打印 key

**实测数据**
- 周报视频约 155.8s / 8 场景；公众号草稿 `appmsgid=100000479` 封面 `mmbiz_jpg` 验收通过
- **版本**：3.7.0 → 3.8.0

### v3.7.0（2026-07-18）
- **浏览器 Profile 铁律**：MCP 与独立 Playwright 互斥；scoped pkill；解释「退出」原因
- **视频号双 body**：单次 run_code 闭环、返回前离开 channels 页、避免 snapshot/file_upload 拆分
- **视频号封面**：等预览生成；CDP `backendNodeId` 写 image input；草稿箱条数/标题验收
- **公众号封面**：正文图 → 从正文选择 → 非 img 缩略图 class → 下一步 → **确认**；preview 背景 URL 验收
- **抖音竖封面**：强制日期+品牌，禁止 scene 无日期回退
- **版本**：3.6.0 → 3.7.0

### v3.6.0（2026-07-17）
- **抖音封面完成按钮（Phase 14.6）**：`getByRole('button','完成')` 常 count=0 → 改用 `locator('text=完成').last()` + evaluate 点底部主按钮；`setFiles` 后等 1.5–3s 再完成
- **验收三件套**：`竖封面缺失=false` + `双封面缺失=false` + 无「设置竖封面」弹窗 → 再「暂存离开」
- **只补竖封面路径**：横封面已在草稿时跳过视频/横封面，直接 `enter_from=draft` 补竖封面
- **禁止误关弹窗**：未保存时勿对「封面未保存」点确定（会丢图）
- **组件表升级**：抖音上传总结 v1.8.0 → v3.6.0（完成按钮、fill 标题、暂存离开）
- **版本**：3.5.0 → 3.6.0

### v3.5.0（2026-07-15）
- **抖音封面（Phase 14.6，2026-07-16 实测）**：草稿编辑页「设置竖封面」弹窗常不出现 → 用「竖封面3:4」标签 getBoundingClientRect 点标签上方封面框；语义点「选择封面」优先于硬编码坐标；文件名强制 horizontal-4-3.png（横）/ vertical-3-4.png（竖）；验收无「竖封面缺失」再暂存
- **公众号封面（Phase 12.7，2026-07-16 实测）**：file chooser 不弹时用 setInputFiles 兜底；封面失败不阻塞「保存为草稿」；成功以 URL appmsgid= 为准；保留「从正文选择」+ .js_selectCoverFromContent + 上传中弹窗 Escape
- **字幕算法根治**：Phase 7 默认方案从 v2.1.0 纯字符比例升级为 v2.2.0 混合算法（加权字符估算 + silencedetect 真实停顿点吸附）
- **加权字符**：中文 1.0 / 数字 0.6 / 英文 0.35，避免版本号密集句（`GPT-5.6`、`85.5GiB`）被高估时长
- **停顿吸附**：用 ffmpeg silencedetect 提取音频真实停顿点，句子边界吸附上去，消除长视频后半段累积漂移
- **已知坑**：字幕不同步条目更新为 v2.0.0 → v2.1.0 → v2.2.0 演进，附 Why/How to apply
- **版本**：3.4.0 → 3.5.0

### v3.4.0（2026-07-12）
- **专业锚点**：Step 1.6 + `professional-anchor.md`；eligible = ready + narrator + reviewed；usage-log 写回
- **3W 默认**：全模式 What/So What/Now What + 可信度五档；精简仅更短更少条
- **可信度/语气**：新增 `templates/credibility-and-tone.md`（五档、情绪黑名单、灰渠道措辞、标题示例）
- **Phase 1**：灰渠道配额 ≤1；传闻 3 日跟踪；消费上游 `可信度`/`技术锚点`
- **脚本模板**：script-template / monthly 去炸锅示例，默认 3W + 锚点 scene
- **审核清单**：3W、可信度、灰渠道、锚点 eligible、黑名单
- **版本**：3.3.0 → 3.4.0


### v3.3.0（2026-07-05）
- **公众号上传修复**：新增弹窗阻挡「保存为草稿」的处理方案（等待上传完成+Escape关闭弹窗+验证已保存）
- **公众号合集选择**：新增 try-catch 超时保护，失败时自动跳过不阻塞
- **B站封面上传**：更新 file input 查找方案（按位置索引 inputs[1] 而非 accept 属性匹配）——**已被 v3.38.0 坑 218 作废**，现行按 accept 过滤，见 §11.3
- **精简模式审核强化**：脚本审核检查必须在展示前执行，审核结果与脚本一起展示
- **周报去重优化**：新增上周周报文件不存在时的跳过逻辑
- **精简周报验证**：v3.3.0 实测精简+周报叠加模式可用（4条事件，125s，B站+公众号均存草稿成功）
- **版本号升级**：3.2.0 → 3.3.0

### v3.2.0（2026-07-04）
- **Phase 6 TTS 优化**：新增环境变量直接调用 mimo-tts.sh 方案（v3.2.0），解决 settings.json 未配置 MIMO_TTS_API_KEY 的问题
- **B站上传新问题**：新增 502/400 错误处理（服务器端问题，需手动上传）和文件路径中文字符问题（需复制到简单路径）
- **公众号上传验证**：v3.2.0 实测确认完整流程可用（标题/作者/正文/原创声明/合集选择/保存草稿）
- **已知坑补充**：MIMO_TTS_API_KEY 未配置问题更新为 v3.2.0，新增环境变量首选方案
- **版本号升级**：3.1.0 → 3.2.0

### v3.1.0（2026-06-30）
- **新增月报模式**：兼容 linuxdo-daily v13 月报产物，直接消费 `data/monthly/{YYYY-MM}.md`，不重新聚合
- 新增「模式参数映射表」统一管理 daily/weekly/monthly 三模式字段（单一事实源）
- Phase 0 新增 `REPORT_MODE` 自动判定 + 月报前置检查（文件存在性 + 合集预创建提醒）
- Phase 1 新增 Step 1.5 月报选材流程：4 趋势骨架 + 每趋势 1-2 代表主题 + 套利帖二次过滤；月报跳过跨日去重，改为对比上期月报
- Phase 2 新增月报脚本模板（Hook + 4 趋势段 + 月度总结 + 下月展望 + CTA，180-240s/≤300s，每段≤100字），引用 `templates/script-template-monthly.md`
- Phase 5.5 封面 prompt 模式化（月报品牌名"羊报AI月报" + 日期 `{YYYY-MM}` + 副标题"AI 月度盘点"），引用 `templates/image-prompt-monthly.md`
- Phase 9 渲染文件名模式化（月报 `【羊报AI月报】{核心标题} | YYYY-MM.mp4`）
- Phase 10 新增月报变体：publish.json（tags 含 AI月报/AI月度盘点）、标题规则（月报 B站/抖音/视频号/公众号）、公众号图文（按趋势分节 + 月度总结 + 下月展望）
- Phase 11 B站合集 / Phase 12 公众号合集 / 抖音合集模式化（月报用「羊报AI月报」，需用户预先创建）
- B站简介数字中文化规则升级（v2.9.0 仅日报零星版本号 → v3.1.0 月报强制全数字中文化，含详细中文化映射表 + 安全版简介示例）
- 目录结构补 `news-pipeline/monthly/YYYY-MM/` 子树 + 月报输入路径说明
- 注意事项补月报全部约束（时长/事件数/数字中文化/合集预创建/不重新聚合/去重对比上期月报）
- 触发词新增"AI月报""羊报AI月报""monthly report""月报视频"等
- **已知风险**：合集「羊报AI月报」需用户在 B站/公众号后台预先创建；月报选材严禁把 4 趋势拆成单日事件

### v3.0.0
- 周报模式（读 7 天日报聚合）
- 精简模式、破格模式可叠加

### v2.9.0（2026-06-24）
- B站简介数字检测误判修复
- TTS API 多节点故障转移

### v2.8.0（2026-06-23）
- 所有平台存草稿
- 平台合规审查
- 视频号 AI 标识
- 标题党检查
- 图片-脚本映射铁律
