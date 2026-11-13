import request from './request'

// 用户端领养申请 API
export function createApplication(data) {
  return request.post('/user/adoption-applications', data)
}

export function listMyApplications() {
  return request.get('/user/adoption-applications')
}

export function getMyApplication(id) {
  return request.get(`/user/adoption-applications/${id}`)
}

export function cancelApplication(id) {
  return request.post(`/user/adoption-applications/${id}/cancel`)
}
