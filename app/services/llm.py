import os
import json
import httpx
from typing import List, Dict, Any, Optional


LLM_API_URL = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = """You are a QA test case generator for medical device software documentation.

Given a section of a technical manual for the CardioTrack CT-200 Blood Pressure Monitor, generate 3-5 concrete, executable QA test cases.

Each test case MUST be a JSON object with exactly these fields:
{
  "id": "TC-NNN",
  "title": "short descriptive title",
  "description": "what this test verifies",
  "preconditions": "setup required before executing",
  "steps": ["step 1", "step 2", "..."],
  "expected_result": "concrete pass/fail criterion",
  "priority": "critical|high|medium|low",
  "traced_to_section": "section number from the document"
}

IMPORTANT RULES:
- Return ONLY a valid JSON array of test case objects
- No markdown, no explanation text, no code fences
- Each test case must be concrete enough that someone else could execute it
- For medical devices, prioritize safety-critical scenarios
- Include edge cases (boundary values, error conditions)
- Steps must be numbered and actionable
- Expected results must be binary (pass/fail), not vague"""

USER_PROMPT_TEMPLATE = """Generate QA test cases for this section of the CardioTrack CT-200 manual:

Section: {section_title}
Section Number: {section_number}

Content:
{content}

Generate 3-5 test cases as a JSON array. Return ONLY the JSON array, nothing else."""


def validate_test_cases(raw_output: str) -> List[Dict]:
    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            start = cleaned.index("[")
            end = cleaned.rindex("]") + 1
            parsed = json.loads(cleaned[start:end])
        except (ValueError, json.JSONDecodeError):
            return []

    if not isinstance(parsed, list):
        return []

    validated = []
    required_fields = {"id", "title", "description", "preconditions",
                       "steps", "expected_result", "priority"}

    for tc in parsed:
        if not isinstance(tc, dict):
            continue
        if not required_fields.issubset(tc.keys()):
            continue
        if not isinstance(tc["steps"], list) or len(tc["steps"]) == 0:
            continue
        if tc["priority"] not in ("critical", "high", "medium", "low"):
            tc["priority"] = "medium"

        validated.append(tc)

    return validated


async def generate_test_cases(
    section_title: str,
    section_number: str,
    content: str,
) -> Dict[str, Any]:
    if not LLM_API_KEY:
        return {
            "success": False,
            "error": "LLM_API_KEY not configured",
            "test_cases": [],
            "model_used": "",
        }

    user_prompt = USER_PROMPT_TEMPLATE.format(
        section_title=section_title,
        section_number=section_number,
        content=content[:4000],
    )

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                LLM_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()

        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        model_used = data.get("model", LLM_MODEL)

        test_cases = validate_test_cases(raw_text)

        if not test_cases:
            return {
                "success": False,
                "error": "LLM returned invalid/malformed output",
                "raw_output": raw_text[:500],
                "test_cases": [],
                "model_used": model_used,
            }

        return {
            "success": True,
            "test_cases": test_cases,
            "model_used": model_used,
        }

    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"LLM API error: {e.response.status_code}",
            "test_cases": [],
            "model_used": LLM_MODEL,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"LLM call failed: {str(e)}",
            "test_cases": [],
            "model_used": LLM_MODEL,
        }
