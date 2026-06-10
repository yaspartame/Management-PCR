def get_faculty_assigned_targets(cursor, emp_id, term_id):
    query = """
        SELECT ct.target_id, ct.indicator_id, ct.assigned_quantity, ct.status,
               mi.indicator_description, tc.category_name
        FROM tbl_committed_targets ct
        JOIN tbl_master_indicators mi ON ct.indicator_id = mi.indicator_id
        LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE ct.emp_id = %s AND mi.term_id = %s
    """
    cursor.execute(query, (emp_id, term_id))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_faculty_ret_menu(cursor, academic_rank, term_id):
    query = """
        SELECT cq.total_target_value as required_selections, mi.indicator_id, mi.indicator_description, tc.category_name
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE cq.term_id = %s AND cq.assigned_to_role = %s
          AND tc.category_name IN ('A. Research', 'B. Extension Services / Training / Advisory')
    """
    cursor.execute(query, (term_id, academic_rank))
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    ret_menu = {
        'research_required': 0,
        'extension_required': 0,
        'research_indicators': [],
        'extension_indicators': []
    }

    if not results:
        return ret_menu

    for r in results:
        if r['category_name'] == 'A. Research':
            ret_menu['research_required'] = int(r['required_selections'])
            ret_menu['research_indicators'].append(r)
        elif r['category_name'] == 'B. Extension Services / Training / Advisory':
            ret_menu['extension_required'] = int(r['required_selections'])
            ret_menu['extension_indicators'].append(r)

    return ret_menu


def save_faculty_ret_selections(conn, cursor, emp_id, term_id, selected_indicator_ids):
    try:
        # First, find RET category indicators for this term
        cursor.execute("""
            SELECT mi.indicator_id 
            FROM tbl_cascaded_quotas cq
            JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
            WHERE cq.term_id = %s AND cq.assigned_to_role IN (
                SELECT DISTINCT academic_rank FROM tbl_employee_profiles WHERE academic_rank IS NOT NULL AND academic_rank != ''
            )
        """, (term_id,))
        ret_indicator_ids = [row[0] for row in cursor.fetchall()]

        if ret_indicator_ids:
            format_strings = ','.join(['%s'] * len(ret_indicator_ids))
            delete_query = f"""
                DELETE FROM tbl_committed_targets 
                WHERE emp_id = %s AND indicator_id IN ({format_strings})
            """
            cursor.execute(delete_query, [emp_id] + ret_indicator_ids)

        # Insert new RET selections
        for ind_id in selected_indicator_ids:
            cursor.execute("""
                INSERT INTO tbl_committed_targets (emp_id, indicator_id, assigned_quantity, status)
                VALUES (%s, %s, 1, 'Draft')
            """, (emp_id, ind_id))

        conn.commit()
        return True, "RET selections saved."
    except Exception as e:
        conn.rollback()
        return False, str(e)


def submit_faculty_ipcr(conn, cursor, emp_id, term_id):
    try:
        cursor.execute("""
            UPDATE tbl_committed_targets ct
            JOIN tbl_master_indicators mi ON ct.indicator_id = mi.indicator_id
            SET ct.status = 'Pending Approval'
            WHERE ct.emp_id = %s AND mi.term_id = %s AND ct.status IN ('Draft', 'Pending Approval')
        """, (emp_id, term_id))
        conn.commit()
        return True, "IPCR successfully submitted for approval."
    except Exception as e:
        conn.rollback()
        return False, str(e)
