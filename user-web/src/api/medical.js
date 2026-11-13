import request from './request'

// 公开医疗信息（游客可访问）
export function listLocations() {
  return request.get('/public/medical/locations')
}

export function listDoctors(locationId) {
  return request.get('/public/medical/doctors', { params: { location_id: locationId } })
}

export function listServices() {
  return request.get('/public/medical/services')
}

export function listSchedules(params) {
  return request.get('/public/medical/schedules', { params })
}

// 我的医疗预约
export function createAppointment(data) {
  return request.post('/user/medical/appointments', data)
}

export function listMyAppointments() {
  return request.get('/user/medical/appointments')
}

export function cancelAppointment(id) {
  return request.post(`/user/medical/appointments/${id}/cancel`)
}
