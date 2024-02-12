from flask import g, request
from flask_admin import helpers as admin_helpers

from ..forms.forms_security import ExtendedRegisterForm
from ..models import Clients, GlobalSettings, User, db
from .admin import GlobalView, HomeView, SecureView, UserView
from .assets import (
    css_custom,
    css_login,
    css_main,
    js_custom,
    js_login,
    js_main,
    js_validation,
)
from .base import admin, assets, mail, qrcode, security


def init_app(app):
    assets.init_app(app)
    mail.init_app(app)
    admin.init_app(app, index_view=HomeView())
    qrcode.init_app(app)
    security.init_app(
        app,
        app.user_datastore,
        register_form=ExtendedRegisterForm,
        confirm_register_form=ExtendedRegisterForm,
    )

    admin.add_view(UserView(model=User, session=db.session, endpoint="accounts"))
    admin.add_view(GlobalView(model=GlobalSettings, session=db.session))
    admin.add_view(SecureView(model=Clients, session=db.session))

    assets.register("css_custom", css_custom)
    assets.register("css_login", css_login)
    assets.register("css_main", css_main)
    assets.register("js_custom", js_custom)
    assets.register("js_login", js_login)
    assets.register("js_main", js_main)
    assets.register("js_validation", js_validation)

    @app.context_processor
    def inject_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
        )

    @security.context_processor
    def sidebar_context_processor():
        g.collapsed = request.cookies.get("sidebar-collapsed", False) == "true"
        return dict()
