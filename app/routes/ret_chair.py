from flask import Blueprint, render_template, request, redirect, session, url_for, flash, jsonify
from app.models import *
from app.decorators import role_required

ret_chair_bp = Blueprint('ret_chair', __name__, url_prefix='/ret_chair')
@ret_chair_bp.route('/')
@role_required('RET_CHAIR')
def ret_chair_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    from app.models.connection import timed_query

    try:
        terms = get_all_terms(cursor)
        active_term = next((t for t in terms if t['is_active'] == 1), None)

        ret_indicators = []
        ret_rules = []
        pending_ret_drafts = []
        pending_ret_count = 0

        ranks_result = timed_query(cursor,
            "SELECT DISTINCT academic_rank FROM tbl_employee_profiles WHERE academic_rank IS NOT NULL AND academic_rank != '' ORDER BY academic_rank",
            label="ret_academic_ranks")
        academic_ranks = [row['academic_rank'] for row in ranks_result]

        if active_term:
            term_id = active_term['term_id']
            ret_indicators = get_ret_indicators(cursor, term_id)
            ret_rules = get_ret_rules(cursor, term_id)
            pending_ret_drafts = get_pending_ret_draft_ipcrs(cursor, term_id)
            pending_ret_count = sum(1 for d in pending_ret_drafts if d['review_status'] in ('Pending', 'Pending Review', 'Waiting for Approval'))

        return render_template('ret_chair_dashboard.html',
                               active_term=active_term,
                               ret_indicators=ret_indicators,
                               ret_rules=ret_rules,
                               academic_ranks=academic_ranks,
                               pending_ret_drafts=pending_ret_drafts,
                               pending_ret_count=pending_ret_count)
    finally:
        cursor.close()
        conn.close()


@ret_chair_bp.route('/save_rule', methods=['POST'])
@role_required('RET_CHAIR')
def ret_chair_save_rule():
    term_id = request.form.get('term_id')
    academic_rank = request.form.get('academic_rank')

    research_selections = request.form.get('research_selections', 0)
    extension_selections = request.form.get('extension_selections', 0)

    research_indicator_ids = request.form.getlist('research_indicator_ids[]')
    extension_indicator_ids = request.form.getlist('extension_indicator_ids[]')

    if not term_id or not academic_rank:
        flash("Please fill all required fields.", "warning")
        return redirect(url_for('ret_chair.ret_chair_dashboard'))

    # Parse quantities for each checked indicator
    research_indicators = []
    for r_id in research_indicator_ids:
        qty_val = request.form.get(f'research_quantity_{r_id}', 1)
        try:
            qty = int(qty_val)
            if qty < 1:
                qty = 1
        except ValueError:
            qty = 1
        research_indicators.append((int(r_id), qty))

    extension_indicators = []
    for e_id in extension_indicator_ids:
        qty_val = request.form.get(f'extension_quantity_{e_id}', 1)
        try:
            qty = int(qty_val)
            if qty < 1:
                qty = 1
        except ValueError:
            qty = 1
        extension_indicators.append((int(e_id), qty))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        success, msg = save_ret_rule(conn, cursor, int(term_id), academic_rank,
                                     int(research_selections), int(extension_selections),
                                     research_indicators, extension_indicators)
        cursor.close()
        conn.close()

        if success:
            flash(msg, "success")
        else:
            flash(msg, "danger")
    except Exception as e:
        flash(f"Error saving rule: {str(e)}", "danger")

    return redirect(url_for('ret_chair.ret_chair_dashboard'))


@ret_chair_bp.route('/delete_rule', methods=['POST'])
@role_required('RET_CHAIR')
def ret_chair_delete_rule():
    rule_id = request.form.get('rule_id')
    category_type = request.form.get('category_type')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        success = delete_ret_rule(conn, cursor, rule_id, category_type)
        cursor.close()
        conn.close()
        if success:
            flash("Rule deleted successfully.", "success")
        else:
            flash("Failed to delete rule.", "danger")
    except Exception as e:
        flash(f"Error deleting rule: {str(e)}", "danger")
    return redirect(url_for('ret_chair.ret_chair_dashboard'))


@ret_chair_bp.route('/review_ipcr/<int:emp_id>')
@role_required('RET_CHAIR')
def review_ipcr(emp_id):
    """
    AJAX endpoint — returns JSON payload of Research/Extension targets for RET review.
    Creates a tbl_ipcr_ret_review record if one doesn't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        ret_chair_emp_id = session.get('user_id')
        terms = get_all_terms(cursor)
        active_term = next((t for t in terms if t['is_active'] == 1), None)

        if not active_term:
            return jsonify({'error': 'No active term found.'}), 400

        term_id = active_term['term_id']

        # Fetch or create RET review record
        review_id = get_or_create_ret_review(conn, cursor, emp_id, term_id, ret_chair_emp_id)

        # Fetch RET review items
        items = get_ret_review_items(cursor, review_id)

        # Fetch overall status and remarks
        cursor.execute(
            "SELECT overall_status, overall_remarks FROM tbl_ipcr_ret_review WHERE review_id = %s",
            (review_id,)
        )
        review_row = cursor.fetchone()
        overall_status = review_row[0] if review_row else 'Pending'
        overall_remarks = review_row[1] if review_row else ''

        # Fetch faculty details
        cursor.execute(
            "SELECT CONCAT(first_name, ' ', last_name), academic_rank FROM tbl_employee_profiles WHERE emp_id = %s",
            (emp_id,)
        )
        fac_row = cursor.fetchone()
        faculty_name = fac_row[0] if fac_row else 'Unknown'
        academic_rank = fac_row[1] if fac_row else ''

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
            })

        return jsonify({
            'review_id': review_id,
            'emp_id': emp_id,
            'faculty_name': faculty_name,
            'academic_rank': academic_rank,
            'overall_status': overall_status,
            'overall_remarks': overall_remarks or '',
            'items': serializable_items,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@ret_chair_bp.route('/edit_review_item', methods=['POST'])
@role_required('RET_CHAIR')
def edit_review_item():
    """
    Saves an edited quantity and optional remark for one RET review item row.
    """
    data = request.get_json()
    item_id = data.get('item_id')
    reviewed_quantity = data.get('reviewed_quantity')
    item_remarks = data.get('item_remarks', '').strip()

    if item_id is None or reviewed_quantity is None:
        return jsonify({'success': False, 'message': 'Missing item_id or reviewed_quantity.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        success, msg = update_ret_review_item(conn, cursor, int(item_id), int(reviewed_quantity), item_remarks)
        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@ret_chair_bp.route('/decide_ipcr', methods=['POST'])
@role_required('RET_CHAIR')
def decide_ipcr():
    """
    Approves or rejects the RET selections.
    """
    review_id = request.form.get('review_id')
    action = request.form.get('action')           # 'approve' or 'reject'
    overall_remarks = request.form.get('overall_remarks', '').strip()

    if not review_id or action not in ('approve', 'reject'):
        flash("Invalid decision parameters.", "danger")
        return redirect(url_for('ret_chair.ret_chair_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        success, msg = decide_ret_review(conn, cursor, int(review_id), action, overall_remarks)
        flash(msg, "success" if success else "danger")
    except Exception as e:
        flash(f"Error processing decision: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('ret_chair.ret_chair_dashboard'))
