# TeamSync AI

## Problem
Teams struggle with scattered communication, invisible blockers, and time-wasting status meetings. This platform improves team coordination by providing AI-powered standups, simplified task workflows, and real-time visibility into workload and progress.

## Solution
TeamSync AI is an AI-powered team collaboration platform that uses Google Gemini to automate daily standups, analyze blockers with actionable suggestions, and enable natural-language task creation. Tasks are persisted in Google Cloud Firestore for team-wide access, and an interactive dashboard provides real-time visibility into workload distribution and task progress.

## Architecture
- **UI**: Streamlit (accessible, responsive, tab-based navigation)
- **AI Engine**: Google Gemini 2.0 Flash (standup generation, blocker analysis, NL task parsing)
- **Deployment**: Google Cloud Run (asia-south1)
- **Persistence**: Google Cloud Firestore (NoSQL task storage, team-wide access)

## Setup

### Prerequisites
- Python 3.12+
- Google Cloud SDK (`gcloud`)
- Gemini API key

### Local Development
```bash
pip install -r requirements-dev.txt
cp .env.example .env  # Fill in your API keys
streamlit run app.py
```

### Run Tests
```bash
pytest test_app.py -v
```

### Deploy to Cloud Run
```bash
gcloud run deploy teamsync-ai \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key
```

## Live Demo
[Cloud Run URL here after deployment]

## Features
1. **Smart Task Board** — CRUD task management with AI-powered natural language task creation
2. **AI Standup Generator** — Gemini analyzes all tasks to produce per-member updates and blocker alerts
3. **Team Dashboard** — Interactive Plotly charts showing workload, priorities, and completion metrics

## Evaluation Criteria Coverage
| Criterion | How It's Addressed |
|-----------|-------------------|
| Code Quality | Type hints on all functions, docstrings, single-responsibility functions (<30 lines), config separation, named constants |
| Security | Environment variables via python-dotenv, input validation, prompt injection sanitization, no secrets in code |
| Efficiency | `@st.cache_data` on Gemini calls, lazy `_get_model()` init, `@st.cache_resource` on Firestore client, minimal API calls |
| Testing | 20 pytest tests with mocked Gemini API, edge cases (empty input, API failure, invalid data) |
| Accessibility | Heading hierarchy (title→header→subheader), `st.caption()` on all charts, `st.spinner` on AI calls, clear error messages |
| Problem Alignment | Standups solve coordination, NL task creation simplifies workflows, dashboard improves visibility |
| Google Services | Gemini API (AI engine), Cloud Run (deployment), Firestore (persistence) — 3 services, all naturally integrated |
