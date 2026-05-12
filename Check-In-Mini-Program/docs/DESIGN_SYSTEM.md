# 微信小程序设计规范
> 技术栈: 原生开发
> 设计基准屏幕: 750rpx（微信标准设计稿宽度）
> 版本: 1.0
> 项目: Check-In-Mini-Program（每日打卡签到小程序）
> 目标用户: 18-45岁，简洁清新风格

---

## 一、颜色体系

### 品牌色

打卡签到类应用，选用清新蓝绿色作为主色调，传达健康、坚持、活力的品牌感受。

```css
--color-primary: #1AAD7A;          /* 主要操作、打卡按钮、强调 */
--color-primary-light: #E8F8F2;    /* 主色背景、标签、成功提示背景 */
--color-primary-dark: #129066;     /* 按压状态、打卡成功深色 */
```

### 功能色（语义色）

```css
--color-success: #07c160;   /* 微信绿，打卡成功、完成 */
--color-warning: #fa9d3b;   /* 警告、断签提醒 */
--color-danger:  #fa5151;   /* 删除、错误 */
--color-info:    #10aeff;   /* 提示、信息 */
```

### 强调色（数字展示）

```css
--color-highlight: #FF6B35;  /* 连续打卡天数、激励数字 */
```

### 中性色（文字和背景）

```css
/* 文字 */
--color-text-primary:   #181818;   /* 主要文字，标题 */
--color-text-secondary: #999999;   /* 次要文字，描述 */
--color-text-tertiary:  #cccccc;   /* 辅助文字，占位符 */
--color-text-disabled:  #cccccc;   /* 禁用状态 */

/* 背景 */
--color-bg-page:        #f6f6f6;   /* 页面背景（微信标准灰） */
--color-bg-card:        #ffffff;   /* 卡片背景 */
--color-bg-input:       #f5f5f5;   /* 输入框背景 */

/* 分割线 */
--color-border:         #e5e5e5;   /* 普通分割线 */
```

### 颜色使用规则

- 品牌色 #1AAD7A 贯穿打卡相关操作（按钮、成功状态、连续天数背景）
- 强调色 #FF6B35 用于连续打卡天数等激励性数字展示
- 背景使用 #f6f6f6（微信标准页面底色），卡片用白色
- 文字颜色只用上方定义的 4 级
- 功能色优先使用微信标准色值，用户更容易理解

---

## 二、字体体系

### rpx 单位说明

```css
/* 微信小程序使用 rpx 响应式单位 */
/* 750rpx = 屏幕宽度 */
/* 设计稿基于 750px 宽度时：1px = 1rpx */
```

### 字号梯度

```css
--font-size-xs:   20rpx;    /* 辅助信息、时间戳、标签 */
--font-size-sm:   24rpx;    /* 次要文字、列表描述 */
--font-size-md:   28rpx;    /* 正文、输入框（最小可读字号） */
--font-size-lg:   32rpx;    /* 卡片标题、重要信息 */
--font-size-xl:   36rpx;    /* 页面标题 */
--font-size-2xl:  44rpx;    /* 大标题、数字展示 */
--font-size-3xl:  72rpx;    /* 连续打卡天数大数字 */
```

### 行高规则

```css
--line-height-tight:  1.25;   /* 标题类 */
--line-height-normal: 1.5;    /* 正文 */
--line-height-loose:  1.75;   /* 多行描述 */
```

### 字重

```css
--font-weight-normal:  400;   /* 正文 */
--font-weight-medium:  500;   /* 次要强调 */
--font-weight-bold:    700;   /* 标题、数字 */
```

### 字体使用规则

- 小程序正文最小字号 24rpx（低于此值难以阅读）
- 一个页面字号种类不超过 4 种
- 小程序不支持自定义字体文件（2MB 包大小限制），使用系统字体
- 连续打卡天数使用 --font-size-3xl (72rpx) 突出展示

---

## 三、间距体系

### 基础单位：8rpx

```css
--spacing-1:  8rpx;    /* 极小间距 */
--spacing-2:  16rpx;   /* 紧凑间距，列表项内部 */
--spacing-3:  24rpx;   /* 小间距，卡片内部元素 */
--spacing-4:  32rpx;   /* 标准间距，卡片内边距 */
--spacing-5:  40rpx;   /* 中等间距 */
--spacing-6:  48rpx;   /* 大间距，区块间隔 */
--spacing-8:  64rpx;   /* 超大间距 */
```

### 常用场景规范

```css
/* 页面内边距 */
--page-padding: 32rpx;

/* 卡片内边距 */
--card-padding: 32rpx;

/* 列表项高度（可点击区域最小 88rpx，满足手指点击） */
--list-item-min-height: 88rpx;

/* 底部安全区 */
--safe-area-bottom: env(safe-area-inset-bottom);
```

---

## 四、圆角体系

```css
--radius-sm:   8rpx;    /* 标签、小徽章 */
--radius-md:   16rpx;   /* 卡片、输入框 */
--radius-lg:   24rpx;   /* 弹窗 */
--radius-xl:   32rpx;   /* 大卡片 */
--radius-full: 50%;     /* 圆形头像、打卡按钮 */
```

---

## 五、阴影体系

```css
--shadow-sm:  0 2rpx 6rpx rgba(0, 0, 0, 0.08);   /* 卡片 */
--shadow-md:  0 8rpx 24rpx rgba(0, 0, 0, 0.10);  /* 浮层 */
--shadow-lg:  0 16rpx 48rpx rgba(0, 0, 0, 0.12); /* 弹窗 */
```

> 注意：微信小程序中阴影使用较少，扁平化设计更符合微信风格。打卡按钮使用轻微阴影增加层次感。

---

## 六、核心页面设计规范

### 6.1 首页（index）— 打卡页

**布局结构：**
```
┌──────────────────────────┐
│      NavigationBar       │  88rpx
├──────────────────────────┤
│                          │
│    连续打卡天数（大数字）  │  --font-size-3xl, --color-highlight
│    "天" 单位文字          │  --font-size-md, --color-text-secondary
│                          │
│   ┌──────────────────┐   │
│   │                  │   │
│   │    打卡按钮       │   │  240rpx 圆形, --color-primary
│   │   （圆形大按钮）  │   │
│   │                  │   │
│   └──────────────────┘   │
│                          │
│   今日日期               │  --font-size-sm, --color-text-secondary
│   打卡状态提示           │  --font-size-md
│                          │
│   ┌──────────────────┐   │
│   │ 本月打卡统计卡片  │   │  --color-bg-card, --radius-md
│   │ 已打卡 X / 31 天  │   │
│   └──────────────────┘   │
│                          │
└──────────────────────────┘
```

**打卡按钮规范：**
- 尺寸：240rpx x 240rpx，圆形（border-radius: 50%）
- 未打卡状态：--color-primary 背景，白色文字"打卡"
- 已打卡状态：--color-primary-light 背景，--color-primary 文字"已打卡"，带勾选图标
- 按压状态：--color-primary-dark
- 阴影：--shadow-md
- 最小可点击区域：已满足 88rpx 要求

**连续天数展示：**
- 数字：--font-size-3xl (72rpx)，--color-highlight，--font-weight-bold
- "连续打卡 X 天" 文字：--font-size-md，--color-text-secondary

### 6.2 打卡记录页（history）— 日历视图

**布局结构：**
```
┌──────────────────────────┐
│      NavigationBar       │
├──────────────────────────┤
│  ◀  2026年5月  ▶         │  月份切换
├──────────────────────────┤
│  日  一  二  三  四  五  六│  星期头
│  ..  ..  ..  01  02  03  04│
│  05  06  [07] [08] [09] ..│  已打卡日期高亮
│  ..  ..  ..  ..  ..  ..  ..│
├──────────────────────────┤
│  本月打卡统计             │
│  已打卡 12 天 / 共 31 天  │
│  打卡率 38.7%            │
└──────────────────────────┘
```

**日历组件规范：**
- 日期格子：88rpx x 88rpx
- 今日日期：--color-primary 边框
- 已打卡日期：--color-primary-light 背景，--color-primary 文字
- 未打卡日期：默认样式
- 未来日期：--color-text-disabled
- 月份切换按钮：--font-size-lg

### 6.3 个人中心页（profile）

**布局结构：**
```
┌──────────────────────────┐
│      NavigationBar       │
├──────────────────────────┤
│                          │
│      用户头像（圆形）     │  128rpx x 128rpx
│      用户昵称            │  --font-size-xl, --font-weight-bold
│                          │
│  ┌──────────────────────┐│
│  │ 总打卡    连续    最高││  三列统计卡片
│  │  45天     7天     15天││
│  └──────────────────────┘│
│                          │
│  ┌──────────────────────┐│
│  │ 退出登录              ││  --color-danger
│  └──────────────────────┘│
│                          │
└──────────────────────────┘
```

**统计卡片规范：**
- 三列等分，白色背景，--radius-md 圆角
- 数字：--font-size-2xl，--color-primary，--font-weight-bold
- 标签：--font-size-xs，--color-text-secondary
- 卡片间距：--spacing-3

---

## 七、微信原生组件适配规范

### NavigationBar

```
高度：88rpx（含状态栏）
背景：--color-bg-card（白色）
标题：--font-size-lg，--color-text-primary，居中
使用默认导航栏，无需自定义
```

### TabBar

```
高度：98rpx + safe-area-bottom
图标：48rpx x 48rpx
文字：--font-size-xs
选中色：--color-primary
未选中色：--color-text-tertiary
页面：首页、打卡记录、个人中心
```

### 弹窗 / Modal

```
宽度：580rpx
圆角：--radius-lg
遮罩：rgba(0, 0, 0, 0.5)
```

### 空状态

```
图标：200rpx 高，主色调淡色
标题：--font-size-lg，--color-text-secondary
描述：--font-size-sm，--color-text-tertiary
```

---

## 八、动效规范

```css
/* 过渡时长 */
--duration-fast:   150ms;   /* 按钮状态切换 */
--duration-normal: 250ms;   /* 元素显示/隐藏 */
--duration-slow:   350ms;   /* 页面切换 */

/* 缓动函数 */
--ease-out:  cubic-bezier(0.0, 0.0, 0.2, 1);
--ease-in:   cubic-bezier(0.4, 0.0, 1, 1);
```

**打卡按钮动效：**
- 点击时：缩放至 0.95，150ms
- 打卡成功：弹跳动画（scale 1.0 -> 1.1 -> 1.0），300ms
- 状态切换：背景色渐变，250ms

> 注意：小程序动画优先使用 wx.createAnimation 或 CSS transition，避免复杂动画影响性能。

---

## 九、暗色模式（跟随微信）

微信小程序支持跟随系统暗色模式：

```css
@media (prefers-color-scheme: dark) {
  page {
    --color-bg-page:        #1f1f1f;
    --color-bg-card:        #2c2c2c;
    --color-text-primary:   #ffffff;
    --color-text-secondary: #8c8c8c;
    --color-border:         #3d3d3d;
    --color-primary:        #26c488;
    --color-primary-light:  #1a3d2e;
    --color-highlight:      #FF8C5A;
  }
}
```

需在 app.json 中配置：
```json
{
  "darkmode": true,
  "themeLocation": "theme.json"
}
```

---

## 十、完成标志

docs/DESIGN_SYSTEM.md 已创建，包含：
- 品牌色、功能色、中性色完整定义
- 字体体系（7级字号梯度）
- 间距体系（8rpx 基础单位）
- 圆角、阴影体系
- 3 个核心页面的布局设计规范
- 打卡按钮交互规范
- 微信原生组件适配规范
- 动效规范
- 暗色模式适配
