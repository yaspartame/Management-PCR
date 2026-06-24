from flask import Blueprint, render_template, request, redirect, session, url_for, flash
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

        ranks_result = timed_query(cursor,
            "SELECT DISTINCT academic_rank FROM tbl_employee_profiles WHERE academic_rank IS NOT NULL AND academic_rank != '' ORDER BY academic_rank",
            label="ret_academic_ranks")
        academic_ranks = [row['academic_rank'] for row in ranks_result]

        if active_term:
            term_id = active_term['term_id']
            ret_indicators = get_ret_indicators(cursor, term_id)
            ret_rules = get_ret_rules(cursor, term_id)

        return render_template('ret_chair_dashboard.html',
                               active_term=active_term,
                               ret_indicators=ret_indicators,
                               ret_rules=ret_rules,
                               academic_ranks=academic_ranks)
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
