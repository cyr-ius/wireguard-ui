from flask import g, request

from ..forms.forms_security import ExtendedRegisterForm
from .assets import (
    css_custom,
    css_login,
    css_main,
    js_custom,
    js_login,
    js_main,
    js_validation,
)
from .base import assets, mail, qrcode, security


def init_app(app):
    assets.init_app(app)
    mail.init_app(app)
    qrcode.init_app(app)
    security.init_app(
        app,
        app.user_datastore,
        register_form=ExtendedRegisterForm,
        confirm_register_form=ExtendedRegisterForm,
    )

    assets.register("css_custom", css_custom)
    assets.register("css_login", css_login)
    assets.register("css_main", css_main)
    assets.register("js_custom", js_custom)
    assets.register("js_login", js_login)
    assets.register("js_main", js_main)
    assets.register("js_validation", js_validation)

    @security.context_processor
    def sidebar_context_processor():
        g.collapsed = request.cookies.get("sidebar-collapsed", False) == "true"
        return dict()
