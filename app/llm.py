"""
LLM integration for narrative generation.
CRITICAL: LLM is ONLY called for narrative generation, NEVER for deterministic checks.
Uses Groq API via REST (not SDK) with llama-3.3-70b-versatile.
"""
import os
import requests
from typing import Dict, Any, List

GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL = 'llama-3.3-70b-versatile'


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
    Generate a narrative summary using Groq API.
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
    api_key = os.environ.get('GROQ_API_KEY')

    if not api_key:
        return _generate_fallback_narrative(
            origin, destination, target_role, salary_expectation,
            currency, timeline_months, destination_data, warnings
        )

    prompt = _build_prompt(
        origin, destination, target_role, salary_expectation,
        currency, timeline_months, work_auth_constraint,
        destination_data, warnings
    )

    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        payload = {
            'model': GROQ_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 500,
        }

        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=10)
        print(f"LLM: Groq status={response.status_code}")
        response.raise_for_status()

        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            narrative = result['choices'][0]['message']['content'].strip()
            print(f"LLM: Groq returned {len(narrative)} chars")
            return narrative

        print(f"LLM: unexpected response shape: {list(result.keys())}")
        return _generate_fallback_narrative(
            origin, destination, target_role, salary_expectation,
            currency, timeline_months, destination_data, warnings
        )

    except Exception as e:
        print(f"LLM API error: {type(e).__name__}: {str(e)}")
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
    visa_info = destination_data.get('visa_requirements', {})
    salary_data = destination_data.get('salary_data', {})
    timeline_data = destination_data.get('timeline', {})

    visa_currency = visa_info.get('currency', currency)
    salary_currency = salary_data.get('currency', currency)
    visa_threshold = visa_info.get('min_salary_threshold', 0)
    salary_median = salary_data.get('median', 0)
    salary_min = salary_data.get('min', 0)
    salary_max = salary_data.get('max', 0)
    typical_months = timeline_data.get('typical_months', 0)
    processing_months = visa_info.get('processing_time_months', 0)

    issues_block = (
        "The system has flagged the following issues with this plan:\n" +
        "\n".join(f"- {w}" for w in warnings)
    ) if warnings else "The system found no blockers with this plan."

    prompt = f"""You are an experienced international career relocation advisor. A candidate has submitted a relocation plan and you need to give them honest, personalised advice on whether it is realistic and what they should adjust.

Here is everything you know about their plan:

The candidate is moving from {origin} to {destination} for a {target_role} role. They expect a salary of {currency} {salary_expectation:,.0f} and want to complete the move within {timeline_months} months. Their work authorisation situation: {work_auth_constraint if work_auth_constraint else 'not specified'}.

The relevant visa is the {visa_info.get('type', 'local work visa')}. It requires a minimum salary of {visa_currency} {visa_threshold:,.0f} and employer sponsorship {"is available" if visa_info.get('sponsorship_available') else "is not commonly available"} in this market. Visa processing alone takes {processing_months} months.

The current market for {target_role} roles in {destination} pays between {salary_currency} {salary_min:,.0f} and {salary_currency} {salary_max:,.0f}, with a median of {salary_currency} {salary_median:,.0f}. The typical end-to-end relocation timeline for this route is {typical_months} months.

{issues_block}

Write a 3–4 paragraph advisory response directly to the candidate (use "you"/"your"). Do not repeat back raw numbers they already know — instead interpret what the numbers mean for their situation. Be direct about what needs to change if anything does. If the plan looks solid, say so and explain why. Close with the single most important next step they should take right now. Keep the tone professional but human — like advice from a senior colleague who has done this before."""

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
