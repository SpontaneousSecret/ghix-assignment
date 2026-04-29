"""
LLM integration for narrative generation.
CRITICAL: LLM is ONLY called for narrative generation, NEVER for deterministic checks.
Uses Gemini Flash free tier via REST API (not SDK).
"""
import os
import requests
from typing import Dict, Any, List


def generate_narrative(
    origin: str,
    destination: str,
    target_role: str,
    salary_expectation: float,
    currency: str,
    timeline_months: int,
    work_auth_constraint: str,
    destination_data: Dict[str, Any],
    warnings: List[str]
) -> str:
    """
    Generate a narrative summary using Gemini Flash API.
    This is ONLY called AFTER all deterministic checks have passed.

    Args:
        origin: Origin country
        destination: Destination country
        target_role: Target role
        salary_expectation: Expected salary
        currency: Currency code
        timeline_months: Desired timeline in months
        work_auth_constraint: Work authorization constraints
        destination_data: Pre-loaded destination data (from JSON)
        warnings: List of warning strings from deterministic checks

    Returns:
        Generated narrative string
    """
    api_key = os.environ.get('GEMINI_API_KEY')

    # If no API key, return a simple fallback narrative
    if not api_key:
        return _generate_fallback_narrative(
            origin, destination, target_role, salary_expectation,
            currency, timeline_months, destination_data, warnings
        )

    # Construct prompt with all deterministic information
    prompt = _build_prompt(
        origin, destination, target_role, salary_expectation,
        currency, timeline_months, work_auth_constraint,
        destination_data, warnings
    )

    try:
        # Call Gemini Flash API via REST
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'

        payload = {
            'contents': [{
                'parts': [{
                    'text': prompt
                }]
            }],
            'generationConfig': {
                'temperature': 0.7,
                'maxOutputTokens': 500,
            }
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()

        # Extract narrative from response
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                if len(parts) > 0 and 'text' in parts[0]:
                    return parts[0]['text'].strip()

        # Fallback if response format unexpected
        return _generate_fallback_narrative(
            origin, destination, target_role, salary_expectation,
            currency, timeline_months, destination_data, warnings
        )

    except Exception as e:
        # On any error, return fallback narrative
        print(f"LLM API error: {str(e)}")
        return _generate_fallback_narrative(
            origin, destination, target_role, salary_expectation,
            currency, timeline_months, destination_data, warnings
        )


def _build_prompt(
    origin: str,
    destination: str,
    target_role: str,
    salary_expectation: float,
    currency: str,
    timeline_months: int,
    work_auth_constraint: str,
    destination_data: Dict[str, Any],
    warnings: List[str]
) -> str:
    """
    Build prompt for LLM with all deterministic information.

    Returns:
        Formatted prompt string
    """
    visa_info = destination_data.get('visa_requirements', {})
    salary_data = destination_data.get('salary_data', {})
    timeline_data = destination_data.get('timeline', {})

    prompt = f"""You are a career relocation advisor. Generate a concise, professional narrative (3-4 paragraphs) for a relocation plan based on the following VERIFIED information:

ORIGIN: {origin}
DESTINATION: {destination}
TARGET ROLE: {target_role}
SALARY EXPECTATION: {currency} {salary_expectation:,.2f}
TIMELINE: {timeline_months} months
WORK AUTHORIZATION: {work_auth_constraint}

VISA INFORMATION:
- Type: {visa_info.get('type', 'N/A')}
- Minimum Salary Threshold: {visa_info.get('currency', currency)} {visa_info.get('min_salary_threshold', 0):,.2f}
- Sponsorship Available: {visa_info.get('sponsorship_available', False)}
- Processing Time: {visa_info.get('processing_time_months', 0)} months

MARKET DATA:
- Salary Range: {salary_data.get('currency', currency)} {salary_data.get('min', 0):,.0f} - {salary_data.get('max', 0):,.0f}
- Median: {salary_data.get('currency', currency)} {salary_data.get('median', 0):,.0f}
- Typical Timeline: {timeline_data.get('typical_months', 0)} months

WARNINGS:
{chr(10).join(f'- {w}' for w in warnings) if warnings else '- None'}

Generate a narrative that:
1. Summarizes the relocation opportunity
2. Highlights key requirements and timeline
3. Addresses any warnings if present
4. Provides encouraging but realistic guidance

Keep it concise, professional, and actionable."""

    return prompt


def _generate_fallback_narrative(
    origin: str,
    destination: str,
    target_role: str,
    salary_expectation: float,
    currency: str,
    timeline_months: int,
    destination_data: Dict[str, Any],
    warnings: List[str]
) -> str:
    """
    Generate a simple fallback narrative when LLM API is unavailable.

    Returns:
        Simple narrative string
    """
    visa_info = destination_data.get('visa_requirements', {})
    salary_data = destination_data.get('salary_data', {})

    narrative_parts = []

    # Opening
    narrative_parts.append(
        f"Your relocation plan from {origin} to {destination} as a {target_role} "
        f"is feasible with your expected salary of {currency} {salary_expectation:,.2f} "
        f"and timeline of {timeline_months} months."
    )

    # Visa information
    if visa_info:
        narrative_parts.append(
            f"You will need to apply for a {visa_info.get('type', 'work visa')}, "
            f"which requires a minimum salary of {visa_info.get('currency', currency)} "
            f"{visa_info.get('min_salary_threshold', 0):,.2f}. "
            f"{'Sponsorship is available from employers.' if visa_info.get('sponsorship_available') else 'Sponsorship requirements apply.'}"
        )

    # Salary context
    if salary_data:
        narrative_parts.append(
            f"The typical salary range for this role is {salary_data.get('currency', currency)} "
            f"{salary_data.get('min', 0):,.0f} to {salary_data.get('max', 0):,.0f}, "
            f"with a median of {salary_data.get('currency', currency)} {salary_data.get('median', 0):,.0f}."
        )

    # Warnings
    if warnings:
        narrative_parts.append(
            "Please note the following considerations: " +
            " ".join(warnings)
        )
    else:
        narrative_parts.append(
            "Your plan aligns well with the typical requirements for this destination and role."
        )

    return " ".join(narrative_parts)
