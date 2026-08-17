# SkillTrack AI — Learning & Assessment Platform

React + Flask + SQLite application for training institutes.

## Features
- Student registration/login
- Admin/student roles
- Course creation with configurable number of classes
- Configurable quiz unlock interval (5, 4, etc.)
- Class completion tracking
- Automatic quiz unlocking
- MCQ quiz engine and instant scoring
- Leaderboard
- Quiz and topic performance graphs
- Admin analytics
- OpenRouter AI learning coach
- OpenRouter AI MCQ generator
- Pytest backend tests
- GitHub Actions CI

## Demo accounts
Admin: `admin@skilltrack.com` / `admin123`
Student: `student@skilltrack.com` / `student123`

## Run backend (Python 3.12)
```powershell
cd backend
py -3.12 -m venv venv
venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m pytest
python app.py
```
Backend: http://localhost:5000

## Run frontend
Open a second terminal:
```powershell
cd frontend
npm install
npm run dev
```
Frontend: http://localhost:5173

## AI
Put your OpenRouter key in `backend/.env`:
`OPENROUTER_API_KEY=...`
The non-AI course/quiz features work without a key.

## CI
Push to GitHub. Actions runs backend pytest and React build.

## Suggested future additions
Email notifications, certificates, attendance QR, CSV question upload, PDF certificates, PostgreSQL/MySQL, RAG from course notes, and production deployment.
