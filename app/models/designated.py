def get_designated_cascaded_quotas(cursor, term_id):
    """Fetches targets assigned by the Dean/Admin (YOUR ORIGINAL CODE)"""
    query = """
        SELECT cq.*, mi.indicator_description, tc.category_name
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE cq.term_id = %s
          AND tc.category_name IN ('Support Functions', 'A. Instructions')
        ORDER BY mi.indicator_id
    """
    cursor.execute(query, (term_id,))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def insert_custom_target(cursor, emp_id, term_id, description, quantity, category):
    """Inserts a user-defined target from the pop-up modal"""
    query = """
        INSERT INTO tbl_individual_targets 
        (emp_id, term_id, description, target_qty, category, status) 
        VALUES (%s, %s, %s, %s, %s, 'Pending')
    """
    cursor.execute(query, (emp_id, term_id, description, quantity, category))
    return cursor.rowcount > 0