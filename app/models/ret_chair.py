def get_ret_indicators(cursor, term_id):
    from app.models.connection import timed_query
    query = """
        SELECT mi.indicator_id, mi.indicator_description, mi.efficiency_type, tc.category_name, cq.total_target_value as dean_quota
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE cq.term_id = %s
          AND cq.assigned_to_role = 'RET / Extension'
        ORDER BY tc.category_name, mi.indicator_id
    """
    return timed_query(cursor, query, (term_id,), label="get_ret_indicators")


def save_ret_rule(conn, cursor, term_id, academic_rank, research_selections, extension_selections, research_indicators, extension_indicators):
    try:
        # 1. Clean up existing rules for this academic rank to avoid conflicts
        cursor.execute("SELECT rule_id FROM tbl_ret_rules WHERE academic_rank = %s", (academic_rank,))
        rule_ids = [row[0] for row in cursor.fetchall()]
        if rule_ids:
            format_strings = ','.join(['%s'] * len(rule_ids))
            cursor.execute(f"DELETE FROM tbl_ret_rule_indicators WHERE rule_id IN ({format_strings})", tuple(rule_ids))
            cursor.execute(f"DELETE FROM tbl_ret_rules WHERE rule_id IN ({format_strings})", tuple(rule_ids))

        # 2. Save Research rule (if indicators are selected)
        if research_indicators and int(research_selections) > 0:
            cursor.execute("INSERT INTO tbl_ret_rules (academic_rank, required_selections) VALUES (%s, %s)", 
                           (academic_rank, int(research_selections)))
            res_rule_id = cursor.lastrowid
            for ind_id, qty in research_indicators:
                cursor.execute("INSERT INTO tbl_ret_rule_indicators (rule_id, indicator_id, target_quantity) VALUES (%s, %s, %s)", 
                               (res_rule_id, ind_id, qty))

        # 3. Save Extension rule (if indicators are selected)
        if extension_indicators and int(extension_selections) > 0:
            cursor.execute("INSERT INTO tbl_ret_rules (academic_rank, required_selections) VALUES (%s, %s)", 
                           (academic_rank, int(extension_selections)))
            ext_rule_id = cursor.lastrowid
            for ind_id, qty in extension_indicators:
                cursor.execute("INSERT INTO tbl_ret_rule_indicators (rule_id, indicator_id, target_quantity) VALUES (%s, %s, %s)", 
                               (ext_rule_id, ind_id, qty))

        conn.commit()
        return True, "Menu configuration saved successfully to structural rules templates."
    except Exception as e:
        conn.rollback()
        return False, str(e)


def get_ret_rules(cursor, term_id):
    from app.models.connection import timed_query
    query = """
        SELECT r.rule_id, r.academic_rank, r.required_selections, mi.indicator_id, mi.indicator_description, tc.category_name, rri.target_quantity
        FROM tbl_ret_rules r
        JOIN tbl_ret_rule_indicators rri ON r.rule_id = rri.rule_id
        JOIN tbl_master_indicators mi ON rri.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE mi.term_id = %s
    """
    return timed_query(cursor, query, (term_id,), label="get_ret_rules")
    rows = cursor.fetchall()
    rules_dict = {}

    for r in rows:
        rule_id, rank, required, ind_id, desc, category, qty = r
        if rank not in rules_dict:
            rules_dict[rank] = {
                'rule_id': rank,  # Use rank string as rule_id for frontend delete forms
                'academic_rank': rank,
                'research_required': 0, 
                'extension_required': 0,
                'research_indicators': [],
                'extension_indicators': []
            }

        if category == 'A. Research':
            rules_dict[rank]['research_required'] = required
            rules_dict[rank]['research_indicators'].append({'id': ind_id, 'desc': desc, 'qty': qty})
        elif category == 'B. Extension Services / Training / Advisory':
            rules_dict[rank]['extension_required'] = required
            rules_dict[rank]['extension_indicators'].append({'id': ind_id, 'desc': desc, 'qty': qty})

    return list(rules_dict.values())


def delete_ret_rule(conn, cursor, rule_id, category_type=None):
    try:
        # Note: rule_id is passed as the academic_rank string from the frontend delete form
        academic_rank = rule_id
        cursor.execute("SELECT rule_id FROM tbl_ret_rules WHERE academic_rank = %s", (academic_rank,))
        rule_ids = [row[0] for row in cursor.fetchall()]
        if rule_ids:
            format_strings = ','.join(['%s'] * len(rule_ids))
            cursor.execute(f"DELETE FROM tbl_ret_rule_indicators WHERE rule_id IN ({format_strings})", tuple(rule_ids))
            cursor.execute(f"DELETE FROM tbl_ret_rules WHERE rule_id IN ({format_strings})", tuple(rule_ids))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
