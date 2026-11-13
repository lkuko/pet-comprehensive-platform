// 前后端字段值 → 中文展示映射
export const GENDER = {
  MALE: '公',
  FEMALE: '母',
  UNKNOWN: '未知'
}

export const ADOPT_STATUS = {
  DRAFT: '草稿',
  AVAILABLE: '可领养',
  OFFLINE: '已下架',
  ADOPTED: '已领养'
}

export const ADOPT_STATUS_TAG = {
  DRAFT: 'info',
  AVAILABLE: 'success',
  OFFLINE: 'warning',
  ADOPTED: 'danger'
}

export const APP_STATUS = {
  PENDING: '待审核',
  APPROVED: '已通过',
  REJECTED: '已拒绝',
  CANCELLED: '已撤回',
  CLOSED: '已关闭'
}

export const APP_STATUS_TAG = {
  PENDING: 'warning',
  APPROVED: 'success',
  REJECTED: 'danger',
  CANCELLED: 'info',
  CLOSED: 'info'
}
