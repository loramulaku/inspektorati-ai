import { NavLink, useNavigate } from 'react-router-dom'
import { ROLE_HOME, ROLE_TITLE } from '../auth/roles'
import { useAuth } from '../auth/useAuth'
import { Stema } from './ui'

function navItems(role) {
  const items = [{ label: 'Paneli', to: ROLE_HOME[role] }]
  if (role === 'admin') {
    items.push({ label: 'Përdoruesit & rolet', to: '/admin/perdoruesit' })
  }
  return items
}

function initials(user) {
  return `${user.emri[0] ?? ''}${user.mbiemri[0] ?? ''}`.toUpperCase()
}

/** Navy sidebar (spec 6.9). The dot is the icon. */
function Sidebar({ user, onLogout }) {
  return (
    <aside className="flex flex-col gap-1.5 bg-sidebar px-5 py-6 md:sticky md:top-0 md:h-screen md:w-[248px] md:shrink-0">
      <div className="flex items-center gap-3 pb-4">
        <Stema className="h-[38px]" />
        <div className="flex flex-col gap-px">
          <span className="text-card-title font-bold text-on-dark">Inspektorati AI</span>
          <span className="text-caption text-on-dark-2">Komuna e Vushtrrisë</span>
        </div>
      </div>

      <nav className="flex flex-col gap-1.5">
        {navItems(user.role).map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) =>
              `group flex items-center gap-2.5 rounded-sm px-3 py-2.5 text-body leading-none ${
                isActive
                  ? 'bg-primary font-semibold text-white'
                  : 'font-medium text-on-dark-2 hover:bg-white/5 hover:text-on-dark'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={`h-[7px] w-[7px] rounded-full ${
                    isActive ? 'bg-white' : 'bg-on-dark-2 group-hover:bg-line-strong'
                  }`}
                />
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="flex-1" />

      <div className="mt-4 flex items-center gap-2.5 rounded-btn-lg bg-sidebar-card px-3 py-2.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-meta font-bold text-white">
          {initials(user)}
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-px">
          <span className="truncate text-meta font-semibold text-on-dark">
            {user.emri} {user.mbiemri}
          </span>
          <span className="text-eyebrow text-on-dark-2">{ROLE_TITLE[user.role]}</span>
        </div>
        <button
          type="button"
          onClick={onLogout}
          className="rounded-sm px-2 py-1 text-caption font-semibold text-on-dark-2 hover:bg-white/5 hover:text-on-dark"
        >
          Dil
        </button>
      </div>
    </aside>
  )
}

/** Staff app shell (spec 5.1): sidebar + 72px top bar + content area. */
export default function AppShell({ title, subtitle, children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/kycu', { replace: true })
  }

  return (
    <div className="min-h-screen md:flex">
      <Sidebar user={user} onLogout={handleLogout} />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-line bg-white px-7">
          <div className="flex flex-col gap-0.5">
            <h1 className="text-page-title font-bold text-ink">{title}</h1>
            {subtitle && <p className="text-meta text-ink-2">{subtitle}</p>}
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-tint text-meta font-bold text-primary">
            {initials(user)}
          </div>
        </header>
        <main className="flex flex-1 flex-col gap-5 px-7 py-6">{children}</main>
      </div>
    </div>
  )
}
