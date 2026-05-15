def get_user_by_email(cursor, email):
    cursor.callproc('get_user_by_email', (email,))
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
