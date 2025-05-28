import hashlib

from flask import Blueprint, render_template, request, jsonify
from lib.login_required import login_required, admin_user_required
from lib.user_repository import UserRepository

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 管理員使用者頁面
@admin_bp.route('/')
@admin_bp.route('/user')
@admin_user_required
def admin_user():
    return render_template('admin_user.html')

# 取得使用者列表 (支援 email/name like 搜尋)
@admin_bp.route('/api/users', methods=['GET'])
@admin_user_required
def api_get_users():
    q = request.args.get('q', '').strip().lower()
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 100))
    repo = UserRepository()
    try:
        users, total = repo.get_users_with_pagination(q, offset, limit)
        return jsonify({'users': users, 'total': total})
    finally:
        repo.close()

# 設為預設密碼 (假設預設密碼為 '12345678')
@admin_bp.route('/api/users/<int:user_id>/reset_password', methods=['POST'])
@admin_user_required
def api_reset_password(user_id):
    # 這裡應該要查詢資料庫並更新密碼
    repo = UserRepository()
    try:
        user = repo.get_user_by_id(user_id)
        if not user:
            raise Exception('找不到使用者')
        else:
            email = user['email']
        # 預設密碼規則: sha256(email)[:6]
        default_pw = hashlib.sha256(email.encode('utf-8')).hexdigest()[:6]
        pw = hashlib.sha256(default_pw.encode()).hexdigest()
        repo.update_password(user_id, pw)
        return jsonify({'success': True, 'msg': f"已將 {email} 密碼設為預設值", 'default_pw': default_pw})
    finally:
        repo.close()

# @admin_bp.route('/user_videos')
# @admin_user_required
# def admin_user_videos():
#     return render_template('admin_user_videos.html')

# @admin_bp.route('/series')
# @admin_user_required
# def admin_series():
#     return render_template('admin_series.html')

# @admin_bp.route('/videos')
# @admin_user_required
# def admin_videos():
#     return render_template('admin_videos.html')

# @admin_bp.route('/admin_users')
# @admin_user_required
# def admin_admin_users():
#     return render_template('admin_admin_users.html')

@admin_bp.app_errorhandler(404)
def admin_page_not_found(e):
    return render_template('admin_404.html'), 404