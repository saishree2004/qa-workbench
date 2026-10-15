from html import escape

import streamlit as st

from ai_client import call_json
from db import LIMIT, get_conn, guarded, upload_error
from prompts import PRIORITIES, TEST_TYPES, generate_cases
from styles import badge, inject_css

inject_css()
ss = st.session_state
ss.setdefault("gen_cases", [])
ss.setdefault("gen_rejected", [])
ss.setdefault("gen_uid", 0)
if "gen_msg" in ss:  # set by save() before st.rerun()
    st.toast(ss.pop("gen_msg"))

# Prefill once from the Analyzer page; widget key is dropped by Streamlit when leaving the page.
handoff = ss.get("analyzer_handoff")
if handoff and "gen_text" not in ss:
    ss["gen_text"] = (handoff if isinstance(handoff, str) else handoff.get("text", ""))[:2000]


def as_text(v):
    return "\n".join(map(str, v)) if isinstance(v, list) else str(v or "")


def save(status):
    """Insert selected cases with `status` plus all rejected cases, then drop them from the review list."""
    picked = [c for c in ss.gen_cases if ss.get(f"sel_{c['uid']}")]
    rows = [(c, status) for c in picked] + [(c, "rejected") for c in ss.gen_rejected]
    with guarded(), get_conn() as conn:
        conn.executemany(
            "INSERT INTO test_cases(suite,title,type,priority,preconditions,steps,expected,tags,status,edited)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            [(suite.strip()[:100], *(str(c[k])[:LIMIT] for k in ("title", "type", "priority", "preconditions", "steps", "expected", "tags")),
              s, c["edited"]) for c, s in rows])
    ss.gen_cases = [c for c in ss.gen_cases if c not in picked]
    ss.gen_rejected = []
    ss.gen_msg = (f"Saved {len(picked)} as {status}" + (f", {len(rows) - len(picked)} rejected" if len(rows) > len(picked) else ""))


st.title("Test Case Generator")
left, right = st.columns(2, gap="large")

with left, st.container(border=True):
    st.subheader("Requirement")
    t_manual, t_file = st.tabs(["Manual Description", "Requirements File"])
    with t_manual:
        manual = st.text_area("Describe the feature", key="gen_text", max_chars=2000, height=220)
    with t_file:
        up = st.file_uploader("Upload .txt or .md (max 5 MB)", type=["txt", "md"])
        bad = upload_error(up, (".txt", ".md")) if up else None
        if bad:
            st.error(bad)
        file_text = up.getvalue().decode("utf-8", errors="replace") if up and not bad else ""
        if file_text:
            st.caption(f"{len(file_text)} chars loaded from {up.name}")
    c1, c2, c3 = st.columns(3)
    test_type = c1.selectbox("Test type", TEST_TYPES)
    priority = c2.selectbox("Priority", PRIORITIES, index=1)
    count = c3.number_input("Count", 1, 10, 5)
    count = max(1, min(10, int(count)))
    requirement = (file_text or manual).strip()
    too_long = len(requirement) > LIMIT
    if too_long:
        st.error(f"Requirement is {len(requirement)} characters; the limit is {LIMIT}.")
    if st.button("✨ Generate", use_container_width=True, disabled=not requirement or too_long):
        with st.spinner("Generating test cases..."):
            data = call_json("generator", generate_cases(requirement, test_type, priority, count))
        cases = data.get("cases") if isinstance(data, dict) else None
        if data is not None and not isinstance(cases, list):
            st.error("The AI response had no test cases. Please try again.")
        for c in (cases or [])[:10]:
            if not isinstance(c, dict):
                continue
            ss.gen_uid += 1
            ss.gen_cases.append({
                "uid": ss.gen_uid, "title": str(c.get("title") or "Untitled"),
                "type": str(c.get("type") or test_type), "priority": str(c.get("priority") or priority),
                "preconditions": as_text(c.get("preconditions")), "steps": as_text(c.get("steps")),
                "expected": as_text(c.get("expected")),
                "tags": ", ".join(map(str, c.get("tags") or [])) if isinstance(c.get("tags"), list) else as_text(c.get("tags")),
                "edited": 0,
            })
            ss[f"sel_{ss.gen_uid}"] = True

with right, st.container(border=True):
    st.subheader("Review & Approve")
    if not ss.gen_cases and not ss.gen_rejected:
        st.caption("Generated cases appear here.")
    for c in list(ss.gen_cases):
        u = c["uid"]
        with st.container(border=True):
            cb, body = st.columns([1, 12])
            cb.checkbox("Select", key=f"sel_{u}", label_visibility="collapsed")
            kind = c["priority"].lower() if c["priority"].lower() in ("low", "medium", "high") else "medium"
            body.markdown(
                f"<u><b>{escape(c['title'])}</b></u><br>{badge(c['priority'], kind)}"
                f"{badge(c['type'], 'type')}" + (" ✏️" if c["edited"] else ""),
                unsafe_allow_html=True)
            if c["tags"]:
                body.caption("🏷️ " + c["tags"])
            with body.expander("Edit"):
                for f in ("title", "preconditions", "steps", "expected", "tags"):
                    new = (st.text_input if f in ("title", "tags") else st.text_area)(f.capitalize(), c[f], key=f"{f}_{u}", max_chars=LIMIT if f != "title" else 200)
                    if new != c[f]:
                        c[f], c["edited"] = new, 1
            if body.button("Reject", key=f"rej_{u}"):
                ss.gen_cases.remove(c)
                ss.gen_rejected.append(c)
                st.rerun()
    if ss.gen_cases or ss.gen_rejected:
        n_sel = sum(bool(ss.get(f"sel_{c['uid']}")) for c in ss.gen_cases)
        st.markdown(badge(f"{n_sel} of {len(ss.gen_cases)} selected", "type")
                    + (f" {badge(f'{len(ss.gen_rejected)} rejected', 'high')}" if ss.gen_rejected else ""),
                    unsafe_allow_html=True)
        suite = st.text_input("Suite name", key="gen_suite", max_chars=100)
        s1, s2 = st.columns(2)
        if s1.button("Save to Suite", use_container_width=True, disabled=not suite.strip()):
            save("draft")
            st.rerun()
        if s2.button(f"Publish Selected ({n_sel})", use_container_width=True, disabled=not (suite.strip() and n_sel)):
            save("published")
            st.rerun()
