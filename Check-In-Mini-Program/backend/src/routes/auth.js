const Router = require('koa-router')
const { wxLogin } = require('../controllers/authController')

const router = new Router({ prefix: '/api/v1/auth' })

// POST /api/v1/auth/wx-login
router.post('/wx-login', wxLogin)

module.exports = router
