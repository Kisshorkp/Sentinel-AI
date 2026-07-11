# React UI + FastAPI backend

## Run both servers

**Terminal 1 — API (port 8000):**
```bash
cd google-ads-spend-guardian
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

**Terminal 2 — React UI (port 5173):**
```bash
cd google-ads-spend-guardian/frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## Demo login
- Email: `demo@sentinel.ai`
- Password: `demo123`

## Streamlit parity

| Streamlit | React route |
|-----------|-------------|
| `app.py` Dashboard | `/dashboard` |
| Campaign Analysis → Google Ads Analyzer | `/campaign-analysis` (Analyzer tab) |
| Campaign Analysis → AI Chat | `/campaign-analysis` (Chat tab) |
| Campaign Analysis → Sample Data | `/campaign-analysis` (Sample tab) |
| Budget Alerts | `/budget-alerts` |

Pipeline steps in React: **Fetch → Account → Daily → Hourly → Campaign** (same as Streamlit).

## Environment
Uses the same `.env` as Streamlit (`GOOGLE_ADS_*`, `OPENROUTER_API_KEY`, etc.).

Optional frontend override:
```env
VITE_API_BASE_URL=http://localhost:8000
```
