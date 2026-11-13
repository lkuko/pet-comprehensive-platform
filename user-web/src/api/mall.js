import request from './request'

// 公开商城（游客可访问）
export function listCategories() {
  return request.get('/public/mall/categories')
}

export function listProducts(params) {
  return request.get('/public/mall/products', { params })
}

// 购物车
export function listCart() {
  return request.get('/user/cart')
}

export function addToCart(data) {
  return request.post('/user/cart', data)
}

export function updateCartItem(productId, quantity) {
  return request.put(`/user/cart/${productId}`, { quantity })
}

export function removeCartItem(productId) {
  return request.delete(`/user/cart/${productId}`)
}

export function clearCart() {
  return request.delete('/user/cart')
}

// 订单
export function checkout(data) {
  return request.post('/user/orders', data)
}

export function listOrders() {
  return request.get('/user/orders')
}

export function payOrder(id) {
  return request.post(`/user/orders/${id}/pay`)
}

export function cancelOrder(id) {
  return request.post(`/user/orders/${id}/cancel`)
}
