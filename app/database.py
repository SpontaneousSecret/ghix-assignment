from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from sqlalchemy import desc, and_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models import db, User, RelocationPlan
import bcrypt


# ==================== USER OPERATIONS ====================

def create_user(email: str, password: str) -> tuple[Optional[User], Optional[str]]:
    """
    Create a new user with hashed password.

    Args:
        email: User email address (must be unique)
        password: Plain text password (will be hashed)

    Returns:
        Tuple of (User object, error_message)
        If successful: (User, None)
        If failed: (None, error_message)
    """
    try:
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return None, "User with this email already exists"

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create user
        user = User(
            email=email,
            password_hash=password_hash
        )

        db.session.add(user)
        db.session.commit()

        return user, None

    except IntegrityError as e:
        db.session.rollback()
        return None, "User with this email already exists"
    except Exception as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"


def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Retrieve user by ID.

    Args:
        user_id: User ID

    Returns:
        User object or None if not found
    """
    return db.session.get(User, user_id)


def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieve user by email address.

    Args:
        email: User email address

    Returns:
        User object or None if not found
    """
    return db.session.query(User).filter_by(email=email).first()


def verify_user_password(user: User, password: str) -> bool:
    """
    Verify user password against stored hash.

    Args:
        user: User object
        password: Plain text password to verify

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))


def update_user_password(user_id: int, new_password: str) -> tuple[bool, Optional[str]]:
    """
    Update user password.

    Args:
        user_id: User ID
        new_password: New plain text password (will be hashed)

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False, "User not found"

        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.password_hash = password_hash
        user.updated_at = datetime.utcnow()

        db.session.commit()
        return True, None

    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"


def delete_user(user_id: int) -> tuple[bool, Optional[str]]:
    """
    Delete user and all associated relocation plans (cascade).

    Args:
        user_id: User ID

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False, "User not found"

        db.session.delete(user)
        db.session.commit()
        return True, None

    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"


# ==================== RELOCATION PLAN OPERATIONS ====================

def create_relocation_plan(
    user_id: int,
    origin: str,
    destination: str,
    target_role: str,
    salary_expectation: float,
    currency: str,
    timeline_months: int,
    work_auth_constraint: Optional[str],
    plan_json: Dict[str, Any],
    data_confidence_json: Dict[str, Any]
) -> tuple[Optional[RelocationPlan], Optional[str]]:
    """
    Create a new relocation plan (always creates a new row for history tracking).

    Args:
        user_id: User ID (foreign key)
        origin: Origin country
        destination: Destination country
        target_role: Target job role
        salary_expectation: Expected salary
        currency: Currency code (e.g., 'USD', 'EUR')
        timeline_months: Expected timeline in months
        work_auth_constraint: Work authorization constraint (optional)
        plan_json: Full generated plan as dictionary
        data_confidence_json: Data confidence flags as dictionary

    Returns:
        Tuple of (RelocationPlan object, error_message)
        If successful: (RelocationPlan, None)
        If failed: (None, error_message)
    """
    try:
        # Verify user exists
        user = get_user_by_id(user_id)
        if not user:
            return None, "User not found"

        # Convert dictionaries to JSON strings
        plan_json_str = json.dumps(plan_json)
        data_confidence_json_str = json.dumps(data_confidence_json)

        # Create relocation plan
        plan = RelocationPlan(
            user_id=user_id,
            origin=origin,
            destination=destination,
            target_role=target_role,
            salary_expectation=salary_expectation,
            currency=currency,
            timeline_months=timeline_months,
            work_auth_constraint=work_auth_constraint,
            plan_json=plan_json_str,
            data_confidence_json=data_confidence_json_str
        )

        db.session.add(plan)
        db.session.commit()

        return plan, None

    except Exception as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"


def get_relocation_plan_by_id(plan_id: int) -> Optional[RelocationPlan]:
    """
    Retrieve relocation plan by ID.

    Args:
        plan_id: RelocationPlan ID

    Returns:
        RelocationPlan object or None if not found
    """
    return db.session.get(RelocationPlan, plan_id)


def get_user_relocation_plans(
    user_id: int,
    limit: Optional[int] = None,
    offset: int = 0,
    destination: Optional[str] = None
) -> List[RelocationPlan]:
    """
    Retrieve all relocation plans for a user (ordered by most recent first).

    Args:
        user_id: User ID
        limit: Maximum number of plans to return (None for all)
        offset: Number of plans to skip (for pagination)
        destination: Filter by destination country (optional)

    Returns:
        List of RelocationPlan objects
    """
    query = db.session.query(RelocationPlan).filter_by(user_id=user_id)

    if destination:
        query = query.filter_by(destination=destination)

    query = query.order_by(desc(RelocationPlan.generated_at))

    if offset:
        query = query.offset(offset)

    if limit:
        query = query.limit(limit)

    return query.all()


def get_latest_relocation_plan(user_id: int, destination: Optional[str] = None) -> Optional[RelocationPlan]:
    """
    Get the most recent relocation plan for a user.

    Args:
        user_id: User ID
        destination: Filter by destination country (optional)

    Returns:
        Most recent RelocationPlan object or None
    """
    plans = get_user_relocation_plans(user_id=user_id, limit=1, destination=destination)
    return plans[0] if plans else None


def get_relocation_plan_history(
    user_id: int,
    origin: str,
    destination: str,
    target_role: str
) -> List[RelocationPlan]:
    """
    Get history of relocation plans for specific criteria.
    Useful for showing user's previous submissions with same parameters.

    Args:
        user_id: User ID
        origin: Origin country
        destination: Destination country
        target_role: Target job role

    Returns:
        List of RelocationPlan objects ordered by most recent first
    """
    return db.session.query(RelocationPlan).filter(
        and_(
            RelocationPlan.user_id == user_id,
            RelocationPlan.origin == origin,
            RelocationPlan.destination == destination,
            RelocationPlan.target_role == target_role
        )
    ).order_by(desc(RelocationPlan.generated_at)).all()


def delete_relocation_plan(plan_id: int, user_id: int) -> tuple[bool, Optional[str]]:
    """
    Delete a specific relocation plan (with user ownership verification).

    Args:
        plan_id: RelocationPlan ID
        user_id: User ID (for ownership verification)

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        plan = get_relocation_plan_by_id(plan_id)
        if not plan:
            return False, "Relocation plan not found"

        if plan.user_id != user_id:
            return False, "Unauthorized: Plan belongs to different user"

        db.session.delete(plan)
        db.session.commit()
        return True, None

    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"


def count_user_relocation_plans(user_id: int, destination: Optional[str] = None) -> int:
    """
    Count total relocation plans for a user.

    Args:
        user_id: User ID
        destination: Filter by destination country (optional)

    Returns:
        Total count of relocation plans
    """
    query = db.session.query(RelocationPlan).filter_by(user_id=user_id)

    if destination:
        query = query.filter_by(destination=destination)

    return query.count()


# ==================== DATABASE INITIALIZATION ====================

def init_db(app=None) -> None:
    """
    Initialize database tables.
    Should be called during application setup.

    Args:
        app: Flask application instance (optional, uses current app context if None)
    """
    if app:
        with app.app_context():
            db.create_all()
    else:
        db.create_all()


def drop_db(app=None) -> None:
    """
    Drop all database tables.
    WARNING: This deletes all data! Use only for testing or development.

    Args:
        app: Flask application instance (optional, uses current app context if None)
    """
    if app:
        with app.app_context():
            db.drop_all()
    else:
        db.drop_all()


def reset_db(app=None) -> None:
    """
    Drop and recreate all database tables.
    WARNING: This deletes all data! Use only for testing or development.

    Args:
        app: Flask application instance (optional, uses current app context if None)
    """
    drop_db(app)
    init_db(app)


# ==================== DATABASE HEALTH CHECK ====================

def check_db_connection() -> tuple[bool, Optional[str]]:
    """
    Check database connection health.

    Returns:
        Tuple of (is_healthy: bool, error_message: Optional[str])
    """
    try:
        # Simple query to test connection
        db.session.execute(text('SELECT 1'))
        return True, None
    except Exception as e:
        return False, f"Database connection error: {str(e)}"
