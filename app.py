"""Flask application factory."""
import os
import sys
from flask import Flask

# Add project root to path for module resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config_map, BASE_DIR
from shared.database import db, migrate
from shared.auth import login_manager


def create_app(config_name: str = None) -> Flask:
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_object(config_map[config_name])

    # Ensure instance folder exists
    os.makedirs(BASE_DIR / "instance", exist_ok=True)
    os.makedirs(app.config.get("UPLOAD_FOLDER", "static/uploads"), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    _register_blueprints(app)

    # Register template context processors
    _register_context_processors(app)

    # Create tables (development convenience)
    with app.app_context():
        _import_models()
        db.create_all()

    return app


def _register_blueprints(app: Flask):
    """Register all application blueprints."""
    from products.routes import products_bp
    from customers.routes import customers_bp
    from ai_reviews.routes import reviews_bp
    from recommendations.routes import recommendations_bp
    from checkout.routes import checkout_bp
    from returns.routes import returns_bp
    from grading.routes import grading_bp
    from routing.routes import routing_bp
    from credits.routes import credits_bp
    from admin_dashboard.routes import admin_bp
    from marketplace.routes import marketplace_bp

    # Main pages blueprint
    from flask import Blueprint, render_template
    main_bp = Blueprint("main", __name__)

    @main_bp.route("/")
    def index():
        from products.services import ProductService
        featured = ProductService.get_featured_products(limit=8)
        refurbished = ProductService.get_refurbished_products(limit=4)
        return render_template(
            "index.html",
            featured_products=featured,
            refurbished_products=refurbished,
        )

    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(returns_bp)
    app.register_blueprint(grading_bp)
    app.register_blueprint(routing_bp)
    app.register_blueprint(credits_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(marketplace_bp)


def _register_context_processors(app: Flask):
    """Register Jinja2 context processors available in all templates."""
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        cart_count = 0
        if current_user.is_authenticated:
            from checkout.services import CartService
            cart_count = CartService.get_cart_count(current_user.id)
        return {
            "app_name": "ReturnLess",
            "current_year": 2026,
            "cart_count": cart_count,
        }


def _import_models():
    """Import all models to ensure they are registered with SQLAlchemy."""
    import products.models  # noqa: F401
    import customers.models  # noqa: F401
    import ai_reviews.models  # noqa: F401
    import recommendations.models  # noqa: F401
    import checkout.models  # noqa: F401
    import returns.models  # noqa: F401
    import grading.models  # noqa: F401
    import routing.models  # noqa: F401
    import credits.models  # noqa: F401
