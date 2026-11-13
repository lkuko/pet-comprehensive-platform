import request from './request'

// 用户端认证与个人资料 API
export function register(data) {
  return request.post('/user/auth/register', data)
}

export function login(data) {
  return request.post('/user/auth/login', data)
}

export function getProfile() {
  return request.get('/user/profile')
}

export function updateProfile(data) {
  return request.put('/user/profile', data)
}
