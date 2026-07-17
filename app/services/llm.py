import os
import re
import json
import hashlib
import httpx
from typing import List, Dict, Any, Optional


LLM_API_URL = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
DEMO_MODE = os.getenv("DEMO_MODE", "auto")


def _generate_demo_test_cases(
    section_title: str, section_number: str, content: str
) -> List[Dict]:
    content_lower = content.lower()
    keywords = set()
    keyword_map = {
        "overpressure": "safety",
        "alarm": "safety",
        "error": "error_handling",
        "battery": "power",
        "bluetooth": "connectivity",
        "deflat": "safety",
        "inflate": "measurement",
        "cuff": "hardware",
        "measurement": "measurement",
        "calibrat": "accuracy",
        "display": "ui",
        "button": "ui",
        "pressure": "measurement",
        "pulse": "measurement",
        "sensor": "hardware",
        "export": "data",
        "data": "data",
        "clean": "maintenance",
        "maintenance": "maintenance",
        "regulatory": "compliance",
        "shutoff": "power",
        "auto": "automation",
        "stored": "data",
        "profile": "data",
    }
    for kw, cat in keyword_map.items():
        if kw in content_lower:
            keywords.add(cat)

    if not keywords:
        keywords = {"measurement", "safety", "ui"}

    priority = "critical" if "safety" in keywords else "high"

    tc_id_salt = f"{section_number}:{section_title}"
    seed = int(hashlib.md5(tc_id_salt.encode()).hexdigest()[:8], 16)

    def _make_tc(idx: int, kw: str) -> Dict:
        tc_seed = seed + idx
        tc_hash = hashlib.md5(str(tc_seed).encode()).hexdigest()[:4]
        tc_id = f"TC-{tc_hash.upper()}"

        templates = {
            "safety": {
                "title": f"Verify {section_title} safety behavior",
                "description": f"Ensure the device handles {section_title.lower()} safely per specification",
                "preconditions": "Device powered on, cuff connected, firmware v1.0",
                "steps": [
                    "Power on the device and wait for ready state",
                    "Trigger the safety condition described in this section",
                    f"Verify device responds correctly to {section_title.lower()}",
                    "Check that no unsafe state persists",
                    "Record all device outputs and behaviors",
                ],
                "expected_result": "Device enters safe state within specified time; no harm to patient",
            },
            "measurement": {
                "title": f"Validate {section_title} accuracy",
                "description": f"Verify measurement accuracy for {section_title.lower()}",
                "preconditions": "Calibrated reference available, device at room temperature",
                "steps": [
                    "Connect calibrated reference cuff",
                    "Perform measurement as described in procedure",
                    "Compare device reading with reference",
                    "Repeat 3 times and record deviations",
                ],
                "expected_result": "Reading within ±3 mmHg of reference for systolic/diastolic",
            },
            "error_handling": {
                "title": f"Test {section_title} error codes",
                "description": f"Verify correct error detection and display for {section_title.lower()}",
                "preconditions": "Device powered on, test conditions prepared",
                "steps": [
                    "Simulate the error condition",
                    "Observe device display and behavior",
                    "Verify error code is displayed correctly",
                    "Confirm device takes corrective action",
                    "Reset device and verify recovery",
                ],
                "expected_result": "Correct error code displayed; device takes specified corrective action",
            },
            "power": {
                "title": f"Test {section_title} power management",
                "description": f"Verify power-related behavior for {section_title.lower()}",
                "preconditions": "Device with fresh batteries, external power disconnected",
                "steps": [
                    "Monitor battery level indicator",
                    f"Trigger {section_title.lower()} condition",
                    "Verify device handles low power correctly",
                    "Check for data preservation during power events",
                ],
                "expected_result": "Device warns user before shutdown; measurement data preserved",
            },
            "connectivity": {
                "title": f"Test {section_title} connectivity",
                "description": f"Verify wireless/Bluetooth behavior for {section_title.lower()}",
                "preconditions": "Paired smartphone with companion app, Bluetooth enabled",
                "steps": [
                    "Enable Bluetooth on device and smartphone",
                    f"Perform {section_title.lower()} operation",
                    "Verify data transfer completes successfully",
                    "Check for connection timeout handling",
                ],
                "expected_result": "Data transmitted within 10 seconds; connection errors handled gracefully",
            },
            "hardware": {
                "title": f"Test {section_title} hardware interaction",
                "description": f"Verify hardware components for {section_title.lower()}",
                "preconditions": "Device assembled, all components present",
                "steps": [
                    "Inspect physical components for damage",
                    f"Operate device as described for {section_title.lower()}",
                    "Check for physical feedback (LEDs, sounds)",
                    "Verify component durability under normal use",
                ],
                "expected_result": "All hardware components function within specification",
            },
            "ui": {
                "title": f"Test {section_title} user interface",
                "description": f"Verify display and interaction for {section_title.lower()}",
                "preconditions": "Device powered on, screen visible",
                "steps": [
                    "Navigate to relevant screen",
                    f"Perform {section_title.lower()} interaction",
                    "Verify display updates correctly",
                    "Check for screen timeout and responsiveness",
                ],
                "expected_result": "Display shows correct values; UI responds within 500ms",
            },
            "data": {
                "title": f"Verify {section_title} data handling",
                "description": f"Check data storage/transfer for {section_title.lower()}",
                "preconditions": "Device with stored measurements, export medium available",
                "steps": [
                    "Create test data through measurement",
                    f"Perform {section_title.lower()} operation",
                    "Verify data integrity after operation",
                    "Check data format and readability",
                ],
                "expected_result": "Data preserved accurately; format matches specification",
            },
            "automation": {
                "title": f"Test {section_title} automatic behavior",
                "description": f"Verify automated functions for {section_title.lower()}",
                "preconditions": "Device in idle state, settings at default",
                "steps": [
                    "Leave device in specified state",
                    f"Wait for {section_title.lower()} to activate",
                    "Verify timing and behavior",
                    "Check device recovers to normal operation",
                ],
                "expected_result": "Automation triggers at correct time; device recovers properly",
            },
            "accuracy": {
                "title": f"Validate {section_title} precision",
                "description": f"Verify accuracy and calibration for {section_title.lower()}",
                "preconditions": "Reference standard available, device calibrated",
                "steps": [
                    "Perform baseline calibration check",
                    f"Execute {section_title.lower()} procedure",
                    "Compare against reference standard",
                    "Document accuracy metrics",
                ],
                "expected_result": "Accuracy within ±3 mmHg; calibration stable over 100 cycles",
            },
            "maintenance": {
                "title": f"Test {section_title} procedures",
                "description": f"Verify maintenance/cleaning for {section_title.lower()}",
                "preconditions": "Device used, cleaning supplies available",
                "steps": [
                    "Follow cleaning procedure as documented",
                    "Verify all surfaces cleaned properly",
                    "Check device function after maintenance",
                    "Document maintenance interval compliance",
                ],
                "expected_result": "Device clean; no damage from maintenance; function intact",
            },
            "compliance": {
                "title": f"Verify {section_title} compliance",
                "description": f"Check regulatory compliance for {section_title.lower()}",
                "preconditions": "Regulatory documents available",
                "steps": [
                    "Review applicable standards",
                    f"Verify {section_title.lower()} meets requirements",
                    "Document compliance evidence",
                    "Flag any non-compliance issues",
                ],
                "expected_result": "Device meets all applicable regulatory requirements",
            },
        }

        kw_list = sorted(keywords)
        primary_kw = kw_list[idx % len(kw_list)]
        t = templates.get(primary_kw, templates["measurement"])

        return {
            "id": tc_id,
            "title": t["title"],
            "description": t["description"],
            "preconditions": t["preconditions"],
            "steps": t["steps"],
            "expected_result": t["expected_result"],
            "priority": priority if idx == 0 else "high" if idx < 3 else "medium",
            "traced_to_section": section_number,
        }

    num_cases = 3 + (seed % 3)
    return [_make_tc(i, kw) for i, kw in enumerate(sorted(keywords)[:num_cases])]

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
    use_demo = (
        DEMO_MODE == "on"
        or (DEMO_MODE == "auto" and not LLM_API_KEY)
    )

    if use_demo:
        test_cases = _generate_demo_test_cases(
            section_title, section_number, content
        )
        return {
            "success": True,
            "test_cases": test_cases,
            "model_used": "demo-rule-based",
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
