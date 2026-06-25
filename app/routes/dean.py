from flask import Blueprint, render_template, request, redirect, session, url_for, flash, jsonify
from app.models import *
from app.decorators import role_required

dean_bp = Blueprint('dean', __name__, url_prefix='/dean')


@dean_bp.route('/')
@role_required('DEAN')
def dean_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    dean_id = session.get('user_id')
    terms = get_all_terms(cursor)
    active_term = next((t for t in terms if t['is_active'] == 1), None)

    if not active_term:
        flash('No active academic term found.', 'warning')
        cursor.close()
        conn.close()
        return render_template('dean_dashboard.html',
                               active_term=None,
                               master_indicators=[],
                               existing_quotas={},
                               completion_rate=0,
                               pending_count=0,
                               top_dept="N/A",
                               pending_approvals=[],
                               draft_submissions=[],
                               college_wide_quotas=[],
                               designated_faculty_list=[])

    term_id = active_term['term_id']

    # Use timed_query helper for all queries
    from app.models.connection import timed_query

    indicators = get_master_indicators(cursor, term_id)

    existing_quotas_raw = get_existing_cascaded_quotas(cursor, term_id)

    existing_quotas = {}
    for quota in existing_quotas_raw:
        ind_id = quota['indicator_id']
        if ind_id not in existing_quotas:
            existing_quotas[ind_id] = {}
        existing_quotas[ind_id][quota['assigned_to_role']] = quota['total_target_value']

    # Consolidated KPI query — 1 round-trip instead of 3
    completion_rate, pending_count, top_dept = get_dean_dashboard_kpis(cursor, term_id)

    pending_approvals = get_pending_final_approvals(cursor, term_id)

    # ── New: Draft IPCR submissions from designated faculty ──
    draft_submissions = get_designated_draft_submissions(cursor, term_id)

    # ── New: College-Wide quotas for target assignment ──
    college_wide_quotas = get_college_wide_cascaded_quotas(cursor, term_id)

    # ── New: Designated faculty list ──
    designated_faculty_list = get_designated_faculty_list(cursor)

    # Get ALL assignments in ONE batch query (replaces N+1 loop)
    emp_ids = [fac['emp_id'] for fac in designated_faculty_list]
    designated_assignments = get_designated_faculty_assignments_batch(cursor, term_id, emp_ids)

    cursor.close()
    conn.close()

    return render_template('dean_dashboard.html',
                           active_term=active_term,
                           master_indicators=indicators,
                           existing_quotas=existing_quotas,
                           completion_rate=completion_rate,
                           pending_count=pending_count,
                           top_dept=top_dept,
                           pending_approvals=pending_approvals,
                           draft_submissions=draft_submissions,
                           college_wide_quotas=college_wide_quotas,
                           designated_faculty_list=designated_faculty_list,
                           designated_assignments=designated_assignments)


@dean_bp.route('/cascade_quotas', methods=['POST'])
@role_required('DEAN')
def cascade_quotas():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        term_id = request.form.get('term_id')
        if not term_id:
            flash('Missing term ID', 'danger')
            return redirect(url_for('dean.dean_dashboard'))

        quotas_data = []
        indicator_ids = request.form.getlist('indicator_id[]')
        wst_values = request.form.getlist('wst[]')
        dst_values = request.form.getlist('dst[]')
        nst_values = request.form.getlist('nst[]')
        bsds_values = request.form.getlist('bsds[]')
        ret_values = request.form.getlist('ret[]')
        college_values = request.form.getlist('college[]')

        for i, ind_id in enumerate(indicator_ids):
            if not ind_id:
                continue

            values = [
                ('WST Program', int(wst_values[i]) if wst_values[i] and int(wst_values[i]) > 0 else 0),
                ('DST Program', int(dst_values[i]) if dst_values[i] and int(dst_values[i]) > 0 else 0),
                ('NST Program', int(nst_values[i]) if nst_values[i] and int(nst_values[i]) > 0 else 0),
                ('BSDS Program', int(bsds_values[i]) if bsds_values[i] and int(bsds_values[i]) > 0 else 0),
                ('RET / Extension', int(ret_values[i]) if ret_values[i] and int(ret_values[i]) > 0 else 0),
                ('College-Wide', int(college_values[i]) if i < len(college_values) and college_values[i] and int(college_values[i]) > 0 else 0)
            ]

            for role, value in values:
                if value > 0:
                    quotas_data.append({
                        'indicator_id': int(ind_id),
                        'total_target': value,
                        'assigned_role': role
                    })

        success, message = save_cascaded_quotas(cursor, conn, term_id, quotas_data)

        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')

    except Exception as e:
        flash(f'Error cascading quotas: {str(e)}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('dean.dean_dashboard'))


@dean_bp.route('/batch_approve', methods=['POST'])
@role_required('DEAN')
def batch_approve():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        score_ids = request.form.getlist('score_ids[]')
        action = request.form.get('action', 'approve')

        if not score_ids:
            flash('No IPCRs selected for approval', 'warning')
            return redirect(url_for('dean.dean_dashboard'))

        new_status = 'Approved' if action == 'approve' else 'Reverted'
        success, message = update_dean_approval_status(cursor, conn, score_ids, new_status)

        flash(message, 'success' if success else 'danger')

    except Exception as e:
        flash(f'Error processing batch approval: {str(e)}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('dean.dean_dashboard'))


@dean_bp.route('/validate_quotas', methods=['POST'])
@role_required('DEAN')
def validate_quotas():
    """AJAX endpoint to validate quotas before submission"""
    data = request.get_json()
    return jsonify({'valid': True, 'message': 'Quotas validated'})


# DPCR export not yet implemented
# @dean_bp.route('/export_dpcr')
# @role_required('DEAN')
# def export_dpcr():
#     ...


# ──────────────────────────────────────────────
# Draft IPCR Review — AJAX endpoints (Program Chair UX style)
# ──────────────────────────────────────────────

@dean_bp.route('/review_draft_fetch/<int:emp_id>')
@role_required('DEAN')
def review_draft_fetch(emp_id):
    """AJAX endpoint — returns JSON to populate the Dean's review modal."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        dean_id = session.get('user_id')
        terms = get_all_terms(cursor)
        active_term = next((t for t in terms if t['is_active'] == 1), None)
        if not active_term:
            return jsonify({'error': 'No active term found.'}), 400

        term_id = active_term['term_id']

        # Get or create review record
        review_id = get_or_create_dean_review(conn, cursor, emp_id, term_id, dean_id)

        # Fetch review items
        items = get_dean_review_items(cursor, review_id)

        # Fetch overall status & remarks
        cursor.execute(
            "SELECT overall_status, overall_remarks FROM tbl_ipcr_dean_review WHERE review_id = %s",
            (review_id,)
        )
        row = cursor.fetchone()
        overall_status = row[0] if row else 'Pending'
        overall_remarks = row[1] if row else ''

        # Faculty info
        cursor.execute(
            "SELECT CONCAT(first_name, ' ', last_name), academic_rank, designation, assigned_program FROM tbl_employee_profiles WHERE emp_id = %s",
            (emp_id,)
        )
        fac = cursor.fetchone()
        faculty_name = fac[0] if fac else 'Unknown'
        academic_rank = fac[1] if fac else ''
        designation = fac[2] if fac else ''
        assigned_program = fac[3] if fac else ''

        # Also get ALL available master indicators for this term
        all_indicators = get_available_master_indicators(cursor, term_id)
        picked_ids = {i['indicator_id'] for i in items}
        unpicked = [ind for ind in all_indicators if ind['indicator_id'] not in picked_ids]

        serializable_items = []
        for item in items:
            serializable_items.append({
                'item_id': item['item_id'],
                'draft_id': item['draft_id'],
                'indicator_id': item['indicator_id'],
                'indicator_description': item['indicator_description'],
                'category_name': item['category_name'],
                'original_quantity': item['original_quantity'],
                'reviewed_quantity': item['reviewed_quantity'],
                'item_remarks': item['item_remarks'] or '',
                'is_custom': item['is_custom'],
            })

        return jsonify({
            'review_id': review_id,
            'emp_id': emp_id,
            'faculty_name': faculty_name,
            'academic_rank': academic_rank,
            'designation': designation,
            'assigned_program': assigned_program,
            'overall_status': overall_status,
            'overall_remarks': overall_remarks or '',
            'items': serializable_items,
            'unpicked': unpicked,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@dean_bp.route('/save_review_items', methods=['POST'])
@role_required('DEAN')
def save_review_items():
    """Batch save all edited quantities and remarks for one review."""
    data = request.get_json()
    review_id = data.get('review_id')
    items = data.get('items', [])

    if not review_id or not items:
        return jsonify({'success': False, 'message': 'Missing review_id or items.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        success, msg = save_dean_review_items(cursor, conn, review_id, items)
        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@dean_bp.route('/submit_review_decision', methods=['POST'])
@role_required('DEAN')
def submit_review_decision():
    """Approve or reject the entire review with overall remarks."""
    data = request.get_json()
    review_id = data.get('review_id')
    action = data.get('action')
    overall_remarks = data.get('overall_remarks', '').strip()

    if not review_id or action not in ('Approved', 'Rejected'):
        return jsonify({'success': False, 'message': 'Missing review_id or invalid action.'}), 400

    if action == 'Rejected' and not overall_remarks:
        return jsonify({'success': False, 'message': 'Remarks are required when rejecting.'}), 400

    dean_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        success, msg = submit_dean_review_decision(cursor, conn, review_id, action, overall_remarks)

        if success:
            details = f"Dean {dean_id} {action.lower()} draft IPCR (review #{review_id}). Remarks: {overall_remarks}"
            from app.models.audit import log_audit_action
            log_audit_action(conn, cursor, dean_id, f'DEAN_REVIEW_{action.upper()}', details, request.remote_addr or '127.0.0.1')

        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# College-Wide Target Assignment (Designated Faculty)
# ──────────────────────────────────────────────

@dean_bp.route('/assign_designated_target', methods=['POST'])
@role_required('DEAN')
def assign_designated_target():
    """Assign a College-Wide target to a designated faculty member."""
    term_id = request.form.get('term_id')
    emp_id = request.form.get('emp_id')
    indicator_id = request.form.get('indicator_id')
    quantity = request.form.get('quantity', '0')

    if not term_id or not emp_id or not indicator_id:
        flash('Missing required data.', 'danger')
        return redirect(url_for('dean.dean_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        success, msg = save_designated_faculty_assignment(
            cursor, conn, int(term_id), emp_id, int(indicator_id), int(quantity) if quantity.isdigit() else 0
        )
        flash(msg, 'success' if success else 'danger')
    except Exception as e:
        flash(f'Error assigning target: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('dean.dean_dashboard'))
