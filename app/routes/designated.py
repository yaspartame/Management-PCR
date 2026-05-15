from flask import Blueprint, render_template
from app.decorators import role_required

designated_bp = Blueprint('designated', __name__, url_prefix='/designated')


@designated_bp.route('/')
@role_required('DESIGNATED')
def designated_dashboard():
    return render_template('designated_dashboard.html')
