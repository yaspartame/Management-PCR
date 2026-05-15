def log_audit_action(conn, cursor, actor_id, action_type, details, ip_address):
    query = "INSERT INTO tbl_audit_logs (actor_id, action_type, action_details, ip_address) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (str(actor_id), action_type, details, ip_address))
    conn.commit()


def get_recent_audit_logs(cursor, limit=50):
    cursor.execute(
        "SELECT log_timestamp, actor_id, action_type, action_details, ip_address FROM tbl_audit_logs ORDER BY log_timestamp DESC LIMIT %s",
        (limit,)
    )
    return cursor.fetchall()


def emergency_reset_password(conn, cursor, emp_id, new_hashed_password):
    cursor.execute(
        "UPDATE tbl_auth_credentials SET password_hash = %s WHERE emp_id = %s",
        (new_hashed_password, emp_id)
    )
    conn.commit()


def emergency_lock_account(conn, cursor, emp_id):
    cursor.execute(
        "UPDATE tbl_system_access SET account_status = 'Locked' WHERE emp_id = %s",
        (emp_id,)
    )
    conn.commit()


def get_all_users_for_security(cursor):
    query = """
        SELECT e.emp_id, e.first_name, e.last_name, s.system_role, s.account_status
        FROM tbl_employee_profiles e
        JOIN tbl_system_access s ON e.emp_id = s.emp_id
        ORDER BY e.last_name ASC
    """
    cursor.execute(query)
    return cursor.fetchall()
