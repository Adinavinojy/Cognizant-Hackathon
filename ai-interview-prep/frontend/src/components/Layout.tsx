import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { User, LogOut } from 'lucide-react'

const NAV_LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/study-plan', label: 'Study Plan' },
]

export default function Layout() {
  const navigate = useNavigate()

  const userStr = localStorage.getItem('user')
  const user = userStr ? JSON.parse(userStr) : null

  const handleLogout = () => {
    localStorage.clear()
    sessionStorage.clear()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Top nav */}
      <nav className="bg-indigo-700 text-white shadow-md">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <span className="font-bold text-lg tracking-tight">🎯 AI Interview Prep</span>
          
          <ul className="flex gap-6 text-sm font-medium items-center">
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

            {/* Profile link */}
            <li>
              <NavLink
                to="/profile"
                className={({ isActive }) =>
                  `flex items-center space-x-1 ${isActive ? 'underline underline-offset-4' : 'opacity-80 hover:opacity-100 transition-opacity'}`
                }
              >
                <User className="h-4 w-4" />
                <span>{user?.name?.split(' ')[0] || 'Profile'}</span>
              </NavLink>
            </li>

            {/* Logout button */}
            <li>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-1 opacity-80 hover:opacity-100 transition-opacity"
                title="Logout"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </button>
            </li>
          </ul>
        </div>
      </nav>

      {/* Page content */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-8">
        <Outlet />
      </main>

      <footer className="text-center text-xs text-gray-400 py-4 border-t">
        AI Interview Prep — v0.2
      </footer>
    </div>
  )
}
