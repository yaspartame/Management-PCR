from flask import render_template, request, redirect, session, url_for
from app import app
from .auth import hash_pass, verify_pass
from .models import get_db_connection, get_user_by_email, register_user
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
    
    conn.close()
    
    if not result:
        time.sleep(0.5) # remove time abuse
        return render_template('login.html', status="Invalid Credentials.")
    
    stored_hash = result[0][1]
    
    if verify_pass(password, stored_hash):
        session['user_id'] = result[0][0] 
        return render_template('login.html', status="success")
    else:
        time.sleep(0.5)
        return render_template('login.html', status="Invalid Credentials.")
        
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
def admin_dashboard(): return render_template('admin_dashboard.html')

@app.route('/faculty')
def faculty_dashboard(): return render_template('faculty_dashboard.html')

@app.route('/dean')
def dean_dashboard(): return render_template('dean_dashboard.html')

@app.route('/manager')
def manager_dashboard(): return render_template('manager_dashboard.html')

@app.route('/designated')
def designated_dashboard(): return render_template('designated_dashboard.html')