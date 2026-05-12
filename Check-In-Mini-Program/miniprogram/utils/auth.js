// utils/auth.js
// 登录态管理

const { request } = require('./request')

/**
 * 微信登录
 */
async function login() {
  try {
    // 1. 获取 code
    const loginRes = await wx.login()
    if (!loginRes.code) {
      throw new Error('wx.login 失败')
    }

    // 2. 发送 code 到后端换取 token
    const res = await request({
      url: '/api/v1/auth/wx-login',
      method: 'POST',
      data: { code: loginRes.code }
    })

    // 3. 存储 token 和用户信息
    wx.setStorageSync('token', res.data.token)
    wx.setStorageSync('userInfo', res.data.userInfo)

    return res.data
  } catch (err) {
    console.error('登录失败', err)
    throw err
  }
}

/**
 * 检查登录态
 */
function checkLogin() {
  return !!wx.getStorageSync('token')
}

/**
 * 退出登录
 */
function logout() {
  wx.removeStorageSync('token')
  wx.removeStorageSync('userInfo')
}

module.exports = { login, checkLogin, logout }
