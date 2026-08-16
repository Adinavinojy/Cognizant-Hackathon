import { NavLink, Outlet } from 'react-router-dom'

const NAV_LINKS = [
  { to: '/dashboard',  label: 'Dashboard'  },
  { to: '/practice',   label: 'Practice'   },
  { to: '/history',    label: 'History'    },
  { to: '/study-plan', label: 'Study Plan' },
]

/**
 * Layout — persistent nav shell used by all authenticated pages.
 * TODO(frontend-pair): Add user avatar, logout button, and mobile hamburger menu.
 */
export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Top nav */}
      <nav className="bg-indigo-700 text-white shadow-md">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <span className="font-bold text-lg tracking-tight">🎯 AI Interview Prep</span>
          <ul className="flex gap-6 text-sm font-medium">
            {NAV_LINKS.map(({ to, label }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  className={({ isActive }) =>
                    isActive
                      ? 'underline underline-offset-4'
                      : 'opacity-80 hover:opacity-100 transition-opacity'
                  }
                >
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      {/* Page content */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-8">
        <Outlet />
      </main>

      <footer className="text-center text-xs text-gray-400 py-4 border-t">
        AI Interview Prep — Hackathon Scaffold v0.1
      </footer>
    </div>
  )
}
