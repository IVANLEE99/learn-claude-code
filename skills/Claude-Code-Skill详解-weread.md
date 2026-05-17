# Claude Code Skill 详解：微信读书助手（weread）

## 一、Skill 是什么

Skill（技能）是 Claude Code 的扩展机制，允许用户定义可复用的专业能力。它比 Command（命令）更强大：

| 特性 | Command | Skill |
|------|---------|-------|
| 调用方式 | 用户手动 `/command` | Claude 自动触发 + 用户手动 |
| 文件结构 | 单个 `.md` 文件 | 目录，含 `SKILL.md` + 参考资料 |
| 典型用途 | 动作型："帮我做 X" | 知识型："知道 X 的最佳实践" |
| 可捆绑资源 | 不能 | 可以（模板、脚本、示例等） |

**一句话理解**：Command 是快捷操作按钮，Skill 是会自动识别场景并执行标准流程的领域专家。

---

## 二、weread Skill 说明

> "让 AI 成为你的阅读搭档" — 连接微信读书账号，让 AI 助手随时查阅你的阅读记录。

### 功能

通过 Agent API Gateway 调用微信读书接口，提供六大核心能力：

| 能力 | 说明 | 用户示例 |
|------|------|----------|
| 查阅书架 | 浏览个人书架，快速了解藏书全貌 | "看看我的书架" |
| 阅读统计 | 时长、天数、偏好深度分析，量化阅读习惯 | "我这个月读了多久" "今年读了几本书" |
| 笔记和划线 | 查看个人划线和想法，导出笔记，回顾阅读中的思考 | "看看我在三体里的笔记" |
| 书籍搜索 | 在书城搜索任意书籍，获取书名、作者、评分等关键信息 | "帮我搜一下三体" |
| 书籍详情 | 查看书籍详情、章节目录、阅读进度 | "这本书有多少章" "我读到哪了" |
| 推荐好书 | 基于阅读偏好的个性化推荐或相似书籍推荐 | "给我推荐几本书" |

此外还支持：章节热门划线（查看热门划线及想法）、书籍点评（查看公开点评）。

### 触发条件

当用户提到以下关键词时，自动触发：
- 微信读书、读书、书架、笔记、划线、书评
- 阅读统计、阅读时长、阅读偏好
- 搜书、找书、推荐书、书单
- weRead、weread

---

## 三、API 接口规范

### 统一入口

```
POST https://i.weread.qq.com/api/agent/gateway
```

### 鉴权

- Header：`Authorization: Bearer $WEREAD_API_KEY`
- `WEREAD_API_KEY` 从环境变量获取，格式 `wrk-xxxxxxxx`
- 若未设置，提示用户：`export WEREAD_API_KEY=<你的apikey>`

### 请求格式

```bash
curl -X POST "https://i.weread.qq.com/api/agent/gateway" \
  -H "Authorization: Bearer $WEREAD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"api_name": "/store/search", "keyword": "三体", "count": 10, "skill_version": "1.0.3"}'
```

### 关键规则

1. **版本上报**：每次请求 body 必须包含 `"skill_version": "1.0.3"`（取 SKILL.md 顶部 version 字段的值），用于服务端检查版本更新
2. **升级提醒**：如果回包中出现 `upgrade_info` 字段，必须立即暂停当前操作，按照 `upgrade_info.message` 中的指引完成升级，升级完成后再重新执行用户请求
3. **参数平铺**：业务参数必须和 `api_name`、`skill_version` 放在同一层；不要包在 `params`、`data`、`body` 等对象里。只有接口文档明确声明的数组/对象字段（如 `/book/readreviews` 的 `reviews`）才允许作为业务字段传入
4. **能力文档预检**：调用任何接口前，必须先阅读对应说明文件（如阅读统计先读 `readdata.md`，书架先读 `shelf.md`），确认接口参数、字段含义、单位和工作流；禁止仅凭字段名或经验猜测含义
5. **字段解释优先级**：以对应说明文件中的字段说明为准；如果回包字段名和直觉含义冲突，必须服从说明文件，不得直接翻译字段名
6. **bookId 解析**：用户输入书名时，先调 `/store/search` 获取 bookId，再执行后续操作
7. **书架数量**：必须按 `books.length + albums.length + (mp 非空 ? 1 : 0)` 计算；`albums[]` 是专辑/有声书，也属于书架里的书
8. **结果展示**：列表用编号展示方便选择；展示接口回包信息时，字段**禁止**直接翻译，应该参考文件中的说明内容提供
9. **上下文衔接**：对话中记住已查询的 bookId，后续操作无需用户重复提供
10. **深度链接**：展示划线、想法、章节等内容时，拼接跳转链接方便用户在 App 中打开
11. **数据展示规范**：
   - **时间戳**：所有 Unix 时间戳字段展示时须转为 YYYY-MM-DD 格式，不得直接展示原始数字
   - **阅读时长**：单位为秒，展示时转为"X小时Y分钟"格式

### 响应格式

- JSON，回包经过字段裁剪，只返回核心字段
- `errcode` 非 0 时表示错误，给出中文提示
- 发送 `{"api_name": "/_list"}` 可查看所有可用接口及参数定义

### 接口总览

| 接口 | 说明 | 参考文档 |
|------|------|----------|
| `/store/search` | 搜索书籍（支持多 scope） | `search.md` |
| `/book/info` | 书籍基本信息 | `book.md` |
| `/book/chapterinfo` | 章节目录 | `book.md` |
| `/book/getprogress` | 阅读进度 | `book.md` |
| `/shelf/sync` | 书架同步 | `shelf.md` |
| `/user/notebooks` | 笔记本概览 | `notes.md` |
| `/book/bookmarklist` | 单本划线内容 | `notes.md` |
| `/review/list/mine` | 个人想法与点评 | `notes.md` |
| `/book/underlines` | 章节划线热度统计 | `notes.md` |
| `/book/bestbookmarks` | 书籍热门划线 | `notes.md` |
| `/book/readreviews` | 划线下想法/评论 | `notes.md` |
| `/review/single` | 单条想法详情 | `notes.md` |
| `/review/list` | 书籍公开点评 | `review.md` |
| `/readdata/detail` | 阅读统计详情 | `readdata.md` |
| `/book/recommend` | 个性化推荐 | `discover.md` |
| `/book/similar` | 相似书推荐 | `discover.md` |
| `/_list` | 查看所有可用接口 | — |

---

## 四、快速安装

### 方式一：自动安装（推荐）

将以下指令发送给 AI 助手即可自动安装：

```
下载 https://cdn.weread.qq.com/skills/weread-skills.zip 安装 skill
```

### 方式二：手动安装

```bash
mkdir -p ~/.claude/skills/weread
cd ~/.claude/skills/weread
curl -sL "https://cdn.weread.qq.com/skills/weread-skills.zip" -o /tmp/weread-skills.zip
unzip -o /tmp/weread-skills.zip -d /tmp/weread-skills-extracted
cp /tmp/weread-skills-extracted/weread-skills/*.md .
```

### 配置 API Key

API Key 用于连接你的微信读书账号，数据仅你可见。

1. 登录微信读书获取 API Key：https://weread.qq.com
2. 设置环境变量：

```bash
export WEREAD_API_KEY=<你的apikey>
```

API Key 格式为 `wrk-xxxxxxxx`，绑定用户身份（vid），需要用户身份的接口会自动注入，无需手动传 vid。

---

## 五、创建详细过程

### 第 1 步：创建目录结构

```bash
mkdir -p ~/.claude/skills/weread
```

最终结构：
```
~/.claude/skills/weread/
├── SKILL.md          # 入口文件（能力列表 + 接口规范 + 通用规则）
├── search.md         # 搜索书籍接口文档
├── book.md           # 书籍信息与阅读进度
├── shelf.md          # 书架管理
├── notes.md          # 笔记/划线
├── review.md         # 书籍点评
├── readdata.md       # 阅读统计
├── profile.md        # 用户信息与阅读统计
└── discover.md       # 发现推荐好书
```

### 第 2 步：编写 SKILL.md

这是 Skill 的核心入口文件，包含：

1. **元信息** — name、description、version
2. **能力矩阵** — 所有能力的概览表，每种能力指向对应的参考文档
3. **接口调用规范** — 统一入口、鉴权、请求格式、通用规则
4. **深度链接** — URL Schema 格式，用于在微信读书 App 中打开对应内容

### 第 3 步：编写各能力参考文档

| 文件 | 对应能力 | 主要接口 |
|------|----------|----------|
| `search.md` | 搜索书籍 | `/store/search` |
| `book.md` | 书籍信息 | `/book/info`, `/book/chapterinfo`, `/book/getprogress` |
| `shelf.md` | 书架管理 | `/shelf/sync` |
| `notes.md` | 笔记划线 | `/user/notebooks`, `/book/bookmarklist`, `/review/list/mine`, `/book/underlines`, `/book/bestbookmarks`, `/book/readreviews`, `/review/single` |
| `review.md` | 书籍点评 | `/review/list` |
| `readdata.md` | 阅读统计 | `/readdata/detail` |
| `discover.md` | 推荐好书 | `/book/recommend`, `/book/similar` |
| `profile.md` | 用户信息 | 组合调用书架+进度+笔记接口 |

### 第 4 步：迭代优化

根据实际使用中的问题进行优化：

| 问题 | 修复方案 |
|------|----------|
| scope 选择不确定 | 在 `search.md` 中添加详细的 scope 选择指引 |
| 书架数量计算错误 | 在 `shelf.md` 中强调 `books + albums + mp` 口径 |
| 参数嵌套导致分页失效 | 在 `notes.md` 中添加 few-shot 正确/错误对比 |
| 字段名误导（如 noteCount） | 在文档中明确字段真实含义，禁止直接翻译 |
| 阅读时长单位混淆 | 在 `readdata.md` 中强调所有时长字段单位为秒 |

---

## 六、深度链接（URL Schema）

在展示内容时，拼接跳转链接方便用户在微信读书 App 中打开：

### 打开书籍

```
weread://reading?bId={bookId}
```

### 跳转到指定章节

```
weread://reading?bId={bookId}&chapterUid={chapterUid}
```

### 跳转到划线/想法位置

```
weread://bestbookmark?bookId={bookId}&chapterUid={chapterUid}&rangeStart={rangeStart}&rangeEnd={rangeEnd}&userVid={userVid}
```

> **range 解析**：划线接口返回的 `range` 格式为 `"起始-结束"`（如 `"900-2004"`），拆分后分别填入 `rangeStart` 和 `rangeEnd`。

---

## 七、常见陷阱与最佳实践

### 1. 参数不要嵌套

**正确**（参数平铺在 body 顶层）：
```json
{"api_name":"/user/notebooks","count":100,"skill_version":"1.0.5"}
```

**正确**（下一页继续平铺 `lastSort`）：
```json
{"api_name":"/user/notebooks","count":100,"lastSort":1516907353,"skill_version":"1.0.5"}
```

**错误**（不要包在 `params` 里，会导致分页失效）：
```json
{"api_name":"/user/notebooks","params":{"count":100,"lastSort":1516907353},"skill_version":"1.0.5"}
```

**错误**（不要使用 `offset`/`limit`，这些字段不是分页参数）：
```json
{"api_name":"/user/notebooks","offset":20,"limit":20,"skill_version":"1.0.5"}
```

### 2. 书架数量必须包含专辑

书架总数 = `books.length + albums.length + (mp 非空 ? 1 : 0)`

- `albums[]` 是专辑/有声书，也属于书架里的书
- 不要只用 `books.length` 回答"书架里有多少本书"

**正确示例**（10 本电子书 + 3 个有声书）：
> 你的书架共有 **13 个条目**：10 本电子书 + 3 个专辑/有声书。

**错误示例**：
> 你的书架共有 10 本书，另外还有 3 个有声书。
> （错误原因：专辑/有声书也在书架里，必须计入总数）

### 3. 搜索 scope 选择指引

| 用户意图 | scope 值 |
|----------|----------|
| "搜书""找书""查某本书" | `10`（电子书） |
| "搜一下 xx"（未限定类型） | `0`（全部） |
| "网文""网络小说" | `16`（网文小说） |
| "听书""有声书""播客" | `14`（微信听书） |
| "搜一下 xx 作者" | `6`（作者） |
| "书里提到了 xx""全文搜索" | `12`（全文） |
| "有什么书单" | `13`（书单） |
| "搜公众号" | `2`（公众号） |
| "搜文章" | `4`（文章） |

### 4. 阅读时长单位是秒

`totalReadTime`、`dayAverageReadTime` 等字段单位均为**秒**，展示时转为"X小时Y分钟"格式。

跨年区间查询示例："2024 年 1 月 31 日至今，我的总阅读时长是多少？"
- 推荐做法：查询 2024 至当前年份的 `annually`，累加年度 `totalReadTime`；再查询 2024-01 的 `monthly`，从总和中扣除 2024 年 1 月的 `totalReadTime`，得到近似的 `2024-02-01 至今` 口径。

### 5. progress 是百分比整数

`book.getprogress` 返回的 `progress` 范围是 0-100，1 表示 1%（不是 100%）。只有 100 才代表读完。

### 6. 笔记数 = 书签 + 划线 + 想法

`/user/notebooks` 的总笔记数 = `reviewCount + noteCount + bookmarkCount`。不要把 `noteCount` 单独当作总笔记数。

- `noteCount` 字段名容易误读：它不是单本书总笔记数，而是划线/高亮原文条数
- `reviewCount` 已包含个人点评/书评想法，计算总笔记数时不要再额外加"点评数"
- 内容导出 = 划线内容 + 想法/点评内容；当前不能导出书签内容

---

## 八、使用方式

```bash
# 手动调用
/weread

# 自动触发
# 说 "帮我看看微信读书里的笔记" 即可
# 说 "搜一下三体" 即可
# 说 "我这个月读了多久" 即可
```

---

## 九、文件内容

Skill 已安装至 `~/.claude/skills/weread/` 目录，完整文件请查看：

| 文件 | 说明 | 路径 |
|------|------|------|
| SKILL.md | 入口文件（能力列表 + 接口规范） | `~/.claude/skills/weread/SKILL.md` |
| search.md | 搜索书籍接口 | `~/.claude/skills/weread/search.md` |
| book.md | 书籍信息与阅读进度 | `~/.claude/skills/weread/book.md` |
| shelf.md | 书架管理 | `~/.claude/skills/weread/shelf.md` |
| notes.md | 笔记/划线 | `~/.claude/skills/weread/notes.md` |
| review.md | 书籍点评 | `~/.claude/skills/weread/review.md` |
| readdata.md | 阅读统计 | `~/.claude/skills/weread/readdata.md` |
| profile.md | 用户信息 | `~/.claude/skills/weread/profile.md` |
| discover.md | 推荐好书 | `~/.claude/skills/weread/discover.md` |

---

## 十、相关资源

- 微信读书 Skill 官方页面: https://weread.qq.com/r/weread-skills
- 微信读书 API Key 获取: https://weread.qq.com
- Skill 下载包: https://cdn.weread.qq.com/skills/weread-skills.zip
- Claude Code 官方文档: https://docs.anthropic.com/en/docs/claude-code
- 微信读书 Agent API Gateway: https://i.weread.qq.com/api/agent/gateway
- MCP 协议: https://modelcontextprotocol.io
- 用户协议: https://weread.qq.com/web/copyright
- 隐私政策: https://privacy.qq.com/mb/policy/tencent-privacypolicy
