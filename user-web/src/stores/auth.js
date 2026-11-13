import { defineStore } from 'pinia'
import * as authApi from '../api/auth'

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
    _persist(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    async login(payload) {
      const res = await authApi.login(payload)
      this._persist(res.data.token, res.data.user)
      return res
    },
    async register(payload) {
      const res = await authApi.register(payload)
      this._persist(res.data.token, res.data.user)
      return res
    },
    async fetchProfile() {
      const res = await authApi.getProfile()
      this.user = res.data
      localStorage.setItem(USER_KEY, JSON.stringify(res.data))
      return res
    },
    async updateProfile(payload) {
      const res = await authApi.updateProfile(payload)
      this.user = res.data
      localStorage.setItem(USER_KEY, JSON.stringify(res.data))
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
