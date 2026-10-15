from datetime import date

import pandas as pd
import streamlit as st

from ai_client import call_json
from db import get_conn
from prompts import daily_update
from styles import inject_css

inject_css()
st.title("Daily Update")

day = st.date_input("Date", date.today()).isoformat()


def q(sql):
    conn = get_conn()
    try:
        return pd.read_sql_query(sql, conn, params=(day,))
    finally:
        conn.close()


runs = q("""SELECT r.suite, SUM(rr.result='Pass') AS Pass, SUM(rr.result='Fail') AS Fail,
            SUM(rr.result='Blocked') AS Blocked
            FROM runs r JOIN run_results rr ON rr.run_id=r.id
            WHERE date(r.finished_at)=? GROUP BY r.suite""")
raised = q("SELECT title, severity FROM bugs WHERE date(created_at)=?")
changed = q("""SELECT title, status FROM bugs
               WHERE date(updated_at)=? AND date(created_at)<>date(updated_at)""")
blocked = q("""SELECT t.title, rr.note FROM run_results rr JOIN test_cases t ON t.id=rr.case_id
               WHERE rr.result='Blocked' AND date(rr.at)=?""")

tot = runs[["Pass", "Fail", "Blocked"]].sum() if len(runs) else pd.Series(0, index=["Pass", "Fail", "Blocked"])
cols = st.columns(5)
for col, (label, val) in zip(cols, [("Pass", tot["Pass"]), ("Fail", tot["Fail"]), ("Blocked", tot["Blocked"]),
                                    ("Bugs raised", len(raised)), ("Bugs updated", len(changed))]):
    col.metric(label, int(val))

notes = st.text_area("Blockers / notes", placeholder="Optional")


def lines(df, fmt):
    return "\n".join(fmt(r) for r in df.itertuples(index=False)) or "None"


def facts():
    return {
        "sections_tested": lines(runs, lambda r: f"- {r.suite}: {int(r.Pass)} pass, {int(r.Fail)} fail, {int(r.Blocked)} blocked"),
        "bugs_raised": lines(raised, lambda r: f"- {r.title} ({r.severity})"),
        "bugs_updated": lines(changed, lambda r: f"- {r.title} -> {r.status}"),
        "blocked_cases": lines(blocked, lambda r: f"- {r.title}: {r.note or 'no note'}"),
    }


def template():
    f = facts()
    blockers = f["blocked_cases"] if f["blocked_cases"] != "None" else ""
    blockers = "\n".join(x for x in [blockers, notes.strip()] if x) or "None"
    return (f"Daily QA Update - {day}\n\nSections tested:\n{f['sections_tested']}\n\n"
            f"Results: {int(tot['Pass'])} pass, {int(tot['Fail'])} fail, {int(tot['Blocked'])} blocked\n\n"
            f"Bugs raised:\n{f['bugs_raised']}\n\nBugs updated:\n{f['bugs_updated']}\n\n"
            f"Blockers:\n{blockers}\n\nNext steps:\n- ")


def from_ai(d):
    return (f"Daily QA Update - {day}\n\nSections tested:\n{d.get('sections_tested', '')}\n\n"
            f"Results:\n{d.get('results', '')}\n\nBugs raised:\n{d.get('bugs_raised', '')}\n\n"
            f"Blockers:\n{d.get('blockers', '')}\n\nNext steps:\n{d.get('next_steps', '')}")


b1, b2 = st.columns(2)
if b1.button("Generate with AI", type="primary"):
    with st.spinner("Generating..."):
        d = call_json("daily_update", daily_update(facts(), notes))
    if d:
        st.session_state["daily_edit"] = st.session_state["daily_text"] = from_ai(d)
if b2.button("Quick summary (no AI)"):
    st.session_state["daily_edit"] = st.session_state["daily_text"] = template()

if "daily_text" in st.session_state:
    text = st.text_area("Edit", st.session_state["daily_text"], height=360, key="daily_edit")
    st.code(text, language=None)
