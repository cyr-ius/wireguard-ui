# Create app blueprints
from .base import (
    handle_access_forbidden,
    handle_bad_gateway,
    handle_bad_request,
    handle_internal_server_error,
    handle_page_not_found,
)
from .main import main_bp
from .user import user_bp


def init_app(app):
    """Init Blueprint."""
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)

    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(403, handle_access_forbidden)
    app.register_error_handler(404, handle_page_not_found)
    app.register_error_handler(500, handle_internal_server_error)
    app.register_error_handler(502, handle_bad_gateway)
