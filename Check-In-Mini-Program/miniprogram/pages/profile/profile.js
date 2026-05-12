// pages/profile/profile.js
const { request } = require('../../utils/request')
const { logout } = require('../../utils/auth')
const app = getApp()

Page({
  data: {
    loading: true,
    userInfo: {},
    totalCheckinDays: 0,
    consecutiveDays: 0,
    maxConsecutiveDays: 0,
    createdAt: ''
  },

  onLoad() {
    this.loadUserInfo()
  },

  onShow() {
    if (!this.data.loading) {
      this.loadUserInfo()
    }
  },

  /**
   * 加载用户信息
   */
  async loadUserInfo() {
    this.setData({ loading: true })

    const isLoggedIn = await app.ensureLogin()
    if (!isLoggedIn) {
      this.setData({ loading: false })
      return
    }

    try {
      const res = await request({ url: '/api/v1/users/me' })
      const data = res.data

      this.setData({
        userInfo: {
          id: data.id,
          nickName: data.nickName,
          avatarUrl: data.avatarUrl
        },
        totalCheckinDays: data.totalCheckinDays,
        consecutiveDays: data.consecutiveDays,
        maxConsecutiveDays: data.maxConsecutiveDays,
        createdAt: this.formatDate(data.createdAt),
        loading: false
      })
    } catch (err) {
      console.error('加载用户信息失败:', err)
      this.setData({ loading: false })
    }
  },

  /**
   * 退出登录
   */
  onLogout() {
    wx.showModal({
      title: '确认退出',
      content: '退出后需要重新登录',
      confirmColor: '#fa5151',
      success: (res) => {
        if (res.confirm) {
          logout()
          app.globalData.isLoggedIn = false
          app.globalData.userInfo = null

          // 重新登录
          app.ensureLogin().then((success) => {
            if (success) {
              this.loadUserInfo()
            }
          })
        }
      }
    })
  },

  /**
   * 格式化日期
   */
  formatDate(isoString) {
    if (!isoString) return ''
    const date = new Date(isoString)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }
})
