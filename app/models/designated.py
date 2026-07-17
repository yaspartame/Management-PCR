def get_designated_selectable_indicators(cursor, term_id):
    """
    Retrieves the standard baseline list of available Instruction and Support functions.
    """
    from app.models.connection import timed_query
    query = """
        SELECT mi.indicator_id, mi.indicator_description, tc.category_name
        FROM tbl_master_indicators mi
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE mi.term_id = %s 
          AND mi.is_custom = 0
          AND tc.category_name IN ('A. Instructions', 'Support Functions')
        ORDER BY tc.category_name, mi.indicator_id
    """
    return timed_query(cursor, query, (term_id,), label="get_designated_selectable_indicators")


def submit_designated_ipcr(conn, cursor, emp_id, term_id, selected_targets, custom_targets):
    """
    Transactionally processes standard baseline selections and inserts custom ad-hoc targets 
    upstream before compiling all submissions securely inside tbl_draft_targets.
    Also resets any prior Dean review so the Dean can review again.
    
    selected_targets: [{'indicator_id': int, 'proposed_quantity': int}]
    custom_targets: [{'description': str, 'proposed_quantity': int}]
    """
    try:
        # 0. Clear any prior Dean review so Dean can re-review fresh
        cursor.execute(
            "SELECT review_id FROM tbl_ipcr_dean_review WHERE emp_id = %s AND term_id = %s",
            (emp_id, term_id)
        )
        old_review = cursor.fetchone()
        if old_review:
            old_review_id = old_review[0]
            cursor.execute("DELETE FROM tbl_ipcr_dean_review_items WHERE review_id = %s", (old_review_id,))
            cursor.execute("DELETE FROM tbl_ipcr_dean_review WHERE review_id = %s", (old_review_id,))

        # 1. Clear any prior unverified submissions for this profile to prevent key errors
        cursor.execute("DELETE FROM tbl_draft_targets WHERE emp_id = %s", (emp_id,))

        # 2. Process Standard Baseline Selected Targets
        for target in selected_targets:
            cursor.execute("""
                INSERT INTO tbl_draft_targets (emp_id, indicator_id, proposed_quantity, review_status)
                VALUES (%s, %s, %s, 'Pending Review')
            """, (emp_id, target['indicator_id'], target['proposed_quantity']))

        # 3. Process Custom Ad-Hoc Target Items
        for custom in custom_targets:
            text_clean = custom['description'].strip()
            qty = custom['proposed_quantity']
            if not text_clean:
                continue

            # Step A: Identify or provision the specific category block dynamically
            cat_name = custom.get('category_name', 'Support Functions')
            cursor.execute("SELECT category_id FROM tbl_target_categories WHERE category_name = %s", (cat_name,))
            cat_row = cursor.fetchone()
            if cat_row:
                category_id = cat_row[0]
            else:
                cursor.execute("INSERT INTO tbl_target_categories (category_name) VALUES (%s)", (cat_name,))
                category_id = cursor.lastrowid

            # Step B: Upstream runtime injection into master indicators (Explicitly flagged as is_custom = 1)
            # Reuses existing indicator if description, term_id, category_id, and is_custom match
            cursor.execute("""
                SELECT indicator_id FROM tbl_master_indicators 
                WHERE indicator_description = %s AND term_id = %s AND category_id = %s AND is_custom = 1
            """, (text_clean, term_id, category_id))
            existing_ind = cursor.fetchone()
            if existing_ind:
                new_indicator_id = existing_ind[0]
            else:
                cursor.execute("""
                    INSERT INTO tbl_master_indicators (category_id, indicator_description, efficiency_type, term_id, is_custom)
                    VALUES (%s, %s, 'Output-Based', %s, 1)
                """, (category_id, text_clean, term_id))
                new_indicator_id = cursor.lastrowid

            # Step C: Downstream projection into the unified draft staging table via the generated relational ID
            cursor.execute("""
                INSERT INTO tbl_draft_targets (emp_id, indicator_id, proposed_quantity, review_status)
                VALUES (%s, %s, %s, 'Pending Review')
            """, (emp_id, new_indicator_id, qty))

        conn.commit()
        return True, "Designated IPCR successfully compiled and submitted to Draft Targets for verification review."
    except Exception as e:
        conn.rollback()
        return False, str(e)