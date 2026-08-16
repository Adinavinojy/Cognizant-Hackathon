/**
 * api.ts — thin fetch/axios wrapper.
 * Base URL is read from the VITE_API_URL env var (falls back to /api for
 * the Vite dev-server proxy).
 *
 * Usage:
 *   import api from '../lib/api'
 *   const questions = await api.get('/questions?role=swe&topic=databases')
 *   const score = await api.post('/sessions/abc/answers', { answer_text: '...' })
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Request interceptor — attach JWT from localStorage if present
// TODO(auth-pair): Replace localStorage key with a proper auth context/store.
// ---------------------------------------------------------------------------
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---------------------------------------------------------------------------
// Response interceptor — global error handling stub
// TODO(frontend-pair): Handle 401 → redirect to /login, show toast on 5xx.
// ---------------------------------------------------------------------------
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error.response?.status, error.response?.data)
    return Promise.reject(error)
  },
)

export default api
