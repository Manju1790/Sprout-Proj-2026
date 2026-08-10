# AI-Powered Job Matching & Career Preparation Agent

A UI-based Agentic AI project built with:

- Python
- Flask
- HTML/CSS/Bootstrap
- SQLite
- LangGraph
- LangChain
- OpenRouter
- PDF resume extraction

## Features

1. User registration/login
2. Student profile
3. PDF resume upload
4. Job search
5. Multi-agent career analysis
6. Job matching
7. Skill gap analysis
8. 8-week career roadmap
9. Interview preparation
10. Career report

## Agent workflow

Profile Agent
    ↓
Job Matching Agent
    ↓
Skill Gap Agent
    ↓
Career Roadmap Agent
    ↓
Interview Agent
    ↓
Final Career Advisor

## Setup

### 1. Create a virtual environment

Windows:

    python -m venv venv
    venv\Scripts\activate

macOS/Linux:

    python3 -m venv venv
    source venv/bin/activate

### 2. Install dependencies

    pip install -r requirements.txt

### 3. Configure OpenRouter

Copy `.env.example` to `.env`.

    OPENROUTER_API_KEY=your_key
    OPENROUTER_MODEL=openai/gpt-4o-mini

### 4. Run

    python app.py

Open:

    http://127.0.0.1:5000

## Important

This demo stores passwords as plain text for simplicity. For production, use Werkzeug password hashing, proper authentication/session management, CSRF protection, HTTPS, PostgreSQL, and secure secret management.

The included jobs.csv is demo data. For a production system, replace it with an authorized job source/API or your own employer database.

AI match scores are recommendations and should not be used as automatic hiring decisions.
