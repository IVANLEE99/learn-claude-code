---
name: gongyi-checkin
description: 公益站（new-api / one-api 系）每日签到自动化。读取 Chrome 书签文件夹 daily-check-in，打开每个站点完成签到，输出签到成功/失败归档（含奖励金额与余额）。触发词：公益站签到、签到、每日签到、check-in、gongyi、公益站、station checkin、签到报告
version: 1.0.0
---

# gongyi-checkin — 公益站每日签到

对 Chrome 书签文件夹 `daily-check-in`（id `6233`）里的公益站逐个完成每日签到，
产出归档报告（签到成功 / 暂时失联 / 需登录），并记录**签到金额**与**余额**。

---

## ⚠️ 关键架构决策：为什么用 AppleScript 而不用 CDP（2026-11-04 实测）

**这一节不要跳过，改动前先读。**

| 方案 | 结论 | 实测依据 |
| --- | --- | --- |
| CDP `--remote-debugging-port=9222` | ❌ 不可用 | Chrome 136+ 拒绝在**默认 profile** 上开调试端口（"user data directory is protected"）。而这些站点的登录态**只在默认 profile 里**：28 个站点中 26 个在 `~/Library/Application Support/Google/Chrome/Default` 有 cookie，仓库自带的 `mcp-chrome` profile 是 **0/28**。 |
| `playwright connect_over_cdp` | ❌ 同上 | 没有 9222 可连。 |
| **AppleScript `execute javascript`** | ✅ **采用** | 可在**任意 tab**（含非活动 tab）读取 DOM **和** 点击元素。 |

已验证的 AppleScript 能力（全部实测通过）：

| 能力 | 写法 | 结果 |
| --- | --- | --- |
| 读 JS | `tell tab N of front window` → `execute javascript "..."` | ✅ |
| 点击 JS | 同上，元素 `.click()` | ✅ |
| 跳转 | `set URL of tab N of front window to "..."` | ✅ |
| 开新标签 | `make new tab at end of tabs of front window` | ✅ |
| 批量关标签 | `repeat with i from n to 2 by -1` → `close tab i` | ✅ |

**不要**每轮重开浏览器：用户日常 Chrome 里的登录态才是关键，重开就丢。

### 🚨 致命：同时存在两个 Chrome 实例时，AppleScript 会绑错

`tell application "Google Chrome"` 按 **bundleID `com.google.Chrome`** 解析。
若有第二个 Chrome 进程（例如 `ai-news-factory` 的 `browser_daemon.py` 用
`--user-data-dir=.../mcp-chrome-* --remote-debugging-port=9222` 起的那个），
两个都注册成 `com.google.Chrome`，**AppleScript 会绑到后启动的那个**。

后果极其隐蔽：脚本照常跑、报告照常出，但打的是**没有登录态的实例**
（实测 mcp-chrome 只有 1/27 站有 cookie，日常 Chrome 26/28），
于是大面积「暂时失联」、余额读到旧值或空值。

**开工前必须先做单实例检查**：

```bash
ps -Ao pid,lstart,command | grep -E "MacOS/Google Chrome( |$)" | grep -v Helper
```

- **多于一个** → **默认自动关掉流水线实例，签完再拉起来**（2026-11-05 用户授权，无人值守场景适用）：
  1. `kill <browser_daemon.py 的 pid>`，再 `kill <mcp-chrome Chrome 的 pid>`，sleep 2 秒复查，还在就 `kill -9`
  2. 按下面「验证绑定正确」复查一遍，确认回到日常 Chrome 再往下跑
  3. 签完恢复：`nohup python3 ~/.claude/skills/ai-news-factory/templates/browser_daemon.py > /tmp/browser_daemon.log 2>&1 &`
  **绝对不要 kill 日常 Chrome**——它不带 `--user-data-dir` 参数，是唯一有登录态的那个。
  若当时新闻流水线正在上传，先判断再动手；拿不准就问用户。
- **验证绑定正确**：`osascript -e 'tell application "Google Chrome" to get name of window 1'`
  应返回**用户自己**的标签标题，而不是「New Tab」/「公众号 / 视频号助手」这类流水线页面。

**三条定位写法都无效**（都会落到同一个实例）：
`tell application "Google Chrome"`、`tell application id "com.google.Chrome"`、
`tell application "/Applications/Google Chrome.app"`。
`System Events` 查 bundle id 反而能列出真实 pid —— 可用它做诊断，但不能用来发 JS。

---

## 🚨 十四个会静默失败的坑

### 坑 1：`esc()` 折叠换行 → JS 里的 `//` 注释吃掉整个脚本

AppleScript 字符串字面量不能跨行，所以 `esc()` 把换行替换成空格。
如果 JS 里有 `// comment`，折叠后**该行剩余全部变成注释**，
IIFE 返回 `undefined` → AppleScript 报 `missing value`，
看起来像"页面坏了"，实际是脚本被注释光了。

**修法**：`esc()` 先调 `strip_js_comments()` 剥掉注释（正确处理字符串/模板字面量/正则里的 `//`），
再折叠换行。**新增任何 JS 常量后必须先 `print(js(...))` 验一次返回值不是 `missing value`。**

### 坑 2：`missing value` ≠ 页面没内容

`missing value` 是 AppleScript 的 undefined，通常是**脚本问题**不是页面问题。
排查顺序：先 `js('location.href')`（能返回 → tab 正常），
再 `js('document.title')`（能返回 → 页面在），
再怀疑 JS 表达式本身。

### 坑 3：读到的是上一个站点的页面（stale read）

导航后立刻 probe，拿到的是**还没提交**的旧文档——于是奖励/余额全是上一个站点的，
看起来完全合理。**这是最危险的坑**：数字不报错，报告全错。

**修法**：两层护栏
1. `page_identity()` 读页面自己的 `location.href`，与请求域名比对，确认文档已提交；
2. probe 后再比一次 `seen_host` vs `want_host`，不一致直接判 `unknown`。
另外每次导航都先走 `about:blank`，否则同 URL 不会重新请求文档。

### 坑 4：正文扫描找「标签→数值」会张冠李戴

`当前余额 $X`（值在后）vs `$X Current balance`（值在前）两种排版都有，
纯文本扫描会把**邻栏的数字**绑到这个标签上——实测抓到过用户 ID、累计总额、
Consumption 额（都不是钱）。

> 上面的金额是**示例形态**，不是真实账户余额；本仓库不记录任何真实账户数值。

**修法**：**DOM 邻接**，不扫文本。找 textContent 恰好等于标签的元素，
再在父节点里找**兄弟**元素里的金额；命中兄弟是别的标签则跳过。

### 坑 5：奖励金额必须带货币符号

`Checked in today 99 Total check-ins` 里的 99 是**签到次数**不是钱；
`累计获得: N 次` 是**历史累计**不是今天拿到的。
只有带 `$¥€` 的才算奖励，且必须和「今天/今日/Today」相邻。

### 坑 6：余额标签可能不在 innerText 里

有些站把「可用余额/总余额」放在**hover 浮层**里，innerText 会丢掉它，
金额却留在 header。此时 DOM 邻接仍能找到（浮层 DOM 在，只是不可见）。
所以余额提取要读 DOM，不要只依赖 innerText 文本。

### 坑 7：短文本登录页被 `body_len` 门禁误判为失联

当站点登录态过期跳转到登录页时（如 `流光绘境` 重定向到 `#/login?redirect=/profile`），
页面通常只有精简的几个登录框与第三方登录按钮（实测仅 51 字符）。
如果 `open_station` 门禁要求 `body_len > 60`，会导致页面被误判为“未提交”，
重试 3 次后错误标记为 `⚫ 暂时失联`。
**修法**：门禁改为 `(body_len >= 20 or len(_title) > 0)`，只要有文档标题或少量文本即判定提交，
交给分类器去识别 `logged_out` 进而触发 LinuxDO 自动授权闭环。

### 坑 8：`已连续签到 N 天` 是历史连签统计，不是完成标记

如 `lOXO` 等独立签到页，卡片正中央始终渲染 `已连续签到 N 天`（代表以往连签天数）。
如果将 `已连续签到` 列入 `DONE_PATTERNS`，脚本一进页面就会把「待领取」的页面误判为「已签到」，
直接跳过真实的 `立即签到` 按钮！
**修法**：将 `已连续签到` 彻底从 `DONE_PATTERNS` 移除；真正的当日完成标志是 `今日已签到` /
`明天 00:00 再来` / `按钮 disabled`，未完成标志为存在可见且可点的 `立即签到`。

### 坑 9：人机验证的两类处置法则（图形 OCR 自动 vs 轨迹滑块人工）

公益站的人机验证分为两类，不能一刀切：
1. **图形验证码（如 简直了）**：弹窗中包含静态 Base64 图片（`<img src="data:image/png;base64,...">`）。
   此类可通过 OCR 识别字符（如 `3WFYB`），并通过 React 原生 Setter（`HTMLInputElement.prototype.value`）
   派发 input/change 事件填入并提交，可做到**全自动过验证**。
2. **行为轨迹滑块验证码（如 PM-Plan）**：前端不仅收集最终拼合坐标 `finalX`，还会采集高频鼠标移动轨迹
   数组 `track: [{x, y, t}]` 提交服务端模型校验。任何脚本模拟事件会被判 `vr.reason === 'bot_behavior'`
   （提示“这次操作轨迹未通过风控，请再自然一点重试”），可能招致封号。
   此类必须**前台弹窗由人工滑动 1 秒完成**。

### 坑 10：点击目标要按「动作词」排序，不能只按面积

2026-11-06 lOXO：侧边栏 `<A>每日签到</A>`（231×40）比真按钮 `<BUTTON>立即签到</BUTTON>`（384×48）**面积更小**。
旧的「最小面积优先」选中了导航链接——点完只是重新进入当前页，状态永远 pending，看起来像「点了没反应」。
**修法**：候选排序改为 `导航链接标记 > 动作词 > 面积`；
动作词（`立即|现在|领取|去签到|开始|Check in now`）优先，`A` 且 class 含 `sidebar|nav|menu|tab` 的降权。

### 坑 11：label→value 的兄弟节点必须「整段就是金额」

同一个 lOXO 页面上 `今日奖励 / 待领取 / 已连续签到 7 天` 三块相邻。
旧的兄弟扫描只要「文本里含数字」就把 `7` 绑成今日奖励。
**修法**：兄弟节点必须满足 `^[$¥€￥]?\d[\d,.]*$`（可带 元/额度/点/次 后缀），
且跳过 `待领取|未领取|暂无|未签到`。证据与数值同源仍成立，但**同源不等于相邻就对**。

### 坑 12：LinuxDO OAuth 按钮可能被「用户协议」复选框挡住

2026-11-06 Pigeonw：登录页点 `Continue with LinuxDO` **完全没有反应**（URL 停在 `/sign-in`），
脚本误报「没有授权按钮」（`NO_AUTH_BUTTON`）。真因是必须先勾「User Agreement」复选框
（该框被隐藏成 1×1，`getBoundingClientRect` 看起来不可点）。
**修法**：点 OAuth 前先 `document.querySelector('input[type=checkbox]').click()`，
再验证 `cb.checked === true`，然后才点 LinuxDO 按钮。

### 坑 13：`front window` 会漂移，多窗口时 tab 索引直接失效

2026-11-06 实跑中途用户新开了一个窗口，`tell tab N of front window` 立刻开始报
`Can't get tab 13 of window 1. Invalid index`，后续所有步骤全部失败。
**修法**：开工时记住窗口身份，后续显式用 `window K`（按 `count of windows` + 目标 tab URL 定位），
不要每步都重读 `front window`。新开 tab 后要**等一拍再读 `count of tabs`**，否则拿到的还是旧值。

### 坑 14：余额可以是负数；也可能是「免费额度」而不是付费余额

- 月城 2026-11-06 显示 `当前余额 -$13.92` → 金额正则必须允许前导负号，否则整段解析成 `None`。
- 三水 2026-11-06 显示 `付费 $0 免费 $16.12`，签到奖励进的是**免费额度**。
  付费余额为 0 时要回落到 `免费|赠送|赠金|Gift|Free` 标签，否则报告一个没用的 `$0`。

---

## ⚠️ 不要动用户的标签页

日常 Chrome 里通常开着用户自己的工作页（linux.do 帖子、项目看板、飞书）。

- **不要**复用 tab 1（那可能是用户正在看的页面）。
- **不要**用「关掉多余标签」来收尾 —— 会把用户的页面一起关掉。
- 正确做法：`claim_scratch_tab()` 追加一个**专用临时标签**并只用它，
  结束时 `release_scratch_tab()` **只关这一个**。
  实测：6 个用户标签跑完整轮后原样保留。

## 定时执行

- 定时任务用 harness 原生 `CronCreate`（一次性、durable 写进
  `.claude/scheduled_tasks.json`），**不要**用后台常驻 shell 脚本
  （会被安全分类器判定为未授权持久化，且不透明）。
- 机器是 MacBook，AC 供电时 `pmset` 显示 `sleep = 0`（不休眠），
  00:05 不会因为睡眠丢失 Chrome 连接。
- ⚠️ **重置时间不是统一的 00:00**（2026-11-06 实测修正）：
  - **08:00 重置**：薄荷（卡片「每天8点刷新」）、Fengwind（「下次刷新 2026/11/7 08:00」），
    以及一批 new-api 站（dicksuck / dudu / Hlool / luckyg / Huan / 烁 / 魔方 / CM-API / Orbitix / 方舟
    —— 00:05 签完后，**08:00 之后再看会重新变成「今日尚未签到」**，并能在当天再签一次）。
  - **00:00 重置**：lOXO、咕咕嘎嘎、Pigeonw、月城、三水、简直了、流光绘境等。
  - **结论：定时任务应放在 08:05，而不是 00:05。** 08:05 之后所有站都处于新窗口内且当日未签，
    一次能覆盖两种重置口径；00:05 跑只会签「上一个 08:00 窗口」，白天打开站点仍显示未签。

---

## 站点形态（2026-11-04 实测 28 站）

| 形态 | 特征 | 签到方式 |
| --- | --- | --- |
| **A. new-api / Semi-UI** | `Daily Check-in` / `每日签到` 卡片，按钮 disabled + 文案 `Checked in` / `已签到` | **打开即签到**：页面加载自动发 `GET /api/user/checkin?month=YYYY-MM` |
| **B. new-api group/card** | `每日签到已签到今天 +$X` | 同 A |
| **C. 独立签到页** | lOXO `今日已签到 · 明天 00:00 再来` + `今日奖励 $X` | 打开即签到 |
| **D. 自研站** | 薄荷 `签到` 转盘 / Fengwind `签到` tab | **需点击** `签到` 按钮（转盘类是 POST） |
| **E. 纯自动站** | Any Router 无签到卡片，仅 `GET /api/user/sign_in` | **打开即签到**（用户 2026-11-04 确认） |
| **F. 状态页** | uptime-kuma 等 | 跳过（`SKIP_URL_FRAGMENTS`） |

**自动签到接口家族**（`performance.getEntriesByType('resource')` 可见）：

- `GET /api/user/checkin?month=YYYY-MM` ← new-api 系（占绝大多数）
- `GET /api/user/sign_in` ← Any Router 系
- `GET /api/checkin/status` / `/api/checkin/calendar` ← 薄荷、Fengwind 系

**判据优先级**：`已签到`文案 > 按钮 disabled > 打开即签到的 API 调用 > 有可点的签到按钮。
**证据与判据必须同源**——判据说"done"，证据行里就要能看见 `已签到`/`Checked in`/`sign_in`。

---

## 登录态与 LinuxDO OAuth

- 登录态在**日常 Chrome 的默认 profile**里，脚本直接附着那个 Chrome（不重开）。
- 若页面出现 LinuxDO 登录按钮（未登录）：
  1. 点 LinuxDO 按钮 → 跳 `connect.linux.do` 授权页
  2. 点 `授权 / 同意 / Authorize / Allow` 按钮
  3. 跳回站点 → 重新 probe 分类
- 站点配置里 `linuxdo_oauth: true` / `linuxdo_client_id` 非空即支持此路径。
- **不要**把站点 token 存进本 skill 或任何仓库文件。

---

## 失联判定

单个站点**重试 3 次**仍打不开（`chrome-error://` 或 body 为空）→ 标记
`⚫ 暂时失联`，**不重试更多次、不算签到失败**（那是站点自己的问题）。

---

## 用法

```bash
cd ~/.claude/skills/gongyi-checkin/scripts

python3 run_checkin.py                    # 全量跑（会真的点签到）
python3 run_checkin.py --dry-run          # 只探测不点击
python3 run_checkin.py --limit 5          # 只跑前 5 个
python3 run_checkin.py --url https://x/profile --name X   # 单站
python3 run_checkin.py --report-only      # 重新渲染上次报告
python3 run_checkin.py --no-login         # 不尝试 OAuth 登录
```

产物（每次运行覆盖）：

- `data/last-run.json` —— 机器可读
- `data/last-run.md` —— 人读报告（成功/待签/需登录/暂时失联 + 奖励 + 余额）

**归档**：跑完把 `data/last-run.md` 内容贴进最终回复。

### 两个「经验」文件，别搞混

| 文件 | 内容 | 是否入库 |
| --- | --- | --- |
| `EXPERIENCE.md` | **手写**的站点笔记/踩坑记录，金额一律写占位符 `$X` | ✅ 入库（公开仓库） |
| `data/run-log.md` | 脚本**自动追加**的每次运行归档，含真实余额/奖励 | ❌ 不入库（`data/` 已 gitignore） |

**真实账户余额和奖励金额不得写进 `EXPERIENCE.md`**——本仓库是公开的。
脚本自动归档只写 `data/run-log.md`；需要沉淀成经验时，手动把**形态/判据/坑**
写进 `EXPERIENCE.md`，金额脱敏成 `$X`。

---

## 报告口径

| 状态 | 含义 |
| --- | --- |
| `✅ 签到成功` | 已签到（含"打开即签到"） |
| `🟡 待签到` | 有可点按钮但未点（dry-run 或点击失败） |
| `🔴 需登录` | 页面要求 LinuxDO 登录且自动登录没成功 |
| `⚫ 暂时失联` | 重试 3 次打不开 |
| `⚠️ 状态未知` | 打开了但判据不明确 |

奖励金额各站币种/单位不同（`$`/`¥`/`¤`），合计仅供参考，不做跨站折算。

---

## 同步规则

本 skill 必须**双向同步**（见 `~/.claude/projects/.../memory/feedback_skill_sync.md`）：

- 系统：`~/.claude/skills/gongyi-checkin/`（实际软链到 `~/.config/magpie/library/skills/gongyi-checkin`）
- 项目：`~/Documents/learn-claude-code/skills/gongyi-checkin/`

改完两处都要一致。用 `diff -rq` 校验。

---

## 目录

```
gongyi-checkin/
├── SKILL.md
├── scripts/
│   ├── chrome_driver.py   # AppleScript↔Chrome 驱动 + 探针 + 分类器
│   └── run_checkin.py     # 主流程 + 报告渲染
└── data/                  # last-run.json / last-run.md
```
