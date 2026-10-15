import json

import streamlit as st

from ai_client import call_json
from db import get_conn
from prompts import ANALYZE_KEYS, analyze_requirement
from styles import badge, inject_css

inject_css()
ss = st.session_state
SECTIONS = {"ambiguities": "Ambiguities", "missing_edge_cases": "Missing edge cases",
            "untestable_statements": "Untestable statements", "po_questions": "Questions for PO"}


def items(data, key):
    v = data.get(key)
    return [str(x) for x in v] if isinstance(v, list) else []


st.title("Requirement Analyzer")
left, right = st.columns(2, gap="large")

with left, st.container(border=True):
    st.subheader("Requirement")
    t_manual, t_file = st.tabs(["Manual Description", "Requirements File"])
    with t_manual:
        manual = st.text_area("Paste the requirement", key="an_text", height=260)
    with t_file:
        up = st.file_uploader("Upload .txt or .md", type=["txt", "md"], key="an_file")
        # shortcut: truncates large files to 20k chars, chunk if real specs exceed it
        file_text = up.getvalue().decode("utf-8", errors="replace")[:20000] if up else ""
        if file_text:
            st.caption(f"{len(file_text)} chars loaded from {up.name}")
    requirement = (file_text or manual).strip()
    if st.button("🔍 Analyze", use_container_width=True, disabled=not requirement):
        with st.spinner("Analyzing..."):
            data = call_json("analyzer", analyze_requirement(requirement))
        if isinstance(data, dict):
            ss["an_result"] = {"text": requirement, "data": {k: items(data, k) for k in ANALYZE_KEYS}}
        elif data is not None:
            st.error("The AI response was not in the expected format. Please try again.")

res = ss.get("an_result")
with right, st.container(border=True):
    st.subheader("Analysis")
    if not res:
        st.caption("Run an analysis to see results here.")
    else:
        data = res["data"]
        for k, label in SECTIONS.items():
            st.markdown(f"**{label}** {badge(len(data[k]), 'type')}", unsafe_allow_html=True)
            for x in data[k]:
                st.markdown(f"- {x}")
        st.markdown("**Copy questions for PO**")
        st.code("\n".join(f"{i}. {q}" for i, q in enumerate(data["po_questions"], 1)), language=None)
        b1, b2 = st.columns(2)
        if b1.button("💾 Save", use_container_width=True):
            with get_conn() as conn:
                conn.execute("INSERT INTO requirements(title,text,analysis_json) VALUES (?,?,?)",
                             (res["text"].splitlines()[0][:80], res["text"], json.dumps(data)))
            st.toast("Requirement saved")
        if b2.button("➡️ Send to Generator", use_container_width=True):
            edge = "\n".join(f"- {x}" for x in data["missing_edge_cases"])
            ss["analyzer_handoff"] = res["text"] + (f"\n\nEdge cases to cover:\n{edge}" if edge else "")
            ss.pop("gen_text", None)  # let the generator prefill from the handoff
            st.switch_page("pages/generator.py")
