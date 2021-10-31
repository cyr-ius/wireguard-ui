from flask_assets import Bundle, Filter
from webassets.filter import get_filter
import re


class ConcatFilter(Filter):
    """
    Filter that merges files, placing a semicolon between them.
    Fixes issues caused by missing semicolons at end of JS assets, for example
    with last statement of jquery.pjax.js.
    """

    def concat(self, out, hunks, **kw):
        out.write(";".join([h.data() for h, info in hunks]))


bs_icons = (
    get_filter(
        "cssrewrite",
        replace=lambda url: re.sub(
            r"./fonts/",
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.6.1/font/fonts/",
            url,
        ),
    ),
)


css_login = Bundle(
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.1/dist/css/bootstrap.min.css",
    Bundle(
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.6.1/font/bootstrap-icons.min.css",
        filters=bs_icons,
    ),
    output="login.css",
)

js_login = Bundle(
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js",
    Bundle("../app/custom/js/login.js", filters="jsmin"),
    output="login.js",
)

js_validation = Bundle(
    "https://cdnjs.cloudflare.com/ajax/libs/jquery-validate/1.19.3/jquery.validate.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery-validate/1.19.3/additional-methods.min.js",
    output="validation.js",
)

css_main = Bundle(
    "https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,600,700,300italic,400italic,600italic",
    "https://fonts.googleapis.com/css?family=Roboto+Mono:400,300,700",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
    Bundle(
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.6.1/font/bootstrap-icons.min.css",
        filters=bs_icons,
    ),
    # "https://cdnjs.cloudflare.com/ajax/libs/admin-lte/3.1.0/css/adminlte.min.css",
    "https://rawcdn.githack.com/darkterminal/tagin/6fa2863c13aa1841f33cf6dcbbf266c92fbf5412/dist/css/tagin.min.css",
    output="main.css",
)

js_main = Bundle(
    # "node_modules/moment/moment.js",
    # "node_modules/jquery.quicksearch/src/jquery.quicksearch.js",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js",
    "https://rawcdn.githack.com/darkterminal/tagin/6fa2863c13aa1841f33cf6dcbbf266c92fbf5412/dist/js/tagin.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js",
    # "https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js",
    # "https://cdnjs.cloudflare.com/ajax/libs/admin-lte/3.1.0/js/adminlte.min.js",
    output="main.js",
)

js_custom = Bundle("../app/custom/js/custom.js", output="custom.js")
# js_custom = Bundle("../app/custom/js/custom.js", filters="rjsmin", output="custom.js")
css_custom = Bundle(
    "../app/custom/css/custom.css", filters="cssmin", output="custom.css"
)
