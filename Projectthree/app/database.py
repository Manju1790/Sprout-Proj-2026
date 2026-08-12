import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Courses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id TEXT PRIMARY KEY,
        course_name TEXT NOT NULL,
        course_code TEXT,
        instructor TEXT,
        syllabus_filename TEXT NOT NULL,
        upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        chunk_count INTEGER DEFAULT 0,
        total_pages INTEGER DEFAULT 0
    );
    """)

    # Chat logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        is_fallback BOOLEAN DEFAULT 0,
        sources TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Unresolved student questions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unresolved_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id TEXT NOT NULL,
        question TEXT NOT NULL UNIQUE,
        frequency_count INTEGER DEFAULT 1,
        first_asked DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_asked DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',
        notes TEXT DEFAULT ''
    );
    """)

    # System settings table (for custom API key overrides, etc.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

# Helper Functions for DB Management

def save_course_metadata(course_id: str, course_name: str, course_code: str, instructor: str, filename: str, chunk_count: int, total_pages: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO courses (course_id, course_name, course_code, instructor, syllabus_filename, upload_timestamp, chunk_count, total_pages)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (course_id, course_name, course_code, instructor, filename, datetime.now().isoformat(), chunk_count, total_pages))
    conn.commit()
    conn.close()

def get_active_course(course_id: str = "default") -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE course_id = ? ORDER BY upload_timestamp DESC LIMIT 1", (course_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_courses() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses ORDER BY upload_timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_chat_interaction(course_id: str, question: str, answer: str, is_fallback: bool, sources: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_logs (course_id, question, answer, is_fallback, sources, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (course_id, question, answer, 1 if is_fallback else 0, sources, datetime.now().isoformat()))
    
    if is_fallback:
        log_unresolved_question(course_id, question)
        
    conn.commit()
    conn.close()

def log_unresolved_question(course_id: str, question: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_q = question.strip()
    
    cursor.execute("SELECT id, frequency_count FROM unresolved_questions WHERE LOWER(question) = LOWER(?) AND course_id = ?", (clean_q, course_id))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("""
            UPDATE unresolved_questions
            SET frequency_count = frequency_count + 1, last_asked = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), row['id']))
    else:
        cursor.execute("""
            INSERT INTO unresolved_questions (course_id, question, frequency_count, first_asked, last_asked, status)
            VALUES (?, ?, 1, ?, ?, 'pending')
        """, (course_id, clean_q, datetime.now().isoformat(), datetime.now().isoformat()))
        
    conn.commit()

def get_unresolved_questions(course_id: str = "default") -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM unresolved_questions WHERE course_id = ? ORDER BY frequency_count DESC, last_asked DESC", (course_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_unresolved_question_status(question_id: int, status: str, notes: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE unresolved_questions SET status = ?, notes = ? WHERE id = ?", (status, notes, question_id))
    conn.commit()
    conn.close()

def delete_unresolved_question(question_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM unresolved_questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()

def get_analytics_summary(course_id: str = "default") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM chat_logs WHERE course_id = ?", (course_id,))
    total_queries = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as fallbacks FROM chat_logs WHERE course_id = ? AND is_fallback = 1", (course_id,))
    fallback_queries = cursor.fetchone()['fallbacks']
    
    cursor.execute("SELECT COUNT(*) as pending FROM unresolved_questions WHERE course_id = ? AND status = 'pending'", (course_id,))
    pending_unresolved = cursor.fetchone()['pending']

    cursor.execute("SELECT * FROM chat_logs WHERE course_id = ? ORDER BY id DESC LIMIT 10", (course_id,))
    recent_logs = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    resolved_queries = total_queries - fallback_queries
    resolution_rate = round((resolved_queries / total_queries * 100), 1) if total_queries > 0 else 100.0
    
    return {
        "total_queries": total_queries,
        "resolved_queries": resolved_queries,
        "fallback_queries": fallback_queries,
        "pending_unresolved": pending_unresolved,
        "resolution_rate": resolution_rate,
        "recent_logs": recent_logs
    }

def set_setting(key: str, value: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_setting(key: str) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None
