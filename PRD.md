# Product Requirements Document (PRD)

## Sentinel AI — Ad Spend Tracker & Overspend Prevention System

| Field | Value |
|-------|-------|
| **Product Name** | Sentinel AI |
| **Version** | 1.0 (Step 1 — Dashboard & Live Analyzer) |
| **Date** | July 11, 2026 |
| **Repository** | `google-ads-spend-guardian/` |
| **Status** | Implemented (hackathon MVP) |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [Technology Stack](#4-technology-stack)
5. [User Personas](#5-user-personas)
6. [Product Screens & User Flows](#6-product-screens--user-flows)
7. [Functional Requirements](#7-functional-requirements)
8. [Business Rules & Thresholds](#8-business-rules--thresholds)
9. [AI Agent Pipeline](#9-ai-agent-pipeline)
10. [Integrations](#10-integrations)
11. [Data Model](#11-data-model)
12. [Configuration & Environment](#12-configuration--environment)
13. [Non-Functional Requirements](#13-non-functional-requirements)
14. [Out of Scope](#14-out-of-scope)
15. [Appendix — Code-to-Feature Mapping](#15-appendix--code-to-feature-mapping)

---

## 1. Executive Summary

**Sentinel AI** is an AI-powered Google Ads spend monitoring platform that helps marketing teams track campaign spend against permissible budget limits, detect overspend early, notify stakeholders with actionable alerts, and quantify net revenue (NR) loss prevention.

The product combines:

- A **real-time Streamlit dashboard** for portfolio-level visibility
- A **live Google Ads analyzer** with a 5-step AI agent pipeline
- **Rule-based threshold checks** plus **LLM-generated summaries** for stakeholders
- **Email alerting** routed by campaign type and stakeholder

This MVP directly addresses the hackathon use case *"AI powered spends tracker"* by delivering a working solution — not just a concept — with quantified business impact, testable Python architecture, and stakeholder notification workflows.

---

## 2. Problem Statement

### 2.1 Business Problem

Marketing teams running Google Ads campaigns frequently exceed permissible spend limits because:

- Spend data is fragmented across campaign types (Search, Video, Demand Gen, Performance Max)
- Budget pacing is checked manually and infrequently
- Stakeholders are notified too late — after overspend has already occurred
- There is no quantified view of NR (net revenue) loss from uncontrolled spend

### 2.2 Core Pain Points

| Pain Point | Impact |
|------------|--------|
| Spend exceeds monthly budget | Direct NR loss |
| No early warning at 80% utilization | Reactive instead of proactive management |
| Hourly spend spikes go unnoticed | Intraday overspend before daily review |
| Stakeholders lack campaign-type-specific alerts | Delayed corrective action |
| No executive summary of spend health | Leadership lacks decision-ready insights |

### 2.3 Solution

Sentinel AI provides:

1. **Real-time visibility** — dashboard KPIs, charts, and campaign tables
2. **Multi-layer checks** — account, daily, hourly, and campaign-level analysis
3. **AI summaries** — LLM-generated stakeholder-ready narratives
4. **Automated alerts** — email notifications on threshold failures
5. **NR loss quantification** — projected overspend × NR loss multiplier

---

## 3. Goals & Success Metrics

### 3.1 Product Goals

| # | Goal | Description |
|---|------|-------------|
| G1 | Prevent overspend | Flag campaigns at ≥80% budget before month-end |
| G2 | Enable fast response | Hourly overspend alerts for current-hour spikes |
| G3 | Notify the right people | Route alerts by campaign type to configured stakeholders |
| G4 | Quantify business impact | Show projected overspend and NR loss prevented |
| G5 | Support live + demo modes | Work with sample CSV data or live Google Ads API |

### 3.2 Success Metrics (KPIs)

| Metric | Source | Target |
|--------|--------|--------|
| Campaigns at risk detected | `SpendAnalyticsService` → `campaigns_at_risk` | 100% of campaigns above warning threshold |
| Campaigns over budget | `DashboardSummary.campaigns_over_budget` | Zero missed over-budget campaigns |
| Projected overspend ($) | `DashboardSummary.projected_overspend` | Visible on dashboard |
| NR loss prevented estimate ($) | `DashboardSummary.prevented_loss_estimate` | Quantified with `NR_LOSS_MULTIPLIER` |
| Alert delivery | `email_agent.py` → `email_sent` flag | Email sent on FAIL/WARNING checks |
| Agent pipeline completion | `sequential_pipeline.py` step status | All 5 steps complete without error |

---

## 4. Technology Stack

### 4.1 Core Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Language | **Python** | 3.x | Backend, agents, services |
| Frontend / UI | **Streamlit** | ≥1.59.0 | Web dashboard & multi-page app |
| Data processing | **Pandas** | ≥2.2.0 | CSV loading, tables, chart data |
| Visualization | **Plotly** | ≥5.24.0 | Bar charts, utilization gauges |
| Data validation | **Pydantic** | ≥2.9.0 | Domain models, type safety |
| Configuration | **pydantic-settings** | ≥2.6.0 | `.env` settings management |
| Environment | **python-dotenv** | ≥1.0.0 | Load `.env` variables |
| Config files | **PyYAML** | ≥6.0.0 | Alert recipient mapping |
| Testing | **pytest** | ≥8.3.0 | Unit & integration tests |

### 4.2 External Integrations

| Integration | Technology | Purpose |
|-------------|------------|---------|
| Google Ads API | **google-ads** SDK ≥25.0.0 | Live campaign spend fetch via GAQL |
| Google Ads Auth | **OAuth 2.0** | client_id, client_secret, refresh_token |
| LLM | **LangChain** + **LangChain-OpenAI** | AI summaries & chatbot |
| LLM Provider | **OpenRouter** | Routes to `openai/gpt-4o-mini` |
| Agent orchestration | **LangGraph** | Optional graph-based agent pipeline |
| Email | **Python smtplib** | SMTP alert delivery |

### 4.3 Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│                     STREAMLIT UI (Frontend)                      │
│  app.py │ pages/1_campaign_analysis │ pages/2_budget_alerts     │
│  components/ (charts, tables, alerts, pipeline, chat)           │
│  Tech: Streamlit, Plotly, Pandas                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     SERVICES LAYER                               │
│  CampaignDataService │ SpendAnalyticsService │ AlertService     │
│  GoogleAdsFetchService │ CampaignAnalyzerService │ EmailService  │
│  Tech: Pandas, google-ads SDK, smtplib                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     AI AGENTS LAYER                              │
│  sequential_pipeline │ analyzer_table │ daily_snapshot │ hourly │
│  campaign_daily_snapshot │ supervisor │ email_agent │ chatbot    │
│  Tech: LangChain, LangGraph, OpenRouter (GPT-4o-mini)           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     DATA / EXTERNAL                              │
│  CSV (sample) │ Google Ads API (GAQL) │ SMTP │ OpenRouter API │
│  Tech: Pandas, google-ads SDK, OAuth 2.0, PyYAML                │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Data Flow

```text
data/sample_campaigns.csv  OR  Google Ads API (GAQL)
        ↓
CampaignDataService / GoogleAdsFetchService
        ↓
Pydantic Models (CampaignSpend, AnalyzerResult)
        ↓
Services (SpendAnalytics, AlertService)
        ↓
AI Agents (threshold checks + LLM summaries)
        ↓
Streamlit UI (Plotly charts) + Email Alerts (SMTP)
```

---

## 5. User Personas

### 5.1 Marketing Lead (Primary User)

- **Role:** Manages Google Ads campaigns across Search, Video, Demand Gen, PMax
- **Needs:** Daily spend visibility, overspend warnings, campaign-type breakdown
- **Uses:** Dashboard, Campaign Analysis page, Run Analyzer pipeline

### 5.2 Stakeholder / Budget Owner

- **Role:** Owns budget for a campaign type (e.g., Search campaigns)
- **Needs:** Email alerts when spend checks fail, clear actionable messages
- **Uses:** Receives emails from `config/alert_recipients.yaml` mapping

### 5.3 Operations / Analytics Team

- **Role:** Configures thresholds, monitors pipeline health
- **Needs:** Adjustable warning/critical thresholds, credential setup, test data mode
- **Uses:** Budget Alerts page, `.env` configuration, credentials panel

---

## 6. Product Screens & User Flows

### 6.1 Screen 1 — Sentinel AI Dashboard

| Attribute | Detail |
|-----------|--------|
| **File** | `app.py` |
| **Technology** | Streamlit, Plotly, Pandas |
| **Route** | `/` (main page) |

**Features:**

| Component | File | Technology |
|-----------|------|------------|
| KPI metrics row | `components/metrics_row.py` | Streamlit `st.metric` |
| Spend vs budget chart | `components/spend_chart.py` | Pandas + Plotly Express |
| Utilization gauge | `components/budget_gauge.py` | Plotly gauge |
| Real-time alerts panel | `components/alert_panel.py` | Streamlit |
| Campaign spend table | `components/campaign_table.py` | Streamlit + Pandas |
| Business impact summary | `app.py` | Streamlit metrics |

**User Flow:**

```text
Open app → Load campaigns (CSV) → View KPIs → Review chart & gauge
        → Read alerts → Inspect campaign table → See NR impact summary
```

---

### 6.2 Screen 2 — Campaign Analysis

| Attribute | Detail |
|-----------|--------|
| **File** | `pages/1_campaign_analysis.py` |
| **Technology** | Streamlit, Pandas, Plotly, Google Ads SDK, LangChain |
| **Route** | `/1_campaign_analysis` |

**Features:**

| Feature | Component / Service | Technology |
|---------|---------------------|------------|
| Sample data view | `CampaignDataService` | Pandas CSV |
| Stakeholder filter | Streamlit selectbox | Streamlit |
| Spend distribution chart | Plotly Express | Plotly |
| Google Ads credentials info | `components/credentials_panel.py` | Streamlit |
| Analyzer form (account, dates, budgets) | `components/analyzer_form.py` | Streamlit forms |
| Live Google Ads fetch | `GoogleAdsFetchService` | google-ads SDK + GAQL |
| 5-step agent pipeline UI | `components/agent_pipeline_ui.py` | Streamlit + HTML |
| Pipeline step details | `components/pipeline_step_detail.py` | Streamlit |
| Agent summary panel | `components/agent_summary_panel.py` | Streamlit |
| Campaign daily snapshot table | `components/campaign_daily_snapshot_table.py` | Pandas |
| AI chatbot | `components/chat_panel.py` | LangChain ChatOpenAI |

**User Flow — Live Analyzer:**

```text
Enter account ID + date range + budgets per campaign type
        ↓
Click "Run Analyzer" → Fetch from Google Ads API
        ↓
Agent Pipeline runs sequentially:
  1. Fetch (Google Ads) → 2. Account-wise → 3. Daily-wise
  → 4. Hourly → 5. Campaign-wise
        ↓
Supervisor merges reports + LLM executive summary
        ↓
Email alerts sent on FAIL/WARNING checks
        ↓
User reviews tables, agent reports, and chats with AI
```

---

### 6.3 Screen 3 — Budget Alerts

| Attribute | Detail |
|-----------|--------|
| **File** | `pages/2_budget_alerts.py` |
| **Technology** | Streamlit |
| **Route** | `/2_budget_alerts` |

**Features:**

| Feature | Technology |
|---------|------------|
| Warning threshold slider (50–95%) | Streamlit slider |
| Critical threshold slider (80–110%) | Streamlit slider |
| Active alerts list | `AlertService` + `alert_panel.py` |
| Stakeholder notification preview | Streamlit expanders |

**User Flow:**

```text
Adjust warning/critical thresholds → View regenerated alerts
        → Preview email content per stakeholder → Take action
```

---

## 7. Functional Requirements

### 7.1 Spend Tracking & Dashboard (FR-01 to FR-06)

| ID | Requirement | Code | Technology |
|----|-------------|------|------------|
| FR-01 | Load campaign data from CSV or sample file | `services/campaign_data_service.py` | Pandas |
| FR-02 | Calculate budget utilization % per campaign | `models/campaign.py` → `utilization_pct` | Pydantic computed field |
| FR-03 | Classify risk level (healthy / warning / critical / over budget) | `models/campaign.py` → `risk_level()` | Python enum logic |
| FR-04 | Project month-end spend based on MTD pacing | `models/campaign.py` → `projected_month_end_spend` | Python date math |
| FR-05 | Aggregate portfolio KPIs (total budget, spend, at-risk count) | `services/spend_analytics_service.py` | Python aggregation |
| FR-06 | Quantify NR loss prevented | `SpendAnalyticsService` × `NR_LOSS_MULTIPLIER` | Configurable multiplier |

### 7.2 Alerting (FR-07 to FR-10)

| ID | Requirement | Code | Technology |
|----|-------------|------|------------|
| FR-07 | Generate alerts for campaigns above warning threshold | `services/alert_service.py` | Python |
| FR-08 | Sort alerts by severity (over budget > critical > warning) | `AlertService.generate_alerts()` | Python sort |
| FR-09 | Build stakeholder-specific alert messages | `AlertService._build_message()` | Python string templates |
| FR-10 | Preview notification content per stakeholder | `pages/2_budget_alerts.py` | Streamlit |

### 7.3 Live Google Ads Analyzer (FR-11 to FR-15)

| ID | Requirement | Code | Technology |
|----|-------------|------|------------|
| FR-11 | Accept account ID, date range, and per-type budgets | `models/analyzer_input.py` | Pydantic |
| FR-12 | Fetch live spend via Google Ads API (GAQL) | `services/google_ads_fetch_service.py` | google-ads SDK |
| FR-13 | Support 4 campaign channel types | `ANALYZER_LABELS` in fetch service | GAQL channel filter |
| FR-14 | Compute MTD achieve, MTD target, 7-day averages | `utils/mtd_metrics.py` | Python date math |
| FR-15 | Display raw fetch records in pipeline preview | `pipeline_step_detail.py` | Streamlit |

**Supported Campaign Types:**

| Channel Type | Label |
|--------------|-------|
| SEARCH | Search campaigns |
| VIDEO | Video campaigns |
| DEMAND_GEN | Demand Gen campaigns |
| PERFORMANCE_MAX | Performance Max campaigns |

### 7.4 AI Agent Checks (FR-16 to FR-22)

| ID | Requirement | Code | Technology |
|----|-------------|------|------------|
| FR-16 | Account-wise: budget utilization + MTD target checks | `agents/analyzer_table_agent.py` | Rule engine + LangChain |
| FR-17 | Daily-wise: T-1 vs 7-day avg + consecutive low spend | `agents/daily_snapshot_agent.py` | Rule engine + LangChain |
| FR-18 | Hourly: current-hour overspend vs 7-day same-hour avg | `agents/hourly_agent.py` | Rule engine + LangChain |
| FR-19 | Campaign-wise: per-campaign daily snapshot checks | `agents/campaign_daily_snapshot_agent.py` | Rule engine + LangChain |
| FR-20 | Supervisor: merge all reports + executive LLM summary | `agents/supervisor.py` | LangChain |
| FR-21 | Run agents sequentially with live pipeline UI | `agents/sequential_pipeline.py` | Python + Streamlit |
| FR-22 | Optional LangGraph orchestration | `agents/graph.py` | LangGraph StateGraph |

### 7.5 Email & Chat (FR-23 to FR-26)

| ID | Requirement | Code | Technology |
|----|-------------|------|------------|
| FR-23 | Send email on agent check FAIL/WARNING | `agents/email_agent.py` | LangChain + SMTP |
| FR-24 | Map recipients by campaign type (YAML) | `config/alert_recipients.yaml` | PyYAML |
| FR-25 | LLM-draft professional email body | `email_agent.py` + `invoke_summary()` | LangChain |
| FR-26 | Chatbot answers questions from analyzer context | `agents/chatbot_agent.py` | LangChain ChatOpenAI |

---

## 8. Business Rules & Thresholds

### 8.1 Dashboard Risk Classification

| Risk Level | Condition | Code |
|------------|-----------|------|
| **Healthy** | Utilization < warning threshold (default 80%) | `RiskLevel.HEALTHY` |
| **Warning** | Utilization ≥ 80% and < 100% | `RiskLevel.WARNING` |
| **Critical** | Utilization ≥ 100% but spend ≤ budget | `RiskLevel.CRITICAL` |
| **Over Budget** | Utilization ≥ 100% and spend > budget | `RiskLevel.OVER_BUDGET` |

### 8.2 Configurable Thresholds

| Setting | Default | Used By | Description |
|---------|---------|---------|-------------|
| `WARNING_THRESHOLD_PCT` | 80 | Dashboard, analyzer agent | High utilization warning |
| `CRITICAL_THRESHOLD_PCT` | 100 | Dashboard, analyzer agent | Budget limit reached |
| `NR_LOSS_MULTIPLIER` | 1.35 | Spend analytics | NR loss estimate multiplier |
| `MTD_TARGET_TOLERANCE_PCT` | 5 | Account-wise agent | MTD achieve vs target band |
| `DAILY_SPEND_VS_7DAY_TOLERANCE_PCT` | 20 | Daily-wise agent | T-1 deviation from 7-day avg |
| `LOW_DAILY_SPEND_BUDGET_PCT` | 50 | Daily-wise agent | Low spend threshold (% of daily budget) |
| `LOW_DAILY_SPEND_CONSECUTIVE_DAYS` | 3 | Daily-wise agent | Consecutive low-spend days to flag |
| `HOURLY_OVERSPEND_MIN_COST` | 1000 | Hourly agent | Minimum spend to trigger hourly alert |
| `HOURLY_OVERSPEND_VS_7DAY_PCT` | 50 | Hourly agent | % above 7-day same-hour avg to flag |

### 8.3 Agent Check Rules (Detail)

#### Account-wise Agent (`analyzer_table_agent.py`)

| Rule ID | Check | Pass | Warning | Fail |
|---------|-------|------|---------|------|
| `budget_used_pct` | Cost / Budget × 100 | < 80% | ≥ 80% | ≥ 100% |
| `mtd_achieve_above_target` | MTD achieve vs MTD target | ≤ target + 5% | > target + 5% | — |
| `mtd_achieve_below_target` | MTD achieve vs MTD target | ≥ target − 5% | < target − 5% | — |

#### Daily-wise Agent (`daily_snapshot_agent.py`)

| Rule ID | Check | Pass | Warning |
|---------|-------|------|---------|
| `t1_vs_7day_avg` | T-1 cost vs 7-day daily average | Within ±20% | Outside ±20% |
| `consecutive_low_daily_spend` | Days below 50% of prorated daily budget | < 3 consecutive days | ≥ 3 consecutive days |

#### Hourly Agent (`hourly_agent.py`)

| Rule ID | Check | Pass | Fail |
|---------|-------|------|------|
| `current_hour_overspend` | Current hour spend vs 7-day same-hour avg | ≤ $1,000 OR ≤ 50% above avg | > $1,000 AND > 50% above avg |

#### Campaign-wise Agent (`campaign_daily_snapshot_agent.py`)

| Rule ID | Status |
|---------|--------|
| `campaign_daily_checks` | Placeholder — per-campaign rules pending configuration |

### 8.4 NR Loss Calculation

```text
For each campaign:
  - If over budget: projected_overspend += (spend_mtd - monthly_budget)
  - If projected EOM > budget: projected_overspend += (projected_EOM - budget)
  - If warning/critical: prevented_loss += (budget - spend_mtd) × 0.15

NR loss estimate = (projected_overspend + prevented_loss) × NR_LOSS_MULTIPLIER
```

**Code:** `services/spend_analytics_service.py`

### 8.5 Email Trigger Rules

| Trigger | When | Recipients |
|---------|------|------------|
| Analyzer table alert | Agent check = WARNING or FAIL on Run Analyzer | Campaign type from `alert_recipients.yaml` |
| Daily snapshot alert | Agent check = WARNING or FAIL on Run Analyzer | Campaign type from YAML |
| Hourly alert | Agent check = FAIL on Extract | Campaign type from YAML |
| Campaign daily alert | Agent check = WARNING or FAIL on Run Analyzer | Campaign type from YAML |

**Demo mode:** When SMTP is not configured, emails are logged to the Streamlit UI instead of sent.

---

## 9. AI Agent Pipeline

### 9.1 Pipeline Overview

The agent pipeline runs **5 sequential steps** after a Google Ads fetch, orchestrated by `agents/sequential_pipeline.py` and visualized in `components/agent_pipeline_ui.py`.

```text
Step 1: FETCH        → Google Ads API data pull (GAQL)
Step 2: ACCOUNT      → analyzer_table_agent (MTD & budget checks)
Step 3: DAILY        → daily_snapshot_agent (daily spend checks)
Step 4: HOURLY       → hourly_agent (current-hour overspend)
Step 5: CAMPAIGN     → campaign_daily_snapshot_agent (per-campaign checks)
        ↓
SUPERVISOR           → Merge reports + LLM executive summary
        ↓
EMAIL AGENT          → Send alerts for FAIL/WARNING checks
```

### 9.2 Agent Details

| Step | Agent | Input | Output | LLM Used |
|------|-------|-------|--------|----------|
| Account-wise | `analyzer_table_agent` | `AnalyzerResult.fields` | `list[TableAgentReport]` | Per-field summary |
| Daily-wise | `daily_snapshot_agent` | `AnalyzerResult.fields` | `list[TableAgentReport]` | Per-field summary |
| Hourly | `hourly_agent` | Hourly rows per campaign type | `TableAgentReport` | Per-type summary |
| Campaign-wise | `campaign_daily_snapshot_agent` | `CampaignDailySnapshotRow[]` | Reports + overall summary | One overall summary |
| Supervisor | `supervisor` | All agent reports | `PipelineAgentReport` | Executive summary |
| Email | `email_agent` | Failing reports | SMTP email | Email body draft |
| Chatbot | `chatbot_agent` | User question + context JSON | Text response | Full conversation |

### 9.3 Severity Model

| Level | Meaning | Trigger |
|-------|---------|---------|
| `healthy` | All checks pass | No WARNING or FAIL |
| `warning` | At least one WARNING check | Threshold deviation |
| `critical` | At least one FAIL check | Budget exceeded or hourly overspend |

**Code:** `models/agent_report.py` → `Severity`, `CheckStatus`

### 9.4 LLM Configuration

| Setting | Default | Purpose |
|---------|---------|---------|
| `OPENROUTER_API_KEY` | (required for AI) | API authentication |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Model selection |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | API endpoint |
| Temperature | 0.2 | Low creativity for factual summaries |

**Fallback:** When `OPENROUTER_API_KEY` is missing, summaries display: *"AI summary unavailable — add OPENROUTER_API_KEY to .env."*

---

## 10. Integrations

### 10.1 Google Ads API

| Attribute | Detail |
|-----------|--------|
| **SDK** | `google-ads>=25.0.0` |
| **Auth** | OAuth 2.0 (developer token + client credentials + refresh token) |
| **Query Language** | GAQL (Google Ads Query Language) |
| **Client Factory** | `clients/google_ads_client.py` |
| **Fetch Service** | `services/google_ads_fetch_service.py` |
| **Daily Snapshot** | `services/campaign_daily_snapshot_service.py` |

**Required Credentials:**

| Variable | Source |
|----------|--------|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads → Tools → API Center |
| `GOOGLE_ADS_CLIENT_ID` | Google Cloud Console → OAuth 2.0 Client |
| `GOOGLE_ADS_CLIENT_SECRET` | Google Cloud Console → OAuth 2.0 Client |
| `GOOGLE_ADS_REFRESH_TOKEN` | OAuth flow with `adwords` scope |
| `GOOGLE_ADS_CUSTOMER_ID` | Google Ads account ID |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | MCC account ID (if applicable) |

**GAQL Query (Daily Metrics):**

```sql
SELECT
  campaign.advertising_channel_type,
  segments.date,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value
FROM campaign
WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
  AND campaign.status != 'REMOVED'
```

### 10.2 OpenRouter LLM

| Attribute | Detail |
|-----------|--------|
| **Library** | `langchain-openai` (ChatOpenAI) |
| **Provider** | OpenRouter |
| **Default Model** | `openai/gpt-4o-mini` |
| **Used For** | Agent summaries, email drafts, chatbot, supervisor executive summary |
| **Code** | `agents/llm.py` |

### 10.3 SMTP Email

| Attribute | Detail |
|-----------|--------|
| **Library** | Python `smtplib` + `email.mime.text.MIMEText` |
| **Protocol** | SMTP with STARTTLS |
| **Code** | `services/email_service.py` |
| **Recipients Config** | `config/alert_recipients.yaml` |

**Recipient Mapping:**

| Campaign Type | Example Recipient |
|---------------|-------------------|
| Search campaigns | spend-lead@example.com |
| Video campaigns | video-lead@example.com |
| Demand Gen campaigns | demandgen-lead@example.com |
| Performance Max campaigns | pmax-lead@example.com |

### 10.4 Sample Data (Demo Mode)

| Attribute | Detail |
|-----------|--------|
| **File** | `data/sample_campaigns.csv` |
| **Loader** | `services/campaign_data_service.py` |
| **Technology** | Pandas `read_csv` |
| **Config** | `DATA_SOURCE=sample` in `.env` |

---

## 11. Data Model

### 11.1 Core Entities

#### CampaignSpend (`models/campaign.py`)

| Field | Type | Description |
|-------|------|-------------|
| `campaign_id` | string | Unique campaign identifier |
| `campaign_name` | string | Display name |
| `platform` | string | Default: "Google Ads" |
| `stakeholder` | string | Budget owner / notify target |
| `monthly_budget` | float | Permissible monthly spend |
| `spend_mtd` | float | Month-to-date spend |
| `spend_yesterday` | float | Previous day spend |
| `conversions` | int | Conversion count |
| `cost_per_conversion` | float | CPA |
| `last_updated` | date | Data freshness date |
| `utilization_pct` | computed | spend_mtd / monthly_budget × 100 |
| `remaining_budget` | computed | monthly_budget − spend_mtd |
| `projected_month_end_spend` | computed | Pacing-based EOM projection |

#### SpendAlert (`models/campaign.py`)

| Field | Type | Description |
|-------|------|-------------|
| `campaign_id` | string | Campaign reference |
| `campaign_name` | string | Display name |
| `stakeholder` | string | Notification target |
| `risk_level` | RiskLevel enum | healthy / warning / critical / over_budget |
| `message` | string | Human-readable alert text |
| `utilization_pct` | float | Current utilization |
| `overspend_amount` | float | Amount over budget (if any) |

#### DashboardSummary (`models/campaign.py`)

| Field | Type | Description |
|-------|------|-------------|
| `total_budget` | float | Sum of all campaign budgets |
| `total_spend_mtd` | float | Sum of all MTD spend |
| `utilization_pct` | float | Portfolio utilization |
| `campaigns_at_risk` | int | Count above warning threshold |
| `campaigns_over_budget` | int | Count exceeding budget |
| `projected_overspend` | float | Estimated overspend ($) |
| `prevented_loss_estimate` | float | NR loss prevented ($) |
| `total_conversions` | int | Sum of conversions |
| `avg_cost_per_conversion` | float | Portfolio CPA |

### 11.2 Analyzer Entities

#### CampaignFieldInput (`models/analyzer_input.py`)

| Field | Type | Description |
|-------|------|-------------|
| `label` | string | Campaign type label |
| `budget` | float | Entered budget for date range |
| `cost` | float | Total cost in range |
| `mtd_achieve` | float | MTD achievement value |
| `mtd_target` | float | MTD target value |
| `t1_cost` | float | T-1 day cost |
| `t2_cost` | float | T-2 day cost |
| `t1_7day_avg_cost` | float | 7-day average ending T-1 |
| `today_cost` | float | Today's cost so far |
| `start_date` / `end_date` | date | Analysis date range |

#### AnalyzerResult (`models/analyzer_input.py`)

| Field | Type | Description |
|-------|------|-------------|
| `account` | string | Google Ads customer ID |
| `fields` | list[CampaignFieldInput] | One per campaign type |
| `fetched_at` | datetime | Fetch timestamp |

### 11.3 Agent Report Entities

#### ThresholdCheck (`models/agent_report.py`)

| Field | Type | Description |
|-------|------|-------------|
| `rule` | string | Rule identifier |
| `threshold` | string | Expected threshold (human-readable) |
| `actual` | string | Actual value observed |
| `status` | CheckStatus | pass / warning / fail |
| `message` | string | Explanation text |

#### TableAgentReport (`models/agent_report.py`)

| Field | Type | Description |
|-------|------|-------------|
| `table_name` | string | Analyzer results / Daily spend / Hourly / Campaign daily |
| `campaign_type` | string | Campaign type label |
| `checks` | list[ThresholdCheck] | All threshold checks run |
| `severity` | Severity | healthy / warning / critical |
| `summary` | string | LLM-generated summary |
| `email_sent` | bool | Whether alert email was sent |

#### PipelineAgentReport (`models/agent_report.py`)

| Field | Type | Description |
|-------|------|-------------|
| `analyzer_table` | list[TableAgentReport] | Account-wise reports |
| `daily_snapshot` | list[TableAgentReport] | Daily-wise reports |
| `hourly` | TableAgentReport | Hourly report (worst across types) |
| `campaign_daily_snapshot` | list[TableAgentReport] | Per-campaign reports |
| `campaign_daily_overall` | TableAgentReport | Overall campaign summary |
| `overall_severity` | Severity | Worst severity across all agents |
| `overall_summary` | string | LLM executive summary |

---

## 12. Configuration & Environment

### 12.1 Environment Variables (`.env`)

```env
# Application
APP_TITLE=Sentinel AI
APP_CURRENCY=USD

# Budget thresholds
WARNING_THRESHOLD_PCT=80
CRITICAL_THRESHOLD_PCT=100
NR_LOSS_MULTIPLIER=1.35

# Demo data
DATA_SOURCE=sample
DATA_CSV_PATH=data/sample_campaigns.csv

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CLIENT_ID=
GOOGLE_ADS_CLIENT_SECRET=
GOOGLE_ADS_REFRESH_TOKEN=
GOOGLE_ADS_CUSTOMER_ID=
GOOGLE_ADS_LOGIN_CUSTOMER_ID=
GOOGLE_ADS_LOOKBACK_DAYS=90

# OpenRouter LLM
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Agent thresholds
MTD_TARGET_TOLERANCE_PCT=5
DAILY_SPEND_VS_7DAY_TOLERANCE_PCT=20
LOW_DAILY_SPEND_BUDGET_PCT=50
LOW_DAILY_SPEND_CONSECUTIVE_DAYS=3
HOURLY_OVERSPEND_MIN_COST=1000
HOURLY_OVERSPEND_VS_7DAY_PCT=50

# Email alerts
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ALERT_FROM_EMAIL=
```

**Settings loader:** `config/settings.py` (pydantic-settings)

### 12.2 Alert Recipients (`config/alert_recipients.yaml`)

```yaml
Search campaigns:
  - spend-lead@example.com
Video campaigns:
  - video-lead@example.com
Demand Gen campaigns:
  - demandgen-lead@example.com
Performance Max campaigns:
  - pmax-lead@example.com
```

### 12.3 Streamlit Theme (`.streamlit/config.toml`)

| Setting | Value |
|---------|-------|
| Primary color | `#2563EB` (blue) |
| Background | `#0F172A` (dark slate) |
| Secondary background | `#1E293B` |
| Text color | `#F8FAFC` |

---

## 13. Non-Functional Requirements

| ID | Requirement | Implementation | Technology |
|----|-------------|----------------|------------|
| NFR-01 | Configurable via environment variables | `config/settings.py` | pydantic-settings |
| NFR-02 | Type-safe domain models | `models/` | Pydantic v2 |
| NFR-03 | Unit test coverage | `tests/` (20+ test files) | pytest |
| NFR-04 | Credential masking in UI | `utils/masking.py` | Python |
| NFR-05 | Graceful fallback when LLM unavailable | `agents/llm.py` | Error message in UI |
| NFR-06 | Graceful fallback when SMTP unavailable | `agents/email_agent.py` | Log to Streamlit |
| NFR-07 | Graceful fallback when Google Ads unavailable | `credentials_panel.py` | Setup instructions |
| NFR-08 | Dark theme UI | `.streamlit/config.toml` | Streamlit theme |
| NFR-09 | Modular service/agent architecture | Package structure | Python packages |
| NFR-10 | Sample data mode for demos | `DATA_SOURCE=sample` | CSV + Pandas |

### 13.1 Test Coverage Areas

| Area | Test Files |
|------|------------|
| Agents | `test_agents.py`, `test_hourly_agent.py`, `test_daily_spend_checks.py`, `test_campaign_daily_agent.py`, `test_email_agent.py` |
| Services | `test_alert_service.py`, `test_spend_analytics.py`, `test_google_ads_fetch.py` |
| Utils | `test_mtd_metrics.py`, `test_hourly_metrics.py`, `test_chat_calculations.py` |
| UI Components | `test_agent_pipeline_ui.py`, `test_pipeline_step_detail.py`, `test_campaign_daily_snapshot.py` |
| Chatbot | `test_chatbot.py` |

**Run tests:** `pytest -q`

---

## 14. Out of Scope

The following are explicitly **not included** in this version (planned for Step 2):

| Item | Notes |
|------|-------|
| Meta (Facebook/Instagram) Ads API | Mentioned in README as future integration |
| Airbyte → BigQuery ingestion | Planned data pipeline |
| Multi-account MCC dashboard | Single account analyzer supported |
| Campaign pause / bid adjustment actions | Read-only monitoring only |
| Role-based access control | No authentication layer |
| Historical alert log / audit trail | Alerts are fire-and-forget |
| Mobile-responsive native app | Streamlit web only |
| Per-campaign daily threshold rules | Placeholder in `campaign_daily_snapshot_agent.py` |

---

## 15. Appendix — Code-to-Feature Mapping

### 15.1 File Index by Layer

#### UI Layer

| File | Feature | Technology |
|------|---------|------------|
| `app.py` | Main dashboard | Streamlit |
| `pages/1_campaign_analysis.py` | Campaign analysis + analyzer | Streamlit, Plotly, Pandas |
| `pages/2_budget_alerts.py` | Budget alerts page | Streamlit |
| `components/metrics_row.py` | KPI row | Streamlit |
| `components/spend_chart.py` | Spend vs budget chart | Plotly |
| `components/budget_gauge.py` | Utilization gauge | Plotly |
| `components/alert_panel.py` | Alert display | Streamlit |
| `components/campaign_table.py` | Campaign table | Streamlit |
| `components/agent_pipeline_ui.py` | 5-step pipeline UI | Streamlit + HTML |
| `components/pipeline_step_detail.py` | Step detail view | Streamlit |
| `components/agent_summary_panel.py` | Agent report display | Streamlit |
| `components/analyzer_form.py` | Analyzer input form | Streamlit |
| `components/analyzer_results.py` | Analyzer results table | Streamlit |
| `components/campaign_daily_snapshot_table.py` | Daily snapshot table | Pandas |
| `components/chat_panel.py` | AI chatbot UI | Streamlit |
| `components/credentials_panel.py` | Google Ads setup help | Streamlit |
| `utils/streamlit_helpers.py` | Sidebar, page init | Streamlit |
| `utils/ui_styles.py` | Custom CSS | HTML/CSS |
| `utils/formatting.py` | Currency, risk labels | Python |

#### Services Layer

| File | Feature | Technology |
|------|---------|------------|
| `services/campaign_data_service.py` | CSV campaign loader | Pandas |
| `services/spend_analytics_service.py` | Dashboard aggregation | Python |
| `services/alert_service.py` | Alert generation | Python |
| `services/google_ads_fetch_service.py` | Google Ads live fetch | google-ads SDK, GAQL |
| `services/campaign_analyzer_service.py` | Analyzer orchestration | Python |
| `services/campaign_daily_snapshot_service.py` | Daily snapshot fetch | google-ads SDK |
| `services/email_service.py` | SMTP delivery | smtplib |

#### Agents Layer

| File | Feature | Technology |
|------|---------|------------|
| `agents/sequential_pipeline.py` | Pipeline orchestration | Python + Streamlit |
| `agents/analyzer_table_agent.py` | Account-wise checks | Rule engine + LangChain |
| `agents/daily_snapshot_agent.py` | Daily-wise checks | Rule engine + LangChain |
| `agents/hourly_agent.py` | Hourly overspend checks | Rule engine + LangChain |
| `agents/campaign_daily_snapshot_agent.py` | Campaign-wise checks | Rule engine + LangChain |
| `agents/supervisor.py` | Report merge + exec summary | LangChain |
| `agents/email_agent.py` | Email alert dispatch | LangChain + SMTP + PyYAML |
| `agents/chatbot_agent.py` | Conversational AI | LangChain ChatOpenAI |
| `agents/chat_context.py` | Chat context builder | Python JSON |
| `agents/chat_calculations.py` | On-demand metric calculations | Python |
| `agents/llm.py` | OpenRouter LLM client | LangChain-OpenAI |
| `agents/graph.py` | LangGraph pipeline (alt) | LangGraph |

#### Models Layer

| File | Feature | Technology |
|------|---------|------------|
| `models/campaign.py` | Campaign, alert, summary models | Pydantic |
| `models/analyzer_input.py` | Analyzer form/result models | Pydantic |
| `models/agent_report.py` | Agent check/report models | Pydantic |
| `models/campaign_daily_snapshot.py` | Daily snapshot row model | Pydantic |

#### Config & Utils

| File | Feature | Technology |
|------|---------|------------|
| `config/settings.py` | App settings | pydantic-settings |
| `config/alert_recipients.yaml` | Email recipients | PyYAML |
| `.env` / `.env.example` | Environment variables | dotenv |
| `clients/google_ads_client.py` | Google Ads client factory | google-ads SDK |
| `utils/mtd_metrics.py` | MTD calculations | Python |
| `utils/daily_spend_checks.py` | Daily spend helpers | Python |
| `utils/masking.py` | Credential masking | Python |

#### Data & Scripts

| File | Feature | Technology |
|------|---------|------------|
| `data/sample_campaigns.csv` | Demo campaign data | CSV |
| `scripts/test_google_ads_connection.py` | API connection test | google-ads SDK |
| `scripts/list_google_ads_accounts.py` | List accounts | google-ads SDK |
| `requirements.txt` | Python dependencies | pip |

### 15.2 Minimum Files for PRD Reference

| Priority | File | Why |
|----------|------|-----|
| 1 | `README.md` | Product overview |
| 2 | `requirements.txt` | Full tech stack |
| 3 | `app.py` | Main dashboard |
| 4 | `pages/1_campaign_analysis.py` | Analyzer + pipeline |
| 5 | `pages/2_budget_alerts.py` | Alerts |
| 6 | `models/campaign.py` | Core domain model |
| 7 | `services/alert_service.py` | Alert logic |
| 8 | `services/spend_analytics_service.py` | Analytics + NR loss |
| 9 | `services/google_ads_fetch_service.py` | Google Ads integration |
| 10 | `agents/sequential_pipeline.py` | Agent orchestration |
| 11 | `agents/analyzer_table_agent.py` | Account checks |
| 12 | `agents/daily_snapshot_agent.py` | Daily checks |
| 13 | `agents/hourly_agent.py` | Hourly checks |
| 14 | `agents/email_agent.py` | Email alerts |
| 15 | `agents/llm.py` | LLM integration |
| 16 | `config/settings.py` | All configuration |
| 17 | `.env.example` | Environment template |
| 18 | `config/alert_recipients.yaml` | Stakeholder mapping |

---

*End of PRD — Sentinel AI v1.0*
