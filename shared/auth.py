"""Authentication setup using Flask-Login."""
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "customers.login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    from customers.models import Customer
    return Customer.query.get(int(user_id))
