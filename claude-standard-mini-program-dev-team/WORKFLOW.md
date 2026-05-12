# 11 阶段工作流详解

---

## 一、Phase 调度全图

```
Phase 0   orchestrator 创建目录
Phase 1   → product-manager          → PRD.md（含微信生态需求）
          ⏸ 人工检查点 #1
Phase 2   → software-architect       → API_CONTRACT.md
                                        DB_SCHEMA.md（含 openid）
                                        TECH_SPEC.md（含微信登录方案）
          ⏸ 人工检查点 #2
Phase 2.5 → ui-designer              → DESIGN_SYSTEM.md
                                        variables.wxss（rpx 体系）
Phase 3   orchestrator 自己拆任务清单
Phase 4   → database-optimizer       → migrations/
Phase 5   → backend-architect + ev-collector  Dev-QA Loop
Phase 6   → mp-developer + ev-collector       Dev-QA Loop
Phase 7   → security-engineer        → SECURITY_REPORT.md
Phase 8   → code-reviewer            → REVIEW_REPORT.md
Phase 9   → mp-publisher             → 包大小 + 配置 + 发布准备
Phase 10  → reality-checker          → READY / NEEDS WORK
Phase 11  → technical-writer         → README + API_DOC
完工 ✅
```

---

## 二、微信小程序 vs Web 的核心差异

### 登录方案
```
Web 应用：用户名密码 → JWT
小程序：  wx.login → code → 后端 code2Session → JWT
         无需用户操作即可获取 openid（静默登录）
         手机号需用户主动授权
```

### 部署方式
```
Web 应用：Docker → Nginx 网关 → 子路径路由
小程序：  微信开发者工具上传 → 微信审核 → 发布
         无 Docker/Nginx，无子路径问题
         有包大小限制（主包 2MB / 总包 20MB）
```

### 安全重点
```
Web 应用：CORS、XSS、CSRF、子路径 404
小程序：  openid 泄露、内容安全审核、隐私合规、接口鉴权
         无 CORS 问题（小程序请求不受浏览器同源策略限制）
         但 CORS origin:* 仍被微信判定为安全风险
```

### 前端开发
```
Web 应用：Vue/React、HTML/CSS/JS、vw/rem 单位
小程序：  WXML/WXSS/JS、rpx 单位、微信原生组件
         setData 替代 setState（性能陷阱）
         页面栈最多 10 层
         不支持自定义字体（包大小限制）
```

---

## 三、Dev-QA Loop

与原版相同，核心机制不变：
1. 实现任务 → QA 独立验证 → PASS/FAIL
2. FAIL 打回实现 agent，重试上限 3 次
3. 超限暂停问用户

小程序额外验证项：
- 包大小合规
- API 地址未硬编码
- openid 未泄露
- rpx 单位正确使用

---

## 四、打回机制

| 触发条件 | 打回目标 | 最大重试 |
|---------|---------|---------|
| DB_ISSUES.md 存在 | software-architect | 2次 |
| 后端 QA FAIL | backend-architect | 3次/任务 |
| 前端 QA FAIL（样式硬编码）| mini-program-developer | 3次/任务 |
| **前端 QA FAIL（API 地址硬编码）** | **mini-program-developer（零容忍）** | **3次/任务** |
| **包大小超限** | **mini-program-developer** | **2次** |
| 安全高危 | 对应 agent | 2次 |
| Review MUST FIX | 对应 agent | 2次 |
| reality-checker NEEDS WORK | 对应 agent | 1次 |

---

## 五、人工检查点

1. **Phase 1 后**：展示 PRD 功能列表 + 微信生态需求（登录/支付/UGC）
2. **Phase 2 后**：展示 API 接口 + 表结构 + 微信登录方案

其余自动执行。

---

## 六、各 Phase 详解

### Phase 0 - 初始化
创建 `docs/` 和 `project-tasks/` 目录。

### Phase 1 - PRD
product-manager 输出 PRD，**额外包含微信生态需求章节**：
- 登录方式选择
- 微信能力清单（支付/分享/订阅消息）
- 内容安全需求（UGC 场景）
- 包大小策略

### Phase 2 - 技术契约（⭐ 最关键）
software-architect 输出三个文件，**额外包含**：
- 微信登录流程图和接口设计
- 小程序前端技术选型（原生/Taro/uni-app）
- API 基础 URL 配置规范（配置文件方式）
- 包大小管理策略
- 小程序特有安全规范

### Phase 2.5 - 设计规范
ui-designer 输出设计规范，**使用 rpx 单位体系**：
- 基于 750rpx 设计稿
- 遵循微信小程序设计指南
- 输出 variables.wxss（非 variables.css）
- 暗色模式适配

### Phase 3 - 任务拆解
orchestrator 读取契约拆任务。

### Phase 4 - 数据库
database-optimizer 创建迁移文件，**用户表必须包含 openid 字段**。

### Phase 5 - 后端实现
backend-architect 实现接口，**必须实现微信登录接口**：
- code2Session 调用
- JWT token 生成
- openid 保护（不返回前端）
- CORS 白名单
- 频率限制基于 openid/userId

### Phase 6 - 小程序前端
mini-program-developer 实现页面，**必须正确使用微信 API**：
- wx.request 统一封装
- wx.login 登录流程
- setData 性能优化
- 页面栈管理
- 分包加载

### Phase 7 - 安全审查
security-engineer 额外检查：
- openid/session_key 保护
- 内容安全审核接入
- 隐私协议合规
- CORS 配置

### Phase 8 - 代码 Review
code-reviewer 额外检查：
- setData 优化
- 包大小合规
- 页面栈风险
- rpx 单位使用

### Phase 9 - 发布准备
mini-program-publisher 检查：
- app.json 配置完整性
- 包大小合规
- API 地址配置
- 隐私声明配置
- 生成发布检查报告

### Phase 10 - 最终验收
reality-checker 额外验证：
- 包大小 ≤ 2MB
- 无硬编码 API 地址
- openid 未泄露
- app.json 配置完整
- 隐私声明完备

### Phase 11 - 文档
technical-writer 生成文档，**包含小程序特有章节**：
- 微信开发者工具配置
- AppID 配置
- 环境切换说明
- 提审发布流程
