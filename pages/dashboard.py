import pandas as pd
import streamlit as st

from db import get_conn, make_backup, restore_backup
from prompts import SEVERITIES
from styles import inject_css, require_login

PURPLE = "#7C3AED"
STATUSES = ["Open", "Fixed", "Retest", "Closed"]


@st.cache_data(ttl=60)
def q(sql):
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn)


def one(sql):
    v = q(sql).iloc[0, 0]
    return 0 if pd.isna(v) else int(v)


def chart(data, empty_msg):
    if not data or sum(data.values()) == 0:
        st.info(empty_msg)
        return
    st.bar_chart(pd.Series(data, name="count"), color=PURPLE)


inject_css()
require_login()
st.title("Dashboard")

cases = one("SELECT COUNT(*) FROM test_cases")
published = one("SELECT COUNT(*) FROM test_cases WHERE status='published'")
rejected = one("SELECT COUNT(*) FROM test_cases WHERE status='rejected'")
edited = one("SELECT COUNT(*) FROM test_cases WHERE edited=1")
open_bugs = one("SELECT COUNT(*) FROM bugs WHERE status='Open'")

runs = q(
    "SELECT r.id, r.started_at, "
    "SUM(rr.result='Pass') AS p, SUM(rr.result='Fail') AS f, "
    "SUM(rr.result='Blocked') AS b, COUNT(rr.id) AS n "
    "FROM runs r JOIN run_results rr ON rr.run_id=r.id "
    "GROUP BY r.id ORDER BY r.id DESC LIMIT 10"
)
last_rate = f"{runs.iloc[0].p / runs.iloc[0].n:.0%}" if len(runs) else "-"

m = st.columns(4)
for col, label, val in zip(
    m,
    ["Total cases", "Published", "Open bugs", "Last run pass rate"],
    [cases, published, open_bugs, last_rate],
):
    with col, st.container(border=True):
        st.metric(label, val)

if not (cases or len(runs) or one("SELECT COUNT(*) FROM bugs")):
    st.info("Nothing here yet. Generate test cases, run a suite or log a bug to see stats.")

left, right = st.columns(2)

with left, st.container(border=True):
    st.subheader("AI quality")
    chart(
        {"Generated": cases, "Published": published, "Edited": edited, "Rejected": rejected},
        "No AI-generated cases yet. Head to the generator.",
    )
    log = q("SELECT COUNT(*) AS n, COALESCE(SUM(ok), 0) AS ok FROM ai_log").iloc[0]
    if log.n:
        st.caption(f"AI call success rate: {log.ok / log.n:.0%} ({int(log.ok)}/{int(log.n)})")
        chart({"Success": int(log.ok), "Failed": int(log.n - log.ok)}, "")
    else:
        st.caption("No AI calls logged yet.")

with right, st.container(border=True):
    st.subheader("Runs")
    if runs.empty:
        st.info("No test runs recorded yet. Execute a suite to see pass rates.")
    else:
        rate = (runs.p / runs.n * 100).round(1)
        rate.index = [f"#{i}" for i in runs.id]
        st.bar_chart(rate.iloc[::-1].rename("pass %"), color=PURPLE)
        res = q("SELECT result, COUNT(*) AS n FROM run_results GROUP BY result").set_index("result").n
        t = st.columns(3)
        for c, k in zip(t, ["Pass", "Fail", "Blocked"]):
            c.metric(k, int(res.get(k, 0)))

left, right = st.columns(2)
sev = q("SELECT severity, COUNT(*) AS n FROM bugs GROUP BY severity").set_index("severity").n
sta = q("SELECT status, COUNT(*) AS n FROM bugs GROUP BY status").set_index("status").n

with left, st.container(border=True):
    st.subheader("Bugs by severity")
    chart({s: int(sev.get(s, 0)) for s in SEVERITIES}, "No bugs logged yet. Nice and clean.")

with right, st.container(border=True):
    st.subheader("Bugs by status")
    chart({s: int(sta.get(s, 0)) for s in STATUSES}, "No bugs logged yet. Nice and clean.")

with st.container(border=True):
    st.subheader("Backup")
    st.download_button("Download backup", make_backup(), "qa-workbench-backup.zip", "application/zip")
    up = st.file_uploader("Restore backup", type="zip")
    if up and st.button("Restore (replaces all current data)"):
        try:
            restore_backup(up.getvalue())
        except ValueError as e:
            st.error(str(e))
        else:
            st.cache_data.clear()
            st.rerun()
