"""
Data loader and deterministic check functions.
CRITICAL: These functions perform deterministic checks only - NO LLM calls.
"""
import json
import os
from typing import Optional, Dict, Any


def get_destination_data(destination: str, role: str) -> Optional[Dict[str, Any]]:
    """
    Load destination and role-specific data from JSON file.
    File naming convention: data/{destination}_{role}.json (lowercase, underscores)

    Args:
        destination: Destination country (e.g., "Germany", "UK")
        role: Target role (e.g., "Senior Backend Engineer", "Product Manager")

    Returns:
        Dictionary with destination data or None if file not found
    """
    # Normalize to lowercase and replace spaces with underscores
    destination_normalized = destination.lower().replace(' ', '_')
    role_normalized = role.lower().replace(' ', '_')

    # Construct file path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', f'{destination_normalized}_{role_normalized}.json')

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def check_missing_data(destination: str, role: str) -> Optional[Dict[str, Any]]:
    """
    Check if destination and role data exists.
    This is a DETERMINISTIC check - no LLM involved.

    Args:
        destination: Destination country
        role: Target role

    Returns:
        Structured error dict if data is missing, None if data exists
    """
    data = get_destination_data(destination, role)

    if data is None:
        return {
            'error': 'missing_data',
            'message': f'No data available for {role} in {destination}',
            'destination': destination,
            'role': role,
            'available_destinations': _get_available_destinations()
        }

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
