import logging
import os
import shutil

from flask import Flask, g, request
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from flask_session import Session

from . import apis, blueprints, models, services
from .forms.forms import frm_client
from .helpers.utils import email_to_gravatar_url, show_all_attrs
from .helpers.wireguard import WireguardError, wireguard_service
from .models import Setting


def create_app(config=None):
    app = Flask(__name__)

    CSRFProtect(app)

    # Create static folder outside app folder
    os.makedirs(f"{app.root_path}/../static", exist_ok=True)
    app.static_folder = f"{app.root_path}/../static"

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

    # URI Database
    SQLALCHEMY_DATABASE_URI = app.config.get("MARIADB_DATABASE_URI")
    if app.config.get("SQLA_DB_TYPE") != "mariadb":
        os.makedirs(app.root_path + "/../database", exist_ok=True)
        db_name = app.config.get("SQLA_DB_NAME")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{app.root_path}/../database/{db_name}.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

    app.jinja_env.filters["show_all_attrs"] = [show_all_attrs]
    app.jinja_env.add_extension("jinja2.ext.debug")
    app.jinja_env.add_extension("jinja2.ext.i18n")
    app.jinja_env.filters["email_to_gravatar_url"] = email_to_gravatar_url

    # Load app's components
    apis.init_app(app)
    blueprints.init_app(app)
    models.init_app(app)
    services.init_app(app)

    # Register context processors
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

    @app.before_request
    def sidebar_collapsed():
        g.collapsed = request.cookies.get("sidebar-collapsed", False) == "true"

    return app
