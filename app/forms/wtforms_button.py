from markupsafe import Markup
from wtforms import StringField
from wtforms.widgets import html_params


class ButtonWidget(object):
    """
    Renders a multi-line text area.
    `rows` and `cols` ought to be passed as keyword args when rendering.
    """

    input_type = "button"

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", self.input_type)
        if "value" not in kwargs:
            kwargs["value"] = field._value()

        return Markup(
            "<button {params}>{label}</button>".format(
                params=self.html_params(name=field.name, **kwargs),
                label=field.label.text,
            )
        )


class ButtonField(StringField):
    widget = ButtonWidget()
