import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "career.db")
JOBS_CSV = os.path.join(BASE_DIR, "jobs.csv")


def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            education TEXT,
            experience TEXT,
            skills TEXT,
            projects TEXT,
            target_role TEXT,
            resume_text TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            profile_analysis TEXT,
            job_matching TEXT,
            skill_gap TEXT,
            roadmap TEXT,
            interview TEXT,
            final_report TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def create_user(name, email, password):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (name, email, password),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user(email, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_profile(user_id, data):
    conn = get_connection()
    conn.execute("""
        INSERT INTO profiles(user_id,education,experience,skills,projects,target_role,resume_text)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET
            education=excluded.education,
            experience=excluded.experience,
            skills=excluded.skills,
            projects=excluded.projects,
            target_role=excluded.target_role,
            resume_text=excluded.resume_text
    """, (
        user_id,
        data.get("education", ""),
        data.get("experience", ""),
        data.get("skills", ""),
        data.get("projects", ""),
        data.get("target_role", ""),
        data.get("resume_text", ""),
    ))
    conn.commit()
    conn.close()


def get_profile(user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM profiles WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_analysis(user_id, result):
    conn = get_connection()
    conn.execute("""
        INSERT INTO analyses(
            user_id, profile_analysis, job_matching, skill_gap,
            roadmap, interview, final_report
        ) VALUES(?,?,?,?,?,?,?)
    """, (
        user_id,
        result.get("profile_analysis", ""),
        result.get("job_matching", ""),
        result.get("skill_gap", ""),
        result.get("roadmap", ""),
        result.get("interview", ""),
        result.get("final_report", ""),
    ))
    conn.commit()
    conn.close()


def get_latest_analysis(user_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT * FROM analyses
        WHERE user_id=?
        ORDER BY id DESC LIMIT 1
    """, (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def load_jobs():
    return pd.read_csv(JOBS_CSV)


def get_job(job_id):
    df = load_jobs()
    row = df[df["job_id"].astype(str) == str(job_id)]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


init_db()
