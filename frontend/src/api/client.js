// frontend/src/api/client.js

import axios from 'axios'

const BASE_URL = 'https://razorpay-agentic-checkout.onrender.com'

// Create axios instance
const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach session token to every request
client.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('session_token')
  if (token) {
    config.headers['X-Session-Token'] = token
  }
  return config
})

// Handle session expiry globally
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 410) {
      // Session expired — clear storage
      sessionStorage.clear()
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export const api = {
  // Session
  createSession: () =>
    client.post('/api/session/create'),

  // Chat
  sendMessage: (message, sessionId) =>
    client.post('/api/chat', { message, session_id: sessionId }),

  // Audit
  getAuditLog: (sessionId) =>
    client.get(`/api/audit/${sessionId}`),

  // Orders
  getOrders: (sessionId) =>
    client.get(`/api/orders/${sessionId}`),
}

export default client