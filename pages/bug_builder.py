import difflib
import os

import streamlit as st

from ai_client import call_json, supports_vision
from db import LIMIT, get_conn, guarded, image_ext, save_image, upload_error
from prompts import BUG_KEYS, SEVERITIES, build_bug
from styles import inject_css, require_login

inject_css()
require_login()
ss = st.session_state
LABELS = {"title": "Title", "severity": "Severity", "description": "Description", "steps": "Steps to Reproduce",
          "expected": "Expected Result", "actual": "Actual Result", "suggested_fix": "Suggested Fix"}

st.title("Bug Builder")
if ss.pop("bb_saved", False):
    st.success("Bug saved.")

pre = ss.pop("bug_prefill", None)
if pre:  # coming from Suites: keep case_id, seed notes and fields
    ss["bb_case_id"] = pre.get("case_id")
    ss["bb_notes"] = "\n".join(f"{k}: {pre[k]}" for k in ("title", "steps", "expected", "note") if pre.get(k))[:LIMIT]
    for k in BUG_KEYS:
        ss[f"bf_{k}"] = str(pre.get(k) or ("Medium" if k == "severity" else ""))[:LIMIT]
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
    vals = [str(ss[f"bf_{k}"])[:LIMIT] for k in BUG_KEYS]  # server-side cap, widgets also set max_chars
    written = []
    try:
        with guarded(), get_conn() as c:
            cur = c.execute(
            "INSERT INTO bugs(title,severity,description,steps,expected,actual,suggested_fix,case_id) VALUES (?,?,?,?,?,?,?,?)",
                (*vals, ss.get("bb_case_id")))
            for n, (f, cap) in enumerate(zip(files, caps), 1):
                written.append(save_image(f.getvalue()))
                c.execute("INSERT INTO bug_images(bug_id,path,caption,fig_no) VALUES (?,?,?,?)",
                          (cur.lastrowid, written[-1], cap[:200], n))
    except BaseException:  # includes st.stop from guarded(): DB rolled back, so drop the orphan files
        for p in written:
            if os.path.isfile(p):
                os.remove(p)
        raise
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
    notes = st.text_area("Notes", key="bb_notes", height=220, max_chars=LIMIT)
    files = st.file_uploader("Screenshots (optional, PNG/JPG, max 5 MB each)", type=["png", "jpg", "jpeg"],
                             accept_multiple_files=True, key=f"bb_up_{ss.get('bb_up_n', 0)}")
    errs = [e for f in files if (e := upload_error(f, (".png", ".jpg", ".jpeg")) or (
        None if image_ext(f.getvalue()) else f"{os.path.basename(f.name)}: not a valid PNG or JPEG image."))]
    for e in errs:
        st.error(e)
    if files and not supports_vision():
        st.caption("Current AI provider has no vision; screenshots are attached but not analysed.")
    if st.button("Generate", type="primary", disabled=not notes.strip() or bool(errs)):
        imgs = [(f.getvalue(), "image/png" if image_ext(f.getvalue()) == ".png" else "image/jpeg") for f in files]
        with st.spinner("Generating..."):
            data = call_json("bug_builder", build_bug(notes, bool(imgs) and supports_vision()), imgs)
        if isinstance(data, dict):
            for k in BUG_KEYS:
                v = data.get(k)
                if k == "severity":
                    v = v if v in SEVERITIES else "Medium"
                ss[f"bf_{k}"] = (v if isinstance(v, str) else ("" if v is None else str(v)))[:LIMIT]
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
            st.text_input(LABELS[k], key="bf_title", max_chars=200)
        else:
            st.text_area(LABELS[k], key=f"bf_{k}", height=100, max_chars=LIMIT)
    for n, f in enumerate(files, 1):
        st.image(f.getvalue(), width=300)
        caps.append(st.text_input(f"Fig. {n} caption", key=f"cap_{n}_{f.name}", max_chars=200))

    ready = bool(ss["bf_title"].strip())
    if st.button("Save bug", type="primary", disabled=not ready or bool(errs)):
        dupes = find_dupes(ss["bf_title"], ss["bf_actual"])
        if dupes:
            ss["bb_dupes"] = dupes
        else:
            save(files, caps)
    if ss.get("bb_dupes"):
        st.warning("Possible duplicates:\n\n" + "\n".join(f"- #{i} {t} ({s:.0%} similar)" for s, i, t in ss["bb_dupes"]))
        if st.button("Save anyway"):
            save(files, caps)
