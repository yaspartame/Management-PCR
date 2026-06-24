def get_existing_cascaded_quotas(cursor, term_id):
    from app.models.connection import timed_query
    query = """
        SELECT cq.*, mi.indicator_description, tc.category_name
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE cq.term_id = %s
        ORDER BY mi.indicator_id
    """
    return timed_query(cursor, query, (term_id,), label="get_existing_cascaded_quotas")


def get_dean_dashboard_kpis(cursor, term_id):
    """
    Consolidated KPI query — replaces 3 separate round-trips
    (get_overall_completion + get_pending_approvals_count + get_top_performing_department)
    into a single query.
    """
    query = """
        SELECT
            COALESCE(
                ROUND(
                    (SUM(CASE WHEN ts.status = 'Approved' THEN 1 ELSE 0 END) 
                     / NULLIF(COUNT(*), 0)) * 100
                ), 0
            ) AS completion_rate,
            (SELECT COUNT(*) FROM tbl_final_scores fs2
             WHERE fs2.term_id = %s AND fs2.dean_approval_status = 'Pending') AS pending_count,
            COALESCE(
                (SELECT ep2.assigned_program
                 FROM tbl_final_scores fs3
                 JOIN tbl_employee_profiles ep2 ON fs3.emp_id = ep2.emp_id
                 WHERE fs3.term_id = %s AND fs3.dean_approval_status = 'Approved'
                 GROUP BY ep2.assigned_program
                 ORDER BY AVG(fs3.final_score) DESC
                 LIMIT 1),
                'N/A'
            ) AS top_dept
        FROM tbl_committed_targets ts
        JOIN tbl_master_indicators mi ON ts.indicator_id = mi.indicator_id
        WHERE mi.term_id = %s
    """
    from app.models.connection import timed_query
    result = timed_query(cursor, query, (term_id, term_id, term_id), label="dean_dashboard_kpis")
    if result:
        return result[0]['completion_rate'], result[0]['pending_count'], result[0]['top_dept']
    return 0, 0, "N/A"


def get_pending_final_approvals(cursor, term_id):
    from app.models.connection import timed_query
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
    return timed_query(cursor, query, (term_id,), label="get_pending_final_approvals")


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


# ──────────────────────────────────────────────
# Draft IPCR Review (Designated Faculty) Mika
# ──────────────────────────────────────────────

def get_designated_draft_submissions(cursor, term_id):
    """
    Get all designated faculty who have submitted draft IPCRs,
    grouped by faculty with summary info.
    """
    from app.models.connection import timed_query
    query = """
        SELECT 
            dt.emp_id,
            CONCAT(ep.first_name, ' ', ep.last_name) AS faculty_name,
            ep.academic_rank,
            ep.assigned_program,
            ep.designation,
            COUNT(dt.draft_id) AS total_targets,
            SUM(CASE WHEN dt.review_status = 'Pending Review' THEN 1 ELSE 0 END) AS pending_count,
            SUM(CASE WHEN dt.review_status = 'Approved' THEN 1 ELSE 0 END) AS approved_count,
            SUM(CASE WHEN dt.review_status = 'Rejected' THEN 1 ELSE 0 END) AS rejected_count,
            MAX(dt.review_status) AS overall_status
        FROM tbl_draft_targets dt
        JOIN tbl_employee_profiles ep ON dt.emp_id = ep.emp_id
        JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
        JOIN tbl_system_access sa ON dt.emp_id = sa.emp_id
        WHERE mi.term_id = %s
          AND sa.system_role = 'DESIGNATED_FACULTY'
          AND mi.is_custom IN (0, 1)
        GROUP BY dt.emp_id, ep.first_name, ep.last_name, ep.academic_rank, ep.assigned_program, ep.designation
        ORDER BY ep.last_name ASC
    """
    return timed_query(cursor, query, (term_id,), label="get_designated_draft_submissions")


def get_designated_faculty_draft_targets(cursor, emp_id, term_id):
    from app.models.connection import timed_query
    query = """
        SELECT 
            dt.draft_id,
            dt.indicator_id,
            dt.proposed_quantity,
            dt.review_status,
            mi.indicator_description,
            tc.category_name,
            mi.efficiency_type,
            mi.is_custom
        FROM tbl_draft_targets dt
        JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
        LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE dt.emp_id = %s AND mi.term_id = %s
        ORDER BY tc.category_name, mi.indicator_id
    """
    return timed_query(cursor, query, (emp_id, term_id), label="get_designated_faculty_draft_targets")


def update_draft_target_quantity(cursor, conn, draft_id, proposed_quantity):
    """Update the proposed quantity of a single draft target."""
    try:
        cursor.execute(
            "UPDATE tbl_draft_targets SET proposed_quantity = %s WHERE draft_id = %s",
            (proposed_quantity, draft_id)
        )
        conn.commit()
        return True, "Target quantity updated successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error updating target: {str(e)}"


def review_designated_draft(cursor, conn, emp_id, term_id, action, remarks):
    """
    Approve or reject ALL draft targets for a designated faculty member.
    action: 'Approved' or 'Rejected'
    """
    try:
        # Update all draft targets for this faculty in the current term
        cursor.execute("""
            UPDATE tbl_draft_targets dt
            JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
            SET dt.review_status = %s
            WHERE dt.emp_id = %s AND mi.term_id = %s
        """, (action, emp_id, term_id))
        conn.commit()
        return True, f"Draft IPCR successfully {action.lower()} with remarks."
    except Exception as e:
        conn.rollback()
        return False, f"Error reviewing draft: {str(e)}"


# ──────────────────────────────────────────────
# College-Wide Target Assignment (Designated Faculty) Mika
# ──────────────────────────────────────────────

def get_designated_faculty_list(cursor):
    """Get all active designated faculty members via system_access role."""
    from app.models.connection import timed_query
    query = """
        SELECT ep.emp_id, ep.first_name, ep.last_name, ep.academic_rank, ep.assigned_program, ep.specialization, ep.designation
        FROM tbl_employee_profiles ep
        JOIN tbl_system_access sa ON ep.emp_id = sa.emp_id
        WHERE sa.system_role = 'DESIGNATED_FACULTY' AND ep.leave_status = 'Active'
        ORDER BY ep.last_name ASC, ep.first_name ASC
    """
    return timed_query(cursor, query, label="get_designated_faculty_list")


def get_college_wide_cascaded_quotas(cursor, term_id):
    """
    Get indicators that have College-Wide quotas set in tbl_cascaded_quotas.
    """
    from app.models.connection import timed_query
    query = """
        SELECT cq.*, mi.indicator_description, tc.category_name, mi.efficiency_type
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE cq.term_id = %s AND cq.assigned_to_role = 'College-Wide' AND cq.total_target_value > 0
        ORDER BY tc.category_name, mi.indicator_id
    """
    return timed_query(cursor, query, (term_id,), label="get_college_wide_cascaded_quotas")


def get_designated_faculty_assignments(cursor, term_id, emp_id):
    """
    Get existing target assignments for a specific designated faculty member
    from tbl_draft_allocation.
    """
    from app.models.connection import timed_query
    query = """
        SELECT da.allocation_id, da.indicator_id, da.assigned_quantity,
               mi.indicator_description, tc.category_name
        FROM tbl_draft_allocation da
        JOIN tbl_master_indicators mi ON da.indicator_id = mi.indicator_id
        LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE mi.term_id = %s AND da.emp_id = %s
        ORDER BY tc.category_name, mi.indicator_id
    """
    return timed_query(cursor, query, (term_id, emp_id), label="get_designated_faculty_assignments")


def get_designated_faculty_assignments_batch(cursor, term_id, emp_ids):
    """
    Get target assignments for MULTIPLE designated faculty members in ONE query.
    Returns a dict: {emp_id: {indicator_id: assigned_quantity, ...}, ...}
    """
    if not emp_ids:
        return {}

    from app.models.connection import timed_query
    placeholders = ','.join(['%s'] * len(emp_ids))
    query = f"""
        SELECT da.emp_id, da.indicator_id, da.assigned_quantity
        FROM tbl_draft_allocation da
        JOIN tbl_master_indicators mi ON da.indicator_id = mi.indicator_id
        WHERE mi.term_id = %s AND da.emp_id IN ({placeholders})
    """
    rows = timed_query(cursor, query, [term_id] + emp_ids, label="get_designated_faculty_assignments_batch")

    result = {}
    for row in rows:
        emp_id = row['emp_id']
        if emp_id not in result:
            result[emp_id] = {}
        result[emp_id][row['indicator_id']] = row['assigned_quantity']
    return result


def save_designated_faculty_assignment(cursor, conn, term_id, emp_id, indicator_id, quantity):
    """Save or update a target assignment for a designated faculty member in tbl_draft_allocation."""
    try:
        # Check if an assignment already exists
        cursor.execute(
            "SELECT allocation_id FROM tbl_draft_allocation WHERE emp_id = %s AND indicator_id = %s",
            (emp_id, indicator_id)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "UPDATE tbl_draft_allocation SET assigned_quantity = %s WHERE allocation_id = %s",
                (quantity, existing[0])
            )
        else:
            cursor.execute(
                "INSERT INTO tbl_draft_allocation (emp_id, indicator_id, assigned_quantity) VALUES (%s, %s, %s)",
                (emp_id, indicator_id, quantity)
            )
        conn.commit()
        return True, "Assignment saved successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error saving assignment: {str(e)}"
