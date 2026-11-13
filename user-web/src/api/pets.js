import request from './request'

// 我的宠物档案 API
export function listPets() {
  return request.get('/user/pets')
}

export function createPet(data) {
  return request.post('/user/pets', data)
}

export function getPet(id) {
  return request.get(`/user/pets/${id}`)
}

export function updatePet(id, data) {
  return request.put(`/user/pets/${id}`, data)
}

export function deletePet(id) {
  return request.delete(`/user/pets/${id}`)
}
