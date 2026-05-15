def get_ret_indicators(cursor, term_id):
    query = """
        SELECT mi.indicator_id, mi.indicator_description, mi.efficiency_type, tc.category_name, cq.total_target_value as dean_quota
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE cq.term_id = %s
          AND cq.assigned_to_role = 'RET / Extension'
        ORDER BY tc.category_name, mi.indicator_id
    """
    cursor.execute(query, (term_id,))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def save_ret_rule(conn, cursor, term_id, academic_rank, research_selections, extension_selections, research_indicator_ids, extension_indicator_ids):
    try:
        cursor.execute("""
            DELETE cq FROM tbl_cascaded_quotas cq
            JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
            JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
            WHERE cq.term_id = %s AND cq.assigned_to_role = %s 
              AND tc.category_name IN ('A. Research', 'B. Extension Services / Training / Advisory')
        """, (term_id, academic_rank))

        for ind_id in research_indicator_ids:
            cursor.execute("INSERT INTO tbl_cascaded_quotas (term_id, indicator_id, total_target_value, assigned_to_role) VALUES (%s, %s, %s, %s)",
                           (term_id, ind_id, research_selections, academic_rank))

        for ind_id in extension_indicator_ids:
            cursor.execute("INSERT INTO tbl_cascaded_quotas (term_id, indicator_id, total_target_value, assigned_to_role) VALUES (%s, %s, %s, %s)",
                           (term_id, ind_id, extension_selections, academic_rank))

        conn.commit()
        return True, "Menu configuration saved successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)


def get_ret_rules(cursor, term_id):
    cursor.execute("""
        SELECT cq.assigned_to_role, cq.total_target_value, mi.indicator_id, mi.indicator_description, tc.category_name
        FROM tbl_cascaded_quotas cq
        JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
        JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
        WHERE cq.term_id = %s AND cq.assigned_to_role IN (
            SELECT DISTINCT academic_rank FROM tbl_employee_profiles WHERE academic_rank IS NOT NULL AND academic_rank != ''
        ) AND tc.category_name IN ('A. Research', 'B. Extension Services / Training / Advisory')
    """, (term_id,))

    rows = cursor.fetchall()
    rules_dict = {}

    for r in rows:
        rank, required, ind_id, desc, category = r
        if rank not in rules_dict:
            rules_dict[rank] = {
                'rule_id': rank,
                'academic_rank': rank,
                'research_required': 0,
                'extension_required': 0,
                'research_indicators': [],
                'extension_indicators': []
            }

        if category == 'A. Research':
            rules_dict[rank]['research_required'] = required
            rules_dict[rank]['research_indicators'].append({'id': ind_id, 'desc': desc})
        elif category == 'B. Extension Services / Training / Advisory':
            rules_dict[rank]['extension_required'] = required
            rules_dict[rank]['extension_indicators'].append({'id': ind_id, 'desc': desc})

    return list(rules_dict.values())


def delete_ret_rule(conn, cursor, rule_id, category_type=None):
    try:
        if category_type == 'research':
            cursor.execute("""
                DELETE cq FROM tbl_cascaded_quotas cq
                JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
                JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
                WHERE cq.assigned_to_role = %s AND tc.category_name = 'A. Research'
            """, (rule_id,))
        elif category_type == 'extension':
            cursor.execute("""
                DELETE cq FROM tbl_cascaded_quotas cq
                JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
                JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
                WHERE cq.assigned_to_role = %s AND tc.category_name = 'B. Extension Services / Training / Advisory'
            """, (rule_id,))
        else:
            cursor.execute("""
                DELETE cq FROM tbl_cascaded_quotas cq
                JOIN tbl_master_indicators mi ON cq.indicator_id = mi.indicator_id
                JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
                WHERE cq.assigned_to_role = %s AND tc.category_name IN ('A. Research', 'B. Extension Services / Training / Advisory')
            """, (rule_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
