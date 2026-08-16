/**
 * History page — shows past mock sessions.
 * TODO(frontend-pair): Fetch real session history from GET /sessions once
 *                      the sessions-pair adds that endpoint.
 * TODO(sessions-pair): Add GET /sessions?user_id= endpoint.
 */

// Mock session data — replace with real API call
const MOCK_SESSIONS = [
  {
    session_id: 'sess-001',
    role: 'Software Engineer',
    started_at: '2026-08-15T10:00:00Z',
    ended_at: '2026-08-15T10:35:00Z',
    status: 'completed',
    question_count: 5,
    avg_score: 0.74,
  },
  {
    session_id: 'sess-002',
    role: 'Software Engineer',
    started_at: '2026-08-14T15:20:00Z',
    ended_at: '2026-08-14T15:48:00Z',
    status: 'completed',
    question_count: 4,
    avg_score: 0.61,
  },
  {
    session_id: 'sess-003',
    role: 'Software Engineer',
    started_at: '2026-08-16T09:10:00Z',
    ended_at: null,
    status: 'active',
    question_count: 2,
    avg_score: null,
  },
]

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export default function History() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Session History</h1>

      <div className="space-y-4">
        {MOCK_SESSIONS.map((s) => (
          <div key={s.session_id} className="bg-white rounded-2xl shadow p-5">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-gray-800">{s.role}</h2>
                <p className="text-xs text-gray-400 mt-0.5">{formatDate(s.started_at)}</p>
              </div>
              <span
                className={`text-xs font-semibold px-2 py-1 rounded-full ${
                  s.status === 'completed'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-amber-100 text-amber-700'
                }`}
              >
                {s.status}
              </span>
            </div>
            <div className="flex gap-6 mt-3 text-sm text-gray-600">
              <span>{s.question_count} question{s.question_count !== 1 ? 's' : ''}</span>
              <span>
                Avg score:{' '}
                {s.avg_score !== null
                  ? `${Math.round(s.avg_score * 100)}%`
                  : '—'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
