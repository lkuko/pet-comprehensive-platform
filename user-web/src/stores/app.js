import { defineStore } from 'pinia'

// Day 1 占位 store；Day 2 认证落地后扩展登录用户、Token 状态
export const useAppStore = defineStore('app', {
  state: () => ({
    appName: '智能宠物综合服务平台'
  })
})
