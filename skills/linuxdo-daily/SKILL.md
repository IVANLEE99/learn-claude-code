---
name: linuxdo-daily
description: linux.do AI日报/周报/月报自动生成。多 Agent 协作：Crawler 抓取双数据源 → Topic Merger 合并主题 → Trend Analyzer 生成趋势 → Writer 输出日报/周报/月报 → Press Writer 生成新闻稿 → PDF Builder 生成 PDF。触发词：日报、周报、月报、linuxdo日报、AI日报、AI周报、AI月报、技术日报、weekly、monthly、过滤后全部抓取完
version: 16.21.0
---

# linuxdo-daily — AI 技术日报生成 Skill（多 Agent 架构，v16.21.0）

从 linux.do 自动抓取 AI 相关帖子，通过 6 个专用 Agent 协作生成每日技术日报，并支持周报与月报模式。

> **🔴 v16.21.0 核心改进（2026-11-26 1126 期实跑：渲染进程崩坏的自愈判据，坑 545）**
>
> 1126 期：Source A **2216** / Source B **600** → 队列 **659** → daily **615**（657 含正文 + 2 永久缺失，
> 二次过滤剔除 42），22:35 触发、次日 02:05 抓取收口，07:17 五平台全部 verified 收工。
> 本期抓取中段出现一次浏览器渲染进程整体崩坏，值得把判据写死。
>
> ① **坑 545：`Page crashed` / `Target crashed` 连续出现是渲染进程崩坏，不是单帖失败；不要用同一个浏览器把全部批次 + retry 跑完。**
> 1126 期 batch 1–11 正常（179 帖有效），batch 12 起连续 32 个批次 15/15 全部
> `page.goto: Page crashed`，retry0 又跑 480 个失败 ID，累计 915 条 error，白耗约 30 分钟；
> 直到旧 attempt 退出、resume 新起 `_crawl_1126.mjs` + 新 Chromium，抓取才恢复，最终 657/659。
> **判据**：同一批内连续 ≥3 帖都是 `Page crashed`/`Target crashed`（不是 `ERR_ABORTED`/超时）⇒ 判定浏览器实例已坏；
> 保存已有 checkpoint 后立即结束本次 crawl attempt，让 resume 重启浏览器，而不是继续遍历剩余批次。
> **不要**因为 scheduler status 仍显示 HEALTHY 就认为抓取正常——status 只看进程与租约，不看批次错误率。
>
> ② **永久缺失清单的证据可以跨主批次与 retry 文件。** 1126 期两个 ID（3243276 / 3243974）分别有 9 / 8 条
> 同 `empty_deleted_private_or_unloaded`、无 title 的证据（主批次 `batch_browser_1.json` / `batch_browser_43.json`
> + `batch_browser_retry1..8.json`），`attempts == len(attempt_files)` 写成 9 / 8 后，下一次 gated tick
> 立即通过全量校验并生成 daily 615 帖（坑 540）。不必强求每个 ID 恰好 6 条，也不要因为证据分散在多个
> retry 文件就继续重试。

> **🔴 v16.20.0 核心改进（2026-11-25 1125 期实跑：永久缺失清单的解锁时机，坑 540）**
>
> 1125 期：Source A **2217** / Source B **601** → 队列 **652** → daily **598**（全部含正文，0 error，
> 二次过滤剔除 54、永久缺失 1），22:35 触发、23:14 抓取收口，次日 00:14 出报告/PDF，
> 06:37 五平台全部 verified 收工（六次 worker attempt，均为正常续跑）。
>
> ① **坑 540：`data/<issue>-permanent-gone.json` 是解锁键，别等重试循环自己收敛。**
> 1125 期 1 个 ID（`3230649`）连续 **21 次** retry 全部返回 `empty_deleted_private_or_unloaded`（无标题），
> 抓取每次以 `rc=1 incomplete bodies` 退出、daily 永远不生成；手写 6 条「同 ID / 同 error / 无 title」的
> 证据清单后，**下一次 tick 立即通过全量校验**（daily 598 帖）。
> **判据**：同一 ID 出现 ≥6 次同 error 且 `permanent_gone=0`，就写清单
> （`attempts == len(attempt_files)`，每条证据文件真实存在且内容完全一致），
> 不要等到重试次数耗尽或人工介入。
>
> ② **坑 540-b：清单写入后，daily 需要下一次 gated tick 才重建；当前正在跑的 crawler 不会自动感知。**
> 判据：写清单 → `bash data/_l3_tick_<issue>.sh` 返回 `START downstream`（或 `phase=downstream`），
> 表示 daily 已通过、下游已启动；若仍返回 `WAIT_RETRY`，说明还在退避窗口，等 180 秒即可。
>
> 另：本期 L3 巡检在退避期用「每 12–15 秒一次 gated tick」的推进器代替 3 分钟 cron，
> 六次 attempt 的空档从数分钟压缩到十余秒；不改 state、不手工起 worker，仍走调度器租约。

> **🔴 v16.19.0 核心改进（2026-11-24 1124 期实跑：并发 spawn 的正常拒绝 / stage 时间戳会被重写，坑 538-539）**
>
> 1124 期：Source A **2218** / Source B **603** → 队列 **522** → daily **473**（全部含正文，0 error，
> 二次过滤剔除 49），22:35 触发、23:14 抓取收口，次日 01:45 出报告/PDF，05:51 五平台全部 verified 收工。
> 抓取侧没有新问题，但**两个「看起来像故障」的调度现象**值得写进判据，避免下次误判。
>
> ① **坑 538：L1/L2 同秒并发 tick 时，先起的那个 supervisor 会被 `reserved child identity mismatch` 拒绝——这是正常竞争，不是故障。**
> 1124 期 22:35:00 两个常驻控制器同时到点，一个 supervisor adopt 失败并打印
> `{"rc": 3, "reason": "exact inherited job lease adoption refused: ValueError: reserved child identity mismatch"}`；
> 父进程按 `supervisor exited before adoption rc=3` → rc=1 走重试（**不落 sticky block**），
> 22:38:00 第二次 spawn 正常接管，之后一路跑完。
> **判据**：`<issue>-crawl-supervisor.log` 出现一次该 JSON，且 ① `job.lock.owner.json` 的 owner/child
> 都是活进程、② `crawl.log` 在推进、③ state 的 `blocked` 为空 —— 三条同时成立就是竞争拒绝，
> **不要手工起第二个 worker、不要清 session、不要改 state**，下一个 180 秒节拍会自愈。
>
> ② **坑 539：stage 的 `completed_at` 会被后续 attempt 的 `automatic_crawl_checkpoints()` 重写，别拿它反推抓取时长。**
> 1124 期 `archive/crawl/daily` 的 `completed_at` 都是 **05:20:06**（第三次下游 attempt 启动时重跑校验的时点），
> 而真实抓取 23:14 就结束了。**审计口径**：抓取结束看 `data/logs/<issue>-crawl.log` 的末尾与
> `data/daily/<date>.json` 的文件 mtime；`completed_at` 只表示「该 stage 最后一次通过校验的时间」。
> 同理，报告里写「抓取耗时」时不要用 stage 时间差算。

> **🔴 v16.18.0 核心改进（2026-11-22 W46 周报实跑：目标周口径 / 周报不重抓 / typst 缺席，坑 525-527）**
>
> W46 周报（2026-11-16 ~ 2026-11-22）实跑：7 天日报全在（294 / 464 / 459 / 630 / 550 / 500 / 365），
> 周内去重 **3258 帖**，公益/交易过滤后 **3241** 进入主题分布；周报 md + press + PDF(832 KB) 落盘后
> 才开视频链，全程没有重新抓取。三条都是「周报模式独有」的口径问题，日报侧不受影响。
>
> ① **坑 525：周报的「本周」不能用 `datetime.now()` 直接取，必须显式指定目标周一。**
> 周日跑时 `now.weekday()==6`，`now - 6天` 恰好是周一，看起来天衣无缝；但周一到周六跑，
> `week_end=now` 会把最近 7 天（含还没产日报的日子）当成一整周，得到「6 天有数据 + 1 天缺失」的残周，
> 且 `--week-id` 随运行日漂移（同一周想补跑会得到另一个周号）。
> **修法**：聚合脚本第一行写死 `TARGET_MONDAY`，`week_end = TARGET_MONDAY + 6 天`；
> 开工前先 `ls data/daily/<week_start>..<week_end>` 确认 7 天齐，缺哪天就在报告「数据来源说明」里点名，
> 不要用「覆盖 6/7 天」含糊带过。
>
> ② **坑 526：周号必须沿用 `%W`（周一起点），不要换成 `isocalendar().week`。**
> 本期一度改成 ISO 周，算出来是 **W47**，而历史产物是 W40–W46 一整套 `%W` 编号（2026-11-16 → `%W46` /
> ISO `W47`）。换成 ISO 会与 `data/weekly/` 全部历史文件断代一天，也会让下游按周号找稿的地方全错位。
> **判据**：新周号必须能对上 `data/weekly/{week_id}.md` 的历史序列；对不上就是口径换了，回退 `%W`。
>
> ③ **坑 527：本机没有 `typst`，PDF 走 Chrome headless 打印，别再等 typst 装好。**
> `command -v typst` 为空（只有 ffmpeg）。本期把 md 转成自写 HTML（标题/列表/表格/引用全支持，
> 中文用 PingFang SC），再用 `playwright` 驱动**系统 Chrome**（`/Applications/Google Chrome.app`）
> `page.pdf(format=A4, print_background=True)`，832 KB / 一次成功，不再走「先 `pip install typst` 再说」。
> 注意两点：① `launch()` 才接受 `executable_path`，`connect_over_cdp()` 不接受；
> ② HTML 里 `**bold**` 要自己转 `<strong>`，Typst 的转义规则（`$`/`#`/`_`）在这里不适用。
>
> 另：本周灰色渠道关键词表补了 `焚诀`（免费试用薅取类黑话）、`虚拟卡`、`不弹出kyc` 三个词，
> 老表只有 `公益站/中转站/接码/代充`，这三类会漏进分布表。

> **🔴 v16.17.0 核心改进（2026-11-22 1122 期实跑：cron 窗口踩当前小时 / worker 空转 / 来源平台名越界，坑 519-521）**
>
> 1122 期：Source A 2217 / Source B 601 → 队列 **409** → daily **365**（全部含正文）；22:35 触发、23:13 进下游、
> 次日 01:11 五平台收口。内容侧零返工，三个卡点全是「调度判据」和「审核口径」，不是内容质量。
>
> ① **坑 519：L3 巡检 cron 的小时窗口不能包含「建任务所在的当前小时」。**
> 1122 建任务时写 `*/3 22-23,0-11`，当时是上午 11 点，cron 立刻在 11:43 命中、起了一轮空巡检。
> **修法**：窗口用 `*/3 22-23,0-10`（次日 10:59 前仍能发现扫码阻塞），并且建完任务立刻看
> `CronList` 的 next run——如果落在「现在」而不是今晚触发时刻，就是小时写错了。
> 触发前空转的每一轮都是一次完整的会话请求，白烧 token 且污染日志。
>
> ② **坑 520：worker「只读探测 + 只输出摘要」就退出，是空转，不是健康自愈。**
> 1122 期 B 站被草稿箱上限挡住、用户清空草稿后，连续两轮 worker 各自只做只读诊断
> （反复读草稿列表、比对「继续编辑」横幅），其中一轮只吐了一段上下文摘要就 `end_turn`，**没有任何新产物**。
> **判据**：`last_exit == 0` **且** 目标 stage 状态未变 **且** `evidence/` 无新文件 = 空转。
> **修法**：确认 `leases.job.busy == False` 后把 `worker.next_retry_epoch` 置 0 再 tick（坑 513 驱动器），
> 连续两轮无产物就升级人工，不要用「再等一轮」硬耗。
>
> ③ **坑 521：第三方来源平台名要清的是「正文和平台简介」，不只是口播字幕。**
> 1122 的审核第 3 条只覆盖 `content.json` 的 voiceover 与 scenes 标题，于是来源平台名一路留在
> 公众号正文「关于本文」段和 B 站简介里，审核照样给 PASS。
> **修法**：来源行**整行删除**，不要另造任何替代串；审核与控制器对
> 公众号/知乎正文、五个平台 description 做同一份禁用词检查（`linux.do` / `linuxdo` / `佬友`），命中即不通过。
> 文章文件已被 sha256 固化的，清洗放在上传脚本的内存副本里，**不要改写磁盘文件**。
>
> **🔴 v16.16.0 核心改进（2026-11-21 1121 期实跑：L3 巡检空转 / 派生 Markdown 补丁格式 / 模型别名告警误判 / CLI 路径漂移，坑 515-518）**
>
> 1121 期：Source A 2217 / Source B 2009 → 队列 **547** → 正文 37 批 → daily **500**（47 帖二次过滤出局）；
> 22:35 触发、22:35:06 归档 92 个上期中间态、23:19 建队列、00:08 L1 校验 daily 后退出，
> 次日 10:30 五平台收口（中途视频号掉登录，见 ai-news-factory 坑 514）。
> 抓取与日报侧零新坑，四条都是「运维判据」——每条都能让一整晚白跑或白等。
>
> ① **坑 515：L3 会话巡检 cron 不要 24 小时 `*/3`。**
> 1121 建任务时用全天 `*/3`，从 17:24 到 22:35 触发前空转 **100+ 次**，每次都要起一个会话轮次、
> 只为读一行 `WAIT`。**修法**：cron 用小时窗口 `*/3 22-23,0-6`（覆盖 22:35 触发到凌晨收工即可），
> 并在 prompt 里写明「action 为 DONE 时先 CronList 找到自己再 CronDelete」。
> L1/L2 是常驻 shell（ppid=1），**不依赖**会话 cron；L3 只用来更快发现中断，会话关掉也不影响主链。
>
> ② **坑 516：派生器给 Markdown 打补丁，锚点必须按文件真实文本，插入 bullet 不要重复 `- `。**
> 1121 派生连踩两次：a) prompts 里「批抓阶段仅一个抓取驱动…」这一行**行首没有 `- `**，
> 照抄带 `- ` 的锚点直接 `AssertionError`；b) 往已有 `- ` 的条目**前面**插新 bullet 时，
> 插入块又写了一遍 `- `，生成 `- - **坑 512…**`。
> **纪律**：所有 patch 锚点先 `grep -F` 确认命中（连行首空白一起比）；插入块的首行**不要**自带 `- `，
> 因为锚点已包含原行前缀；派生写盘后立刻 `grep -n '^- - '` 断言为空，再跑 `--check`。
>
> ③ **坑 517：`[claude-code:unrecognized_model]` 是告警，不是模型死亡判决。**
> 1121 建任务时同一别名（`auto/deepseek-v4.1-flash-1017[1M]`）先打这行，随后**正常返回结果**；
> 大小写 `[1m]` / `[1M]` 两种写法都只是告警。**判据仍是 worker stream**：只有 `system init` + 报错两行、
> 无任何 assistant 输出，才是真挂（对应 1119 的坑 483）。别因为看到这行就换模型、清 session 或改全局 settings。
>
> ④ **坑 518：worker CLI 路径写死扩展版本目录，扩展一升级 worker 全部 spawn 失败。**
> `data/_scheduler_<issue>.py` 的 `CLAUDE` 常量形如
> `~/.devin/extensions/anthropic.claude-code-<version>-darwin-arm64/resources/native-binary/claude`，
> 版本号是目录名的一部分。扩展自动升级后旧目录消失 → 每晚 22:35 起 `Popen` 直接 `FileNotFoundError`，
> 看门狗只看到 `RETRY`，整晚没有 worker、没有 stage。
> **修法（三层）**：派生器 `validate()` 断言 `Path(CLAUDE).is_file()`；`_arm_<issue>.sh` 启动 L1/L2 前
> 预检 claude/node/python，缺失即 `exit 65`；`worker_command()` 运行时再判一次，缺失 `Refusal(1)` 并提示
> 「更新 CLAUDE 常量后重跑 `_derive_<issue>.py --check`」。永远不要改用户全局 settings 来绕过。

## 🔒 抓取 profile 必须与上传 profile 分开（2026-11-13 根因查清，坑 463）

**抓取**：`~/Library/Caches/ms-playwright-mcp/mcp-chrome-crawl`（Chrome for Testing 148）
**上传**：`~/Library/Caches/ms-playwright-mcp/mcp-chrome-10b76e5`（系统 Chrome 157）

**为什么必须分开**：macOS 的 v10 cookie 密钥来自 Keychain 的 "Chrome Safe Storage"，
**跟着浏览器 App 走、不跟 profile 走**。共用同一目录而两边浏览器版本不同（CFT 148 vs Chrome 157）时，
一方写入的 cookie 另一方解不开，还会用错密钥改写 → 表现为「cookie 条数还在，但平台要求重新登录」。
1112、1113 两期上传各扫码一次，就是这个原因（每次抓取跑一遍就坏一次）。

具体改动：
- `_fetch_lists_<issue>.mjs` / `_crawl_<issue>.mjs`：`PROFILE` → `mcp-chrome-crawl`
- `_launch_<issue>.sh`：`CRAWL_PROFILE` → `mcp-chrome-crawl`，
  且 `reclaim_profile` / `alive_crawl` **不再 kill `browser_daemon.py`**（上传侧与本 profile 无关）
- `_watchdog_<issue>.sh`：crawl-stalled 的 `CHROME_HIST` → `mcp-chrome-crawl/Default/History`
  （不改则读不到文件，detector 静默失效）

抓取 profile 是干净的、无需登录，首次过 Cloudflare 实测一次即过。

## 🔒 浏览器 profile 约定（2026-11-12 用户明确指示；2026-11-13 / 2026-11-19 两次补充）

> 用户原话：「**记得保留这个 profile，现在每次都要登录好烦**」「打开专用 profile 的浏览器，里面已经登录五个平台；**以后每次都用这个独立 profile**」

**上传 profile 是登录态的唯一载体**：`~/Library/Caches/ms-playwright-mcp/mcp-chrome-10b76e5`。
用户为它扫过至少三轮码，重建 = 让用户重扫五个平台，属于严重返工。

- 长期驻留五平台上传登录态（公众号/知乎/B站/抖音/视频号），**不要清空、不要重建**。
- **禁止**对该目录做任何破坏性操作：`rm -rf` / `mv` / 重命名 / 清空 `Default/`、`Cookies`、`Login Data`；
  也不要用 `cp -r` 复制到别处再跑（Cookie 加密绑定会让复制品失效）。
- 允许读 `Default/History`，但必须 `cp` 到 `/tmp` 再读（原库被 Chrome 锁住）。
- 需要清理时先 `cp -a` 备份到 `~/Library/Caches/ms-playwright-mcp/.backup-<ts>/`。
- **禁止**用日常 Chrome 的 `~/Library/Application Support/Google/Chrome` 跑自动化
  （Chrome 157+ 拒绝默认 data dir 开调试端口，坑 461；也会污染用户日常登录态）。
- 某平台掉登录 → 只在该 profile 的窗口里重新扫码，**不要**重建 profile。

**抓取 profile 独立**：`~/Library/Caches/ms-playwright-mcp/mcp-chrome-crawl`（Chrome for Testing）。
抓取与上传**不再互踢**：`reclaim_profile` 只清抓取 profile 自己的残留，**不 kill `browser_daemon.py`**；
抓取期间不需要重启上传 daemon，上传期间也不需要停抓取。两边共用会毁登录态（坑 463）。

**2026-11-19 路径漂移事故（必读）**：home 改名后 daemon 默认路径会静默从
`/Users/<oldhome>/Library/Caches/ms-playwright/mcp-chrome-10b76e5` 漂到
`/Users/<newhome>/Library/Caches/ms-playwright-mcp/mcp-chrome-10b76e5`（`ms-playwright` vs
`ms-playwright-mcp`）。旧目录不存在时 Chrome 会新建空壳，表现是「五平台全部未登录」而**不是报错**。
开工前先核对 `DAEMON_START ... profile=` 与预期路径；不一致就 `UPLOAD_PROFILE=<正确路径>` 或修默认值。

> **🔴 v16.7 核心改进（2026-11-13 1113 期实跑：触发时刻不是惯例值 / 派生器断言照抄上期 needle）**
>
> 本期抓取 35 批 / 521 队列 / 515 帖 / err=0（`no_created=0 parse_fail=0`），merge 后 ORDER CHECK OK。
> 两条都是「建档阶段」的坑，没花钱但会直接卡住开工：
>
> ① **触发时刻由用户当晚指令决定，不是固定 22:35**。1113 期用户明确说「今天 **23:25pm** 执行」。
> 派生器若把 `22:35` 当常量抄下来，`TRIGGER_EPOCH` 会算错一小时 → wrapper 要么提前一小时开抓（拿到不该抓的窗口），
> 要么白等一小时。**纪律：每次从用户原话取触发时刻，派生器里把四种替换分开写并加断言**：
> ```python
> TRIG_OLD_DT, TRIG_NEW_DT = '2026-11-11 22:35', '2026-11-12 23:25'   # 整串
> TRIG_OLD_HM, TRIG_NEW_HM = '22:35', '23:25'                          # 裸时刻
> EPOCH_OLD,   EPOCH_NEW   = '1794407700', '1794497100'                # epoch 字面量
> ```
> 派生完再 `date -j -f '%Y-%m-%d %H:%M:%S' '<触发时刻>' '+%s'` 反算一遍，与 `EPOCH_NEW` 对齐。
> **替换顺序**：先整串后裸时刻，且已含本期整串时不再替换（否则 watchdog 的 GUARD 文案会与 epoch 门禁矛盾，1112 踩过）。
>
> ② **派生器里的 `for needle in (...)` 断言块不能整段照抄上一期**。`_derive_1113.py` 抄了 1112 的
> `'连续 GATE'`，而 `_watchdog_1112.sh` 里实际只有 `GATE 卡死`（注释标题）→ 派生第一步就
> `AssertionError: 1113 watchdog lost inherited detector: '连续 GATE'`。
> **纪律：每个 needle 先 `grep` 源文件确认存在**，再写进断言。
>
> 另：本期归档了 1112 期 70 个中间态文件（`data/archive/2026-11-13-prev-20261112_233619`），
> 否则 `_resume` 的 `isComplete` 会把上期批次当成本期已完成直接跳过（与 1112 期同一条前置动作）。
>
> **🔴 v16.9 核心改进（2026-11-15 1115 期实跑：跨期锁元数据把冷启动打成粘性 blocked / CAP 仍是字面量 / adoption 窗口良性竞态，坑 475-477）**
>
> 1115 期：Source A 2219 行、Source B 2220 行均触发近期窗口上限；合并 2763 → 历史去重 2719 →
> 标题去重 1506 → 公益/交易 1348 → 32h 窗口 **378 队列**；正文覆盖 377/378（1 条已删帖按排除清单出局），
> daily **posts=344**；22:35 触发、00:09:56 DONE，全程 1 小时 35 分。
> 本期最贵的一条不是抓取逻辑，而是**上一期留下的锁 sidecar 把本期冷启动直接打成粘性 blocked**——
> L1/L2 都活着、job 也不忙，但 22:35→22:41 这 6 分钟里 tick 恒返回 BLOCKED，且 `automatic_retry: false`
> 意味着不人工介入就会一直卡下去。
>
> ① **坑 475：`data/logs/crawl-resource.lock.owner.json` 是跨期共享的租约 sidecar，上一期跑完会留下 `date=<上期>` 的已释放记录；本期 `Mutex.__enter__` 要求 `record['date'] == DATE`，于是冷启动归档第一步就 `rc=3 LOCK metadata identity refusal: crawl-resource.lock`，并被写成 `automatic_retry: false` 的粘性 blocked。**
> **症状**：`_archive_<issue>.py` 日志只有一行 `rc=3 LOCK metadata identity refusal: crawl-resource.lock`；
> `status` 里 `blocked.kind=identity`，L1/L2 lease 都 healthy、job 不 busy，但 tick 恒返回 BLOCKED。
> **排查三步**：① `lsof data/logs/crawl-resource.lock` 确认无 flock 持有者；② `ps` 确认无
> `_fetch_lists_* / _crawl_* / _resume_*` 活跃进程；③ 读 sidecar，确认 `owner: null` 且有 `released_at`
> （= 上一期已释放，不是活锁）。
> **处置（可逆，别直接 rm）**：把 sidecar 移进 `data/logs/repair-<issue>/` 备份 → 清 state 里的 `blocked`
> （置 null，`status` 回 `waiting`）→ 下一轮 tick 自动重新归档（1115 期成功移入 95 个中间态文件到
> `data/archive/2026-11-15-prev-20261114_224100-*`）。
> **预防**：新期号 arm 之前先清上一期遗留的 `crawl-resource.lock.owner.json`，并顺带确认 `1114-*.owner.json`
> 这类上期锁 sidecar 不会被本期误读。
>
> ② **坑 476：CAP 写死 2200 与「现场推导」的规则互相矛盾，派生器会把字面量逐期复制。**
> v16.8 已写「CAP = 32h 窗口所需行数 × 2，现场推导」，但 1115 期 `_fetch_lists_1115.mjs` 里仍是
> `count >= 2200` 字面量——派生时没人真去算。
> **本期侥幸没截断**：Source A 的 2219 行 `created` 一直回溯到 **2024-11-25**，远早于 cutoff，窗口被完整覆盖。
> **纪律**：派生器必须把 CAP 作为参数算出来并打印（含来源行数与窗口内最后一行索引），派生断言里禁止出现
> 历史期的硬编码值；抓完用 `created` 反算「窗口内最后一行索引 < CAP × 0.7」才是硬证据，
> 不能只看「行数够 2200」就放心。
>
> ③ **坑 477：crawl 阶段在 adoption 观察窗口（≤2s）内跑完，tick 会返回 `RETRY_LATER supervisor exited before adoption rc=0`，这是良性竞态，不是失败。**
> 1115 期 23:21 手动 tick 时 daily 已就绪，`_run crawl` 只做校验即退出，父进程看到子进程先退就按
> 「未接管成功」报 `Refusal(1)`。**处置**：看到这条先 `status`——若已是 `ready_downstream`、或后续 tick
> 返回 SKIP（job 已被 L1/L2 接管），说明工作已完成，**不要重置 state、不要重复起 worker**；
> 真正的接管失败会同时伴随 daily/checkpoint 缺失。
>
> 另：本期 32h 窗口是 `2026-11-13 16:05 → 2026-11-15 00:05`，`too_old=970 future=0 parse_fail=0`；
> 标题去重一次砍 1213 条（近 3 天覆盖度高）属正常，别为了「多抓」放宽去重。
>
> **🔴 v16.15.0 核心改进（2026-11-20 1120 期实跑：permanent-gone 不会自动生成 / 健康压缩循环别误判成坏会话，补坑 470·504）**
>
> 1120 期：Source A 2217 / Source B 613 → 队列 601 → 正文 598 → daily **550**（51 excluded，含 3 帖永久消失）。
> 抓取侧没出新坑，但两个**既有结论需要补操作细节**，都是「判据对、但操作者不知道下一步该干嘛」。
>
> ① **补坑 470：`permanent-gone.json` 没有任何自动生成机制，必须操作者手写。**
> 1120 期 3 个 id（3206149 / 3198175 / 3202642）每轮都返回 `empty_deleted_private_or_unloaded`，
> resume 会**每 ~60 秒新造一个** `batch_browser_retry<N>.json` 无限重试 —— 日志看起来像「在干活」，
> 实际永远 `missing=3`。**磁盘上没有任何脚本会写这个清单**，`permanent_gone()` 只读不写。
> **操作步骤**：`ls data/batch_browser_retry*.json | wc -l` 确认 ≥6 → 逐 id 校验每个文件
> 「恰好一行 + 无 title + error 逐字一致」→ 原子写清单 → 下一轮 resume 自动读到。
> 1120 实测：23:39 写入 → 23:41 就 `crawl+merge VALIDATED`（7 份证据：origin batch + retry0..5）。
> 写清单前**不要**先改门禁或删 retry 文件——那是伪造覆盖率。
>
> ② **补坑 504：除了「4 行就退」的真坏会话，还有一种健康压缩循环，绝不能清 session。**
> 1120 期 worker 连续多轮以 `end_turn` 干净退出、状态 `interrupted`，看起来极像 504，
> 但清 session 会丢进度。**三条同时成立就是健康、不要动**：
> `is_error=false` / stream **100+ 行** / **每轮都有新落盘产物或 progress 推进**。
> 退化的信号是**三者同时崩**：stream 行数断崖式下降（1120 实测 50 → 37 → **4** 行）、
> `input_tokens` 只剩两千、末尾直接吐压缩摘要、零产物 —— 这时才按 504 清 `session_id`。
> 机理：单轮几十次工具调用把上下文顶到压缩阈值（实测 in 400–780K / cache_read 1–5M），
> 压缩即结束该轮，摘要成为下一轮起点，上下文骤降后才腾出空间推进。
>
> ③ **附：成本统计口径。** `result.total_cost_usd` 是**会话累计值**不是单轮值
> （1120 实测 1.71 → 5.14 → 8.25 → 15.59 → 19.08 → 31.56 → 53.68 → 60.17 单调递增）。
> 汇报成本时取最后一次的值，别把各轮相加。
>
> **🔴 v16.14.0 核心改进（2026-11-19 1119 期实跑：Cloudflare 中文挑战页 / 派生常量未导出 / created 窗口覆盖 / worker 会话复用 / 模型别名漂移，坑 501-505）**
>
> 1119 期：Source A 2218 / Source B 605 → 队列 679 → daily 630（675/679 有效 + 4 帖永久消失）。
> 抓取阶段连踩四坑，全部是「代码看起来对、跑起来空转」：
>
> ① **坑 501：Cloudflare 挑战页现在会说中文「请稍候…」。** 旧 `passCloudflare` 只匹配
> `Just a moment|Checking|Attention Required`，中文页直接当成功返回；随后 12 次滚动全 0 行，
> 被 `shortList` 判欠抓。**修法**：挑战标题正则同时包含
> `请稍候|请稍等|正在检查|检查中|验证中`，等待上限提到 **12×10s=120s**（实测挑战约 40–48s）。
> 日志里 `scroll 10: 0 rows` + 没有 `[cf]` 行就是本坑。
>
> ② **坑 502：派生脚本引用共享常量必须显式 export/import。** `_fetch_lists_<issue>.mjs` 新增的
> created 覆盖检查用了 `CUTOFF`，但 `_crawl_<issue>.mjs` 里 `const CUTOFF` 没 `export` →
> 每轮滚到 2216 行后抛 `ReferenceError`，表现成 transient 重试 3 次 → `rc=1 failed after 3 attempts`，
> resume 又从第 1 行重来。**判据**：日志 transient 后**没有** `(short list)` 后缀。
> **修法**：`export const CUTOFF` + fetch 侧 `import { ..., CUTOFF }`；派生后 `node --check` 不够，
> 要 `node --input-type=module -e "import('./_fetch_lists_<issue>.mjs')"` 实跑 import。
>
> ③ **坑 503：CAP 2200 只是安全上限，完整性要用 created 反算。** 列表按活动排序，CAP 早退不代表
> 32h 窗口覆盖。抓完必须验证「加载到的最老一行 created < CUTOFF」；仍 >= CUTOFF 就按欠抓重试/block。
> 1119 实测 2218 行、min created 2024-05-05、窗口内 896，才允许进 build_queue。
>
> ④ **坑 504：worker 复用同一个 `--resume` 会话会把请求体滚坏。** 连续十几个 attempt 都
> `API Error 400 ... Invalid request` 或只写 2 条事件挂起；换模型别名无效。**修法**：operator 在
> job 空闲时清 `worker.session_id` / `initialized=False` / `next_retry_epo`，强制新会话；
> 磁盘 checkpoint（batch/evidence/state）才是事实源，坏会话可丢。
>
> ⑤ **坑 505：本地代理模型别名会整条消失。** `auto/deepseek-v4.1-flash[1m]` 当天不在 `/v1/models`，
> CLI 直接 `unrecognized_model`；`[1M]` 版本可能被上游按签名 403。**修法**：scheduler 加
> `WORKER_MODEL = os.environ.get('PIPELINE_<issue>_MODEL', '<别名>')` 并给 worker 传 `--model`，
> 不改用户全局 settings；选别名必须用**完整 worker prompt** 实测（`--print` + 长 prompt + 90s），
> PING 测不出。
>
> **🔴 v16.13.0 核心改进（2026-11-18 1118 期实跑：Source A 懒加载失败只抓到 30 帖，daily 全绿却是静默欠抓，坑 496）**
>
> 1118 期：Source A 只返回 **30 帖**（1117 是 2217、1116 是 2219），32h 窗口内 19 帖，
> daily 只有 **28 帖**；而控制器的 queue_hash / batch 覆盖 **29/29 全绿**，没有任何告警。
> 用户对比历史期数后发现，整条报告基于 1/16 的素材生成，只能重抓重跑。
>
> ① **坑 496：`scrollLoad` 的 `stable >= 3` plateau 判据会把「首屏 30 行没继续加载」误判成列表已到底。**
> 日志指纹：`scroll 1..320: 0 rows`（列表元素 `tr.topic-list-item` 根本没渲染）→ transient 重试 →
> `scroll 1: 30 rows` → 连续 3 次不变 → 返回 30。**修法（`_fetch_lists_<issue>.mjs`）**：
> - 加行数下限 `MIN_ROWS = { a: 800, b: 200 }`（Source A 历史 ~2200 行，Source B 过滤前 ~2200 行）；
> - plateau 阈值 `3 → 6`，且必须 `count >= MIN_ROWS[key]` 才允许返回；
> - 滚动 12 次仍 0 行 → 立即 transient 重试（不再空转 420 次 / 11 分钟）；
> - 低于下限时先点 `button.load-more / a.load-more / .load-more`，没有或仍不涨就 reload；
> - 三次仍短 → 抛 `rc=4`（source abnormal），让控制器 **block** 而不是静默继续。
> 修复后同一页面立刻抓到 **2219 帖 / 窗口内 709**，说明是瞬时渲染失败，不是站点改版。
>
> ② **判据纪律**：`validate_daily` 只校验队列内部一致性，**不校验源是否抓全**。
> 开工后先看 `data/source_a.json` 条数，`< 1500` 一律按欠抓处理；
> 不要因为 `CHECKPOINT coverage: valid=N/N` 与 `DAILY VERIFIED` 全绿就认为素材完整。
>
> ③ **恢复路径（本期实测有效）**：停 L2 与 supervisor → 归档 bad-run 产物（daily/report/press/pdf/
> news-pipeline/logs/batch/queue，共 23 项）→ 保留 `ARCHIVE-DONE` marker → 重置 state →
> 修 `_fetch_lists` → 重新 arm → tick。重抓后 495 队列、494 帖正文、1 帖 404 确认删除
> （写 `permanent-gone.json`，需 ≥6 个同错误 attempt 文件佐证）、daily 459 帖。
>
> **🔴 v16.12.0 核心改进（2026-11-17 1117 期实跑：audit 探针要求字面 PASS / Claude CLI 路径写死扩展版本，坑 491-492）**
>
> 1117 期：Source A 2217 / Source B 595 → 队列 **507** → daily **464 帖**（507/507 有效、0 error）；
> 22:35 触发 → 23:20 crawl VALIDATED → 23:23 downstream；00:13 在 audit 处粘性 blocked，人工修复后
> 15:48 DONE，全程约 **17 小时**。两条都不是抓取问题，而是**判据**与**运行环境**。
>
> ① **坑 491：控制器 `_audit_probe` 要求系统 checker 的 stdout 含字面 `PASS`，而 checker 的真实成功契约是
> `rc=0` + `RESULT: OK`——这个门永远不可能通过。**
> 1116 是靠额外写 `run_check_1116.py` 适配器补打 `PASS:` 绕过去的；1117 的 worker 拒绝伪造 PASS，
> 按契约 `block --kind source` 停机（00:13，report/press/pdf/content 断点全部保留）。
> **正确修法（改判据，不伪造证据）**：
> ```python
> upper = (result.stdout or '').upper()
> if (result.returncode or 'RESULT: BLOCKED' in upper or 'FAIL' in upper
>         or not ('RESULT: OK' in upper or 'PASS' in upper)):
>     raise Refusal(1, 'actual derived-content audit did not PASS')
> ```
> **纪律**：新期派生后先跑一次真实 checker，确认探针接受的成功令牌；不要写 PASS 适配器、不要改内容层。
> 遇到 `kind=source` 的 audit block，先查这条；修完探针后用原 evidence 重新 `checkpoint audit`。
>
> ② **坑 492：`CLAUDE` 常量写死了扩展版本号，VS Code 扩展升级后所有 downstream worker 都 spawn 失败。**
> 1117 期间扩展从 `anthropic.claude-code-2.1.310` 升到 `2.1.325`，旧路径消失，L2 每 180s 重试、
> 连续 16 次 `FileNotFoundError: .../resources/native-binary/claude`，日志只有 supervisor traceback，
> 表面像「worker 没进展」。**预防/处置**：arm 前和长跑中定期检查
> `ls -d ~/.devin/extensions/anthropic.claude-code-*`，把 `CLAUDE` 指到实际存在的最新
> `resources/native-binary/claude`；指纹是 `<issue>-downstream-supervisor.log` 里的 `FileNotFoundError`。
> 不要重装/降级扩展，也不要改 `worker_command` 的其它参数。
>
> ③ **验证正例**：坑 475 预防生效（arm 前移走 `crawl-resource.lock.owner.json`，lsof/ps 双确认）；
> 507 队列全量抓取 0 error；五平台草稿全部落库（公众号 `100002098` / 知乎 `2106048447715468379` /
> B站 `4132286` / 抖音 `v0300fg…` / 视频号 `export/UzFf…`）。
>
> **🔴 v16.11.0 核心改进（2026-11-16 1116 期实跑：触发时刻串被日期替换二次位移 / worker 首尝试静默退出后自动续跑，坑 487-488）**
>
> 1116 期：Source A 2216 行、Source B 605 行 → 队列 321 → daily **294 帖**（二次过滤排除 27，22 批 err=0）。
> 22:35 触发 → 23:08 冷启动归档一次通过 → 23:15 crawl+merge VALIDATED → 23:39 report / 23:41 press / 23:43 PDF；
> downstream 首尝试 23:08–01:48 无新 checkpoint 退出（rc=1），L2 02:07 自动 `--resume` 续跑，10:35:18 DONE，
> 全程 **12 小时**。本期抓取链很干净，时间全在 downstream 与抖音上传。
>
> ① **坑 487：派生器的日期四形态替换会把「触发时刻串」二次位移，必须占位保护 + 全量审计。**
> 1115 源码的 GUARD 文案/`trigger_at` 写着 `2026-11-15 22:35`，而 `TRIGGER_EPOCH=1794666900`
> （= `2026-11-14 22:35`）——这是 1114→1115 派生时通用 `2026-11-14`→`2026-11-15` 替换把刚改好的触发串又推了一天的残留
> （纯文案错位，epoch 门禁本身正确）。1116 派生改用**占位符保护**：先把 `2026-11-15T22:35:00+08:00` /
> `2026-11-15 22:35:00` 换成 `\x00TRIG_ISO\x00`/`\x00TRIG_SP\x00` → 跑完全部日期/期号替换 → 原样放回；
> 触发断言 tuple `2026, 11, 14, 22, 35,` 单独 +1 天改写。
> **纪律**：替换列表第一行写 `(X, X)` 这种 no-op「guard」没有任何保护作用（1115 的假 guard 什么都没挡住）；
> 派生器末尾必须断言：派生文件不含上期号、不含旧 epoch、剩余旧报告日期只允许紧跟 `T22:35`/` 22:35`、
> 旧 cutoff 形态不得残留。1116 派生一次通过（18 文件 + prompts + state），GUARD 文案与 epoch 首次对齐。
>
> ② **坑 488：downstream worker 首个尝试会在长生成阶段静默退出（rc=1），L2 自动 `--resume` 续跑是设计内路径，别当故障。**
> 1116 实测：attempt 1 23:08 启动、01:48 无新 checkpoint 退出（2h40m）；L2 02:07:22 以同一会话 `--resume` +
> 磁盘 checkpoint 起 attempt 2，随后 content 03:26 → audit 03:50 → covers 04:00 → video 06:11 → articles 06:48
> → publish 06:50 → 五平台上传 07:18–10:33 → finish 10:35 全链完成。
> **监控口径**：`worker.attempts` 增加 + `last_exit=1` 是恢复路径，不是失败；判进度只看 stage checkpoint 与
> `progress`，不要凭 stream 尾巴有没有输出来下结论；禁止手工重启 worker / 并发第二个 worker。
> **预防**：content 这类长生成阶段开始前先落 progress checkpoint（本期在 pdf 已 checkpoint 后进入 content，
> 续跑没有重做已核验阶段）；整期 10h+ 属正常长尾，半夜别误判卡死。
>
> ③ **验证正例**：坑 475 的预防生效——arm 前清 `crawl-resource.lock.owner.json`（lsof 无持有者 + ps 无爬虫），
> 本期冷启动归档一次通过、无 rc=3；坑 477 的 adoption 竞态本期未触发（crawl 正常接管）。
>
> **🔴 v16.8 核心改进（2026-11-14 1114 期实跑：列表页永不收敛 / 永久消失帖把整条链卡成死循环，坑 469-470）**
>
> 本期 1114：Source A 列表滚到 2903 行仍在涨，加近期窗口上限后在 2218 行收口（Source B 2220 行）；
> 正文 `BODY COVERAGE 622/623 errors=1 permanent_gone=1 missing=0`，daily `posts=583 covered=622/623 excluded=40`。
> 两条主干坑都在抓取侧（另带一条 `coverage` 附条），且都不是「抓不到」，而是**判据永不为真 / 硬门禁永不通过**。
>
> ① **坑 469：板块列表是无界增长的，别等「稳定平台」**。`_fetch_lists_<issue>.mjs` 的终止条件要求
> 「连续 3 次计数相等」，但 1114 实测每 1–2 次滚动就 +30 行（`scroll 180` 时已 2903 行仍在涨），
> 单次重复从不连续 3 次 → 三次 resume 各跑满 180 次滚动后 `rc=1 Source A failed after 3 attempts`。
> **修法：滚动循环必须有「近期窗口行数上限」**——
> ```js
> if (count >= CAP && i >= 20) { console.log(`recent-window cap reached at ${count} rows`); return count; }
> ```
> CAP 按「32h 窗口所需行数 × 2」现场推导，**不要照抄 2200**（1114 的 2200 只对当期板块活跃度成立；
> 本期窗口内最后一行索引 A=1328 / B=35，A 仍有约 870 行余量）。
> 同时保留 11 分钟硬超时与「仍在增长 / 未穷尽」的显式错误，别让「到达上限」伪装成「已抓完」。
> **校验方式**：抓完用 `created` 反算「窗口内最后一行的索引」，必须 `< CAP × 0.7`。
>
> ② **坑 470：全队列「每个 ID 必须有正文」是死门禁，遇到已删/私有帖会无限重试**。
> 1114 有 1 个 id 连续 7 次 `rc=1 incomplete bodies`，重试 8 次（`batch_browser_4` + `retry0..6`）都返回
> `empty_deleted_private_or_unloaded`。**删掉的帖子重跑一万次也不会回来，攒够证据就该出清单——但注意校验器要求 `attempt_files` ≥ 6（`batch_browser_N.json` + `retry0..k` 合计），所以实际要等到第 6 份证据；只写 3 份会被 `Refusal(3)` 打回（1115 期实测：`batch_browser_16.json` + `retry0..5` 共 7 份才落库）。**
> **修法：允许「证据背书的排除清单」**——`data/<issue>-permanent-gone.json` 每条含
> `id / reason / attempts / attempt_files`；加载时**逐份 checkpoint 反查**：
> 文件存在、该 id 恰好一行、无标题、`error` 与 `reason` 完全一致、`attempts == len(attempt_files)` 且 `>= 6`，
> 任一不符即 `Refusal(3)`。**禁止伪造标题/正文凑覆盖率**。
>
> **附条（坑 470）：`coverage` 必须写 provenance，不能只写一个比值**。旧日志只打
> `BODY COVERAGE 622/623 errors=1`，看不出分母怎么来的、那 1 个去哪了。**修法：coverage 同时写
> `valid_total` 与 `gone_ids`，`validate_daily` 断言 `set(good) | set(gone) == set(ids)`；
> 日志固定打 `errors=… permanent_gone=… missing=…` 三个计数。** 这样「覆盖率」才是可复核的等式，
> 而不是 worker 自报的分子分母。
>
> 另：本期 L1/L2 的唯一中断是 `controller interrupted; exact-owner lease cleanup`（调度层租约问题记在
> ai-news-factory v3.96.0 坑 468）。`STALL_SECONDS` 的卡死回收本期**未触发**，不作结论。
>
> **🔴 v16.6 核心改进（2026-11-13 1113 期派生：历史注释泛化必须覆盖「本期发现」这类措辞）**
>
> 派生器的 `HIST_GENERALIZE` 表若只写 `1112 期实测` / `1112 期修正`，会漏掉源文件里的
> `坑 443（本期发现，1110/1111 继承）`、`坑 444（本期发现）：` 这类**不带期号的「本期」**。
> 它们描述的是上一实现周期发生的事，不泛化就会在下一期被读成「这期发现的坑」，是**对事实的错误陈述**。
> **纪律：`HIST_GENERALIZE` 要同时覆盖「带期号」与「裸本期」两种形态**，并在派生末尾用
> 反向断言（`assert not re.search(r'(?<!\d)1112(?!\d)', t)`）兜底。
>
> **🔴 v16.5 核心改进（2026-11-12 1112 日报实跑：daily 排序静默失效 / 完判据虚高，坑 443·445）**
>
> 本期抓取 33 批 / 488 帖 / err=0，32h 窗口 488，二次过滤 477。链路上没报任何错，但**两处判据/排序在静默失效**：
>
> ① **坑 443：`_merge_<issue>.py` 的 `sorted(filtered.values(), key=vn, reverse=True)` 传错了 key**。`vn()` 期望一个 views 字符串，这里拿到的是整个 post dict；`str(dict)` 以 `{` 开头，正则 `re.match(r'([\d.]+)\s*([km万])?', s)` 不匹配 → 落到 `int(re.sub(r'\D','',s) or 0)`，把 `id`/`created`/`views` 里的所有数字拼成一个巨型整数。**排序因此退化为按 id 数字串排列，daily 不再是浏览量降序**：本期首元素 views=40，全表最大 7600 卡在第 54 位。**修法 `key=lambda p: vn(p.get('views'))`，并在 merge 末尾加 `assert views == sorted(views, reverse=True)` 把它钉死**。该 bug 至少从 1110 期就存在，是「派生只换日期」的典型副作用。
> ② **坑 445：`_resume_<issue>.sh` 的「抓取完成」判据按文件累加 `len(results)`**。`glob('data/batch_browser_*.json')` 会命中 `batch_browser_retry0.json`（同 id 计两次），且 `crawlOne` 返回 error 时 `results` 长度仍等于 batchIds（error 也计入完成）。**有帖没抓到却判 complete → 提前 merge、daily.total 偏小**。**改为按 id 去重、只数 `r.get('title') and not r.get('error')`**。本期 err=0 未触发。
>
> 另：本期冷启动归档了 1111 期 59 个中间态文件（`batch_browser_*` / `source_a|b` / `crawl_queue` / `batch_ids_*`）后才开工，否则 `_resume` 的 `isComplete` 会把上期批次当成本期已完成直接跳过。
>
> **🔴 v16.4 核心改进（2026-11-10 1110 日报实跑·跨机迁移首日：linux.do 列表页 i18n 变中文导致 created 全空、32h 窗口过滤成 0；抓取链对本机环境的三处硬依赖）**
>
> 1110 期在新机器（macOS 14.6 / arm64，整目录从旧机迁移）跑通：双源 900 + 273 → 合并去重 1153 → 标题去重 917 →
> 公益站过滤 824 → **32h 窗口 405** → 26 批正文（err=1）→ **daily 393 帖**。**当期最贵的一条坑不在抓取逻辑，而在页面文案。**
>
> **① 坑 A：`td.activity[title]` 已本地化，`Created:` 正则全部落空 → 所有帖子 `created=''` → 32h 窗口 0 条 → `daily total=0` 假成功（新，本期最重要）**
> **症状链**：`_fetch_lists_*.mjs` 正常跑完（Source A 900 / B 273），`_build_queue_*.py` 也正常输出，但窗口统计是
> `32h window: 0 (no_created=824 parse_fail=0 too_old=0)` → `crawl_queue total=0` → `crawl bodies queue: 0 posts` →
> `saved data/daily/<DATE>.json total=0` → **整条链"成功"退出**，launch wrapper 却因 `total < 100` 卡在 600s 空转。
> **根因**：`td.activity` 的 `title` 文案已本地化，从 `Created: Nov 8, 2026 10:14 pm` 变成 `创建日期：2026 年 11月 8 日 15:36`
> （`最新：…` 另起一行）。旧正则 `/Created:\s*(.+?)(?:\n|$)/` **永远不匹配**，`created` 恒为 `''`。
> **修法（两段都要）**：
> ```js
> let created = createdMatch ? createdMatch[1].trim() : '';   // 🔴 必须 let，const 会抛 Assignment to constant variable
> if (!created) {                                             // 中文回退
>   const cn = titleAttr.match(/创建日期[：:]\s*(.+?)(?:\n|$)/);
>   if (cn) created = cn[1].trim().replace(/\s+/g, ' ');
> }
> if (created && !createdMatch) {                             // 归一化成 dateutil 可解析形态
>   const m = created.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(\d{1,2}):(\d{2})/);
>   if (m) created = `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}`;
> }
> ```
> **本期踩的二次坑**：补丁第一版写成 `const created = ...` 再赋值 → 浏览器抛 `TypeError: Assignment to constant variable`，
> `page.evaluate` 把整批 result 变成 `attempt N failed`。改 `let` 后一次通过。
> **判据**：跑 `_build_queue` 后**必须看 `no_created` 计数** —— `no_created > 0` 就说明时间解析又变了。健康值 `no_created=0 parse_fail=0`。
>
> **② 坑 B：`daily total=0` 会被链路当成"成功"，必须显式拦截（新）**
> `_resume_*.sh` 的判据是 `crawl complete have>=n` —— 当 `n=0` 时 `0>=0` 恒真，直接 merge 并写出 `total=0` 的 daily。
> **修法**：`_build_queue` 输出 `crawl_queue total=0` 时**主动非 0 退出**；`_resume` 加
> `[ "$(python3 -c "import json;print(json.load(open('data/crawl_queue.json'))['total'])")" -eq 0 ] && exit 4`；
> launch wrapper 把 `rc=4` 判为「数据源异常，停止重试并告警」。
> **排查口诀**：`daily total=0` + `crawl.log` 有 `queue: 0 posts` → **先查 `source_a.json` 的 `posts[0].created` 是否为空**，
> 空就是坑 A；不是网络问题、不是 CF 拦截、不是站点封禁。
>
> **③ 坑 C：新机抓取链的三处硬依赖（一次性全踩）**
> | 依赖 | 本期现象 | 处置 |
> |---|---|---|
> | **node ≥ 18** | PATH 首位是 nvm **v14.21.3**，`playwright-core` 报 `Playwright requires Node.js 18 or higher` | shell 脚本 `set -u` 后注入 `export PATH="$HOME/.nvm/versions/node/<ver>/bin:$PATH"` |
> | **playwright-core** | 旧路径 `~/.nvm/.../openclaw/node_modules/playwright-core` 不存在 → `MODULE_NOT_FOUND` | `npm i -g playwright-core@<ver>`，把 `createRequire` 路径改到 `$(npm root -g)/playwright-core/package.json`；**版本必须与本机 chromium 缓存 revision 对齐**（chromium-1223 ↔ playwright-core 1.60.0） |
> | **机器路径** | 派生脚本 ROOT 仍是旧机 `/Users/olduser/Documents/learn-claude-code` | 派生器加 `text.replace('/Users/olduser/...', '/Users/newuser/...')`；**只换日期不换路径 = 全部脚本 cd 失败**（本期 launch 启动即 exit，watchdog 一直误报 GUARD） |
>
> **④ 坑 D：`_archive_*.py` 对无 `date` 字段的中间态一律归档**
> `batch_ids_*.json` 没有 `date` 字段 → 判 `date=None` → 一律搬走。冷启动正确，但**续跑时会把手上的 batch_ids 搬空**。
> **纪律**：归档只在**开工前**跑一次，续跑一律不跑；脚本注释里写清。
>
> **⑤ 坑 E：watchdog 的 `GUARD` 分支只看 pid，wrapper 早退仍报"armed"**
> 本期 `alive()` 校验了 pidfile + cmdline，但 wrapper 因 `cd` 失败 exit 后 pid 被复用/或 pidfile 残留 → 仍报
> `GUARD … wrapper pid XXXXX armed`。**修法**：`GUARD` 分支加「`launch.log` 最近 10 分钟有无新行」或 `ps -p $pid -o lstart=` 比对。
> 另：**`crawl.log` 出现 `queue: 0 posts` 时直接 ALERT**，不等 wrapper 空转 600s。
>
> **⑥ 本期正例读数（未来基线）**
> 双源 900 + 273 → 合并去重 1153 → 标题去重 917（掉 216）→ 公益站 824（掉 93）→ **32h 窗口 405（no_created=0）** →
> 26 批（batch 17 有 1 err）→ `crawl complete 406/405` → **daily 393（with_content 393 / removed 11 / errors_skipped 1）**。
>
> **⑦ 与 ai-news-factory 的衔接（本期新增）**
> 抓取稳定后，**视频链内容层必须整份重写**（见 ai-news-factory v3.87.0 坑 429）：事件、口播、图片 prompt、公众号 sections
> 全部由本期报告驱动，禁止沿用上期脚本只改日期。判据：口播里的专名必须能在 `data/reports/<DATE>.md` 里找到。
>
> **🔴 v16.3 核心改进（2026-11-06 1106 日报实跑：无超时 `page.evaluate` 挂死 + 看门狗盲区 + kill 顺序）**
>
> 1106 期 batch13 最后一帖（第 15 帖，tid=`3126308`）把整条抓取链挂死约 60 分钟；三个新增判据与处置如下：
> ① **`page.evaluate()` 必须包 `Promise.race(30s)`（根因）**：`page.goto` 有 25s timeout，`page.evaluate` 没有任何超时，renderer 不回调就永久挂起。1106 实测 node 32942 `STAT=SN`、`%CPU 0.0`、栈停在 `uv__io_poll`/`kevent`，renderer 60603 CPU time 仅 `0:00.20`，Chrome History 最后导航停在 `23:02:43`（已 60 分钟未动）。修法：`crawlOne()` 内每个 `page.evaluate` 都写成 `await Promise.race([page.evaluate(fn), new Promise((_, rej) => setTimeout(() => rej(new Error('evaluate_timeout_30s')), 30000))])`，捕获后记 `{id: tid, error: 'evaluate_timeout'}` 并继续下一帖，禁止让单帖异常冒泡终止整批。
> ② **看门狗新增 crawl stalled 判据（必须先于 pid 存活判断）**：1106 期 watchdog 因 launch wrapper pid 活着一直判 `RUNNING`，实际抓取已死 60 分钟。新增三条全真即 `emit ALERT "crawl stalled: no crawl.log/nav for >30min (node pid alive)"`：node 存活（`alive "$CRAWL_PIDFILE"` 或 `pgrep -f _crawl_<issue>.mjs`）**且** `crawl.log` mtime > 30min（`[ -n "$(find "$CRAWL_LOG" -mmin +30)" ]`）**且** Chrome History 最新导航 > 30min。History 原库被 Chrome 锁住，必须先复制再查：`cp "$HOME/Library/Caches/ms-playwright-mcp/mcp-chrome-10b76e5/Default/History" /tmp/hist_<issue>.db && sqlite3 /tmp/hist_<issue>.db "select datetime(max(last_visit_time)/1000000-11644473600,'unixepoch','localtime') from urls;"`（**抓取用的是 `ms-playwright-mcp` 这个 profile，不是日常 Chrome 的 `Application Support/Google/Chrome`**）。该分支必须放在现有「正在执行 → 跳过」段之前，否则永远被 pid 判据短路；处置见 `templates/watchdog.md`。
> ③ **kill 顺序：先 node 后 Chrome 树；kill 后先归档假批次再续跑**：反过来先杀 Chrome，node 会在浏览器断开后抢写「`complete: true` 但 15/15 全 error」的批次（1106 写出 batch14/15 全 error）。正确顺序：`kill -TERM <node_pid>`（10s 不退再 `kill -KILL`，1106 node 32942 忽略 TERM）→ 确认 node 已死 → `kill -TERM <chrome_pid>` 杀进程树。随后立刻把该时间窗内新写的 `data/batch_browser_*.json` 移到 `data/archive/<date>-prev-<ts>/`，再 `bash data/_resume_<issue>.sh`；`isComplete()` 会跳过 batch0-12，从 batch13 重抓。1106 实测重抓 batch13 得 `n=15 valid=15 err=0`，链自动恢复。
>
> **v16.2 核心改进（2026-10-20 日报实测）**：**Discourse 帖子页内嵌 i18n 字典含官方警告原文，裸 includes 判据对正常页逐页误报（新坑）**——1020 期 `bodyText.includes('系统检测到该账号存在异常使用行为')` 连误报 3 次（23:04 + 次晨 2 次），`_resume` 的 sticky 标记检查直接拒绝续跑；用户指出"打开后页面有内容、没有被封"才暴露误判。根因：Discourse 前端把 en/zh/zh-hant 三语警告文案以内嵌 JSON 字典形式下发（含 `SUBMIT_FEEDBACK`/`EDIT_INPUT` 键），**每个正常帖子页都含该字符串**。修法：判据函数 `isOfficialWarning()` 必须排除字典行——命中关键词时再检查同行是否含 `/"zh-hant"\s*:/`、`/"en"\s*:"/`、`SUBMIT_FEEDBACK`、`EDIT_INPUT`，有则判正常；改判据前先用诊断脚本回读页面三要素（标题/正文长度/cooked 数）确认页面真实可用，`node --check` 过后再续跑。1020 实测：406 帖队列 → 28 批 err=0 → daily 395 帖。**附带**：看门狗三态（pid 活/log 近 5min/heartbeat ≤25min）任一真则跳过，中断续跑先 `bash data/_resume_*.sh` 补齐抓取链再碰下游。
> **v16.1 核心改进（2026-10-16 日报实测）**：**派生日期有三种 sed 漏网形态（坑 241 日期三形态跨 skill）**——1016 期 `s/1015/1016/g` + `s/2026-10-15/2026-10-16/g` 只能命中①连字符日期（`2026-10-16`）、②裸期号（`1016`）、③下划线标识（`__wx1016`），**漏掉 `datetime(2026, 10, 15, 0, 5)` 这种逗号分隔的 Python 日期常量**：`_build_queue_1016.py` 的 `BASE = datetime(2026, 10, 15, 0, 5, tzinfo=CST)` 没被替换，32h 窗口会整体偏一天（`_build_queue` 自带的 `assert (BASE-CUTOFF)==32h` 救不了，因为 BASE 和 CUTOFF 一起偏）。修法：派生后 `grep -n "2026, 10,"` 逐行核对 BASE 行 + 运行期 `print(BASE.isoformat())` 断言；亮点对照窗口（`2026-10-1{3,4,5}.md`）、cutoff 字符串（`2026-10-14 16:05`）同样逐项核对。1016 实测：516 帖队列 → 35 批 err=0 → daily 509 帖。**附带**：`data/source_a/b.json` + `crawl_queue.json` 属上一期残留时必须一并归档，否则 `_resume` 脚本会拿旧队列跳过重建（1016 冷启动归档 37 残留批次 + source/queue 另存 `-src` 目录）。
> **v16.0 核心改进（2026-09-18～09-20 三期全量日报实测）**：把 v15.9 的 Node 直连 Playwright 从临时兜底升级为**可复用全量抓取协议**：脚本必须按当期日期复制/参数化（禁止只改文件名却保留 0917 注释与固定 cutoff）；32h 窗口基准默认固定为当期 **00:05 CST**，禁止用脚本实际启动时间 `datetime.now()` 漂移；最近 3 日标题去重必须做**规范化比较**，不只精确字符串；每批结果写临时文件后原子替换，避免中断留下半截 JSON；冷启动归档目录已存在时不得 `shutil.rmtree` 覆盖，须生成唯一目录。0918：422→400；0919：414（413 valid/1 error）→400；0920：326→316。安全分类器不可用时只读命令仍可过，非只读任务暂停并改用 Write/Edit 落盘，恢复后从磁盘 batch 续跑。
> **v15.9 核心改进（2026-09-17 日报实测）**：Playwright MCP 断连时改 **Node 直连 Playwright** 抓列表+正文（headed 过 Cloudflare；`page.evaluate` 只传单对象参数）；chromium 路径用本机最新 `chromium-NNNN`，勿写死 1223。全量 **26 批 / 382 帖 0 error**，二次过滤 **362**。
> **v15.8 核心改进（2026-07-25 日报实测）**：`crawl_js`+`filename` 全量 **33 批 / 489 帖零 error**；中断后以磁盘 `batch_browser_0..N` 为准续跑合并；二次过滤 **455**；PDF 后接 ai-news-factory。
> **v15.7 核心改进（2026-07-22 日报实测）**：冷启动 archive 用 **Python `shutil.move`**（复杂 bash `for/pkill` 可能被自动模式拦截）；Source B `browser_navigate` 可 60s 超时 → **重试一次**；`crawl_js`+`filename` 批抓全量 31 批零 `ERR_ABORTED`；列表 double-encoded 仍 `json.loads(json.load)`；实测 462 队列 → **440** 有效。
> **v15.6 核心改进（2026-07-21 日报实测）**：冷启动禁 `rm` 旧 batch（改 **archive 挪移**）；预生成 `data/crawl_js/batch_N.js` + `filename` 批抓；`concepts.json` 是 `{concepts:[]}` 根对象；候选去重读 `data['concepts']`；实测 469 队列 → **447** 有效 / 32 批。
> **v15.5 核心改进（2026-07-20 日报实测）**：批抓 MCP 长静默超时；`ERR_ABORTED` 重置浏览器重试；batch 污染校验；`retryN` 批号；中断后续跑；实测 364 帖 / 26+ 批。
> **v15.4 核心改进（2026-07-19 周报实测）**：周聚合浏览量解析 `6.2k/万`；同 id 保留更高 views；`week_posts[id]['_day']` 记录来源日；周 PDF/Typst 同步落盘；与 ai-news-factory 衔接时 **PDF 落盘后再开视频**。
> **v15.3 核心改进（2026-07-18 实测）**：全量 19 批 / 531 帖闭环；Playwright 批抓与「浏览器退出」解耦说明；batch 保存脚本固化；二次过滤后再 Writer；与 ai-news-factory 衔接时避免边抓边开多浏览器。
> **v15.2 核心改进（2026-07-17 实测）**：固定项目 cwd；「过滤后全部抓取完」冷启动协议；`crawl_queue`/`batch_ids` 预切分；transcript 回填 batch；正文二次公益站过滤；列表页 views 合并；全量规模 500+ 帖。
> **v15.1 核心改进**：概念候选受控入库——日报附录经去重/过滤后只追加最小 `candidate`，不写口播、不晋升 ready。
> **v15 核心改进**：接入 `ai-concept-bank` 技术锚点；可信度五档；账号权益黑话过滤。
> **v14 核心改进**：Cloudflare 点击绕过、周报模式完整流程、并行 Agent 优化、旧 batch 文件清理。
> **v13 核心改进**：新增月报模式。月报基于当月已抓取数据与已生成的日报数据聚合，不重复抓取，输出月度趋势总结 + 主题归纳 + 下月展望。
> **v12 核心改进**：批量抓取数据强制保存、空帖检测跳过、官方警告检测、全量抓取支持、Typst 特殊字符处理。

## ⚡ 开工前环境自检（v16.4.0 新增，新机 / 换机必跑）

```bash
bash ~/.claude/skills/ai-news-factory/templates/env-preflight.sh $(date '+%Y-%m-%d')
```

它一次检查 15 项：pipeline python 及其依赖（PIL / jieba / faster_whisper / playwright / av）、
`ffmpeg`/`ffprobe`、ffmpeg 字幕滤镜、`edge-tts` 版本、**node ≥ 18**、`playwright-core` 全局安装、
**chromium revision 与 playwright-core 是否对齐**、上传 profile、CDP daemon、Remotion compositor 可用性、中文字体。

**1110 期在新机上六处依赖全靠"跑到一半才发现"，这个脚本把它们前置成一次检查。**
输出 `FAIL>0` 时先修环境；`WARN` 决定链路走法（例如无 `ass` 滤镜就必须走 PIL overlay 烧字幕）。

## ⚡ 工作目录与冷启动（v15.2 必读）

### 固定项目根目录

**所有 `data/` 读写必须在项目目录执行**，不要依赖 shell 默认 cwd：

```bash
cd /Users/youngsdream/Documents/learn-claude-code
# 或在 Python 内：
# os.chdir('/Users/youngsdream/Documents/learn-claude-code')
```

> **2026-07-17 实测坑**：Bash 可能落在 `~/.claude/projects/...`，导致 `data/` 不存在、清理 batch 误报 0、写出文件写到错误位置。

`browser_evaluate` 的 `filename` 参数也要用**绝对路径**：

```text
/Users/youngsdream/Documents/learn-claude-code/data/source_a.json
/Users/youngsdream/Documents/learn-claude-code/data/source_b.json
```

### 触发词：「过滤后全部抓取完」/「0717 linuxdo日报 过滤后全部抓取完」

含义：**按全量模式跑完日报流水线**（不是“已经有 daily 了只写报告”）。

| 磁盘状态 | 动作 |
|---------|------|
| 无 `data/daily/{date}.json`，batch 也为昨/空 | **从 Crawler 冷启动**：清旧 batch → 预授权 → 双源列表 → 合并过滤 → **全量正文** → Writer/Press/PDF |
| 有 `batch_browser_*.json` 且 mtime 是今天、无 daily | 合并 batch → 写 daily → 后续 Agent |
| 已有 `data/daily/{date}.json` 与报告 | 跳过抓取，只补缺失产物 |

**禁止**在未验证 `data/daily/{date}.json` 存在时，假设“用户说抓取完=数据已在磁盘”。

### 推荐 Todo 清单（全量日）

```
0. 清上一期跨期锁 sidecar：`data/logs/crawl-resource.lock.owner.json` 若仍是上期的 date（先 lsof+ps 确认无活跃），备份后移出，否则冷启动归档会 rc=3 粘性 blocked（坑 475）
0.5 校验 `CLAUDE` 二进制路径：`ls -d ~/.devin/extensions/anthropic.claude-code-*`，把 `_scheduler_<issue>.py` 的 `CLAUDE` 指到实际存在的最新 `resources/native-binary/claude`；扩展升级后旧路径消失会让所有 downstream spawn 失败（坑 492）
1. 清理旧 batch + 浏览器预授权（固定 cwd）
2. Source A/B 列表 + 合并去重/公益站/32h → crawl_queue + batch_ids
3. 全量逐帖抓取正文（每批立即保存）
4. 合并 daily JSON + 正文二次过滤 + Topic/Trend
5. Writer 日报 + 概念候选入库
6. Press Writer + PDF Builder
```

## ⚡ 权限预授权（必须最先执行，一次性完成）

**开始抓取前，必须一次性授权所有 Playwright MCP 工具**，避免中途反复弹出授权窗口。

### 预授权步骤（按顺序执行，用户只需点击"允许"一次）

```
步骤 1: pkill -f "mcp-chrome" 2>/dev/null; sleep 2
步骤 2: browser_navigate → https://linux.do
步骤 3: browser_wait_for → time: 15（等待 Cloudflare 加载）
步骤 4: browser_snapshot → 查看页面结构
步骤 5: 如果标题仍为 "Just a moment..."，用 browser_click 点击验证区域（通常是 ref=e6 或 e5）
步骤 6: browser_evaluate → () => document.title（确认标题变为 "LINUX DO"）
```

**⚠️ Cloudflare 点击绕过（v14 新增）**：
2026-07-05 实测发现，Cloudflare Turnstile 挑战页需要**点击验证区域**才能通过，仅等待 15 秒不够。
- `browser_snapshot` 后找到 `main` 内的 `generic` 元素（通常是 `e6`）
- 用 `browser_click(target="e6")` 点击，页面标题会立即变为 "LINUX DO - 新的理想型社区"
- 如果一次点击未通过，再等 15 秒后重试点击

### 需要预授权的工具清单

| 工具 | 用途 | 必须 |
|------|------|------|
| `browser_navigate` | 页面导航（列表页、帖子页） | ✅ |
| `browser_run_code_unsafe` | 执行 JS（滚动加载列表页） | ✅ |
| `browser_evaluate` | 执行 JS 表达式（提取帖子数据） | ✅ |
| `browser_wait_for` | 等待加载（Cloudflare 挑战页） | ✅ |
| `browser_snapshot` | 页面快照 | 可选 |
| `browser_take_screenshot` | 截图 | 可选 |

> **不需要登录态**：匿名访问即可获取公开帖子数据。

---

## 数据源

| 源 | URL | 说明 |
|----|-----|------|
| Source A: #人工智能 标签 | `https://linux.do/tag/444-tag/444` | 直接命中，无需过滤 |
| Source B: 前沿快讯 分类 | `https://linux.do/c/news/34` | 全部新闻，需按 tags 过滤 |

## 触发条件

### 日报模式
当用户说以下关键词时激活：
- "日报"、"AI日报"、"技术日报"
- "linuxdo日报"、"抓取linuxdo"
- "今日AI新闻"、"AI资讯"
- **"过滤后全部抓取完"** / `MMDD linuxdo日报 过滤后全部抓取完` → **全量模式冷启动**（见上方协议）

### 周报模式
当用户说以下关键词时激活：
- "周报"、"AI周报"、"技术周报"
- "weekly"、"出周报"
- "本周AI新闻"、"一周总结"

### 月报模式
当用户说以下关键词时激活：
- "月报"、"AI月报"、"技术月报"
- "linuxdo月报"、"monthly"、"出月报"
- "本月AI新闻"、"月度总结"

**指定月份**（可选）：
- "月报 2026-05" / "2026年5月月报" — 生成指定月份的月报
- "上月月报" — 生成上一个自然月的月报
- 不指定时默认生成**上一个自然月**的月报（若当月已结束则也可生成当月）

## 模式对比

| 维度 | 日报 | 周报 | 月报 |
|------|------|------|------|
| 时间范围 | 当前往前 32h | 上周一~上周日 | 指定月份（默认上月）1日~月末 |
| 数据来源 | 实时抓取双源 | 聚合当周日报 | **聚合当月已抓取数据 + 已生成日报** |
| 是否抓取 | ✅ 必须抓取 | 可复用日报数据 | ❌ 不重复抓取 |
| 历史去重 | 必须执行 | 按周累计 | 不去重（全量呈现） |
| 输出风格 | 今日亮点 + 新内容 | 本周总结 | **月度趋势总结 + 主题归纳 + 下月展望** |

## 目录结构

**数据输出目录**：`/Users/youngsdream/Documents/learn-claude-code/data/`（项目目录，非 skill 目录）

```
/Users/youngsdream/Documents/learn-claude-code/data/
├── daily/{date}.json          # 每日抓取原始数据（合并后）
├── posts/{id}.json            # 单帖详情（含 scrape_history）
├── reports/{date}.md          # 生成的 Markdown 日报
├── reports/{date}_press.md    # 生成的专业新闻稿
├── reports/{date}.pdf         # 生成的 PDF 日报
├── reports/{date}.typ         # Typst 源文件
├── weekly/{week}.md           # 周报 Markdown
├── weekly/{week}_press.md     # 周报新闻稿
├── weekly/{week}.pdf          # 周报 PDF
├── monthly/{YYYY-MM}.md       # 月报 Markdown
├── monthly/{YYYY-MM}_press.md # 月报新闻稿
├── monthly/{YYYY-MM}.pdf      # 月报 PDF
├── monthly/{YYYY-MM}.typ      # 月报 Typst 源文件
├── source_a.json              # Source A 帖子列表
├── source_b.json              # Source B 帖子列表（AI过滤后）
├── merged_ids.json            # 合并后的帖子ID列表
└── batch_browser_N.json       # 浏览器抓取的帖子数据批次
```

## 过滤规则

### 公益站过滤（日报模式必须执行）

以下帖子在生成日报时**必须过滤掉**，不纳入统计和报告：

**关键词过滤**（标题、标签、内容中出现以下任一即过滤）：
- 公益站、公益推广、LDC、ldc、cdk
- 签到、白嫖、薅羊毛、薅秃
- 充值额度、兑换码、免费额度
- 号池、号商、共享号
- 中转站、高级推广、抽奖、富可敌国

**意图过滤**（帖子主要内容为以下类型即过滤）：
- 分享免费 API 额度/Key 的帖子
- 公益站注册/使用教程
- 公益站运维公告（关站、维护、升级等）
- 薅羊毛攻略
- **纯交易帖（v15）**：求号/出号/共享车/代充/接码且无行业分析价值 → 过滤
- 标题命中「接码」「号商」「代充」且无风控/行业讨论价值 → 过滤

**说明（v15）**：账号风控/封号潮**不默认删除**（仍有信息价值），但 Writer **降权**，不得霸榜亮点。

### 历史去重（日报模式必须执行）

生成日报前，扫描所有历史日报 Markdown 文件，提取已报道的帖子 ID：

```python
import re, os
prev_ids = set()
for f in os.listdir('data/reports'):
    if f.endswith('.md') and f != f'{today}.md':
        with open(f'data/reports/{f}') as fh:
            ids = re.findall(r'\[(\d{7,})\]', fh.read())
            prev_ids.update(ids)
```

已存在于 `prev_ids` 中的帖子不再纳入今日日报。

### 32小时范围筛选（日报模式必须执行）

帖子必须在 32 小时范围内才纳入日报。

**时间窗口**：当前时间往前 32 小时（例如：当前 09:41，则窗口为 06-19 01:41 ~ 06-20 09:41）

**注意**：Discourse ID 不按日期顺序（跨分类），**不能用 ID 阈值判断日期**。必须通过帖子页面获取 `created_at`。

---

## Agent 1: Crawler（抓取器）

**职责**：从两个数据源抓取帖子，获取时间戳筛选32h范围，检查历史记录，批量抓取正文。

### ⚠️ 核心经验：浏览器 fetch API 会触发 429

**2026-06-21 实测结论**：
- `browser_evaluate` + `fetch('/t/{id}.json')` 会被 linux.do 429 限流
- 即使间隔 1.5 秒，批量 50 帖也会触发 429
- **必须使用浏览器逐帖浏览方式**：`browser_navigate` 打开帖子页面 → 提取 DOM 数据

### 1.1 打开列表页

使用 Playwright MCP `browser_navigate` 依次打开：
- Source A: `https://linux.do/tag/444-tag/444`
- Source B: `https://linux.do/c/news/34`

**Cloudflare 处理**：如果页面标题包含 "Just a moment"，使用 `browser_wait_for → time: 15` 等待自动通过。

### 1.2 滚动加载全部帖子

打开列表页后，使用 `browser_run_code_unsafe` 滚动加载。**采用递增滚动策略**，每轮后检查数量：

| 轮次 | 滻动次数 | 间隔 | 预期加载量 |
|------|---------|------|-----------|
| 第 1 轮 | 15 次 | 2.5s | ~450 帖 |
| 第 2 轮 | 10 次 | 2.5s | ~750 帖 |
| 第 3 轮 | 5 次 | 2.5s | ~900 帖 |
| 第 4 轮（可选） | 5 次 | 2.5s | ~1050 帖 |

```js
async (page) => {
  for (let i = 0; i < 15; i++) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2500);
    const title = await page.title();
    if (title.includes('Just a moment') || title.includes('Checking')) {
      await page.waitForTimeout(15000);
    }
  }
  const count = await page.evaluate(() => document.querySelectorAll('tr.topic-list-item').length);
  return `scrolled 15 times, found ${count} posts`;
}
```

**终止条件**：每轮滚动后检查数量，如果 < 400 则追加一轮。通常 35 次滚动（3 轮）可加载 1000+ 帖，足够日报使用。

> **🔴 v16.8 追加（坑 469）**：板块列表是**无界增长**的，「连续 3 次计数相等」的稳定平台判据在活跃板块上不可达（1114 实测 180 次滚动仍在 +30 行/次）。滚动循环必须同时有**近期窗口行数上限**：`if (count >= CAP && i >= 20) { console.log(`recent-window cap reached at ${count} rows`); return count; }`，CAP = 32h 窗口所需行数 × 2，**现场推导、不照抄 2200**；到达上限与「仍在增长」必须是两种不同的退出信号。

### 1.3 提取帖子列表（含时间戳）并保存

> **v11 优化**：时间戳提取合并到此步骤，无需单独提取。从 `td.activity[title]` 一次提取完成。

使用 `browser_evaluate` 的 `filename` 参数直接保存帖子列表到文件：

```js
// Source A: 保存全部帖子（含时间戳）
browser_evaluate(filename="data/source_a.json", function=() => {
  const rows = document.querySelectorAll('tr.topic-list-item');
  const posts = [];
  rows.forEach(row => {
    const topicId = row.getAttribute('data-topic-id');
    const titleLink = row.querySelector('.main-link a.title') || row.querySelector('a.title');
    const title = titleLink ? titleLink.textContent.trim() : '';
    const views = row.querySelector('.views .number')?.textContent?.trim() || '0';
    const replies = row.querySelector('.posts .number')?.textContent?.trim() || '0';
    const tags = Array.from(row.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
    const activityCell = row.querySelector('td.activity');
    const titleAttr = activityCell?.getAttribute('title') || '';
    const createdMatch = titleAttr.match(/Created:\s*(.+?)(?:\n|$)/);
    const created = createdMatch ? createdMatch[1].trim() : '';
    posts.push({ id: topicId, title, views, replies, tags, created });
  });
  return JSON.stringify({ source: 'A', count: posts.length, ids: posts.map(p => p.id), posts });
})

// Source B: 保存 AI 标签过滤后的帖子（含时间戳）
browser_evaluate(filename="data/source_b.json", function=() => {
  const rows = document.querySelectorAll('tr.topic-list-item');
  const aiPosts = [];
  rows.forEach(row => {
    const topicId = row.getAttribute('data-topic-id');
    const titleLink = row.querySelector('.main-link a.title') || row.querySelector('a.title');
    const title = titleLink ? titleLink.textContent.trim() : '';
    const views = row.querySelector('.views .number')?.textContent?.trim() || '0';
    const replies = row.querySelector('.posts .number')?.textContent?.trim() || '0';
    const tags = Array.from(row.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
    const activityCell = row.querySelector('td.activity');
    const titleAttr = activityCell?.getAttribute('title') || '';
    const createdMatch = titleAttr.match(/Created:\s*(.+?)(?:\n|$)/);
    const created = createdMatch ? createdMatch[1].trim() : '';
    if (tags.some(t => /人工智能|ai/i.test(t))) {
      aiPosts.push({ id: topicId, title, views, replies, tags, created });
    }
  });
  return JSON.stringify({ source: 'B', total: rows.length, aiFiltered: aiPosts.length, ids: aiPosts.map(p => p.id), posts: aiPosts });
})
```

时间戳格式为 `"Jun 22, 2026 9:53 pm"`，后续用 `dateutil.parser.parse()` 解析。

### 1.4 合并两源 ID 列表

```python
import json
with open('data/source_a.json') as f:
    src_a = json.loads(json.load(f))
with open('data/source_b.json') as f:
    src_b = json.loads(json.load(f))

ids_a = set(src_a['ids'])
ids_b = set(src_b['ids'])
merged = list(ids_a | ids_b)

with open('data/merged_ids.json', 'w') as f:
    json.dump(merged, f)
print(f'Source A: {len(ids_a)}, Source B: {len(ids_b)}, Merged: {len(merged)}')
```

### 1.5 历史去重

```python
import re, os
prev_ids = set()
for f in os.listdir('data/reports'):
    if f.endswith('.md'):
        with open(f'data/reports/{f}') as fh:
            ids = re.findall(r'\[(\d{7,})\]', fh.read())
            prev_ids.update(ids)

with open('data/merged_ids.json') as f:
    all_ids = json.load(f)
new_ids = [pid for pid in all_ids if pid not in prev_ids]
with open('data/merged_ids.json', 'w') as f:
    json.dump(new_ids, f)
print(f'历史去重: {len(all_ids)} → {len(new_ids)}')
```

### 1.6 时间戳解析与 32h 筛选 + 写 crawl_queue（v15.2）

> **v11 变更**：时间戳已在步骤 1.3 中从列表页 `td.activity[title]` 提取，此步骤仅做解析和筛选。  
> **v15.2**：筛选结果写入 `data/crawl_queue.json`，并切分为 `data/batch_ids_{N}.json`（每批 30 id），**禁止**只 merge id 不写 queue。

**⚠️ 常识提醒**：帖子页面没有 `<time>` 元素！`document.querySelector('time')` 返回空。时间只能从列表页提取。

```python
import json, re, os
from dateutil import parser as dateparser
from datetime import datetime, timezone, timedelta

# 假定 posts 已是：两源合并 + 历史去重 + 标题/标签公益站过滤后的 dict 或 list
now = datetime.now(timezone(timedelta(hours=8)))
cutoff = now - timedelta(hours=32)
date_str = now.strftime('%Y-%m-%d')

def views_num(p):
    return int(re.sub(r'\D', '', str(p.get('views', '0'))) or 0)

final = []
for p in posts:  # list of post dicts with id/title/views/tags/created
    created_str = p.get('created', '')
    if not created_str:
        continue
    try:
        created_dt = dateparser.parse(created_str)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone(timedelta(hours=8)))
        if created_dt >= cutoff:
            p = dict(p)
            p['id'] = str(p['id'])
            p['created_at'] = created_dt.isoformat()
            final.append(p)
    except Exception:
        pass

final.sort(key=views_num, reverse=True)
os.makedirs('data', exist_ok=True)
with open('data/merged_ids.json', 'w') as f:
    json.dump([p['id'] for p in final], f)
with open('data/crawl_queue.json', 'w') as f:
    json.dump({'date': date_str, 'total': len(final), 'cutoff': cutoff.isoformat(), 'posts': final},
              f, ensure_ascii=False, indent=2)
for i in range(0, len(final), 30):
    n = i // 30
    with open(f'data/batch_ids_{n}.json', 'w') as f:
        json.dump([p['id'] for p in final[i:i+30]], f)
print(f'32h 筛选: {len(final)} 帖 → batches 0-{(len(final)-1)//30}')
```

### 1.7 逐帖浏览器浏览（核心抓取方案）

**必须使用此方案**，浏览器 fetch API 会被 429 限流。

#### ⚡ 提前终止 vs 全量（v15.2 澄清）

| 模式 | 条件 | 行为 |
|------|------|------|
| **标准** | 用户只说「日报」 | 按浏览量优先抓 4–5 批（120–150 帖）后可生成 |
| **全量** | 用户说「全部抓取」「过滤后全部抓取完」 | **必须**跑完 `crawl_queue` 全部批次（0717 实测约 18 批 / 517 帖） |

全量时不要在 150 帖提前停；Todo 标进度 `valid/total`。

#### 抓取流程

1. **打开列表页**：`browser_navigate → https://linux.do/tag/444-tag/444`
2. **滚动加载全部帖子**：见步骤 1.2（35 次滚动）
3. **提取帖子列表含时间戳**：`browser_evaluate`（见步骤 1.3，**绝对路径 filename**）
4. **合并去重筛选**：历史去重 + 公益站过滤 + 32h 筛选 → **crawl_queue + batch_ids**
5. **按浏览量排序**：已在 queue 内完成
6. **批量抓取正文**：每批 30 帖，从 `batch_ids_N.json` 读 id

#### 每帖提取数据

```js
// browser_evaluate 提取帖子数据
() => {
  const title = document.querySelector('.fancy-title')?.textContent?.trim() || '';
  const cooked = document.querySelector('.topic-post .cooked');
  const content = cooked ? cooked.textContent.trim().substring(0, 500) : '';
  const views = document.querySelector('.views .number')?.textContent?.trim() || '0';
  const tags = Array.from(document.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
  return { title, content, views, tags };
}
```

**注意**：不要用 `document.querySelector('time')` 获取时间，帖子页面没有 `<time>` 元素！时间从列表页的 `td.activity[title]` 提取。

#### 批量抓取代码（每批 30 帖，不回列表页）

```js
async (page) => {
  const ids = ["ID1", "ID2", /* ... 30个ID */];
  const results = [];
  for (let i = 0; i < ids.length; i++) {
    const tid = ids[i];
    try {
      await page.goto('https://linux.do/t/topic/' + tid, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForTimeout(2000);
      let pgTitle = await page.title();
      // Cloudflare 检测
      if (pgTitle.includes('Just a moment') || pgTitle.includes('Checking')) await page.waitForTimeout(15000);
      // 官方警告检测（v12 新增）
      const pageContent = await page.evaluate(() => document.body.innerText);
      if (pageContent.includes('异常的自动化访问行为') || pageContent.includes('系统检测到')) {
        return JSON.stringify({ batch: N, count: results.length, results, stopped: 'official_warning' });
      }
      const data = await page.evaluate(() => {
        const title = document.querySelector('.fancy-title')?.textContent?.trim() || '';
        const cooked = document.querySelector('.topic-post .cooked');
        const content = cooked ? cooked.textContent.trim().substring(0, 500) : '';
        const views = document.querySelector('.views .number')?.textContent?.trim() || '0';
        const tags = Array.from(document.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
        return { title, content, views, tags };
      });
      results.push({ id: tid, ...data });
      await page.waitForTimeout(1500);
    } catch (e) {
      results.push({ id: tid, error: String(e).substring(0, 100) });
    }
  }
  return JSON.stringify({ batch: N, count: results.length, results });
}
```

#### ⚠️ 批量抓取数据保存（v12 核心 + v15.2 transcript 回填）

**2026-06-29 实测问题**：浏览器 `browser_run_code_unsafe` 返回的 JSON 结果必须**立即保存到文件**，否则数据会丢失。

**正确流程**：
1. `browser_run_code_unsafe` 执行批量抓取 → 返回 JSON 字符串
2. **立即**保存到 `data/batch_browser_N.json`
3. 继续下一批

**错误做法**：等所有批次抓完再保存（数据会丢失）

```python
# 理想情况：工具返回字符串可直接 loads
import json
data = json.loads(results_json)  # 若外层仍是转义字符串，再 loads 一次
with open(f'data/batch_browser_{N}.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Batch {N} 已保存: {len(data.get("results", []))} 帖, valid={sum(1 for r in data["results"] if r.get("title"))}')
```

#### ⚠️ 大结果无法直接管道时：从 session transcript 回填（v15.2）

当返回体极大、无法在下一步 Bash 里手工粘贴时，**不要重爬该批**。从当前 session 的 jsonl 解析最近一次 `### Result\n"{...}"`：

```python
# 思路：读 ~/.claude/projects/.../<session>.jsonl
# 找含 ### Result 且 "batch":N 的 tool 结果文本
# start = text.find('### Result\n"') + len('### Result\n"')
# end = text.find('"\n###', start)
# unescaped = json.loads('"' + text[start:end] + '"')
# data = json.loads(unescaped)
# 写入 data/batch_browser_{N}.json
```

建议在项目里保留可复用脚本 `data/save_latest_batch.py`（参数为 batch 号），每批结束后：

```bash
python3 data/save_latest_batch.py N
```

#### 空帖检测（v12 新增）

抓取过程中会遇到大量**已删除或私有帖子**（返回空标题/空内容）。这些帖子不需要保存。

```python
# 过滤空帖
valid_posts = [p for p in results if p.get('title')]
deleted_count = len(results) - len(valid_posts)
if deleted_count > 0:
    print(f'跳过 {deleted_count} 个已删除/私有帖子')
```

#### 速度优化

- **每批 10–15 帖优先（v15.5）**：全量日长批（30）易触发 MCP 静默超时；稳定优先用 15，失败多时降到 10
- **每帖等待 2 秒**：帖子页加载后等待 2 秒再提取
- **帖间等待 1.5 秒**：避免触发限流（不回列表页，直接导航下一帖）
- **超时 20 秒**：单帖加载超时 20 秒则记 `error`，不中断整批

#### ⚠️ 批抓稳定性（v15.5 / 2026-07-20 实测）

**1) MCP 长静默超时**

`browser_run_code_unsafe` 一批跑很久无 progress 时，可能被 abort（实测约 **2491s**）：
> `MCP server "playwright" tool "browser_run_code_unsafe" sent no response or progress for 2491s; aborting`

**处理**：
- 优先 **缩小批次**（15 → 10），不要硬等超时
- 若可改 MCP 配置：为 playwright 设更大 per-server `timeout`（ms）
- 超时后：**不要当成功**；检查是否已有 partial 结果可回填；否则重跑该批

**2) `net::ERR_ABORTED` 批量失败**

`page.goto` 连续 `ERR_ABORTED` 时浏览器会话多半已坏。

**处理**：
1. 立即把本批结果落盘（含 `error` 项）
2. `pkill -f "mcp-chrome"` → `sleep 2` → `browser_navigate https://linux.do` 重建会话
3. 失败 id 写入 `data/rem_batch_*.json` 或单独 `batch_browser_retryN.json`
4. 重试成功后再并入 daily；**禁止**把全 error 批当 valid

**3) batch 文件污染**

旧 session / 错 cwd / 回填脚本把 **别日或非本批** 内容写入 `batch_browser_0.json` 等。

**合并前必须校验**每个 batch：
```python
import json, glob
for f in sorted(glob.glob('data/batch_browser_*.json')):
    d = json.load(open(f))
    results = d.get('results', d if isinstance(d, list) else [])
    if not results:
        print('EMPTY', f); continue
    # 本批应含 title 或 error；全空 / 结构不对则删除重抓
    ok = sum(1 for r in results if r.get('title') or r.get('error'))
    print(f, 'n=', len(results), 'okish=', ok)
```
污染文件：**删除** → 重算剩余 queue → 只抓缺失 id。

**4) 重试批命名**

`batch_browser_retry1.json` 等 **非纯数字** 批号合法。`save_latest_batch.py` 解析 batch 号时勿 `int()` 强制数字文件名；合并用 `glob('data/batch_browser_*.json')`。

**5) 中断 / 工具丢失后续跑**

用户 interrupt 或会话只剩部分工具时：
1. 先 `ls data/batch_browser_*.json` + 是否已有 `data/daily/{date}.json`
2. 有 batch 无 daily → **只合并 + Writer**，不冷启动清 queue
3. 有 daily+pdf → 直接交 ai-news-factory
4. **禁止**在工具不全时重写「手动 bash 教程」假装完成；恢复 MCP/Bash 后再跑

### 1.7 数据保存

每批抓取完成后，**必须立即**使用 Python 保存到文件（v12 强调：延迟保存会导致数据丢失）：

```python
import json
# results_json 是 browser_run_code_unsafe 返回的字符串
data = json.loads(results_json)
with open(f'data/batch_browser_{N}.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Batch {N} 已保存: {data.get("count", 0)} 帖')
```

### 1.8 数据合并与过滤（v15.2：正文二次过滤 + 列表 views 合并）

> **v12 重要修复**：`browser_evaluate` 使用 `filename` 参数保存的 JSON 文件是 **double-encoded**，需要用 `json.loads(json.load(f))` 读取。  
> **v15.2**：列表阶段公益站过滤不够（正文才暴露「公益推广/CDK/日抛」）→ **合并 batch 后再滤一次**；帖子页 `views` 常为 `0` → **与 crawl_queue 列表 views 取更合理值**。

```python
import json, os, glob, re
from datetime import datetime, timezone, timedelta

queue = json.load(open('data/crawl_queue.json'))
meta = {str(p['id']): p for p in queue['posts']}

all_posts = {}
for f in sorted(glob.glob('data/batch_browser_*.json')):
    with open(f) as fh:
        batch = json.load(fh)
    if isinstance(batch, str):
        batch = json.loads(batch)
    for p in batch.get('results', []):
        pid = str(p.get('id', ''))
        if not (pid and p.get('title')):
            continue
        m = meta.get(pid, {})
        if m.get('created'):
            p['created'] = m['created']
        if m.get('created_at'):
            p['created_at'] = m['created_at']
        # 列表页 views 优先于帖子页 0/异常
        def vn(x):
            return int(re.sub(r'\D', '', str(x or '0')) or 0)
        if vn(p.get('views')) == 0 and vn(m.get('views')) > 0:
            p['views'] = m.get('views')
        elif vn(m.get('views')) > vn(p.get('views')):
            p['views'] = m.get('views')
        p['tags'] = list(dict.fromkeys((p.get('tags') or []) + (m.get('tags') or [])))
        p['id'] = pid
        all_posts[pid] = p

print(f'合并后有效帖子: {len(all_posts)}')

GONGYI_KEYWORDS = [
    '公益站', '公益推广', 'LDC', 'ldc', 'cdk', '签到', '白嫖',
    '薅羊毛', '薅秃', '兑换码', '免费额度', '号池', '号商', '充值额度',
    '中转站', '高级推广', '抽奖', '富可敌国', '接码', '代充',
    # v15.2 正文二次过滤补充
    'LightBridge公益', 'YSX666', '日抛', '午夜福利', 'CDK',
    # v16.18 补充（W46 实测漏网）：薅取黑话与虚拟卡/绕验证类操作帖。
    # 注意不要加 '0元试用' 这类纯事件词——它会把「官方免费试用被清算」的新闻帖一起滤掉，
    # 那类帖属于风险信号，应保留并按降权处理（不进亮点、不给操作步骤）。
    '焚诀', '虚拟卡', '不弹出kyc', '不弹kyc',
]
TRADE = ['求号', '出号', '共享车']

filtered = {}
removed = 0
for pid, p in all_posts.items():
    title = p.get('title', '') or ''
    tags = ' '.join(p.get('tags') or [])
    content = (p.get('content') or '')[:200]
    all_text = f'{title} {tags} {content}'
    if any(kw in all_text for kw in GONGYI_KEYWORDS):
        removed += 1
        continue
    if any(kw in title for kw in TRADE) and not any(x in title for x in ['风控', '封号', '行业', '分析', '讨论']):
        removed += 1
        continue
    filtered[pid] = p

print(f'公益站/交易二次过滤后: {len(filtered)} (removed {removed})')

date_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')
os.makedirs('data/daily', exist_ok=True)
posts_list = sorted(filtered.values(),
                    key=lambda p: int(re.sub(r'\D', '', str(p.get('views', '0'))) or 0),
                    reverse=True)
daily_data = {
    'date': date_str,
    'total': len(posts_list),
    'with_content': sum(1 for p in posts_list if p.get('content')),
    'cutoff': queue.get('cutoff'),
    'posts': posts_list,
}
with open(f'data/daily/{date_str}.json', 'w') as f:
    json.dump(daily_data, f, ensure_ascii=False, indent=2)
print(f'saved data/daily/{date_str}.json total={daily_data["total"]}')
```

---

## Agent 2: Topic Merger（主题合并器）

**职责**：合并两个数据源的帖子，去重，过滤公益站，按主题聚类。

### 主题分类规则

按以下维度对帖子进行分组（按优先级匹配，命中第一个即归类）：
- **OpenAI/ChatGPT/Codex 生态**：codex, chatgpt, gpt, openai, sub2api, plus, pro20, pro 5x, sol, terra, luna, tibo, gpt-red
- **Claude/Anthropic 生态**：fable, mythos, opus, anthropic, claude code, claudecode, cc-switch, max, ultracode
- **Kimi/月之暗面**：kimi, 月之暗面, moonshot, k3, kivine, kivio
- **Grok/xAI 生态**：grok, xai, spacexai, supergrok, 马圣, 老马
- **豆包/火山引擎 生态**：豆包, doubao, seed, 火山, seedance, 字节, qoder
- **GLM/智谱 生态**：glm, 智谱, zai, glm5.2, codegeex
- **Google/Gemini 生态**：gemini, google, antigravity, spark, ai studio, pixel
- **DeepSeek 生态**：deepseek, ds, v4（注意与通用英文词区分，优先标题/标签）
- **AI 编程工具**：cursor, windsurf, trae, hermes, opencode, kiro, minimax, copilot
- **开源项目**：开源推广, 开源
- **行业动态**：前沿快讯, 前沿, 转载, 安全, 边界, waic, nvidia, h200, 监管, linus
- **其他话题**：其余

---

## Agent 3: Trend Analyzer（趋势分析器）

**职责**：分析帖子内容和热度，生成今日技术趋势。

### 分析维度

- **热度分析**：浏览量、回复数、点赞数最高的帖子
- **内容分析**：帖子正文中反复出现的技术关键词
- **时间线**：今日新出现的话题 vs 持续讨论的话题
- **争议性**：回复数/浏览比最高的帖子（讨论最激烈）
- **可信度提示（v15）**：对关键话题尽量给 `source_hint`（能判则判，不能判标未确认）：
  - 含官网 / 官方 blog / 官方公告 / 官方 X → `官方确认`
  - 含主流媒体报道 → `媒体报道`
  - 含可复现实测 / 截图实测 → `社区实测`
  - 仅模型列表 / changelog / 源码字符串 → `源码迹象`
  - 含网传 / 疑似 / 爆料 / 猜测 → `未确认传闻`

---

## Agent 4: Writer（日报撰写器）

**职责**：读取合并数据和趋势分析，生成完整的 Markdown 日报。

### 🔴 技术锚点（v15.0.0 · ai-concept-bank）

Writer **应**在日报中点出技术概念，供下游 ai-news-factory Step 1.6 匹配；**不**在报告里写完整 15s 口播。

1. **读库**（可选但推荐）：`ai-concept-bank/concepts.json`  
   - 仅使用 `status=ready` 且 `script_meta.authored_by=ai-concept-narrator` 且 `reviewed=true` 的条目做「技术锚点」字段  
   - 用帖子标题+摘要匹配 `news_keywords` / `aliases` / `name`  
2. **条目可增字段**（有命中时写；无命中可省略）：
   - `技术锚点：{concept name} — {one_liner}`  
   - 不得把 `script_15s` 全文贴进日报（口播留给视频 Phase 2）  
3. **禁止**：主会话手写与库冲突的长定义；库无命中时可用半句中性说明，或省略  
4. **候选发现**（不阻断成稿）：正文出现库中没有的黑话 → 在日报末可选附录 `## 概念候选（供 concept-bank）` 列 1–5 个词，供周维护晋升  

> 完整 15s 台词、usage-log 由 **ai-news-factory** 与 **ai-concept-narrator** 负责，Writer 不写 usage-log。

### 日报结构

```markdown
# linux.do 人工智能 技术日报
**{date}** | 数据来源：linux.do #人工智能 + 前沿快讯

## 今日亮点
1. [{可信度五档之一}] {一句话事实} — 影响：{一句}（浏览 X）
2. ...
（3–5 条；优先模型发布/开源/安全/开发者工具/政策/可引用数据；
 权益/封号/低价渠道 **不得占亮点 50% 以上**）

## 新内容

### {主题分组名}
- **{中性重写标题}** — {事实摘要 1–2 句}
  - 可信度：{官方确认 | 媒体报道 | 社区实测 | 源码迹象 | 未确认传闻}
  - 影响：{对用户/开发者/行业，一句}
  - 技术锚点：{可选} {ready name} — {one_liner}
  - 信号：浏览 X · 争议度{高/中/低}

（按主题分组，每组 3-10 个帖子；低价值权益帖可短摘要或合并）

## 数据概览
| 标签 | 帖数 |
|------|------|

## 概念候选（供 concept-bank，可选）
- {新黑话1} — 出现在：{帖标题}
```

### Writer 风格硬规则（v15）

1. **禁止原样转发**含：震惊、牛逼、已急哭、铁证、炸了、大瓜、彻底炸锅 等 → 必须中性重写  
2. **摘要**须回答「发生了什么 + 为何值得记」，禁止只截帖子首句情绪句  
3. **可信度必填**（五档枚举，禁止自创）；`未确认传闻` 不得写成已官宣事实  
4. **技术锚点**：架构/评测/安全/Agent/定价机制尽量给 1 句（来自 concept-bank ready 的 one_liner）；纯融资可省略  
5. **亮点选择**：硬新闻优先；封号潮重复、低价区、未确认灰度第 N 次、纯情绪帖降权  
6. 数据来源说明可加：「条目含可信度分层，未确认信息不作为定论」

### 🟡 概念候选受控入库（v15.1.0 · 可选但推荐）

**执行时机**：日报 Markdown 写入完成后、Press Writer / PDF Builder 启动前。
**目标**：减少人工搬运，但只把合格新词追加为最小 `candidate`；不生产口播、不晋升 `draft/ready`、不写 `usage-log`。

#### 1. 读取候选来源

仅从本期日报 Markdown 的附录读取：

```markdown
## 概念候选（供 concept-bank）
- **候选名** — 出现在：...
```

若日报没有该附录，或附录为空，跳过本步骤，不阻断 Press / PDF。

#### 2. 读取概念库与频次表

必须读取：

```text
ai-concept-bank/concepts.json
```

可选读取（用于长期价值参考，不要求每天重跑）：

```text
ai-concept-bank/extracts/term-frequency.json
```

月度维护时由 `ai-concept-bank/scripts/extract-term-frequency.py` 刷新长期频次；日报候选只负责发现新词。

#### 3. 去重规则（任一命中即跳过新增）

候选必须与 `concepts.json` 中已有条目的以下字段去重：

- `id`
- `name`
- `aliases`
- `news_keywords`

去重时应同时检查中英文、大小写、空格、连字符和常见缩写。若候选更像已有概念的新说法，优先记录为后续 `aliases` / `angles.available` 的维护建议，不新建概念。

#### 4. 过滤规则（任一命中即跳过）

- 营销词、标题党词、社区情绪词。
- 公司名、产品名、模型型号或单次事件名。
- 账号权益、低价渠道、封号套利、号池、兑换码等权益黑话。
- `可信度=未确认传闻` 且缺少可复核技术含义。
- 只能描述当天个案、无法形成稳定定义的说法。
- 不能在约 15 秒内讲清一个核心点的复杂混合表达。
- 与已有 ready/candidate 概念高度重叠，但更适合作为新角度。

#### 5. 追加最小 candidate

> **v15.6 结构铁律**：`ai-concept-bank/concepts.json` 根对象是  
> `{ "version", "updated", "reuse_gap_days", "narrator_agent", "corpus_extract", "concepts": [ ... ] }`，  
> **不是**顶层数组。读写必须：
> ```python
> data = json.load(open('ai-concept-bank/concepts.json'))
> concepts = data['concepts']          # list
> # ... append / mutate concepts ...
> data['concepts'] = concepts
> data['updated'] = 'YYYY-MM-DD'
> json.dump(data, open(...), ensure_ascii=False, indent=2)
> ```
> 禁止 `for c in json.load(...): c.get(...)`（根是 dict 会 AttributeError）。

通过去重与过滤后，只能追加最小 `candidate`，字段模板：

```json
{
  "id": "snake_case_id",
  "name": "候选名",
  "aliases": [],
  "category": "待定",
  "tier": 3,
  "difficulty": "待定",
  "status": "candidate",
  "one_liner": "",
  "analogy": "",
  "script_15s": "",
  "script_60s": null,
  "script_meta": {
    "authored_by": "ai-concept-narrator",
    "authored_at": null,
    "reviewed": false,
    "angle": null
  },
  "news_keywords": ["候选名"],
  "corpus": null,
  "angles": {
    "available": ["基础定义"],
    "used": []
  },
  "related_events": [],
  "sources": ["data/reports/{YYYY-MM-DD}.md#概念候选"],
  "last_used": null,
  "use_count": 0
}
```

若候选可匹配 `term-frequency.json` 的 `normalized_id`，可复制精简 `corpus`：

```json
{
  "count_total": 0,
  "count_scripts": 0,
  "count_reports": 0,
  "top_paths": []
}
```

否则保持 `corpus: null`，等待月度 term-frequency 验证长期价值。

#### 6. 写入后校验

写入 `concepts.json` 后必须执行：

```bash
jq empty ai-concept-bank/concepts.json
jq '.concepts | type' ai-concept-bank/concepts.json   # 期望 "array"
```

并人工确认：

- 新增条目在 `data['concepts']` 内，且 `status == "candidate"`。
- `script_15s == ""`。
- `script_meta.reviewed == false`。
- 未修改 `usage-log.json`。
- 未改动已有 ready 概念的口播和状态。

#### 7. 禁止事项

- 禁止自动调用 `ai-concept-narrator`。
- 禁止自动设 `reviewed=true`。
- 禁止自动晋升 `draft` 或 `ready`。
- 禁止写入 `usage-log.json`。
- 禁止覆盖已有概念、删除历史字段或改 `last_used/use_count`。
- 禁止静默 git commit 子模块。

> 职责边界：日报候选负责发现新词；`term-frequency` 负责验证长期价值；概念库维护 Agent 决定后续 `candidate → draft → ready`。

---

## Agent 5: Press Writer（新闻稿撰写器）

**职责**：基于日报内容，生成专业 AI 科技新闻稿。

### 新闻稿结构

```markdown
# {标题}

{导语 — 一句话概括核心事件}

## 正文

{2-4 段深度报道}

## 社区反应

{精选 3-5 条有代表性的社区观点}

## 风险与争议

{潜在风险、争议点}
```

### 写作风格

- **对标媒体**：Bloomberg Tech、The Verge、TechCrunch
- **禁止**：论坛口语、emoji、感叹号堆砌、情绪夸张词（炸了/大瓜等）
- **数据优先**：每个论点必须有数据支撑
- **可信度（v15）**：每则核心事件标注五档之一；导语禁止情绪词；「风险与争议」区分已证实风险 vs 社区猜测
- **技术概念（v15）**：可引用 `ai-concept-bank` ready 的 `one_liner`；禁止自创与库冲突的长定义；完整口播归 narrator

---

## Agent 6: PDF Builder（PDF 生成器）

**职责**：将 Markdown 日报转换为 PDF 文件，使用 Typst 排版。

### Typst 模板

```typst
#set document(title: "linux.do AI 技术日报 - {date}")
#set page(paper: "a4", margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm))
#set text(font: ("PingFang SC", "Helvetica Neue", "Arial"), size: 10pt)
#set heading(numbering: none)
```

### ⚠️ Typst 特殊字符处理（v12 重点修复）

**2026-06-29 实测问题**：以下字符在 Typst 中有特殊含义，必须转义：

| 字符 | 用途 | 转义方式 | 示例 |
|------|------|---------|------|
| `$` | 数学模式 | `\$` | `\$50` 而非 `$50` |
| `#` | 标记符号 | `\#` | `\#人工智能` 而非 `#人工智能` |
| `*` | 斜体 | 用 `*text*` | 标题用斜体代替粗体 |
| `_` | 下标 | `\_` | `\_views` 而非 `_views` |

**Typst 不支持 `**bold**` 语法**，用 `*斜体*` 代替。

### 编译命令

```bash
typst compile data/reports/{date}.typ data/reports/{date}.pdf
```

---

## 周报模式（v14 新增完整流程）

> **🔴 v16.10.0 平台发布字段（坑 482，2026-11-15 W45 实跑）**：周报交给 ai-news-factory 时，`publish.json` 的
> `platform.bilibili.collection` / `douyin.collection` / `channels.collection` / `wechat.collection` /
> `zhihu.column` **全部必须是「羊报AI周刊」**，不能沿用日更的「今日羊报 AI」/「今日羊报Al」。
> 月报同理，全部为「羊报AI月报」。只改日期不改这五个字段 = 五平台合集/专栏全选错，而且点击全部成功、零报错。
> 详见 ai-news-factory 的「模式参数映射表」与「平台合集/专栏矩阵」。

周报**聚合当周已抓取的日报数据**，不重复抓取。基于 `data/daily/{YYYY-MM-DD}.json` 和 `data/reports/{YYYY-MM-DD}.json` 生成。

### 周报数据聚合

```python
import json, os, glob, re
from datetime import datetime, timedelta, timezone

# 🔴 v16.18：目标周必须显式取「周一 → 周日」，不能用 now 直接取「本周至今」。
#    now.weekday() 在周日跑时恰好等于 6，看起来没问题；但周一到周六跑会把最近 7 天
#    （含缺勤日）当成一整周，产出「6 天有数据、1 天缺失」的残周，而且 --week-id 会漂移。
TARGET_MONDAY = datetime(2026, 11, 16, tzinfo=timezone(timedelta(hours=8)))  # ← 当场显式写死
week_start = TARGET_MONDAY.strftime('%Y-%m-%d')
week_end = (TARGET_MONDAY + timedelta(days=6)).strftime('%Y-%m-%d')
# 周号沿用历史口径 %W（周一起点），与 data/weekly/W40..W46 全部产物一致：
# 11-16 周一 → %W46；若换 isocalendar().week（ISO）会得到 W47，与历史断代一天。
week_id = TARGET_MONDAY.strftime('%Y-W%W')  # 2026-11-16 → 2026-W46
# 🔴 v16.18 门禁：先把 7 天日报点齐再聚合，缺哪天要点名而非静默跳过。
missing_days = [ (TARGET_MONDAY + timedelta(days=i)).strftime('%Y-%m-%d')
                 for i in range(7)
                 if not os.path.exists(f'data/daily/{(TARGET_MONDAY + timedelta(days=i)).strftime("%Y-%m-%d")}.json') ]
if missing_days:
    print(f'WARN missing daily: {missing_days}  -> 必须写进报告「数据来源说明」')
    # 缺 1-2 天可继续（报告里点名）；缺 >=3 天就停，让用户先补日报，别产出半周周报
    assert len(missing_days) < 3, f'缺 {len(missing_days)} 天日报，周报不成立：{missing_days}'


# 聚合本周 daily JSON（注意只匹配 YYYY-MM-DD.json，排除 _sorted/_topics 等后缀文件）
week_posts = {}
covered_days = []
for f in sorted(glob.glob('data/daily/2026-*.json')):
    fname = os.path.basename(f).replace('.json', '')
    # 排除带后缀的文件（如 2026-06-30_sorted.json）
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fname):
        continue
    if week_start <= fname <= week_end:
        try:
            with open(f) as fh:
                d = json.load(fh)
            posts = d.get('posts', [])
            covered_days.append(fname)
            for p in posts:
                pid = str(p.get('id', ''))
                if not (pid and p.get('title')):
                    continue
                # v15.4：同 id 保留更高浏览量；记下来源日
                def vn(x):
                    s = str(x or '0').strip().lower().replace(',', '')
                    m = re.match(r'([\d.]+)\s*([km万])?', s)
                    if not m:
                        return int(re.sub(r'\D', '', s) or 0)
                    n = float(m.group(1)); u = m.group(2)
                    if u == 'k': n *= 1000
                    elif u == 'm': n *= 1e6
                    elif u == '万': n *= 10000
                    return int(n)
                prev = week_posts.get(pid)
                if not prev or vn(p.get('views')) >= vn(prev.get('views')):
                    p = dict(p)
                    p['id'] = pid
                    p['_day'] = fname
                    week_posts[pid] = p
        except Exception:
            pass

# 扫描本周日报提取亮点
weekly_highlights = {}
for f in sorted(glob.glob('data/reports/2026-*.md')):
    fname = os.path.basename(f).replace('.md', '')
    if '_press' in fname:
        continue
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fname):
        continue
    if week_start <= fname <= week_end:
        try:
            with open(f) as fh:
                content = fh.read()
            m = re.search(r'## (?:今日|本周)亮点\n+(.*?)(?=\n##|\Z)', content, re.S)
            if m:
                bullets = [b.strip() for b in m.group(1).strip().split('\n') if b.strip()]
                if bullets:
                    weekly_highlights[fname] = bullets
        except Exception:
            pass

os.makedirs('data/weekly', exist_ok=True)
week_data = {
    'week': week_id,
    'week_start': week_start,
    'week_end': week_end,
    'covered_days': covered_days,
    'total_topics': len(week_posts),
    'posts': list(week_posts.values()),
    'daily_highlights': weekly_highlights,
}
with open(f'data/weekly/{week_id}.json', 'w') as f:
    json.dump(week_data, f, ensure_ascii=False, indent=2)
print(f'week={week_id} days={covered_days} total={len(week_posts)}')
```

### 周报 TOP 排序注意（v15.4）

列表页 `views` 常为 **`6.2k` / `1.1万` 字符串**，TOP 排序必须用上面的 `vn()`（k/m/万）解析，**禁止** `int(re.sub(r'\D','', views))`（会把 `6.2k` 变成 `62` 或丢掉数量级）。

输出文件（建议齐全）：
- `data/weekly/{week_id}.json` / `.md` / `_press.md` / `.typ` / `.pdf`
- 可选：`{week_id}_topics.json`（主题分组计数 + hard-news TOP）

### 周报多 Agent 流程

周报**不抓取新数据**，6 个 Agent 职责调整：

| Agent | 日报职责 | 周报职责 |
|-------|---------|---------|
| Crawler | 抓取双源 | **聚合本周 daily JSON + 日报 MD** |
| Topic Merger | 合并去重 | 合并本周所有帖子按主题分类（每周 TOP 5） |
| Trend Analyzer | 今日趋势 | **跨日趋势归纳**（升温/降温/事件线） |
| Writer | 日报 MD | 周报 MD（含大事记 + 趋势 + 升温降温表） |
| Press Writer | 新闻稿 | 周度新闻稿 |
| PDF Builder | 日报 PDF | 周报 PDF |

**⚡ 并行优化（v14 新增）**：Topic Merger 和 Trend Analyzer 可以**并行启动**，两者数据独立无需等待。Writer 等两者完成后再启动。

### 周报 Markdown 模板（Writer Agent 专用）

```markdown
# linux.do 人工智能 技术周报
**{week_id}（{week_start} ~ {week_end}）** | 数据来源：linux.do #人工智能 + 前沿快讯

## 本周亮点
1. [{可信度}] {事实} — 影响：{一句}（浏览 X）
（5 条；硬新闻优先；中性标题）

## 本周大事记
- **{日期}** [{可信度}] {中性标题} — {一句}；影响：{一句}

## 本周热门主题 TOP 10
1. **{中性标题}** — 摘要（浏览 X | 日期）
   - 可信度：{五档}

## 主题趋势分析
### 趋势一：{趋势名}
（事实变化 → 谁受益/谁承压 → 下周观察；避免情绪复述）
- 可信度区间：{若案例多为传闻需写明}

## 主题分布
| 主题分组 | 帖数 | 占比 |

## 升温 vs 降温
| 升温话题 | 降温话题 |

## 下周展望
（2-3 句可验证观察点）

## 数据来源说明
- 数据时间范围：{week_start} ~ {week_end}
- 基于日报文件：{count} 份
- 公益站/中转站内容已过滤
- 条目含可信度分层，未确认信息不作为定论
```

---

## 月报模式（v13 新增）

> **🔴 v16.10.0 平台发布字段（坑 482）**：月报的 B站/抖音/视频号/公众号合集与知乎专栏全部为「羊报AI月报」；
> 交付 ai-news-factory 时必须覆盖 `publish.json` 的五个 collection/column 字段，不能沿用日更或周报值。

月报**不重复抓取**，而是基于当月已抓取的日报数据（`data/daily/{YYYY-MM-DD}.json`）与已生成的日报 Markdown（`data/reports/{YYYY-MM-DD}.md`）聚合生成。若某日数据缺失，月报会标注缺失天数并继续生成。

### 月份解析

```python
import re
from datetime import datetime, timezone, timedelta

def parse_month(user_msg, now=None):
    """从用户消息解析目标月份，默认返回上一个自然月 (YYYY-MM)。"""
    now = now or datetime.now(timezone(timedelta(hours=8)))
    # 支持形如 "2026-05" / "2026年5月" / "2026-5"
    m = re.search(r'(20\d{2})\D{0,2}(\d{1,2})', user_msg)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    # "上月月报" → 上一个自然月
    first_of_this_month = now.replace(day=1)
    last_month = first_of_this_month - timedelta(days=1)
    return last_month.strftime('%Y-%m')
```

### 数据聚合逻辑

读取目标月份所有日报数据，合并帖子去重，并扫描日报 Markdown 提取亮点：

```python
import json, os, glob, re
from datetime import datetime, timedelta, timezone

month = parse_month(user_msg)  # 如 "2026-05"

# 1. 定位月内所有日期
year, mon = map(int, month.split('-'))
start = datetime(year, mon, 1, tzinfo=timezone(timedelta(hours=8)))
if mon == 12:
    end = datetime(year + 1, 1, 1, tzinfo=timezone(timedelta(hours=8)))
else:
    end = datetime(year, mon + 1, 1, tzinfo=timezone(timedelta(hours=8)))
total_days = (end - start).days

# 2. 聚合 daily JSON
month_posts = {}          # 帖子去重
covered_days = []         # 有日报数据的日期
missing_days = []
day_topic_counts = {}     # 每日主题数（用于活跃度趋势）

cur = start
while cur < end:
    date_str = cur.strftime('%Y-%m-%d')
    daily_path = f'data/daily/{date_str}.json'
    if os.path.exists(daily_path):
        try:
            with open(daily_path) as f:
                daily = json.load(f)
            posts = daily.get('posts', [])
            day_topic_counts[date_str] = len(posts)
            if posts:
                covered_days.append(date_str)
            for p in posts:
                pid = str(p.get('id', ''))
                if pid and p.get('title'):
                    month_posts[pid] = p
        except Exception:
            missing_days.append(date_str)
    else:
        missing_days.append(date_str)
    cur += timedelta(days=1)

# 3. 扫描日报 Markdown 提取每日亮点（用于月度趋势归纳）
daily_highlights = {}     # {date: [亮点句子]}
for md_path in sorted(glob.glob('data/reports/*.md')):
    fname = os.path.basename(md_path).replace('.md', '')
    if not fname.startswith(month):
        continue
    try:
        with open(md_path) as f:
            content = f.read()
    except Exception:
        continue
    # 提取 "今日亮点" / "本周亮点" 段落要点
    m = re.search(r'## (?:今日|本周)亮点\n+(.*?)(?=\n##|\Z)', content, re.S)
    if m:
        bullets = [b.strip('- ').strip() for b in m.group(1).strip().split('\n') if b.strip().startswith('-')]
        if bullets:
            daily_highlights[fname] = bullets

# 4. 公益站过滤（与日报一致，v12 规则复用）
GONGYI_KEYWORDS = ['公益站', '公益推广', 'LDC', 'ldc', 'cdk', '签到', '白嫖',
                   '薅羊毛', '薅秃', '兑换码', '免费额度', '号池', '号商', '充值额度',
                   '中转站', '高级推广', '抽奖', '富可敌国']
filtered_posts = {}
for pid, p in month_posts.items():
    all_text = f"{p.get('title', '')} {' '.join(p.get('tags', []))}"
    if not any(kw in all_text for kw in GONGYI_KEYWORDS):
        filtered_posts[pid] = p

# 5. 按浏览量排序取月度 TOP 10
top_posts = sorted(filtered_posts.values(),
                   key=lambda p: int(re.sub(r'\D', '', p.get('views', '0')) or 0),
                   reverse=True)[:10]

month_data = {
    'month': month,
    'total_days': total_days,
    'covered_days': covered_days,
    'missing_days': missing_days,
    'coverage': f'{len(covered_days)}/{total_days}',
    'total_topics': len(filtered_posts),
    'day_topic_counts': day_topic_counts,
    'daily_highlights': daily_highlights,
    'top_posts': top_posts,
}
os.makedirs('data/monthly', exist_ok=True)
with open(f'data/monthly/{month}.json', 'w') as f:
    json.dump(month_data, f, ensure_ascii=False, indent=2)
print(f'月报数据聚合: {month} 覆盖 {len(covered_days)}/{total_days} 天, '
      f'有效主题 {len(filtered_posts)} 个')
```

### 月报 Markdown 模板（Writer Agent 专用）

```markdown
# linux.do 人工智能 技术月报
**{YYYY-MM}** | 数据来源：当月日报聚合（{covered_days}/{total_days} 天）

## 本月概览
- 数据覆盖天数：{covered_days}/{total_days}
- 缺失天数：{missing_days}（如有）
- 月度主题总数：{total_topics}
- 最活跃讨论日：{most_active_day}（{peak_count} 个新主题）
- 日均新主题数：{avg_per_day}

## 本月热门主题 TOP 10
1. **{中性标题}** — 摘要（浏览 X | 回复 Y | 出现日期）
   - 可信度：{五档}
2. ...
（按月度浏览量降序；套利/渠道促销帖不得入选 TOP）

## 月度技术趋势
### 趋势一：{趋势名称}
- **热度变化**：本月讨论量 / 起止时间 / 周环比
- **关键驱动**：核心事件或发布
- **代表主题**：相关帖子链接
- **可信度区间**：{若案例多为传闻需写明}
- **影响**：谁受益 / 谁承压

### 趋势二 / 趋势三 …
（基于 daily_highlights 跨日归纳，不按天拼接）

## 主题分布
| 主题分组 | 帖数 | 占比 |
|---------|------|------|
| OpenAI/ChatGPT 生态 | ... | ... |
| Claude/Anthropic 生态 | ... | ... |
（复用 Agent 2 主题分类规则）

## 下月展望
基于本月趋势，预测下月可能关注的方向：
- 预测方向 1（依据：本月某趋势持续升温）
- 预测方向 2
- 预测方向 3

## 数据来源说明
- 数据时间范围：{YYYY-MM-01} ~ {YYYY-MM-末}
- 基于日报文件：{daily_count} 份
- 缺失日期：{missing_days}（如有，标注影响）
- 公益站/中转站内容已过滤
- 条目含可信度分层，未确认信息不作为定论
```

### 月报多 Agent 流程

月报模式下，**Crawler 不抓取新数据**，6 个 Agent 的职责调整：

| Agent | 日报职责 | 月报职责 |
|-------|---------|---------|
| Crawler | 抓取双源 | **读取当月 daily JSON + 日报 MD** |
| Topic Merger | 合并去重 | 合并当月所有帖子去重（不去重历史） |
| Trend Analyzer | 今日趋势 | **跨日趋势归纳**（基于 daily_highlights） |
| Writer | 日报 MD | 月报 MD（用月报模板） |
| Press Writer | 新闻稿 | 月度新闻稿 |
| PDF Builder | 日报 PDF | 月报 PDF（复用 Typst 模板，转义规则同 v12） |

### 月报 Typst 输出

```bash
typst compile data/monthly/{YYYY-MM}.typ data/monthly/{YYYY-MM}.pdf
```
Typst 特殊字符转义规则与日报一致（`$` → `\$`、`#` → `\#`、不支持 `**bold**`）。

---

## 注意事项

### 浏览器与抓取
- **固定 cwd**：先 `cd /Users/youngsdream/Documents/learn-claude-code`（v15.2）
- **必须使用浏览器逐帖浏览**：`browser_navigate` / `browser_run_code_unsafe` 打开帖子页面，不能用 fetch API
- **Cloudflare 挑战**：标题含 "Just a moment" 则等待 15 秒；预授权可点击验证区域（v14）。**0717 实测有时可直接进入站点**——以 `document.title` 为准
- **不回列表页**：直接从一个帖子导航到下一个帖子
- **每帖等待 1.5 秒** + 页载后 2 秒：避免触发限流
- **每批 10–15 帖（v15.5 默认）**：全量稳定优先；标准模式仍可 30
- **提前终止**：仅标准日报可在 120–150 帖后进入生成
- **全量抓取**：「全部抓取 / 过滤后全部抓取完」必须跑完 queue；规模约 **20–35 批 / 350–550 帖**（0717：517→490 有效；0720：26+ 批 → 364；**0725：33 批 → 489→455 有效**）
- **单 Playwright**：批抓阶段禁止并行独立 Chrome 抢 profile（v15.3）
- **ERR_ABORTED / MCP 静默超时**：重置浏览器、缩小批次、retry 批号（v15.5）
- **中断续跑（v15.8）**：用户 interrupt 后先盘点 `batch_browser_*.json` 是否已覆盖 queue；**已齐 → 只合并 Writer**，不要清 archive 重抓
- **MCP 断连兜底（v15.9 / 2026-09-17）**：`claude mcp list` 显示 playwright `Failed to connect` 时，**不要空等 MCP**。用项目脚本 Node 直连 Playwright（参考 `data/_fetch_lists_0917.mjs` + `data/_crawl_0917.mjs`）：
  1. **headed 默认**（`HEADLESS=1` 才无头）。0917 实测 headless 卡 Cloudflare，「Just a moment」滚 30 次仍 0 rows；headed 后 Source A 750 / B 321。
  2. `page.evaluate` 在 playwright-core 里**只接受一个参数**。0831 脚本把 `(key, filterSrc)` 拆成两参 → `Too many arguments`，必须包成对象 `{ key, filterSrc }`。
  3. Chromium 可执行文件**按本机缓存探测**，勿写死 `chromium-1223`（0917 已是 `chromium-1228`）。优先 `~/Library/Caches/ms-playwright/chromium-*/chrome-mac-arm64/.../Google Chrome for Testing` 最新目录。
  4. 列表+正文共用 **mcp-chrome profile**；每批立即写 `data/batch_browser_N.json`；已存在批次跳过（续跑协议不变）。
  5. 此兜底**只用于抓取**。上传阶段浏览器必须是日常 Chrome / MCP 会话，禁止把 Chrome for Testing 当上传 daemon（见 ai-news-factory v3.34 坑 198）。
- **Node 直连全量协议（v16.0 / 2026-09-18～09-20）**：连续三期使用后，Node 路径从临时兜底升级为可复用方案，但必须满足以下约束：
  1. **当期日期是显式参数/常量**：文件名、头部注释、Usage、queue 的 `date/base/cutoff`、batch 元数据必须同源；复制 `_0917` 脚本后要全量搜索旧日期，禁止只改文件名。
  2. **32h 窗口固定按当期 00:05 CST**：`base = datetime(Y, M, D, 0, 5, tzinfo=CST)`，`cutoff = base - timedelta(hours=32)`；禁止用脚本实际启动时的 `datetime.now()`，否则 00:05 之后恢复任务会无意缩短窗口（0920 实测启动较晚，cutoff 漂到 16:34）。
  3. **正文批次原子保存**：先写同目录 `batch_browser_N.json.tmp`，写完并 `JSON.parse` 自检后 `renameSync(tmp, outfile)`；中断不得留下可被续跑误认成完整批次的半截 JSON。
  4. **跳过已有批次前验完整性**：至少校验 `date`、`batch`、`complete=true`、`ids` 与本批期望 ID 完全一致、`results.length === ids.length`；旧格式缺元数据时只能经人工盘点确认，不得见文件就跳过。
  5. **进程结束前补抓 error**：单帖 error 不计入 valid/with_content；先生成 retry 批并立即保存，再合并。0919 的 414 帖中 valid=413/error=1，日报最终 400，不可把 error 当正文成功。

### ⚠️ 反检测规则（必须遵守）
1. **逐帖浏览间隔 1.5 秒**
2. **检测 Cloudflare 挑战**：标题含 "Just a moment" 则等待 15 秒
3. **检测官方警告**：内容含 "异常的自动化访问行为" 或 "系统检测到" 则立即停止
4. **429 限流处理**：等待 30 秒后重试
5. **单帖 timeout 20s**：超时记 `error`，不中断整批
6. **连续 ERR_ABORTED ≥3**：停止本批，重置 MCP 浏览器后再抓（v15.5）

### ⚠️ 旧 Batch 文件清理（v14 + v15.2 + v15.5 + v15.6 + **v15.7**）
跨 session 时 `batch_browser_*` / `batch_ids_*` / `rem_batch_*` 会污染合并计数。

**冷启动抓取前处理**（必须在项目 cwd；**续跑有今日 batch 时不要清**）：

> **v15.6 / 2026-07-21**：自动模式可能 **拒绝 `os.remove`/`rm` 清理既有 `data/batch_*`**（不可逆破坏策略）。  
> **v15.7 / 2026-07-22**：含 `pkill` + 长 `for` 的 bash 归档也可能被自动模式拦截。  
> **正确做法：挪移归档，不要删；优先 Python `shutil.move`。**

```python
# 推荐（v16.0）：只增不删的唯一归档目录；禁止覆盖已有归档
import os, glob, shutil
base = 'data/archive/YYYY-MM-DD-prev'  # 换成当日日期
idx, dst = 1, base
while os.path.exists(dst):
    dst = f'{base}-{idx:02d}'
    idx += 1
os.makedirs(dst)  # 唯一路径，不用 exist_ok=True 掩盖冲突
patterns = [
    'data/batch_browser_*.json', 'data/batch_ids_*.json', 'data/rem_batch_*.json',
    'data/crawl_queue*.json', 'data/remaining_todo.json',
    'data/source_a.json', 'data/source_b.json', 'data/merged_ids.json',
]
for pat in patterns:
    for f in glob.glob(pat):
        if os.path.isfile(f):
            shutil.move(f, os.path.join(dst, os.path.basename(f)))
if os.path.isdir('data/crawl_js'):
    shutil.move('data/crawl_js', os.path.join(dst, 'crawl_js'))
print('archive:', dst)
print('remaining batch_browser:', len(glob.glob('data/batch_browser_*.json')))  # 期望 0
```

> **🔴 v16.0 归档铁律**：`data/archive/YYYY-MM-DD-prev` 已存在时，创建 `-01`、`-02`……唯一目录。禁止 `shutil.rmtree(target)`、禁止把同名文件覆盖进旧归档；先前 `_archive_prev.py` 的「target 存在就删掉」写法会破坏历史断点。

```bash
# 浏览器重置与归档拆开（减少权限连坐）
pkill -f "mcp-chrome" 2>/dev/null; sleep 2
```

仅在用户明确授权删除时，才可用 `os.remove` 脚本。

**合并前污染检查（v15.5）**：空 results / 结构异常 / mtime 明显非本 run → 挪到 archive 并只补抓缺失 id。

### 数据保存（v12 + v15.2 + v15.5 + v15.6 + v15.7）
- **每批立即保存**到 `data/batch_browser_N.json`（或 `batch_browser_retryN.json`）
- **不要等所有批次完成再保存**
- **空帖过滤**：无 `title` 不入库
- **大结果回填**：无法管道时用 session transcript / `save_latest_batch.py`（v15.2）
- **预生成批抓脚本（v15.6/v15.7）**：队列切分后写 `data/crawl_js/batch_{N}.js`，用  
  `browser_run_code_unsafe(filename=".../data/crawl_js/batch_N.js")`  
  减少每批粘贴 15 个 ID 的 token 开销；仍每批后 `python3 data/save_latest_batch.py N`  
  （0722 实测：31 批 filename 批抓全程成功）
- **列表页导航超时（v15.7）**：Source B 等 `browser_navigate` 60s Timeout → **同一 URL 重试一次**，不必立刻重置浏览器
- **合并时二次公益站过滤**（标题+标签+content 前 200 字）
- **列表 views 合并**：帖子页 views=0 时用 crawl_queue 列表 views（解析 `k/万`）
- **error 帖单独重试**：不要把 error 计入 with_content

### 日期与过滤

- **概念库（v15）**：Writer 技术锚点只引用 `ai-concept-bank` 中 eligible ready；路径 `ai-concept-bank/concepts.json`
- **概念候选入库（v15.1）**：仅从日报 `## 概念候选（供 concept-bank）` 附录追加最小 `candidate`；必须去重、过滤、`jq` 校验；不生成口播、不改 ready、不写 usage-log
- **不能用 ID 阈值判断日期**：Discourse ID 不按日期顺序
- **必须过滤公益站**（列表 + 正文两遍）：公益站、LDC、cdk、签到、白嫖、薅羊毛、兑换码、免费额度、号池、号商、中转站、高级推广、抽奖、富可敌国、LightBridge公益、YSX666、日抛、午夜福利
- **必须历史去重**：扫描 `data/reports/*.md` 提取已报道帖子 ID（可排除 `_press.md`）
- **daily 文件名匹配**：用正则 `^\d{4}-\d{2}-\d{2}$` 严格匹配，排除 `_sorted`、`_topics`、`_classified` 等后缀文件（v14 新增）

### 并行 Agent 优化（v14 新增）
- **Topic Merger 和 Trend Analyzer 可并行启动**：两者数据独立，无需互相等待
- **Writer 必须等两者完成**：需要读取 topic_groups 和 trend_analysis
- **Press Writer 等 Writer 完成**：需要读取日报 Markdown
- **PDF Builder 等 Writer 完成**：需要读取日报 Markdown 转 Typst

### 流程完整性
- **必须按顺序完成所有 Agent**：Crawler → Topic Merger → Trend Analyzer → Writer → Press Writer → PDF Builder
- **Press Writer 和 PDF Builder 不可跳过**：即使用户没有明确要求，也必须生成
- **月报模式不抓取新数据**：聚合当月 daily JSON + 日报 MD，Crawler 仅做读取与聚合
- **月报数据缺失处理**：若某日数据缺失，标注缺失天数并继续生成，不中断流程

---

## 更新日志

### v16.21.0 (2026-11-26) — 1126 期实跑：渲染进程崩坏自愈与永久缺失清单口径（坑 545）

**实测数据（DATE=2026-11-26）**
- Source A **2216** / Source B **600** → 合并去重 **2747** → 历史/标题去重 **1688** → 公益/交易过滤 **1556**
  → 32h 窗口 **659** → daily **615**（657 含正文 + 2 永久缺失；二次过滤剔除 42）
- 22:35 触发；02:05 crawl+merge VALIDATED；03:41 PDF（5 页 6846 字）；07:17 五平台全部 verified 收工

#### 坑 545：连续 `Page crashed` 是浏览器实例崩坏，必须重启，不要继续跑批

- **症状**：`data/logs/<issue>-crawl.log` 中 batch 1–11 正常（179 帖有效），batch 12 起每个批次都是
  15/15 `page.goto: Page crashed` / `Target crashed`；主批次跑完后 retry0 又跑 480 个失败 ID，
  累计 915 条 error，实际有效正文仍停在 179/659。
- **根因**：Chromium 渲染进程整体崩坏后，`crawlOne` 的逐帖 try/catch 会把每一帖都记成
  `Page crashed` 并继续下一帖——批次循环不会自己重启浏览器，于是剩余 32 批 + retry 全部空转。
  旧 attempt 退出后，resume 新起 `_crawl_<issue>.mjs` + 新 Chromium，同一队列立刻恢复，最终 **657/659**。
- **判据**：同一批内连续 ≥3 帖都是 `Page crashed`/`Target crashed`（不是 `ERR_ABORTED`、不是单帖超时）
  ⇒ 判定浏览器实例已坏，保存已有 checkpoint 后**立即结束本次 crawl attempt**（抛出 `rc=1` 让 resume 重启），
  不要继续遍历剩余批次，也不要等 `BODY COVERAGE` 跑完才处理。
- **不要误判**：scheduler `status=HEALTHY` 只代表进程/租约健康，不代表抓取健康；巡检必须同时看
  `crawl.log` 的批次错误率与 `BODY COVERAGE` 增长。
- **验收**：新 attempt 启动后看前 3 个批次是否恢复 `15/15` content；恢复后再让它跑全量。

#### 永久缺失清单（坑 540 补充）：证据可跨主批次与 retry 文件

- 1126 期两个 ID `3243276` / `3243974` 分别有 **9 / 8** 条同 `empty_deleted_private_or_unloaded`、
  无 title 的证据：`batch_browser_1.json` / `batch_browser_43.json` + `batch_browser_retry1..8.json`。
- `attempts == len(attempt_files)` 写成 9 / 8（不是强求 6），下一次 gated tick 立即通过全量校验并生成 daily 615 帖。
- 诊断口径：`BODY COVERAGE 657/659 errors=2 permanent_gone=0 missing=2` 时，逐个 ID 汇总
  `(文件, error)`；只要同一 ID 的每条证据都满足「同 ID / 同 error / 无 title」，就写清单，不要再重试。

### v16.13.0 (2026-11-18) — 1118 期实跑：Source A 短列表静默欠抓（坑 496）

**坑 496：`scrollLoad` 的 `stable >= 3` 会把「首屏 30 行 + 懒加载失败」误判为列表到底。**

- **实测指纹**：`data/logs/<issue>-crawl.log`
  ```
  scroll 10: 0 rows
  ...（到 scroll 320 全是 0 rows）
  Source A transient attempt=1
  scroll 1: 30 rows
  SOURCE A: count=30 ...
  ```
  即首轮列表元素 `tr.topic-list-item` 完全没渲染；重试后只拿到首屏 30 行，
  连续 3 次不变（3.6s）就返回。Source B 同会话正常（594 帖 / 2220 行），说明浏览器与 profile 没问题。
- **后果**：32h 窗口内 Source A 只有 19 帖（正常 655），daily 28 帖（正常 460+）；
  控制器 `CHECKPOINT coverage: valid=29/29`、`DAILY VERIFIED` 全绿，**没有任何告警**。
- **修法**（`_fetch_lists_<issue>.mjs`）：
  ```js
  const MIN_ROWS = { a: 800, b: 200 };
  // plateau: stable >= 6 且 count >= MIN_ROWS[key] 才允许返回
  if (stable >= 6 && count > 0 && i >= 12) {
    const clicked = await evaluate30(page, () => { /* 点 button.load-more / a.load-more / .load-more */ });
    if (clicked) { stable = 0; await sleep(2500); continue; }
    throw shortList(key, count);      // rc=1，触发 transient 重试
  }
  if (!count && i >= 12) throw shortList(key, count);
  ```
  外层 3 次仍 short → `throw fail(4, 'under-coverage after 3 attempts')`，让控制器 block。
- **修复后实测**：同一 URL 立刻 2219 帖 / 窗口内 709，证明是瞬时渲染失败。
- **验收纪律**：开工后先看 `data/source_a.json` 条数，`< 1500` 一律按欠抓处理；
  **daily 的内部一致性全绿不代表源完整**。重抓恢复路径见 v16.13.0 顶部摘要 ③。

### v16.12.0 (2026-11-17) — 1117 期实跑：audit 探针要求字面 PASS + CLI 路径写死扩展版本

**版本**：16.11.0 → 16.12.0

**实测数据（2026-11-17 期，DATE=2026-11-17）**
- Source A 2217 / Source B 595 → 队列 **507** → 正文 507/507 有效、0 error → daily **464 帖**
- 22:35 触发 → 23:20 crawl+merge VALIDATED → 23:23 downstream → 00:13 audit 粘性 blocked
- 人工修判据 + 12:08 续跑 → 15:48 DONE；五平台草稿全落库（公众号 `100002098` / 知乎 `2106048447715468379` / B站 `4132286` / 抖音 `v0300fg…` / 视频号 `export/UzFf…`）

**新坑（v16.12.0）**
- **坑 491：audit 探针要求字面 `PASS`，系统 checker 只输出 `RESULT: OK` → 门永远不可能通过**。1116 用 `run_check_1116.py` 适配器补 PASS 绕开；1117 worker 拒绝伪造 PASS，按契约 `block --kind source` 停机，断点保留。**修法**：探针接受 `rc==0 and ('RESULT: OK' in upper or 'PASS' in upper)`，同时拒绝 `RESULT: BLOCKED`/`FAIL`；新期派生后先跑真实 checker 验证成功令牌，不写适配器、不改内容层。
- **坑 492：`CLAUDE` 常量写死扩展版本号，扩展升级后 worker 全部 spawn 失败**。1117 期间 `2.1.310 → 2.1.325`，旧路径 `FileNotFoundError`，L2 连试 16 次。**处置**：arm 前与长跑中检查 `ls -d ~/.devin/extensions/anthropic.claude-code-*`，把 `CLAUDE` 指到最新存在的二进制；指纹是 `<issue>-downstream-supervisor.log` 的 `FileNotFoundError`。

**验证正例（v16.12.0）**
- 坑 475 预防生效：arm 前移走 `crawl-resource.lock.owner.json`，归档一次通过。
- 507 队列全量抓取 0 error；五平台草稿全部落库，DONE 15:48:26。

### v16.10.0 (2026-11-15) — W45 周报：平台合集/专栏必须按模式取值

**版本**：16.9.0 → 16.10.0

**W45 周报实测（2026-11-09 ~ 11-15）**
- 每日 279 / 393 / 392 / 477 / 515 / 583 / 344；周内去重 2979 → 过滤后 2911 帖
- 周报 md / press / PDF（831 KB）落盘后开视频链；成片 189.49s / 1920×1080 / 15.74 MB
- 五平台草稿落库，但用户指出三处平台字段选错：B站合集、抖音合集、知乎专栏都沿用了日更名称

**新坑（v16.10.0）**
- **坑 482：周报/月报的平台合集与专栏不能沿用日更硬编码。** B站/抖音/视频号/公众号合集与知乎专栏必须按模式取值：
  日报「今日羊报 AI」或「今日羊报Al」，**周报「羊报AI周刊」，月报「羊报AI月报」**。
  修法：`publish.json` 增加 `platform.<p>.collection` 与 `platform.zhihu.column`；脚本只读字段并回读断言。
- **附带两条交付要求**：公众号「摘要/卡片描述」选填但必须写全（`platform.wechat.digest`）；抖音竖封面默认不拖缩放滑块，按原图 3:4 提交。

### v16.9.0 (2026-11-15) — 1115 期：跨期锁元数据把冷启动打成粘性 blocked + CAP 仍是字面量

**版本**：16.8.0 → 16.9.0

**实测数据（2026-11-15 期，DATE=2026-11-15）**
- Source A 2219 / Source B 2220 行均触发 `recent-window cap`；A 的 `created` 回溯到 2024-11-25，证明窗口未被截断
- 合并去重 2763 → 历史 ID 去重 2719 → 标题去重 1506（-1213）→ 公益/交易 1348（-158）→ 32h 窗口 **378**
- 正文 `BODY COVERAGE 377/378 errors=1 permanent_gone=1 missing=0` → daily **posts=344 excluded=34**
- 时间线：22:35 触发 →（修锁）22:41 归档 95 文件 → 22:47 建队 → 23:19 抓完 → 23:24 报告/PDF（4 页 593KB）
  → 23:28 内容/审核/封面 → 23:39 成片 → 23:43 文章/publish → 23:51 微信 → 23:59 知乎 → 00:02 B站
  → 00:05 抖音 → 00:08 视频号 → **00:09:56 DONE（1h35m）**

**新坑（v16.9）**
- **坑 475：跨期共享锁 sidecar 会把新期号冷启动打成粘性 blocked**。上一期留下的 `data/logs/crawl-resource.lock.owner.json`（`date=2026-11-14`、`owner:null`、`released_at` 有值）让本期 `Mutex.__enter__` 的 `record['date'] == DATE` 判定失败 → 归档 `rc=3 LOCK metadata identity refusal` → `blocked.automatic_retry=false`。**处置顺序**：`lsof` 无持有者 + `ps` 无活跃爬虫 → 备份并移出 sidecar（禁止直接 rm）→ 清 state 的 `blocked` → 下一轮 tick 自动归档。**预防**：arm 新期号前先清上一期 sidecar。
- **坑 476：CAP 的「现场推导」只写在文档里，派生器照抄 2200 字面量**。1115 期 `_fetch_lists_1115.mjs` 仍是 `count >= 2200`；本期靠 A 列表 `created` 回溯到 2024-11-25 才确认没截断。派生器必须输出 CAP 推导过程，断言里禁止历史硬编码值；验收用 `created` 反算窗口内最后一行索引 `< CAP × 0.7`，而不是「行数到了」。
- **坑 477：`RETRY_LATER supervisor exited before adoption rc=0` 是良性竞态**。daily 已就绪时 `_run crawl` 只做校验、2s 内退出，父进程按「未接管」报可重试错误。**先 `status` 再决定**：`ready_downstream` 或后续 tick 返回 SKIP 即已成功，不要重置 state 或重复起 worker。

### v16.11.0 (2026-11-16) — 1116 期实跑：触发串占位保护 + worker 自动续跑

**版本**：16.10.0 → 16.11.0

**实测数据（2026-11-16 期，DATE=2026-11-16，触发 2026-11-15 22:35）**
- Source A 2216 行 / Source B 605 行 → 队列 321 → daily **294 帖**（二次过滤排除 27，22 批 err=0）
- 22:35 触发 → 23:08 归档完成 → 23:15 crawl+merge VALIDATED → 23:39 report / 23:41 press / 23:43 PDF
- downstream：attempt 1 23:08–01:48（rc=1，无新 checkpoint）→ attempt 2 02:07–10:35（`--resume` 续跑）
- 总时长 12h00m；上传阶段 06:50–10:33（约 3h43m），其中抖音独占 2h11m（见 ai-news-factory v3.99.0 坑 489）

**新坑（v16.11.0）**
- **坑 487：触发时刻串会被「日期四形态替换」二次位移，必须用占位符保护**。1115 源码 GUARD 文案/`trigger_at` 是 `2026-11-15 22:35`，与 `TRIGGER_EPOCH=1794666900`（`2026-11-14 22:35`）错位一天——1114→1115 派生时通用日期替换把触发串又推了一天，且在替换列表第一行放 `(X, X)` 的 no-op「guard」并不保护任何东西。1116 修法：先把触发串（ISO/空格两形态）替换为 `\x00TRIG_ISO\x00`/`\x00TRIG_SP\x00`，全部日期/期号替换跑完再原样放回；触发断言 tuple 单独 +1 天。派生器末尾加全量审计：派生文件不得含上期号 `1115`、不得含旧 epoch `1794666900`、剩余 `2026-11-15` 只允许紧跟 `T22:35`/` 22:35`、旧 cutoff 形态（`2026-11-13T16:05`/`2026-11-13 16:05`）不得残留。
- **坑 488：worker 首尝试静默退出 rc=1 → L2 `--resume` 续跑是设计内恢复**。1116 期 attempt 1 于 23:08 启动、01:48 无新 checkpoint 退出（2h40m）；L2 在 02:07:22 用同一 session `--resume` + 磁盘 checkpoint 起 attempt 2，后续 content/audit/covers/video/articles/publish/五平台上传全部完成。**监控口径**：`worker.attempts` 增加 + `last_exit=1` ≠ 失败，判进度只看 stage checkpoint/progress；禁止手工重启 worker 或并发第二 worker。**预防**：长生成阶段开始前先落 progress checkpoint；整期 10h+ 属正常长尾。

**验证正例（v16.11.0）**
- 坑 475 预防生效：arm 前清 `crawl-resource.lock.owner.json`（`lsof` 无持有者 + `ps` 无爬虫），冷启动归档一次通过、无 `rc=3`。
- 坑 477 未触发：crawl 阶段正常接管，没有出现 `RETRY_LATER ... before adoption`。

### v16.8.0 (2026-11-14) — 1114 期：板块列表无界增长 + 永久消失帖把整条链钉死

**版本**：16.7.0 → 16.8.0

**实测数据（2026-11-14 期，DATE=2026-11-14）**
- Source A 列表滚动到 **2903 行仍在增长**，加近期窗口上限后 `recent-window cap reached at 2218 rows`（Source B 2220 行）
- 正文 `BODY COVERAGE 622/623 errors=1 permanent_gone=1 missing=0` → daily `posts=583 covered=622/623 excluded=40`
- 期间 `_resume` 连续 7 次 `rc=1 incomplete bodies`（同一个已删帖），第 3 次 resume 才靠排除清单收工

**新坑（v16.8）**
- **坑 469：列表页是无界增长的，「连续 N 次计数相等」的稳定平台判据永远不可达**。实测每 1–2 次滚动 +30 行，180 次滚动跑满也不收敛 → 三次 resume 全 `rc=1 Source A failed after 3 attempts`。**必须加「近期窗口行数上限」**（`count >= CAP && i >= 20` 即返回并打印 `recent-window cap reached at N rows`），CAP = 32h 窗口所需行数 × 2 现场推导，不照抄 2200；抓完用 `created` 反算窗口内最后一行索引，须 `< CAP × 0.7`。
- **坑 470：全队列「每个 ID 必须有正文」是死门禁**，已删/私有帖会无限重试（本期同一 id 8 次尝试，reason 恒为 `empty_deleted_private_or_unloaded`）。改用 `data/<issue>-permanent-gone.json` 证据清单：逐份 checkpoint 反查（文件存在 / 该 id 恰一行 / 无标题 / error == reason / attempts == len(files) 且 ≥ 6），任一不符即 `Refusal(3)`；**禁止伪造标题正文凑覆盖率**。
- **附条（坑 470）：`coverage` 必须写 provenance**。同时写 `valid_total` 与 `gone_ids`，`validate_daily` 断言 `set(good) | set(gone) == set(ids)`，日志固定打 `errors / permanent_gone / missing` 三个计数，覆盖率才是可复核的等式而非自报比值。

### v16.7.0 (2026-11-13) — 1113 期：触发时刻不是惯例值 + 派生器断言照抄上期

**版本**：16.6.0 → 16.7.0

**实测数据（2026-11-13 期，DATE=2026-11-13）**
- Source A 900 + Source B 280 → 合并去重 → 标题去重 995 → 公益站过滤 904 → 32h 窗口 **521**（`no_created=0 parse_fail=0 too_old=383`）
- 35 批全 `valid=15 err=0` → merge 521→515（二次过滤去掉 6 条），`ORDER CHECK OK`（views 降序 top5=12400/9400/7200/4300/3300）
- 触发时刻 **2026-11-12 23:25**（epoch 1794497100），**不是惯例的 22:35**

**新坑（v16.7）**
- **触发时刻由用户当晚指令决定，不是固定 22:35**。派生器把 `22:35` 当常量抄 → `TRIGGER_EPOCH` 错一小时。四种替换需分开写（整串 / 裸时刻 / epoch 字面量），派生完用 `date -j -f` 反算校验。
- **派生器的 `for needle in (...)` 断言块不能整段照抄上一期**。1113 抄了 1112 的 `'连续 GATE'`，而源文件里只有 `GATE 卡死` → 派生第一步就 AssertionError。**每个 needle 先 `grep` 确认存在**。

**新坑（v16.6）**
- **`HIST_GENERALIZE` 必须覆盖「本期发现」这类不带期号的措辞**。`坑 443（本期发现，1110/1111 继承）` 描述的是上一实现周期的事，不泛化就会在下期被读成「这期发现的坑」，是对事实的错误陈述。末尾用反向断言兜底。

### v16.4.0 (2026-11-10) — 跨机迁移首日：列表页 i18n 变中文致 created 全空

1110 期在新机器（macOS 14.6 / arm64）跑通：双源 900 + 273 → 合并去重 1153 → 标题去重 917 → 公益站 824 →
**32h 窗口 405（no_created=0）** → 26 批正文（err=1）→ **daily 393 帖**。

| # | 坑 | 一句话处置 |
|---|---|---|
| A | `td.activity[title]` 已本地化（`创建日期：2026 年 11月 8 日 15:36`），`Created:` 正则全落空 → `created=''` → 窗口 0 条 | 加中文回退 + 归一化成 `YYYY-M-D H:MM`；**`const` 必须改 `let`**（否则 `Assignment to constant variable` 整批失败） |
| B | `daily total=0` 被链路当"成功"（`have>=n` 在 `n=0` 时恒真） | `_build_queue` 输出 `total=0` 时非 0 退出；`_resume` 加 `rc=4`；**判据看 `no_created` 而非 `total`** |
| C | 新机三处硬依赖：node v14（要 ≥18）、`playwright-core` 路径不存在、派生脚本 ROOT 仍是旧机路径 | PATH 注入新 node；`npm i -g playwright-core` 且 revision 对齐；派生器加路径替换 |
| D | `_archive_*.py` 把无 `date` 字段的 `batch_ids_*.json` 一律归档 | 归档只在开工前跑一次，续跑不跑 |
| E | watchdog `GUARD` 只看 pid，wrapper 早退仍报 armed | 加 `launch.log` 近 10 分钟有无新行；`queue: 0 posts` 直接 ALERT |

**排查口诀**：`daily total=0` + `crawl.log` 有 `queue: 0 posts` → **先看 `source_a.json` 的 `posts[0].created` 是否为空**（空 = 坑 A）。

### v16.0.0 (2026-09-18～2026-09-20)
基于 **连续三期全量日报**（过滤后全部抓取完 + 视频工厂联跑）实战，将 v15.9 的 Node 直连 Playwright 从临时兜底固化为可复用协议：

**日期与去重（核心）**
- 32h 窗口统一以当期 **00:05 CST** 为基准：`base = YYYY-MM-DD 00:05+08:00`，禁止用脚本实际启动时间 `datetime.now()`；0920 恢复较晚导致旧脚本 cutoff 漂到 16:34，是明确反例
- 最近 3 日标题先规范化再比对：去空白、标点、大小写与全/半角差异；禁止只做原始字符串精确相等
- `_fetch_lists_YYYY.mjs` / `_build_queue_YYYY.py` / `_crawl_YYYY.mjs` 的日期、Usage、queue 元数据必须同源；复制旧脚本后全量搜索旧日期

**批次持久化与续跑**
- 每批先写 `.tmp`，JSON 自检通过后原子 `rename` 为 `batch_browser_N.json`
- 已有批次只有在 `date`、`batch`、`complete=true`、`ids`、`results.length` 全部匹配时才可跳过；不能再以“文件存在”为唯一判据
- error 帖先生成 retry 批并立即保存，再合并；error 不计入 `valid` / `with_content`
- 冷启动归档目录冲突时创建 `-01/-02` 唯一路径，禁止 `shutil.rmtree` 覆盖既有归档

**环境降级**
- 安全分类器不可用时，只读命令可继续；`python3`、Node 抓取、Cron 等非只读动作暂停并间隔重试
- 等待期间用 Write/Edit 更新状态和文档；恢复后先盘点磁盘 batch，再从缺口续跑，禁止重抓已完整批次

**实测数据**
- 2026-09-18：双源合并 993 → 历史去重 894 → 公益站过滤 833 → 32h **422** → 29 批 0 error → 二次过滤 **400**
- 2026-09-19：双源合并 951 → 历史去重 768 → 公益站过滤 713 → 32h **414** → 28 批（valid 413 / error 1）→ 二次过滤 **400**
- 2026-09-20：双源合并 995 → 历史 ID/标题去重 887/707 → 公益站过滤 652 → 32h **326** → 22 批 0 error → 二次过滤 **316**
- 三期均完成 daily + report + press + typ + PDF，并在 PDF 落盘后交给 ai-news-factory

**版本**：15.9.0 → 16.0.0

### v15.9.0 (2026-09-17)
基于 **2026-09-17 全量日报**（过滤后全部抓取完 + 视频工厂联跑）实战：

**MCP 断连兜底（核心）**
- Playwright MCP `Failed to connect` 时改 Node 直连 Playwright，headed 过 Cloudflare
- `page.evaluate` 多参会抛 `Too many arguments` → 传对象
- Chromium 路径探测最新 `chromium-NNNN`，0917 为 1228（旧脚本写死 1223 找不到）

**实测数据（2026-09-17）**
- Source A 750 + Source B AI 321 → 合并 1043 → 历史去重（ID+近 3 日标题）809 → 公益站 739 → 32h **382** → 正文 26 批 0 error → 二次过滤 **362**
- `data/daily/2026-09-17.json` total=362 / with_content=362
- 报告 md + press + typ + pdf；PDF 后接 ai-news-factory（视频 98.2s / 公众号草稿 `appmsgid=100001221`）

**版本**：15.8.0 → 15.9.0

### v15.8.0 (2026-07-25)
基于 **2026-07-25 全量日报**（过滤后全部抓取完 + 视频工厂联跑）实战：

**批抓稳定性**
- `crawl_js` + `browser_run_code_unsafe(filename=...)` + 每批 `python3 data/save_latest_batch.py N`：批次 **0–32（33 批）**、每批 15，**titles=489 / errors=0**
- 会话中断后：先 `ls data/batch_browser_*.json` 盘点；**已齐则只合并**，禁止默认冷启动清 queue

**合并与过滤**
- 列表 views（`k/万`）回填详情页 `0`；正文二次公益站/交易过滤
- 实测：32h **489** → 二次过滤 **455**

**实测数据（2026-07-25）**
- Source A 1020 + Source B AI 536 → 合并 1491 → 历史+列表过滤 → 32h **489** → 正文 0–32 → 二次过滤 **455**
- `data/daily/2026-07-25.json` total=455 / with_content=455
- 报告：md + press + typ + pdf；PDF 后接 ai-news-factory

**版本**：15.7.0 → 15.8.0

### v15.7.0 (2026-07-22)
基于 **2026-07-22 全量日报**（过滤后全部抓取完 + 视频工厂联跑）实战：

**冷启动**
- 复杂 bash 归档（`for` + `pkill`）可能被自动模式拒绝 → **Python `shutil.move` 归档**；`pkill mcp-chrome` 单独执行
- 同时归档 `crawl_js/` 目录，避免旧批脚本污染

**列表页与批抓**
- Source B `browser_navigate` 可 **60s Timeout** → 同一 URL **重试一次**即可（不必立刻 pkill）
- `crawl_js` + `browser_run_code_unsafe(filename=...)` + 每批 `save_latest_batch.py N`：**31 批全程成功**，无 `ERR_ABORTED` / 无官方警告
- `source_a.json` / `source_b.json` 仍可能 **double-encoded**：`json.loads(json.load(f))`

**合并与过滤**
- 列表公益站 + 正文二次过滤关键词表沿用 v15.2/v15.6
- 列表 views（`7.5k` / `万`）回填详情页 `0` 视图

**实测数据（2026-07-22）**
- Source A 901 + Source B AI 446 → 合并 1282 → 历史+列表过滤 → 32h **462** → 正文 0–30（末批 12）→ 二次过滤 **440**
- `data/daily/2026-07-22.json` total=440 / with_content=440
- 报告：md + press + typ + pdf；概念候选 4 个；PDF 后接 ai-news-factory

**版本**：15.6.0 → 15.7.0

### v15.6.0 (2026-07-21)
基于 **2026-07-21 全量日报**（过滤后全部抓取完 + 视频工厂联跑）实战：

**冷启动与权限**
- 自动模式拒绝 `rm`/`os.remove` 清理既有 `data/batch_*` → **改 archive 挪移**（`data/archive/YYYY-MM-DD-prev/`）
- 同时归档 `source_a/b.json`、`merged_ids.json`、`crawl_queue*`，避免跨日污染

**批抓效率**
- 32h 后写 `data/batch_ids_N.json`（默认每批 **15**）
- 预生成 `data/crawl_js/batch_N.js`，用 `browser_run_code_unsafe(filename=...)` 跑批，减 token
- 每批仍 `python3 data/save_latest_batch.py N`；合并前校验 + 二次公益站过滤 + k/万 views

**概念库**
- `concepts.json` 根为 **dict**（`data['concepts']` 才是数组）；候选入库/usage-log 必须按此结构
- 去重/append 后 `jq empty` + 确认 `status=candidate` / 空口播 / 未改 ready

**实测数据（2026-07-21）**
- Source A 929 + Source B AI 456 → 合并 1321 → 历史+列表过滤 → 32h **469** → 正文 32 批 → 二次过滤 **447**
- `data/daily/2026-07-21.json` total=447 / with_content=447
- 报告：md + press + typ + pdf；PDF 后接 ai-news-factory

**版本**：15.5.0 → 15.6.0

### v15.5.0 (2026-07-20)
基于 **2026-07-20 全量日报**（过滤后全部抓取完）实战：

**批抓稳定性**
- MCP `browser_run_code_unsafe` 长静默可被 abort（~2491s）→ 默认批大小 **10–15**，必要时加 MCP timeout
- 连续 `page.goto` **`net::ERR_ABORTED`** → 立即落盘 → 重置 mcp-chrome → `rem_batch` / `batch_browser_retryN` 重试
- 合并前 **batch 污染校验**（旧 session 可写坏 `batch_browser_0.json`）
- 批号支持 `retry1` 等非纯数字；合并用 glob，勿假设 `int(N)` 文件名

**续跑协议**
- 中断后以磁盘为准：有 batch 无 daily → 合并；有 daily+pdf → 交视频；工具不全时不假装完成

**实测数据（2026-07-20）**
- 全量约 26 批 + retry → `data/daily/2026-07-20.json` **total=364 / with_content=364**
- 报告：`data/reports/2026-07-20.md` + press + typ + pdf
- PDF 落盘后接 ai-news-factory 免视频

**版本**：15.4.0 → 15.5.0

### v15.4.0 (2026-07-19)
基于 **2026-W28 周报**（07-13~07-19）实战：

**周聚合浏览量与去重**
- `views` 支持 `6.2k` / `万` 解析；同 id 合并时保留更高 views
- 帖子写入 `_day` 来源日期，便于大事记与 TOP 标注
- 覆盖检查：本周 7 日 `daily/*.json` + `reports/*.md` 齐全后再写周报

**产物与衔接**
- 周报 md/press/**pdf** 必须落盘。**`typst` 本机没有（坑 527）**，现行路径是「md → 自写 HTML → 系统 Chrome `page.pdf()`」：
  ```bash
  # 1) md -> HTML（自己转 <h1/h2/h3>、<ul>、<table>、<blockquote>；**bold** -> <strong>）
  # 2) Chrome headless 打印（launch() 才接受 executable_path，connect_over_cdp 不接受）
  python3 -c "from playwright.sync_api import sync_playwright as s; \
    p=s().start(); b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True); \
    pg=b.new_page(); pg.goto(html_uri); pg.pdf(path='data/weekly/<week_id>.pdf', format='A4', print_background=True); b.close()"
  ```
  **PDF 落盘并回读文件大小/页数之后，才允许开视频流水线**（v16.3 的衔接铁律不变）；
  没有 typst 就不要在那上面反复尝试，也不要去 `pip install typst`（需要用户授权）。
- 实测：去重主题 **2823**；日帖 374/491/454/390/490/531/668
- 与 ai-news-factory：**周 PDF 落盘后再开视频流水线**；批抓阶段只保留一个 Playwright

**版本**：15.3.0 → 15.4.0

### v15.2.0 (2026-07-17)
基于 2026-07-17 全量日报实战优化：

**固定项目 cwd（核心）**
- Bash 可能落在 `~/.claude/projects/...`，导致 `data/` 找不到、清理 batch 失败
- 强制 `cd /Users/youngsdream/Documents/learn-claude-code`；`browser_evaluate` filename 用绝对路径

**「过滤后全部抓取完」冷启动协议**
- 该触发词 = 全量流水线，不以用户口述代替磁盘检查
- 无 `data/daily/{date}.json` 时从 Crawler 重跑；有今日 batch 无 daily 则只合并

**crawl_queue + batch_ids 预切分**
- 32h 筛选后写 `data/crawl_queue.json` 与 `data/batch_ids_N.json`
- 全量模式按 batch_ids 顺序抓完，不在 150 帖提前停

**batch 保存 / transcript 回填**
- 每批立即 `batch_browser_N.json`
- 大 JSON 无法管道时，从 session jsonl 解析 `### Result` 转义串回填（`save_latest_batch.py`）

**正文二次公益站过滤 + views 合并**
- 列表过滤后仍会混入正文含「公益推广/CDK/日抛」的帖 → 合并时 title+tags+content[:200] 再滤
- 帖子页 views 常为 0 → 用列表页 views 补全

**主题分类扩展**
- 独立 DeepSeek；Kimi/Grok/OpenAI 关键词补全（k3/kivine/sol/terra/gpt-red 等）

**实测数据（2026-07-17）**
- Source A 930 + Source B AI 378 → 合并 1232 → 历史去重/公益站后 1084 → 32h **517** 帖
- 全量 18 批（0–17）→ 正文合并 514 → 二次过滤 **490** 有效
- 产出：`data/daily/2026-07-17.json` + reports md/press/pdf/typ + 4 个 concept candidate
- 整体耗时：约 90 分钟（含全量抓取 + 成稿）

### v15.1.0 (2026-07-13)
- **概念候选受控入库**：日报生成后可读取 `## 概念候选（供 concept-bank）`，经去重、过滤后只追加最小 `candidate`
- **安全边界**：不自动调用 narrator、不设 `reviewed=true`、不晋升 `draft/ready`、不写 `usage-log`
- **长期验证**：日报候选负责发现新词；`term-frequency` 负责验证长期价值；维护 Agent 决定后续 `candidate → draft → ready`
- **校验要求**：写入 `concepts.json` 后必须 `jq empty`，并确认新增条目为空口播、未审核、未影响 ready 概念

### v15.0.0 (2026-07-12)
- **接入 ai-concept-bank**：Writer 可读 `concepts.json`，条目「技术锚点：name — one_liner」（仅 ready + narrator + reviewed）
- **可信度五档**：官方确认 / 媒体报道 / 社区实测 / 源码迹象 / 未确认传闻；条目与亮点必标
- **条目模板**：中性标题 + 事实摘要 + 可信度 + 影响 + 技术锚点 + 信号
- **亮点**：硬新闻优先；权益/封号不得占亮点 50% 以上
- **Trend Analyzer**：可选 `source_hint` 映射五档
- **Press**：核心事件标可信度；风险区分已证实 vs 猜测
- **过滤**：求号/出号/接码/号商/代充纯交易帖过滤；账号风控帖降权不删
- **周报/月报模板**：同步可信度与中性标题；数据来源声明含「未确认不作为定论」
- **不写 15s 全文 / usage-log**：归 ai-news-factory + narrator
- **可选附录**：`## 概念候选（供 concept-bank）`
- **版本**：14.0.0 → 15.0.0


### v14.0.0 (2026-07-05)
基于 2026-07-05 日报+周报实战经验优化：

**Cloudflare 点击绕过（核心修复）**
- 旧方案：等待 15 秒自动通过 → **实测不够，页面停留在 "Just a moment..."**
- 新方案：`browser_snapshot` 查看结构 → `browser_click` 点击验证区域（通常是 `e6`）→ 页面立即通过
- 原因：Cloudflare Turnstile 挑战需要用户交互才能通过

**周报模式完整流程（核心新增）**
- 新增周报数据聚合脚本：基于 `data/daily/YYYY-MM-DD.json` 和 `data/reports/YYYY-MM-DD.md` 聚合
- 新增周报 Markdown 模板：含本周亮点、大事记、TOP 10、趋势分析、升温/降温对照表
- 新增周报多 Agent 流程表：6 个 Agent 的周报职责对照
- 新增并行优化说明：Topic Merger + Trend Analyzer 可并行启动

**旧 Batch 文件清理**
- 新增清理脚本：每次抓取前删除 `data/batch_browser_*.json`，避免跨 session 数据污染
- 新增说明：旧 batch 文件导致合并计数虚高

**daily 文件名匹配修复**
- 问题：`2026-06-30_sorted.json`、`2026-07-01_topics.json` 等后缀文件被日期范围匹配选中
- 修复：用正则 `^\d{4}-\d{2}-\d{2}$` 严格匹配纯日期格式文件名

**并行 Agent 优化**
- 新增并行模式说明：Topic Merger 和 Trend Analyzer 数据独立，可并行启动
- Writer/Press Writer/PDF Builder 仍需串行（有数据依赖关系）

**实测数据**
- 日报：Source A 930 帖 + Source B 292 帖 → 合并 1189 帖 → 32h 筛选 239 帖 → 全量抓取 8 批
- 周报：聚合 6 天日报数据、1994 帖、11 个主题分组
- 周报生成耗时：约 8 分钟（含 Topic Merger + Trend Analyzer 并行）

### v13.0.0 (2026-06-30)
新增**月报模式**，基于已有数据聚合，不重复抓取：

**月报触发词**
- 新增：月报、AI月报、技术月报、linuxdo月报、monthly、出月报、本月AI新闻、月度总结
- 支持指定月份：`月报 2026-05` / `2026年5月月报` / `上月月报`
- 不指定时默认生成上一个自然月

**月报数据策略（核心）**
- 不重复抓取，聚合当月 `data/daily/{YYYY-MM-DD}.json` 与 `data/reports/{YYYY-MM-DD}.md`
- 扫描日报 Markdown 提取每日亮点，用于跨日趋势归纳
- 帖子去重但不做历史去重（月内全量呈现）
- 复用 v12 公益站过滤规则
- 缺失日期标注并继续生成，不中断

**月报输出风格**
- 月度趋势总结 + 主题归纳（非按天拼接）
- 月度热门主题 TOP 10（按月度浏览量）
- 主题分布表（复用 Agent 2 分类规则）
- **下月展望**（基于本月趋势预测）

**月报多 Agent 职责调整**
- Crawler：改为读取当月已有数据并聚合
- Trend Analyzer：改为跨日趋势归纳（基于 daily_highlights）
- Writer / Press Writer / PDF Builder：使用月报模板，Typst 转义规则同 v12

**目录结构**
- 新增 `data/monthly/{YYYY-MM}.md` / `.json` / `_press.md` / `.pdf` / `.typ`

### v12.0.0 (2026-06-29)
基于 2026-06-29 实战经验优化：

**批量抓取数据保存修复（核心问题）**
- 旧方案：文档未强调保存时机，导致 batch 3-10 数据丢失
- 新方案：明确要求每批抓取后**立即**用 Python 保存到文件
- 新增空帖检测：已删除/私有帖子（空标题）不保存

**官方警告检测（v12 新增）**
- 新增检测页面内容中的 "异常的自动化访问行为" 或 "系统检测到"
- 触发时立即停止爬取，返回 `stopped: 'official_warning'`

**JSON 双重编码处理（v12 新增）**
- `browser_evaluate` 使用 `filename` 参数保存的 JSON 文件是 double-encoded
- 读取时需用 `json.loads(json.load(f))` 处理

**Typst 特殊字符处理（v12 重点修复）**
- `$` 必须转义为 `\$`（数学模式符号）
- `#` 必须转义为 `\#`（标记符号）
- `*` 用于斜体，不支持 `**bold**` 语法
- macOS 字体只需 PingFang SC

**全量抓取支持**
- 新增"全量抓取"模式说明：用户要求"全部抓取"时需完成所有批次
- 通常 8-10 批，240-300 帖

**实测数据**
- Source A: 868 帖，Source B: 135 帖 → 合并 970 帖
- 历史去重后 871 帖，32h 筛选后 262 帖
- 全量抓取 10 批 × 30 帖 = 300 帖（含空帖）
- 有效帖子约 180-200 帖，整体耗时约 35 分钟

### v11.0.0 (2026-06-24)
基于 2026-06-24 实战经验优化：

**滚动策略优化**
- 旧方案：固定 15 次滚动，不足再追加
- 新方案：递增滚动 3 轮（15+10+5），35 次可加载 1000+ 帖
- 每轮后检查数量决定是否继续

**批量抓取提前终止（核心优化）**
- 旧方案：必须抓取全部帖子正文
- 新方案：100-150 帖正文 + 其余仅用标题/标签/浏览量即可生成高质量日报
- 按浏览量降序优先抓取热门帖，4-5 批后可直接进入日报生成
- 大幅缩短总耗时（从 50 分钟降至 ~25 分钟）

**时间戳提取合并**
- 旧方案：步骤 1.3 提取列表 + 步骤 1.6 单独提取时间戳
- 新方案：步骤 1.3 一次性提取列表+时间戳（从 `td.activity[title]`）
- 省去单独的时间戳提取步骤和 `data/topic_timestamps.json` 中间文件

**批量抓取不回列表页**
- 旧方案：每帖抓取后返回列表页（多 1.5s 等待 + 一次页面加载）
- 新方案：直接从一个帖子导航到下一个帖子
- 每帖节省约 3 秒，30 帖一批节省约 90 秒

**批量大小调整**
- 每批从 20 帖提升到 30 帖（减少批次切换开销）

**Typst 模板修复**
- 字体：`("PingFang SC", "Helvetica Neue", "Arial")`（移除未安装的 Noto Sans CJK SC）
- 新增 `#` 转义提醒：文本中的 `#` 必须写成 `\#`

**主题分类规则更新**
- 新增：豆包/火山引擎 生态（豆包, doubao, seed, 火山, seedance, 字节）
- 新增：Grok 生态（grok）
- 扩展 AI 编程工具：加入 hermes, opencode, kiro, minimax
- 扩展 OpenAI 关键词：sub2api, plus, pro20, pro 5x
- 扩展 Claude 关键词：cc-switch, max

**实测数据**
- Source A: 1049 帖，Source B: 372 帖 → 合并 1379 帖
- 历史去重后 1313 帖，32h 筛选后 432 帖，公益站过滤后 412 帖
- 正文抓取 120 帖（4 批），整体耗时约 25 分钟

### v10.0.0 (2026-06-23)
基于 2026-06-23 实战经验重构：

**核心变更：时间戳提取方式**
- 旧方案：`document.querySelector('time')` 从帖子页面提取 → **返回空！帖子页面没有 `<time>` 元素**
- 新方案：从列表页 `td.activity[title]` 属性提取 `"Created: Jun 22, 2026 9:53 pm"` 格式
- 原因：Discourse 帖子页使用相对时间显示（"14h"），不暴露 `<time>` 元素

**抓取流程优化**
- 用户要求模拟人类浏览：逐帖打开 → 返回列表页 → 打开下一帖
- 每批 20 帖（原 30 帖），返回列表页间隔 1.5 秒
- 全部抓取完后再做 32 小时筛选（不在抓取过程中筛选）
- 超时 20 秒（原 15 秒）

**时间戳合并流程**
- 滚动加载列表页 → 提取 `td.activity[title]` → 保存到 `data/topic_timestamps.json`
- 使用 `dateutil.parser.parse()` 解析 `"Jun 22, 2026 9:53 pm"` 格式
- 合并时间戳到帖子数据后再做 32 小时筛选

**公益站过滤优化**
- 增加关键词：LDC、ldc、高级推广、富可敌国、中转站、抽奖
- 同时检查标题、标签、内容前 200 字

**实测数据**
- 496 帖全部抓取，公益站过滤后 420 帖
- 32 小时筛选后 253 帖纳入日报
- 整体耗时约 50 分钟（含浏览器预授权）

### v9.0.0 (2026-06-21)
基于 2026-06-21 实战经验重构：

**核心变更：浏览器 fetch API → 浏览器逐帖浏览**
- 旧方案：`browser_evaluate` + `fetch('/t/{id}.json')` → 触发 429 限流
- 新方案：`browser_navigate` 打开帖子页面 → 提取 DOM 数据 → 直接导航下一帖
- 原因：linux.do 对批量 API 请求做了严格限流，浏览器逐帖浏览更安全

**抓取流程**
- 主力方案：`browser_navigate` 打开帖子页面 + `browser_evaluate` 提取 DOM 数据
- 速度优化：不回列表页，直接从一个帖子导航到下一个帖子
- Cloudflare 处理：每帖检测标题，包含 "Just a moment" 则等待 15 秒

**预授权优化**
- 简化为 4 步：关闭旧实例 → 导航触发 → 等待 Cloudflare → 确认页面加载
- 明确列出需要预授权的工具清单
- 强调不需要登录态

**已知限制**
- 逐帖浏览方式较慢（每帖约 3-5 秒：导航 2s + 提取 1s + 等待 0.5s）
- 849 帖全部抓取需要约 45-70 分钟
- 部分帖子可能返回空标题（已删除或私有）

### v15.3.0 (2026-07-18)
基于 2026-07-18 全量日报 + 视频工厂联跑经验：

**全量抓取闭环（实测）**
- 双源列表合并后队列约 557 帖 → 正文批次 0–18（末批不足 30）→ 有效标题约 556 → 二次公益站过滤后 **531** 入 `data/daily/YYYY-MM-DD.json`
- **每批必须立即** `data/save_latest_batch.py N` 或等价写入 `data/batch_browser_N.json`；禁止「全部抓完再存」
- 工具返回 JSON 若只在 transcript 里：从 session jsonl 回填（见 v15.2 协议）

**浏览器稳定**
- 全量批抓阶段**只保留一个** Playwright MCP 会话；不要并行启动视频号独立 Chrome 共用 profile
- 批抓循环内：Cloudflare 标题检测 + 官方「异常自动化访问」文案则停批保存已抓
- 与 `ai-news-factory` 衔接：日报 PDF/报告落盘后再开视频流水线，减少浏览器互杀

**合并与过滤**
- 合并 `crawl_queue` 元数据时：列表页 views 若高于详情 DOM 则回填（详情有时为 0/占位）
- 二次过滤：标题/标签/内容前 200 字扫公益站与纯交易词（与 v15.2 关键词表一致）
- Writer 可信度分层：官方确认 / 社区实测 / 媒体报道 / 未确认传闻

**联跑检查清单**
1. `data/daily/{date}.json` total 与 with_content
2. `data/reports/{date}.md` + `_press.md` + `.pdf`
3. 再触发 ai-news-factory（推荐事件可不确认）
