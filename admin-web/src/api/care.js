import request from './request'

// 服务分类
export function listCategories() {
  return request.get('/admin/care/categories')
}
export function createCategory(data) {
  return request.post('/admin/care/categories', data)
}
export function updateCategory(id, data) {
  return request.put(`/admin/care/categories/${id}`, data)
}
export function deleteCategory(id) {
  return request.delete(`/admin/care/categories/${id}`)
}

// 服务套餐
export function listPackages(categoryId) {
  return request.get('/admin/care/packages', { params: { category_id: categoryId } })
}
export function createPackage(data) {
  return request.post('/admin/care/packages', data)
}
export function updatePackage(id, data) {
  return request.put(`/admin/care/packages/${id}`, data)
}
export function deletePackage(id) {
  return request.delete(`/admin/care/packages/${id}`)
}

// 预约处理
export function listAppointments(params) {
  return request.get('/admin/care/appointments', { params })
}
export function confirmAppointment(id) {
  return request.post(`/admin/care/appointments/${id}/confirm`)
}
export function rejectAppointment(id, reviewComment) {
  return request.post(`/admin/care/appointments/${id}/reject`, { review_comment: reviewComment })
}
export function completeAppointment(id) {
  return request.post(`/admin/care/appointments/${id}/complete`)
}
