from flask import render_template, request, redirect, session, url_for, flash
from app import app
from .auth import hash_pass, verify_pass
from .models import get_db_connection, get_user_by_email, register_user
from .decorators import role_required
import mysql.connector, time


@app.route('/')
def login():
    return render_template('login.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    email = request.form.get('email', '').lower().strip()
    password = request.form.get('password', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    result = get_user_by_email(cursor, email)
    
    cursor.close()
    conn.close()
    
    if not result:
        time.sleep(0.5) # remove time abuse
        flash("Invalid Credentials.", "danger")
        return redirect(url_for('login'))
    
    emp_id, stored_hash, verification, role = result[0]
    
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
def admin_dashboard(): return render_template('admin_dashboard.html')

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