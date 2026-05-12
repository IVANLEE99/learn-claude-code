// config/env.js
// 环境配置 - API 地址可配置，禁止硬编码

const ENV = {
  development: {
    API_BASE: 'http://localhost:3000'
  },
  production: {
    API_BASE: 'https://api.your-domain.com'
  }
}

// 小程序环境判断
const accountInfo = wx.getAccountInfoSync()
const envVersion = accountInfo.miniProgram.envVersion || 'develop'
const env = envVersion === 'release' ? 'production' : 'development'

module.exports = ENV[env]
