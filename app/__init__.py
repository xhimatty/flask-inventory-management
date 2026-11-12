import logging
from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager, csrf

app = Flask(__name__)

app.config.from_object(Config)

log_handler = logging.FileHandler('logs/app.log')

log_handler.setLevel(logging.WARNING)

log_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

log_handler.setFormatter(log_format)

app.logger.addHandler(log_handler)
app.logger.setLevel(logging.WARNING)


db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
csrf.init_app(app)

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


from app.views.main import main
from app.views.auth import auth
from app.views.products import prod
from app.views.inventory import inventory
from app.views.errors import register_error_handlers

app.register_blueprint(main)
app.register_blueprint(auth)
app.register_blueprint(prod)
app.register_blueprint(inventory)

register_error_handlers(app)

from app import models

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(models.User, int(user_id))