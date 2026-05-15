from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Set a secret key for secure sessions (login cookies)
app.secret_key = os.getenv('SECRET_KEY', 'accrual_version_13_secret_key')

# Register route blueprints
from app.routes import register_blueprints
register_blueprints(app)