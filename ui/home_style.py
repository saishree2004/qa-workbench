import streamlit as st

CSS = """
<style>
.st-key-qw-hero { background: #F3EEFF; border: 1px solid #E9DDFE; border-radius: 16px;
  padding: 2.5rem 1.5rem; align-items: center; text-align: center; }
.st-key-qw-hero > div, .st-key-qw-hero [data-testid="stMarkdownContainer"],
.home-hero, .home-hero h1 { width: 100%; text-align: center; margin-left: 0; margin-right: 0;
  padding-left: 0; padding-right: 0; }
/* the heading anchor icon reserves space on the right and pushes the title off-center */
.home-hero h1 [data-testid="stHeaderActionElements"], .home-hero h1 a { display: none !important; }
.home-hero h1 { font-size: 2.6rem; font-weight: 800; margin: 0 0 .5rem; color: #111827; }
.home-hero h1 span { background: linear-gradient(90deg, #8B5CF6, #DB2777); -webkit-background-clip: text;
  background-clip: text; color: transparent; }
.home-hero p { text-align: center; color: #4B5563; max-width: 640px; margin: 0 auto; font-size: 1.1rem; }
.st-key-qw-hero [data-testid="stPageLink"] { margin-top: 1.5rem; }
/* overrides the width:100% hero rule above so the CTA stays button-sized */
.st-key-qw-hero > div:has([data-testid="stPageLink"]), .st-key-qw-hero [data-testid="stPageLink"],
.st-key-qw-hero [data-testid="stPageLink"] a { width: fit-content !important; margin-left: auto; margin-right: auto; }
.st-key-qw-hero [data-testid="stPageLink"] a { background: linear-gradient(90deg, #8B5CF6, #DB2777);
  border-radius: 10px; padding: .5rem 1.25rem; }
.st-key-qw-hero [data-testid="stPageLink"] a, .st-key-qw-hero [data-testid="stPageLink"] a * { color: #fff; }
.st-key-qw-hero [data-testid="stPageLink"] a:focus-visible { outline: 2px solid #7C3AED; outline-offset: 2px; }
.home-flow { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; justify-content: center;
  margin: 1.25rem 0; }
.home-flow .step { background: #fff; border: 1px solid #E5E7EB; border-radius: 999px; padding: .35rem .9rem;
  font-weight: 600; color: #374151; }
.home-flow .step b { display: inline-block; width: 1.4rem; height: 1.4rem; line-height: 1.4rem; border-radius: 50%;
  background: #7C3AED; color: #fff; text-align: center; margin-right: .4rem; font-size: .8rem; }
.home-flow .arrow { color: #9CA3AF; }
.home-stat { background: #fff; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem 1.25rem;
  box-shadow: 0 1px 3px rgba(16,24,40,.06); }
.home-stat .label { color: #6B7280; font-size: .85rem; }
.home-stat .value { font-size: 1.8rem; font-weight: 800; color: #111827; }
.home-row { display: flex; align-items: center; gap: .75rem; padding: .45rem 0;
  border-bottom: 1px solid #F3F4F6; }
.home-row .title { flex: 1; min-width: 0; overflow-wrap: anywhere; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.home-row .pills { flex-shrink: 0; display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.home-row .pills .badge { margin: 0; text-align: center; box-sizing: border-box; overflow: hidden;
  text-overflow: ellipsis; padding: 2px 6px; }
.pills-bug .badge:first-child { width: 72px; }
.pills-bug .badge:last-child { width: 64px; }
.pills-run .badge { width: 56px; }
.home-row:last-child { border-bottom: 0; }
.home-footer { text-align: center; color: #9CA3AF; font-size: .85rem; margin-top: 2rem; padding: 1rem 0;
  border-top: 1px solid #E5E7EB; }
</style>
"""


def inject_home_css():
    st.markdown(CSS, unsafe_allow_html=True)
