import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "support.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                team TEXT NOT NULL,
                suggested_resolution TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def row_to_dict(row):
    return dict(row) if row else None


def create_ticket(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO tickets (
                name, email, subject, description,
                category, priority, sentiment, team,
                suggested_resolution, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open')
        """, (
            data["name"],
            data["email"],
            data["subject"],
            data["description"],
            data["category"],
            data["priority"],
            data["sentiment"],
            data["team"],
            data["suggested_resolution"],
        ))
        ticket_id = cursor.lastrowid

    return get_ticket(ticket_id)


def get_ticket(ticket_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,)
        ).fetchone()
    return row_to_dict(row)


def get_tickets(status=None, category=None, priority=None, search=None):
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)

    if search:
        query += """
            AND (
                subject LIKE ?
                OR description LIKE ?
                OR name LIKE ?
                OR email LIKE ?
            )
        """
        pattern = f"%{search}%"
        params.extend([pattern] * 4)

    query += " ORDER BY id DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def update_status(ticket_id, status):
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE tickets
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, ticket_id))

    return cursor.rowcount > 0


def get_stats():
    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM tickets"
        ).fetchone()[0]

        open_count = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE status = 'Open'"
        ).fetchone()[0]

        progress = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE status = 'In Progress'"
        ).fetchone()[0]

        resolved = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE status = 'Resolved'"
        ).fetchone()[0]

        urgent = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE priority = 'Urgent'"
        ).fetchone()[0]

        high = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE priority = 'High'"
        ).fetchone()[0]

    return {
        "total": total,
        "open": open_count,
        "in_progress": progress,
        "resolved": resolved,
        "urgent": urgent,
        "high": high,
    }
