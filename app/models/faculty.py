def get_faculty_assigned_targets(cursor, emp_id, term_id):
    from app.models.connection import timed_query
    # Check if this user has already submitted their targets to the review registry
    count_result = timed_query(cursor, """
        SELECT COUNT(*) as cnt FROM tbl_draft_targets dt
        JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
        WHERE dt.emp_id = %s AND mi.term_id = %s
    """, (emp_id, term_id), label="get_faculty_assigned_targets_check")
    has_submitted = count_result[0]['cnt'] > 0 if count_result else False

    if has_submitted:
        query = """
            SELECT dt.draft_id as target_id, dt.indicator_id,
                   COALESCE(
                       CASE WHEN cr.overall_status IN ('Approved', 'Rejected') THEN ri.reviewed_quantity ELSE NULL END,
                       dt.proposed_quantity
                   ) as assigned_quantity,
                   dt.review_status as status,
                   mi.indicator_description, tc.category_name,
                   ri.item_remarks as chair_item_remarks,
                   ri.reviewed_quantity as chair_reviewed_quantity
            FROM tbl_draft_targets dt
            JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
            LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
            LEFT JOIN tbl_ipcr_chair_review cr
                ON cr.emp_id = dt.emp_id AND cr.term_id = mi.term_id
            LEFT JOIN tbl_ipcr_chair_review_items ri
                ON ri.review_id = cr.review_id AND ri.draft_id = dt.draft_id
            WHERE dt.emp_id = %s AND mi.term_id = %s
            ORDER BY tc.category_name, mi.indicator_id
        """
    else:
        query = """
            SELECT MIN(da.allocation_id) as target_id, da.indicator_id, MAX(da.assigned_quantity) as assigned_quantity, 'Draft' as status,
                   mi.indicator_description, tc.category_name,
                   NULL as chair_item_remarks, NULL as chair_reviewed_quantity
            FROM tbl_draft_allocation da
            JOIN tbl_master_indicators mi ON da.indicator_id = mi.indicator_id
            LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
            JOIN tbl_employee_profiles ep ON da.emp_id = ep.emp_id
            WHERE ep.specialization = (SELECT specialization FROM tbl_employee_profiles WHERE emp_id = %s)
              AND mi.term_id = %s
            GROUP BY da.indicator_id, mi.indicator_description, tc.category_name
            ORDER BY tc.category_name, da.indicator_id
        """
    return timed_query(cursor, query, (emp_id, term_id), label="get_faculty_assigned_targets_load")


def get_faculty_chair_review_status(cursor, emp_id, term_id):
    """
    Returns the Program Chair's current review record for this faculty member,
    or None if no review has been started yet.
    Used by the faculty dashboard to display the 'Returned' alert with remarks.
    """
    cursor.execute("""
        SELECT review_id, overall_status, overall_remarks, reviewed_at
        FROM tbl_ipcr_chair_review
        WHERE emp_id = %s AND term_id = %s
    """, (emp_id, term_id))
    row = cursor.fetchone()
    if row:
        return {
            'review_id':      row[0],
            'overall_status': row[1],
            'overall_remarks': row[2],
            'reviewed_at':    row[3],
        }
    return None


def get_faculty_ret_menu(cursor, academic_rank, term_id):
    from app.models.connection import timed_query
    query = """
        SELECT r.required_selections, mi.indicator_id, mi.indicator_description, tc.category_name, rri.target_quantity
        FROM tbl_ret_rules r
        JOIN tbl_ret_rule_indicators rri ON r.rule_id = rri.rule_id
        JOIN tbl_master_indicators mi ON rri.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE r.academic_rank = %s AND mi.term_id = %s
    """
    results = timed_query(cursor, query, (academic_rank, term_id), label="get_faculty_ret_menu")

    ret_menu = {
        'research_required': 0,
        'extension_required': 0,
        'research_indicators': [],
        'extension_indicators': []
    }

    for r in results:
        if r['category_name'] == 'A. Research':
            ret_menu['research_required'] = int(r['required_selections'])
            ret_menu['research_indicators'].append(r)
        elif r['category_name'] == 'B. Extension Services / Training / Advisory':
            ret_menu['extension_required'] = int(r['required_selections'])
            ret_menu['extension_indicators'].append(r)

    return ret_menu


def save_faculty_ret_selections(conn, cursor, emp_id, term_id, selected_indicator_ids):
    # This helper is deprecated as RET selections are processed inside the submit pipeline,
    # but we keep a dummy return for backward compatibility.
    return True, "RET selections processed."


def submit_faculty_ipcr(conn, cursor, emp_id, selected_research_targets):
    """
    selected_research_targets parameter format:
    [
        {'indicator_id': 12, 'proposed_quantity': 1},
        ...
    ]
    """
    try:
        # Check if they are resubmitting (meaning a review record already exists for the active term)
        cursor.execute("SELECT term_id FROM tbl_academic_terms WHERE is_active = 1 LIMIT 1")
        term_row = cursor.fetchone()
        active_term_id = term_row[0] if term_row else None

        is_resubmission = False
        if active_term_id:
            cursor.execute("""
                SELECT 1 FROM tbl_ipcr_chair_review 
                WHERE emp_id = %s AND term_id = %s
                LIMIT 1
            """, (emp_id, active_term_id))
            is_resubmission = cursor.fetchone() is not None

        target_status = 'Waiting for Approval' if is_resubmission else 'Pending Review'

        # 1. Sync any reviewed quantities from the chair's decision back into tbl_draft_targets FIRST
        # to preserve any adjustments made by the Program Chair on standard workloads.
        cursor.execute("""
            UPDATE tbl_draft_targets dt
            JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
            JOIN tbl_ipcr_chair_review cr ON dt.emp_id = cr.emp_id AND cr.term_id = mi.term_id
            JOIN tbl_ipcr_chair_review_items ri ON ri.review_id = cr.review_id AND ri.draft_id = dt.draft_id
            SET dt.proposed_quantity = ri.reviewed_quantity
            WHERE dt.emp_id = %s
        """, (emp_id,))

        # 2. Gather all assigned regular workloads distributed by the Program Chair for this specialization (if any)
        cursor.execute("""
            SELECT da.indicator_id, MAX(da.assigned_quantity)
            FROM tbl_draft_allocation da
            JOIN tbl_employee_profiles ep ON da.emp_id = ep.emp_id
            WHERE ep.specialization = (SELECT specialization FROM tbl_employee_profiles WHERE emp_id = %s)
            GROUP BY da.indicator_id
        """, (emp_id,))
        chair_allocations = cursor.fetchall()

        # 3. Process and migrate standard workloads into tbl_draft_targets
        for ind_id, qty in chair_allocations:
            cursor.execute("""
                SELECT draft_id FROM tbl_draft_targets 
                WHERE emp_id = %s AND indicator_id = %s
            """, (emp_id, ind_id))
            existing_draft = cursor.fetchone()

            if existing_draft:
                # To prevent overwriting the Program Chair's custom-reviewed target quantities,
                # we check if a review item exists for this draft. If it does, we preserve the
                # synced proposed_quantity instead of resetting it to tbl_draft_allocation baseline.
                cursor.execute("""
                    SELECT 1 FROM tbl_ipcr_chair_review_items ri
                    JOIN tbl_ipcr_chair_review cr ON ri.review_id = cr.review_id
                    WHERE cr.emp_id = %s AND ri.draft_id = %s
                    LIMIT 1
                """, (emp_id, existing_draft[0]))
                has_review_item = cursor.fetchone() is not None

                if has_review_item:
                    cursor.execute("""
                        UPDATE tbl_draft_targets 
                        SET review_status = %s 
                        WHERE draft_id = %s
                    """, (target_status, existing_draft[0]))
                else:
                    cursor.execute("""
                        UPDATE tbl_draft_targets 
                        SET proposed_quantity = %s, review_status = %s 
                        WHERE draft_id = %s
                    """, (qty, target_status, existing_draft[0]))
            else:
                cursor.execute("""
                    INSERT INTO tbl_draft_targets (emp_id, indicator_id, proposed_quantity, review_status)
                    VALUES (%s, %s, %s, %s)
                """, (emp_id, ind_id, qty, target_status))

        # 4. If this is a re-submission, reset the status of existing standard workloads (not research/extension) to target_status
        cursor.execute("""
            UPDATE tbl_draft_targets dt
            JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
            JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
            SET dt.review_status = %s
            WHERE dt.emp_id = %s
              AND tc.category_name IN ('A. Instructions', 'Support Functions')
        """, (target_status, emp_id))

        # 4b. Check if Research & Extension targets are editable by the faculty member.
        # They are only editable on first submission or when returned (Rejected) by the RET Chair.
        # Otherwise, they are locked/disabled in the UI, and we must preserve the existing selections.
        ret_editable = True
        if is_resubmission and active_term_id:
            cursor.execute(
                """
                SELECT overall_status FROM tbl_ipcr_ret_review 
                WHERE emp_id = %s AND term_id = %s
                """,
                (emp_id, active_term_id)
            )
            ret_row = cursor.fetchone()
            ret_status = ret_row[0] if ret_row else 'Pending'
            if ret_status != 'Rejected':
                ret_editable = False

        if ret_editable:
            # 5. Delete existing Research and Extension targets for this employee from tbl_draft_targets
            # to ensure that any deselected targets are not carried over.
            cursor.execute("""
                DELETE dt FROM tbl_draft_targets dt
                JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
                JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
                WHERE dt.emp_id = %s
                  AND tc.category_name IN ('A. Research', 'B. Extension Services / Training / Advisory')
            """, (emp_id,))

            # 6. Process and write the new faculty self-selected Research/Extension targets into tbl_draft_targets
            for target in selected_research_targets:
                res_ind_id = target['indicator_id']
                
                # Fetch target quantity configured by RET Chair
                cursor.execute("""
                    SELECT rri.target_quantity 
                    FROM tbl_ret_rule_indicators rri
                    JOIN tbl_ret_rules r ON rri.rule_id = r.rule_id
                    JOIN tbl_employee_profiles ep ON ep.academic_rank = r.academic_rank
                    WHERE ep.emp_id = %s AND rri.indicator_id = %s
                    LIMIT 1
                """, (emp_id, res_ind_id))
                row = cursor.fetchone()
                res_qty = row[0] if (row and row[0] is not None) else 1

                cursor.execute("""
                    INSERT INTO tbl_draft_targets (emp_id, indicator_id, proposed_quantity, review_status)
                    VALUES (%s, %s, %s, %s)
                """, (emp_id, res_ind_id, res_qty, target_status))

        # 8. Update existing Program Chair review records for active term to 'Pending' and clear items/remarks
        if active_term_id and is_resubmission:
            cursor.execute("""
                SELECT review_id FROM tbl_ipcr_chair_review 
                WHERE emp_id = %s AND term_id = %s
            """, (emp_id, active_term_id))
            existing_review = cursor.fetchone()
            if existing_review:
                review_id = existing_review[0]
                # Delete ONLY Research and Extension review items to preserve standard workload adjustments
                cursor.execute("""
                    DELETE ri FROM tbl_ipcr_chair_review_items ri
                    JOIN tbl_master_indicators mi ON ri.indicator_id = mi.indicator_id
                    JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
                    WHERE ri.review_id = %s
                      AND tc.category_name IN ('A. Research', 'B. Extension Services / Training / Advisory')
                """, (review_id,))
                cursor.execute("""
                    UPDATE tbl_ipcr_chair_review
                    SET overall_status = 'Pending',
                        overall_remarks = NULL,
                        reviewed_at = NULL
                    WHERE review_id = %s
                """, (review_id,))

        # 8b. Reset RET Chair review record and items if it exists for active term and is editable
        if active_term_id and ret_editable:
            cursor.execute("""
                SELECT review_id FROM tbl_ipcr_ret_review
                WHERE emp_id = %s AND term_id = %s
            """, (emp_id, active_term_id))
            existing_ret_review = cursor.fetchone()
            if existing_ret_review:
                ret_review_id = existing_ret_review[0]
                cursor.execute("DELETE FROM tbl_ipcr_ret_review_items WHERE review_id = %s", (ret_review_id,))
                cursor.execute("""
                    UPDATE tbl_ipcr_ret_review
                    SET overall_status = 'Pending',
                        overall_remarks = NULL,
                        reviewed_at = NULL
                    WHERE review_id = %s
                """, (ret_review_id,))

        conn.commit()
        return True, "IPCR successfully submitted for review."
    except Exception as e:
        conn.rollback()
        return False, str(e)
