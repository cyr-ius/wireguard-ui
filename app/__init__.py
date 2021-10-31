# app/__init__.py
import logging
import os

from flask import Flask, request, g
from flask_admin import Admin, helpers as admin_helpers
from flask_assets import Environment
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_qrcode import QRcode
from flask_security import Security, SQLAlchemySessionUserDatastore
from flask_security.utils import hash_password
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from .forms.forms import frm_client
from .forms.forms_security import ExtendedRegisterForm
from .services.admin import GlobalView, HomeView, UserView, SecureView
from .services.assets import (
    css_login,
    css_main,
    css_custom,
    js_login,
    js_main,
    js_validation,
    js_custom,
)
from .services.handle import (
    handle_access_forbidden,
    handle_bad_request,
    handle_internal_server_error,
    handle_page_not_found,
    handle_unauthorized_access,
)


mail = Mail()
db = SQLAlchemy()
qrcode = QRcode()
assets = Environment()
migrate = Migrate()
login_manager = LoginManager()
admin = Admin(
    name="Administration",
    template_mode="bootstrap4",
    base_template="administration.html",
)
security = Security()


def create_app(config=None):
    app = Flask(__name__)

    # Create static folder outside app folder
    try:
        os.makedirs(app.root_path + "/../static", exist_ok=True)
        app.static_folder = app.root_path + "/../static"
    except OSError:
        pass

    # Read log level from environment variable
    log_level_name = os.environ.get("LOG_LEVEL", "WARNING")
    log_level = logging.getLevelName(log_level_name.upper())
    # Setting logger
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s",
    )

    # If we use Docker + Gunicorn, adjust the log handler
    if "GUNICORN_LOGLEVEL" in os.environ:
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    # Proxy
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Load default configuration
    app.config.from_object("app.config")

    # Load config file from FLASK_CONF env variable
    if "FLASK_CONF" in os.environ:
        app.config.from_envvar("FLASK_CONF")

    # Load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith(".py"):
            app.config.from_pyfile(config)

    # Load Flask-Session
    if app.config.get("FILESYSTEM_SESSIONS_ENABLED"):
        app.config["SESSION_TYPE"] = "filesystem"
        sess = Session()
        sess.init_app(app)

    # Load Database
    SQLALCHEMY_DATABASE_URI = app.config.get("MARIADB_DATABASE_URI")
    if app.config.get("SQLA_DB_TYPE") != "mariadb":
        db_name = app.config.get("SQLA_DB_NAME")
        # Ensure the instance folder exists
        try:
            os.makedirs(app.root_path + "/../database", exist_ok=True)
        except OSError:
            pass
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{app.root_path}/../database/{db_name}.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

    # Load app's components
    mail.init_app(app)
    db.init_app(app)
    assets.init_app(app)
    migrate.init_app(app, db)
    qrcode.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app, index_view=HomeView())

    # Register filters
    from .utils import email_to_gravatar_url

    app.jinja_env.filters["email_to_gravatar_url"] = email_to_gravatar_url
    if app.debug:
        def show_all_attrs(value):
            res = []
            for k in dir(value):
                res.append('%r %r\n' % (k, getattr(value, k)))
            return '\n'.join(res)
        app.jinja_env.filters["show_all_attrs"] = show_all_attrs
        app.jinja_env.add_extension("jinja2.ext.debug")

    # Register Assets
    assets.register("css_login", css_login)
    assets.register("js_login", js_login)
    assets.register("js_validation", js_validation)
    assets.register("css_main", css_main)
    assets.register("js_main", js_main)
    assets.register("css_custom", css_custom)
    assets.register("js_custom", js_custom)

    # Create app blueprints
    from .routes.main import main_bp

    app.register_blueprint(main_bp)
    from .routes.user import user_bp

    app.register_blueprint(user_bp)
    from .routes.api import api_bp

    app.register_blueprint(api_bp)

    # Register error handler
    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(401, handle_unauthorized_access)
    app.register_error_handler(403, handle_access_forbidden)
    app.register_error_handler(404, handle_page_not_found)
    app.register_error_handler(500, handle_internal_server_error)

    # Import tables for security & admin
    from .models import Clients, User, GlobalSettings, Role, Setting

    # Register Security model
    app.user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
    security.init_app(app, app.user_datastore, register_form=ExtendedRegisterForm, confirm_register_form=ExtendedRegisterForm)

    # Register Admin
    admin.add_view(UserView(model=User, session=db.session, endpoint="accounts"))
    admin.add_view(GlobalView(model=GlobalSettings, session=db.session))
    admin.add_view(SecureView(model=Clients, session=db.session))

    # Init database
    @app.before_first_request
    def create_tables():
        app.logger.info("Initialising the table in database.")
        db.create_all()
        if len(db.session.query(Setting).all()) == 0:
            Setting().init_db()

        app.user_datastore.find_or_create_role(
            name="admin",
            permissions={"admin-read", "admin-write", "user-read", "user-write"},
        )
        app.user_datastore.find_or_create_role(
            name="user", permissions={"user-read", "user-write"}
        )
        app.user_datastore.find_or_create_role(
            name="dba",
            permissions={"dba-read", "dba-write"},
        )

        if not app.user_datastore.find_user(username=app.config["USERNAME"]):
            app.user_datastore.create_user(
                email=app.config["USER_MAIL"],
                password=hash_password(app.config["PASSWORD"]),
                username=app.config["USERNAME"],
                first_name=app.config["USERNAME"],
                roles=["admin"],
            )
        db.session.commit()
        app.logger.info("Database is ready.")

    # Register context proccessors
    @app.context_processor
    def inject_sitename():
        return dict(
            SITE_NAME=app.config["SITE_NAME"],
            WUI_VERSION=app.config["WUI_VERSION"],
        )

    @app.context_processor
    def inject_setting():
        setting = Setting()
        return dict(SETTING=setting)

    @app.context_processor
    def inject_form_client():
        return dict(form_client=frm_client())

    @app.context_processor
    def inject_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
        )

    @security.change_password_context_processor
    def change_password_context_processor():
        from .utils import is_first_run

        is_first_run()
        g.collapsed = request.cookies.get('sidebar-collapsed', False) == 'true'
        return dict()

    @security.tf_setup_context_processor
    def tf_setup_context_processor():
        from .utils import is_first_run

        is_first_run()
        g.collapsed = request.cookies.get('sidebar-collapsed', False) == 'true'
        return dict()

    if app.config["WIREGUARD_STARTUP"]:
        with app.app_context():
            from app.utils import wireguard_service, WireguardError

            try:
                wireguard_service("start")
            except WireguardError:
                pass

    return app
