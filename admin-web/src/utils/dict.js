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

export const MEDICAL_APP_STATUS = {
  PENDING_CONFIRMATION: '待确认',
  CONFIRMED: '已确认',
  REJECTED: '已拒绝',
  CANCELLED: '已取消',
  COMPLETED: '已完成'
}

export const MEDICAL_APP_STATUS_TAG = {
  PENDING_CONFIRMATION: 'warning',
  CONFIRMED: 'success',
  REJECTED: 'danger',
  CANCELLED: 'info',
  COMPLETED: 'info'
}

export const ENABLE_STATUS = {
  ACTIVE: '启用',
  INACTIVE: '停用'
}

export const ENABLE_STATUS_TAG = {
  ACTIVE: 'success',
  INACTIVE: 'info'
}

export const SERVICE_TYPE = {
  GROOMING: '洗护美容',
  BOARDING: '寄养'
}

export const CARE_APP_STATUS = {
  PENDING_CONFIRMATION: '待确认',
  CONFIRMED: '已确认',
  REJECTED: '已拒绝',
  CANCELLED: '已取消',
  COMPLETED: '已完成'
}

export const CARE_APP_STATUS_TAG = {
  PENDING_CONFIRMATION: 'warning',
  CONFIRMED: 'success',
  REJECTED: 'danger',
  CANCELLED: 'info',
  COMPLETED: 'info'
}

export const ORDER_STATUS = {
  PENDING_PAYMENT: '待支付',
  PAID: '待发货',
  SHIPPED: '已发货',
  COMPLETED: '已完成',
  CANCELLED: '已取消',
  CLOSED: '已关闭'
}

export const ORDER_STATUS_TAG = {
  PENDING_PAYMENT: 'warning',
  PAID: 'primary',
  SHIPPED: 'success',
  COMPLETED: 'info',
  CANCELLED: 'info',
  CLOSED: 'info'
}

export const BUSINESS_TYPE = {
  ADOPTION_APPLICATION: '领养申请',
  MEDICAL_APPOINTMENT: '医疗预约',
  SERVICE_BOOKING: '洗护/寄养预约',
  PRODUCT_ORDER: '商品订单'
}

export const BUSINESS_TYPE_TAG = {
  ADOPTION_APPLICATION: 'warning',
  MEDICAL_APPOINTMENT: 'success',
  SERVICE_BOOKING: 'primary',
  PRODUCT_ORDER: 'info'
}
