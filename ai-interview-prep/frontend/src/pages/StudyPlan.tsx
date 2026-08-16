import { useEffect, useState } from 'react'
import api from '../lib/api'

interface StudyPlanItem {
  id: string
  topic_id: string
  priority_rank: number
  recommended_resources: string[] | null
  generated_at: string
}

const TOPIC_NAMES: Record<string, string> = {
  '22222222-2222-2222-2222-222222222222': 'Operating Systems',
  '33333333-3333-3333-3333-333333333333': 'System Design',
  '44444444-4444-4444-4444-444444444444': 'Databases',
  '55555555-5555-5555-5555-555555555555': 'Algorithms',
  '66666666-6666-6666-6666-666666666666': 'Behavioural',
}

const STUB_USER_ID = '00000000-0000-0000-0000-000000000002'

/**
 * StudyPlan page — shows a prioritised list of topics with resources.
 * TODO(frontend-pair): Add ability to mark topics as done / snooze.
 * TODO(dashboard-pair): Replace stub with real study plan generation.
 */
export default function StudyPlan() {
  const [plan, setPlan] = useState<StudyPlanItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await api.get(`/study-plan/${STUB_USER_ID}`)
        const sorted = [...data].sort(
          (a: StudyPlanItem, b: StudyPlanItem) => a.priority_rank - b.priority_rank,
        )
        setPlan(sorted)
      } catch (err) {
        console.error('Failed to load study plan', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <p className="text-gray-500">Loading study plan…</p>

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Your Study Plan</h1>
      <p className="text-sm text-gray-500 mb-6">
        Topics ranked by priority — focus on the top items first.
      </p>

      <ol className="space-y-4">
        {plan.map((item) => (
          <li
            key={item.id}
            className="bg-white rounded-2xl shadow p-5 flex gap-4"
          >
            <span className="text-2xl font-bold text-indigo-200 w-8 shrink-0 text-center">
              {item.priority_rank}
            </span>
            <div className="flex-1">
              <h2 className="font-semibold text-gray-800 mb-2">
                {TOPIC_NAMES[item.topic_id] ?? 'Unknown Topic'}
              </h2>
              {item.recommended_resources && item.recommended_resources.length > 0 && (
                <ul className="space-y-1">
                  {item.recommended_resources.map((r) => (
                    <li key={r} className="text-sm text-indigo-600">
                      {r.startsWith('http') ? (
                        <a
                          href={r}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline"
                        >
                          🔗 {r}
                        </a>
                      ) : (
                        <span className="text-gray-600">📖 {r}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}
