import axios from 'axios'

// Backend address. Override with VITE_API_URL in frontend/.env if needed.
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const REFRESH_KEY = 'inspektorati.refreshToken'

// The access token lives only in memory; the refresh token is kept in
// localStorage so a page reload can restore the session.
let accessToken = null
let onSessionExpired = () => {}

export const tokens = {
  setAccess(token) {
    accessToken = token
  },
  getRefresh() {
    try {
      return localStorage.getItem(REFRESH_KEY)
    } catch {
      return null
    }
  },
  setRefresh(token) {
    try {
      localStorage.setItem(REFRESH_KEY, token)
    } catch {
      // storage blocked: the session simply won't survive a reload
    }
  },
  clear() {
    accessToken = null
    try {
      localStorage.removeItem(REFRESH_KEY)
    } catch {
      // nothing to clear
    }
  },
}

/** Called when the refresh token is no longer valid (e.g. revoked). */
export function setSessionExpiredHandler(handler) {
  onSessionExpired = handler
}

export const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// Several requests can fail with 401 at the same time; they share one refresh.
let refreshPromise = null

export function refreshAccessToken() {
  const refreshToken = tokens.getRefresh()
  if (!refreshToken) {
    return Promise.reject(new Error('Nuk ka seancë aktive'))
  }
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken })
      .then((response) => {
        accessToken = response.data.access_token
        return accessToken
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

const NO_RETRY = ['/auth/login', '/auth/refresh', '/auth/logout']

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const canRetry =
      error.response?.status === 401 &&
      original &&
      !original._retried &&
      !NO_RETRY.includes(original.url) &&
      tokens.getRefresh()

    if (!canRetry) {
      return Promise.reject(error)
    }

    original._retried = true
    try {
      const token = await refreshAccessToken()
      original.headers.Authorization = `Bearer ${token}`
      return api(original)
    } catch {
      tokens.clear()
      onSessionExpired()
      return Promise.reject(error)
    }
  },
)

/** Turn an API error into a short Albanian message for the UI. */
export function errorMessage(error, fallback = 'Diçka shkoi keq. Provoni përsëri.') {
  if (!error.response) {
    return 'Serveri nuk përgjigjet. Kontrolloni që backend-i është i ndezur.'
  }
  const detail = error.response.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail) && detail.length > 0) {
    // FastAPI validation errors: [{ loc, msg }]
    return detail.map((item) => item.msg.replace(/^Value error, /, '')).join(' · ')
  }
  return fallback
}
