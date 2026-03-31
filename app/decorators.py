from flask import session, redirect, url_for

def role_required(required_role):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') != required_role:
                return "Unauthorised", 403
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator