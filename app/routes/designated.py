from flask import Blueprint, render_template, session, request, jsonify
from app.models import *
from app.decorators import role_required
# Import both your original fetch function and the new save function
from app.models.designated import get_designated_cascaded_quotas, insert_custom_target

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
    if active_term:
        dpcr_targets = get_designated_cascaded_quotas(cursor, active_term['term_id'])

    cursor.close()
    conn.close()

    return render_template('designated_dashboard.html',
                           emp_name=f"{first_name} {last_name}",
                           academic_rank=academic_rank,
                           designation=designation,
                           assigned_program=assigned_program,
                           active_term=active_term,
                           dpcr_targets=dpcr_targets)


@designated_bp.route('/add-target', methods=['POST'])
@role_required('DESIGNATED_FACULTY')
def add_custom_target():
    """Endpoint handling the AJAX submission from the Add Target popup modal"""
    data = request.get_json()
    emp_id = session.get('user_id')
    term_id = data.get('term_id')
    description = data.get('description')
    quantity = data.get('quantity')
    category = data.get('category')

    # Validation
    if not all([description, quantity, category, term_id]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Save custom target to database
        success = insert_custom_target(cursor, emp_id, term_id, description, quantity, category)
        
        conn.commit()
        cursor.close()
        conn.close()

        if success:
            return jsonify({'success': True, 'message': 'Target added successfully!'})
        return jsonify({'success': False, 'message': 'Failed to save target.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500