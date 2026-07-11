export type Severity = 'healthy' | 'warning' | 'critical'

export interface User {
  email: string
  name: string
  initials: string
}

export interface Campaign {
  id: string
  name: string
  stakeholder: string
  budget: number
  spendMtd: number
  spendYesterday: number
  utilization: number
  status: Severity
}

export interface DashboardSummary {
  status: string
  statusTone: Severity
  totalBudget: number
  totalSpend: number
  utilization: number
  campaignsAtRisk: number
  preventedNrLoss: number
  apiHealth: number
  qualityScore: number
}

export interface AlertItem {
  id: string
  title: string
  message: string
  severity: Severity
  campaignType: string
  timestamp: string
}

export interface PipelineStep {
  id: string
  label: string
  status: 'pending' | 'running' | 'complete' | 'error'
}

export interface SpendTrendPoint {
  day: string
  search: number
  video: number
  demandGen: number
  pmax: number
}

export interface ResourceUsage {
  label: string
  value: number
  color: string
}

export interface AnalyzerField {
  label: string
  cost: number
  budget: number
  mtdAchieve: number
  mtdTarget: number
  t1Cost: number
  severity: Severity
}

export interface AgentSummary {
  campaignType: string
  severity: Severity
  summary: string
}
