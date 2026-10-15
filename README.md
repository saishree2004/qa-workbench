# QA Workbench

A Streamlit app for QA work: turn a requirement into test cases, organize them into suites, run them, write bug reports with numbered screenshots, and track progress. AI helps on button click only, never on page load. Data lives in a local SQLite file.

## Features

1. **Analyzer** - break a requirement into testable points, gaps and risks.
2. **Generator** - turn requirements into structured test cases (5 by default, max 10), then review and approve.
3. **Suites** - browse published cases and run a suite with Pass / Fail / Blocked results.
4. **Bug Builder** - turn rough notes into a full bug report; screenshots are captioned "Fig. N" and numbered across the whole report. Export to .docx.
5. **Bug Tracker** - follow each bug from Open to Fixed, Retest and Closed.
6. **Daily Update** - generate an end-of-day QA summary.
7. **Dashboard** - pass rates, open bugs by severity, run history, AI call success rate, and backup/restore.

## Local setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and set:

- `APP_PASSWORD` - the login password (the app refuses access if it is unset)
- `GEMINI_API_KEY` - primary AI provider
- `GROQ_API_KEY` - optional fallback

Keys can also come from environment variables of the same names. `secrets.toml` is git-ignored; never commit it.

## Run

```bash
streamlit run app.py
```

## AI providers

Set at the top of `ai_client.py`:

| Constant | Meaning |
|----------|---------|
| `PROVIDER` | `"gemini"` or `"groq"` |
| `MODEL` | Gemini model |
| `GROQ_MODEL` | Groq model |
| `MAX_TOKENS` | Response cap |

- **Gemini is primary** and supports screenshots (vision).
- **Groq is the fallback.** If Gemini returns 429 or 503 and `GROQ_API_KEY` is set, the app makes one text-only Groq attempt and shows "Used Groq fallback".
- Set `PROVIDER = "groq"` to use Groq directly. Groq has no vision, so screenshots are attached to bug reports but not analysed.
- Prompts request JSON only. Invalid JSON is retried once, then a friendly error is shown.

## Project structure

```
app.py              entry point, login gate, home page
pages/
  analyzer.py       Requirement Analyzer
  generator.py      Test Case Generator
  suites.py         Browse and run suites
  bug_builder.py    Bug Builder
  bug_tracker.py    Bug Tracker
  daily_update.py   Daily Update
  dashboard.py      Dashboard and backup/restore
ai_client.py        provider constants, Gemini/Groq calls, JSON validation
prompts.py          all AI prompts
db.py               SQLite schema, queries, backup/restore
styles.py           inject_css(), require_login()
export.py           .docx bug report export
assets/             logo and favicon
tests/smoke_test.py smoke test
.streamlit/         config.toml, secrets.toml.example
uploads/            screenshots (created at runtime, git-ignored)
```

## Backup and restore

Streamlit Community Cloud storage is ephemeral: the SQLite database and `uploads/` reset whenever the app restarts, redeploys or sleeps and wakes. Treat the cloud copy as disposable.

- On the **Dashboard**, use **Download backup** to get a zip of the database and uploads. Do this at the end of every session.
- After a reset, use **Restore backup** on the Dashboard and upload the zip. Restore replaces all current data.

## Deploy to Streamlit Community Cloud

1. Push the repo to GitHub. Confirm `secrets.toml`, `*.db` and `uploads/` are not committed.
2. At share.streamlit.io, choose **New app**, select the repo and branch, and set the main file to `app.py`.
3. Under **Advanced settings > Secrets**, paste:
   ```toml
   APP_PASSWORD = "..."
   GEMINI_API_KEY = "..."
   GROQ_API_KEY = "..."
   ```
4. Deploy. Dependencies install from `requirements.txt`.
5. Restore your latest backup from the Dashboard, since storage starts empty.
