import request from './request'

// 公开端领养相关 API（游客可访问）
export function listPets(params) {
  return request.get('/public/adoption-pets', { params })
}

export function getPet(id) {
  return request.get(`/public/adoption-pets/${id}`)
}

export function listCategories() {
  return request.get('/public/pet-categories')
}
