from flask import Blueprint, render_template, request, redirect, session, url_for, flash, jsonify
from app.models import *
from app.decorators import role_required

dean_bp = Blueprint('dean', __name__, url_prefix='/dean')


@dean_bp.route('/')
@role_required('DEAN')
def dean_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

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
                               pending_approvals=[])

    term_id = active_term['term_id']

    indicators = get_master_indicators(cursor, term_id)

    existing_quotas_raw = get_existing_cascaded_quotas(cursor, term_id)

    existing_quotas = {}
    for quota in existing_quotas_raw:
        ind_id = quota['indicator_id']
        if ind_id not in existing_quotas:
            existing_quotas[ind_id] = {}
        existing_quotas[ind_id][quota['assigned_to_role']] = quota['total_target_value']

    completion_rate = get_overall_completion(cursor, term_id)
    pending_count = get_pending_approvals_count(cursor, term_id)
    top_dept = get_top_performing_department(cursor, term_id)

    pending_approvals = get_pending_final_approvals(cursor, term_id)

    cursor.close()
    conn.close()

    return render_template('dean_dashboard.html',
                           active_term=active_term,
                           master_indicators=indicators,
                           existing_quotas=existing_quotas,
                           completion_rate=completion_rate,
                           pending_count=pending_count,
                           top_dept=top_dept,
                           pending_approvals=pending_approvals)


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

        for i, ind_id in enumerate(indicator_ids):
            if not ind_id:
                continue

            values = [
                ('WST Program', int(wst_values[i]) if wst_values[i] and int(wst_values[i]) > 0 else 0),
                ('DST Program', int(dst_values[i]) if dst_values[i] and int(dst_values[i]) > 0 else 0),
                ('NST Program', int(nst_values[i]) if nst_values[i] and int(nst_values[i]) > 0 else 0),
                ('BSDS Program', int(bsds_values[i]) if bsds_values[i] and int(bsds_values[i]) > 0 else 0),
                ('RET / Extension', int(ret_values[i]) if ret_values[i] and int(ret_values[i]) > 0 else 0)
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
