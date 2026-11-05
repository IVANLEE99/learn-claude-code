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

### 有人机验证的站（不要尝试自动过）
- **PM-Plan**（`https://plan.pmcat.top/`）：点 `今日签到` 弹「签到人机验证 — 拖动滑块拼合缺口」。
- **简直了**（`https://jianzhile.vip/console/personal`）：点 `Check in now` 弹
  「Security verification / Refresh captcha」图形验证码。
- 这两类**标记为 `🔒 需人工验证`**，脚本不重试、不绕过。用户自己点一下即可。

### dicksuck / 多数 new-api 站：重复点会被拒
- 页面文案 `You can only check in once per day` = **今天已经签过了**，不是失败。
- 判据要包含这句：见到它直接判 `done`，不要再点、不要报 pending。

### 每日签到 - lOXO — https://loxo.cc/check-in
- 2026-11-04 独立签到页。字段齐全：`今日奖励 $X`、`可用余额 $X`、
  `今日已签到 · 明天 00:00 再来`、月历显示每日金额。
- 余额标签在**下拉浮层**里（`pointer-events-none absolute right-0 top-full`），
  但 innerText 仍包含，DOM 抓取可拿到。

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

### 42 API — https://api.42x.shop/profile
- 2026-11-04 `ERR_CONNECTION_CLOSED` 打不开 → 暂时失联。

### [35ldc]luckyg — https://luckyg.131518.xyz/profile
- 2026-11-04 `ERR_CONNECTION_CLOSED` 打不开 → 暂时失联。

### [api生图]流光绘境 — https://images.aihappy.indevs.in/#/profile
- 2026-11-04 `ERR_CONNECTION_CLOSED` 打不开 → 暂时失联。

### 子非鱼 status / CHY 状态页
- 2026-11-04 uptime-kuma 状态页，不签到，已在 `SKIP_URL_FRAGMENTS` 排除。

## 下次开工先看

1. `SKILL.md` 的「六个会静默失败的坑」——`esc()` 注释吃掉脚本是头号杀手，
   「读到上一个站点的页面」是危害最大的（数字看着对但全是错的）。
2. 「站点形态」表 + 本文件的「站点笔记」，判断新站点归哪一形态。
3. 新站点先 `--dry-run --url <地址> --name <名字>` 单站试，别直接全量点。

---

> **本文件只放手写、脱敏后的经验。** 金额一律写 `$X` 占位符——
> 本仓库是公开的，真实余额/奖励不得入库。
> 脚本自动写的运行归档在 `data/run-log.md`（已 gitignore）。

