from flask import Flask
from app.models import db
from app.config import Config


def create_app(config_class=Config) -> Flask:
    """
    Flask application factory.

    Args:
        config_class: Configuration class to use (defaults to Config)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    app.config.from_object(config_class)

    # Initialize SQLAlchemy with app
    db.init_app(app)

    # Create instance folder and database tables
    import os
    os.makedirs(app.instance_path, exist_ok=True)

    with app.app_context():
        db.create_all()

    # Register blueprints
    from app.auth import auth_bp
    from app.plans import plans_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(plans_bp, url_prefix='/api/plans')

    return app
