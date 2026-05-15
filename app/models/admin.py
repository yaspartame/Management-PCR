def get_admin_kpis(cursor):
    kpis = {
        'claimed_accounts': 0,
        'total_roster': 0,
        'adoption_rate': 0,
        'term_status': "No Active Term"
    }

    # KPI 1: Roster Adoption Rate
    cursor.execute("SELECT COUNT(emp_id) FROM tbl_employee_profiles")
    roster_res = cursor.fetchone()
    kpis['total_roster'] = roster_res[0] if roster_res and roster_res[0] else 0

    cursor.execute("SELECT COUNT(emp_id) FROM tbl_auth_credentials")
    claimed_res = cursor.fetchone()
    kpis['claimed_accounts'] = claimed_res[0] if claimed_res and claimed_res[0] else 0

    if kpis['total_roster'] > 0:
        kpis['adoption_rate'] = round((kpis['claimed_accounts'] / kpis['total_roster']) * 100)

    # KPI 2: Term Deadline (Days Remaining)
    cursor.execute("SELECT DATEDIFF(deadline_date, CURDATE()) FROM tbl_academic_terms WHERE is_active = TRUE LIMIT 1")
    term_result = cursor.fetchone()

    if term_result is not None:
        if term_result[0] is not None:
            days = term_result[0]
            if days < 0:
                kpis['term_status'] = "Deadline Passed"
            else:
                kpis['term_status'] = f"{days} Days Remaining"
        else:
            kpis['term_status'] = "No Deadline Set"

    return kpis
