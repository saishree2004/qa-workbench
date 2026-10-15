import streamlit as st

CSS = """
<style>
.stApp { background: #F8F9FC; }
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E5E7EB; }
.card, [data-testid="stVerticalBlockBorderWrapper"] {
  background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
  box-shadow: 0 1px 3px rgba(16,24,40,.06), 0 1px 2px rgba(16,24,40,.04);
}
.card { padding: 1.25rem; margin-bottom: 1rem; }
h1, h2, h3 { color: #111827; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  background: linear-gradient(90deg, #8B5CF6, #DB2777); color: #fff; border: 0;
  border-radius: 10px; font-weight: 600;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  filter: brightness(1.05); color: #fff;
}
.stButton > button:focus-visible { outline: 2px solid #7C3AED; outline-offset: 2px; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .75rem;
  font-weight: 600; margin-right: 4px; }
.badge-low { background: #DCFCE7; color: #166534; }
.badge-medium { background: #FEF9C3; color: #854D0E; }
.badge-high { background: #FEE2E2; color: #991B1B; }
.badge-type { background: #DBEAFE; color: #1E40AF; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def badge(text, kind):
    """kind: low|medium|high|type"""
    return f'<span class="badge badge-{kind}">{text}</span>'
