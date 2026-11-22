---
name: gongyi-checkin
description: 公益站（new-api / one-api 系）每日签到自动化。读取 Chrome 书签文件夹 daily-check-in，打开每个站点完成签到，输出签到成功/失败归档（含奖励金额与余额）。触发词：公益站签到、签到、每日签到、check-in、gongyi、公益站、station checkin、签到报告
version: 1.3.0
---

# gongyi-checkin — 公益站每日签到

对 Chrome 书签文件夹 `daily-check-in`（当前 id `5923`，以文件夹名兜底）里的公益站逐个完成每日签到，
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

> 进程命令行里带 `--remote-debugging-port=9222` **不代表 CDP 可用**：2026-11-16 实测日常 Chrome
> 带着该参数启动，但 `curl http://127.0.0.1:9222/json/version` 无响应（Chrome 拒绝在默认 profile
> 开调试端口）。判据永远是「端口有没有应答」，不要因为看到参数就临时切回 CDP 方案。

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
  **绝对不要 kill 日常 Chrome**——判断依据是 `--user-data-dir` 的**路径**，不是「有没有这个参数」：
  日常 Chrome 要么不带该参数，要么显式指向 `~/Library/Application Support/Google/Chrome`
  （2026-11-16 实测日常 Chrome 就带 `--user-data-dir=.../Google/Chrome --remote-debugging-port=9222`，
  按「不带参数」的旧判据会把它误认成流水线实例）。流水线实例的路径一定含 `mcp-chrome-`。
  若当时新闻流水线正在上传，先判断再动手；拿不准就问用户。
- **验证绑定正确**：`osascript -e 'tell application "Google Chrome" to get name of window 1'`
  应返回**用户自己**的标签标题，而不是「New Tab」/「公众号 / 视频号助手」这类流水线页面。

**三条定位写法都无效**（都会落到同一个实例）：
`tell application "Google Chrome"`、`tell application id "com.google.Chrome"`、
`tell application "/Applications/Google Chrome.app"`。
`System Events` 查 bundle id 反而能列出真实 pid —— 可用它做诊断，但不能用来发 JS。

### 🔮 演进方向：本地 CF 验证转发 + `curl_cffi` 协议直连（待实现）

当前版本受制于 AppleScript 链路（macOS 锁屏阻断 AppleEvent、多 Chrome 实例抢绑定、Turnstile 需切前台激活）。后续规划替代方案如下：

1. **本地 CF 验证转发**：由本地 Chrome（或轻量扩展/代理）完成 Cloudflare 人机验证后，提取并转发有效 `cf_clearance` 与站点会话 Cookie。
2. **`curl_cffi` 指纹模拟直连**：使用 `curl_cffi` 并指定 `impersonate="chrome{ver}"`（对齐本机 Chrome 主版本），复刻真实浏览器的 **TLS 指纹（JA3/JA4）与 HTTP/2 指纹**。
3. **请求头严格对齐**：随请求同步透传匹配的 `User-Agent`、`Sec-Ch-Ua`、`Sec-Ch-Ua-Mobile`、`Sec-Ch-Ua-Platform` 及业务头（`Origin`、`Referer`、`New-Api-User` 等），避免 `cf_clearance` 因指纹或头信息不一致被 CF 拦截（403）。

---

## 🚨 四十四个会静默失败的坑

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
   此类可通过 OCR 识别 5 位字符，再用 **React 原生 Setter** 填入并提交，可做到**全自动过验证**。
   **注意**：直接执行 `input.value = code` 会被 React 受控组件忽略；必须通过
   `Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(input, code)`
   赋值，并依次派发 `input`（`{bubbles: true}`）和 `change` 事件后再点击 Confirm（`chrome_driver.py` 已封装 `solve_react_captcha()`）。
2. **行为轨迹滑块验证码（如 PM-Plan）**：前端不仅收集最终拼合坐标 `finalX`，还会采集高频鼠标移动轨迹
   数组 `track: [{x, y, t}]` 提交服务端模型校验。任何脚本模拟事件会被判 `vr.reason === 'bot_behavior'`
   （提示“这次操作轨迹未通过风控，请再自然一点重试”），可能招致封号。
   此类必须**前台弹窗由人工滑动 1 秒完成**。2026-11-15 实测 PM-Plan 已换成**图片点选验证**
   （9 宫格食物图「找出所有通常趁热食用的食物」，共 2 页，`.selfcheck-*`），同样必须**人工完成**，
   绝不脚本代选图片，也不直接调接口绕过。

### 坑 10：点击目标要按「动作词」排序，不能只按面积

2026-11-06 lOXO：侧边栏 `<A>每日签到</A>`（231×40）比真按钮 `<BUTTON>立即签到</BUTTON>`（384×48）**面积更小**。
旧的「最小面积优先」选中了导航链接——点完只是重新进入当前页，状态永远 pending，看起来像「点了没反应」。
**修法**：候选排序改为 `按钮优于链接 > 导航链接降权 > 历史/记录降权 > 动作词 > 面积`；
动作词（`立即|今日签到|每日签到|现在|领取|去签到|签到领|开始|Check in now`）优先，`A` 且 class 含 `sidebar|nav|menu|tab` 的降权。
同为按钮、又都不含动作词时，面积更小的「历史签到」仍会赢过「今日签到」，见坑 39。

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

- 月城 2026-11-06 显示 `当前余额 -$X` → 金额正则必须允许前导负号，否则整段解析成 `None`。
- 三水 2026-11-06 显示 `付费 $0 免费 $X`，签到奖励进的是**免费额度**。
  付费余额为 0 时要回落到 `免费|赠送|赠金|Gift|Free` 标签，否则报告一个没用的 `$0`。

### 坑 15：Mac 锁屏时不投递 AppleEvent，`run_checkin.py` 会误报「Chrome 没开」

2026-11-11 00:05 实测：Mac 屏幕锁着（`CGSSessionScreenIsLocked=true`）时跑签到，脚本直接退出并报
`cannot talk to Chrome (tabs=__TIMEOUT__). Is Chrome running?` —— **Chrome 进程其实好好地在跑**
（单实例、pid 正常、没有第二个实例抢绑定），是 macOS 在锁屏时不给 GUI 应用投递 AppleEvent。

- 判据：`ioreg -n Root -d1 -a | grep -A1 CGSSessionScreenIsLocked` → `true` 即锁屏。
- 锁屏时**所有** GUI 应用的 AppleEvent 都超时（TextEdit / Safari / Finder 同样），
  只有不触碰窗口的 `tell app "X" to return version` 还能返回 —— 所以「app 在跑」≠「AppleEvent 通」。
- `caffeinate -u` 只能唤醒显示器，**解不开锁屏**；`stat -f%Su /dev/console` 显示 console user 也不代表未锁。
- **处理**：不要 kill / 重启 Chrome（那是日常唯一有登录态的实例）。改为先判锁屏，
  锁屏就挂一个「解锁后再跑」的轮询任务，等解锁后重跑。
- 定时任务放 08:05 的另一个好处：人通常在白天，屏幕多半是解锁的，撞上锁屏的概率远低于 00:05。
- **解锁判据要两个都查**：`CGSSessionScreenIsLocked`（存在且为 true）与 `IOConsoleLocked`。
  解锁后 `CGSSessionScreenIsLocked` 这个 key 会**整个消失**（不只是变成 false），
  `grep` 命中数为 0 —— 只 grep `-A1` 一行容易误判。

### 坑 16：书签文件夹的数字 id 会变，名字才稳

2026-11-11 实测：Chrome 里 `daily-check-in` 文件夹的 id 从 `6233` 变成了 `5923`
（文件夹被移动/重建时 Chrome 会重新生成 id；`Bookmarks.bak` 里也没有 `6233`）。
旧脚本只按 id 找，直接 `SystemExit: bookmark folder 6233 not found`，31 个站一个都跑不了。

- 修法：`read_bookmarks()` 先按 id 找，**找不到就按文件夹名字 `daily-check-in` 回退**，
  并在日志里打印实际解析到的 id。
- 跑之前先自查：
  ```bash
  python3 -c "import sys;sys.path.insert(0,'~/.claude/skills/gongyi-checkin/scripts');import run_checkin as r;print(len(r.read_bookmarks()))"
  ```
  打印 31 就是好的；报 not found 就是 id 又变了。
- **别把 `DEFAULT_FOLDER_ID` 写死当唯一事实源** —— 名字是稳定标识，id 只是缓存。

### 坑 17：AppleScript 绑的是「最后注册/最后激活」的那个 Chrome，不是「你的」那个

2026-11-11 实测：机器上同时有日常 Chrome（pid 832，默认 profile，30 站登录态全在这）
和 ai-news-factory 的 mcp-chrome（pid 82854，`--user-data-dir=.../mcp-chrome-10b76e5`）。
`tell application "Google Chrome"` 绑的是 **mcp-chrome**，不是日常 Chrome ——
表现是 `name of window 1` 返回「公众号」而不是用户自己的标签页。

- 判据：跑签到前先 `osascript -e 'tell application "Google Chrome" to return URL of every tab of every window'`，
  看返回的是不是五个平台的页面（weixin/zhihu/bilibili/douyin）—— 是就说明绑错了。
- `open -a "Google Chrome"` **不解决问题**：它只是激活某个实例，绑定不变。
- 正确 reclaim 顺序（repo 里 `data/_launch_1111.sh` 的 `reclaim_profile` 同款）：
  1. `kill <browser_daemon.py pid>`（先停 daemon，否则 Chrome 会被它守着）
  2. `kill <mcp-chrome Chrome pid>`；残留就 `kill -9`
  3. `sleep 3` 后复查绑定：`name of window 1` 应该是用户自己的标签页
  4. **绝不 kill 日常 Chrome**（不带 `--user-data-dir` 的那个）
- 签完要恢复 pipeline：`bash data/_restart_upload_daemon_1111.sh`（幂等，9222 已通会直接返回）。

### 坑 18：Cloudflare 5 秒盾与 Turnstile 验证弹窗必须「切前台激活 + 显式轮询等待」

2026-11-12 实测：多个 new-api 站（AzureKilnAPI、三水公益站等）在打开站点、LinuxDO OAuth 授权页跳转，
或点击 `Check in now` 后，会触发 Cloudflare 5 秒盾或弹出
`Security Check: Please complete the security check to continue` 弹窗（内嵌 `challenges.cloudflare.com/turnstile` iframe）。

- **修法**：
  1. `is_cf_challenge()` 同时判定整页挑战与页内 Turnstile 弹窗（`hasCfModal || isCfPage`），避免因页面已加载站内文案而漏检弹窗；
  2. `open_station()` 与 `handle_linuxdo_oauth_authorize()` 接入 `wait_cf_pass()`，检测到 CF 盾时显式轮询等待通过；
  3. 点击签到后的验证循环每轮调用 `activate_tab(tab)` **将标签置为前台激活态**（后台标签中 Turnstile 常会卡死不自动校验），
     并尝试触发 Turnstile checkbox，等待 10~30 秒直到带 token 的 `/api/user/checkin?turnstile=...` 请求发出且状态翻转；且若检测到 CF/验证码仍在进行中，不得盲目重试点击以免重置 Turnstile。

### 坑 19：日历底部静态规则 `You can only check in once per day` ≠ Toast 成功提示

new-api 系日历组件底部常驻静态规则说明 `You can only check in once per day`（**未签到时也在 DOM 里**）。
若将其放进全局文本的 `DONE_PATTERNS` 或 `_hard_done`，会直接击穿「有可点动作按钮优先判 `pending`」的护栏，导致真实待签到站点被误判为 `done` 而漏签。

- **修法**（2026-11-12 已在 `chrome_driver.py` 修正）：
  1. 从全局正文匹配 `DONE_PATTERNS` 和 `_hard_done` 中移除 `You can only check in once per day` 与 `Do not repeat check-in`；
  2. `probe()` 单独采集 Toast 容器（`.ant-message-notice`、`.semi-toast`、`.Toastify__toast`、`[data-sonner-toast]`、`.el-message`、`.v-toast` 等）写入 `toasts` 字段，**只有命中最外层 Toast 容器** 里的提示（含 `You can only check in once per day` / `Check-in successful` / `签到成功`）才认作服务端明确回复；
  3. 正文仅认硬完成语（`今日已签到`/`今日已领取`/`今日已打卡`/`明天 00:00`/`明日再来`/`已领取，明天再来`）或按钮翻转为 disabled / `Checked in`。

### 坑 20：AppleScript 动态 Tab 索引安全保护与越界防御（`-1719` 无效索引）

多标签场景或 OAuth 登录弹窗导致窗口标签数动态增减时，脚本里写死 `tab %d` 会抛出 `(-1719 无效的索引)` 中断流程。此外，若盲目将超出标签数的索引下夹（clamp）到 `totalTabs`，可能在临时标签提前关闭时误向用户的日常工作标签注入脚本！

- **修法**（2026-11-12 已在 `chrome_driver.py` 与 `run_checkin.py` 统一加固）：
  1. 所有操作 tab 的 AppleScript 封装（`js`、`navigate`、`current_url`、`activate_tab`）严格执行边界校验：
     `if tIdx < 1 or tIdx > totalTabs then error "Tab index out of bounds: " & tIdx & " (total: " & totalTabs & ")"`，拒绝误伤用户标签；
  2. 关闭临时标签 `release_scratch_tab()` 严格限定 `tIdx > 1 and tIdx <= totalTabs`，**绝对不关闭 tab 1**；
  3. `claim_scratch_tab()` 在超时未检测到新标签生成时抛出明确异常，绝不 fallback 到 tab 1。

### 坑 21：单站必须「循环验证确认成功」才切下一站，不能等固定秒数就走

旧流程点完按钮只 `sleep(SETTLE_SECONDS)` 一次即切往下一站，遇到 Turnstile 弹窗延迟、异步接口慢或转盘动画，容易没签上就离开导致漏签或误报。

- **修法**（2026-11-12 已在 `run_checkin.py` 落地 Verification Loop）：
  1. 常规 `pending` 站点点击后进入最多 14 轮 × 2s（约 28~30s）循环验证：每轮激活前台标签、辅助点击 Turnstile、`probe/classify`，
     直到明确翻转为 `done`/`auto`、命中 Toast 成功、或识别出 `blocked_captcha` 才退出循环；
     仅在第 8 轮仍 `pending` 且确认**无 CF Turnstile / 图形验证码进行中**（`not cf_active and not has_captcha`）时才自动补点一次，避免重置 Turnstile；
  2. **薄荷公益站（`up.x666.me`）**：点击 `开始转动` 后等待 5 秒转盘动画，**必须重新 `navigate(url)` 刷新页面**并重新 `probe/classify` 确认 `done`。

### 坑 22：Cloudflare Tunnel Error 1033 宕机与「签到功能未启用」的分类归因

- **Cloudflare Tunnel `Error 1033`**（如 PM-Plan 2026-11-09 起的隧道中断）：属于目标站服务端隧道宕机，`classify()` 直接归为 `unreachable`（`⚫ 暂时失联`，evidence 标明 `Cloudflare Tunnel Error 1033 (HTTP 530)`），不要当作脚本点击逻辑故障反复调试。
- **签到模块未启用**（如 君の星辰 `/api/user/checkin` 返回 `{"message":"签到功能未启用","success":false}`）：站点本身关闭了签到功能，`classify()` 直接归为 `unsupported`（`ℹ️ 未启用签到`，同时保留读取到的余额），不再误判为 `⚠️ 状态未知` 或漏签。

### 坑 23：SPA 异步渲染延迟与初始探针重试（如 CM-API-公益站）

像 `CM-API-公益站` 等 React/Vue SPA 站点，页面在 `document.readyState === 'complete'` 时仅完成了骨架渲染，根组件仍在异步拉取 chunk 或初始配置数据。若在初次 `probe()` 阶段 body 字符数刚达标但签到卡片与按钮尚未挂载，会导致 `hits` 为空而直接被误判为 `⚠️ 状态未知`。

- **修法**（2026-11-12 在 `run_checkin.py` 落地）：
  当初次分类状态为 `unknown` 且没有任何 `hits` 与 `apiHits` 时，脚本额外暂停 3.0 秒并二次执行 `probe()` + `classify()`，给 SPA 充分的挂载与接口请求时间，彻底消除假阴性。

### 坑 24：DOM 最内层原子节点匹配与正则剥离安全（`strip_js_comments`）

1. **DOM 嵌套层级误取**：在复杂前端框架（如 Semi-UI / Ant Design）中，按钮往往被嵌套在外层容器中（例如 `<div><button disabled>签到</button></div>`），外层 `div` 与内层 `button` 具有完全一致的 `textContent`。若在候选去重时从外层判定 `contains(inner)`，会错误剔除内层真正带有 `disabled` 属性的 `<button>` 而保留无 disabled 属性的外层 `<div>`，引发漏判已签到。
   - **修法**：在 `PROBE_JS` 中改为通过 `e.querySelectorAll('*')` 递归检查子节点，只要子节点中已存在相同文本的元素即跳过外层，精准抓取最内层的原子按钮控件。
2. **AppleScript 单行换行折叠与正则字面量安全**：AppleScript 的 `execute javascript` 要求注入的字符串不能跨行，`strip_js_comments()` 必须先剔除代码中的注释。但若 JS 代码包含正则字面量（如 `/https?:\/\//`、`/linux\s*do/i`），朴素的注释过滤会把正则内部的 `//` 或 `/*` 截断为行内注释，导致脚本语法破损，AppleScript 返回 `missing value`。
   - **修法**：`strip_js_comments()` 引入完整的 JavaScript 词法扫描状态机，追踪前驱字符与关键字，精准区分除号运算符与正则字面量，并在正则内完整识别字符集 `[...]` 与转义字符 `\`。

### 坑 25：Toast 成功提示与按钮未翻转站点的豁免（Aether API 模式）

部分站点（如 Aether API）在完成签到后，服务端接口已成功记录签到，且页面弹出 `You can only check in once per day` 或 `签到成功` 的 Toast 提示，但页面上的按钮文案仍保持 `Check in now` 且不设置为 `disabled`。若单站验证循环（Verification Loop）死板地要求 `state_v["state"] != "pending"`，会导致脚本在已成功签到后反复轮询直到超时。

- **修法**（2026-11-12 已在 `run_checkin.py` 落地）：
  在单站验证循环中，只要 Toast 容器捕获到明确的服务端回复（`Check-in successful` / `签到成功` / `You can only check in once per day` 等），即明确判定为 `done` 并提前退出循环，避免无谓等待。同时在 `classify()` 中保持严谨：仅当 Toast 容器匹配时豁免，页面普通静态正文中的规则说明仍不得击穿可点按钮。

### 坑 26：LinuxDO OAuth 授权页 CF 质询耗尽单步超时 & 授权重定向保护

自动化登录（如流光绘境）跳转至 `connect.linux.do` 授权页时，授权页自身常弹出 Cloudflare 5 秒盾或 Turnstile 质询。旧的 `handle_linuxdo_oauth_authorize` 仅设置固定 25 秒总超时，CF 轮询等待（15~20 秒）耗尽了整个授权处理窗口，导致抛出 `AUTH_TIMEOUT`，使得页面停滞在授权页，随后被域名一致性检查误判定为异常停止。

- **修法**（2026-11-13 已在 `run_checkin.py` 落地）：
  1. 授权等待超时基线延长至 45 秒；
  2. 在 `handle_linuxdo_oauth_authorize` 中接入 `wait_cf_pass()`，一旦检测到 CF 质询并在通过后**重置超时 deadline**，确保授权按钮有完整的时间窗口被点击提交；
  3. 点击授权后增加重定向等待缓冲（`wait_for` 35s），并调用 `wait_cf_pass()` 与 `settle()` 平滑过渡回原站。

### 坑 27：非标准代币单位与无符号数值奖励提取（LDC / Payload / +N 额度）

公益站生态日益多样化，签到奖励不再局限于 `$`/`¥`/`BTC`：
- `hkai` 发放 `LDC 1` (Linux DO Credit)；
- `Aether API` 发放 `Payload 86.27`；
- `流光绘境` 发放 `+11` 或 `签到 11` 额度；
- `[✅]Ark API[img]` / `Lanln[gpt]` 发放 `🍥X` / `¤X`。
旧的 `_money()` 和奖励正则仅匹配固定货币符号，遇到以上非标代币时会将奖励解析为 `None` 或直接漏掉。

- **修法**（2026-11-13 已在 `chrome_driver.py` 与 `run_checkin.py` 落地）：
  1. `_money()` 正则扩展前导与后缀识别集合：新增 `LDC`、`Payload`、`🍥`、`¤` 及单纯前导正负号的数值提取（如 `+11`）；
  2. `classify()` 与 Verification Loop 优先从 `.ant-message-notice` / `.semi-toast` 等 Toast 容器的回执文本（`Check-in successful! Received ...`）中提取准确的单次入账奖励数值，避免被页面历史累计总额干扰。

### 坑 28：纯钱包/充值页（如 君の星辰）自适应归类为「未启用签到」

部分站点（如 `君の星辰` `https://ai.centos.hk/wallet`）书签直达钱包页，页面只展示当前余额（`¥5`）和充值档位，后台完全未开放签到模块或组件。旧分类器在未见完成语且无动作按钮时，直接判定为 `⚠️ 状态未知`，导致严格门禁误拦截中断。

- **修法**（2026-11-13 已在 `chrome_driver.py` 落地）：
  当站点已正常登录、成功提取到有效账户余额（如 `Current Balance ¥5`），但整页既无签到动作候选、无签到日历与完成语、且 URL 为钱包/账单管理页（`/wallet`、`/recharge` 等）时，自动归类为 `ℹ️ 未启用签到`（`unsupported`），完整保留余额快照，不再误判为 `⚠️ 状态未知`。

### 坑 29：断点恢复状态机（Resume）必须保留所有合法终态

在严格门禁模式或中断恢复时，若上一站遇到合规的不可逆终态（例如重试 3 次均超时失联的 `unreachable` 站点 Orbitix，或 Cloudflare Tunnel Error 1033 宕机站点 PM-Plan，以及 `unsupported` 未启用签到站），朴素的 resume 逻辑如果执行 `results[-1]['state'] != 'done' -> results.pop()`，会导致已合规判定的失联站被反复出栈重跑，形成死循环卡点。

- **修法**（2026-11-13 已在 `run_checkin.py` 落地）：
  1. `run_checkin.py` 原生支持 `--resume` 参数；
  2. 断点恢复状态机将合法终态集合扩大为 `('done', 'auto', 'unreachable', 'unsupported')`，只有真正未决的异常（如 `logged_out`、`blocked_captcha`、`unknown`）才在重跑时出栈重试；
  3. 主循环每完成一个站点即实时保存 `last-run.json` 与 `last-run.md`，确保任意时刻中断均不丢失前面站点的签到成果。

### 坑 30：LinuxDO 登录按钮文本带点与 Discourse SSO 流程中转（`linux.do/session`）

1. **按钮文本正则防漏**：`lOXO` 等站点第三方登录按钮文案为 `Continue with Linux.do`（带点 `.`）。旧正则 `/linux\s*do|linuxdo/i` 只匹配空格与无空格写法，导致漏认登录按钮，误判为状态未知。
   - **修法**（2026-11-14 落地）：统一升级为 `/linux[\s._-]*do/i`，覆盖 `Linux.do`、`Linux-DO`、`Linux DO` 等各类写法。
2. **Discourse SSO 授权中转与终态锁定**：`connect.linux.do` 进行鉴权时常中转至 `linux.do/session/sso_provider`。若脚本只监控 `connect.linux.do`，会误将中转页判定为跳出授权并提前重定向，破坏授权流。此外，当授权未完成（如 `linuxdo_session_logged_out`）时，若继续 probe `linux.do/login` 页面会被误判为 `unknown`（提示 `Skip to main`）。
   - **修法**（2026-11-14 落地）：将 `linux.do/session` 纳入 OAuth 授权监控范围；授权失败（`linuxdo_session_logged_out` / `AUTH_TIMEOUT`）时明确锁定 `logged_out`（`🔴 需登录`），避免覆盖为状态未知。

### 坑 31：React 验证码提交按钮误伤 Token 词根与限定弹窗容器（`\bOK\b`）

1. **确定按钮误伤导航链接**：旧正则 `/确定|确认|Confirm|Submit|OK/i` 中的 `OK` 会无前缀匹配 `Token Management` 中的 `token`（含 `ok` 子串），导致将验证码提交误点成页面侧边栏导航链接。
   - **修法**（2026-11-14 落地）：必须使用 `\bOK\b` 严格整词匹配，并优先限定在 `.semi-modal, .ant-modal, [role=dialog]` 容器内部寻找提交按钮。
2. **图形验证码自动提取落盘**：引入 `get_captcha_image_base64()` 与 `save_captcha_image()`，当检测到图形验证码弹窗时自动将完整 Base64 图片还原保存至 `/tmp/gongyi_captcha.png`，便于人工速览或后续接入自动化 OCR。

### 坑 32：积分兑换/账号绑定链接混淆为第三方登录按钮（`Credit redemption` / `Bind`）

侧边栏与设置页中的 `Linux.DO Credit redemption` / `LinuxDO Bind` 等积分兑换或账号绑定链接会被 `login` 规则误收录（文本包含 `linux.do`），导致已处于登录状态的站点（如 `简直了`）被张冠李戴误判为未登录（`logged_out`）。
- **修法**（2026-11-14 落地）：在 `PROBE_JS` 与 `linuxdo_login()` 中增加排除词过滤：`/已绑定|管理|解除|redemption|credit|兑换|充值|bind/i`，彻底隔离正常业务链接。

### 坑 33：多 Chrome 实例启动竞争与 AppleScript 窗口绑定诊断防护

当系统后台运行 AI 新闻流水线守护进程（`browser_daemon.py` 起的 `--user-data-dir=.../mcp-chrome-10b76e5`）时，`tell application "Google Chrome"` 默认会被系统解析至最后注册或激活的实例。若脚本静默附着到 `mcp-chrome`，由于其完全不具备日常 Chrome 的 28+ 站点 Cookie，会导致大面积出现 `logged_out` 或「暂时失联」。
- **修法**（2026-11-14 落地）：
  1. 启动时自检 Chrome 进程数：`ps -Ao pid,command | grep ...`；
  2. 若大于 1 个实例，通过 `tell application "Google Chrome" to get name of window 1` 探测当前绑定的窗口标题；
  3. 若命中微信公众号/视频号/抖音/B站/创作者平台等流水线特征，立即在日志中输出高危告警提示用户或安全抢占，防止 0 登录态误跑。

### 坑 34：未签到页面上的「奖励」可能是日历历史，不能当真

2026-11-15 简直了：页面尚未签到、按钮仍是 `Check in now`，但日历里留着前一天的
`Received ¥10.00`，旧分类器把它当今日奖励写进报告（当天金额碰巧相同，掩盖了问题）。
同理 `Total received ¥X` 的 `received` 也会命中奖励正则，而累计守卫只看匹配到的
`Received ¥X` 本身，看不到前面的 `Total`。

- **修法**（2026-11-15 落地）：
  1. `classify()` 变为外层包装：只有 `done` / `auto` 才保留 `reward` 并计入合计；
     `pending` / `blocked_captcha` / `unknown` 等未确认状态下的金额降级为证据文本
     「页面显示奖励 $X，本次未确认，不计入合计」，`reward` 置空。
  2. `Received` 正则改为逐条 `finditer`，检查匹配前 14 字符，命中
     `累计|总共|共获得|历史|total` 就跳过，`Total received` 不再劫持今日奖励。
  3. 证据与事实必须同源：报告里的奖励只能来自「已确认签到」页面或成功 Toast。

### 坑 35：图片点选人机验证弹窗完全漏检（PM-Plan 2026-11-15 形态变更）

PM-Plan 的验证从行为滑块换成了**图片点选**：`.modal-backdrop.open` 内放
`.modal[role=dialog][aria-modal=true]`，九宫格图片 `src=/api/selfcheck/img/img-*`，
提示「找出所有通常趁热食用的食物」，共 2 页。旧探针只认
`img[src^=data:image] + 验证码输入框`（图形码）和滑块文案，对这种弹窗
`hasModal=false / hasSlider=false` → 分类仍是 `pending`；验证循环第 8 轮还可能
再点一次按钮，重置验证。

- **修法**（2026-11-15 落地，`chrome_driver.py` / `run_checkin.py`）：
  1. `PROBE_JS` 新增 `hasVerify`（`.selfcheck-grid` 或弹窗内含
     人机验证/请选出所有符合要求的图片/安全验证/验证码等语义）和
     `blocking`（任意 `.modal-backdrop.open` 或 `[role=dialog][aria-modal=true]` 可见弹窗），
     并采集 `prompt` / `page`（如「找出所有通常趁热食用的食物」「第 1 页，共 2 页」）。
  2. `classify()` 把 `hasVerify` 也归入 `blocked_captcha`，证据里带上验证提示与页码。
  3. 验证循环的重复点击守卫扩展为
     `hasModal or hasSlider or hasVerify or blocking`——**任何弹窗打开时都不再补点**。
  4. 图片点选/滑块**不自动求解**：新增两段式命令（见「用法」），
     `--prepare-captcha` 把验证弹窗留在前台，人工完成后 `--submit-captcha` 只用于图形码。

### 坑 36：单站补跑（`--url`）会覆盖当天的全量归档

全量跑后把 `unknown` / `pending` 的站点用 `--url` 逐个补跑是常规收尾动作，
但旧版每次运行都会**整体重写** `data/last-run.json` / `last-run.md`——
2026-11-16 实测：32 站的全量报告在补跑 3 个站点后只剩 1 条结果，
`--report-only` 也只能渲染出最后一站，当天的完整归档等于丢了，只能手工重建。

- **修法**（2026-11-16 落地，`run_checkin.py`）：单站运行结束时，若
  `last-run.json` 的 `meta.date` 就是今天且已有条目更多，则按
  `(url, name)` 把本次单站结果**合并回原列表**再落盘，保留全量报告。
- 兜底：万一报告已被覆盖，`data/run-log.md` 只记「有变化的站点」，
  不能还原全量；此时只能按终端日志逐站重建，或在同一天重跑全量（已签站点不会被重复领取）。
- 提醒：`--submit-captcha` 更新归档是**原地匹配 URL**，不会丢其它站点；问题只在 `--url` 全量落盘路径。
- **回归**（2026-11-20）：合并只发生在跑完之后，主循环每站结束的中间落盘会先把全量覆盖成 1 条，
  `merge_into_today_archive` 再读就没有全量可合。单站跑（`--url`）必须跳过这次中间落盘。

### 坑 37：`--prepare-captcha` 报 `blocked_captcha` ≠ 一定需要人工

2026-11-16 PM-Plan 实测：`--prepare-captcha` 返回
`{"kind":"verify","state":"blocked_captcha"}`，但几秒后再 probe，弹窗已消失、
页面显示「今天是 YYYY-MM-DD，已完成签到」+ 按钮 disabled —— 验证在无人操作下
自行通过/关闭了（该站的点选验证对本次会话未强制拦截）。

- **修法**（2026-11-16 落地，`run_checkin.py`）：`prepare_captcha()` 发现
  `verify`/`slider` 类验证后，先做最多 10 秒的重探；若状态翻转为 `done`/`auto`，
  返回里带 `resolved_after_wait: true` 并自动回收临时标签，不必再叫人。
- **人工前先重探**：看到 `blocked_captcha` 别急着喊人，先用 `probe` 看一眼当前状态；
  只有弹窗仍可见、状态仍阻塞时才走人工两段式。
- 重探时**不要点签到按钮**（会重置验证）；只读 DOM 即可。

### 坑 38：验证码图片太小，直接读容易认错字

2026-11-16 简直了的 5 位彩色图形码原图约 120×46，直接读图容易把 `M` 看成 `H`、
`D` 看成 `O`。低分辨率是实打实的误判来源。

- **修法**：读图前先放大（无插值失真担忧，验证码是硬边缘字形）：
  ```bash
  sips -z 400 960 data/captcha.png --out /tmp/captcha_big.png
  ```
  再读 `/tmp/captcha_big.png`；提交后以 `--submit-captcha` 返回的
  `state=done` 与 Toast 回执为准，失败就重新 `--prepare-captcha` 换一张（验证码一次性）。
- 识别结果**不要写进 `EXPERIENCE.md` 等入库文件**（验证码是一次性的，没有沉淀价值）。

### 坑 39：并列按钮里「历史签到」会因面积更小赢过「今日签到」

2026-11-21 YeeMagine（`demo.yeelo.fun`）：同一行有 `历史签到`、`今日签到`、`试试手气` 三个按钮。
前两者都含「签到」、都是 `BUTTON`、都不含 `立即|去签到|签到领|Check in now`，
排序落到最后一档「面积更小优先」。`历史签到` 更短，两次都返回 `CLICKED:历史签到`——
点开的是历史记录，状态永远停在 `pending`。手点文本恰好为「今日签到」的按钮后，
余额增加、日历变为「已签到」。

- **修法**（2026-11-21，`chrome_driver.py` 的 `CLICK_JS`）：
  1. 候选直接排除 `历史签到|签到历史|签到记录|历史记录`；
  2. 排序在面积之前增加「历史/记录/日历/排行」降权；
  3. 动作词补上 `今日签到|每日签到|签到领`，避免真按钮和记录按钮同分后再比面积。
- `试试手气` 这类抽奖按钮不含「签到」，本来就不会被选中，不要为了它放宽匹配。

### 坑 40：`--prepare-captcha` 复核成 `done` 不回写归档

2026-11-21 PM-Plan：全量跑留下 `blocked_captcha`。之后 `--prepare-captcha` 打开页面已经是
「今日已签到」（`state=done`，坑 37 的自行通过），JSON 打印是对的，但 `last-run.json`
仍停在 `blocked_captcha`——只有 `--submit-captcha` 会原地改归档。当天只能手改 JSON 再渲染。

- **修法**（2026-11-21，`run_checkin.py`）：`--prepare-captcha` 与 `--submit-captcha`
  在结果为 `done`/`auto` 时都走 `patch_today_archive()`，按域名（有站名则再按站名）
  改当天归档里的那一行并重渲染 markdown。归档日期不是今天、或匹配不到行，则不写并打日志。
- 回写前确认 `meta.date` 是今天，避免把昨天的失败行改成成功。

### 坑 41：点击后页面不翻转，重新打开才显示已签到

2026-11-21 iGrok、Pigeonw：验证循环里已经 `CLICKED:立即签到` / `CLICKED:Check in now`，
14 轮结束后仍是 `pending` 或 `unknown`（Pigeonw 的最终证据甚至是空的）。
同一天用 `--url` 重新打开，页面直接是「已签到」并带上今日奖励。
new-api 系本来就会在加载时发 checkin，SPA 却不一定把按钮文案翻过来。

- **修法**（2026-11-21，`run_checkin.py`）：验证循环耗尽且仍是 `pending`/`unknown`、
  并且**没有**验证弹窗（`hasModal/hasSlider/hasVerify/blocking` 都没有）时，
  `navigate` 回原 URL 再 probe 一次，把刷新后的状态当最终结果。
- 有验证弹窗时不刷新——刷新会把 Turnstile / 图形码 / 点选验证重置（坑 35）。
- 这不是再点一次按钮。第 8 轮的补点逻辑不变。
- 刷新必须先走 `about:blank`，否则同 URL 不会重新请求文档（坑 3）。

### 坑 42：`立即签到` 只打开说明框，而且不吃脚本点击（iGrok）

2026-11-22 iGrok：`CLICKED:立即签到` 之后按钮一直还在，刷新也还是「立即签到」。
这个按钮的点击处理只打开「签到奖励说明」，真正入账的是框里的 `领取当前奖励`
（POST `/api/user/checkin`）。`element.click()` 能触发 DOM click，但处理函数不跑，
框根本不出现；按按钮的屏幕坐标发一次真实鼠标点击才会打开。确认后再点
`领取当前奖励`，接着弹出 Turnstile「安全验证」。标签在前台时这个盾会自己通过，
不要把它当成图片点选交给人工。

- **修法**（2026-11-22，`chrome_driver.py` / `run_checkin.py`）：
  1. 验证循环每轮先找 `领取当前奖励` / `Claim this reward`，找到就点；脚本点击后按钮还在，再补一次真实鼠标点击；
  2. 只有文本恰好是 `立即签到`、JS 点击约 8 秒后仍是 pending、且没有验证弹窗时，才对这个按钮做一次真实鼠标点击。`Check in now` 不走这条，避免每个慢站都挪鼠标；
  3. 点击前用 `elementFromPoint` 核对目标就是该按钮，并且坐标落在 Chrome 窗口内，对不上就不点；
  4. 探测到可见的 Turnstile iframe 时继续前台等待，不判 `需人工验证`。
- 真实鼠标点击会挪一下指针，只作为上面这一次兜底。锁屏时 AppleEvent 和鼠标事件都不可用（坑 15）。

### 坑 43：哈希路由的控制台壳先出来，签到区晚挂（RelayFor）

2026-11-22 RelayFor（`/console/#benefits`）：第一次 probe 的正文全是侧边栏
（概览、模型与价格、API Key），没有签到按钮，3 秒重试后仍是 `unknown`。
同一天重新打开，签到区已经在，按钮是 `今日签到还款`，点完是「今日已签到」。

- **修法**（2026-11-22，`run_checkin.py`）：`unknown`、URL 带 `#`、正文里还没有
  「签到 / check-in」时，再等 8 秒探一次。没有 hash、或正文里已经有签到字样的站不额外等。

### 坑 44：验证弹窗关掉后的 SPA 软跳，残留 checkin 请求不是成功（PM-Plan）

2026-11-22 PM-Plan：点选验证在 10 秒复核里还开着。过一会儿弹窗没了，地址却停在
`#/models`。这时 `performance` 里仍留着刚才的 `/api/user/checkin`，分类器把它当成
「打开即签到」。重新 `about:blank` 再打开首页，页面才是「今天是 YYYY-MM-DD，已完成签到」。

- **修法**（2026-11-22，`chrome_driver.py` / `run_checkin.py`）：
  1. 只有当前页读得到余额，或正文里有签到/余额字样，才允许 `apiHits` 判 `auto`；
  2. 非图形验证（点选/滑块）先在前台再等最多 30 秒；弹窗还在就不要刷新（坑 35）；
  3. 弹窗已经不在、页面又不是已签到时，走 `about:blank` 重新打开原 URL 再判；
  4. `已完成签到` 算硬完成语。图形验证码仍不在这里干等。

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

## 失联与异常分类判定

- 单个站点**重试 3 次**仍打不开（`chrome-error://`、body 为空，或 Cloudflare Tunnel `Error 1033` 隧道宕机）→ 标记
  `⚫ 暂时失联`，**不重试更多次、不算脚本失败**（那是站点自己的问题）。
- 页面或接口明确返回 `签到功能未启用`（如 君の星辰）→ 标记 `ℹ️ 未启用签到`（`unsupported`），不视为漏签。

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

# 两段式人工验证：全量跑报 blocked_captcha 后使用（坑 35）
python3 run_checkin.py --prepare-captcha https://plan.pmcat.top/ --name PM-Plan
#   返回 JSON: tab / kind(graphic|verify|slider) / prompt / page / image
#   verify/slider 会先自动重探 10 秒：若验证自行通过，返回 resolved_after_wait=true 并回收标签（坑 37）
#   复核结果已是 done/auto 时，会回写当天 last-run 里该站的状态（坑 40）
#   图形码 → 图片存到 data/captcha.png，放大后识图再提交（坑 38）：
sips -z 400 960 data/captcha.png --out /tmp/captcha_big.png
python3 run_checkin.py --submit-captcha BDMM8 --host jianzhile.vip
#   图片点选/滑块 → 标签页留在前台，人工完成即可（脚本绝不代选/代滑）
#   默认成功后保留标签页；加 --close-tab 才会关闭
```

产物：

- `data/last-run.json` —— 机器可读
- `data/last-run.md` —— 人读报告（成功/待签/需登录/暂时失联 + 奖励 + 余额）
- 单站补跑（`--url`）在同一天会**合并回全量归档**，不再覆盖整天报告（坑 36）

**收尾**：`--prepare-captcha` / `--submit-captcha` 默认可能留下自己的临时标签，
确认完成后按 URL 只关这些临时标签；**绝不批量关闭**，用户自己的页面要原样保留。

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
| `⚫ 暂时失联` | 重试 3 次打不开（含 Tunnel Error 1033 宕机） |
| `🔒 需人工验证` | 遇到人机验证弹窗（行为滑块 / 图片点选 / 待识别图形验证码） |
| `ℹ️ 未启用签到` | 站点接口明确返回「签到功能未启用」（非漏签） |
| `⚠️ 状态未知` | 打开了但判据不明确 |

奖励金额各站币种/单位不同（`$`/`¥`/`¤`），合计仅供参考，不做跨站折算。

---

## 同步规则

本 skill 必须**双向同步**（见 `~/.claude/projects/.../memory/skill-dual-copy-sync.md`）：

- 系统：`~/.claude/skills/gongyi-checkin/`（运行时实际加载目录）
- 项目：`~/Documents/youngs/learn-claude-code/skills/gongyi-checkin/`

改完两处都要一致。用 `diff -rq -x data -x __pycache__` 校验。

---

## 目录

```
gongyi-checkin/
├── SKILL.md
├── EXPERIENCE.md              # 手写脱敏站点笔记与踩坑记录
├── scripts/
│   ├── chrome_driver.py   # AppleScript↔Chrome 驱动 + 探针 + 分类器
│   └── run_checkin.py     # 主流程 + 报告渲染
└── data/                  # last-run.json / last-run.md / run-log.md（不入库）
```
