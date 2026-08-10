import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

if not API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY is missing. Create a .env file from .env.example."
    )

llm = ChatOpenAI(
    model=MODEL,
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0.2,
)


def ask(prompt):
    response = llm.invoke(prompt)
    return response.content


def profile_agent(profile):
    return ask(f"""
You are a Career Profile Analysis Agent.

Analyze this candidate profile:
{json.dumps(profile, indent=2)}

Return:
1. Professional summary
2. Technical skills
3. Strengths
4. Weaknesses
5. Suitable roles
6. Resume improvement suggestions

Focus only on job-relevant information.
""")


def job_matching_agent(profile, jobs_text):
    return ask(f"""
You are a Job Matching Agent.

Candidate:
{json.dumps(profile, indent=2)}

Available jobs:
{jobs_text}

Compare the candidate against the jobs.

For the TOP 5 matches, provide:
- Job ID
- Company
- Role
- Location
- Match score from 0-100
- Matching skills
- Missing skills
- Short reason

Do not use age, gender, religion, race, disability, or other protected
characteristics. Use only job-relevant qualifications.
""")


def skill_gap_agent(profile, matching):
    return ask(f"""
You are a Skill Gap Agent.

Candidate:
{json.dumps(profile, indent=2)}

Job matching:
{matching}

Identify the most important missing skills.

For each:
- Skill
- Priority: High/Medium/Low
- Why it matters
- What to learn
- One practical project

Finish with the 3 most important skills to learn first.
""")


def roadmap_agent(profile, skill_gap):
    return ask(f"""
You are a Career Roadmap Agent.

Candidate:
{json.dumps(profile, indent=2)}

Skill gaps:
{skill_gap}

Create an 8-week practical roadmap.
For every week include:
- Topic
- Learning tasks
- Hands-on task
- Expected outcome

Prefer projects and measurable outcomes over passive reading.
""")


def interview_agent(profile, matching):
    return ask(f"""
You are an AI Interview Preparation Agent.

Candidate:
{json.dumps(profile, indent=2)}

Recommended jobs:
{matching}

Create interview preparation for the target role:
- 5 technical questions
- 3 Python questions if relevant
- 3 SQL questions if relevant
- 2 project questions
- 2 behavioral questions
- What a strong answer should contain for each

Match difficulty to the candidate's experience.
""")


def final_career_agent(profile, matching, skill_gap, roadmap, interview):
    return ask(f"""
You are the Final Career Advisor Agent.

Candidate:
{json.dumps(profile, indent=2)}

JOB MATCHING:
{matching}

SKILL GAP:
{skill_gap}

ROADMAP:
{roadmap}

INTERVIEW:
{interview}

Create a concise career report with:
1. Candidate summary
2. Best roles
3. Top job matches
4. Current strengths
5. Skill gaps
6. 8-week roadmap
7. Projects to build
8. Interview preparation
9. Application readiness: Ready / Almost Ready / Needs Preparation
10. Next 3 actions

Treat AI scores as recommendations, not hiring decisions.
""")


def analyze_career(profile, jobs_df):
    jobs_text = jobs_df.to_string(index=False)

    profile_analysis = profile_agent(profile)
    job_matching = job_matching_agent(profile, jobs_text)
    skill_gap = skill_gap_agent(profile, job_matching)
    roadmap = roadmap_agent(profile, skill_gap)
    interview = interview_agent(profile, job_matching)
    final_report = final_career_agent(
        profile,
        job_matching,
        skill_gap,
        roadmap,
        interview,
    )

    return {
        "profile_analysis": profile_analysis,
        "job_matching": job_matching,
        "skill_gap": skill_gap,
        "roadmap": roadmap,
        "interview": interview,
        "final_report": final_report,
    }
