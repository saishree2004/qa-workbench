import html

import streamlit as st

from db import get_conn
from styles import badge
from ui.home_style import inject_home_css

GROUPS = [
    ("Plan", "Turn requirements into reviewed, runnable suites.", [
        ("pages/analyzer.py", "🔍", "Analyzer"),
        ("pages/generator.py", "✨", "Generator"),
        ("pages/suites.py", "🗂️", "Suites"),
    ]),
    ("Bugs", "Write clear reports and follow them to Closed.", [
        ("pages/bug_builder.py", "🐞", "Bug Builder"),
        ("pages/bug_tracker.py", "📋", "Bug Tracker"),
    ]),
    ("Report", "Share progress and see pass rates at a glance.", [
        ("pages/daily_update.py", "📝", "Daily Update"),
        ("pages/dashboard.py", "📊", "Dashboard"),
    ]),
]
STEPS = ["Analyze", "Generate", "Organize", "Log bugs", "Report"]
SEVERITY = {"low": "low", "medium": "medium", "high": "high", "critical": "high"}
STATUS = {"Open": "high", "Retest": "medium", "Fixed": "low", "Closed": "type"}


def _load():
    # read-only: SELECT statements only
    with get_conn() as c:
        cases = c.execute("SELECT COUNT(*) FROM test_cases").fetchone()[0]
        open_bugs = c.execute("SELECT COUNT(*) FROM bugs WHERE status='Open'").fetchone()[0]
        last = c.execute(
            "SELECT r.started_at, date(r.started_at) = date('now') AS today, "
            "COUNT(rr.id) AS total, SUM(rr.result='Pass') AS passed "
            "FROM runs r LEFT JOIN run_results rr ON rr.run_id = r.id "
            "GROUP BY r.id ORDER BY r.started_at DESC, r.id DESC LIMIT 1").fetchone()
        bugs = c.execute("SELECT title, severity, status FROM bugs "
                         "ORDER BY created_at DESC, id DESC LIMIT 5").fetchall()
        runs = c.execute(
            "SELECT r.suite, r.started_at, COUNT(rr.id) AS total, SUM(rr.result='Pass') AS passed "
            "FROM runs r LEFT JOIN run_results rr ON rr.run_id = r.id "
            "GROUP BY r.id ORDER BY r.started_at DESC, r.id DESC LIMIT 5").fetchall()
    return cases, open_bugs, last, bugs, runs


def _rate(row):
    return f"{round(100 * (row['passed'] or 0) / row['total'])}%" if row and row["total"] else "–"


def _stat(col, label, value):
    col.markdown(f'<div class="home-stat"><div class="label">{label}</div>'
                 f'<div class="value">{html.escape(str(value))}</div></div>', unsafe_allow_html=True)


def _row(text, pills):
    return f'<div class="home-row"><span>{html.escape(str(text))}</span><span>{pills}</span></div>'


def home():
    inject_home_css()
    st.markdown('<div class="home-hero"><h1>Test smarter. <span>Ship with confidence.</span></h1>'
                '<p>From requirements to test cases to bugs, QA Workbench keeps your whole '
                'testing workflow in one place.</p></div>', unsafe_allow_html=True)
    with st.container(key="home_cta"):
        st.page_link("pages/analyzer.py", label="Start with a requirement", icon=":material/arrow_forward:")

    steps = '<span class="arrow">→</span>'.join(
        f'<span class="step"><b>{i}</b>{s}</span>' for i, s in enumerate(STEPS, 1))
    st.markdown(f'<div class="home-flow">{steps}</div>', unsafe_allow_html=True)

    cases, open_bugs, last, bugs, runs = _load()
    st.markdown("### Overview")
    c1, c2, c3, c4 = st.columns(4)
    _stat(c1, "Test cases", cases or "–")
    _stat(c2, "Open bugs", open_bugs if bugs else "–")
    _stat(c3, "Last run pass rate", _rate(last))
    _stat(c4, "Last run", ("Today" if last["today"] else last["started_at"][:10]) if last else "–")

    st.markdown("### Everything you need")
    for col, (name, desc, links) in zip(st.columns(3), GROUPS):
        with col, st.container(border=True):
            st.markdown(f"#### {name}")
            st.caption(desc)
            for path, icon, title in links:
                st.page_link(path, label=title, icon=icon)

    st.markdown("### Recent activity")
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("**Latest bugs**")
        st.markdown("".join(_row(b["title"], badge(b["severity"], SEVERITY.get(str(b["severity"]).lower(), "type"))
                                 + badge(b["status"], STATUS.get(b["status"], "type"))) for b in bugs)
                    or "No bugs logged yet.", unsafe_allow_html=True)
    with right, st.container(border=True):
        st.markdown("**Latest runs**")
        st.markdown("".join(_row(f"{r['suite']} · {r['started_at'][:10]}", badge(_rate(r), "type")) for r in runs)
                    or "No runs yet.", unsafe_allow_html=True)

    st.markdown('<div class="home-footer">QA Workbench · Analyze, generate, organize, log bugs, report.</div>',
                unsafe_allow_html=True)
