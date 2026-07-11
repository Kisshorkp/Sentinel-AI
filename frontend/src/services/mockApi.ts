export function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function fetchDashboardData() {
  await delay(900)
  const { dashboardSummary, campaigns, spendTrend, resourceUsage, alerts } = await import('../data/mockData')
  return { dashboardSummary, campaigns, spendTrend, resourceUsage, alerts }
}

export async function runAnalyzer() {
  await delay(2200)
  const { pipelineSteps, analyzerFields, agentSummaries } = await import('../data/mockData')
  return { pipelineSteps, analyzerFields, agentSummaries }
}

export async function fetchAlerts() {
  await delay(700)
  const { alerts, campaigns } = await import('../data/mockData')
  return { alerts, campaigns: campaigns.filter((c) => c.status !== 'healthy') }
}
