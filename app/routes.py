from flask import render_template, request, redirect, session, url_for
from app import app
from .auth import hash_pass, verify_pass
from .models import get_db_connection, get_user_by_email, register_user
from .decorators import role_required
import mysql.connector, time


@app.route('/')
def login():
    return render_template('login.html', status="")

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
        return render_template('login.html', status="Invalid Credentials.")
    
    emp_id, stored_hash, verification, role = result[0]
    
    if verification != "APPROVED":
        return render_template('login.html', status="Account not approved.")
    
    if not verify_pass(password, stored_hash):
        time.sleep(0.5)
        return render_template('login.html', status="Invalid Credentials.")
        
    session['user_id'] = emp_id
    session['role'] = role
    
    if role == "admin":
        return redirect(url_for('admin_dashboard'))
    elif role == "dean":
        return redirect(url_for('dean_dashboard'))
    elif role == "faculty":
        return redirect(url_for('faculty_dashboard'))
    elif role == "designated":
        return redirect(url_for('designated_dashboard'))
    else: 
        return render_template('login.html', status="No role assigned.")
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        email = request.form.get('email', ' ').lower().strip()
        password = request.form.get('password', '')
        if not emp_id or not email or not password:
            return render_template('register.html', status="All fields required.")
        
        hashed_pw = hash_pass(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            register_user(cursor, emp_id, email, hashed_pw)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
        except mysql.connector.Error as e:
            return render_template('register.html', status=f"Database error: {e}")
        
    return render_template('register.html', status="")

@app.route('/admin')
@role_required('admin')
def admin_dashboard(): return render_template('admin_dashboard.html')

@app.route('/faculty')
@role_required('faculty')
def faculty_dashboard(): return render_template('faculty_dashboard.html')

@app.route('/dean')
@role_required('dean')
def dean_dashboard(): return render_template('dean_dashboard.html')

@app.route('/manager')
@role_required('manager')
def manager_dashboard(): return render_template('manager_dashboard.html')

@app.route('/designated')
@role_required('designated')
def designated_dashboard(): return render_template('designated_dashboard.html')