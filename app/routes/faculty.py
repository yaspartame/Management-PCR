from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from app.models import *
from app.decorators import role_required

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')


@faculty_bp.route('/')
@role_required('FACULTY')
def faculty_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    from app.models.connection import timed_query

    emp_id = session.get('user_id')

    emp_result = timed_query(cursor, "SELECT academic_rank, specialization FROM tbl_employee_profiles WHERE emp_id = %s", (emp_id,), label="faculty_profile")
    academic_rank = emp_result[0]['academic_rank'] if emp_result else ''
    specialization = emp_result[0]['specialization'] if emp_result else ''

    terms = get_all_terms(cursor)
    active_term = next((t for t in terms if t['is_active'] == 1), None)

    assigned_targets = []
    ret_menu = {'required_selections': 0, 'indicators': []}
    has_submitted = False
    is_locked = False
    chair_review = None

    if active_term:
        term_id = active_term['term_id']
        assigned_targets = get_faculty_assigned_targets(cursor, emp_id, term_id)
        if academic_rank:
            ret_menu = get_faculty_ret_menu(cursor, academic_rank, term_id)

        # Check if the faculty member has submitted
        sub_result = timed_query(cursor, """
            SELECT COUNT(*) as cnt
            FROM tbl_draft_targets dt
            JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
            WHERE dt.emp_id = %s AND mi.term_id = %s AND dt.review_status = 'Pending Review'
        """, (emp_id, term_id), label="faculty_submit_check")
        has_submitted = sub_result[0]['cnt'] > 0 if sub_result else False

        # Fetch the Program Chair's review decision (if any)
        chair_review = get_faculty_chair_review_status(cursor, emp_id, term_id)

        # Check if locked
        cursor.execute("""
            SELECT COUNT(*) FROM tbl_committed_targets ct
            JOIN tbl_master_indicators mi ON ct.indicator_id = mi.indicator_id
            WHERE ct.emp_id = %s AND mi.term_id = %s
        """, (emp_id, term_id))
        is_locked = cursor.fetchone()[0] > 0

        # If the Program Chair has rejected/returned the IPCR, allow faculty to re-submit (fields are locked via pointer-events)
        if chair_review and chair_review['overall_status'] == 'Rejected':
            has_submitted = False
        elif chair_review and chair_review['overall_status'] == 'Approved':
            has_submitted = True

        if is_locked:
            has_submitted = True

    cursor.close()
    conn.close()

    return render_template('faculty_dashboard.html',
                           active_term=active_term,
                           assigned_targets=assigned_targets,
                           ret_menu=ret_menu,
                           academic_rank=academic_rank,
                           specialization=specialization,
                           has_submitted=has_submitted,
                           is_locked=is_locked,
                           chair_review=chair_review)


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
        # Check if already locked or approved
        cursor.execute("""
            SELECT COUNT(*) FROM tbl_committed_targets ct
            JOIN tbl_master_indicators mi ON ct.indicator_id = mi.indicator_id
            WHERE ct.emp_id = %s AND mi.term_id = %s
        """, (emp_id, term_id))
        is_locked = cursor.fetchone()[0] > 0

        cursor.execute("""
            SELECT overall_status FROM tbl_ipcr_chair_review
            WHERE emp_id = %s AND term_id = %s
        """, (emp_id, term_id))
        review_row = cursor.fetchone()
        is_approved = review_row and review_row[0] == 'Approved'

        if is_locked or is_approved:
            flash("Your IPCR has already been approved/locked and cannot be re-submitted.", "danger")
            return redirect(url_for('faculty.faculty_dashboard'))

        # Construct research targets payload (proposed_quantity=1 per selection)
        selected_ret_targets = [{'indicator_id': int(x), 'proposed_quantity': 1} for x in selected_indicators]

        # Call submit pipeline (handles writing both chair allocations and RET selections to tbl_draft_targets)
        success, msg = submit_faculty_ipcr(conn, cursor, emp_id, selected_ret_targets)

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


@faculty_bp.route('/lock_ipcr', methods=['POST'])
@role_required('FACULTY')
def faculty_lock_ipcr():
    emp_id = session.get('user_id')
    term_id = request.form.get('term_id')

    if not term_id:
        flash("No active term.", "danger")
        return redirect(url_for('faculty.faculty_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if already locked
        cursor.execute("""
            SELECT COUNT(*) FROM tbl_committed_targets ct
            JOIN tbl_master_indicators mi ON ct.indicator_id = mi.indicator_id
            WHERE ct.emp_id = %s AND mi.term_id = %s
        """, (emp_id, term_id))
        is_locked = cursor.fetchone()[0] > 0
        if is_locked:
            flash("Your IPCR is already locked.", "warning")
            return redirect(url_for('faculty.faculty_dashboard'))

        # Verify it is approved by chair before locking
        cursor.execute("""
            SELECT overall_status FROM tbl_ipcr_chair_review
            WHERE emp_id = %s AND term_id = %s
        """, (emp_id, term_id))
        row = cursor.fetchone()
        is_approved = row and row[0] == 'Approved'
        if not is_approved:
            flash("Your IPCR must be approved by the Program Chair before locking.", "danger")
            return redirect(url_for('faculty.faculty_dashboard'))

        success, msg = lock_and_commit_ipcr(conn, cursor, emp_id, int(term_id))
        if success:
            flash("IPCR locked successfully and committed to evaluation targets.", "success")
        else:
            flash(msg, "danger")
    except Exception as e:
        flash(f"Error locking IPCR: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('faculty.faculty_dashboard'))
