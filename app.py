from flask import Flask, render_template, request, redirect, url_for, flash, session, get_flashed_messages
import requests
from functools import wraps
import secrets
import psycopg2
from config import config
import os
from datetime import timedelta
from lib.user_repository import UserRepository
from lib.video_repository import VideoRepository
import hashlib

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)  # 使用隨機產生的安全密鑰
app.permanent_session_lifetime = timedelta(days=30)  # 設定 session 有效期 30 天

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('請先登入', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/member_videos')
@login_required
def member_videos():
    user_email = session.get('user_email')
    repo = VideoRepository()
    video_list = repo.get_videos_with_status(user_email)
    repo.close()
    return render_template('member_videos.html', video_list=video_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hcaptcha_token = request.form.get('h-captcha-response')
        if not hcaptcha_token:
            flash('請完成驗證碼', 'danger')
            return render_template('login.html')
        # hCaptcha 驗證
        hcaptcha_secret = 'ES_e3cff9ee84a04dc08df9f3543d599641'  # 請換成你的 secret key
        verify_url = 'https://hcaptcha.com/siteverify'
        data = {
            'secret': hcaptcha_secret,
            'response': hcaptcha_token,
            'remoteip': request.remote_addr
        }
        try:
            resp = requests.post(verify_url, data=data, timeout=5)
            result = resp.json()
            if not result.get('success'):
                flash('驗證碼失敗，請重試', 'danger')
                return render_template('login.html')
        except Exception:
            flash('驗證服務異常，請稍後再試', 'danger')
            return render_template('login.html')
        # 使用者資料庫驗證
        repo = UserRepository()
        user = repo.get_user_by_email(username)
        if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
            session['logged_in'] = True
            session['user_email'] = user['email']
            if request.form.get('remember_me'):
                session.permanent = True
            else:
                session.permanent = False
            flash('登入成功', 'success')
            repo.close()
            return redirect(url_for('member_videos'))
        else:
            flash('帳號或密碼錯誤', 'danger')
        repo.close()
    else:
        get_flashed_messages()  # 清空殘留訊息
    return render_template('login.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        email = session.get('user_email')  # 假設 session 有存 email
        if not email:
            flash('請重新登入', 'danger')
            return redirect(url_for('login'))
        if new_password != confirm_password:
            flash('新密碼與確認密碼不一致', 'danger')
        elif old_password == new_password:
            flash('新密碼不可與舊密碼相同', 'danger')
        else:
            repo = UserRepository()
            user = repo.get_user_by_email(email)
            if not user:
                flash('找不到使用者', 'danger')
            else:
                old_hash = hashlib.sha256(old_password.encode()).hexdigest()
                if user['password'] != old_hash:
                    flash('舊密碼錯誤', 'danger')
                else:
                    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
                    repo.update_password(user['id'], new_hash)
                    flash('密碼修改成功', 'success')
                    repo.close()
                    return redirect(url_for('login'))
            repo.close()
    return render_template('change_password.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        # 這裡應加入發送重設密碼信件的邏輯
        flash('重設密碼信已寄出，請檢查您的信箱', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功登出', 'success')
    return redirect(url_for('login'))

@app.route('/test-db')
def test_db():
    db_info = {
        'DB_HOST': config.DB_HOST,
        'DB_PORT': config.DB_PORT,
        'DB_USER': getattr(config, 'DB_USER', 'postgres'),
        'DB_NAME': getattr(config, 'DB_NAME', 'postgres'),
        'DB_PASSWORD': getattr(config, 'DB_PASSWORD', '***隱藏***'),  # 顯示密碼（可改為***隱藏***）
    }
    result = None
    error = None
    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=getattr(config, 'DB_USER', 'postgres'),
            password=config.DB_PASSWORD,
            dbname=getattr(config, 'DB_NAME', 'postgres')
        )
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            result = cur.fetchone()
        conn.close()
    except Exception as e:
        error = str(e)
    return render_template(
        'test_db.html',
        db_info=db_info,
        result=result,
        error=error
    )

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/debug-socket')
def debug_socket():
    try:
        socket_files = os.listdir('/cloudsql')
    except Exception as e:
        socket_files = f'Error reading socket dir: {e}'
    return {
        "cloudsql_dir": socket_files,
        "db_host_env": config.DB_HOST,
    }
    
if __name__ == '__main__':
    app.run(debug=True, port=8080)