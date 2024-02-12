from flask_assets import Environment
from flask_mail import Mail
from flask_qrcode import QRcode
from flask_security import Security

assets = Environment()
qrcode = QRcode()
mail = Mail()
security = Security()
