import streamlit as st

from db import init_db
from styles import inject_css, require_login

st.set_page_config(page_title="QA Workbench", page_icon="assets/favicon.svg", layout="wide")
st.logo("assets/logo.svg", icon_image="assets/favicon.svg")
inject_css()
require_login()
init_db()


FEATURES = [
    ("pages/analyzer.py", "🔍", "Analyzer", "Break a requirement into testable points, gaps and risks."),
    ("pages/generator.py", "✨", "Generator", "Turn requirements into structured test cases in one click."),
    ("pages/suites.py", "🗂️", "Suites", "Organize, review and publish cases into runnable suites."),
    ("pages/bug_builder.py", "🐞", "Bug Builder", "Write clear bug reports with numbered, captioned screenshots."),
    ("pages/bug_tracker.py", "📋", "Bug Tracker", "Follow every bug from Open to Closed."),
    ("pages/daily_update.py", "📝", "Daily Update", "Share a clean end-of-day QA summary."),
    ("pages/dashboard.py", "📊", "Dashboard", "See pass rates, open bugs and progress at a glance."),
]


def home():
    st.image("assets/logo.svg", width=220)
    st.markdown('<div class="hero"><h1>Test smarter. <span>Ship with confidence.</span></h1>'
                '<p>From requirements to test cases to bugs, QA Workbench keeps your whole '
                'testing workflow in one place.</p></div>', unsafe_allow_html=True)
    st.markdown("### Everything you need")
    for i in range(0, len(FEATURES), 3):
        for col, (path, icon, title, desc) in zip(st.columns(3), FEATURES[i:i + 3]):
            with col, st.container(border=True):
                st.markdown(f"#### {icon} {title}")
                st.caption(desc)
                st.page_link(path, label=f"Open {title}", icon=":material/arrow_forward:")


nav = st.navigation({
    "": [st.Page(home, title="Home", icon="🏠", default=True)],
    "Plan": [
        st.Page("pages/analyzer.py", title="Analyzer", icon="🔍"),
        st.Page("pages/generator.py", title="Generator", icon="✨"),
        st.Page("pages/suites.py", title="Suites", icon="🗂️"),
    ],
    "Bugs": [
        st.Page("pages/bug_builder.py", title="Bug Builder", icon="🐞"),
        st.Page("pages/bug_tracker.py", title="Bug Tracker", icon="📋"),
    ],
    "Report": [
        st.Page("pages/daily_update.py", title="Daily Update", icon="📝"),
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
    ],
})
nav.run()
