from functools import wraps
from flask import session, flash, redirect, url_for
from lib.user_repository import UserRepository

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('請先登入', 'warning')
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
