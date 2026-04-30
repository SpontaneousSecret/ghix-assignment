"""
Relocation plans API endpoints.
All endpoints require JWT authentication.
"""
from flask import Blueprint, request, jsonify, g
from app.auth import require_auth
from app.data_loader import (
    check_visa_minimum_timeline,
    check_timeline_conflict,
    check_salary_shortfall,
    get_destination_data_or_generic
)
from app.llm import generate_narrative
from app.database import (
    create_relocation_plan,
    get_user_relocation_plans,
    get_relocation_plan_by_id
)

plans_bp = Blueprint('plans', __name__)


@plans_bp.route('/generate', methods=['POST'])
@require_auth
def generate_plan():
    """
    Generate a relocation plan.
    CRITICAL FLOW:
    1. check_missing_data → if hit, return error immediately (NO LLM call)
    2. load destination JSON
    3. run timeline + salary checks → collect warnings[]
    4. call llm.py with deterministic fields
    5. save to DB
    6. return response with data_confidence

    Request body:
        {
            "origin": "India",
            "destination": "Germany",
            "target_role": "Senior Backend Engineer",
            "salary_expectation": 45000,
            "currency": "EUR",
            "timeline_months": 12,
            "work_auth_constraint": "Need visa sponsorship"
        }

    Returns:
        201: Plan generated successfully
        400: Validation error
        404: Missing destination data (no LLM call made)
    """
    user_id = g.user_id
    data = request.get_json()

    # Validate input
    if not data:
        return jsonify({
            'error': 'invalid_request',
            'message': 'Request body is required'
        }), 400

    origin = data.get('origin', '').strip()
    destination = data.get('destination', '').strip()
    target_role = data.get('target_role', '').strip()
    salary_expectation = data.get('salary_expectation')
    currency = data.get('currency', 'USD').strip()
    timeline_months = data.get('timeline_months')
    work_auth_constraint = data.get('work_auth_constraint', '').strip()

    # Validate required fields
    errors = []
    if not origin:
        errors.append('origin is required')
    if not destination:
        errors.append('destination is required')
    if not target_role:
        errors.append('target_role is required')
    if salary_expectation is None:
        errors.append('salary_expectation is required')
    if timeline_months is None:
        errors.append('timeline_months is required')

    if errors:
        return jsonify({
            'error': 'validation_error',
            'message': 'Validation failed',
            'details': errors
        }), 400

    # Validate types
    try:
        salary_expectation = float(salary_expectation)
        timeline_months = int(timeline_months)
    except (ValueError, TypeError):
        return jsonify({
            'error': 'validation_error',
            'message': 'salary_expectation must be a number and timeline_months must be an integer'
        }), 400

    # STEP 1: Load destination data (generic fallback if no JSON file exists)
    destination_data, is_generic = get_destination_data_or_generic(destination, target_role)

    # STEP 2: Run deterministic checks and collect warnings
    warnings = []

    # Always check: visa processing takes at least 6 months globally
    visa_min_warning = check_visa_minimum_timeline(timeline_months)
    if visa_min_warning:
        warnings.append(visa_min_warning)

    # If we have specific route data, also check route-specific timeline minimum
    route_min_months = destination_data.get('timeline', {}).get('min_months', 0)
    if not is_generic:
        timeline_warning = check_timeline_conflict(timeline_months, route_min_months)
        if timeline_warning and not visa_min_warning:
            warnings.append(timeline_warning)

    # Check salary shortfall (only when specific visa data exists)
    visa_threshold = destination_data.get('visa_requirements', {}).get('min_salary_threshold', 0)
    visa_currency = destination_data.get('visa_requirements', {}).get('currency', currency)

    if visa_threshold and currency.upper() == visa_currency.upper():
        salary_warning = check_salary_shortfall(salary_expectation, visa_threshold, currency)
        if salary_warning:
            warnings.append(salary_warning)

    # Build data confidence
    has_salary_data = bool(destination_data.get('salary_data'))
    has_visa_data = bool(destination_data.get('visa_requirements'))
    has_timeline_data = not is_generic
    data_confidence = {
        'salary_data_available': has_salary_data,
        'timeline_data_available': has_timeline_data,
        'visa_data_available': has_visa_data,
        'overall_confidence': 'low' if is_generic else ('medium' if warnings else 'high')
    }

    # STEP 4: Call LLM for narrative generation (ONLY after deterministic checks)
    narrative = generate_narrative(
        origin=origin,
        destination=destination,
        target_role=target_role,
        salary_expectation=salary_expectation,
        currency=currency,
        timeline_months=timeline_months,
        work_auth_constraint=work_auth_constraint,
        destination_data=destination_data,
        warnings=warnings
    )

    # Build plan structure
    plan_data = {
        'eligibility': {
            'eligible': True,
            'visa_type': destination_data.get('visa_requirements', {}).get('type', 'Unknown'),
            'sponsorship_required': destination_data.get('visa_requirements', {}).get('sponsorship_available', True),
            'min_salary_threshold': visa_threshold,
            'threshold_currency': visa_currency
        },
        'timeline': {
            'user_timeline_months': timeline_months,
            'typical_timeline_months': destination_data.get('timeline', {}).get('typical_months', 0),
            'min_timeline_months': route_min_months,
            'breakdown': destination_data.get('timeline', {}).get('breakdown', {})
        },
        'salary_analysis': {
            'user_expectation': salary_expectation,
            'currency': currency,
            'market_range': {
                'min': destination_data.get('salary_data', {}).get('min', 0),
                'median': destination_data.get('salary_data', {}).get('median', 0),
                'max': destination_data.get('salary_data', {}).get('max', 0),
                'currency': destination_data.get('salary_data', {}).get('currency', currency)
            }
        },
        'narrative': narrative,
        'warnings': warnings
    }

    # STEP 5: Save to database
    relocation_plan, db_error = create_relocation_plan(
        user_id=user_id,
        origin=origin,
        destination=destination,
        target_role=target_role,
        salary_expectation=salary_expectation,
        currency=currency,
        timeline_months=timeline_months,
        work_auth_constraint=work_auth_constraint,
        plan_json=plan_data,
        data_confidence_json=data_confidence
    )

    if db_error:
        return jsonify({
            'error': 'database_error',
            'message': db_error
        }), 500

    # STEP 6: Return response with data_confidence
    return jsonify({
        'message': 'Relocation plan generated successfully',
        'plan': relocation_plan.to_dict(),
        'data_confidence': data_confidence
    }), 201


@plans_bp.route('', methods=['GET'])
@require_auth
def list_plans():
    """
    List all relocation plans for the authenticated user.

    Query parameters:
        - limit (optional): Maximum number of plans to return
        - offset (optional): Number of plans to skip (for pagination)
        - destination (optional): Filter by destination country

    Returns:
        200: List of plans
    """
    user_id = g.user_id

    # Get query parameters
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    destination = request.args.get('destination', type=str)

    # Get plans from database
    plans = get_user_relocation_plans(
        user_id=user_id,
        limit=limit,
        offset=offset,
        destination=destination
    )

    # Convert to list of dicts (summary without full plan)
    plans_list = [plan.to_summary_dict() for plan in plans]

    return jsonify({
        'plans': plans_list,
        'count': len(plans_list),
        'offset': offset,
        'limit': limit
    }), 200


@plans_bp.route('/<int:plan_id>', methods=['GET'])
@require_auth
def get_plan(plan_id):
    """
    Get a single relocation plan by ID.

    Args:
        plan_id: Plan ID from URL

    Returns:
        200: Plan details
        404: Plan not found
        403: Unauthorized (plan belongs to different user)
    """
    user_id = g.user_id

    # Get plan from database
    plan = get_relocation_plan_by_id(plan_id)

    if not plan:
        return jsonify({
            'error': 'not_found',
            'message': 'Plan not found'
        }), 404

    # Check ownership
    if plan.user_id != user_id:
        return jsonify({
            'error': 'forbidden',
            'message': 'You do not have access to this plan'
        }), 403

    # Return full plan with data_confidence
    plan_dict = plan.to_dict(include_plan=True)

    return jsonify({
        'plan': plan_dict
    }), 200
