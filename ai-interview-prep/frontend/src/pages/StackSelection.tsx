import { useState, useEffect, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, Plus, X, ArrowRight } from 'lucide-react'

export default function StackSelection() {
  const navigate = useNavigate()
  const [roleName, setRoleName] = useState('')
  const [selectedStacks, setSelectedStacks] = useState<string[]>([])
  const [customStack, setCustomStack] = useState('')

  useEffect(() => {
    const role = sessionStorage.getItem('selected_role_name')
    if (!role) {
      navigate('/setup/role')
      return
    }
    setRoleName(role)

    const defaultStacks = JSON.parse(sessionStorage.getItem('default_tech_stack') || '[]')
    setSelectedStacks(defaultStacks)
  }, [navigate])

  const toggleStack = (stack: string) => {
    if (selectedStacks.includes(stack)) {
      setSelectedStacks(selectedStacks.filter(s => s !== stack))
    } else {
      setSelectedStacks([...selectedStacks, stack])
    }
  }

  const addCustomStack = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = customStack.trim()
    if (trimmed && !selectedStacks.includes(trimmed)) {
      setSelectedStacks([...selectedStacks, trimmed])
    }
    setCustomStack('')
  }

  const handleContinue = () => {
    sessionStorage.setItem('final_tech_stacks', JSON.stringify(selectedStacks))
    // Persist to localStorage so Quick Start and Profile can read them
    localStorage.setItem('profile_role_name', roleName)
    localStorage.setItem('profile_role_id', sessionStorage.getItem('selected_role_id') || '')
    localStorage.setItem('profile_stacks', JSON.stringify(selectedStacks))
    navigate('/setup/config')
  }

  // Predefined popular choices for easy picking if not already selected
  const popularChoices = [
    'React', 'Node.js', 'Python', 'System Design', 'Databases', 'AWS', 
    'Docker', 'Kubernetes', 'Algorithms', 'Behavioural'
  ]

  const unselectedPopular = popularChoices.filter(s => !selectedStacks.includes(s))

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-8">
        
        <div className="text-center">
          <p className="text-sm font-semibold text-indigo-600 uppercase tracking-wide">
            {roleName}
          </p>
          <h1 className="mt-2 text-3xl font-extrabold text-gray-900 tracking-tight">
            Customize your tech stack
          </h1>
          <p className="mt-4 text-lg text-gray-500">
            We've pre-selected core topics for this role. Add or remove topics to match your exact interview.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm p-8 border border-gray-100">
          
          {/* Selected Stacks */}
          <div className="mb-8">
            <h3 className="text-sm font-medium text-gray-500 mb-4">YOUR TOPICS</h3>
            <div className="flex flex-wrap gap-3">
              {selectedStacks.map((stack) => (
                <div
                  key={stack}
                  onClick={() => toggleStack(stack)}
                  className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-indigo-50 text-indigo-700 border border-indigo-200 cursor-pointer hover:bg-red-50 hover:text-red-700 hover:border-red-200 transition-colors group"
                >
                  {stack}
                  <X className="ml-2 h-4 w-4 text-indigo-400 group-hover:text-red-500" />
                </div>
              ))}
              {selectedStacks.length === 0 && (
                <span className="text-sm text-gray-400 italic">No topics selected.</span>
              )}
            </div>
          </div>

          <div className="border-t border-gray-100 my-6"></div>

          {/* Add Custom */}
          <div className="mb-8">
            <form onSubmit={addCustomStack} className="flex gap-4">
              <input
                type="text"
                value={customStack}
                onChange={(e) => setCustomStack(e.target.value)}
                placeholder="Type a specific skill (e.g. GraphQL, Redis)..."
                className="flex-1 rounded-xl border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-4 py-3"
              />
              <button
                type="submit"
                disabled={!customStack.trim()}
                className="inline-flex items-center px-4 py-3 border border-gray-300 shadow-sm text-sm font-medium rounded-xl text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                <Plus className="mr-2 h-4 w-4 text-gray-500" />
                Add
              </button>
            </form>
          </div>

          {/* Popular Choices */}
          {unselectedPopular.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-4">POPULAR ADDITIONS</h3>
              <div className="flex flex-wrap gap-2">
                {unselectedPopular.map((stack) => (
                  <button
                    key={stack}
                    onClick={() => toggleStack(stack)}
                    className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-white border border-gray-200 text-gray-600 hover:border-indigo-500 hover:text-indigo-600 transition-colors"
                  >
                    <Plus className="mr-1 h-3.5 w-3.5" />
                    {stack}
                  </button>
                ))}
              </div>
            </div>
          )}

        </div>

        <div className="flex justify-end">
          <button
            onClick={handleContinue}
            disabled={selectedStacks.length === 0}
            className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-bold rounded-xl shadow-lg text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            Continue to Session Config
            <ArrowRight className="ml-3 h-5 w-5" />
          </button>
        </div>

      </div>
    </div>
  )
}
