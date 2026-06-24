def open_new_term(conn, cursor, academic_year, semester, deadline_date):
    try:
        # Deactivate all current terms
        cursor.execute("UPDATE tbl_academic_terms SET is_active = FALSE")

        # Insert and activate the new term
        query_open = """
            INSERT INTO tbl_academic_terms (academic_year, semester, deadline_date, is_active)
            VALUES (%s, %s, %s, TRUE)
        """
        cursor.execute(query_open, (academic_year, semester, deadline_date))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e


def get_all_terms(cursor):
    from app.models.connection import timed_query
    query = "SELECT term_id, academic_year, semester, deadline_date, is_active FROM tbl_academic_terms ORDER BY term_id DESC"
    return timed_query(cursor, query, label="get_all_terms")
