import type { AppConfig } from '../../services/api'
import { DashboardCard } from '../ui/DashboardCard'

interface CredentialsPanelProps {
  config: AppConfig | null
}

export function CredentialsPanel({ config }: CredentialsPanelProps) {
  if (!config) return null

  return (
    <DashboardCard title="Google Ads API Credentials" subtitle="Add credentials to .env for live fetch">
      <div className="space-y-4 text-sm text-slate-600">
        <p>
          Required to fetch <strong>Cost</strong>, <strong>Conversions</strong>, and <strong>Conversion Value</strong>{' '}
          from Google Ads.
        </p>
        <div className="overflow-x-auto rounded-xl border border-slate-100">
          <table className="min-w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-400">
              <tr>
                <th className="px-3 py-2">Variable</th>
                <th className="px-3 py-2">Where to get it</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['GOOGLE_ADS_DEVELOPER_TOKEN', 'Google Ads → Tools → API Center'],
                ['GOOGLE_ADS_CLIENT_ID', 'Google Cloud Console → OAuth 2.0 Client'],
                ['GOOGLE_ADS_CLIENT_SECRET', 'Same OAuth client'],
                ['GOOGLE_ADS_REFRESH_TOKEN', 'OAuth flow with adwords scope'],
                ['GOOGLE_ADS_CUSTOMER_ID', 'Google Ads account ID'],
                ['GOOGLE_ADS_LOGIN_CUSTOMER_ID', 'Manager (MCC) ID if applicable'],
              ].map(([variable, source]) => (
                <tr key={variable} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-mono text-slate-700">{variable}</td>
                  <td className="px-3 py-2">{source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {config.google_ads_configured ? (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-800">
            OAuth credentials are set in `.env`.
            <div className="mt-2 grid gap-1 font-mono text-xs sm:grid-cols-2">
              {Object.entries(config.masked_credentials).map(([key, value]) => (
                <div key={key}>
                  {key}: {value}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800">
            Missing in `.env`: {config.google_ads_missing.join(', ')}
          </div>
        )}

        <p className="text-xs text-slate-400">
          Run Analyzer fetches the last {config.lookback_days} days ending on your selected date.
        </p>
      </div>
    </DashboardCard>
  )
}
