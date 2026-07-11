# Plan.md — Sentinel AI

| Field | Value |
|-------|-------|
| **Product** | Sentinel AI — Ad Spend Tracker & Overspend Prevention |
| **Version** | 1.0 (Step 1 complete) → Step 2 roadmap |
| **Date** | July 11, 2026 |
| **Repo** | `google-ads-spend-guardian/` |
| **Related docs** | [README.md](./README.md) · [PRD.md](./PRD.md) |

---

## 1. Purpose

This plan translates the PRD into an execution roadmap: what is already shipped, how the system is structured, what remains open, and the ordered work for Step 2+.

**Hackathon use case:** *AI powered spends tracker* — track spend vs budget, flag overspend early, notify stakeholders, quantify NR loss prevention.

---

## 2. Current State (Step 1 — Done)

Step 1 is an implemented MVP with dual UIs sharing the same Python services and agents.

| Capability | Status | Notes |
|------------|--------|-------|
| Sample CSV dashboard (KPIs, charts, alerts, NR impact) | Done | Streamlit + React |
| Risk classification (healthy / warning / critical / over budget) | Done | Configurable thresholds |
| Live Google Ads fetch (GAQL) | Done | Search, Video, Demand Gen, PMax |
| 5-step AI agent pipeline + supervisor | Done | Rules + LLM summaries |
| Stakeholder email alerts (SMTP / demo log) | Done | YAML recipient map |
| AI chatbot over analyzer context | Done | OpenRouter / GPT-4o-mini |
| FastAPI API for React UI | Done | Feature parity with Streamlit |
| Demo auth (React) | Done | `demo@sentinel.ai` / `demo123` |
| Unit tests (pytest) | Done | 20+ test modules |

### 2.1 Recommended runtime (today)

```text
Terminal 1:  uvicorn api.main:app --reload --port 8000
Terminal 2:  cd frontend && npm run dev   →  http://localhost:5173
Legacy:      streamlit run app.py         →  http://localhost:8501
```

### 2.2 What Step 1 deliberately excludes

See PRD §14. Highest-impact gaps for planning:

- Meta Ads API
- Airbyte → BigQuery ingestion
- Multi-account MCC portfolio dashboard
- Campaign pause / bid actions (read-only today)
- Real RBAC / production auth
- Historical alert audit trail
- Full per-campaign daily threshold rules (placeholder agent)

---

## 3. Architecture (as built)

```text
┌──────────────────────────────────────────────────────────────┐
│  React (Vite)  OR  Streamlit (legacy)                         │
│  /dashboard · /campaign-analysis · /budget-alerts             │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP (FastAPI) or in-process
┌────────────────────────────▼─────────────────────────────────┐
│  Services                                                     │
│  CampaignData · SpendAnalytics · Alert · GoogleAdsFetch       │
│  CampaignAnalyzer · DailySnapshot · Email · Pipeline runner   │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│  Agents (sequential pipeline)                                 │
│  Fetch → Account → Daily → Hourly → Campaign                  │
│  → Supervisor (exec summary) → Email agent · Chatbot          │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│  Data / External                                              │
│  sample_campaigns.csv · Google Ads API · OpenRouter · SMTP    │
└──────────────────────────────────────────────────────────────┘
```

### 3.1 Key packages

| Layer | Path |
|-------|------|
| React UI | `frontend/src/` |
| API | `api/main.py`, `api/session_store.py` |
| Streamlit UI | `app.py`, `pages/`, `components/` |
| Domain models | `models/` |
| Business logic | `services/` |
| AI agents | `agents/` |
| Config | `config/settings.py`, `.env`, `config/alert_recipients.yaml` |
| Tests | `tests/` |

---

## 4. Goals & success criteria

| Goal | Measure |
|------|---------|
| G1 Prevent overspend | Flag ≥80% utilization before month-end |
| G2 Fast response | Hourly spike alerts vs 7-day same-hour avg |
| G3 Right stakeholders | Route by campaign type via YAML |
| G4 Quantify impact | Projected overspend + NR loss × multiplier |
| G5 Live + demo | `DATA_SOURCE=sample` or Google Ads credentials |

**Definition of done (Step 1):** Dashboard + analyzer + alerts + emails + chatbot working in sample mode; live mode when Google Ads + OpenRouter (+ optional SMTP) are configured; `pytest -q` green.

---

## 5. Phased delivery plan

### Phase A — Step 1 hardening (near-term)

Keep the MVP stable for demos and reviews.

| # | Task | Owner focus | Priority |
|---|------|-------------|----------|
| A1 | Keep React ↔ FastAPI parity with Streamlit features | Frontend / API | P0 |
| A2 | Complete campaign-wise daily threshold rules (replace placeholder) | Agents | P0 |
| A3 | Document demo script (sample → thresholds → analyzer → email log) | Docs | P1 |
| A4 | Smoke checklist: health, dashboard, analyzer run, chat, budget alerts | QA | P1 |
| A5 | Ensure graceful fallbacks (no LLM / no SMTP / no Ads) stay clear in UI | UX | P1 |
| A6 | Expand API tests where Streamlit-only coverage exists | Tests | P2 |

**Exit criteria:** Reliable hackathon demo path; no silent failures on missing credentials; campaign-level agent checks configurable and tested.

---

### Phase B — Data platform (Step 2 foundation)

Move from on-demand fetch + CSV to durable, multi-source spend data.

| # | Task | Notes | Priority |
|---|------|-------|----------|
| B1 | Airbyte connectors → staging tables | Google Ads first | P0 |
| B2 | BigQuery warehouse schema (campaign, daily, hourly facts) | Align with existing models | P0 |
| B3 | Scheduled sync (hourly / daily) | Replace pure on-demand for dashboard | P0 |
| B4 | Point `CampaignDataService` / analytics at BQ (feature flag) | Keep CSV for demos | P1 |
| B5 | Meta Ads connector + channel-normalized model | README Step 2 | P1 |

**Exit criteria:** Dashboard can load MTD spend from warehouse without manual analyzer run; sample CSV still available for offline demos.

---

### Phase C — Multi-account & productization

| # | Task | Notes | Priority |
|---|------|-------|----------|
| C1 | MCC / multi-customer selector and portfolio rollup | Beyond single account analyzer | P0 |
| C2 | Production auth (replace demo login) | SSO or email+password + sessions | P0 |
| C3 | Role-based access (viewer / marketer / admin) | Stakeholder vs ops personas | P1 |
| C4 | Alert history + audit trail | Persist sends, severity, recipients | P1 |
| C5 | Retire or freeze Streamlit as “legacy analyzer” | React as primary UI | P2 |

**Exit criteria:** Ops can monitor multiple accounts; access is controlled; alerts are queryable after the fact.

---

### Phase D — Action & automation (optional / later)

| # | Task | Notes | Priority |
|---|------|-------|----------|
| D1 | Suggested actions in UI (pause, reduce budget, reallocate) | Human-in-the-loop first | P1 |
| D2 | Optional write-back to Google Ads (pause / budget cap) | Requires strong auth + audit | P2 |
| D3 | Scheduled pipeline jobs (cron / Cloud Scheduler) | Unattended hourly checks | P1 |
| D4 | Mobile-friendly polish / PWA | Not a native app | P2 |

**Exit criteria:** Clear path from alert → recommended action → (optional) approved platform change.

---

## 6. Feature workstreams (cross-cutting)

### 6.1 Spend tracking & dashboard

- Load / aggregate campaigns; utilization; risk; EOM projection; NR loss.
- **Next:** warehouse-backed KPIs; multi-account rollups.

### 6.2 Live analyzer & agents

```text
Fetch → Account (MTD/budget) → Daily (T-1 vs 7d) → Hourly → Campaign
     → Supervisor summary → Email on WARNING/FAIL
```

- **Next:** finish campaign-level rules; scheduled runs; LangGraph path only if it simplifies ops.

### 6.3 Alerting & notifications

- Rule alerts + SMTP; YAML recipients; React/Streamlit preview.
- **Next:** audit log; digest mode; Slack/Teams channel (if stakeholders request).

### 6.4 AI layer

- OpenRouter summaries, email drafts, chatbot.
- **Next:** tighter grounding on warehouse facts; cost controls; eval set for summary quality.

---

## 7. Implementation sequence (recommended)

```text
Now          A1–A5  Harden MVP + finish campaign agent rules
             │
Short term   B1–B4  Airbyte → BigQuery → read path for dashboard
             │
Medium       B5 + C1–C4  Meta + multi-account + auth + alert history
             │
Later        D1–D3  Actions + scheduled pipelines
```

Do not start write-back (D2) before auth, audit trail, and clear approval UX (C2–C4, D1).

---

## 8. Milestones & checkpoints

| Milestone | Deliverable | Checkpoint |
|-----------|-------------|------------|
| **M0** | Step 1 MVP (current) | Demo login → dashboard → analyzer → chat → alerts |
| **M1** | Hardened Step 1 | Campaign agent rules live; smoke checklist signed off |
| **M2** | Warehouse MVP | Airbyte + BQ; dashboard flag to read warehouse |
| **M3** | Multi-platform | Meta spend in same risk model |
| **M4** | Productized access | Real auth + RBAC + alert history |
| **M5** | Closed-loop (optional) | Suggested actions ± controlled Ads write-back |

---

## 9. Configuration required per environment

| Concern | Variables / files |
|---------|-------------------|
| Thresholds & NR | `WARNING_THRESHOLD_PCT`, `CRITICAL_THRESHOLD_PCT`, `NR_LOSS_MULTIPLIER` |
| Demo data | `DATA_SOURCE=sample`, `DATA_CSV_PATH` |
| Google Ads | `GOOGLE_ADS_*` |
| LLM | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` |
| Email | `SMTP_*`, `ALERT_FROM_EMAIL`, `config/alert_recipients.yaml` |
| React API | `VITE_API_BASE_URL` (optional) |

Copy `.env.example` → `.env` before first run. Never commit secrets.

---

## 10. Testing & quality plan

| Layer | Approach |
|-------|----------|
| Unit | `pytest -q` — agents, services, utils, pipeline UI helpers |
| API | Health, dashboard, budget-alerts, analyzer session, chat |
| Manual demo | Sample mode without Ads/SMTP; live mode with credentials |
| Regression | Keep Streamlit paths green until React is declared sole UI |

Add tests whenever agent rules or NR formulas change.

---

## 11. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Google Ads API / token friction | Sample CSV + credentials panel; connection scripts under `scripts/` |
| LLM unavailable in demos | Rule checks still run; clear “AI unavailable” copy |
| SMTP blocked | Log alert body in UI (demo mode) |
| Dual UI drift | Treat FastAPI as source of truth for React; parity checklist (A1) |
| Scope creep into write-back | Gate D2 behind M4 auth/audit |

---

## 12. Out-of-scope reminders (do not pull into M1)

- Native mobile apps  
- Full MCC portfolio UX before warehouse (B)  
- Unattended bid/pause automation without human approval  
- Replacing rule engines with LLM-only decisions  

---

## 13. Immediate next actions

1. Run React + API demo path and confirm M0 checklist.  
2. Implement real rules in `campaign_daily_snapshot_agent` (A2) + tests.  
3. Draft Airbyte → BigQuery schema sketch aligned to `CampaignSpend` / daily / hourly models (B2).  
4. Decide primary UI (React) and freeze Streamlit feature adds except critical fixes (C5 prep).

---

*Plan aligns with PRD v1.0 (July 11, 2026). Update this file when milestones M1+ complete or Step 2 scope is locked.*
