import html

import pandas as pd
import streamlit as st

from db import LIMIT, get_conn, guarded
from prompts import PRIORITIES, TEST_TYPES
from styles import badge, inject_css, require_login

inject_css()
require_login()
ss = st.session_state
ss.setdefault("run", None)  # {"id", "suite", "done"} for the active run
st.title("Suites")
tab_browse, tab_run = st.tabs(["Browse", "Run suite"])


def suites():
    with get_conn() as c:
        return [r[0] for r in c.execute("SELECT DISTINCT suite FROM test_cases WHERE suite IS NOT NULL AND suite != '' ORDER BY suite")]


with tab_browse:
    names = suites()
    if not names:
        st.info("No test cases yet. Generate some first.")
    else:
        suite = st.selectbox("Suite", names, key="br_suite")
        q = st.text_input("Search", key="br_q")
        f1, f2, f3 = st.columns(3)
        types = f1.multiselect("Type", TEST_TYPES, key="br_type")
        prios = f2.multiselect("Priority", PRIORITIES, key="br_prio")
        stats = f3.multiselect("Status", ["draft", "published", "rejected"], key="br_status")
        with get_conn() as c:
            df = pd.read_sql_query("SELECT id,title,type,priority,status,steps,expected,tags FROM test_cases WHERE suite=?", c, params=(suite,))
        if q:
            m = df.apply(lambda r: q.lower() in " ".join(map(str, r.values)).lower(), axis=1)
            df = df[m]
        for col, vals in (("type", types), ("priority", prios), ("status", stats)):
            if vals:
                df = df[df[col].isin(vals)]
        df = df.reset_index(drop=True)
        st.caption(f"{len(df)} case(s)")
        ev = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun", selection_mode="multi-row", key="br_table")
        ids = [int(df.loc[i, "id"]) for i in ev.selection.rows if i < len(df)]
        d1, d2 = st.columns([1, 4])
        d1.download_button("Export CSV", df.to_csv(index=False).encode(), f"{suite}.csv", "text/csv")
        if ids:
            with d2.popover(f"Delete selected ({len(ids)})"):
                st.warning(f"Permanently delete {len(ids)} case(s), their run results and bug links?")
                if st.button("Confirm delete", type="primary", key="br_del"):
                    marks = ",".join("?" * len(ids))
                    with guarded(), get_conn() as c:
                        c.execute(f"DELETE FROM run_results WHERE case_id IN ({marks})", ids)
                        c.execute(f"UPDATE bugs SET case_id=NULL WHERE case_id IN ({marks})", ids)
                        c.execute(f"DELETE FROM test_cases WHERE id IN ({marks})", ids)
                    st.rerun()

with tab_run:
    names = suites()
    run = ss.run
    if not names:
        st.info("No test cases yet.")
    elif run is None:
        suite = st.selectbox("Suite", names, key="run_suite")
        with get_conn() as c:
            n = c.execute("SELECT COUNT(*) FROM test_cases WHERE suite=? AND status='published'", (suite,)).fetchone()[0]
        st.caption(f"{n} published case(s)")
        if st.button("Start run", type="primary", disabled=n == 0):
            with guarded(), get_conn() as c:
                rid = c.execute("INSERT INTO runs(suite) VALUES(?)", (suite,)).lastrowid
            ss.run = {"id": rid, "suite": suite, "done": False}
            st.rerun()
    else:
        st.subheader(f"Run #{run['id']} - {run['suite']}")
        with get_conn() as c:
            cases = c.execute("SELECT * FROM test_cases WHERE suite=? AND status='published' ORDER BY id", (run["suite"],)).fetchall()
        if not run["done"]:
            for cs in cases:
                with st.container(border=True):
                    st.markdown(f"**{html.escape(cs['title'] or '')}** " + badge(cs["type"] or "", "type") +
                                " " + badge(cs["priority"] or "", (cs["priority"] or "low").lower()), unsafe_allow_html=True)
                    st.markdown("**Steps**\n\n" + (cs["steps"] or "-"))
                    st.markdown("**Expected**\n\n" + (cs["expected"] or "-"))
                    res = st.radio("Result", ["Pass", "Fail", "Blocked"], index=None, horizontal=True, key=f"res_{cs['id']}")
                    note = st.text_input("Note", key=f"note_{cs['id']}", max_chars=LIMIT)
                    if res == "Fail" and st.button("Report bug", key=f"bug_{cs['id']}"):
                        ss["bug_prefill"] = {"case_id": cs["id"], "title": cs["title"], "steps": cs["steps"],
                                             "expected": cs["expected"], "note": note}
                        st.switch_page("pages/bug_builder.py")
            unset = [c for c in cases if not ss.get(f"res_{c['id']}")]
            if unset:
                st.caption(f"{len(unset)} case(s) without a result will be skipped.")
            b1, b2 = st.columns([1, 5])
            if b1.button("Finish run", type="primary"):
                with guarded(), get_conn() as c:
                    c.executemany("INSERT INTO run_results(run_id,case_id,result,note) VALUES(?,?,?,?)",
                                  [(run["id"], x["id"], ss[f"res_{x['id']}"], str(ss.get(f"note_{x['id']}", ""))[:LIMIT]) for x in cases if ss.get(f"res_{x['id']}")])
                    c.execute("UPDATE runs SET finished_at=CURRENT_TIMESTAMP WHERE id=?", (run["id"],))
                run["done"] = True
                st.rerun()
            if b2.button("Cancel run"):
                with guarded(), get_conn() as c:
                    c.execute("DELETE FROM runs WHERE id=?", (run["id"],))
                ss.run = None
                st.rerun()
        else:
            with get_conn() as c:
                counts = dict(c.execute("SELECT result, COUNT(*) FROM run_results WHERE run_id=? GROUP BY result", (run["id"],)).fetchall())
            total = sum(counts.values())
            m = st.columns(4)
            m[0].metric("Pass rate", f"{counts.get('Pass', 0) / total:.0%}" if total else "n/a")
            for col, k in zip(m[1:], ("Pass", "Fail", "Blocked")):
                col.metric(k, counts.get(k, 0))
            if st.button("New run"):
                ss.run = None
                st.rerun()
