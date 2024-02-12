from flask_admin import Admin
from flask_assets import Environment
from flask_mail import Mail
from flask_qrcode import QRcode
from flask_security import Security

admin = Admin(
    name="Administration",
    template_mode="bootstrap4",
    base_template="administration.html",
)
assets = Environment()
qrcode = QRcode()
mail = Mail()
security = Security()
