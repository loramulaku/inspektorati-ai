import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, refreshAccessToken, setSessionExpiredHandler, tokens } from '../api/client'
import { ROLE_LABEL } from './roles'
import { AuthContext } from './useAuth'

/**
 * Holds the logged-in staff user and the login / logout actions.
 * Staff accounts are created only by an admin, so there is no register here.
 * status: 'loading' while an existing session is being restored, then 'ready'.
 * welcome: the greeting shown once on the dashboard right after a login.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // Only a stored refresh token means there is a session to restore.
  const [status, setStatus] = useState(() => (tokens.getRefresh() ? 'loading' : 'ready'))
  const [welcome, setWelcome] = useState(null)

  useEffect(() => {
    setSessionExpiredHandler(() => setUser(null))

    // Restore the session after a page reload, using the stored refresh token.
    if (!tokens.getRefresh()) {
      return
    }
    refreshAccessToken()
      .then(() => api.get('/auth/me'))
      .then((response) => setUser(response.data))
      .catch((error) => {
        // Forget the session only if the server rejected it, not when it's offline.
        if (error.response?.status === 401) tokens.clear()
      })
      .finally(() => setStatus('ready'))
  }, [])

  const login = useCallback(async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    tokens.setAccess(data.access_token)
    tokens.setRefresh(data.refresh_token)
    setUser(data.user)
    setWelcome(`Mirë se erdhe, ${data.user.emri}! Roli juaj është ${ROLE_LABEL[data.user.role]}.`)
    return data.user
  }, [])

  const logout = useCallback(async () => {
    const refreshToken = tokens.getRefresh()
    if (refreshToken) {
      try {
        await api.post('/auth/logout', { refresh_token: refreshToken })
      } catch {
        // already invalid on the server: logging out locally is enough
      }
    }
    tokens.clear()
    setUser(null)
    setWelcome(null)
  }, [])

  const dismissWelcome = useCallback(() => setWelcome(null), [])

  const value = useMemo(
    () => ({ user, status, welcome, login, logout, dismissWelcome }),
    [user, status, welcome, login, logout, dismissWelcome],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
