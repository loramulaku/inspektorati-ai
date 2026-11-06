import { Link, NavLink } from 'react-router-dom'
import { Stema } from './ui'

const LINKS = [
  { to: '/', label: 'Kreu', end: true },
  { to: '/gjurmo', label: 'Gjurmo kërkesën' },
]

/** White header of the citizen portal pages (spec 5.3). */
export default function PublicHeader() {
  return (
    <header className="border-b border-line bg-white">
      <div className="flex h-[68px] items-center gap-3 px-4 sm:px-10">
        <Link to="/" className="flex items-center gap-3">
          <Stema className="h-9" />
          <div className="flex flex-col">
            <span className="text-body-lg font-bold text-ink">Komuna e Vushtrrisë</span>
            <span className="text-caption text-ink-2">Inspektorati — Portali i qytetarit</span>
          </div>
        </Link>
        <div className="flex-1" />
        <nav className="flex items-center gap-6 sm:gap-8">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `text-body font-medium ${isActive ? 'text-ink' : 'text-ink-2 hover:text-ink'}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  )
}
