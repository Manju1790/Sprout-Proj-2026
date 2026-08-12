# Smart Support Ticket Resolution System

A real-world full-stack support platform that uses AI to classify incoming support tickets, determine priority, analyze sentiment, detect urgency, suggest a resolution, and route the ticket to a support team.

## Technology

- Frontend: React + Vite
- Backend: Python Flask REST API
- Database: SQLite
- AI: OpenRouter through LangChain `ChatOpenAI`
- Testing: Pytest + Vitest
- CI/CD: GitHub Actions
- Deployment: Render
- Docker: Not required

## Main workflow

```text
Customer
   |
   v
React Ticket Form
   |
   v
Flask REST API
   |
   v
AI Ticket Analyzer
   |
   +--> Category
   +--> Priority
   +--> Sentiment
   +--> Team
   +--> Suggested Resolution
   |
   v
SQLite
   |
   v
Support Dashboard
```

## Features

1. Customer creates a support ticket.
2. AI analyzes the ticket.
3. Ticket gets category, priority, sentiment and assigned team.
4. AI generates a suggested resolution.
5. Support staff can update ticket status.
6. Dashboard shows ticket statistics.
7. Search and filtering.
8. CI runs backend tests, frontend tests and production build.
9. CD can trigger Render deployment after CI succeeds on `main`.

## Python setup

Recommended Python: 3.12.

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install:

```bash
python -m pip install -r requirements.txt
```

## OpenRouter setup

Create `.env` in the project root:

```text
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
```

Never commit `.env`.

The AI layer has a deterministic fallback. If no API key is configured, the application still works using keyword/rule-based analysis. This is useful while building the UI and testing locally.

## Run backend

```bash
python app.py
```

Backend:
http://127.0.0.1:5000

## Run frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:
http://localhost:5173

During development, Vite proxies `/api` requests to Flask.

## Run tests

Backend:

```bash
pytest
```

Frontend:

```bash
cd frontend
npm test
```

## Production build without Docker

Build React:

```bash
cd frontend
npm install
npm run build
cd ..
python build_frontend.py
```

Then:

```bash
gunicorn app:app
```

## GitHub

```bash
git add .
git commit -m "Add smart support ticket resolution system"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## CI/CD

`.github/workflows/ci.yml`:

- installs Python dependencies
- runs Pytest
- installs React dependencies
- runs Vitest
- builds React

`.github/workflows/deploy.yml`:

- waits for successful CI on `main`
- calls a Render deploy hook stored in GitHub Secrets as `RENDER_DEPLOY_HOOK_URL`

## Suggested future upgrades

- PostgreSQL
- JWT authentication
- Role-based access
- File/image attachments
- Email notifications
- Knowledge-base RAG
- Human-in-the-loop approval
- SLA breach detection
- Analytics
- Audit logs
- Multi-agent workflow
