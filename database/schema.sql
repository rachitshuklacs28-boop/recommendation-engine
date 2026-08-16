-- =========================================================
-- Recommendation Engine Database Schema
-- =========================================================

-- Stores each user's profile. This is the input to the engine.
CREATE TABLE IF NOT EXISTS users (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL,
    education         TEXT NOT NULL,
    skills            TEXT NOT NULL,      -- semicolon-separated, e.g. "Python;SQL;Flask"
    interests         TEXT NOT NULL,      -- semicolon-separated
    experience_level  TEXT NOT NULL CHECK (experience_level IN ('Beginner', 'Intermediate', 'Advanced')),
    career_goal       TEXT NOT NULL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Catalog of internship opportunities (seeded from data/internships.csv)
CREATE TABLE IF NOT EXISTS internships (
    id                INTEGER PRIMARY KEY,
    title             TEXT NOT NULL,
    company           TEXT NOT NULL,
    description       TEXT NOT NULL,
    required_skills   TEXT NOT NULL,      -- semicolon-separated
    domain            TEXT NOT NULL,
    level             TEXT NOT NULL,
    duration          TEXT,
    location          TEXT,
    mode              TEXT
);

-- Catalog of project ideas (seeded from data/projects.csv)
CREATE TABLE IF NOT EXISTS projects (
    id                INTEGER PRIMARY KEY,
    title             TEXT NOT NULL,
    description       TEXT NOT NULL,
    skills_required   TEXT NOT NULL,      -- semicolon-separated
    domain            TEXT NOT NULL,
    difficulty_level  TEXT NOT NULL,
    category          TEXT
);

-- Catalog of learning resources (seeded from data/learning_resources.csv)
CREATE TABLE IF NOT EXISTS learning_resources (
    id                INTEGER PRIMARY KEY,
    title             TEXT NOT NULL,
    provider          TEXT NOT NULL,
    description       TEXT NOT NULL,
    skills_covered    TEXT NOT NULL,      -- semicolon-separated
    category          TEXT NOT NULL,
    level             TEXT NOT NULL,
    url               TEXT,
    resource_type     TEXT
);

-- Audit trail: every recommendation ever generated, with its computed score.
-- This proves scores are computed live per request rather than hard-coded,
-- and lets the dashboard show recommendation history if needed.
CREATE TABLE IF NOT EXISTS recommendation_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    item_type     TEXT NOT NULL CHECK (item_type IN ('internship', 'project', 'learning_resource')),
    item_id       INTEGER NOT NULL,
    match_score   REAL NOT NULL,
    generated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
