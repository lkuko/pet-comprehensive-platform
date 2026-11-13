import request from './request'

// 管理端认证 API
export function adminLogin(data) {
  return request.post('/admin/auth/login', data)
}
