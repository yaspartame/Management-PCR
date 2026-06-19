from flask import Blueprint, render_template, session, request, jsonify, redirect, url_for, flash
from app.models import *
from app.decorators import role_required
from app.models.designated import get_designated_selectable_indicators, submit_designated_ipcr

designated_bp = Blueprint('designated', __name__, url_prefix='/designated')


@designated_bp.route('/')
@role_required('DESIGNATED_FACULTY')
def designated_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    emp_id = session.get('user_id')

    cursor.execute("""
        SELECT academic_rank, specialization, designation, first_name, last_name, assigned_program 
        FROM tbl_employee_profiles 
        WHERE emp_id = %s
    """, (emp_id,))
    emp_profile = cursor.fetchone()
    
    academic_rank = emp_profile[0] if emp_profile else ''
    specialization = emp_profile[1] if emp_profile else ''
    designation = emp_profile[2] if emp_profile else ''
    first_name = emp_profile[3] if emp_profile else ''
    last_name = emp_profile[4] if emp_profile else ''
    assigned_program = emp_profile[5] if emp_profile else ''

    terms = get_all_terms(cursor)
    active_term = next((t for t in terms if t['is_active'] == 1), None)

    dpcr_targets = []
    has_submitted = False

    if active_term:
        term_id = active_term['term_id']
        
        # Check if the user has already submitted by looking up tbl_draft_targets
        cursor.execute("""
            SELECT COUNT(*) FROM tbl_draft_targets dt
            JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
            WHERE dt.emp_id = %s AND mi.term_id = %s
        """, (emp_id, term_id))
        has_submitted = cursor.fetchone()[0] > 0

        if has_submitted:
            # Load submitted draft targets (both standard and custom) from tbl_draft_targets
            query = """
                SELECT dt.draft_id as target_id, dt.indicator_id, dt.proposed_quantity as total_target_value, dt.review_status as status,
                       mi.indicator_description, tc.category_name
                FROM tbl_draft_targets dt
                JOIN tbl_master_indicators mi ON dt.indicator_id = mi.indicator_id
                LEFT JOIN tbl_target_categories tc ON mi.category_id = tc.category_id
                WHERE dt.emp_id = %s AND mi.term_id = %s
            """
            cursor.execute(query, (emp_id, term_id))
            columns = [col[0] for col in cursor.description]
            dpcr_targets = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            # Load standard selectable baseline targets
            dpcr_targets = get_designated_selectable_indicators(cursor, term_id)
            for t in dpcr_targets:
                t['total_target_value'] = 0

    cursor.close()
    conn.close()

    return render_template('designated_dashboard.html',
                           emp_name=f"{first_name} {last_name}",
                           academic_rank=academic_rank,
                           designation=designation,
                           assigned_program=assigned_program,
                           active_term=active_term,
                           dpcr_targets=dpcr_targets,
                           has_submitted=has_submitted)


@designated_bp.route('/submit', methods=['POST'])
@role_required('DESIGNATED_FACULTY')
def submit_designated_ipcr_route():
    emp_id = session.get('user_id')
    term_id = request.form.get('term_id')
    
    if not term_id:
        flash("No active academic term found.", "danger")
        return redirect(url_for('designated.designated_dashboard'))

    # Parse baseline target checkboxes
    selected_ids = request.form.getlist('selected_indicators[]')
    selected_targets = []
    for ind_id in selected_ids:
        qty_val = request.form.get(f'target_qty_{ind_id}', '0')
        selected_targets.append({
            'indicator_id': int(ind_id),
            'proposed_quantity': int(qty_val) if qty_val.isdigit() else 1
        })
        
    # Parse custom targets added on the frontend
    custom_descriptions = request.form.getlist('custom_descriptions[]')
    custom_quantities = request.form.getlist('custom_quantities[]')
    
    custom_targets = []
    for desc, qty in zip(custom_descriptions, custom_quantities):
        if desc.strip():
            custom_targets.append({
                'description': desc.strip(),
                'proposed_quantity': int(qty) if str(qty).isdigit() else 1
            })

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        success, msg = submit_designated_ipcr(conn, cursor, emp_id, int(term_id), selected_targets, custom_targets)
        if success:
            flash(msg, "success")
        else:
            flash(msg, "danger")
    except Exception as e:
        flash(f"Error submitting IPCR: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('designated.designated_dashboard'))