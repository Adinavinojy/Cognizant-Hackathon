import { useEffect, useState } from 'react'
import api from '../lib/api'

interface TopicProgress {
  id: string
  topic_id: string
  avg_score: number | null
  attempts_count: number
  last_updated: string
}

// Stub topic name map — replace with a real /topics endpoint lookup
const TOPIC_NAMES: Record<string, string> = {
  '22222222-2222-2222-2222-222222222222': 'Operating Systems',
  '33333333-3333-3333-3333-333333333333': 'System Design',
  '44444444-4444-4444-4444-444444444444': 'Databases',
  '55555555-5555-5555-5555-555555555555': 'Algorithms',
  '66666666-6666-6666-6666-666666666666': 'Behavioural',
}

// Stub user ID — replace with value from auth context/store
const STUB_USER_ID = '00000000-0000-0000-0000-000000000002'

/**
 * Dashboard page — shows per-topic average scores.
 * TODO(frontend-pair): Add chart visualisation (e.g. Recharts radar chart).
 * TODO(dashboard-pair): Replace STUB_USER_ID with real user from JWT.
 */
export default function Dashboard() {
  const [progress, setProgress] = useState<TopicProgress[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await api.get(`/dashboard/${STUB_USER_ID}`)
        setProgress(data)
      } catch (err) {
        console.error('Failed to load dashboard', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <p className="text-gray-500">Loading dashboard…</p>

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Your Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {progress.map((row) => {
          const pct = row.avg_score !== null ? Math.round(row.avg_score * 100) : null
          const color =
            pct === null ? 'bg-gray-300'
            : pct >= 80 ? 'bg-green-500'
            : pct >= 60 ? 'bg-indigo-500'
            : 'bg-amber-500'

          return (
            <div
              key={row.id}
              className="bg-white rounded-2xl shadow p-5 flex flex-col gap-2"
            >
              <h2 className="text-sm font-semibold text-gray-700">
                {TOPIC_NAMES[row.topic_id] ?? 'Unknown Topic'}
              </h2>
              <div className="flex items-center gap-3">
                <div className="flex-1 bg-gray-100 rounded-full h-2">
                  <div
                    className={`${color} h-2 rounded-full transition-all`}
                    style={{ width: pct !== null ? `${pct}%` : '0%' }}
                  />
                </div>
                <span className="text-sm font-bold text-gray-800">
                  {pct !== null ? `${pct}%` : '—'}
                </span>
              </div>
              <p className="text-xs text-gray-400">
                {row.attempts_count} attempt{row.attempts_count !== 1 ? 's' : ''}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
