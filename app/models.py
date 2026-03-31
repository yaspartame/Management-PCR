import mysql.connector
from mysql.connector import Error


def get_db_connection():
    try:
        connection = mysql.connector.connect(
           host='144.21.57.156',
           port=6767,
           database='ipcr_db',
           user='app_user',
           password='cN5FTZkDnJ+RdtnANZ1xCqD/EDspz7WqHEasXc0QHFZ9xtG2XopJdsL9S83QSvvAOmRzkUpHU3K27bsGY8csNA==',
           connection_timeout=5
        )
        if connection.is_connected():
            print("Connection established")
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None
    
    
def get_user_by_email(cursor,email):
    cursor.callproc('get_user_by_email',(email,))
    for result in cursor.stored_results():
        return result.fetchall()
    return []

def register_user(cursor, emp_id, email, password_hash):
    cursor.callproc('register_user', (emp_id, email, password_hash))
    