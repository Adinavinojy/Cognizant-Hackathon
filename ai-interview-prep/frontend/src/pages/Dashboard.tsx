import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Award, Target, Activity, ArrowRight, TrendingUp, TrendingDown, Minus, Zap, Clock, PlayCircle } from 'lucide-react'
import api from '../lib/api'

type Tab = 'overview' | 'test' | 'history'

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<any>(null)
  const [skills, setSkills] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [hasProfile, setHasProfile] = useState(false)
  const [profileRole, setProfileRole] = useState('')

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (!userStr) { navigate('/login'); return }
    const user = JSON.parse(userStr)

    const savedRole = localStorage.getItem('profile_role_name') || ''
    setProfileRole(savedRole)
    setHasProfile(!!savedRole)

    const load = async () => {
      try {
        const [statsRes, skillsRes] = await Promise.all([
          api.get(`/dashboard/${user.user_id}/stats`),
          api.get(`/dashboard/${user.user_id}/skills`)
        ])
        setStats(statsRes.data)
        setSkills(skillsRes.data)
      } catch (err) {
        console.error('Failed to load dashboard', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [navigate])

  if (loading) return (
    <div className="flex h-64 items-center justify-center">
      <div className="animate-pulse flex flex-col items-center">
        <div className="h-12 w-12 bg-indigo-200 rounded-full mb-4"></div>
        <div className="text-indigo-400 font-medium">Loading your stats...</div>
      </div>
    </div>
  )

  const hasHistory = stats && stats.total_sessions > 0
  const chartData = hasHistory ? [...stats.history].reverse().map((s: any) => ({
    date: new Date(s.started_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    score: Math.round((s.overall_score || 0) * 100)
  })) : []

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900">Your Dashboard</h1>
          <p className="text-gray-500 mt-1">Track your progress and identify your weak spots.</p>
        </div>
        <div className="flex items-center gap-3">
          {hasProfile ? (
            <>
              <Link
                to="/setup/config"
                className="inline-flex items-center px-5 py-2.5 bg-indigo-600 text-white font-bold rounded-xl shadow hover:bg-indigo-700 transition-colors"
              >
                <Zap className="mr-2 h-4 w-4" />
                Quick Start
              </Link>
              <Link
                to="/setup/role"
                className="inline-flex items-center px-5 py-2.5 border border-gray-300 text-gray-700 font-bold rounded-xl hover:bg-gray-50 transition-colors text-sm"
              >
                Change Role / Stack
              </Link>
            </>
          ) : (
            <Link
              to="/setup/role"
              className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white font-bold rounded-xl shadow hover:bg-indigo-700 transition-colors"
            >
              Start Setup
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        {(['overview', 'test', 'history'] as Tab[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-3 text-sm font-semibold capitalize transition-colors border-b-2 -mb-px
              ${activeTab === tab
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-800'}`}
          >
            {tab === 'test' ? '🎯 Take a Test' : tab === 'overview' ? '📊 Overview' : '📋 History'}
          </button>
        ))}
      </div>

      {/* ── Overview Tab ── */}
      {activeTab === 'overview' && (
        <div className="space-y-8">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center">
              <div className="p-4 bg-indigo-50 rounded-2xl">
                <Activity className="h-8 w-8 text-indigo-600" />
              </div>
              <div className="ml-6">
                <p className="text-sm font-bold text-gray-500 uppercase">Sessions Done</p>
                <p className="text-3xl font-black text-gray-900">{stats?.total_sessions || 0}</p>
              </div>
            </div>
            
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center">
              <div className="p-4 bg-green-50 rounded-2xl">
                <Award className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-6">
                <p className="text-sm font-bold text-gray-500 uppercase">Highest Score</p>
                <p className="text-3xl font-black text-gray-900">
                  {stats?.highest_score != null ? `${Math.round(stats.highest_score * 100)}%` : '--'}
                </p>
              </div>
            </div>

            <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center">
              <div className="p-4 bg-blue-50 rounded-2xl">
                <Target className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-6">
                <p className="text-sm font-bold text-gray-500 uppercase">Average Score</p>
                <p className="text-3xl font-black text-gray-900">
                  {stats?.average_score != null ? `${Math.round(stats.average_score * 100)}%` : '--'}
                </p>
              </div>
            </div>
          </div>

          {/* Progress Chart */}
          <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Progress Over Time</h2>
            {hasHistory && chartData.length > 1 ? (
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                    <XAxis dataKey="date" stroke="#9CA3AF" tick={{fill: '#6B7280'}} axisLine={false} tickLine={false} />
                    <YAxis stroke="#9CA3AF" tick={{fill: '#6B7280'}} axisLine={false} tickLine={false} domain={[0, 100]} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      formatter={(value: any) => [`${value}%`, 'Score']}
                    />
                    <Line type="monotone" dataKey="score" stroke="#4F46E5" strokeWidth={4}
                      activeDot={{ r: 8, fill: '#4F46E5', stroke: '#fff', strokeWidth: 2 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-center bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                <TrendingUp className="h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-bold text-gray-900">Not enough data</h3>
                <p className="text-gray-500 max-w-sm mt-2">Complete at least two sessions to see your progress graph.</p>
              </div>
            )}
          </div>

          {/* Skills Analysis */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-green-100 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1.5 bg-green-500"></div>
              <div className="flex items-center space-x-3 mb-6">
                <TrendingUp className="h-6 w-6 text-green-500" />
                <h2 className="text-lg font-bold text-gray-900">Strengths</h2>
              </div>
              <div className="space-y-4">
                {skills?.strengths?.length > 0 ? skills.strengths.map((s: any) => (
                  <div key={s.topic_name} className="flex justify-between items-center">
                    <span className="font-medium text-gray-700">{s.topic_name}</span>
                    <span className="font-bold text-green-600 bg-green-50 px-2 py-1 rounded-md text-sm">
                      {Math.round(s.avg_score * 100)}%
                    </span>
                  </div>
                )) : <p className="text-sm text-gray-400 italic">No strong topics yet.</p>}
              </div>
            </div>

            <div className="bg-white rounded-3xl p-6 shadow-sm border border-yellow-100 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1.5 bg-yellow-400"></div>
              <div className="flex items-center space-x-3 mb-6">
                <Minus className="h-6 w-6 text-yellow-500" />
                <h2 className="text-lg font-bold text-gray-900">Developing</h2>
              </div>
              <div className="space-y-4">
                {skills?.average?.length > 0 ? skills.average.map((s: any) => (
                  <div key={s.topic_name} className="flex justify-between items-center">
                    <span className="font-medium text-gray-700">{s.topic_name}</span>
                    <span className="font-bold text-yellow-600 bg-yellow-50 px-2 py-1 rounded-md text-sm">
                      {Math.round(s.avg_score * 100)}%
                    </span>
                  </div>
                )) : <p className="text-sm text-gray-400 italic">No developing topics yet.</p>}
              </div>
            </div>

            <div className="bg-white rounded-3xl p-6 shadow-sm border border-red-100 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1.5 bg-red-500"></div>
              <div className="flex items-center space-x-3 mb-6">
                <TrendingDown className="h-6 w-6 text-red-500" />
                <h2 className="text-lg font-bold text-gray-900">Needs Focus</h2>
              </div>
              <div className="space-y-4">
                {skills?.weaknesses?.length > 0 ? skills.weaknesses.map((s: any) => (
                  <div key={s.topic_name} className="flex justify-between items-center">
                    <span className="font-medium text-gray-700">{s.topic_name}</span>
                    <span className="font-bold text-red-600 bg-red-50 px-2 py-1 rounded-md text-sm">
                      {Math.round(s.avg_score * 100)}%
                    </span>
                  </div>
                )) : <p className="text-sm text-gray-400 italic">No weak topics yet.</p>}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Test Tab ── */}
      {activeTab === 'test' && (
        <div className="space-y-6 max-w-2xl mx-auto">
          <p className="text-gray-500 text-center">
            {hasProfile
              ? `Practicing as <strong>${profileRole}</strong>. Questions will be adaptively picked based on your weak spots.`
              : 'Set up your profile first to get personalised questions.'}
          </p>

          {hasProfile ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Quick Start Card */}
              <Link to="/setup/config"
                className="bg-white rounded-3xl border-2 border-indigo-200 hover:border-indigo-500 p-8 flex flex-col items-center text-center transition-all group shadow-sm hover:shadow-md"
              >
                <div className="p-4 bg-indigo-50 rounded-2xl mb-4 group-hover:bg-indigo-100 transition-colors">
                  <Zap className="h-10 w-10 text-indigo-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Quick Start</h3>
                <p className="text-sm text-gray-500">Use your saved role and stacks. Just pick a mode and go.</p>
                <span className="mt-4 text-indigo-600 font-bold text-sm group-hover:underline">
                  Start now →
                </span>
              </Link>

              {/* New Setup Card */}
              <Link to="/setup/role"
                className="bg-white rounded-3xl border-2 border-gray-200 hover:border-gray-400 p-8 flex flex-col items-center text-center transition-all group shadow-sm hover:shadow-md"
              >
                <div className="p-4 bg-gray-50 rounded-2xl mb-4 group-hover:bg-gray-100 transition-colors">
                  <PlayCircle className="h-10 w-10 text-gray-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Change Setup</h3>
                <p className="text-sm text-gray-500">Pick a different role or tech stack for this session.</p>
                <span className="mt-4 text-gray-600 font-bold text-sm group-hover:underline">
                  Change settings →
                </span>
              </Link>
            </div>
          ) : (
            <div className="text-center">
              <Link to="/setup/role"
                className="inline-flex items-center px-8 py-4 bg-indigo-600 text-white font-bold rounded-2xl shadow-lg hover:bg-indigo-700 transition-colors text-lg"
              >
                <PlayCircle className="mr-3 h-6 w-6" />
                Set Up & Start
              </Link>
            </div>
          )}
        </div>
      )}

      {/* ── History Tab ── */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {!hasHistory ? (
            <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-12 text-center">
              <Clock className="h-10 w-10 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 font-medium">No completed sessions yet.</p>
            </div>
          ) : (
            stats.history.map((s: any) => (
              <div key={s.session_id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-xl ${s.mode === 'rapid' ? 'bg-red-50' : 'bg-indigo-50'}`}>
                      {s.mode === 'rapid'
                        ? <Zap className="h-5 w-5 text-red-500" />
                        : <Clock className="h-5 w-5 text-indigo-500" />}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800 capitalize">
                        {s.mode === 'rapid' ? 'Rapid Fire' : 'Normal'} Session
                      </p>
                      <p className="text-xs text-gray-400">{new Date(s.started_at).toLocaleDateString(undefined, { dateStyle: 'medium' })}</p>
                    </div>
                  </div>
                  {s.overall_score != null && (
                    <span className={`font-bold px-3 py-1 rounded-full text-sm ${
                      s.overall_score >= 0.7 ? 'bg-green-100 text-green-700' :
                      s.overall_score >= 0.4 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {Math.round(s.overall_score * 100)}%
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-2">{s.question_count} question{s.question_count !== 1 ? 's' : ''}</p>
              </div>
            ))
          )}
        </div>
      )}

    </div>
  )
}
