from flask import render_template, request, redirect, session, url_for, flash, Response
from app import app
from .auth import hash_pass, verify_pass
from .models import get_db_connection, get_user_by_email, register_user, get_all_profiles, save_single_profile, toggle_profile_status, import_csv_roster, open_new_term, get_all_terms, get_master_indicators, add_master_indicator, edit_master_indicator, delete_master_indicator, import_previous_term_indicators, log_audit_action, get_recent_audit_logs, emergency_reset_password, emergency_lock_account, get_all_users_for_security, get_admin_kpis
from .decorators import role_required
import mysql.connector, time, csv, io, secrets, string, datetime


@app.route('/')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/admin/backup')
@role_required('ADMIN')
def admin_backup():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        output = io.StringIO()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        output.write(f"-- Accrual IPCR System Database Backup\n")
        output.write(f"-- Generated: {timestamp}\n")
        output.write(f"-- Database: ipcr_db\n\n")
        output.write("SET FOREIGN_KEY_CHECKS=0;\n\n")

        for table in tables:
            cursor.execute(f"SELECT * FROM `{table}`")
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]

            output.write(f"-- Table: {table}\n")
            output.write(f"TRUNCATE TABLE `{table}`;\n")

            if rows:
                cols = ', '.join(f'`{c}`' for c in col_names)
                output.write(f"INSERT INTO `{table}` ({cols}) VALUES\n")
                value_rows = []
                for row in rows:
                    vals = []
                    for v in row:
                        if v is None:
                            vals.append('NULL')
                        elif isinstance(v, (int, float)):
                            vals.append(str(v))
                        elif isinstance(v, (datetime.date, datetime.datetime)):
                            vals.append(f"'{v}'")
                        else:
                            escaped = str(v).replace("'", "''")
                            vals.append(f"'{escaped}'")
                    value_rows.append(f"  ({', '.join(vals)})")
                output.write(',\n'.join(value_rows) + ";\n")
            output.write("\n")

        output.write("SET FOREIGN_KEY_CHECKS=1;\n")

        cursor.close()
        conn.close()

        filename = f"ipcr_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        return Response(
            output.getvalue(),
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )

    except Exception as e:
        flash(f"Backup failed: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route('/authenticate', methods=['POST'])
def authenticate():
    email = request.form.get('email', '').lower().strip()
    password = request.form.get('password', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    result = get_user_by_email(cursor, email)
    
    if not result:
        cursor.close()
        conn.close()
        time.sleep(0.5) # remove time abuse
        flash("Invalid Credentials.", "danger")
        return redirect(url_for('login'))
    
    emp_id, stored_hash, verification, role = result[0]
    
    # Check if account has been soft-deleted/deactivated
    cursor.execute("SELECT account_status FROM tbl_system_access WHERE emp_id = %s", (emp_id,))
    acc_status_row = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if acc_status_row and acc_status_row[0] == 'Inactive':
        flash("Your account has been deactivated. Please contact the administrator.", "danger")
        return redirect(url_for('login'))
    
    # Normalize role for matching
    role = role.upper() if role else ""
    
    if verification != "APPROVED":
        flash("Account not approved. Please contact the administrator.", "danger")
        return redirect(url_for('login'))
    
    if not verify_pass(password, stored_hash):
        time.sleep(0.5)
        flash("Invalid Credentials.", "danger")
        return redirect(url_for('login'))
        
    session['user_id'] = emp_id
    session['role'] = role
    
    if role == "ADMIN":
        return redirect(url_for('admin_dashboard'))
    elif role == "DEAN":
        return redirect(url_for('dean_dashboard'))
    elif role == "FACULTY":
        return redirect(url_for('faculty_dashboard'))
    elif role == "PROGRAM_CHAIR":
        return redirect(url_for('prog_chair_dashboard'))
    elif role == "RET_CHAIR":
        return redirect(url_for('ret_chair_dashboard'))
    elif role == "DESIGNATED":
        return redirect(url_for('designated_dashboard'))
    else: 
        flash(f"No system role assigned to this account (Role: {role}).", "danger")
        return redirect(url_for('login'))
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        employee_id_number = request.form.get('employee_id_number')
        email = request.form.get('email', ' ').lower().strip()
        password = request.form.get('password', '')

        if not employee_id_number or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))
        
        hashed_pw = hash_pass(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Use the updated model function which handles commit/rollback
            register_user(conn, cursor, employee_id_number, email, hashed_pw)
            
            cursor.close()
            conn.close()
            
            flash("Account claimed successfully! You have been auto-approved and may now log in.", "success")
            return redirect(url_for('login'))
            
        except mysql.connector.Error as e:
            # specifically for Custom State 45000 (ID not in roster / Already claimed)
            flash(str(e), "danger")
            return redirect(url_for('register'))
        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return redirect(url_for('register'))
        
    return render_template('register.html')

@app.route('/admin')
@role_required('ADMIN')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    profiles = get_all_profiles(cursor)
    terms = get_all_terms(cursor)
    active_term = next((t for t in terms if t['is_active'] == 1), None)
    indicators = get_master_indicators(cursor, active_term['term_id']) if active_term else []
    audit_logs = get_recent_audit_logs(cursor)
    security_users = get_all_users_for_security(cursor)
    kpis = get_admin_kpis(cursor)
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', profiles=profiles, terms=terms, active_term=active_term, indicators=indicators, audit_logs=audit_logs, security_users=security_users, kpis=kpis)

@app.route('/admin/open_term', methods=['POST'])
@role_required('ADMIN')
def admin_open_term():
    academic_year = request.form.get('academic_year')
    semester = request.form.get('semester')
    deadline_date = request.form.get('deadline_date')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        open_new_term(conn, cursor, academic_year, semester, deadline_date)
        log_audit_action(conn, cursor, session.get('user_id'), 'Term Opened',
                         f"New term opened: {academic_year} {semester} (Deadline: {deadline_date})",
                         request.remote_addr)
        cursor.close()
        conn.close()
        flash("New Academic Term opened successfully.", "success")
    except Exception as e:
        flash(f"Error opening term: {e}", "danger")
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/faculty/save', methods=['POST'])
@role_required('ADMIN')
def save_faculty():
    data = {
        'employee_id_number': request.form.get('employee_id_number'),
        'first_name': request.form.get('first_name'),
        'last_name': request.form.get('last_name'),
        'college': request.form.get('college'),
        'assigned_program': request.form.get('assigned_program'),
        'academic_rank': request.form.get('academic_rank'),
        'employment_status': request.form.get('employment_status'),
        'leave_status': request.form.get('leave_status'),
        'designation': request.form.get('designation') or None
    }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        save_single_profile(conn, cursor, data)
        cursor.close()
        conn.close()
        flash("Faculty profile saved successfully.", "success")
    except Exception as e:
        flash(f"Error saving profile: {str(e)}", "danger")
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/faculty/toggle_status', methods=['POST'])
@role_required('ADMIN')
def toggle_status():
    emp_id = request.form.get('employee_id_number')
    if not emp_id:
        flash("Employee ID missing.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        new_status = toggle_profile_status(conn, cursor, emp_id)
        cursor.close()
        conn.close()
        if new_status:
            flash(f"Profile status updated to {new_status}.", "success")
        else:
            flash("Profile not found.", "danger")
    except Exception as e:
        flash(f"Error toggling status: {str(e)}", "danger")
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/csv/import', methods=['POST'])
@role_required('ADMIN')
def import_csv():
    if 'csv_file' not in request.files:
        flash("No file part.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    file = request.files['csv_file']
    if file.filename == '':
        flash("No selected file.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    if not file.filename.endswith('.csv'):
        flash("File must be a CSV.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        rows = list(csv_reader)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        success, new_added, updated, unchanged = import_csv_roster(conn, cursor, rows)
        if success:
            log_audit_action(conn, cursor, session.get('user_id'), 'CSV Roster Import',
                             f"Import complete: {new_added} added, {updated} updated, {unchanged} unchanged.",
                             request.remote_addr)
        cursor.close()
        conn.close()
        
        if success:
            flash(f"CSV Import Complete: {new_added} New Hires Added, {updated} Profiles Updated, {unchanged} Unchanged.", "success")
        else:
            flash(f"Error importing CSV: {new_added}", "danger") # new_added holds error str on failure
    except Exception as e:
        flash(f"Error reading CSV file: {str(e)}", "danger")
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/indicators/add', methods=['POST'])
@role_required('ADMIN')
def admin_add_indicator():
    term_id = request.form.get('term_id')
    category_name = request.form.get('category_name')
    description = request.form.get('description')
    efficiency_type = request.form.get('efficiency_type')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        add_master_indicator(conn, cursor, category_name, description, efficiency_type, term_id)
        cursor.close()
        conn.close()
        flash("Master Indicator added successfully.", "success")
    except Exception as e:
        flash(f"Error adding indicator: {str(e)}", "danger")
    return redirect(url_for('admin_dashboard') + '#nav-indicators')


@app.route('/admin/indicators/edit', methods=['POST'])
@role_required('ADMIN')
def admin_edit_indicator():
    indicator_id = request.form.get('indicator_id')
    category_name = request.form.get('category_name')
    description = request.form.get('description')
    efficiency_type = request.form.get('efficiency_type')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        edit_master_indicator(conn, cursor, indicator_id, category_name, description, efficiency_type)
        cursor.close()
        conn.close()
        flash("Master Indicator updated successfully.", "success")
    except Exception as e:
        flash(f"Error updating indicator: {str(e)}", "danger")
    return redirect(url_for('admin_dashboard') + '#nav-indicators')


@app.route('/admin/indicators/delete', methods=['POST'])
@role_required('ADMIN')
def admin_delete_indicator():
    indicator_id = request.form.get('indicator_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        delete_master_indicator(conn, cursor, indicator_id)
        cursor.close()
        conn.close()
        flash("Master Indicator deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting indicator: {str(e)}", "danger")
    return redirect(url_for('admin_dashboard') + '#nav-indicators')


@app.route('/admin/indicators/import', methods=['POST'])
@role_required('ADMIN')
def admin_import_indicators():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        active_term_id = request.form.get('term_id')
        success, message = import_previous_term_indicators(conn, cursor, active_term_id)
        cursor.close()
        conn.close()
        flash(message, "success" if success else "warning")
    except Exception as e:
        flash(f"Error importing indicators: {str(e)}", "danger")
    return redirect(url_for('admin_dashboard') + '#nav-indicators')


@app.route('/admin/security/reset_password', methods=['POST'])
@role_required('ADMIN')
def admin_reset_password():
    emp_id = request.form.get('emp_id')
    try:
        # Generate a cryptographically secure random temporary password
        alphabet = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))

        conn = get_db_connection()
        cursor = conn.cursor()
        new_hash = hash_pass(temp_password)
        emergency_reset_password(conn, cursor, emp_id, new_hash)
        log_audit_action(conn, cursor, session.get('user_id'), 'Emergency Password Reset',
                         f"Temporary password issued for emp_id: {emp_id}",
                         request.remote_addr)
        cursor.close()
        conn.close()
        # Flash the plaintext once — admin must relay this to the user securely
        flash(f"Password for account #{emp_id} has been reset. Temporary password (show once): {temp_password}", "warning")
    except Exception as e:
        flash(f"Error resetting password: {str(e)}", "danger")
    return redirect(url_for('admin_dashboard') + '#nav-security')


@app.route('/admin/security/lock_account', methods=['POST'])
@role_required('ADMIN')
def admin_lock_account():
    emp_id = request.form.get('emp_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        emergency_lock_account(conn, cursor, emp_id)
        log_audit_action(conn, cursor, session.get('user_id'), 'Emergency Account Lock',
                         f"Force locked account for emp_id: {emp_id}",
                         request.remote_addr)
        cursor.close()
        conn.close()
        flash(f"Account #{emp_id} has been locked.", "warning")
    except Exception as e:
        flash(f"Error locking account: {str(e)}", "danger")
    return redirect(url_for('admin_dashboard') + '#nav-security')


@app.route('/faculty')
@role_required('FACULTY')
def faculty_dashboard(): return render_template('faculty_dashboard.html')

@app.route('/dean')
@role_required('DEAN')
def dean_dashboard(): return render_template('dean_dashboard.html')

@app.route('/prog_chair')
@role_required('PROGRAM_CHAIR')
def prog_chair_dashboard(): return render_template('prog_chair_dashboard.html')

@app.route('/ret_chair')
@role_required('RET_CHAIR')
def ret_chair_dashboard(): return render_template('ret_chair_dashboard.html')

@app.route('/designated')
@role_required('DESIGNATED')
def designated_dashboard(): return render_template('designated_dashboard.html')