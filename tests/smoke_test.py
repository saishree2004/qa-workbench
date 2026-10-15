"""Smoke test: temp DB, one case/run/bug, a docx export. Run: python tests/smoke_test.py"""
import os
import sqlite3
import sys
import tempfile
import zipfile
import io
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import db  # noqa: E402

tmp = tempfile.mkdtemp()
db.DB_PATH = os.path.join(tmp, "test.db")
db.UPLOADS = os.path.join(tmp, "uploads")
db.init_db()



def _chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))


PNG = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
       + _chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00")) + _chunk(b"IEND", b""))
assert db.image_ext(PNG) == ".png" and db.image_ext(b"\xff\xd8\xff\xe0x") == ".jpg"
assert db.image_ext(b"GIF89a") is None and db.image_ext(b"<svg>") is None
path = db.save_image(PNG)
assert os.path.dirname(path) == db.UPLOADS and os.path.isfile(path)
try:
    db.save_image(b"not an image")
    raise SystemExit("save_image accepted junk")
except ValueError:
    pass

with db.get_conn() as c:
    case = c.execute("INSERT INTO test_cases(suite,title,type,priority,steps,expected,status)"
                     " VALUES (?,?,?,?,?,?,?)", ("S1", "Login <b>fails</b>", "Functional", "High",
                                               "1. Open\n2. Submit", "Error shown", "published")).lastrowid
    run = c.execute("INSERT INTO runs(suite) VALUES (?)", ("S1",)).lastrowid
    c.execute("INSERT INTO run_results(run_id,case_id,result,note) VALUES (?,?,?,?)", (run, case, "Fail", "n"))
    bug = c.execute("INSERT INTO bugs(title,severity,description,steps,expected,actual,suggested_fix,case_id)"
                    " VALUES (?,?,?,?,?,?,?,?)", ("Bug", "High", "d", "1) a\n2) b", "e", "a", "f", case)).lastrowid
    c.execute("INSERT INTO bug_images(bug_id,path,caption,fig_no) VALUES (?,?,?,?)", (bug, path, "cap", 1))

# foreign keys are enforced and a failed write rolls back
try:
    with db.get_conn() as c:
        c.execute("INSERT INTO run_results(run_id,case_id,result) VALUES (999,999,'Pass')")
    raise SystemExit("foreign key not enforced")
except sqlite3.IntegrityError:
    pass
with db.get_conn() as c:
    assert c.execute("SELECT COUNT(*) FROM run_results").fetchone()[0] == 1

import export  # noqa: E402

export.get_conn = db.get_conn
data = export.bugs_to_docx([bug])
names = zipfile.ZipFile(io.BytesIO(data)).namelist()
assert "word/document.xml" in names and any(n.startswith("word/media/") for n in names)

from styles import badge  # noqa: E402

assert "<script>" not in badge("<script>", "high") and 'badge-type"' in badge("a", 'x" onclick="1')
print("smoke test passed")
