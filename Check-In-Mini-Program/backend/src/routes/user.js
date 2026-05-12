const Router = require('koa-router')
const { getMe } = require('../controllers/userController')

const router = new Router({ prefix: '/api/v1/users' })

// GET /api/v1/users/me
router.get('/me', getMe)

module.exports = router
