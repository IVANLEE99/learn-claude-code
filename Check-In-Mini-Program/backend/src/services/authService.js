const { PrismaClient } = require('@prisma/client')
const prisma = new PrismaClient()

/**
 * 根据 openid 查找用户
 */
async function findByOpenid(openid) {
  return prisma.user.findUnique({
    where: { openid }
  })
}

/**
 * 创建用户
 */
async function create(data) {
  return prisma.user.create({
    data: {
      openid: data.openid,
      unionid: data.unionid || null,
      nickName: data.nickName || '微信用户',
      avatarUrl: data.avatarUrl || ''
    }
  })
}

/**
 * 更新用户信息
 */
async function update(userId, data) {
  return prisma.user.update({
    where: { id: BigInt(userId) },
    data: {
      nickName: data.nickName,
      avatarUrl: data.avatarUrl
    }
  })
}

/**
 * 根据 ID 查找用户
 */
async function findById(userId) {
  return prisma.user.findUnique({
    where: { id: BigInt(userId) }
  })
}

module.exports = { findByOpenid, create, update, findById }
