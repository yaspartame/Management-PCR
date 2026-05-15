import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    try:
        connection = mysql.connector.connect(
           host=os.getenv('DB_HOST', '144.21.57.156'),
           port=int(os.getenv('DB_PORT', '6767')),
           database=os.getenv('DB_NAME', 'ipcr_db'),
           user=os.getenv('DB_USER', 'app_user'),
           password=os.getenv('DB_PASSWORD', 'cN5FTZkDnJ+RdtnANZ1xCqD/EDspz7WqHEasXc0QHFZ9xtG2XopJdsL9S83QSvvAOmRzkUpHU3K27bsGY8csNA=='),
           connection_timeout=5
        )
        if connection.is_connected():
            return connection
        raise RuntimeError("Database connection could not be established.")
    except Error as e:
        raise RuntimeError(f"Database connection failed: {e}")
