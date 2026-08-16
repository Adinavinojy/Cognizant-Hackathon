import { useLocation, useNavigate } from 'react-router-dom'

interface Score {
  score_id: string
  answer_id: string
  similarity_score: number | null
  llm_judge_score: number | null
  concept_match_score: number | null
  fused_score: number | null
  feedback_text: string | null
  missing_keywords: string[] | null
}

interface Question {
  question_text: string
  difficulty: string
}

/**
 * Feedback page — displays score breakdown and AI feedback after an answer.
 * TODO(frontend-pair): Add radar/bar chart for score visualisation.
 * TODO(scoring-pair): Replace hardcoded mock scores with real values from the API.
 */
export default function Feedback() {
  const location = useLocation()
  const navigate = useNavigate()
  const score = location.state?.score as Score | undefined
  const question = location.state?.question as Question | undefined

  if (!score) {
    return (
      <div>
        <p className="text-gray-500">No feedback data available.</p>
        <button
          id="feedback-back"
          onClick={() => navigate('/practice')}
          className="mt-4 text-indigo-600 hover:underline text-sm"
        >
          ← Back to Practice
        </button>
      </div>
    )
  }

  const pct = (v: number | null) =>
    v !== null ? `${Math.round(v * 100)}%` : '—'

  const scoreRows = [
    { label: 'Similarity Score',     value: score.similarity_score },
    { label: 'LLM Judge Score',      value: score.llm_judge_score },
    { label: 'Concept Match Score',  value: score.concept_match_score },
    { label: 'Fused Score',          value: score.fused_score },
  ]

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Your Feedback</h1>
      {question && (
        <p className="text-sm text-gray-500 mb-6">
          For: <em>{question.question_text}</em>
        </p>
      )}

      {/* Score breakdown */}
      <div className="bg-white rounded-2xl shadow p-6 mb-6">
        <h2 className="text-base font-semibold text-gray-700 mb-4">Score Breakdown</h2>
        <div className="space-y-3">
          {scoreRows.map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between">
              <span className="text-sm text-gray-600">{label}</span>
              <div className="flex items-center gap-3">
                <div className="w-40 bg-gray-100 rounded-full h-2">
                  <div
                    className="bg-indigo-500 h-2 rounded-full"
                    style={{ width: value !== null ? `${value * 100}%` : '0%' }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-800 w-10 text-right">
                  {pct(value)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Feedback text */}
      {score.feedback_text && (
        <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-5 mb-6">
          <h2 className="text-sm font-semibold text-indigo-700 mb-2">AI Feedback</h2>
          <p id="feedback-text" className="text-sm text-gray-700">{score.feedback_text}</p>
        </div>
      )}

      {/* Missing keywords */}
      {score.missing_keywords && score.missing_keywords.length > 0 && (
        <div className="bg-amber-50 border border-amber-100 rounded-2xl p-5 mb-6">
          <h2 className="text-sm font-semibold text-amber-700 mb-2">Missing Keywords</h2>
          <div className="flex flex-wrap gap-2">
            {score.missing_keywords.map((kw) => (
              <span
                key={kw}
                className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full font-medium"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      <button
        id="feedback-practice-again"
        onClick={() => navigate('/practice')}
        className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2 rounded-lg transition-colors"
      >
        Practice Another Question
      </button>
    </div>
  )
}
