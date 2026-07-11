# Sentinel AI — Ad Spend Tracker & Overspend Prevention

Streamlit dashboard for the hackathon use case **"AI powered spends tracker"**:

- Track ad spend against permissible budget limits
- Flag overspend and at-risk campaigns in real time
- Notify stakeholders with actionable alerts
- Quantify NR (net revenue) loss prevention

## Architecture

```text
data/sample_campaigns.csv
        ↓
CampaignDataService → SpendAnalyticsService / AlertService
        ↓
Streamlit Dashboard (app.py) + Analysis Pages
```

Step 1 uses sample Google Ads campaign data. Step 2 will connect live Google Ads / Meta APIs and Airbyte → BigQuery ingestion.

## Quick Start

### React UI (recommended)

Modern dashboard UI with login, toasts, loaders — **full Streamlit feature parity** via FastAPI backend.

**Terminal 1 — API:**
```bash
cd google-ads-spend-guardian
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

**Terminal 2 — React:**
```bash
cd google-ads-spend-guardian/frontend
npm install
npm run dev
```

Open **http://localhost:5173**

**Demo login:** `demo@sentinel.ai` / `demo123`

| React route | Streamlit equivalent |
|-------------|---------------------|
| `/dashboard` | `app.py` |
| `/campaign-analysis` → Analyzer tab | Google Ads Analyzer + 5-step pipeline |
| `/campaign-analysis` → Chat tab | AI Chat |
| `/campaign-analysis` → Sample tab | Sample Data |
| `/budget-alerts` | `pages/2_budget_alerts.py` |

### Streamlit backend (legacy analyzer)

```bash
cd google-ads-spend-guardian
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Open **http://localhost:8501**

## Modules

| Module | Purpose |
|--------|---------|
| **React Frontend** (`frontend/`) | Login, dashboard, campaign analysis, budget alerts, toasts & loaders |
| **Dashboard** (`app.py`) | KPIs, spend vs budget chart, utilization gauge, alerts, campaign table |
| **Campaign Analysis** | Stakeholder filters, spend distribution, top overspend risk |
| **Budget Alerts** | Adjustable thresholds, stakeholder notification preview |

## Configuration

Edit `.env`:

```env
WARNING_THRESHOLD_PCT=80
CRITICAL_THRESHOLD_PCT=100
NR_LOSS_MULTIPLIER=1.35
DATA_SOURCE=sample
```

## Tests

```bash
pytest -q
```

## Hackathon Impact

This step directly addresses reviewer feedback by providing:

1. A concrete solution (not just an idea)
2. Quantified business impact (projected overspend, NR loss prevented)
3. Real-time stakeholder alerting workflow
4. Clean, testable Python architecture
