// app.js
const { login, checkLogin } = require('./utils/auth')

App({
  globalData: {
    userInfo: null,
    isLoggedIn: false
  },

  onLaunch() {
    // 检查登录态
    if (checkLogin()) {
      this.globalData.isLoggedIn = true
      this.globalData.userInfo = wx.getStorageSync('userInfo')
    }
  },

  /**
   * 确保已登录
   */
  async ensureLogin() {
    if (checkLogin()) {
      return true
    }

    try {
      const result = await login()
      this.globalData.isLoggedIn = true
      this.globalData.userInfo = result.userInfo
      return true
    } catch (err) {
      console.error('登录失败:', err)
      return false
    }
  }
})
