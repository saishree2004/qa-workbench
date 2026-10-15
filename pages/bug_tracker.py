import os

import pandas as pd
import streamlit as st

from db import get_conn
from export import bugs_to_docx
from prompts import SEVERITIES
from styles import badge, inject_css

STATUSES = ["Open", "Fixed", "Retest", "Closed"]

inject_css()
st.title("Bug Tracker")

c1, c2, c3 = st.columns([1, 1, 2])
sev = c1.selectbox("Severity", ["All", *SEVERITIES])
stat = c2.selectbox("Status", ["All", *STATUSES])
q = c3.text_input("Search")

sql, args = "SELECT * FROM bugs WHERE 1=1", []
if sev != "All":
    sql += " AND severity=?"; args.append(sev)
if stat != "All":
    sql += " AND status=?"; args.append(stat)
if q:
    sql += " AND (title LIKE ? OR description LIKE ?)"; args += [f"%{q}%"] * 2
with get_conn() as c:
    bugs = c.execute(sql + " ORDER BY id DESC", args).fetchall()

if not bugs:
    st.info("No bugs match.")
    st.stop()

df = pd.DataFrame([{"Select": False, "ID": b["id"], "Title": b["title"], "Severity": b["severity"],
                    "Status": b["status"], "Updated": b["updated_at"]} for b in bugs])
edited = st.data_editor(df, hide_index=True, use_container_width=True, key="bt_table",
                        disabled=["ID", "Title", "Severity", "Status", "Updated"])
picked = [int(i) for i in edited.loc[edited["Select"], "ID"]]
st.download_button(f"Export selected to Word ({len(picked)})", bugs_to_docx(picked) if picked else b"",
                   file_name="bugs.docx", disabled=not picked,
                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

for b in bugs:
    with st.expander(f"#{b['id']} {b['title']} [{b['status']}]"):
        kind = {"Low": "low", "Medium": "medium"}.get(b["severity"], "high")
        st.markdown(badge(b["severity"], kind), unsafe_allow_html=True)
        for label, key in [("Description", "description"), ("Steps to Reproduce", "steps"),
                           ("Expected Result", "expected"), ("Actual Result", "actual"),
                           ("Suggested Fix", "suggested_fix")]:
            st.markdown(f"**{label}**\n\n{b[key] or ''}")
        with get_conn() as c:
            imgs = c.execute("SELECT * FROM bug_images WHERE bug_id=? ORDER BY fig_no", (b["id"],)).fetchall()
        for im in imgs:
            if os.path.isfile(im["path"] or ""):
                st.image(im["path"], caption=f"Fig. {im['fig_no']}: {im['caption'] or ''}")
        s1, s2 = st.columns([2, 1])
        new = s1.selectbox("Status", STATUSES, index=STATUSES.index(b["status"]), key=f"st_{b['id']}")
        if new != b["status"]:
            with get_conn() as c:
                c.execute("UPDATE bugs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new, b["id"]))
            st.rerun()
        if s2.checkbox("Confirm delete", key=f"cf_{b['id']}") and s2.button("Delete", key=f"del_{b['id']}"):
            with get_conn() as c:
                c.execute("DELETE FROM bugs WHERE id=?", (b["id"],))
            for im in imgs:
                if os.path.isfile(im["path"] or ""):
                    os.remove(im["path"])
            st.rerun()
