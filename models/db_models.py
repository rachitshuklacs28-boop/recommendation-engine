"""
models/db_models.py
---------------------
Small helper functions for reading/writing rows in the SQLite database.
Kept deliberately simple (plain sqlite3 + dict rows) so the project stays
beginner-friendly — no ORM required to understand what's happening.
"""

import sqlite3


def get_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def create_user(db_path, name, education, skills, interests, experience_level, career_goal):
    """
    Insert a new user profile. `skills` and `interests` are expected as
    semicolon-separated strings (e.g. "Python;SQL;Flask").
    Returns the new user's id.
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO users (name, education, skills, interests, experience_level, career_goal)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, education, skills, interests, experience_level, career_goal),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user(db_path, user_id):
    """Return a single user's profile as a dict, or None if not found."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_users(db_path):
    """Return all user profiles (used for an optional 'switch user' view)."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT id, name, career_goal, created_at FROM users ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_user(db_path, user_id, **fields):
    """Update one or more fields of an existing user profile."""
    allowed = {"name", "education", "skills", "interests", "experience_level", "career_goal"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False

    conn = get_connection(db_path)
    try:
        set_clause = ", ".join(f"{col} = ?" for col in updates)
        values = list(updates.values()) + [user_id]
        conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return True
    finally:
        conn.close()
