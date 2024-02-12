# import base64
from flask import redirect, render_template, request, session, url_for


class ErrorHandler:
    """Object Error Handler."""

    def init_app(self, app):
        """Initialize Application."""
        app.register_error_handler(400, self.handle_bad_request)
        app.register_error_handler(200, self.handle_unauthorized_access)        
        app.register_error_handler(403, self.handle_access_forbidden)
        app.register_error_handler(404, self.handle_page_not_found)
        app.register_error_handler(500, self.handle_internal_server_error)
        app.register_error_handler(502, self.handle_bad_gateway)    

    def handle_bad_request(self, e):
        """Bad request."""
        return render_template("errors/400.html", code=400, message=e), 400


    def handle_unauthorized_access(e):
        session["next"] = request.script_root + request.path
        return redirect(url_for("index.login"))


    def handle_access_forbidden(self, e):
        """Access forbidden."""
        return render_template("errors/403.html", code=403, message=e), 403


    def handle_page_not_found(self, e):
        """Page not found."""
        return render_template("errors/404.html", code=404, message=e), 404

    def handle_internal_server_error(self, e):
        """Internal error."""
        return render_template("errors/500.html", code=500, message=e), 500     

    def handle_bad_gateway(self, e):
        """Bad gateway."""
        return render_template("errors/502.html", code=502, message=e), 502