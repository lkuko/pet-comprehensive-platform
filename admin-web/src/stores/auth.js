import { defineStore } from 'pinia'
import { adminLogin } from '../api/auth'

const TOKEN_KEY = 'token'
const USER_KEY = 'user'

function readUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: readUser()
  }),
  getters: {
    isLoggedIn: (state) => !!state.token
  },
  actions: {
    async login(payload) {
      const res = await adminLogin(payload)
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem(TOKEN_KEY, res.data.token)
      localStorage.setItem(USER_KEY, JSON.stringify(res.data.user))
      return res
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  }
})
