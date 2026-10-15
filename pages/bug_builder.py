import difflib
import os
import uuid

import streamlit as st

from ai_client import call_json, supports_vision
from db import get_conn
from prompts import BUG_KEYS, SEVERITIES, build_bug
from styles import inject_css

inject_css()
ss = st.session_state
UPLOADS = "uploads"
LABELS = {"title": "Title", "severity": "Severity", "description": "Description", "steps": "Steps to Reproduce",
          "expected": "Expected Result", "actual": "Actual Result", "suggested_fix": "Suggested Fix"}

st.title("Bug Builder")
if ss.pop("bb_saved", False):
    st.success("Bug saved.")

pre = ss.pop("bug_prefill", None)
if pre:  # coming from Suites: keep case_id, seed notes and fields
    ss["bb_case_id"] = pre.get("case_id")
    ss["bb_notes"] = "\n".join(f"{k}: {pre[k]}" for k in ("title", "steps", "expected", "note") if pre.get(k))
    for k in BUG_KEYS:
        ss[f"bf_{k}"] = pre.get(k) or ("Medium" if k == "severity" else "")
for k in BUG_KEYS:
    ss.setdefault(f"bf_{k}", "Medium" if k == "severity" else "")


def find_dupes(title, actual):
    key = f"{title} {actual}".lower()
    with get_conn() as c:
        rows = c.execute("SELECT id, title, actual FROM bugs").fetchall()
    out = []
    for r in rows:
        score = difflib.SequenceMatcher(None, key, f"{r['title'] or ''} {r['actual'] or ''}".lower()).ratio()
        if score > 0.6:
            out.append((score, r["id"], r["title"]))
    return sorted(out, reverse=True)


def save(files, caps):
    os.makedirs(UPLOADS, exist_ok=True)
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO bugs(title,severity,description,steps,expected,actual,suggested_fix,case_id) VALUES (?,?,?,?,?,?,?,?)",
            (*[ss[f"bf_{k}"] for k in BUG_KEYS], ss.get("bb_case_id")))
        for n, (f, cap) in enumerate(zip(files, caps), 1):
            path = os.path.join(UPLOADS, uuid.uuid4().hex + os.path.splitext(f.name)[1].lower())
            with open(path, "wb") as fh:
                fh.write(f.getvalue())
            c.execute("INSERT INTO bug_images(bug_id,path,caption,fig_no) VALUES (?,?,?,?)", (cur.lastrowid, path, cap, n))
    for k in list(ss.keys()):
        if k.startswith(("bf_", "cap_")) or k in ("bb_notes", "bb_case_id", "bb_dupes"):
            del ss[k]
    ss["bb_up_n"] = ss.get("bb_up_n", 0) + 1  # new uploader key clears the files
    ss["bb_saved"] = True
    st.rerun()


left, right = st.columns(2)
with left, st.container(border=True):
    st.subheader("Rough notes")
    if ss.get("bb_case_id"):
        st.caption(f"Linked to test case #{ss['bb_case_id']}")
    notes = st.text_area("Notes", key="bb_notes", height=220)
    files = st.file_uploader("Screenshots (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=True,
                             key=f"bb_up_{ss.get('bb_up_n', 0)}")
    if files and not supports_vision():
        st.caption("Current AI provider has no vision; screenshots are attached but not analysed.")
    if st.button("Generate", type="primary", disabled=not notes.strip()):
        imgs = [(f.getvalue(), f.type) for f in files]
        with st.spinner("Generating..."):
            data = call_json("bug_builder", build_bug(notes, bool(imgs) and supports_vision()), imgs)
        if isinstance(data, dict):
            for k in BUG_KEYS:
                v = data.get(k)
                if k == "severity":
                    v = v if v in SEVERITIES else "Medium"
                ss[f"bf_{k}"] = v if isinstance(v, str) else ("" if v is None else str(v))
            ss.pop("bb_dupes", None)
            st.rerun()

caps = []
with right, st.container(border=True):
    st.subheader("Bug report")
    for k in BUG_KEYS:
        if k == "severity":
            if ss["bf_severity"] not in SEVERITIES:
                ss["bf_severity"] = "Medium"
            st.selectbox(LABELS[k], SEVERITIES, key="bf_severity")
        elif k == "title":
            st.text_input(LABELS[k], key="bf_title")
        else:
            st.text_area(LABELS[k], key=f"bf_{k}", height=100)
    for n, f in enumerate(files, 1):
        st.image(f.getvalue(), width=300)
        caps.append(st.text_input(f"Fig. {n} caption", key=f"cap_{n}_{f.name}"))

    ready = bool(ss["bf_title"].strip())
    if st.button("Save bug", type="primary", disabled=not ready):
        dupes = find_dupes(ss["bf_title"], ss["bf_actual"])
        if dupes:
            ss["bb_dupes"] = dupes
        else:
            save(files, caps)
    if ss.get("bb_dupes"):
        st.warning("Possible duplicates:\n\n" + "\n".join(f"- #{i} {t} ({s:.0%} similar)" for s, i, t in ss["bb_dupes"]))
        if st.button("Save anyway"):
            save(files, caps)
