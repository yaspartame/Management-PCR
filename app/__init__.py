from flask import Flask, g, request
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Set a secret key for secure sessions (login cookies)
app.secret_key = os.getenv('SECRET_KEY', 'dipcr_version_13_secret_key')

# Initialize DB connection pool at startup
from app.models.connection import init_db_pool
init_db_pool()


# Request timing middleware
@app.before_request
def start_timer():
    g.start_time = time.time()


@app.after_request
def log_request_time(response):
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        if elapsed > 1.0:
            logger.warning(f"SLOW REQUEST: {request.method} {request.path} — took {elapsed:.2f}s")
        else:
            logger.info(f"REQUEST: {request.method} {request.path} — {elapsed:.2f}s")
    return response

# Register route blueprints
from app.routes import register_blueprints
register_blueprints(app)