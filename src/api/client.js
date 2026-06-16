import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 45000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('edu_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function login(username, password) {
  const { data } = await api.post('/auth/login', { username, password })
  localStorage.setItem('edu_token', data.access_token)
  localStorage.setItem('edu_user', JSON.stringify(data.user))
  return data
}

export function logout() {
  localStorage.removeItem('edu_token')
  localStorage.removeItem('edu_user')
}

export function currentUser() {
  const raw = localStorage.getItem('edu_user')
  return raw ? JSON.parse(raw) : null
}
