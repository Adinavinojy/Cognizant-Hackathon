import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Clock, HelpCircle, ArrowLeft, ArrowRight, CheckCircle, Loader2, X } from 'lucide-react'
import api from '../lib/api'

export default function Interview() {
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [sessionData, setSessionData] = useState<any>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [showHint, setShowHint] = useState(false)
  
  // Timer state (for rapid mode)
  const [timeLeft, setTimeLeft] = useState<number>(7 * 60)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Only block UI during the very final submit
  const [isFinishing, setIsFinishing] = useState(false)

  useEffect(() => {
    const dataStr = sessionStorage.getItem('current_session')
    if (dataStr) {
      const data = JSON.parse(dataStr)
      if (data.session_id === sessionId) {
        setSessionData(data)
      }
    }
  }, [sessionId])

  // Reset hint and timer on question change
  useEffect(() => {
    setShowHint(false)

    if (sessionData && sessionData.mode === 'rapid') {
      setTimeLeft(7 * 60)
      if (timerRef.current) clearInterval(timerRef.current)
      timerRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current!)
            handleNext(true)
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [currentIndex, sessionData])

  if (!sessionData) {
    return <div className="p-8 text-center text-gray-500">Loading session...</div>
  }

  const questions = sessionData.questions || []
  const currentQ = questions[currentIndex]
  const isRapid = sessionData.mode === 'rapid'
  const isLast = currentIndex === questions.length - 1

  const handleAnswerChange = (text: string) => {
    setAnswers({ ...answers, [currentQ.question.question_id]: text })
  }

  // Fire-and-forget: submit but don't block navigation on the result
  const submitCurrentAnswerAsync = (qId: string, text: string) => {
    const userStr = localStorage.getItem('user')
    if (!userStr) return
    const user = JSON.parse(userStr)

    const payload = {
      question_id: qId,
      user_id: user.user_id,
      answer_text: text || ''
    }

    // Fire off the request. We store the result when it comes back.
    api.post(`/sessions/${sessionId}/answers`, payload)
      .then(res => {
        const evalResults = JSON.parse(sessionStorage.getItem('eval_results') || '{}')
        evalResults[qId] = res.data
        sessionStorage.setItem('eval_results', JSON.stringify(evalResults))
      })
      .catch(err => console.error('Failed to submit answer', err))
  }

  const handleNext = (_autoAdvanced = false) => {
    const qId = currentQ.question.question_id
    const text = answers[qId] || ''

    if (isLast) {
      handleFinish()
    } else {
      // Fire answer submission in background — don't await it
      submitCurrentAnswerAsync(qId, text)
      setCurrentIndex((i) => i + 1)
    }
  }

  const handlePrev = () => {
    if (currentIndex > 0) setCurrentIndex((i) => i - 1)
  }

  const handleFinish = async () => {
    setIsFinishing(true)
    // Submit the last question synchronously so we wait for all scores
    const qId = currentQ.question.question_id
    const text = answers[qId] || ''
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const user = JSON.parse(userStr)
      try {
        const res = await api.post(`/sessions/${sessionId}/answers`, {
          question_id: qId,
          user_id: user.user_id,
          answer_text: text
        })
        const evalResults = JSON.parse(sessionStorage.getItem('eval_results') || '{}')
        evalResults[qId] = res.data
        sessionStorage.setItem('eval_results', JSON.stringify(evalResults))
      } catch (err) {
        console.error('Failed to submit final answer', err)
      }
    }
    // Small delay to let any in-flight earlier answers finish
    await new Promise(r => setTimeout(r, 500))
    navigate(`/evaluation/${sessionId}`)
  }

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  // Extract a short hint from the reference answer (first ~2 sentences)
  const getHintText = () => {
    const ref = currentQ.question.reference_answer || ''
    const sentences = ref.match(/[^.!?]+[.!?]+/g) || []
    return sentences.slice(0, 2).join(' ') || ref.slice(0, 200) + '...'
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-4">
          <span className="text-xl font-black text-indigo-900 tracking-tight">AI Prep</span>
          <span className="text-gray-300">|</span>
          <span className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Question {currentIndex + 1} of {questions.length}
          </span>
        </div>
        
        <div className="flex items-center space-x-6">
          {/* Difficulty Badge */}
          <span className={`px-3 py-1 text-xs font-bold rounded-full uppercase
            ${currentQ.question.difficulty === 'Easy' ? 'bg-green-100 text-green-700' :
              currentQ.question.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-700'}`}>
            {currentQ.question.difficulty}
          </span>

          {/* Timer */}
          {isRapid && (
            <div className={`flex items-center space-x-2 font-mono text-lg font-bold
              ${timeLeft < 60 ? 'text-red-600 animate-pulse' : 'text-gray-700'}`}>
              <Clock className="h-5 w-5" />
              <span>{formatTime(timeLeft)}</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        
        {/* Left Side: Question */}
        <div className="w-1/3 bg-white border-r border-gray-200 p-8 flex flex-col overflow-y-auto">
          <div className="mb-4">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-sm font-medium bg-indigo-50 text-indigo-800">
              {currentQ.question.topic}
            </span>
          </div>
          
          <h2 className="text-xl font-semibold text-gray-900 leading-relaxed">
            {currentQ.question.question_text}
          </h2>

          {/* Hint Panel */}
          {!isRapid && (
            <div className="mt-auto pt-8">
              {!showHint ? (
                <button
                  onClick={() => setShowHint(true)}
                  className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-indigo-600 transition-colors"
                >
                  <HelpCircle className="h-4 w-4 mr-2" />
                  I'm stuck, give me a hint
                </button>
              ) : (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 relative">
                  <button
                    onClick={() => setShowHint(false)}
                    className="absolute top-3 right-3 text-amber-400 hover:text-amber-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <p className="text-xs font-bold text-amber-700 uppercase tracking-wide mb-2">💡 Hint</p>
                  <p className="text-sm text-amber-900 leading-relaxed">{getHintText()}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Side: Answer Input */}
        <div className="w-2/3 bg-gray-50 flex flex-col">
          <div className="flex-1 p-8">
            <textarea
              className="w-full h-full p-6 text-lg bg-white border border-gray-200 rounded-2xl shadow-sm focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 resize-none outline-none transition-all placeholder:text-gray-400"
              placeholder="Type your answer here..."
              value={answers[currentQ.question.question_id] || ''}
              onChange={(e) => handleAnswerChange(e.target.value)}
              autoFocus
            />
          </div>
          
          {/* Footer actions */}
          <div className="px-8 py-6 bg-white border-t border-gray-200 flex items-center justify-between shrink-0">
            {!isRapid ? (
              <button
                onClick={handlePrev}
                disabled={currentIndex === 0}
                className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-xl text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-40 transition-colors"
              >
                <ArrowLeft className="mr-2 h-5 w-5" />
                Previous
              </button>
            ) : (
              <div></div>
            )}

            <button
              onClick={() => handleNext(false)}
              disabled={isFinishing}
              className={`inline-flex items-center px-8 py-3 border border-transparent text-base font-bold rounded-xl shadow-sm text-white transition-colors
                ${isLast 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-indigo-600 hover:bg-indigo-700'}`}
            >
              {isFinishing ? (
                <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
              ) : isLast ? (
                <CheckCircle className="-ml-1 mr-2 h-5 w-5" />
              ) : null}
              
              {isFinishing 
                ? 'Submitting...' 
                : isLast 
                  ? 'Submit Assessment' 
                  : 'Next Question'}
                  
              {!isLast && !isFinishing && <ArrowRight className="ml-2 h-5 w-5 -mr-1" />}
            </button>
          </div>
        </div>

      </main>
    </div>
  )
}
