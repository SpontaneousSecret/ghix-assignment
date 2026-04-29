"""
Authentication module with JWT token management.
Provides register/login endpoints and authentication decorator.
"""
from flask import Blueprint, request, jsonify, g, current_app
from functools import wraps
import jwt
from datetime import datetime, timedelta
from app.database import create_user, get_user_by_email, verify_user_password, get_user_by_id

auth_bp = Blueprint('auth', __name__)


# ==================== JWT HELPERS ====================

def encode_jwt(user_id: int) -> str:
    """
    Encode user ID into a JWT token.

    Args:
        user_id: User ID to encode

    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'iat': datetime.utcnow()
    }

    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config['JWT_ALGORITHM']
    )

    return token


def decode_jwt(token: str) -> dict:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dictionary

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    payload = jwt.decode(
        token,
        current_app.config['JWT_SECRET_KEY'],
        algorithms=[current_app.config['JWT_ALGORITHM']]
    )

    return payload


# ==================== AUTHENTICATION DECORATOR ====================

def require_auth(f):
    """
    Decorator to protect routes with JWT authentication.
    Puts user_id on flask.g for use in the route handler.

    Usage:
        @auth_bp.route('/protected')
        @require_auth
        def protected_route():
            user_id = g.user_id
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'error': 'missing_token',
                'message': 'Authorization header is required'
            }), 401

        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'error': 'invalid_header',
                'message': 'Authorization header must be in format: Bearer <token>'
            }), 401

        token = parts[1]

        try:
            # Decode and verify token
            payload = decode_jwt(token)
            user_id = payload.get('user_id')

            if not user_id:
                return jsonify({
                    'error': 'invalid_token',
                    'message': 'Token payload is invalid'
                }), 401

            # Verify user still exists
            user = get_user_by_id(user_id)
            if not user:
                return jsonify({
                    'error': 'user_not_found',
                    'message': 'User no longer exists'
                }), 401

            # Put user_id on flask.g for use in route handler
            g.user_id = user_id

            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({
                'error': 'token_expired',
                'message': 'Token has expired'
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                'error': 'invalid_token',
                'message': 'Token is invalid'
            }), 401

    return decorated_function


# ==================== ENDPOINTS ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.

    Request body:
        {
            "email": "user@example.com",
            "password": "secure_password"
        }

    Returns:
        201: User created successfully with JWT token
        400: Validation error or user already exists
    """
    data = request.get_json()

    # Validate input
    if not data:
        return jsonify({
            'error': 'invalid_request',
            'message': 'Request body is required'
        }), 400

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email:
        return jsonify({
            'error': 'validation_error',
            'message': 'Email is required'
        }), 400

    if not password:
        return jsonify({
            'error': 'validation_error',
            'message': 'Password is required'
        }), 400

    if len(password) < 6:
        return jsonify({
            'error': 'validation_error',
            'message': 'Password must be at least 6 characters'
        }), 400

    # Basic email validation
    if '@' not in email or '.' not in email:
        return jsonify({
            'error': 'validation_error',
            'message': 'Invalid email format'
        }), 400

    # Create user
    user, error = create_user(email, password)

    if error:
        return jsonify({
            'error': 'registration_failed',
            'message': error
        }), 400

    # Generate JWT token
    token = encode_jwt(user.id)

    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'token': token,
        'token_type': 'Bearer',
        'expires_in_hours': 24
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login an existing user.

    Request body:
        {
            "email": "user@example.com",
            "password": "secure_password"
        }

    Returns:
        200: Login successful with JWT token
        401: Invalid credentials
        400: Validation error
    """
    data = request.get_json()

    # Validate input
    if not data:
        return jsonify({
            'error': 'invalid_request',
            'message': 'Request body is required'
        }), 400

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({
            'error': 'validation_error',
            'message': 'Email and password are required'
        }), 400

    # Get user by email
    user = get_user_by_email(email)

    if not user:
        return jsonify({
            'error': 'invalid_credentials',
            'message': 'Invalid email or password'
        }), 401

    # Verify password
    if not verify_user_password(user, password):
        return jsonify({
            'error': 'invalid_credentials',
            'message': 'Invalid email or password'
        }), 401

    # Generate JWT token
    token = encode_jwt(user.id)

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'token': token,
        'token_type': 'Bearer',
        'expires_in_hours': 24
    }), 200
