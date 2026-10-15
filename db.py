import os
import sqlite3
import uuid
from contextlib import contextmanager

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


LIMIT = 2000  # max chars for any free-text input
MAX_UPLOAD = 5 * 1024 * 1024
UPLOADS = "uploads"
IMAGE_MAGIC = {b"\x89PNG\r\n\x1a\n": ".png", b"\xff\xd8\xff": ".jpg"}


@contextmanager
def get_conn():
    """Commit on success, roll back on error, always close."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:
            yield conn
    finally:
        conn.close()


@contextmanager
def guarded(msg="Could not save your changes. Please try again."):
    """Turn DB/file errors into a friendly st.error and stop the script run."""
    import streamlit as st

    try:
        yield
    except (sqlite3.Error, OSError):
        st.error(msg)
        st.stop()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def upload_error(f, exts):
    """Return a message if the upload is oversized or not one of `exts`, else None."""
    if os.path.splitext(f.name)[1].lower() not in exts:
        return f"{os.path.basename(f.name)}: only {', '.join(exts)} files are allowed."
    if f.size > MAX_UPLOAD:
        return f"{os.path.basename(f.name)}: file is larger than 5 MB."
    return None


def image_ext(data):
    """Extension from the file's magic bytes (never from the client filename), or None."""
    return next((e for m, e in IMAGE_MAGIC.items() if data.startswith(m)), None)


def save_image(data):
    """Write validated image bytes to uploads/<uuid>.<ext>; return the path."""
    ext = image_ext(data)
    if ext is None:
        raise ValueError("not a PNG or JPEG image")
    os.makedirs(UPLOADS, exist_ok=True)
    path = os.path.join(UPLOADS, uuid.uuid4().hex + ext)
    with open(path, "xb") as fh:
        fh.write(data)
    return path
