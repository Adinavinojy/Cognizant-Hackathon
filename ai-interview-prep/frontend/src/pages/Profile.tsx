import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { User, Briefcase, Layers, LogOut, Pencil } from 'lucide-react'

export default function Profile() {
  const navigate = useNavigate()
  const [user, setUser] = useState<any>(null)
  const [role, setRole] = useState<string>('')
  const [stacks, setStacks] = useState<string[]>([])

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (!userStr) { navigate('/login'); return }
    setUser(JSON.parse(userStr))

    const savedRole = localStorage.getItem('profile_role_name') || ''
    const savedStacks = JSON.parse(localStorage.getItem('profile_stacks') || '[]')
    setRole(savedRole)
    setStacks(savedStacks)
  }, [navigate])

  const handleLogout = () => {
    localStorage.clear()
    sessionStorage.clear()
    navigate('/login')
  }

  if (!user) return null

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-extrabold text-gray-900">Profile</h1>
        <button
          onClick={handleLogout}
          className="inline-flex items-center px-4 py-2 text-sm font-semibold text-red-600 border border-red-200 rounded-xl hover:bg-red-50 transition-colors"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </button>
      </div>

      {/* User Info */}
      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center space-x-4">
          <div className="h-16 w-16 rounded-full bg-indigo-100 flex items-center justify-center">
            <User className="h-8 w-8 text-indigo-600" />
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900">{user.name}</p>
            <p className="text-gray-500">{user.email}</p>
          </div>
        </div>
      </div>

      {/* Role & Stack */}
      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Interview Setup</h2>
          <Link
            to="/setup/role"
            className="inline-flex items-center text-sm font-semibold text-indigo-600 hover:underline"
          >
            <Pencil className="h-4 w-4 mr-1" />
            Change Role / Stack
          </Link>
        </div>

        {role ? (
          <>
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <Briefcase className="h-4 w-4 text-gray-400" />
                <p className="text-sm font-bold text-gray-500 uppercase tracking-wide">Target Role</p>
              </div>
              <p className="text-base font-semibold text-gray-800 ml-6">{role}</p>
            </div>

            <div>
              <div className="flex items-center space-x-2 mb-3">
                <Layers className="h-4 w-4 text-gray-400" />
                <p className="text-sm font-bold text-gray-500 uppercase tracking-wide">Tech Stacks</p>
              </div>
              <div className="flex flex-wrap gap-2 ml-6">
                {stacks.length > 0 ? stacks.map(s => (
                  <span key={s} className="px-3 py-1 bg-indigo-50 text-indigo-700 text-sm font-semibold rounded-full">
                    {s}
                  </span>
                )) : (
                  <span className="text-sm text-gray-400 italic">No stacks selected.</span>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-6">
            <p className="text-gray-400 mb-4">You haven't set up your interview profile yet.</p>
            <Link
              to="/setup/role"
              className="inline-flex items-center px-5 py-2.5 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors"
            >
              Set Up Profile
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
