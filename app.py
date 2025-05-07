from flask import Flask, render_template, request, redirect, url_for, flash, session, get_flashed_messages, jsonify
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
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText
from admin_blueprint import admin_bp
from lib.login_required import login_required
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vf-life-20240506-very-secret-key')  # 固定密鑰，建議用環境變數
app.permanent_session_lifetime = timedelta(days=30)  # 設定 session 有效期 30 天
app.register_blueprint(admin_bp)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/member_videos')
@login_required
def member_videos():
    user_email = session.get('user_email')
    repo = VideoRepository()
    # 取得系列 id 與名稱
    series_list = repo.get_all_series()
    active_series_id = series_list[0]['id'] if series_list else None
    video_list = repo.get_videos_with_status(user_email, active_series_id)
    repo.close()
    return render_template('member_videos.html', video_list=video_list, series_list=series_list, active_series_id=active_series_id, user_email=user_email)

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
            session['user_id'] = user['id']  # 新增 user_id 進 session
            if request.form.get('remember_me'):
                session.permanent = True
            else:
                session.permanent = False
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
                    flash('密碼修改成功，請重新登入', 'success')
                    repo.close()
                    return redirect(url_for('login'))
            repo.close()
    return render_template('change_password.html')

def generate_reset_token(email, expires_sec=3600):
    s = URLSafeTimedSerializer(app.secret_key)
    return s.dumps(email, salt='reset-password')

def verify_reset_token(token, expires_sec=3600):
    s = URLSafeTimedSerializer(app.secret_key)
    try:
        email = s.loads(token, salt='reset-password', max_age=expires_sec)
    except Exception:
        return None
    return email

def send_reset_email(to_email, token):
    reset_link = url_for('reset_password', token=token, _external=True)
    subject = '雙生紫焰直播回放平台 - 密碼重設連結'
    body = render_template('mail_templates/reset_password.html', reset_link=reset_link)
    msg = MIMEText(body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = getattr(config, 'EMAIL_USER', 'noreply@example.com')
    msg['To'] = to_email
    try:
        with smtplib.SMTP_SSL(getattr(config, 'EMAIL_HOST', 'smtp.gmail.com'), getattr(config, 'EMAIL_PORT', 465)) as server:
            server.login(getattr(config, 'EMAIL_USER', ''), getattr(config, 'EMAIL_PASSWORD', ''))
            server.sendmail(msg['From'], [to_email], msg.as_string())
        return True
    except Exception as e:
        app.logger.error(f"Error sending reset email: {e}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        repo = UserRepository()
        user = repo.get_user_by_email(email)
        repo.close()
        if not user:
            flash('該 Email 並未註冊，請確認後再試', 'danger')
            return redirect(url_for('forgot_password'))
        token = generate_reset_token(email)
        if send_reset_email(email, token):
            flash('重設密碼信已寄出，請檢查您的信箱', 'info')
            return redirect(url_for('login'))
        else:
            flash('發送重設連結時發生錯誤，請稍後再試', 'danger')
            return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('連結已失效或無效，請重新申請', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash('新密碼與確認密碼不一致', 'danger')
        else:
            repo = UserRepository()
            user = repo.get_user_by_email(email)
            if not user:
                flash('找不到使用者', 'danger')
                repo.close()
                return redirect(url_for('forgot_password'))
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            repo.update_password(user['id'], new_hash)
            repo.close()
            flash('密碼已重設，請重新登入', 'success')
            return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    # 如果是 admin 路徑，顯示 admin_404.html
    if request.path.startswith('/admin'):
        return render_template('admin_404.html'), 404
    return render_template('404.html'), 404

@app.route('/api/videos_by_series', methods=['POST'])
@login_required
def api_videos_by_series():
    user_email = session.get('user_email')
    series_id = request.json.get('series_id')
    logging.info(f"[api_videos_by_series] user_email: {user_email}, series_id: {series_id}")
    repo = VideoRepository()
    video_list = repo.get_videos_with_status(user_email, series_id)
    repo.close()
    return jsonify({'video_list': video_list})

@app.route('/member_sample')
def member_sample():
    # 這個 sample 頁面不需要登入，也不需要資料庫，直接渲染假資料
    return render_template('member_sample.html')

@app.route('/faqs')
def faqs():
    return render_template('faqs.html')
    
if __name__ == '__main__':
    app.run(debug=True, port=8080)