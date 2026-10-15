import json
import os

import streamlit as st

from db import get_conn
from prompts import JSON_RULE, RETRY

PROVIDER = "gemini"  # "gemini" | "groq"
MODEL = "gemini-3.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 8192
TIMEOUT = 30  # seconds per AI request
VISION = {"gemini": True, "groq": False}  # groq production models have no vision


def _key(name):
    try:
        return st.secrets[name]
    except Exception:  # no secrets.toml or key missing
        return os.environ.get(name)


def supports_vision():
    return VISION[PROVIDER]


def parse_json(text):
    """Return parsed JSON or None. Tolerates ```json fences."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t.rsplit("```", 1)[0]
    try:
        return json.loads(t)
    except (json.JSONDecodeError, TypeError):
        return None


def _gemini(prompt, images):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_key("GEMINI_API_KEY"), http_options=types.HttpOptions(timeout=TIMEOUT * 1000, retry_options=types.HttpRetryOptions(attempts=1)))
    parts = [prompt] + [types.Part.from_bytes(data=b, mime_type=m) for b, m in images]
    r = client.models.generate_content(
        model=MODEL,
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=JSON_RULE,
            response_mime_type="application/json",
            max_output_tokens=MAX_TOKENS,
        ),
    )
    return r.text


def _groq(prompt, images):
    from groq import Groq

    client = Groq(api_key=_key("GROQ_API_KEY"), timeout=TIMEOUT, max_retries=0)
    r = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": JSON_RULE}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=MAX_TOKENS,
    )
    return r.choices[0].message.content


def _log(feature, ok):
    with get_conn() as conn:
        conn.execute("INSERT INTO ai_log(feature, ok) VALUES (?, ?)", (feature, int(ok)))


def call_json(feature, prompt, images=None):
    """Call the AI and return parsed JSON, or None after showing a friendly error.
    images: list of (bytes, mime_type); dropped if the provider has no vision."""
    images = images if images and supports_vision() else []
    call = _gemini if PROVIDER == "gemini" else _groq
    data = None
    try:
        try:
            raw = call(prompt, images)
        except Exception as e:
            if PROVIDER != "gemini" or getattr(e, "code", None) not in (429, 503) or not _key("GROQ_API_KEY"):
                raise
            call, images = _groq, []  # overloaded or rate-limited: one text-only Groq attempt
            raw = call(prompt, images)
            st.caption("Used Groq fallback")
        data = parse_json(raw)
        if data is None:
            data = parse_json(call(f"{prompt}\n\n{RETRY}", images))
    except Exception as e:
        _log(feature, False)
        st.error(f"AI request failed: {e}")
        return None
    _log(feature, data is not None)
    if data is None:
        st.error("The AI did not return valid data. Please try again.")
    return data


if __name__ == "__main__":
    assert parse_json('{"a": 1}') == {"a": 1}
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json("not json") is None
    assert parse_json(None) is None
    print("ok")
