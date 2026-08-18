"""
Service: Role Classifier
======================
Uses a small, fast LLM to map custom user-entered job titles
to the nearest predefined role in our system.
"""

import json
import logging
import re
from typing import Optional

from google import genai
from google.genai import types as genai_types

from app.config import settings
from app.services.question_generation import FALLBACK_MODELS

log = logging.getLogger(__name__)


def classify_custom_role(custom_role: str, predefined_roles: list[str]) -> Optional[str]:
    """
    Classifies a custom job title into the closest matching predefined role.
    
    Args:
        custom_role: The free-text string the user entered (e.g., "Fullstack React Node dev")
        predefined_roles: List of valid roles in our system (e.g., ["Backend Engineer", "Frontend Engineer", "Data Scientist"])
        
    Returns:
        The exact string of the matched predefined role, or None if no match is found.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        log.warning("GEMINI_API_KEY not set — role classification unavailable.")
        return None

    if not predefined_roles:
        return None

    roles_str = ", ".join(f'"{r}"' for r in predefined_roles)

    prompt = f"""You are a technical recruiting assistant. Map a user's custom job title to the closest predefined role.

Predefined Roles Available: [{roles_str}]

User's Custom Role: "{custom_role}"

Instructions:
1. Choose the SINGLE most appropriate predefined role from the list above.
2. If it's a completely unrelated or garbage title, return null for the mapped_role.
3. Return valid JSON only.

Format:
{{
    "mapped_role": "String from the predefined list, or null"
}}
"""

    client = genai.Client(api_key=api_key)

    # Use the fastest/cheapest models first
    for model_name in FALLBACK_MODELS:
        for _attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,  # Keep it deterministic
                    ),
                )
                
                if response.text:
                    raw = re.sub(r"^```json\s*|\s*```$", "", response.text.strip())
                    data = json.loads(raw)
                    
                    mapped_role = data.get("mapped_role")
                    if mapped_role in predefined_roles:
                        return mapped_role
                    return None  # It wasn't found or was explicitly mapped to null

            except Exception as exc:  # noqa: BLE001
                log.debug("Role classification failed on model %s: %s", model_name, exc)
                continue

    log.warning("All LLM attempts failed for classifying role: %s", custom_role)
    return None
