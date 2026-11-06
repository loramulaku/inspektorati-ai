import { Navigate, Outlet } from 'react-router-dom'
import { ROLE_HOME } from './roles'
import { useAuth } from './useAuth'

/**
 * Lets the page through only for logged-in users whose role is in `roles`.
 * Not logged in → login page. Wrong role → that user's own dashboard.
 */
export default function ProtectedRoute({ roles }) {
  const { user, status } = useAuth()

  if (status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center text-meta text-ink-2">
        Duke u ngarkuar…
      </div>
    )
  }
  if (!user) {
    return <Navigate to="/kycu" replace />
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={ROLE_HOME[user.role]} replace />
  }
  return <Outlet />
}
