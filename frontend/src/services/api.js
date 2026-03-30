import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

// Track if we're currently refreshing to avoid multiple refresh requests
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Interceptor de response: en 401 intentar refresh, luego redirect
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Check if this is a 401 error
    if (error.response?.status === 401) {
      const url = originalRequest?.url || ''

      // Don't attempt refresh for auth endpoints
      const isAuthEndpoint = url.includes('/auth/login') ||
                            url.includes('/auth/refresh') ||
                            url.includes('/auth/logout')

      if (isAuthEndpoint) {
        return Promise.reject(error)
      }

      // Avoid infinite loops
      if (originalRequest._retry) {
        // Refresh failed, clear tokens and redirect to login
        setAuthToken(null)
        localStorage.removeItem('kc_access_token')
        localStorage.removeItem('kc_refresh_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(token => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch(err => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      // Attempt to refresh the token
      const refreshToken = localStorage.getItem('kc_refresh_token')

      if (!refreshToken) {
        // No refresh token, redirect to login
        setAuthToken(null)
        localStorage.removeItem('kc_access_token')
        localStorage.removeItem('kc_refresh_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        const { data } = await api.post('/auth/refresh', null, {
          params: { refresh_token: refreshToken },
        })

        const newAccessToken = data.access_token
        const newRefreshToken = data.refresh_token || refreshToken

        // Update tokens
        localStorage.setItem('kc_access_token', newAccessToken)
        localStorage.setItem('kc_refresh_token', newRefreshToken)
        setAuthToken(newAccessToken)

        // Process queued requests
        processQueue(null, newAccessToken)

        // Retry original request with new token
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
        return api(originalRequest)

      } catch (refreshError) {
        // Refresh failed, clear everything and redirect
        processQueue(refreshError, null)
        setAuthToken(null)
        localStorage.removeItem('kc_access_token')
        localStorage.removeItem('kc_refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default api
