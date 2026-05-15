from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from app.models import *
from app.decorators import role_required

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')


@faculty_bp.route('/')
@role_required('FACULTY')
def faculty_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    emp_id = session.get('user_id')

    cursor.execute("SELECT academic_rank, specialization FROM tbl_employee_profiles WHERE emp_id = %s", (emp_id,))
    emp_profile = cursor.fetchone()
    academic_rank = emp_profile[0] if emp_profile else ''
    specialization = emp_profile[1] if emp_profile else ''

    terms = get_all_terms(cursor)
    active_term = next((t for t in terms if t['is_active'] == 1), None)

    assigned_targets = []
    ret_menu = {'required_selections': 0, 'indicators': []}
    has_submitted = False

    if active_term:
        term_id = active_term['term_id']
        assigned_targets = get_faculty_assigned_targets(cursor, emp_id, term_id)
        if academic_rank:
            ret_menu = get_faculty_ret_menu(cursor, academic_rank, term_id)

        for t in assigned_targets:
            if t['status'] == 'Pending Approval':
                has_submitted = True
                break

    cursor.close()
    conn.close()

    return render_template('faculty_dashboard.html',
                           active_term=active_term,
                           assigned_targets=assigned_targets,
                           ret_menu=ret_menu,
                           academic_rank=academic_rank,
                           specialization=specialization,
                           has_submitted=has_submitted)


@faculty_bp.route('/submit_ipcr', methods=['POST'])
@role_required('FACULTY')
def faculty_submit_ipcr():
    emp_id = session.get('user_id')
    term_id = request.form.get('term_id')
    selected_indicators = request.form.getlist('ret_indicators[]')

    if not term_id:
        flash("No active term.", "danger")
        return redirect(url_for('faculty.faculty_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if selected_indicators:
            save_faculty_ret_selections(conn, cursor, emp_id, int(term_id), [int(x) for x in selected_indicators])

        success, msg = submit_faculty_ipcr(conn, cursor, emp_id, int(term_id))

        if success:
            flash(msg, "success")
        else:
            flash(msg, "danger")

    except Exception as e:
        flash(f"Error submitting IPCR: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('faculty.faculty_dashboard'))
