import { Navigate, Route, Routes } from 'react-router-dom'
import { PublicOnlyRoute, ProtectedRoute } from './components/auth/ProtectedRoute'
import { AppLayout } from './components/layout/AppLayout'
import { BudgetAlertsPage } from './pages/BudgetAlertsPage'
import { CampaignAnalysisPage } from './pages/CampaignAnalysisPage'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'

export default function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/campaign-analysis" element={<CampaignAnalysisPage />} />
          <Route path="/budget-alerts" element={<BudgetAlertsPage />} />
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
