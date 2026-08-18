import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, CheckCircle2, Zap, AlertCircle } from 'lucide-react'
import api from '../lib/api'

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function duration(start: string, end?: string | null) {
  if (!end) return null
  const ms = new Date(end).getTime() - new Date(start).getTime()
  const mins = Math.floor(ms / 60000)
  return `${mins} min`
}

export default function History() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (!userStr) { navigate('/login'); return }
    const user = JSON.parse(userStr)

    api.get(`/dashboard/${user.user_id}/stats`)
      .then(res => {
        // history array from the stats endpoint already filtered to this user
        setSessions(res.data.history || [])
      })
      .catch(err => console.error('Failed to load history', err))
      .finally(() => setLoading(false))
  }, [navigate])

  if (loading) return (
    <div className="flex h-64 items-center justify-center">
      <div className="animate-pulse text-indigo-400 font-medium">Loading history...</div>
    </div>
  )

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Session History</h1>

      {sessions.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-12 text-center">
          <AlertCircle className="h-10 w-10 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-medium">No completed sessions yet.</p>
          <p className="text-sm text-gray-400 mt-1">Complete an interview session to see it here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sessions.map((s: any) => (
            <div key={s.session_id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-xl ${s.mode === 'rapid' ? 'bg-red-50' : 'bg-indigo-50'}`}>
                    {s.mode === 'rapid'
                      ? <Zap className="h-5 w-5 text-red-500" />
                      : <Clock className="h-5 w-5 text-indigo-500" />
                    }
                  </div>
                  <div>
                    <p className="font-semibold text-gray-800 capitalize">
                      {s.mode === 'rapid' ? 'Rapid Fire' : 'Normal'} Session
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">{formatDate(s.started_at)}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {s.overall_score !== null && s.overall_score !== undefined && (
                    <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                      s.overall_score >= 0.7 ? 'bg-green-100 text-green-700' :
                      s.overall_score >= 0.4 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {Math.round(s.overall_score * 100)}%
                    </span>
                  )}
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-green-100 text-green-700 flex items-center">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Completed
                  </span>
                </div>
              </div>

              <div className="flex gap-6 mt-4 text-sm text-gray-500">
                <span>{s.question_count} question{s.question_count !== 1 ? 's' : ''}</span>
                {s.overall_score !== null && (
                  <span>Score: <strong className="text-gray-800">{Math.round(s.overall_score * 100)}%</strong></span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
