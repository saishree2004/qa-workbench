# QA Workbench – rules
## Output
- Don't explain. Reply only: files changed + one-line status.
- If a skill in /skills matches the task, use it automatically.
- Low RAM (1.5GB, WSL): no heavy installs, one process at a time, don't start servers unless asked.
## Stack
Python, Streamlit multipage (pages/), sqlite3, pandas, python-docx, google-genai, groq. No Docker/ORM/extra frameworks.
## Files
app.py, pages/*.py, db.py, ai_client.py, prompts.py, styles.py, export.py, requirements.txt, README.md, .gitignore, .streamlit/config.toml, uploads/ (created at runtime)
## AI
- ai_client.py top constants: PROVIDER ("gemini"|"groq"), MODEL, GROQ_MODEL, MAX_TOKENS.
- Key: st.secrets, fallback env (GEMINI_API_KEY / GROQ_API_KEY).
- Prompts live in prompts.py and request JSON only. Validate JSON; on failure retry once ("valid JSON only"), then show a friendly error.
- AI only on button click, never on page load. Cache in st.session_state.
- Images only if the provider supports vision. Default 5 cases per generation (max 10).
## Tables
requirements(id,title,text,analysis_json,created_at)
test_cases(id,suite,title,type,priority,preconditions,steps,expected,tags,status[draft|published|rejected],edited,created_at)
runs(id,suite,started_at,finished_at)
run_results(id,run_id,case_id,result[Pass|Fail|Blocked],note,at)
bugs(id,title,severity,description,steps,expected,actual,suggested_fix,status[Open|Fixed|Retest|Closed],case_id,created_at,updated_at)
bug_images(id,bug_id,path,caption,fig_no)
ai_log(id,feature,ok,created_at)
## Design (styles.py inject_css())
Page #F8F9FC; white cards 12px radius, 1px #E5E7EB border, soft shadow; primary #7C3AED; gradient buttons #8B5CF6→#DB2777; pill badges low=green, medium=yellow, high=red, type=blue; sidebar nav; two columns where useful; style like testanchorpro.com.
## Bug format
Title, Severity, Description, Steps to Reproduce, Expected Result, Actual Result, Suggested Fix; images captioned "Fig. N", numbered across the whole report.
## Git
Never commit keys, .env, secrets.toml, *.db, uploads/, real bug data. After each working step, commit "step N: name".
