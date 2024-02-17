"""Use Flask-Asssets for build and minified css and js."""

from flask_assets import Bundle, Filter


class ConcatFilter(Filter):
    """
    Filter that merges files, placing a semicolon between them.
    Fixes issues caused by missing semicolons at end of JS assets, for example
    with last statement of jquery.pjax.js.
    """

    def concat(self, out, hunks, **kw):
        out.write(";".join([h.data() for h, info in hunks]))


css_login = Bundle(
    "https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,600,700,300italic,400italic,600italic",  # noqa
    "https://fonts.googleapis.com/css?family=Roboto+Mono:400,300,700",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
    Bundle(
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.min.css",
        filters="datauri",
    ),
    output="css/login.css",
)

css_main = Bundle(
    "https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,600,700,300italic,400italic,600italic",
    "https://fonts.googleapis.com/css?family=Roboto+Mono:400,300,700",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
    Bundle(
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.min.css",
        filters="datauri",
    ),
    "https://rawcdn.githack.com/darkterminal/tagin/6fa2863c13aa1841f33cf6dcbbf266c92fbf5412/dist/css/tagin.min.css",
    output="css/main.css",
)

css_custom = Bundle(
    "../app/resources/css/custom.css", filters="cssmin", output="css/custom.css"
)


js_login = Bundle(
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js",
    Bundle("../app/resources/js/login.js", filters="jinja2,rjsmin"),
    output="js/login.js",
)

js_validation = Bundle(
    "https://cdnjs.cloudflare.com/ajax/libs/jquery-validate/1.20.0/jquery.validate.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery-validate/1.20.0/additional-methods.min.js",
    output="js/validation.js",
)

js_main = Bundle(
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js",
    "https://rawcdn.githack.com/darkterminal/tagin/6fa2863c13aa1841f33cf6dcbbf266c92fbf5412/dist/js/tagin.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js",
    output="js/main.js",
)

js_custom = Bundle(
    "../app/resources/js/custom.js",
    "../app/resources/js/libs.js",
    filters="jinja2,rjsmin",
    output="js/custom.js",
)
