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
            return connection
        raise RuntimeError("Database connection could not be established.")
    except Error as e:
        raise RuntimeError(f"Database connection failed: {e}")
    
    
def get_user_by_email(cursor,email):
    cursor.callproc('get_user_by_email',(email,))
    for result in cursor.stored_results():
        return result.fetchall()
    return []

def register_user(conn, cursor, employee_id_number, email, password_hash):
    try:
        cursor.callproc('register_user', (employee_id_number, email, password_hash))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def get_all_profiles(cursor):
    cursor.execute("SELECT * FROM tbl_employee_profiles ORDER BY last_name ASC, first_name ASC")
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def save_single_profile(conn, cursor, data):
    sql = """
        INSERT INTO tbl_employee_profiles 
        (employee_id_number, first_name, last_name, college, assigned_program, specialization, academic_rank, employment_status, leave_status, designation)
        VALUES (%(employee_id_number)s, %(first_name)s, %(last_name)s, %(college)s, %(assigned_program)s, %(specialization)s, %(academic_rank)s, %(employment_status)s, %(leave_status)s, %(designation)s)
        ON DUPLICATE KEY UPDATE 
        first_name = VALUES(first_name),
        last_name = VALUES(last_name),
        college = VALUES(college),
        assigned_program = VALUES(assigned_program),
        specialization = VALUES(specialization),
        academic_rank = VALUES(academic_rank),
        employment_status = VALUES(employment_status),
        leave_status = VALUES(leave_status),
        designation = VALUES(designation)
    """
    try:
        cursor.execute(sql, data)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def toggle_profile_status(conn, cursor, employee_id_number):
    try:
        cursor.execute("SELECT emp_id, leave_status FROM tbl_employee_profiles WHERE employee_id_number = %s", (employee_id_number,))
        result = cursor.fetchone()
        if not result:
            return False
            
        emp_id, current_status = result
        new_status = 'Inactive' if current_status == 'Active' else 'Active'
        
        cursor.execute("UPDATE tbl_employee_profiles SET leave_status = %s WHERE employee_id_number = %s", (new_status, employee_id_number))
        cursor.execute("UPDATE tbl_system_access SET account_status = %s WHERE emp_id = %s", (new_status, emp_id))
        
        conn.commit()
        return new_status
    except Exception as e:
        conn.rollback()
        raise e

def import_csv_roster(conn, cursor, csv_rows):
    new_added = 0
    updated = 0
    unchanged = 0
    
    try:
        cursor.execute("SELECT employee_id_number, first_name, last_name, college, assigned_program, specialization, academic_rank, employment_status, leave_status, designation FROM tbl_employee_profiles")
        columns = [col[0] for col in cursor.description]
        existing_profiles = {}
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            for k, v in record.items():
                if v is None:
                    record[k] = ""
            existing_profiles[record['employee_id_number']] = record

        insert_sql = """
            INSERT INTO tbl_employee_profiles 
            (employee_id_number, first_name, last_name, college, assigned_program, specialization, academic_rank, employment_status, leave_status, designation)
            VALUES (%(employee_id_number)s, %(first_name)s, %(last_name)s, %(college)s, %(assigned_program)s, %(specialization)s, %(academic_rank)s, %(employment_status)s, %(leave_status)s, %(designation)s)
        """
        
        update_sql = """
            UPDATE tbl_employee_profiles 
            SET first_name=%(first_name)s, last_name=%(last_name)s, college=%(college)s, 
                assigned_program=%(assigned_program)s, specialization=%(specialization)s, academic_rank=%(academic_rank)s, 
                employment_status=%(employment_status)s, leave_status=%(leave_status)s, designation=%(designation)s
            WHERE employee_id_number=%(employee_id_number)s
        """
        
        for row in csv_rows:
            emp_id = row.get('employee_id_number', '').strip()
            if not emp_id:
                continue
            
            current_row = {
                'employee_id_number': emp_id,
                'first_name': row.get('first_name', '').strip(),
                'last_name': row.get('last_name', '').strip(),
                'college': row.get('college', '').strip(),
                'assigned_program': row.get('assigned_program', '').strip(),
                'specialization': row.get('specialization', '').strip(),
                'academic_rank': row.get('academic_rank', '').strip(),
                'employment_status': row.get('employment_status', '').strip(),
                'leave_status': row.get('leave_status', '').strip(),
                'designation': row.get('designation', '').strip()
            }
            
            if emp_id not in existing_profiles:
                cursor.execute(insert_sql, current_row)
                new_added += 1
            else:
                existing = existing_profiles[emp_id]
                differs = False
                for key in ['first_name', 'last_name', 'college', 'assigned_program', 'specialization', 'academic_rank', 'employment_status', 'leave_status', 'designation']:
                    if str(current_row[key]) != str(existing[key]):
                        differs = True
                        break
                        
                if differs:
                    cursor.execute(update_sql, current_row)
                    updated += 1
                else:
                    unchanged += 1
                    
        conn.commit()
        return True, new_added, updated, unchanged
    except Exception as e:
        conn.rollback()
        return False, str(e), 0, 0

def open_new_term(conn, cursor, academic_year, semester, deadline_date):
    try:
        # Deactivate all current terms
        cursor.execute("UPDATE tbl_academic_terms SET is_active = FALSE")
        
        # Insert and activate the new term
        query_open = """
            INSERT INTO tbl_academic_terms (academic_year, semester, deadline_date, is_active)
            VALUES (%s, %s, %s, TRUE)
        """
        cursor.execute(query_open, (academic_year, semester, deadline_date))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def get_all_terms(cursor):
    query = "SELECT term_id, academic_year, semester, deadline_date, is_active FROM tbl_academic_terms ORDER BY term_id DESC"
    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_master_indicators(cursor, term_id):
    query = """
        SELECT m.indicator_id, c.category_name, m.indicator_description, m.efficiency_type,
               EXISTS(SELECT 1 FROM tbl_cascaded_quotas q WHERE q.indicator_id = m.indicator_id) AS is_locked
        FROM tbl_master_indicators m
        JOIN tbl_target_categories c ON m.category_id = c.category_id
        WHERE m.term_id = %s
        ORDER BY c.category_name, m.indicator_id
    """
    cursor.execute(query, (term_id,))
    return cursor.fetchall()


def add_master_indicator(conn, cursor, category_name, description, efficiency_type, term_id):
    cursor.execute("SELECT category_id FROM tbl_target_categories WHERE category_name = %s", (category_name,))
    cat_result = cursor.fetchone()
    if not cat_result:
        cursor.execute("INSERT INTO tbl_target_categories (category_name) VALUES (%s)", (category_name,))
        category_id = cursor.lastrowid
    else:
        category_id = cat_result[0]

    query = "INSERT INTO tbl_master_indicators (category_id, indicator_description, efficiency_type, term_id) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (category_id, description, efficiency_type, term_id))
    conn.commit()


def edit_master_indicator(conn, cursor, indicator_id, category_name, description, efficiency_type):
    cursor.execute("SELECT category_id FROM tbl_target_categories WHERE category_name = %s", (category_name,))
    cat_result = cursor.fetchone()
    if not cat_result:
        cursor.execute("INSERT INTO tbl_target_categories (category_name) VALUES (%s)", (category_name,))
        category_id = cursor.lastrowid
    else:
        category_id = cat_result[0]

    query = "UPDATE tbl_master_indicators SET category_id = %s, indicator_description = %s, efficiency_type = %s WHERE indicator_id = %s"
    cursor.execute(query, (category_id, description, efficiency_type, indicator_id))
    conn.commit()


def delete_master_indicator(conn, cursor, indicator_id):
    cursor.execute("DELETE FROM tbl_master_indicators WHERE indicator_id = %s", (indicator_id,))
    conn.commit()


def import_previous_term_indicators(conn, cursor, active_term_id):
    cursor.execute("SELECT term_id FROM tbl_academic_terms WHERE is_active = FALSE ORDER BY term_id DESC LIMIT 1")
    prev_term = cursor.fetchone()
    if not prev_term:
        return False, "No previous term found to import from."

    cursor.execute("SELECT category_id, indicator_description, efficiency_type FROM tbl_master_indicators WHERE term_id = %s", (prev_term[0],))
    prev_indicators = cursor.fetchall()

    if not prev_indicators:
        return False, "Previous term has no indicators to import."

    for ind in prev_indicators:
        cursor.execute(
            "INSERT INTO tbl_master_indicators (category_id, indicator_description, efficiency_type, term_id) VALUES (%s, %s, %s, %s)",
            (ind[0], ind[1], ind[2], active_term_id)
        )
    conn.commit()
    return True, "Previous semester targets successfully imported!"


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


def get_admin_kpis(cursor):
    kpis = {
        'claimed_accounts': 0,
        'total_roster': 0,
        'adoption_rate': 0,
        'term_status': "No Active Term"
    }

    # KPI 1: Roster Adoption Rate
    cursor.execute("SELECT COUNT(emp_id) FROM tbl_employee_profiles")
    roster_res = cursor.fetchone()
    kpis['total_roster'] = roster_res[0] if roster_res and roster_res[0] else 0

    cursor.execute("SELECT COUNT(emp_id) FROM tbl_auth_credentials")
    claimed_res = cursor.fetchone()
    kpis['claimed_accounts'] = claimed_res[0] if claimed_res and claimed_res[0] else 0

    if kpis['total_roster'] > 0:
        kpis['adoption_rate'] = round((kpis['claimed_accounts'] / kpis['total_roster']) * 100)

    # KPI 2: Term Deadline (Days Remaining)
    cursor.execute("SELECT DATEDIFF(deadline_date, CURDATE()) FROM tbl_academic_terms WHERE is_active = TRUE LIMIT 1")
    term_result = cursor.fetchone()

    if term_result is not None:
        if term_result[0] is not None:
            days = term_result[0]
            if days < 0:
                kpis['term_status'] = "Deadline Passed"
            else:
                kpis['term_status'] = f"{days} Days Remaining"
        else:
            kpis['term_status'] = "No Deadline Set"

    return kpis

# ! ADDED 28-APR-2026

def get_master_indicators(cursor, term_id):
    query = """
        SELECT mi.*, tc.category_name 
        FROM tbl_master_indicators mi
        LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE mi.term_id = %s
        ORDER BY tc.category_name, mi.indicator_id
    """
    cursor.execute(query, (term_id,))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_existing_cascaded_quotas(cursor, term_id):
    query = """
        SELECT cq.*, mi.indicator_description, tc.category_name
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE cq.term_id = %s
        ORDER BY mi.indicator_id
    """
    cursor.execute(query, (term_id,))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_overall_completion(cursor, term_id):
    query = """
        SELECT 
            COUNT(*) as total_targets,
            SUM(CASE WHEN ts.status = 'Approved' THEN 1 ELSE 0 END) as completed_targets
        FROM tbl_committed_targets ts
        WHERE ts.term_id = %s
    """
    cursor.execute(query, (term_id,))
    result = cursor.fetchone()
    if result and result[0] > 0:
        return round((result[1] / result[0]) * 100)
    return 0

def get_pending_approvals_count(cursor, term_id):
    query = """
        SELECT COUNT(*) 
        FROM tbl_final_scores fs
        WHERE fs.term_id = %s AND fs.dean_approval_status = 'Pending'
    """
    cursor.execute(query, (term_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_top_performing_department(cursor, term_id):
    query = """
        SELECT ep.assigned_program, AVG(fs.final_score) as avg_score
        FROM tbl_final_scores fs
        JOIN tbl_employee_profiles ep ON fs.emp_id = ep.emp_id
        WHERE fs.term_id = %s AND fs.dean_approval_status = 'Approved'
        GROUP BY ep.assigned_program
        ORDER BY avg_score DESC
        LIMIT 1
    """
    cursor.execute(query, (term_id,))
    result = cursor.fetchone()
    return result[0] if result else "N/A"

def get_pending_final_approvals(cursor, term_id):
    query = """
        SELECT 
            fs.score_id,
            ep.emp_id,
            CONCAT(ep.first_name, ' ', ep.last_name) as faculty_name,
            ep.assigned_program as department,
            fs.final_score,
            fs.adjectival_rating,
            fs.dean_approval_status
        FROM tbl_final_scores fs
        JOIN tbl_employee_profiles ep ON fs.emp_id = ep.emp_id
        WHERE fs.term_id = %s AND fs.dean_approval_status = 'Pending'
        ORDER BY ep.last_name ASC
    """
    cursor.execute(query, (term_id,))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def save_cascaded_quotas(cursor, connection, term_id, quotas_data):
    try:
        cursor.execute("DELETE FROM tbl_cascaded_quotas WHERE term_id = %s", (term_id,))
        
        for quota in quotas_data:
            cursor.execute("""
                INSERT INTO tbl_cascaded_quotas (term_id, indicator_id, total_target_value, assigned_to_role)
                VALUES (%s, %s, %s, %s)
            """, (term_id, quota['indicator_id'], quota['total_target'], quota['assigned_role']))
        
        connection.commit()
        return True, "Quotas cascaded successfully!"
    except Exception as e:
        connection.rollback()
        return False, f"Error saving quotas: {str(e)}"

def update_dean_approval_status(cursor, connection, score_ids, new_status):
    try:
        placeholders = ','.join(['%s'] * len(score_ids))
        cursor.execute(f"""
            UPDATE tbl_final_scores 
            SET dean_approval_status = %s 
            WHERE score_id IN ({placeholders})
        """, [new_status] + score_ids)
        connection.commit()
        return True, f"Successfully updated {cursor.rowcount} IPCR(s)"
    except Exception as e:
        connection.rollback()
        return False, f"Error updating approvals: {str(e)}"

# ! -- ADDED FOR PROG CHAIR --
def get_chair_indicators(cursor, term_id, specialization):
    query = """
        SELECT mi.indicator_id, mi.indicator_description, mi.efficiency_type, tc.category_name, cq.total_target_value as dept_quota
        FROM tbl_master_indicators mi
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        JOIN tbl_cascaded_quotas cq ON mi.indicator_id = cq.indicator_id AND cq.term_id = mi.term_id
        WHERE mi.term_id = %s
          AND tc.category_name IN ('A. Instructions', 'Support Functions')
          AND cq.assigned_to_role = %s
        ORDER BY tc.category_name, mi.indicator_id
    """
    cursor.execute(query, (term_id, specialization))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_specialization_faculty(cursor, specialization):
    query = """
        SELECT emp_id, first_name, last_name, academic_rank, leave_status
        FROM tbl_employee_profiles
        WHERE specialization = %s AND leave_status = 'Active'
    """
    cursor.execute(query, (specialization,))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_assigned_quantity(cursor, term_id, indicator_id, faculty_ids):
    if not faculty_ids:
        return 0
    format_strings = ','.join(['%s'] * len(faculty_ids))
    query = f"""
        SELECT assigned_quantity
        FROM tbl_committed_targets
        WHERE term_id = %s AND indicator_id = %s AND emp_id IN ({format_strings})
        LIMIT 1
    """
    cursor.execute(query, [term_id, indicator_id] + faculty_ids)
    res = cursor.fetchall()
    return res[0][0] if res else 0

def save_chair_allocation(conn, cursor, term_id, indicator_id, assigned_quantity, faculty_ids):
    try:
        if not faculty_ids:
            return False, "No active faculty found for this specialization."
            
        for emp_id in faculty_ids:
            # Check if exists
            check_query = "SELECT target_id FROM tbl_committed_targets WHERE emp_id = %s AND term_id = %s AND indicator_id = %s"
            cursor.execute(check_query, (emp_id, term_id, indicator_id))
            existing = cursor.fetchall()
            
            if existing:
                update_query = "UPDATE tbl_committed_targets SET assigned_quantity = %s WHERE target_id = %s"
                cursor.execute(update_query, (assigned_quantity, existing[0][0]))
            else:
                insert_query = """
                    INSERT INTO tbl_committed_targets (emp_id, term_id, indicator_id, assigned_quantity, status)
                    VALUES (%s, %s, %s, %s, 'Draft')
                """
                cursor.execute(insert_query, (emp_id, term_id, indicator_id, assigned_quantity))
        
        conn.commit()
        return True, "Targets distributed successfully to all faculty in your specialization."
    except Exception as e:
        conn.rollback()
        return False, str(e)
# ! -- ADD END --

# ! -- RET CHAIR ADDITIONS --
def get_ret_indicators(cursor, term_id):
    query = """
        SELECT mi.indicator_id, mi.indicator_description, mi.efficiency_type, tc.category_name, cq.total_target_value as dean_quota
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE cq.term_id = %s
          AND cq.assigned_to_role = 'RET / Extension'
        ORDER BY tc.category_name, mi.indicator_id
    """
    cursor.execute(query, (term_id,))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def save_ret_rule(conn, cursor, term_id, academic_rank, required_selections, indicator_ids):
    try:
        cursor.execute("DELETE FROM tbl_cascaded_quotas WHERE term_id = %s AND assigned_to_role = %s", (term_id, academic_rank))
        
        for ind_id in indicator_ids:
            cursor.execute("INSERT INTO tbl_cascaded_quotas (term_id, indicator_id, total_target_value, assigned_to_role) VALUES (%s, %s, %s, %s)", 
                           (term_id, ind_id, required_selections, academic_rank))
            
        conn.commit()
        return True, "Menu configuration saved successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)

def get_ret_rules(cursor, term_id):
    cursor.execute("""
        SELECT cq.assigned_to_role, cq.total_target_value, mi.indicator_id, mi.indicator_description
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        WHERE cq.term_id = %s AND cq.assigned_to_role IN (
            SELECT DISTINCT academic_rank FROM tbl_employee_profiles WHERE academic_rank IS NOT NULL AND academic_rank != ''
        )
    """, (term_id,))
    
    rows = cursor.fetchall()
    rules_dict = {}
    
    for r in rows:
        rank, required, ind_id, desc = r
        if rank not in rules_dict:
            rules_dict[rank] = {
                'rule_id': rank, 
                'academic_rank': rank,
                'required_selections': required,
                'indicators': []
            }
        rules_dict[rank]['indicators'].append({'id': ind_id, 'desc': desc})
        
    return list(rules_dict.values())

def delete_ret_rule(conn, cursor, rule_id):
    try:
        cursor.execute("DELETE FROM tbl_cascaded_quotas WHERE assigned_to_role = %s", (rule_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
# ! -- RET CHAIR ADDITIONS END --