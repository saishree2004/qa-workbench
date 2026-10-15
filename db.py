import sqlite3

DB_PATH = "qa.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS requirements(
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, text TEXT, analysis_json TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS test_cases(
  id INTEGER PRIMARY KEY AUTOINCREMENT, suite TEXT, title TEXT, type TEXT, priority TEXT,
  preconditions TEXT, steps TEXT, expected TEXT, tags TEXT,
  status TEXT DEFAULT 'draft' CHECK(status IN ('draft','published','rejected')),
  edited INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, suite TEXT, started_at TEXT DEFAULT CURRENT_TIMESTAMP,
  finished_at TEXT);
CREATE TABLE IF NOT EXISTS run_results(
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER REFERENCES runs(id),
  case_id INTEGER REFERENCES test_cases(id),
  result TEXT CHECK(result IN ('Pass','Fail','Blocked')), note TEXT,
  at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS bugs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, severity TEXT, description TEXT, steps TEXT,
  expected TEXT, actual TEXT, suggested_fix TEXT,
  status TEXT DEFAULT 'Open' CHECK(status IN ('Open','Fixed','Retest','Closed')),
  case_id INTEGER REFERENCES test_cases(id),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS bug_images(
  id INTEGER PRIMARY KEY AUTOINCREMENT, bug_id INTEGER REFERENCES bugs(id) ON DELETE CASCADE,
  path TEXT, caption TEXT, fig_no INTEGER);
CREATE TABLE IF NOT EXISTS ai_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT, feature TEXT, ok INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
