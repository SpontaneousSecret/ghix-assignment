"""
Data loader and deterministic check functions.
CRITICAL: These functions perform deterministic checks only - NO LLM calls.
"""
import json
import os
from typing import Optional, Dict, Any

VISA_PROCESSING_MIN_MONTHS = 6


def get_destination_data(destination: str, role: str) -> Optional[Dict[str, Any]]:
    """
    Load destination and role-specific data from JSON file.
    Returns None if no file exists — callers should use get_destination_data_or_generic().
    """
    destination_normalized = destination.lower().replace(' ', '_')
    role_normalized = role.lower().replace(' ', '_')

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', f'{destination_normalized}_{role_normalized}.json')

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_destination_data_or_generic(destination: str, role: str) -> tuple[Dict[str, Any], bool]:
    """
    Load destination data from JSON, or return generic defaults if no file exists.

    Returns:
        (data dict, is_generic: bool) — is_generic=True means no specific data was found
    """
    data = get_destination_data(destination, role)
    if data is not None:
        return data, False

    generic = {
        'destination': destination,
        'role': role,
        'visa_requirements': {},
        'timeline': {
            'min_months': VISA_PROCESSING_MIN_MONTHS,
            'typical_months': 12,
            'max_months': 24,
            'breakdown': {}
        },
        'salary_data': {},
        'cost_of_living': {}
    }
    return generic, True


def check_visa_minimum_timeline(user_months: int) -> Optional[str]:
    """
    Always-on check: visa processing takes at minimum 6 months globally.
    Returns a warning if the user's timeline is below that.
    """
    if user_months < VISA_PROCESSING_MIN_MONTHS:
        return (
            f'Timeline too short: Visa processing alone typically takes a minimum of '
            f'{VISA_PROCESSING_MIN_MONTHS} months in any country. Your requested timeline of '
            f'{user_months} month(s) is likely not achievable.'
        )
    return None


def check_timeline_conflict(user_months: int, route_min_months: int) -> Optional[str]:
    """
    Check if user's timeline is shorter than the minimum required.
    This is a DETERMINISTIC check - no LLM involved.

    Args:
        user_months: User's desired timeline in months
        route_min_months: Minimum months required for this route

    Returns:
        Warning string if there's a conflict, None otherwise
    """
    if user_months < route_min_months:
        gap = route_min_months - user_months
        return (
            f'Timeline conflict: Your desired timeline of {user_months} months '
            f'is {gap} month(s) shorter than the typical minimum of {route_min_months} months. '
            f'This route typically requires at least {route_min_months} months.'
        )

    return None


def check_salary_shortfall(
    user_salary: float,
    threshold: float,
    currency: str
) -> Optional[str]:
    """
    Check if user's salary expectation is below the visa threshold.
    This is a DETERMINISTIC check - no LLM involved.

    Args:
        user_salary: User's salary expectation
        threshold: Minimum salary threshold for visa
        currency: Currency code (e.g., 'EUR', 'GBP')

    Returns:
        Warning string with exact gap if shortfall exists, None otherwise
    """
    if user_salary < threshold:
        gap = threshold - user_salary
        return (
            f'Salary shortfall: Your expected salary of {currency} {user_salary:,.2f} '
            f'is {currency} {gap:,.2f} below the minimum visa threshold of '
            f'{currency} {threshold:,.2f}. You may not be eligible for this visa route.'
        )

    return None


def _get_available_destinations() -> list:
    """
    Get list of available destination+role combinations.
    Helper function for error messages.

    Returns:
        List of available destination and role combinations
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    available = []

    try:
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                # Parse filename: destination_role.json
                name = filename[:-5]  # Remove .json
                parts = name.split('_')

                # Reconstruct with proper capitalization
                # This is a simple approach - assumes destination and role parts
                if len(parts) >= 2:
                    available.append(filename[:-5].replace('_', ' ').title())

        return available
    except Exception:
        return []
