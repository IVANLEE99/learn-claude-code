// pages/history/history.js
const { request } = require('../../utils/request')
const app = getApp()

Page({
  data: {
    loading: true,
    year: 0,
    month: 0,
    weekdays: ['日', '一', '二', '三', '四', '五', '六'],
    emptyDays: [],
    days: [],
    totalCheckins: 0,
    totalDays: 0,
    checkinRate: '0%'
  },

  onLoad() {
    const now = new Date()
    this.setData({
      year: now.getFullYear(),
      month: now.getMonth() + 1
    })
    this.loadCalendar()
  },

  onShow() {
    if (!this.data.loading) {
      this.loadCalendar()
    }
  },

  /**
   * 加载日历数据
   */
  async loadCalendar() {
    this.setData({ loading: true })

    const isLoggedIn = await app.ensureLogin()
    if (!isLoggedIn) {
      this.setData({ loading: false })
      return
    }

    try {
      const { year, month } = this.data

      // 获取打卡记录
      const res = await request({
        url: `/api/v1/checkin/history?year=${year}&month=${month}`
      })

      const checkinDates = new Set(
        res.data.list.map(item => item.checkinDate)
      )

      // 生成日历数据
      const firstDay = new Date(year, month - 1, 1).getDay() // 本月1日是星期几
      const daysInMonth = new Date(year, month, 0).getDate() // 本月天数
      const today = new Date()
      const todayStr = this.formatDate(today)

      const emptyDays = Array(firstDay).fill(null)
      const days = []

      for (let i = 1; i <= daysInMonth; i++) {
        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(i).padStart(2, '0')}`
        const date = new Date(year, month - 1, i)
        const isFuture = date > today && dateStr !== todayStr

        days.push({
          day: i,
          date: dateStr,
          isToday: dateStr === todayStr,
          isCheckedIn: checkinDates.has(dateStr),
          isFuture
        })
      }

      this.setData({
        emptyDays,
        days,
        totalCheckins: res.data.total,
        totalDays: daysInMonth,
        checkinRate: daysInMonth > 0
          ? Math.round((res.data.total / daysInMonth) * 100) + '%'
          : '0%',
        loading: false
      })
    } catch (err) {
      console.error('加载日历数据失败:', err)
      this.setData({ loading: false })
    }
  },

  /**
   * 上个月
   */
  onPrevMonth() {
    let { year, month } = this.data
    month--
    if (month < 1) {
      month = 12
      year--
    }
    this.setData({ year, month })
    this.loadCalendar()
  },

  /**
   * 下个月
   */
  onNextMonth() {
    let { year, month } = this.data
    const now = new Date()

    // 不允许查看未来月份
    if (year === now.getFullYear() && month >= now.getMonth() + 1) {
      return
    }

    month++
    if (month > 12) {
      month = 1
      year++
    }
    this.setData({ year, month })
    this.loadCalendar()
  },

  /**
   * 格式化日期
   */
  formatDate(date) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }
})
