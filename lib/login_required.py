from functools import wraps
from flask import session, flash, redirect, url_for, request, jsonify
import logging
from lib.user_repository import UserRepository

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            # 若為 API 路徑則回傳 JSON
            if request.path.startswith('/api/'):
                logging.warning('API 未登入，回傳 401 JSON')
                logging.info(f'session: {dict(session)}')
                logging.info(f'request.headers: {dict(request.headers)}')
                logging.info(f'request.cookies: {request.cookies}')
                return jsonify({'error': '未登入，請先登入'}), 401
            flash('請先登入', 'warning')
            return redirect(url_for('login'))
        # 單一登入驗證
        user_email = session.get('user_email')
        session_token = session.get('session_token')
        if not user_email or not session_token:
            session.clear()
            flash('請重新登入', 'danger')
            return redirect(url_for('login'))
        repo = UserRepository()
        user = repo.get_user_by_email(user_email)
        repo.close()
        if not user or user.get('session_token') != session_token:
            session.clear()
            flash('您的帳號已在其他裝置登入，請重新登入', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('請先登入', 'warning')
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        if not user_id or not user_email:
            flash('找不到會員資訊', 'danger')
            return redirect(url_for('login'))
        repo = UserRepository()
        # 以 user_id 查詢 admin 權限
        is_admin = repo.is_admin_user(user_id) if hasattr(repo, 'is_admin_user') else False
        repo.close()
        if not is_admin:
            flash('您沒有管理員權限', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function
