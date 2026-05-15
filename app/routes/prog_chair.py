from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from app.models import *
from app.decorators import role_required

prog_chair_bp = Blueprint('prog_chair', __name__, url_prefix='/prog_chair')


@prog_chair_bp.route('/')
@role_required('PROGRAM_CHAIR')
def prog_chair_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    specialization = session.get('specialization')
    if not specialization:
        cursor.execute("SELECT specialization FROM tbl_employee_profiles WHERE emp_id = %s", (session.get('user_id'),))
        spec_rows = cursor.fetchall()
        specialization = spec_rows[0][0] if spec_rows else ''
        session['specialization'] = specialization

    if not specialization:
        flash("Your account does not have a designated specialization. Please contact HR/Admin.", "warning")

    try:
        terms = get_all_terms(cursor)
        active_term = next((t for t in terms if t['is_active'] == 1), None)

        indicators = []
        faculty_count = 0
        faculty_list = []

        if active_term and specialization:
            indicators = get_chair_indicators(cursor, active_term['term_id'], specialization)
            faculty_list = get_specialization_faculty(cursor, specialization)
            faculty_count = len(faculty_list)
            faculty_ids = [f['emp_id'] for f in faculty_list]

            for ind in indicators:
                assigned_qty = get_assigned_quantity(cursor, active_term['term_id'], ind['indicator_id'], faculty_ids)
                ind['assigned_per_faculty'] = assigned_qty
                ind['total_distributed'] = assigned_qty * faculty_count

        return render_template('prog_chair_dashboard.html',
                               active_term=active_term,
                               specialization=specialization,
                               indicators=indicators,
                               faculty_count=faculty_count)
    finally:
        cursor.close()
        conn.close()


@prog_chair_bp.route('/assign_target', methods=['POST'])
@role_required('PROGRAM_CHAIR')
def assign_chair_target():
    specialization = session.get('specialization')
    term_id = request.form.get('term_id')
    indicator_id = request.form.get('indicator_id')
    assigned_quantity = request.form.get('assigned_quantity')

    if not specialization or not term_id or not indicator_id or not assigned_quantity:
        flash("Missing required data for assignment.", "danger")
        return redirect(url_for('prog_chair.prog_chair_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        faculty_list = get_specialization_faculty(cursor, specialization)
        faculty_ids = [f['emp_id'] for f in faculty_list]

        success, msg = save_chair_allocation(conn, cursor, int(term_id), int(indicator_id), int(assigned_quantity),
                                              faculty_ids)
        if success:
            flash(msg, "success")
        else:
            flash(msg, "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('prog_chair.prog_chair_dashboard'))
