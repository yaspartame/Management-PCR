def get_chair_indicators(cursor, term_id, specialization):
    from app.models.connection import timed_query
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
    return timed_query(cursor, query, (term_id, specialization), label="get_chair_indicators")


def get_specialization_faculty(cursor, specialization):
    from app.models.connection import timed_query
    query = """
        SELECT emp_id, first_name, last_name, academic_rank, leave_status
        FROM tbl_employee_profiles
        WHERE specialization = %s AND leave_status = 'Active'
    """
    return timed_query(cursor, query, (specialization,), label="get_specialization_faculty")


def get_assigned_quantity_batch(cursor, term_id, indicator_ids, faculty_ids):
    """
    Get assigned quantities for MULTIPLE indicators in ONE query.
    Returns dict: {indicator_id: assigned_quantity}
    Replaces N+1 get_assigned_quantity() calls.
    """
    if not faculty_ids or not indicator_ids:
        return {}
    from app.models.connection import timed_query
    fac_placeholders = ','.join(['%s'] * len(faculty_ids))
    ind_placeholders = ','.join(['%s'] * len(indicator_ids))
    query = f"""
        SELECT da.indicator_id, da.assigned_quantity
        FROM tbl_draft_allocation da
        JOIN tbl_master_indicators mi ON da.indicator_id = mi.indicator_id
        WHERE mi.term_id = %s 
          AND da.indicator_id IN ({ind_placeholders})
          AND da.emp_id IN ({fac_placeholders})
        GROUP BY da.indicator_id, da.assigned_quantity
    """
    rows = timed_query(cursor, query, [term_id] + indicator_ids + faculty_ids, label="get_assigned_quantity_batch")
    result = {}
    for row in rows:
        result[row['indicator_id']] = row['assigned_quantity']
    return result


def get_assigned_quantity(cursor, term_id, indicator_id, faculty_ids):
    if not faculty_ids:
        return 0
    format_strings = ','.join(['%s'] * len(faculty_ids))
    query = f"""
        SELECT da.assigned_quantity
        FROM tbl_draft_allocation da
        JOIN tbl_master_indicators mi ON da.indicator_id = mi.indicator_id
        WHERE mi.term_id = %s AND da.indicator_id = %s AND da.emp_id IN ({format_strings})
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
            # Check if an allocation record already exists in the draft staging table
            check_query = """
                SELECT allocation_id 
                FROM tbl_draft_allocation
                WHERE emp_id = %s AND indicator_id = %s
            """
            cursor.execute(check_query, (emp_id, indicator_id))
            existing = cursor.fetchall()

            if existing:
                update_query = "UPDATE tbl_draft_allocation SET assigned_quantity = %s WHERE allocation_id = %s"
                cursor.execute(update_query, (assigned_quantity, existing[0][0]))
            else:
                insert_query = """
                    INSERT INTO tbl_draft_allocation (emp_id, indicator_id, assigned_quantity)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (emp_id, indicator_id, assigned_quantity))

        conn.commit()
        return True, "Targets distributed successfully to all faculty draft worklists."
    except Exception as e:
        conn.rollback()
        return False, str(e)
