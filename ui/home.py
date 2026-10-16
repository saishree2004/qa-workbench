import streamlit as st

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

