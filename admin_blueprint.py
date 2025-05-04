from flask import Blueprint, render_template
from lib.login_required import login_required, admin_user_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
# @admin_user_required
def admin_index():
    return render_template('admin_sample.html')

@admin_bp.route('/user')
# @admin_user_required
def admin_user():
    return render_template('admin_user.html')

@admin_bp.route('/user_videos')
# @admin_user_required
def admin_user_videos():
    return render_template('admin_user_videos.html')

@admin_bp.route('/series')
# @admin_user_required
def admin_series():
    return render_template('admin_series.html')

@admin_bp.route('/videos')
# @admin_user_required
def admin_videos():
    return render_template('admin_videos.html')

@admin_bp.route('/admin_users')
# @admin_user_required
def admin_admin_users():
    return render_template('admin_admin_users.html')
