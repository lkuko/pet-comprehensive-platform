import request from './request'

// 医疗点
export function listLocations() {
  return request.get('/admin/medical/locations')
}
export function createLocation(data) {
  return request.post('/admin/medical/locations', data)
}
export function updateLocation(id, data) {
  return request.put(`/admin/medical/locations/${id}`, data)
}
export function deleteLocation(id) {
  return request.delete(`/admin/medical/locations/${id}`)
}

// 医生
export function listDoctors(locationId) {
  return request.get('/admin/medical/doctors', { params: { location_id: locationId } })
}
export function createDoctor(data) {
  return request.post('/admin/medical/doctors', data)
}
export function updateDoctor(id, data) {
  return request.put(`/admin/medical/doctors/${id}`, data)
}
export function deleteDoctor(id) {
  return request.delete(`/admin/medical/doctors/${id}`)
}

// 医疗项目
export function listServices() {
  return request.get('/admin/medical/services')
}
export function createService(data) {
  return request.post('/admin/medical/services', data)
}
export function updateService(id, data) {
  return request.put(`/admin/medical/services/${id}`, data)
}
export function deleteService(id) {
  return request.delete(`/admin/medical/services/${id}`)
}

// 排班
export function listSchedules(params) {
  return request.get('/admin/medical/schedules', { params })
}
export function createSchedule(data) {
  return request.post('/admin/medical/schedules', data)
}
export function updateSchedule(id, data) {
  return request.put(`/admin/medical/schedules/${id}`, data)
}
export function deleteSchedule(id) {
  return request.delete(`/admin/medical/schedules/${id}`)
}

// 预约处理
export function listAppointments(params) {
  return request.get('/admin/medical/appointments', { params })
}
export function confirmAppointment(id) {
  return request.post(`/admin/medical/appointments/${id}/confirm`)
}
export function rejectAppointment(id, reviewComment) {
  return request.post(`/admin/medical/appointments/${id}/reject`, { review_comment: reviewComment })
}
export function completeAppointment(id) {
  return request.post(`/admin/medical/appointments/${id}/complete`)
}
