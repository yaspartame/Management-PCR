from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Set a secret key for secure sessions (login cookies)
app.secret_key = os.getenv('SECRET_KEY', 'dipcr_version_13_secret_key')

# Register route blueprints
from app.routes import register_blueprints
register_blueprints(app)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response