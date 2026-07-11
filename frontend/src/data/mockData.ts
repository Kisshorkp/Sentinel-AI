import type {
  AlertItem,
  AnalyzerField,
  Campaign,
  DashboardSummary,
  PipelineStep,
  ResourceUsage,
  SpendTrendPoint,
  AgentSummary,
} from '../types'

export const DEMO_EMAIL = 'demo@sentinel.ai'
export const DEMO_PASSWORD = 'demo123'

export const dashboardSummary: DashboardSummary = {
  status: 'Needs Attention',
  statusTone: 'warning',
  totalBudget: 405000,
  totalSpend: 360700,
  utilization: 89.1,
  campaignsAtRisk: 4,
  preventedNrLoss: 128400,
  apiHealth: 100,
  qualityScore: 96.5,
}

export const campaigns: Campaign[] = [
  { id: '1001', name: 'Brand Search - IN', stakeholder: 'Marketing Team', budget: 50000, spendMtd: 41200, spendYesterday: 1850, utilization: 82.4, status: 'warning' },
  { id: '1002', name: 'Performance Max - Retail', stakeholder: 'Retail Growth', budget: 75000, spendMtd: 68900, spendYesterday: 3200, utilization: 91.9, status: 'warning' },
  { id: '1003', name: 'YouTube Awareness', stakeholder: 'Brand Team', budget: 30000, spendMtd: 33400, spendYesterday: 980, utilization: 111.3, status: 'critical' },
  { id: '1004', name: 'Lead Gen - Finance', stakeholder: 'Finance BU', budget: 40000, spendMtd: 28800, spendYesterday: 1100, utilization: 72.0, status: 'healthy' },
  { id: '1005', name: 'Competitor Keywords', stakeholder: 'Performance Team', budget: 25000, spendMtd: 24100, spendYesterday: 890, utilization: 96.4, status: 'warning' },
  { id: '1006', name: 'Shopping - Electronics', stakeholder: 'E-commerce', budget: 60000, spendMtd: 45200, spendYesterday: 2100, utilization: 75.3, status: 'healthy' },
  { id: '1010', name: 'Seasonal Promo - Summer', stakeholder: 'Marketing Team', budget: 45000, spendMtd: 47800, spendYesterday: 2250, utilization: 106.2, status: 'critical' },
]

export const alerts: AlertItem[] = [
  {
    id: 'a1',
    title: 'Overspend Alert',
    message: 'YouTube Awareness exceeded 100% of monthly budget. Immediate review required.',
    severity: 'critical',
    campaignType: 'Video campaigns',
    timestamp: 'Today, 12:45 PM',
  },
  {
    id: 'a2',
    title: 'Hourly Spike',
    message: 'Search campaigns hour 14 spend is 62% above 7-day same-hour average.',
    severity: 'warning',
    campaignType: 'Search campaigns',
    timestamp: 'Today, 2:30 PM',
  },
  {
    id: 'a3',
    title: 'Campaign Ending',
    message: 'Seasonal Promo - Summer ends today. Confirm pause or budget extension.',
    severity: 'warning',
    campaignType: 'Search campaigns',
    timestamp: 'Today, 9:00 AM',
  },
]

export const spendTrend: SpendTrendPoint[] = [
  { day: 'Mon', search: 42000, video: 18000, demandGen: 9000, pmax: 31000 },
  { day: 'Tue', search: 44500, video: 19200, demandGen: 8800, pmax: 32500 },
  { day: 'Wed', search: 43800, video: 21000, demandGen: 9200, pmax: 31800 },
  { day: 'Thu', search: 46200, video: 20500, demandGen: 9500, pmax: 33200 },
  { day: 'Fri', search: 45100, video: 19800, demandGen: 9100, pmax: 32800 },
  { day: 'Sat', search: 38900, video: 16500, demandGen: 7600, pmax: 28900 },
  { day: 'Sun', search: 37200, video: 15800, demandGen: 7200, pmax: 27600 },
]

export const resourceUsage: ResourceUsage[] = [
  { label: 'Budget Used', value: 89, color: '#0284c7' },
  { label: 'Pacing', value: 72, color: '#10b981' },
  { label: 'At-Risk', value: 34, color: '#ef4444' },
  { label: 'Efficiency', value: 81, color: '#8b5cf6' },
]

export const pipelineSteps: PipelineStep[] = [
  { id: 'fetch', label: 'Fetch', status: 'complete' },
  { id: 'account', label: 'Account', status: 'complete' },
  { id: 'daily', label: 'Daily', status: 'complete' },
  { id: 'hourly', label: 'Hourly', status: 'complete' },
  { id: 'campaign', label: 'Campaign', status: 'complete' },
]

export const analyzerFields: AnalyzerField[] = [
  { label: 'Search campaigns', cost: 45100, budget: 120000, mtdAchieve: 41200, mtdTarget: 43500, t1Cost: 1850, severity: 'warning' },
  { label: 'Video campaigns', cost: 33400, budget: 30000, mtdAchieve: 33400, mtdTarget: 29000, t1Cost: 980, severity: 'critical' },
  { label: 'Demand Gen campaigns', cost: 9100, budget: 20000, mtdAchieve: 8800, mtdTarget: 9000, t1Cost: 420, severity: 'healthy' },
  { label: 'Performance Max campaigns', cost: 32800, budget: 75000, mtdAchieve: 68900, mtdTarget: 65000, t1Cost: 3200, severity: 'warning' },
]

export const agentSummaries: AgentSummary[] = [
  {
    campaignType: 'Search campaigns',
    severity: 'warning',
    summary:
      'Search spend on T-1 was 8% above the 7-day average. Two new campaigns started yesterday require budget confirmation. One campaign ends today.',
  },
  {
    campaignType: 'Video campaigns',
    severity: 'critical',
    summary:
      'Video campaigns are over monthly budget with sustained hourly overspend in the afternoon block. Eligible campaigns with zero last-6-hour spend detected.',
  },
  {
    campaignType: 'Performance Max campaigns',
    severity: 'warning',
    summary:
      'PMax pacing is ahead of MTD target by 6%. Budget mode confirmation needed for one newly launched campaign with 55% higher budget vs type average.',
  },
]
