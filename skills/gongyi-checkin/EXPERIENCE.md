# 签到经验记录

> 这个文件是**累积**的：每次跑完 `run_checkin.py`，把新学到的站点特性追加到
> 「站点笔记」节；通用的坑和判据回写到 `SKILL.md`。
> 格式约定：**一条一行**，以 `- ` 开头，注明站点名与现象，便于下期 grep。

## 通用经验

- 2026-11-04 登录态只在**日常 Chrome 默认 profile**（`~/Library/Application Support/Google/Chrome/Default`），
  28 站中 26 站有 cookie；仓库的 `mcp-chrome` profile 是 0/28。所以只能附着日常 Chrome，不能换 profile。
- 2026-11-04 Chrome 136+ 默认 profile 不允许 `--remote-debugging-port`，CDP 路线整体不可用；
  改用 AppleScript `execute javascript`，可在任意 tab 读 DOM + 点击。
- 2026-11-04 new-api 系站点**打开页面即签到**：加载时自动发 `GET /api/user/checkin?month=YYYY-MM`，
  无需点按钮。任何 Router 用的是 `GET /api/user/sign_in`。
- **2026-11-06 判 done 的最终依据只能是「可点按钮在不在」，不是整页文本**：
  咕咕嘎嘎 / HappyCoding 的卡片在**未签到时**也常驻一句 `Checked in`（隐藏态/文案残留），
  旧逻辑整页扫到 `Checked in` 就判 done → `already_done` 直接跳过点击，**当天实际没签**（用户发现漏签）。
  修法：页面存在**可见且可点的动作按钮**（`Check in now` / `立即签到` / `去签到`…）时一律判 pending，
  除非同时出现硬完成语（`今日已签到` / `明天 00:00 再来` / `You can only check in once per day`）。
- 2026-11-04 **导航后必须确认文档已提交**（读页面自己的 `location.href` 比对域名），
  否则会读到上一个站点的页面——奖励/余额全是上一个站的，数字看着正常所以不会报错。
  每次导航先走 `about:blank`，否则同 URL 不重新请求文档。
- 2026-11-04 「标签→数值」**不要用正文扫描**：有的站值在标签前（`$X Current balance`），
  有的在后（`当前余额 $X`），扫描会把邻栏数字绑错（实测误取用户 ID、累计总额、消费额）。
  改用 **DOM 邻接**：找 textContent 恰等于标签的元素，取其兄弟里的金额。
- 2026-11-04 奖励金额**必须带货币符号**且与「今天/今日/Today」相邻：
  `Checked in today 99 Total check-ins` 的 99 是签到次数；
  `累计获得: N 次` 是历史累计，都不是今天的奖励。
- 2026-11-04 余额标签可能只在 **hover 浮层**里（innerText 会丢），金额却在 header；
  所以余额走 DOM 邻接而不是 innerText 文本。
- **2026-11-11 00:05 签到失败不是 Chrome 挂了，是 Mac 锁屏**：脚本报
  `cannot talk to Chrome (tabs=__TIMEOUT__). Is Chrome running?`，但 Chrome 进程在跑、单实例、无绑定冲突。
  根因是 macOS 锁屏时不向 GUI 应用投递 AppleEvent（TextEdit/Safari/Finder 同样全超时）。
  判据：`ioreg -n Root -d1 -a | grep -A1 CGSSessionScreenIsLocked` → `true` 即锁屏；
  解锁后该 key **整个消失**（grep 命中 0），要配合 `IOConsoleLocked` 一起看。
  `caffeinate -u` 唤醒不了锁屏。处理：**不要 kill/重启 Chrome**，先判锁屏，锁屏就等解锁再跑。
  详见 SKILL.md 坑 15。
- **2026-11-11 书签文件夹 id 变了**：`daily-check-in` 的 id 从 `6233` 变成 `5923`
  （Chrome 在文件夹被移动/重建时重新生成 id；`Bookmarks.bak` 里也没有 6233）。
  旧脚本只按 id 找 → `SystemExit: bookmark folder 6233 not found`，31 个站一个没跑。
  修法：`read_bookmarks()` 找不到 id 时**按名字 `daily-check-in` 回退**，日志打印实际 id。
  详见 SKILL.md 坑 16。
- **2026-11-11 AppleScript 绑的是 mcp-chrome，不是日常 Chrome**：机器上有两个 Chrome 时，
  `tell application "Google Chrome"` 绑到 ai-news-factory 的那个
  （`--user-data-dir=.../mcp-chrome-10b76e5`，CDP 9222），`name of window 1` 返回「公众号」。
  判据：先 `URL of every tab of every window` 看是不是五个平台页面。
  `open -a "Google Chrome"` 不改变绑定；必须按 `kill daemon → kill mcp-chrome → 复查` reclaim，
  **绝不 kill 不带 `--user-data-dir` 的日常 Chrome**（30 站登录态全在它那儿）。
  签完 `bash data/_restart_upload_daemon_1111.sh` 恢复 pipeline。详见 SKILL.md 坑 17。
- 2026-11-04 单站打不开重试 3 次即可判「暂时失联」，不要死磕（可能是站点自己挂了或被墙）。

## 站点笔记

### Any Router — https://anyrouter.top/console/personal
- 2026-11-04 打开即签到（`GET /api/user/sign_in`），**页面上没有任何签到卡片**，
  靠 DOM 找不到签到元素，只能靠「页面加载发过 sign_in 接口」判定。
- 余额标签是 `Current balance $X`（英文），不是「余额」。

### 42 Plan — https://plan.42x.shop/dash
- 2026-11-04 是套餐购买页（42lite/42plus/42pro），**不是签到页**，无签到按钮。
  打开不发 checkin 接口。

### 薄荷公益站 — https://up.x666.me/
- 2026-11-04 转盘签到站：`签到` 按钮 class `spin-button`，已签到时文案 `今日已签到` 且 disabled。
  接口家族是 `/api/checkin/status` + `/api/checkin/calendar`（**不是** `/api/user/checkin`）。
- **2026-11-05 真控件是「开始转动」（转盘）不是「签到」**：顶部 `<A>签到</A>` 只是切换视图，
  点它永远无效。要点 `BUTTON` 文案 `开始转动`；点击后变 `转动中...`(disabled)，
  **必须 reload 才能读到结果**（动画不结束按钮一直卡住）—— reload 后看
  `余额` 是否增长 + `已连签 N 天` 是否 +1 + 按钮是否变 `今日已签到`。
- **2026-11-06 重置窗口是 08:00，不是 00:00**：卡片写「每天8点刷新」，
  `GET /api/checkin/status` 的 `can_spin` / `today_record.spin_date` 按 08:00 切窗口。
  00:05 跑时页面显示「今日已签到」属于上一窗口，**不是假阳性**；
  08:00 之后 `can_spin` 会重新变 true，需要再转一次。判据以接口为准，别只看页面文案。

### Fengwind API 福利站 — https://api-welfalre.fengwind.com/
- 2026-11-04 自研站，顶部有 `签到` 导航项（`router-link-ex`）+ 页面内 tab 按钮 `签到`。
  文案 `今日已签到`。接口 `/api/checkin/status`。
- **2026-11-05 签到前必须先选「额度有效期」radio**：`input[name="checkin-validity"]`
  取值 `d1/d2/d3/d5/d7/permanent`（1天100% / 2天80% / ... / 永久10%）。
  选 `d1` 收益最高。**不选 radio 直接点签到无效**。
- 真正的签到按钮是页面底部那个 **50×36 的小 `BUTTON 签到`**（不是顶部导航的 `<A>签到</A>`，
  也不是 tab 栏那个 302×29 的）。按面积取最小的 `BUTTON` 才命中。
- 成功标志：`今日已签到` + `本次获得 $X` + `已入账`。
- 书签名带「[禁止测活]」的站点**不要发探活请求**（用户标注，见 Fengwind 的同名书签）。

### Pigeonw 公益站 — https://new-api.pigeonw.com/profile
- **2026-11-06 掉登录后的真坑：必须先在登录页勾「User Agreement」复选框，`Continue with LinuxDO` 才有反应**。
  不勾时点了完全无跳转（URL 停留在 `/sign-in?redirect=%2Fprofile`），
  脚本会误报「点了登录但 connect.linux.do 没有授权按钮」（`NO_AUTH_BUTTON`）。
  修法：点 OAuth 前先 `document.querySelector('input[type=checkbox]').click()`（该复选框被藏成 1×1）。
  勾选后正常跳 `connect.linux.do` →「允许」→ 回 `dashboard/overview`，再进 `/profile` 点 `Check in now`。

### [50ldc]三水公益站 — https://api.3sbqs.xyz/profile
- 2026-11-06 头部显示 `付费 $0 免费 $16.12`。**签到奖励进的是「免费」额度，付费余额真的是 $0**。
  只报 `$0` 没用，余额解析要在此情形回落到「免费/赠送/Gift」标签。

### 君の星辰 — https://ai.centos.hk/wallet
- 2026-11-06 直接查接口：`GET /api/user/checkin?month=2026-11`（带 `New-Api-User` 头）
  返回 `{"message":"签到功能未启用","success":false}` —— **该站没有签到功能**，不是失败。
  `/wallet`、`/profile`、`/dashboard`、`/console/personal` 都没有签到卡片，也没有 checkin 资源请求。

### 月城公益站：余额可以是负数
- **2026-11-06 实测 `当前余额 -$13.92`**。金额正则必须允许前导负号，否则整段解析成 None。


### 验证码站点处置经验（2026-11-05 实测）
- **PM-Plan**（`https://plan.pmcat.top/`）：点 `今日签到` 弹「签到人机验证 — 拖动滑块拼合缺口」。
  前端收集 `track: [{x, y, t}]` 高频轨迹数组送审，模拟拖动会被报 `vr.reason === 'bot_behavior'` 拦截。
  **处置策略**：脚本开标签页置顶并唤起弹窗，**需人工在浏览器中拖动滑块 1 秒完成**。
  2026-11-09 遇 Cloudflare Tunnel Error 1033 隧道宕机。
- **简直了**（`https://jianzhile.vip/console/personal`）：点 `Check in now` 弹
  「Security verification / Refresh captcha」5位彩色英数字图形验证码。
  **处置策略**：提取 `<img src="data:image/png;base64,...">` 进行 OCR 识别，通过 React 状态绑定或置顶标签页人工输入 5 位验证码完成签到。

### dicksuck / 多数 new-api 站：重复点会被拒
- 页面文案 `You can only check in once per day` = **今天已经签过了**，不是失败。
- 判据要包含这句：见到它直接判 `done`，不要再点、不要报 pending。
- **2026-11-07 已把这两句并入 `DONE_PATTERNS`**（之前只写在文档里、代码没实现）：
  `You can only check in once per day` / `Do not repeat check-in`。
  起因：Aether API 点完签到后**按钮文案不变、仍显示 `Check in now`**，
  只有服务端 toast 能证明已签 → 旧逻辑把它判成 pending，每轮都白点一次。

### Aether API — https://api.abnt.it/profile
- 2026-11-07 点 `Check in now` 成功后**按钮不翻转**（仍是 `Check in now`，不 disabled、文案不变），
  页面也不出现 `Checked in`，唯一证据是 toast `You can only check in once per day`。
- 所以「按钮优先」规则要配合硬完成语白名单；没有硬完成语的站只能靠服务端拒绝文案判 done。

### 链趣 — https://qulink.cyou/points/check-in
- 2026-11-07 新增。积分制（不是额度）：按钮 `签到领 10 积分`（673×44，很宽），
  另有 `刷新签到状态` 和顶部 `<A>每日签到`（78×44）。
- 成功标志：`今日 09:00:00 已领取，明天再来。` + `今日已签到`。
- 重置窗口 **北京时间 00:00**。动作按钮文案是 `签到领 N 积分`（不是「立即签到」），
  需在动作词表里补 `签到领`。
- ⚠️ **签到状态是异步拉的，必须等**：页面先渲染「请先确认签到状态 / 正在读取签到状态」，
  约 8–10 秒后才变成「今日已签到」。用 6 秒的 settle 会读到加载中态，
  被误判成 `pending`（然后就白点一次 `每日签到` 导航链接）。
  实测：6s → pending 假阳性；15s → done 正确。**该站 settle 至少 12 秒。**

### 皮皮智绘 — https://img.pipiwangcom.com/
- 2026-11-07 新增书签。按钮 `签到 +100~200`，余额在 `当前余额`。
  点完余额 370 → 490（本日 +120）。

### 每日签到 - lOXO — https://loxo.cc/check-in
- 2026-11-04 独立签到页。字段齐全：`今日奖励 $X`、`可用余额 $X`、
  `今日已签到 · 明天 00:00 再来`、月历显示每日金额。
- 余额标签在**下拉浮层**里（`pointer-events-none absolute right-0 top-full`），
  但 innerText 仍包含，DOM 抓取可拿到。
- **2026-11-05 避坑**：`已连续签到 N 天` 是连签统计，不是完成标记！未签到时显示「今日奖励 待领取」
  和按钮「立即签到」；若把「已连续签到」放入 `DONE_PATTERNS` 会导致未签到时误报已签到。
- **2026-11-06 两个真 bug（已修）**：
  1. **点错目标**：侧边栏 `<A>每日签到</A>`（231×40）比真按钮 `<BUTTON>立即签到</BUTTON>`（384×48）**面积更小**，
     旧的「最小面积优先」选中了导航链接——点完只是重新进入当前页，状态永远 pending。
     修法：候选排序改为 `导航链接 > 动作词 > 面积`，动作词（立即/现在/领取/去签到/Check in now）优先。
  2. **奖励误绑连签**：页面上「今日奖励 / 待领取 / 已连续签到 7 天」相邻，
     label→value 的兄弟扫描只要「含数字」就把 `7` 绑成今日奖励。
     修法：兄弟节点必须是**整段就是金额**（`^[$¥€￥]?\d[\d,.]*$` 之类），并跳过 待领取/未领取/暂无。

  真正的完成标记是 `今日已签到 · 明天 00:00 再来`。

### 简直了 / 魔方 / Ark API 等 Semi-UI 系 — `*.vip/console/personal`
- 2026-11-04 卡片文案 `Daily Check-in` + `Checked in today, total check-ins NN day`，
  余额 `Current balance`（或 `当前余额`）。奖励写在按钮里 `Today +$X`。

### 月城公益站 — https://52ccl.net/profile
- 2026-11-04 用 `group/card` 形态：按钮文案 `每日签到已签到今天 +$X`，
  内层 `已签到` 徽章 class `inline-flex items-center gap-1 rounded-m`。

### 兆丰 / AzureKilnAPI — https://newapi.azurekiln.cn/profile
- 2026-11-04 **SPA 加载失败**：`#root` 为空，React 未挂载。
  原因疑似直连时 JS bundle 被截断（直连 43KB vs 走代理 370KB）。
  3 次重试都空 → 判「暂时失联」。
- **2026-11-06 复现**：`#root` 仍为 0 子节点；多个 vendor chunk 的 `transferSize=0`（6ms 返回），
  只有一个 206KB 的 chunk 花了 7.3s。属于**站点自身 chunk 加载失败**，不是本机网络策略。
  连续两天如此 → 建议当作「站点不可用」，不要反复重试占用整体时长。

### 42 API — https://api.42x.shop/profile
- 2026-11-04 `ERR_CONNECTION_CLOSED` 打不开 → 暂时失联。

### [35ldc]luckyg — https://luckyg.131518.xyz/profile
- 2026-11-04 `ERR_CONNECTION_CLOSED` 打不开 → 暂时失联。

### [api生图]流光绘境 — https://images.aihappy.indevs.in/#/profile
- 2026-11-04 `ERR_CONNECTION_CLOSED` 打不开 → 暂时失联。
- **2026-11-05 实测通过（LinuxDO OAuth + 自动签到）**：
  未登录时会重定向到 `#/login?redirect=/profile`（登录页字符数较短，`open_station` 门禁已适配）。
  页面有「使用 LinuxDO 登录」按钮，点击并完成 `connect.linux.do` 授权后自动跳转回个人设置。
  已登录页有「签到」按钮（若已签到显示「已签到」），奖励展示在相邻 `span`（如 `签到 19` 代表 +19 额度），
  余额展示为「可用额度 $X」。已签到直接判 `done`。
- **2026-11-06 会话不持久**：00:07 用 OAuth 登录并签到成功后，隔一段时间再打开又回到
  `#/login?redirect=/profile`。**但签到记录是保留的**（页面上仍显示 `签到 12 已签到`）。
  所以「再次打开是登录页」不代表签到没成，重走一次 OAuth 即可确认，不要判失败。

### 子非鱼 status / CHY 状态页
- 2026-11-04 uptime-kuma 状态页，不签到，已在 `SKIP_URL_FRAGMENTS` 排除。

## 下次开工先看

0. **定时放 08:05，不要 00:05**：站点的签到窗口分两套——`00:00` 重置（lOXO / 咕咕嘎嘎 / Pigeonw /
   月城 / 三水 / 简直了 / 流光绘境）和 `08:00` 重置（薄荷 / Fengwind / dicksuck / dudu / Hlool / luckyg /
   Huan / 烁 / 魔方 / CM-API / Orbitix / 方舟）。00:05 跑签的是「上一个 08:00 窗口」，
   白天打开站点会重新显示「今日尚未签到」；08:05 跑则两种口径都在当日窗口内。

1. `SKILL.md` 的「十四个会静默失败的坑」——`esc()` 注释吃掉脚本是头号杀手，
   「读到上一个站点的页面」是危害最大的（数字看着对但全是错的）。
2. 「站点形态」表 + 本文件的「站点笔记」，判断新站点归哪一形态。
3. 新站点先 `--dry-run --url <地址> --name <名字>` 单站试，别直接全量点。

---

> **本文件只放手写、脱敏后的经验。** 金额一律写 `$X` 占位符——
> 本仓库是公开的，真实余额/奖励不得入库。
> 脚本自动写的运行归档在 `data/run-log.md`（已 gitignore）。

