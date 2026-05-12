// pages/index/index.js
const { request } = require('../../utils/request')
const app = getApp()

Page({
  data: {
    loading: true,
    isCheckedIn: false,
    consecutiveDays: 0,
    maxConsecutiveDays: 0,
    todayDate: '',
    monthlyCheckins: 0,
    monthlyTotal: 0,
    checkinRate: '0%'
  },

  onLoad() {
    this.initData()
  },

  onShow() {
    // 每次显示页面时刷新状态
    if (!this.data.loading) {
      this.loadCheckinStatus()
    }
  },

  async initData() {
    const isLoggedIn = await app.ensureLogin()
    if (!isLoggedIn) {
      wx.showToast({ title: '登录失败', icon: 'none' })
      return
    }

    this.setData({ todayDate: this.formatTodayDate() })
    await Promise.all([
      this.loadCheckinStatus(),
      this.loadMonthlyStats()
    ])
  },

  /**
   * 加载今日打卡状态
   */
  async loadCheckinStatus() {
    try {
      const res = await request({ url: '/api/v1/checkin/status' })
      const { isCheckedIn, consecutiveDays, maxConsecutiveDays } = res.data

      this.setData({
        isCheckedIn,
        consecutiveDays,
        maxConsecutiveDays,
        loading: false
      })
    } catch (err) {
      console.error('加载打卡状态失败:', err)
      this.setData({ loading: false })
    }
  },

  /**
   * 加载本月统计
   */
  async loadMonthlyStats() {
    try {
      const now = new Date()
      const year = now.getFullYear()
      const month = now.getMonth() + 1
      const daysInMonth = new Date(year, month, 0).getDate()

      const res = await request({
        url: `/api/v1/checkin/history?year=${year}&month=${month}`
      })

      const monthlyCheckins = res.data.total
      this.setData({
        monthlyCheckins,
        monthlyTotal: daysInMonth,
        checkinRate: daysInMonth > 0
          ? Math.round((monthlyCheckins / daysInMonth) * 100) + '%'
          : '0%'
      })
    } catch (err) {
      console.error('加载月度统计失败:', err)
    }
  },

  /**
   * 点击打卡
   */
  async onCheckin() {
    if (this.data.isCheckedIn) {
      wx.showToast({ title: '今日已打卡', icon: 'none' })
      return
    }

    try {
      const res = await request({
        url: '/api/v1/checkin',
        method: 'POST'
      })

      const { consecutiveDays, maxConsecutiveDays } = res.data

      this.setData({
        isCheckedIn: true,
        consecutiveDays,
        maxConsecutiveDays,
        monthlyCheckins: this.data.monthlyCheckins + 1
      })

      wx.showToast({ title: '打卡成功', icon: 'success' })

      // 打卡成功动画效果
      this.animateCheckin()
    } catch (err) {
      if (err.error === 'already_checked_in') {
        this.setData({ isCheckedIn: true })
        wx.showToast({ title: '今日已打卡', icon: 'none' })
      }
    }
  },

  /**
   * 打卡成功动画
   */
  animateCheckin() {
    // 简单的缩放动画效果
    this.setData({ animating: true })
    setTimeout(() => {
      this.setData({ animating: false })
    }, 300)
  },

  /**
   * 格式化今日日期
   */
  formatTodayDate() {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    const weekDays = ['日', '一', '二', '三', '四', '五', '六']
    const weekDay = weekDays[now.getDay()]
    return `${year}年${month}月${day}日 星期${weekDay}`
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: `我已连续打卡${this.data.consecutiveDays}天，快来一起打卡吧！`,
      path: '/pages/index/index'
    }
  }
})
