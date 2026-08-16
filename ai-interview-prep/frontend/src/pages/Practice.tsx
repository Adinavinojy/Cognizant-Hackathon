import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'

interface Question {
  question_id: string
  question_text: string
  difficulty: string
  topic_id: string
  role_id: string
}

/**
 * Practice page — shows a question and accepts a free-text answer.
 * TODO(frontend-pair): Add role/topic selectors, timer, and multi-question flow.
 * TODO(sessions-pair): Create a real session before fetching questions.
 */
export default function Practice() {
  const navigate = useNavigate()
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)

  // Stub session/user IDs — replace with real values from auth context
  const STUB_SESSION_ID = '00000000-0000-0000-0000-000000000001'
  const STUB_USER_ID = '00000000-0000-0000-0000-000000000002'
  const STUB_ROLE_ID = '11111111-1111-1111-1111-111111111111'

  useEffect(() => {
    const loadQuestions = async () => {
      try {
        const { data } = await api.get('/questions', {
          params: { role: 'software-engineer' },
        })
        setQuestions(data)
      } catch (err) {
        console.error('Failed to load questions', err)
      } finally {
        setFetching(false)
      }
    }
    loadQuestions()
  }, [])

  const handleSubmit = async () => {
    if (!answer.trim()) return
    setLoading(true)
    try {
      const { data: scoreData } = await api.post(
        `/sessions/${STUB_SESSION_ID}/answers`,
        {
          question_id: questions[currentIdx]?.question_id,
          user_id: STUB_USER_ID,
          answer_text: answer,
        },
      )
      navigate('/feedback', { state: { score: scoreData, question: questions[currentIdx] } })
    } catch (err) {
      console.error('Failed to submit answer', err)
    } finally {
      setLoading(false)
    }
  }

  if (fetching) {
    return <p className="text-gray-500">Loading questions…</p>
  }

  const question = questions[currentIdx]

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Practice Session</h1>
      <p className="text-sm text-gray-500 mb-6">
        Question {currentIdx + 1} of {questions.length}
      </p>

      {question && (
        <div className="bg-white rounded-2xl shadow p-6 mb-6">
          <span className="inline-block text-xs font-semibold uppercase tracking-wide text-indigo-500 mb-3">
            {question.difficulty ?? 'medium'}
          </span>
          <p id="practice-question-text" className="text-lg font-medium text-gray-800">
            {question.question_text}
          </p>
        </div>
      )}

      <textarea
        id="practice-answer-input"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        rows={6}
        placeholder="Type your answer here…"
        className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 mb-4"
      />

      <div className="flex gap-3">
        <button
          id="practice-submit"
          onClick={handleSubmit}
          disabled={loading || !answer.trim()}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2 rounded-lg transition-colors disabled:opacity-60"
        >
          {loading ? 'Submitting…' : 'Submit Answer'}
        </button>
        {currentIdx < questions.length - 1 && (
          <button
            id="practice-next"
            onClick={() => { setCurrentIdx((i) => i + 1); setAnswer('') }}
            className="border border-gray-300 px-6 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            Skip →
          </button>
        )}
      </div>

      {/* Suppress unused variable warning — stub IDs used in handleSubmit */}
      <span className="hidden">{STUB_ROLE_ID}</span>
    </div>
  )
}
