import io
import os
import shutil
import tempfile
import zipfile
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


MAX_BACKUP = 200 * 1024 * 1024  # uncompressed cap, guards against zip bombs
TABLES = {"requirements", "test_cases", "runs", "run_results", "bugs", "bug_images", "ai_log"}


def make_backup():
    """Zip of a consistent DB snapshot plus uploads/, as bytes."""
    buf = io.BytesIO()
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        snap = os.path.join(tmp, DB_PATH)
        src, dst = sqlite3.connect(DB_PATH), sqlite3.connect(snap)
        try:
            src.backup(dst)
        finally:
            src.close()
            dst.close()
        z.write(snap, DB_PATH)
        for name in os.listdir(UPLOADS) if os.path.isdir(UPLOADS) else []:
            z.write(os.path.join(UPLOADS, name), f"{UPLOADS}/{name}")
    return buf.getvalue()


def restore_backup(data):
    """Validate a backup zip and replace the DB and uploads/. Raises ValueError if invalid."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        infos = z.infolist()
    except zipfile.BadZipFile:
        raise ValueError("Not a valid zip file.")
    names = {i.filename for i in infos}
    if DB_PATH not in names or sum(i.file_size for i in infos) > MAX_BACKUP:
        raise ValueError("Not a QA Workbench backup, or it is too large.")
    for i in infos:
        n = i.filename
        if n != DB_PATH and not (n.startswith(UPLOADS + "/") and n.count("/") == 1 and n[len(UPLOADS) + 1:]
                                 and n[len(UPLOADS) + 1] != "." and "\\" not in n):
            raise ValueError(f"Unexpected file in backup: {n!r}")
    with tempfile.TemporaryDirectory() as tmp:
        for i in infos:
            if i.filename == DB_PATH:
                path = os.path.join(tmp, DB_PATH)
            else:
                os.makedirs(os.path.join(tmp, UPLOADS), exist_ok=True)
                path = os.path.join(tmp, UPLOADS, os.path.basename(i.filename))
            with z.open(i) as s, open(path, "wb") as o:
                shutil.copyfileobj(s, o)
        new_db = os.path.join(tmp, DB_PATH)
        try:
            c = sqlite3.connect(new_db)
            try:
                ok = c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                have = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            finally:
                c.close()
        except sqlite3.Error:
            raise ValueError("Database in backup is corrupt.")
        if not ok or not TABLES <= have:
            raise ValueError("Database in backup is corrupt or has the wrong tables.")
        src, dst = sqlite3.connect(new_db), sqlite3.connect(DB_PATH)
        try:
            src.backup(dst)  # in-place, keeps the live file and its connections valid
        finally:
            src.close()
            dst.close()
        shutil.rmtree(UPLOADS, ignore_errors=True)
        if os.path.isdir(os.path.join(tmp, UPLOADS)):
            shutil.copytree(os.path.join(tmp, UPLOADS), UPLOADS)
