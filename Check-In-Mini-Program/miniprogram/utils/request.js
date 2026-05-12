// utils/request.js
// 统一的 wx.request 封装

const ENV = require('../config/env.js')

/**
 * 发起 HTTP 请求
 * @param {Object} options - 请求选项
 * @param {string} options.url - 请求路径（不含基础 URL）
 * @param {string} options.method - 请求方法，默认 GET
 * @param {Object} options.data - 请求数据
 * @param {Object} options.header - 额外请求头
 * @returns {Promise} 响应数据
 */
const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token')

    wx.request({
      url: `${ENV.API_BASE}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header
      },
      success(res) {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // token 过期，清除登录态
          wx.removeStorageSync('token')
          wx.removeStorageSync('userInfo')
          wx.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
          reject(new Error('登录已过期'))
        } else {
          const errMsg = res.data?.message || '请求失败'
          wx.showToast({ title: errMsg, icon: 'none' })
          reject(res.data)
        }
      },
      fail(err) {
        wx.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      }
    })
  })
}

module.exports = { request }
