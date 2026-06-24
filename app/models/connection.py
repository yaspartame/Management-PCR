import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_pool = None


def _require_env(key):
    """Get an env var or raise a clear error."""
    val = os.getenv(key)
    if not val:
        raise RuntimeError(
            f"Missing required environment variable '{key}'. "
            f"Check your .env file or set it in your environment."
        )
    return val


def init_db_pool():
    """Initialize the connection pool once at app startup."""
    global _pool
    try:
        logger.info("Initializing database connection pool...")
        _pool = MySQLConnectionPool(
            pool_name="dipcr_pool",
            pool_size=5,
            host=_require_env('DB_HOST'),
            port=int(_require_env('DB_PORT')),
            database=_require_env('DB_NAME'),
            user=_require_env('DB_USER'),
            password=_require_env('DB_PASSWORD'),
            connection_timeout=5,
            autocommit=True
        )
        logger.info("Database connection pool created successfully.")
    except Error as e:
        raise RuntimeError(f"Failed to create DB connection pool: {e}")


def get_db_connection():
    global _pool
    if _pool is None:
        init_db_pool()
    try:
        t0 = time.time()
        connection = _pool.get_connection()
        elapsed = time.time() - t0
        if elapsed > 0.5:
            logger.warning(f"Slow pool checkout: {elapsed:.2f}s")
        if connection.is_connected():
            return connection
        raise RuntimeError("Database connection could not be established.")
    except Error as e:
        raise RuntimeError(f"Database connection failed: {e}")


def timed_query(cursor, query, params=None, label=""):
    """Execute a query with timing logging."""
    t0 = time.time()
    cursor.execute(query, params or ())
    elapsed = time.time() - t0
    if elapsed > 0.3:
        logger.warning(f"SLOW QUERY ({elapsed:.2f}s): {label or query[:80]}")
    columns = [col[0] for col in cursor.description] if cursor.description else []
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
