import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { CheckCircle2, XCircle, AlertCircle, ChevronDown, ChevronUp, ArrowRight, TrendingUp, Lightbulb } from 'lucide-react'

export default function Evaluation() {
  const { sessionId } = useParams()
  const [results, setResults] = useState<Record<string, any>>({})
  const [sessionData, setSessionData] = useState<any>(null)
  const [expandedQ, setExpandedQ] = useState<string | null>(null)

  useEffect(() => {
    // Read session config and results from storage
    const dataStr = sessionStorage.getItem('current_session')
    if (dataStr) setSessionData(JSON.parse(dataStr))

    const resStr = sessionStorage.getItem('eval_results')
    if (resStr) setResults(JSON.parse(resStr))
  }, [])

  if (!sessionData || Object.keys(results).length === 0) {
    return <div className="p-8 text-center text-gray-500">Loading evaluation... (Did you complete a session?)</div>
  }

  const questions = sessionData.questions || []
  
  // Calculate overall score
  const scores = Object.values(results).map(r => r.fused_score || 0)
  const overallAvg = scores.reduce((a, b) => a + b, 0) / (scores.length || 1)
  const overallPercentage = Math.round(overallAvg * 100)

  const toggleExpand = (qId: string) => {
    setExpandedQ(expandedQ === qId ? null : qId)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Top Banner */}
        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-2 bg-indigo-500"></div>
          
          <h1 className="text-sm font-bold text-gray-500 tracking-widest uppercase mb-4">
            Session Complete
          </h1>
          
          <div className="flex justify-center items-end space-x-2">
            <span className="text-6xl font-black text-gray-900 tracking-tighter">
              {overallPercentage}%
            </span>
            <span className="text-xl font-medium text-gray-400 mb-2">Overall Score</span>
          </div>
          
          <p className="mt-6 text-lg text-gray-500 max-w-2xl mx-auto">
            {overallPercentage > 80 ? "Excellent work! You've mastered these concepts." :
             overallPercentage > 50 ? "Good effort, but there's room for improvement." :
             "Keep practicing! Review the feedback below to strengthen your weak spots."}
          </p>

          <div className="mt-8 flex justify-center">
            <Link
              to="/dashboard"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-bold rounded-xl shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 transition-colors"
            >
              Back to Dashboard
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </div>
        </div>

        {/* Question Breakdown */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-gray-900 px-2">Question Breakdown</h2>
          
          {questions.map((q: any, idx: number) => {
            const qId = q.question.question_id
            const res = results[qId]
            const isExpanded = expandedQ === qId
            
            // If they skipped or it timed out without submitting
            if (!res) {
              return (
                <div key={qId} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 opacity-60">
                  <h3 className="font-bold text-gray-900">Q{idx + 1}. Unattempted</h3>
                </div>
              )
            }

            const simPercent = res.similarity_percentage
            
            return (
              <div key={qId} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden transition-all">
                {/* Header (Clickable) */}
                <div 
                  onClick={() => toggleExpand(qId)}
                  className="px-6 py-5 cursor-pointer hover:bg-gray-50 flex items-center justify-between"
                >
                  <div className="flex items-center space-x-4 flex-1">
                    <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg
                      ${simPercent > 80 ? 'bg-green-100 text-green-700' : 
                        simPercent > 50 ? 'bg-yellow-100 text-yellow-700' : 
                        'bg-red-100 text-red-700'}`}>
                      {Math.round(simPercent)}%
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-indigo-600 mb-1">{q.question.topic}</h3>
                      <p className="text-base font-bold text-gray-900 line-clamp-1">{q.question.question_text}</p>
                    </div>
                  </div>
                  <div className="ml-4">
                    {isExpanded ? <ChevronUp className="h-6 w-6 text-gray-400" /> : <ChevronDown className="h-6 w-6 text-gray-400" />}
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="px-6 pb-6 pt-2 border-t border-gray-100 bg-gray-50/50 space-y-6">
                    
                    {/* The Question */}
                    <div>
                      <h4 className="text-sm font-bold text-gray-500 uppercase mb-2">Question</h4>
                      <p className="text-gray-900">{q.question.question_text}</p>
                    </div>

                    {/* Simple Explanation */}
                    <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                      <div className="flex items-start">
                        <Lightbulb className="h-5 w-5 text-blue-600 mt-0.5 mr-3 shrink-0" />
                        <div>
                          <h4 className="text-sm font-bold text-blue-900 mb-1">Simple Explanation</h4>
                          <p className="text-sm text-blue-800 leading-relaxed">{res.answer_explanation}</p>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Correct Answer */}
                      <div>
                        <h4 className="text-sm font-bold text-gray-500 uppercase mb-2">Correct Answer</h4>
                        <div className="bg-white border border-gray-200 rounded-xl p-4 text-sm text-gray-700 leading-relaxed max-h-48 overflow-y-auto">
                          {res.reference_answer}
                        </div>
                      </div>

                      {/* Hints & Feedback */}
                      <div className="space-y-4">
                        
                        <div>
                          <h4 className="text-sm font-bold text-gray-500 uppercase mb-2 flex items-center">
                            <CheckCircle2 className="h-4 w-4 text-green-500 mr-2" />
                            You got right
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {res.hint.connecting_keywords.map((kw: string, i: number) => (
                              <span key={i} className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-md">
                                {kw}
                              </span>
                            ))}
                            {res.hint.connecting_keywords.length === 0 && <span className="text-sm text-gray-400">None identified.</span>}
                          </div>
                        </div>

                        <div>
                          <h4 className="text-sm font-bold text-gray-500 uppercase mb-2 flex items-center">
                            <XCircle className="h-4 w-4 text-red-500 mr-2" />
                            Missing Concepts
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {res.hint.missing_keywords.map((kw: string, i: number) => (
                              <span key={i} className="px-2 py-1 bg-red-100 text-red-700 text-xs font-bold rounded-md">
                                {kw}
                              </span>
                            ))}
                            {res.hint.missing_keywords.length === 0 && <span className="text-sm text-gray-400">Nothing major missed!</span>}
                          </div>
                        </div>

                      </div>
                    </div>

                    {/* Tips & Tricks */}
                    {res.hint.tips_and_tricks && res.hint.tips_and_tricks.length > 0 && (
                      <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
                        <h4 className="text-sm font-bold text-indigo-900 mb-2 flex items-center">
                          <TrendingUp className="h-4 w-4 mr-2" />
                          Tips & Tricks for Next Time
                        </h4>
                        <ul className="list-disc pl-5 space-y-1 text-sm text-indigo-800">
                          {res.hint.tips_and_tricks.map((tip: string, i: number) => (
                            <li key={i}>{tip}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                  </div>
                )}
              </div>
            )
          })}
        </div>

      </div>
    </div>
  )
}
