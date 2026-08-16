import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Practice from './pages/Practice'
import Feedback from './pages/Feedback'
import Dashboard from './pages/Dashboard'
import History from './pages/History'
import StudyPlan from './pages/StudyPlan'

/**
 * App — top-level router shell.
 * All protected routes are wrapped in <Layout> which provides the nav bar.
 * TODO(frontend-pair): Add a real auth guard once JWT handling is wired up.
 */
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />

        {/* Protected — wrapped in shared nav Layout */}
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/practice" element={<Practice />} />
          <Route path="/feedback" element={<Feedback />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/history" element={<History />} />
          <Route path="/study-plan" element={<StudyPlan />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
