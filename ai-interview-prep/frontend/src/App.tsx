import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import RoleSelection from './pages/RoleSelection'
import StackSelection from './pages/StackSelection'
import SessionConfig from './pages/SessionConfig'
import Interview from './pages/Interview'
import Evaluation from './pages/Evaluation'
import Dashboard from './pages/Dashboard'
import History from './pages/History'
import StudyPlan from './pages/StudyPlan'
import Profile from './pages/Profile'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />

        {/* Setup Flow (Standalone - No Sidebar Layout needed, or custom header) */}
        <Route path="/setup/role" element={<RoleSelection />} />
        <Route path="/setup/stack" element={<StackSelection />} />
        <Route path="/setup/config" element={<SessionConfig />} />
        
        {/* Interview Session (Standalone UI) */}
        <Route path="/interview/:sessionId" element={<Interview />} />
        <Route path="/evaluation/:sessionId" element={<Evaluation />} />

        {/* Protected Dashboard/App — wrapped in shared nav Layout */}
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/history" element={<History />} />
          <Route path="/study-plan" element={<StudyPlan />} />
          <Route path="/profile" element={<Profile />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
