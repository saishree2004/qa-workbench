JSON_RULE = "Respond with a single valid JSON object only. No markdown, no code fences, no commentary."
RETRY = "Your previous reply was not valid JSON. Reply again with valid JSON only."

TEST_TYPES = ["Functional", "UI", "Boundary", "Negative", "Security", "Mobile/Interruption"]
PRIORITIES = ["High", "Medium", "Low"]


def generate_cases(requirement, test_type, priority, count):
    return f"""You are a senior QA engineer. Write {count} distinct {test_type} test cases with {priority} priority
for the requirement below. Each step must be one concrete, verifiable user action.

Return JSON exactly in this shape:
{{"cases": [{{"title": "short imperative title", "type": "{test_type}", "priority": "{priority}",
"preconditions": "text", "steps": ["step 1", "step 2"], "expected": "expected result",
"tags": ["tag1", "tag2"]}}]}}

Requirement:
\"\"\"{requirement}\"\"\""""


ANALYZE_KEYS = ["ambiguities", "missing_edge_cases", "untestable_statements", "po_questions"]


def analyze_requirement(requirement):
    return f"""You are a senior QA engineer reviewing a requirement before testing starts.
Be specific and quote the requirement where useful. Each list item is one short string.

Return JSON exactly in this shape:
{{"ambiguities": ["vague or conflicting wording"], "missing_edge_cases": ["scenario the requirement does not cover"],
"untestable_statements": ["statement with no measurable pass/fail criteria"],
"po_questions": ["question to ask the Product Owner"]}}

Requirement:
\"\"\"{requirement}\"\"\""""


BUG_KEYS = ["title", "severity", "description", "steps", "expected", "actual", "suggested_fix"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]


def build_bug(notes, has_images):
    shots = "Screenshots are attached; use what they show. " if has_images else ""
    return f"""You are a senior QA engineer writing a clear bug report from rough notes. {shots}
Do not invent facts that are not in the notes. Keep it concise.
"severity" must be one of {SEVERITIES}. "steps" is a numbered list as one string with newlines.

Return JSON exactly in this shape:
{{"title": "short summary", "severity": "Medium", "description": "what is wrong",
"steps": "1. ...\\n2. ...", "expected": "expected result", "actual": "actual result",
"suggested_fix": "likely cause or fix"}}

Notes:
\"\"\"{notes}\"\"\""""
