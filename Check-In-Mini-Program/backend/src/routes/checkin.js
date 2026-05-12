const Router = require('koa-router')
const { checkin, getStatus, getHistory } = require('../controllers/checkinController')

const router = new Router({ prefix: '/api/v1/checkin' })

// POST /api/v1/checkin
router.post('/', checkin)

// GET /api/v1/checkin/status
router.get('/status', getStatus)

// GET /api/v1/checkin/history
router.get('/history', getHistory)

module.exports = router
