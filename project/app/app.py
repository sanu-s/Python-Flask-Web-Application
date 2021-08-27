from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

from app.settings import DevelopmentSettings as Settings


# Setup Flask Configurations
app = Flask(__name__)

app.config.from_object(Settings)
db = SQLAlchemy(app)
jwt = JWTManager(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
