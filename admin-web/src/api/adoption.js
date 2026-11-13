import request from './request'

// 管理端领养宠物维护 API
export function listPets(params) {
  return request.get('/admin/adoption-pets', { params })
}

export function getPet(id) {
  return request.get(`/admin/adoption-pets/${id}`)
}

export function createPet(data) {
  return request.post('/admin/adoption-pets', data)
}

export function updatePet(id, data) {
  return request.put(`/admin/adoption-pets/${id}`, data)
}

export function updateStatus(id, status) {
  return request.patch(`/admin/adoption-pets/${id}/status`, { status })
}

export function listCategories() {
  return request.get('/public/pet-categories')
}
