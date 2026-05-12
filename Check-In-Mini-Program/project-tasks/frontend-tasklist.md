# 小程序前端任务清单
> 每任务对应一个页面或核心模块
> 契约文件：docs/API_CONTRACT.md
> 设计规范：docs/DESIGN_SYSTEM.md
> 状态：全部完成

---

### [x] TASK-F01：项目基础架构与全局配置

- 对应契约：TECH_SPEC.md 项目目录结构
- 验收标准：
  - app.js 存在，全局登录逻辑实现
  - app.json 存在，配置 3 个页面路由 + TabBar（首页/打卡记录/个人中心）
  - app.wxss 存在，引入 styles/variables.wxss
  - project.config.json 存在，appid 配置
  - sitemap.json 存在
  - config/env.js 存在，API_BASE 可配置（禁止硬编码）
  - utils/request.js 存在，统一封装 wx.request
  - utils/auth.js 存在，实现 login / checkLogin / logout
  - styles/variables.wxss 存在（DESIGN_SYSTEM 规范落地）

---

### [x] TASK-F02：首页 — 打卡页面

- 调用契约：POST /api/v1/checkin, GET /api/v1/checkin/status
- 设计规范：DESIGN_SYSTEM.md #首页（index）
- 验收标准：
  - pages/index/index.wxml 存在
  - pages/index/index.wxss 存在，样式全部使用 CSS 变量
  - pages/index/index.js 存在
  - pages/index/index.json 存在
  - 显示连续打卡天数（大数字，--font-size-3xl，--color-highlight）
  - 打卡按钮：240rpx 圆形，未打卡/已打卡两种状态
  - 点击打卡调用 POST /api/v1/checkin
  - 页面加载时调用 GET /api/v1/checkin/status 获取状态
  - 显示今日日期
  - 显示本月打卡统计卡片
  - 已打卡状态显示"已打卡" + 勾选图标
  - 错误处理：409 already_checked_in 提示"今日已打卡"
  - 所有 API 字段名与契约一致

---

### [x] TASK-F03：打卡记录页 — 日历视图

- 调用契约：GET /api/v1/checkin/history
- 设计规范：DESIGN_SYSTEM.md #打卡记录页（history）
- 验收标准：
  - pages/history/history.wxml 存在
  - pages/history/history.wxss 存在，样式全部使用 CSS 变量
  - pages/history/history.js 存在
  - pages/history/history.json 存在
  - 显示当月日历视图
  - 已打卡日期高亮（--color-primary-light 背景）
  - 今日日期边框标识（--color-primary）
  - 月份切换功能（左右箭头）
  - 调用 GET /api/v1/checkin/history?year=X&month=X 获取数据
  - 显示本月打卡统计（已打卡天数 / 总天数 / 打卡率）
  - 日历格子 88rpx x 88rpx
  - 所有 API 字段名与契约一致

---

### [x] TASK-F04：个人中心页面

- 调用契约：GET /api/v1/users/me
- 设计规范：DESIGN_SYSTEM.md #个人中心页（profile）
- 验收标准：
  - pages/profile/profile.wxml 存在
  - pages/profile/profile.wxss 存在，样式全部使用 CSS 变量
  - pages/profile/profile.js 存在
  - pages/profile/profile.json 存在
  - 显示用户头像（128rpx 圆形）
  - 显示用户昵称
  - 三列统计卡片：总打卡天数 / 当前连续天数 / 最高连续天数
  - 数字使用 --font-size-2xl，--color-primary
  - 退出登录按钮（--color-danger）
  - 退出登录清除本地缓存并重新登录
  - 调用 GET /api/v1/users/me 获取数据
  - 所有 API 字段名与契约一致

---

### [x] TASK-F05：日历自定义组件

- 对应契约：TECH_SPEC.md components/calendar
- 设计规范：DESIGN_SYSTEM.md #日历组件规范
- 验收标准：
  - components/calendar/calendar.wxml 存在
  - components/calendar/calendar.wxss 存在
  - components/calendar/calendar.js 存在
  - components/calendar/calendar.json 存在（component: true）
  - 支持属性：year, month, checkinDates（已打卡日期数组）
  - 支持事件：monthChange（月份切换）
  - 渲染当月日历网格
  - 已打卡日期高亮显示
  - 今日日期标识
  - 可复用于 history 页面

---

### [x] TASK-F06：打卡按钮自定义组件

- 对应契约：TECH_SPEC.md components/check-button
- 设计规范：DESIGN_SYSTEM.md #打卡按钮规范
- 验收标准：
  - components/check-button/check-button.wxml 存在
  - components/check-button/check-button.wxss 存在
  - components/check-button/check-button.js 存在
  - components/check-button/check-button.json 存在（component: true）
  - 支持属性：checked（是否已打卡）
  - 支持事件：tap（点击打卡）
  - 未打卡状态：--color-primary 背景，白色"打卡"文字
  - 已打卡状态：--color-primary-light 背景，"已打卡" + 勾选
  - 点击动画：缩放 0.95 -> 1.0，150ms
  - 240rpx 圆形按钮
  - 可复用于 index 页面
