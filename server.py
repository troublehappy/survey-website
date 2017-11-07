from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

app = Flask(__name__, static_url_path='/static')

app.config.from_object('config')
app.secret_key = os.urandom(5)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
