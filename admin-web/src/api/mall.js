import request from './request'

// 商品分类
export function listCategories() {
  return request.get('/admin/mall/categories')
}
export function createCategory(data) {
  return request.post('/admin/mall/categories', data)
}
export function updateCategory(id, data) {
  return request.put(`/admin/mall/categories/${id}`, data)
}
export function deleteCategory(id) {
  return request.delete(`/admin/mall/categories/${id}`)
}

// 商品
export function listProducts(categoryId) {
  return request.get('/admin/mall/products', { params: { category_id: categoryId } })
}
export function createProduct(data) {
  return request.post('/admin/mall/products', data)
}
export function updateProduct(id, data) {
  return request.put(`/admin/mall/products/${id}`, data)
}
export function deleteProduct(id) {
  return request.delete(`/admin/mall/products/${id}`)
}

// 订单处理
export function listOrders(params) {
  return request.get('/admin/mall/orders', { params })
}
export function shipOrder(id) {
  return request.post(`/admin/mall/orders/${id}/ship`)
}
export function completeOrder(id) {
  return request.post(`/admin/mall/orders/${id}/complete`)
}
