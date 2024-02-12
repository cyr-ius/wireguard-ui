# app/__init__.py
import logging
import os
import shutil

from flask import Flask, g, request
from flask_admin import Admin
from flask_admin import helpers as admin_helpers
from flask_assets import Environment
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_qrcode import QRcode
from flask_security import Security, SQLAlchemySessionUserDatastore
from flask_security.utils import hash_password
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from flask_session import Session

from . import blueprints
from .forms.forms import frm_client
from .forms.forms_security import ExtendedRegisterForm
from .models import Clients, GlobalSettings, Role, Setting, User
from .services.admin import GlobalView, HomeView, SecureView, UserView
from .services.handle import ErrorHandler
from .utils import (
    WireguardError,
    email_to_gravatar_url,
    is_first_run,
    wireguard_service,
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
errorhandler = ErrorHandler()


def create_app(config=None):
    app = Flask(__name__)

    # Create static folder outside app folder
    try:
        os.makedirs(app.root_path + "/../static", exist_ok=True)
        app.static_folder = app.root_path + "/../static"
    except OSError:
        pass

    shutil.copytree(
        f"{app.root_path}/resources/css/fonts",
        f"{ app.static_folder}/css/fonts",
        dirs_exist_ok=True,
    )
    shutil.copytree(
        f"{app.root_path}/resources/img",
        f"{ app.static_folder}/img",
        dirs_exist_ok=True,
    )

    # Set log level
    log_level = logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO").upper())
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

    if app.debug:

        def show_all_attrs(value):
            res = []
            for k in dir(value):
                res.append("%r %r\n" % (k, getattr(value, k)))
            return "\n".join(res)

        app.jinja_env.filters["show_all_attrs"] = [show_all_attrs]

    app.jinja_env.add_extension("jinja2.ext.debug")
    app.jinja_env.add_extension("jinja2.ext.i18n")
    app.jinja_env.filters["email_to_gravatar_url"] = email_to_gravatar_url

    # Register Security model


    app.user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)

    # Register Admin
    admin.add_view(UserView(model=User, session=db.session, endpoint="accounts"))
    admin.add_view(GlobalView(model=GlobalSettings, session=db.session))
    admin.add_view(SecureView(model=Clients, session=db.session))

    # Load app's components
    assets.init_app(app)
    blueprints.init_app(app)
    errorhandler.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    assets.init_app(app)
    migrate.init_app(app, db)
    qrcode.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app, index_view=HomeView())
    security.init_app(
        app,
        app.user_datastore,
        register_form=ExtendedRegisterForm,
        confirm_register_form=ExtendedRegisterForm,
    )

    # Init database
    with app.app_context():
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
        is_first_run()
        g.collapsed = request.cookies.get("sidebar-collapsed", False) == "true"
        return dict()

    @security.tf_setup_context_processor
    def tf_setup_context_processor():
        is_first_run()
        g.collapsed = request.cookies.get("sidebar-collapsed", False) == "true"
        return dict()

    if app.config["WIREGUARD_STARTUP"]:
        with app.app_context():
            try:
                wireguard_service("start")
            except WireguardError as error:
                app.logger.error("Error while startup (%s)", error)

    @app.after_request
    def set_secure_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    return app
