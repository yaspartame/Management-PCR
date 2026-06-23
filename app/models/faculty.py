def get_faculty_assigned_targets(cursor, emp_id, term_id):
    # Check if locked (committed targets exist)
    cursor.execute("""
        SELECT COUNT(*) FROM tbl_committed_targets ct
        JOIN tbl_master_indicators mi ON ct.indicator_id = mi.indicator_id
        WHERE ct.emp_id = %s AND mi.term_id = %s
    """, (emp_id, term_id))
    is_locked = cursor.fetchone()[0] > 0

    if is_locked:
        # Load from tbl_committed_targets
        query = """
            SELECT ct.target_id, ct.indicator_id,
                   ct.assigned_quantity,
                   ct.status,
                   mi.indicator_description, tc.category_name,
                   NULL as chair_item_remarks,
                   NULL as chair_reviewed_quantity
            FROM tbl_committed_targets ct
            JOIN tbl_master_indicators mi ON ct.indicator_id = mi.indicator_id
            LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
            WHERE ct.emp_id = %s AND mi.term_id = %s
            ORDER BY tc.category_name, mi.indicator_id
        """
        cursor.execute(query, (emp_id, term_id))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Check if this user has already submitted their targets to the review registry
    cursor.execute("""
        SELECT COUNT(*) FROM tbl_draft_targets dt
        JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
        WHERE dt.emp_id = %s AND mi.term_id = %s
    """, (emp_id, term_id))
    has_submitted = cursor.fetchone()[0] > 0

    if has_submitted:
        # Load from tbl_draft_targets, also surface any per-item chair remarks
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
        # Load pre-assigned targets from Program Chair's tbl_draft_allocation
        query = """
            SELECT da.allocation_id as target_id, da.indicator_id, da.assigned_quantity, 'Draft' as status,
                   mi.indicator_description, tc.category_name,
                   NULL as chair_item_remarks, NULL as chair_reviewed_quantity
            FROM tbl_draft_allocation da
            JOIN tbl_master_indicators mi ON da.indicator_id = mi.indicator_id
            LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
            WHERE da.emp_id = %s AND mi.term_id = %s
            ORDER BY tc.category_name, mi.indicator_id
        """
    cursor.execute(query, (emp_id, term_id))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


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
    query = """
        SELECT r.required_selections, mi.indicator_id, mi.indicator_description, tc.category_name
        FROM tbl_ret_rules r
        JOIN tbl_ret_rule_indicators rri ON r.rule_id = rri.rule_id
        JOIN tbl_master_indicators mi ON rri.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE r.academic_rank = %s AND mi.term_id = %s
    """
    cursor.execute(query, (academic_rank, term_id))
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

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
        # 1. Sync any reviewed quantities from the chair's decision back into tbl_draft_targets FIRST
        # to preserve any adjustments made by the Program Chair on standard workloads.
        cursor.execute("""
            UPDATE tbl_draft_targets dt
            JOIN tbl_ipcr_chair_review cr ON dt.emp_id = cr.emp_id
            JOIN tbl_ipcr_chair_review_items ri ON ri.review_id = cr.review_id AND ri.indicator_id = dt.indicator_id
            SET dt.proposed_quantity = ri.reviewed_quantity
            WHERE dt.emp_id = %s
        """, (emp_id,))

        # 2. Gather all assigned regular workloads distributed by the Program Chair (if any)
        cursor.execute("""
            SELECT indicator_id, assigned_quantity 
            FROM tbl_draft_allocation 
            WHERE emp_id = %s
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
                cursor.execute("""
                    UPDATE tbl_draft_targets 
                    SET proposed_quantity = %s, review_status = 'Pending Review' 
                    WHERE draft_id = %s
                """, (qty, existing_draft[0]))
            else:
                cursor.execute("""
                    INSERT INTO tbl_draft_targets (emp_id, indicator_id, proposed_quantity, review_status)
                    VALUES (%s, %s, %s, 'Pending Review')
                """, (emp_id, ind_id, qty))

        # 4. If this is a re-submission, reset the status of existing standard workloads (not research/extension) to 'Pending Review'
        cursor.execute("""
            UPDATE tbl_draft_targets dt
            JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
            JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
            SET dt.review_status = 'Pending Review'
            WHERE dt.emp_id = %s
              AND tc.category_name IN ('A. Instructions', 'Support Functions')
        """, (emp_id,))

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
            res_qty = target['proposed_quantity']

            cursor.execute("""
                INSERT INTO tbl_draft_targets (emp_id, indicator_id, proposed_quantity, review_status)
                VALUES (%s, %s, %s, 'Pending Review')
            """, (emp_id, res_ind_id, res_qty))

        # 7. Success — Flush out temporary allocation staging for this employee
        cursor.execute("DELETE FROM tbl_draft_allocation WHERE emp_id = %s", (emp_id,))

        # 8. Clear any existing Program Chair review records so the chair sees a fresh 'Pending' submission
        cursor.execute("""
            DELETE ri FROM tbl_ipcr_chair_review_items ri
            JOIN tbl_ipcr_chair_review cr ON ri.review_id = cr.review_id
            WHERE cr.emp_id = %s
        """, (emp_id,))
        cursor.execute("""
            DELETE FROM tbl_ipcr_chair_review WHERE emp_id = %s
        """, (emp_id,))

        conn.commit()
        return True, "IPCR successfully submitted for review."
    except Exception as e:
        conn.rollback()
        return False, str(e)
