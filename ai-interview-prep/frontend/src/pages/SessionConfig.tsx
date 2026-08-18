import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Settings, Zap, Clock, Loader2, ArrowRight } from 'lucide-react'
import api from '../lib/api'

export default function SessionConfig() {
  const navigate = useNavigate()
  
  const [mode, setMode] = useState<'normal' | 'rapid'>('normal')
  const [questionCount, setQuestionCount] = useState(5)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStart = async () => {
    setIsGenerating(true)
    setError(null)

    // Support two flows: full setup (sessionStorage) and Quick Start (localStorage fallback)
    const role_id = sessionStorage.getItem('selected_role_id') || localStorage.getItem('profile_role_id')
    const tech_stacks = JSON.parse(
      sessionStorage.getItem('final_tech_stacks') || localStorage.getItem('profile_stacks') || '[]'
    )
    
    // Get current user id from local storage
    const userStr = localStorage.getItem('user')
    if (!userStr) {
      navigate('/login')
      return
    }
    const user = JSON.parse(userStr)

    try {
      const payload = {
        user_id: user.user_id,
        role_id: role_id,
        mode: mode,
        question_count: questionCount,
        tech_stacks: tech_stacks
      }
      
      // This endpoint adaptively picks difficulty and generates all questions
      const { data } = await api.post('/sessions', payload)
      
      // We will store the generated session in state/storage or just rely on passing it,
      // but for simplicity we can store it in sessionStorage or fetch it inside the interview component.
      // We will pass the full session data to the interview via sessionStorage so we don't have to re-fetch immediately.
      sessionStorage.setItem('current_session', JSON.stringify(data))
      
      navigate(`/interview/${data.session_id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate session. Please try again.')
      setIsGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto space-y-8">
        
        <div className="text-center">
          <div className="inline-flex items-center justify-center p-3 bg-indigo-100 rounded-full mb-4">
            <Settings className="h-8 w-8 text-indigo-600" />
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            Configure Your Session
          </h1>
          <p className="mt-4 text-lg text-gray-500">
            Choose how you want to practice. Questions will be adaptively tailored to your skill level.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg text-center font-medium">
            {error}
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-sm p-8 border border-gray-100 space-y-8">
          
          {/* Mode Selection */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4">Interview Mode</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              
              <div 
                onClick={() => setMode('normal')}
                className={`relative rounded-xl border p-5 cursor-pointer transition-all ${
                  mode === 'normal' 
                    ? 'border-indigo-600 ring-2 ring-indigo-600 bg-indigo-50/30' 
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className="flex justify-between">
                  <div className="flex-1">
                    <h4 className={`text-base font-bold ${mode === 'normal' ? 'text-indigo-900' : 'text-gray-900'}`}>
                      Normal Mode
                    </h4>
                    <p className="mt-1 text-sm text-gray-500">
                      Untimed. Take your time, request hints, and navigate back and forth between questions.
                    </p>
                  </div>
                  <Clock className={`h-6 w-6 flex-shrink-0 ml-4 ${mode === 'normal' ? 'text-indigo-600' : 'text-gray-400'}`} />
                </div>
              </div>

              <div 
                onClick={() => setMode('rapid')}
                className={`relative rounded-xl border p-5 cursor-pointer transition-all ${
                  mode === 'rapid' 
                    ? 'border-red-500 ring-2 ring-red-500 bg-red-50/30' 
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className="flex justify-between">
                  <div className="flex-1">
                    <h4 className={`text-base font-bold ${mode === 'rapid' ? 'text-red-900' : 'text-gray-900'}`}>
                      Rapid Fire
                    </h4>
                    <p className="mt-1 text-sm text-gray-500">
                      7 minutes per question. Strict auto-advance. No hints. No going back.
                    </p>
                  </div>
                  <Zap className={`h-6 w-6 flex-shrink-0 ml-4 ${mode === 'rapid' ? 'text-red-500' : 'text-gray-400'}`} />
                </div>
              </div>

            </div>
          </div>

          <div className="border-t border-gray-100"></div>

          {/* Question Count */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">Number of Questions</h3>
              <span className="text-xl font-bold text-indigo-600">{questionCount}</span>
            </div>
            <input
              type="range"
              min="5"
              max="10"
              step="1"
              value={questionCount}
              onChange={(e) => setQuestionCount(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-2 font-medium">
              <span>5 Min</span>
              <span>10 Max</span>
            </div>
          </div>

        </div>

        <div className="flex justify-end">
          <button
            onClick={handleStart}
            disabled={isGenerating}
            className="inline-flex w-full sm:w-auto justify-center items-center px-8 py-4 border border-transparent text-lg font-bold rounded-xl shadow-lg text-white bg-indigo-900 hover:bg-black disabled:bg-indigo-400 transition-colors"
          >
            {isGenerating ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5" />
                Generating Questions...
              </>
            ) : (
              <>
                Start Interview
                <ArrowRight className="ml-3 h-5 w-5" />
              </>
            )}
          </button>
        </div>
        
        {isGenerating && (
          <p className="text-center text-sm text-gray-500 font-medium animate-pulse">
            This may take 10-15 seconds while we adaptively fetch and generate your unique questions...
          </p>
        )}

      </div>
    </div>
  )
}
