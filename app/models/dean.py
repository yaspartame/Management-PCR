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
