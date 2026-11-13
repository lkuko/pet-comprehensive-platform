import request from './request'

// 公开服务信息（游客可访问）
export function listCategories(serviceType) {
  return request.get('/public/care/categories', { params: { service_type: serviceType } })
}

export function listPackages(categoryId) {
  return request.get('/public/care/packages', { params: { category_id: categoryId } })
}

// 我的洗护/寄养预约
export function createAppointment(data) {
  return request.post('/user/care/appointments', data)
}

export function listMyAppointments() {
  return request.get('/user/care/appointments')
}

export function cancelAppointment(id) {
  return request.post(`/user/care/appointments/${id}/cancel`)
}
