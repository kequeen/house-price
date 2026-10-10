import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })
export default api
export const errorMessage = error => error.response?.data?.detail || error.message || '请求失败'
