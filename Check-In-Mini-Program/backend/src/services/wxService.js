const axios = require('axios')

/**
 * 调用微信 code2Session 接口
 * @param {string} code - wx.login 获取的临时登录凭证
 * @returns {Object} { openid, sessionKey, unionid }
 */
async function code2Session(code) {
  const { data } = await axios.get('https://api.weixin.qq.com/sns/jscode2session', {
    params: {
      appid: process.env.WX_APPID,
      secret: process.env.WX_SECRET,
      js_code: code,
      grant_type: 'authorization_code'
    }
  })

  if (data.errcode) {
    throw new Error(`WeChat API error: ${data.errcode} ${data.errmsg}`)
  }

  return {
    openid: data.openid,
    sessionKey: data.session_key,
    unionid: data.unionid || null
  }
}

module.exports = { code2Session }
