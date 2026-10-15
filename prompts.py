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
