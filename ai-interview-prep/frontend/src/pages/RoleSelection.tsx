import { useState, useEffect, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, Plus, Loader2, ArrowRight } from 'lucide-react'
import api from '../lib/api'

interface JobRole {
  role_id: string
  role_name: string
  description?: string
  topics: Array<{ topic_name: string }>
}

export default function RoleSelection() {
  const navigate = useNavigate()
  const [roles, setRoles] = useState<JobRole[]>([])
  const [loading, setLoading] = useState(true)
  
  const [customRole, setCustomRole] = useState('')
  const [isClassifying, setIsClassifying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get('/roles').then((res) => {
      setRoles(res.data)
      setLoading(false)
    }).catch(() => {
      setError("Failed to load roles.")
      setLoading(false)
    })
  }, [])

  const selectRole = (role: JobRole) => {
    // Store selected role and its default stack in sessionStorage for the flow
    sessionStorage.setItem('selected_role_id', role.role_id)
    sessionStorage.setItem('selected_role_name', role.role_name)
    sessionStorage.setItem('default_tech_stack', JSON.stringify(role.topics.map(t => t.topic_name)))
    navigate('/setup/stack')
  }

  const handleCustomSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!customRole.trim()) return

    setIsClassifying(true)
    setError(null)

    try {
      const { data } = await api.post('/roles/classify', { custom_role: customRole })
      
      if (data.mapped_role) {
        // The backend created/found a custom role mapped to a predefined one
        selectRole(data.mapped_role)
      } else {
        // Fallback if LLM couldn't map it — we could just map to a generic "Software Engineer"
        // but for now, we show an error.
        setError("Could not map that role. Please select from the predefined list.")
      }
    } catch (err) {
      setError("Classification failed. Try again.")
    } finally {
      setIsClassifying(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-8">
        
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            What role are you applying for?
          </h1>
          <p className="mt-4 text-lg text-gray-500">
            Select a common role below, or type your exact target job title.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg text-center font-medium">
            {error}
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
          <form onSubmit={handleCustomSubmit} className="flex gap-4">
            <input
              type="text"
              value={customRole}
              onChange={(e) => setCustomRole(e.target.value)}
              placeholder="e.g. Senior React Developer, Data Engineer..."
              className="flex-1 rounded-xl border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-4 py-3 text-lg"
            />
            <button
              type="submit"
              disabled={isClassifying || !customRole.trim()}
              className="inline-flex items-center px-6 py-3 border border-transparent text-lg font-medium rounded-xl shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {isClassifying ? (
                <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
              ) : (
                <ArrowRight className="-ml-1 mr-2 h-5 w-5" />
              )}
              Continue
            </button>
          </form>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="animate-spin h-8 w-8 text-indigo-600" />
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {roles.map((role) => (
              <div
                key={role.role_id}
                onClick={() => selectRole(role)}
                className="relative rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:border-indigo-500 hover:ring-1 hover:ring-indigo-500 cursor-pointer transition-all group"
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0 bg-indigo-100 rounded-lg p-3 group-hover:bg-indigo-600 transition-colors">
                    <Briefcase className="h-6 w-6 text-indigo-600 group-hover:text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 group-hover:text-indigo-600 transition-colors">
                      {role.role_name}
                    </h3>
                    <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                      {role.topics.map(t => t.topic_name).slice(0, 3).join(', ')}...
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  )
}
