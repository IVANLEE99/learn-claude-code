# 设计系统文档 (DESIGN_SYSTEM) -- Todo App

> 版本：1.0
> 日期：2026-05-11
> 作者：ui-designer
> 基于：PRD v1.0 / TECH_SPEC v1.0

---

## 1. 设计理念

- **极简高效**：3 秒完成待办创建，界面零干扰
- **移动端优先**：最小视口 320px，可点击区域最小 44px
- **状态驱动**：视觉聚焦"未完成"，完成后弱化处理
- **中文友好**：字号不低于 16px，行高宽松

---

## 2. 颜色体系

### 2.1 品牌色

| 变量名 | 亮色值 | 暗色值 | 用途 |
|--------|--------|--------|------|
| `--color-brand-primary` | #4A90D9 | #5BA0E9 | 主按钮、链接、选中态 |
| `--color-brand-primary-light` | #E8F0FE | #1A3A5C | 品牌色浅底（hover 背景） |
| `--color-brand-primary-dark` | #2E6DB4 | #3D7FC4 | 品牌色深色（按下态） |

### 2.2 功能色

| 变量名 | 亮色值 | 暗色值 | 用途 |
|--------|--------|--------|------|
| `--color-success` | #27AE60 | #2ECC71 | 成功提示、完成标记 |
| `--color-success-light` | #E8F8EF | #1A3D27 | 成功浅底 |
| `--color-warning` | #F39C12 | #F1C40F | 警告提示 |
| `--color-warning-light` | #FEF5E7 | #3D3010 | 警告浅底 |
| `--color-danger` | #E74C3C | #EC7063 | 危险操作、错误提示 |
| `--color-danger-light` | #FDEDEC | #3D1A17 | 危险浅底 |
| `--color-info` | #3498DB | #5DADE2 | 信息提示 |

### 2.3 中性色

| 变量名 | 亮色值 | 暗色值 | 用途 |
|--------|--------|--------|------|
| `--color-text-primary` | #1A1A1A | #E8E8E8 | 主文本 |
| `--color-text-secondary` | #666666 | #A0A0A0 | 次要文本 |
| `--color-text-tertiary` | #999999 | #6B6B6B | 占位符、禁用文本 |
| `--color-text-inverse` | #FFFFFF | #1A1A1A | 反色文本（深底白字） |
| `--color-bg-page` | #F5F5F5 | #121212 | 页面背景 |
| `--color-bg-card` | #FFFFFF | #1E1E1E | 卡片背景 |
| `--color-bg-elevated` | #FFFFFF | #2A2A2A | 浮层/弹窗背景 |
| `--color-bg-hover` | #F0F0F0 | #333333 | hover 态背景 |
| `--color-border` | #E0E0E0 | #3A3A3A | 边框 |
| `--color-border-light` | #F0F0F0 | #2E2E2E | 轻边框（分隔线） |
| `--color-divider` | #EEEEEE | #2C2C2C | 分割线 |

### 2.4 优先级色

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--color-priority-high` | #E74C3C | 高优先级标识 |
| `--color-priority-medium` | #F39C12 | 中优先级标识 |
| `--color-priority-low` | #3498DB | 低优先级标识 |

---

## 3. 字体体系

### 3.1 字体栈

| 变量名 | 值 |
|--------|-----|
| `--font-family` | -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif |

### 3.2 字号梯度

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--font-size-xs` | 12px | 辅助信息、时间戳（仅限非交互文本） |
| `--font-size-sm` | 14px | 次要文本、列表副标题 |
| `--font-size-base` | 16px | 正文、表单输入 |
| `--font-size-md` | 18px | 列表标题 |
| `--font-size-lg` | 20px | 页面标题 |
| `--font-size-xl` | 24px | 主标题 |

### 3.3 行高

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--line-height-tight` | 1.25 | 标题 |
| `--line-height-normal` | 1.5 | 正文 |
| `--line-height-loose` | 1.75 | 多行文本 |

### 3.4 字重

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--font-weight-normal` | 400 | 正文 |
| `--font-weight-medium` | 500 | 列表标题、按钮 |
| `--font-weight-bold` | 700 | 页面标题 |

---

## 4. 间距体系

基础单位：4px

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--spacing-xs` | 4px | 图标与文字间距 |
| `--spacing-sm` | 8px | 紧凑元素内距 |
| `--spacing-md` | 12px | 卡片内距（小） |
| `--spacing-base` | 16px | 标准内距、列表项间距 |
| `--spacing-lg` | 20px | 卡片内距（大） |
| `--spacing-xl` | 24px | 页面边距（移动端） |
| `--spacing-2xl` | 32px | 页面边距（桌面端） |
| `--spacing-3xl` | 48px | 区块间距 |

---

## 5. 圆角体系

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--radius-sm` | 4px | 小按钮、标签 |
| `--radius-md` | 8px | 卡片、输入框 |
| `--radius-lg` | 12px | 弹窗、大卡片 |
| `--radius-full` | 9999px | 圆形头像、胶囊按钮 |

---

## 6. 阴影体系

| 变量名 | 亮色值 | 暗色值 | 用途 |
|--------|--------|--------|------|
| `--shadow-sm` | 0 1px 2px rgba(0,0,0,0.06) | 0 1px 2px rgba(0,0,0,0.3) | 微浮起 |
| `--shadow-md` | 0 2px 8px rgba(0,0,0,0.1) | 0 2px 8px rgba(0,0,0,0.4) | 卡片 |
| `--shadow-lg` | 0 4px 16px rgba(0,0,0,0.12) | 0 4px 16px rgba(0,0,0,0.5) | 弹窗 |
| `--shadow-focus` | 0 0 0 3px rgba(74,144,217,0.3) | 0 0 0 3px rgba(91,160,233,0.4) | 焦点环 |

---

## 7. 尺寸体系

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--size-icon-sm` | 16px | 小图标 |
| `--size-icon-md` | 20px | 标准图标 |
| `--size-icon-lg` | 24px | 大图标 |
| `--size-clickable` | 44px | 最小可点击区域 |
| `--size-header` | 56px | 顶部导航栏高度 |
| `--size-sidebar` | 280px | 侧边栏宽度（桌面端） |
| `--size-todo-item` | 72px | 待办列表项最小高度 |
| `--size-avatar` | 36px | 用户头像 |

---

## 8. 动画体系

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--duration-fast` | 150ms | hover、焦点 |
| `--duration-normal` | 250ms | 展开折叠、切换 |
| `--duration-slow` | 350ms | 页面过渡 |
| `--ease-out` | cubic-bezier(0.25, 0.46, 0.45, 0.94) | 通用缓出 |
| `--ease-in-out` | cubic-bezier(0.42, 0, 0.58, 1) | 通用缓入缓出 |

---

## 9. 组件视觉规范

### 9.1 按钮 Button

| 类型 | 背景色 | 文字色 | 边框 | 圆角 | 高度 |
|------|--------|--------|------|------|------|
| 主要 | `--color-brand-primary` | `--color-text-inverse` | 无 | `--radius-sm` | 44px |
| 次要 | 透明 | `--color-brand-primary` | 1px solid `--color-brand-primary` | `--radius-sm` | 44px |
| 危险 | `--color-danger` | `--color-text-inverse` | 无 | `--radius-sm` | 44px |
| 文字 | 透明 | `--color-brand-primary` | 无 | - | 44px |

- 内边距：0 `--spacing-lg`
- 字号：`--font-size-base`
- 字重：`--font-weight-medium`
- hover 态：背景色加深 10%
- 按下态：背景色加深 20%
- 禁用态：透明度 0.5
- 焦点态：`--shadow-focus`

### 9.2 输入框 Input

| 状态 | 边框 | 背景 | 高度 |
|------|------|------|------|
| 默认 | 1px solid `--color-border` | `--color-bg-card` | 44px |
| 焦点 | 1px solid `--color-brand-primary` + `--shadow-focus` | `--color-bg-card` | 44px |
| 错误 | 1px solid `--color-danger` | `--color-bg-card` | 44px |
| 禁用 | 1px solid `--color-border-light` | `--color-bg-hover` | 44px |

- 内边距：0 `--spacing-base`
- 字号：`--font-size-base`
- 圆角：`--radius-md`
- 错误提示文字：`--color-danger`，`--font-size-sm`

### 9.3 待办卡片 TodoCard

| 属性 | 值 |
|------|-----|
| 背景 | `--color-bg-card` |
| 圆角 | `--radius-md` |
| 内边距 | `--spacing-base` `--spacing-lg` |
| 间距（卡片间） | `--spacing-sm` |
| 阴影 | `--shadow-sm` |
| 左侧优先级色条 | 3px 宽，颜色取 `--color-priority-*` |
| 完成态标题 | `--color-text-tertiary`，添加删除线 |
| 复选框尺寸 | 22px x 22px |
| 最小高度 | `--size-todo-item` |

### 9.4 列表导航项 ListItem

| 属性 | 值 |
|------|-----|
| 高度 | `--size-clickable` |
| 内边距 | 0 `--spacing-base` |
| 选中态背景 | `--color-brand-primary-light` |
| 选中态文字 | `--color-brand-primary` |
| 左侧颜色圆点 | 8px 直径 |
| 未完成计数 | 右侧，`--font-size-sm`，`--color-text-tertiary`，圆角 `--radius-full` 背景 `--color-bg-hover` |

### 9.5 筛选栏 FilterBar

| 属性 | 值 |
|------|-----|
| 高度 | 40px |
| 内边距 | 0 `--spacing-base` |
| 选项间距 | `--spacing-md` |
| 选中态文字 | `--color-brand-primary`，`--font-weight-medium` |
| 未选中态文字 | `--color-text-secondary` |
| 底部指示线 | 2px 高，`--color-brand-primary`，宽度自适应文字 |

### 9.6 空状态 EmptyState

| 属性 | 值 |
|------|-----|
| 图标尺寸 | 64px |
| 图标颜色 | `--color-text-tertiary` |
| 标题字号 | `--font-size-md` |
| 标题颜色 | `--color-text-secondary` |
| 副标题字号 | `--font-size-base` |
| 副标题颜色 | `--color-text-tertiary` |
| 垂直间距 | 图标与标题 `--spacing-lg`，标题与副标题 `--spacing-sm` |

### 9.7 表单 Form

| 属性 | 值 |
|------|-----|
| 标签字号 | `--font-size-base` |
| 标签字重 | `--font-weight-medium` |
| 标签到输入框间距 | `--spacing-xs` |
| 输入框组间距 | `--spacing-lg` |
| 按钮组顶部间距 | `--spacing-xl` |

---

## 10. 布局规范

### 10.1 页面布局

- 移动端（< 768px）：单栏，页面边距 `--spacing-xl`，侧边栏抽屉化
- 桌面端（>= 768px）：侧边栏 + 主内容双栏，侧边栏宽 `--size-sidebar`

### 10.2 导航栏

- 高度：`--size-header`
- 背景：`--color-bg-card`
- 底部边框：1px solid `--color-border-light`
- 标题字号：`--font-size-lg`
- 标题字重：`--font-weight-bold`

### 10.3 安全区适配

- 底部安全区：`padding-bottom: env(safe-area-inset-bottom)`
- 顶部安全区：`padding-top: env(safe-area-inset-top)`

---

## 11. 暗色模式

### 11.1 切换策略

- 使用 `prefers-color-scheme` 媒体查询自动检测
- 同时提供手动切换（存储到 localStorage）
- 根元素添加 `data-theme="dark"` 属性切换

### 11.2 暗色模式适配要点

- 卡片与背景必须有足够对比度（WCAG AA 标准）
- 阴影在暗色模式下加深
- 图片/图标在暗色模式下降低亮度
- 焦点环颜色加亮以确保可见

---

## 12. Z-index 层级

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--z-normal` | 1 | 普通定位元素 |
| `--z-sticky` | 10 | 粘性头部、筛选栏 |
| `--z-drawer` | 100 | 侧边栏抽屉 |
| `--z-overlay` | 200 | 遮罩层 |
| `--z-modal` | 300 | 弹窗 |
| `--z-toast` | 400 | 提示消息 |
