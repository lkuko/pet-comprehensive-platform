import request from './request'

export function getSummary() {
  return request.get('/admin/dashboard/summary')
}
