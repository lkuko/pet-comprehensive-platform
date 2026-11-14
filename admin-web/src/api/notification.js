import request from './request'

export function listNotifications(params) {
  return request.get('/admin/notifications', { params })
}

export function unreadCount() {
  return request.get('/admin/notifications/unread-count')
}

export function markRead(id) {
  return request.post(`/admin/notifications/${id}/read`)
}

export function markAllRead() {
  return request.post('/admin/notifications/read-all')
}
