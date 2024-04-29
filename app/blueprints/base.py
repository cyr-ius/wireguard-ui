from flask import redirect, render_template, request, session, url_for
from flask_login import LoginManager

# from flask_seasurf import SeaSurf

# csrf = SeaSurf()
login_manager = LoginManager()


def handle_bad_request(e):
    """Bad request."""
    return render_template("errors/400.html", code=400, message=e), 400


def handle_unauthorized_access(e):
    session["next"] = request.script_root + request.path
    return redirect(url_for("index.login"))


def handle_access_forbidden(e):
    """Access forbidden."""
    return render_template("errors/403.html", code=403, message=e), 403


def handle_page_not_found(e):
    """Page not found."""
    return render_template("errors/404.html", code=404, message=e), 404


def handle_internal_server_error(e):
    """Internal error."""
    return render_template("errors/500.html", code=500, message=e), 500


def handle_bad_gateway(e):
    """Bad gateway."""
    return render_template("errors/502.html", code=502, message=e), 502
